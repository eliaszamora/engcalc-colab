from pathlib import Path

MODELS = Path("src/engcalc_colab/models.py")
CHARACTERISTICS = Path("src/engcalc_colab/characteristics.py")

models_text = MODELS.read_text(encoding="utf-8")
old_interval = '''@dataclass(frozen=True)\nclass CharacteristicInterval:\n    lower_symbolic: Any\n    upper_symbolic: Any\n    lower_quantity: Any\n    upper_quantity: Any\n    role: str\n    provenance: str = "exact"\n    value_symbolic: Any | None = None\n    value_quantity: Any | None = None\n\n    def __post_init__(self) -> None:\n        if self.provenance not in _CHARACTERISTIC_PROVENANCE:\n            raise ValueError("characteristic provenance must be 'exact' or 'numeric'")\n'''
new_interval = '''@dataclass(frozen=True)\nclass CharacteristicInterval:\n    lower_symbolic: Any\n    upper_symbolic: Any\n    lower_quantity: Any\n    upper_quantity: Any\n    role: str\n    provenance: str = "exact"\n    value_symbolic: Any | None = None\n    value_quantity: Any | None = None\n    lower_closed: bool = True\n    upper_closed: bool = True\n\n    def __post_init__(self) -> None:\n        if self.provenance not in _CHARACTERISTIC_PROVENANCE:\n            raise ValueError("characteristic provenance must be 'exact' or 'numeric'")\n        if not isinstance(self.lower_closed, bool) or not isinstance(self.upper_closed, bool):\n            raise ValueError("characteristic interval closure flags must be boolean")\n'''
if old_interval in models_text:
    models_text = models_text.replace(old_interval, new_interval, 1)
elif new_interval not in models_text:
    raise SystemExit("CharacteristicInterval guard failed: expected source block not found")
MODELS.write_text(models_text, encoding="utf-8")

characteristics_text = CHARACTERISTICS.read_text(encoding="utf-8")
if "class ContinuousRegion:" not in characteristics_text:
    characteristics_text = characteristics_text.replace(
        "from .models import CharacteristicPoint\n",
        "from .models import CharacteristicInterval, CharacteristicPoint\n"
        "from .piecewise import extract_symbolic_breakpoints\n",
        1,
    )
    domain_block = '''@dataclass(frozen=True)\nclass AnalysisDomain:\n    lower_symbolic: sp.Expr\n    upper_symbolic: sp.Expr\n    lower_quantity: Any\n    upper_quantity: Any\n    unit: Any\n'''
    region_block = domain_block + '''\n\n@dataclass(frozen=True)\nclass ContinuousRegion:\n    expression: sp.Expr\n    lower_symbolic: sp.Expr\n    upper_symbolic: sp.Expr\n    lower_quantity: Any\n    upper_quantity: Any\n    lower_closed: bool\n    upper_closed: bool\n'''
    if domain_block not in characteristics_text:
        raise SystemExit("AnalysisDomain guard failed")
    characteristics_text = characteristics_text.replace(domain_block, region_block, 1)

    solver_start = characteristics_text.find("def solve_roots_exact(\n")
    if solver_start < 0:
        raise SystemExit("solve_roots_exact guard failed")

    replacement = r'''def _normalize_piecewise_breakpoint_quantity(
    context,
    expression: sp.Expr,
    domain: AnalysisDomain,
    *,
    overrides: dict[str, Any] | None,
):
    try:
        _, quantity = context.evaluate_symbolic(
            sp.sympify(expression),
            overrides=dict(overrides or {}),
        )
    except EngEvaluationError as exc:
        raise EngEvaluationError(
            "piecewise characteristic breakpoint must be numerically resolvable: "
            + str(exc)
        ) from None

    if quantity.dimensionless and not domain.lower_quantity.dimensionless:
        if float(quantity.magnitude) != 0.0:
            raise EngEvaluationError(
                "piecewise characteristic breakpoint has incompatible units"
            )
        quantity = context.ureg.Quantity(0, domain.unit)
    try:
        quantity = quantity.to(domain.unit)
    except DimensionalityError as exc:
        raise EngEvaluationError(
            "piecewise characteristic breakpoint has incompatible units"
        ) from exc

    magnitude = float(quantity.magnitude)
    if not math.isfinite(magnitude):
        raise EngEvaluationError("piecewise characteristic breakpoint must be finite")
    return quantity


def _piecewise_substitutions(
    expression: sp.Expr,
    variable: sp.Symbol,
    point_quantity,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> dict[str, Any]:
    fixed_overrides = dict(overrides or {})
    names = sorted(symbol.name for symbol in sp.sympify(expression).free_symbols)
    substitutions: dict[str, Any] = {}
    for name in names:
        if name == variable.name:
            substitutions[name] = point_quantity
        elif name in fixed_overrides:
            substitutions[name] = fixed_overrides[name]
        elif name in context.values:
            substitutions[name] = context.values[name]
        else:
            raise EngEvaluationError(
                "piecewise characteristic domain could not be partitioned safely: "
                f"missing numeric value for '{name}'"
            )
    return substitutions


def _condition_truth(condition, substitutions: dict[str, Any], context) -> bool:
    if condition == sp.true:
        return True
    if condition == sp.false:
        return False
    if isinstance(condition, sp.Rel):
        return bool(context._evaluate_relation(condition, substitutions))
    if condition.func == sp.And:
        return all(_condition_truth(arg, substitutions, context) for arg in condition.args)
    if condition.func == sp.Or:
        return any(_condition_truth(arg, substitutions, context) for arg in condition.args)
    if condition.func == sp.Not and len(condition.args) == 1:
        return not _condition_truth(condition.args[0], substitutions, context)
    raise EngEvaluationError(
        "piecewise characteristic domain could not be partitioned safely"
    )


def _select_piecewise_branch(
    piecewise: sp.Piecewise,
    variable: sp.Symbol,
    point_quantity,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> tuple[int, sp.Expr]:
    substitutions = _piecewise_substitutions(
        piecewise,
        variable,
        point_quantity,
        context,
        overrides=overrides,
    )
    for index, (branch_expression, condition) in enumerate(piecewise.args):
        if _condition_truth(condition, substitutions, context):
            return index, sp.sympify(branch_expression)
    raise EngEvaluationError(
        "piecewise characteristic domain could not be partitioned safely"
    )


def _same_branch_at_boundary(
    piecewise: sp.Piecewise,
    selected_index: int,
    variable: sp.Symbol,
    point_quantity,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> bool:
    try:
        boundary_index, _ = _select_piecewise_branch(
            piecewise,
            variable,
            point_quantity,
            context,
            overrides=overrides,
        )
    except EngEvaluationError:
        return False
    return boundary_index == selected_index


def _partition_piecewise_regions(
    expression,
    variable: sp.Symbol,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None = None,
) -> tuple[ContinuousRegion, ...]:
    expression = sp.sympify(expression)
    folded = sp.piecewise_fold(expression)
    if not isinstance(folded, sp.Piecewise):
        return (
            ContinuousRegion(
                expression=folded,
                lower_symbolic=domain.lower_symbolic,
                upper_symbolic=domain.upper_symbolic,
                lower_quantity=domain.lower_quantity,
                upper_quantity=domain.upper_quantity,
                lower_closed=True,
                upper_closed=True,
            ),
        )

    lower_magnitude = float(domain.lower_quantity.to(domain.unit).magnitude)
    upper_magnitude = float(domain.upper_quantity.to(domain.unit).magnitude)
    span = abs(upper_magnitude - lower_magnitude)
    tolerance = 1e-12 * max(1.0, abs(lower_magnitude), abs(upper_magnitude), span)

    internal: list[tuple[sp.Expr, Any]] = []
    for breakpoint_expression in extract_symbolic_breakpoints(
        expression,
        variable.name,
    ):
        quantity = _normalize_piecewise_breakpoint_quantity(
            context,
            breakpoint_expression,
            domain,
            overrides=overrides,
        )
        magnitude = float(quantity.magnitude)
        if not (lower_magnitude + tolerance < magnitude < upper_magnitude - tolerance):
            continue
        if any(
            math.isclose(
                magnitude,
                float(existing_quantity.magnitude),
                rel_tol=1e-12,
                abs_tol=tolerance,
            )
            for _, existing_quantity in internal
        ):
            continue
        internal.append((sp.sympify(breakpoint_expression), quantity))

    internal.sort(key=lambda item: float(item[1].magnitude))
    boundaries = [
        (domain.lower_symbolic, domain.lower_quantity),
        *internal,
        (domain.upper_symbolic, domain.upper_quantity),
    ]

    regions: list[ContinuousRegion] = []
    for index in range(len(boundaries) - 1):
        lower_symbolic, lower_quantity = boundaries[index]
        upper_symbolic, upper_quantity = boundaries[index + 1]
        midpoint = lower_quantity + (upper_quantity - lower_quantity) / 2
        selected_index, branch_expression = _select_piecewise_branch(
            folded,
            variable,
            midpoint,
            context,
            overrides=overrides,
        )
        lower_closed = _same_branch_at_boundary(
            folded,
            selected_index,
            variable,
            lower_quantity,
            context,
            overrides=overrides,
        )
        upper_closed = _same_branch_at_boundary(
            folded,
            selected_index,
            variable,
            upper_quantity,
            context,
            overrides=overrides,
        )
        regions.append(
            ContinuousRegion(
                expression=branch_expression,
                lower_symbolic=sp.sympify(lower_symbolic),
                upper_symbolic=sp.sympify(upper_symbolic),
                lower_quantity=lower_quantity,
                upper_quantity=upper_quantity,
                lower_closed=lower_closed,
                upper_closed=upper_closed,
            )
        )
    return tuple(regions)


def _candidate_in_region(quantity, region: ContinuousRegion, domain: AnalysisDomain) -> bool:
    magnitude = float(quantity.to(domain.unit).magnitude)
    lower = float(region.lower_quantity.to(domain.unit).magnitude)
    upper = float(region.upper_quantity.to(domain.unit).magnitude)
    tolerance = 1e-12 * max(1.0, abs(lower), abs(upper), abs(upper - lower))
    if magnitude < lower - tolerance or magnitude > upper + tolerance:
        return False
    if math.isclose(magnitude, lower, rel_tol=1e-12, abs_tol=tolerance):
        return region.lower_closed
    if math.isclose(magnitude, upper, rel_tol=1e-12, abs_tol=tolerance):
        return region.upper_closed
    return True


def _zero_interval_for_region(
    original_expression: sp.Expr,
    variable: sp.Symbol,
    region: ContinuousRegion,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> CharacteristicInterval:
    midpoint = region.lower_quantity + (region.upper_quantity - region.lower_quantity) / 2
    sample_overrides = dict(overrides or {})
    sample_overrides[variable.name] = midpoint
    value_quantity = None
    try:
        _, value_quantity = context.evaluate_symbolic(
            original_expression,
            overrides=sample_overrides,
        )
    except EngEvaluationError:
        try:
            _, value_quantity = context.evaluate_symbolic(
                region.expression,
                overrides=sample_overrides,
            )
        except EngEvaluationError:
            value_quantity = None
    return CharacteristicInterval(
        lower_symbolic=region.lower_symbolic,
        upper_symbolic=region.upper_symbolic,
        lower_quantity=region.lower_quantity,
        upper_quantity=region.upper_quantity,
        role="roots",
        provenance="exact",
        value_symbolic=sp.Integer(0),
        value_quantity=value_quantity,
        lower_closed=region.lower_closed,
        upper_closed=region.upper_closed,
    )


def _point_is_covered_by_interval(
    point: CharacteristicPoint,
    interval: CharacteristicInterval,
    domain: AnalysisDomain,
) -> bool:
    point_magnitude = float(point.x_quantity.to(domain.unit).magnitude)
    lower = float(interval.lower_quantity.to(domain.unit).magnitude)
    upper = float(interval.upper_quantity.to(domain.unit).magnitude)
    tolerance = 1e-12 * max(1.0, abs(lower), abs(upper), abs(upper - lower))
    if point_magnitude < lower - tolerance or point_magnitude > upper + tolerance:
        return False
    if math.isclose(point_magnitude, lower, rel_tol=1e-12, abs_tol=tolerance):
        return interval.lower_closed
    if math.isclose(point_magnitude, upper, rel_tol=1e-12, abs_tol=tolerance):
        return interval.upper_closed
    return True


def _piecewise_boundary_candidates(
    expression: sp.Expr,
    variable: sp.Symbol,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> tuple[sp.Expr, ...]:
    candidates: list[sp.Expr] = [domain.lower_symbolic]
    for breakpoint in extract_symbolic_breakpoints(expression, variable.name):
        quantity = _normalize_piecewise_breakpoint_quantity(
            context,
            breakpoint,
            domain,
            overrides=overrides,
        )
        if _candidate_in_domain(quantity, domain):
            candidates.append(sp.sympify(breakpoint))
    candidates.append(domain.upper_symbolic)

    ordered: list[tuple[float, sp.Expr]] = []
    for candidate in candidates:
        try:
            _, quantity = context.evaluate_symbolic(
                candidate,
                overrides=dict(overrides or {}),
            )
            quantity = _normalize_candidate_quantity(context, quantity, domain)
        except EngEvaluationError:
            continue
        ordered.append((float(quantity.magnitude), candidate))
    ordered.sort(key=lambda item: item[0])

    unique: list[sp.Expr] = []
    previous: float | None = None
    span = abs(
        float(domain.upper_quantity.magnitude)
        - float(domain.lower_quantity.magnitude)
    )
    tolerance = 1e-12 * max(1.0, span)
    for magnitude, candidate in ordered:
        if previous is not None and math.isclose(
            magnitude,
            previous,
            rel_tol=1e-12,
            abs_tol=tolerance,
        ):
            continue
        unique.append(candidate)
        previous = magnitude
    return tuple(unique)


def solve_roots_exact(
    expression,
    variable,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None = None,
    source_label: str | None = None,
):
    expression = sp.sympify(expression)
    if isinstance(variable, str):
        variable = sp.Symbol(variable)
    if not isinstance(variable, sp.Symbol):
        raise EngEvaluationError("roots variable must be a symbolic identifier")

    if sp.simplify(expression) == 0:
        interval = CharacteristicInterval(
            lower_symbolic=domain.lower_symbolic,
            upper_symbolic=domain.upper_symbolic,
            lower_quantity=domain.lower_quantity,
            upper_quantity=domain.upper_quantity,
            role="roots",
            provenance="exact",
            value_symbolic=sp.Integer(0),
            value_quantity=None,
            lower_closed=True,
            upper_closed=True,
        )
        return (), (interval,), False

    if not expression.has(sp.Piecewise):
        candidates, unresolved = _exact_real_solution_set(expression, variable)
        if unresolved:
            return (), (), True

        points: list[CharacteristicPoint] = []
        for candidate in candidates:
            point = _evaluate_root_candidate(
                expression,
                variable,
                sp.sympify(candidate),
                domain,
                context,
                overrides=overrides,
                source_label=source_label,
            )
            if point is not None:
                points.append(point)
        return _ordered_unique_points(points, domain), (), False

    regions = _partition_piecewise_regions(
        expression,
        variable,
        domain,
        context,
        overrides=overrides,
    )
    points: list[CharacteristicPoint] = []
    intervals: list[CharacteristicInterval] = []
    unresolved_any = False

    for region in regions:
        branch_expression = sp.sympify(region.expression)
        if sp.simplify(branch_expression) == 0:
            intervals.append(
                _zero_interval_for_region(
                    expression,
                    variable,
                    region,
                    context,
                    overrides=overrides,
                )
            )
            continue

        candidates, unresolved = _exact_real_solution_set(branch_expression, variable)
        unresolved_any = unresolved_any or unresolved
        if unresolved:
            continue
        for candidate in candidates:
            point = _evaluate_root_candidate(
                branch_expression,
                variable,
                sp.sympify(candidate),
                domain,
                context,
                overrides=overrides,
                source_label=source_label,
            )
            if point is not None and _candidate_in_region(
                point.x_quantity,
                region,
                domain,
            ):
                points.append(point)

    for candidate in _piecewise_boundary_candidates(
        expression,
        variable,
        domain,
        context,
        overrides=overrides,
    ):
        point = _evaluate_root_candidate(
            expression,
            variable,
            candidate,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
        )
        if point is not None:
            points.append(point)

    ordered_points = _ordered_unique_points(points, domain)
    visible_points = tuple(
        point
        for point in ordered_points
        if not any(
            _point_is_covered_by_interval(point, interval, domain)
            for interval in intervals
        )
    )
    intervals.sort(
        key=lambda item: float(item.lower_quantity.to(domain.unit).magnitude)
    )
    return visible_points, tuple(intervals), unresolved_any
'''
    characteristics_text = characteristics_text[:solver_start] + replacement
elif "def _partition_piecewise_regions(" not in characteristics_text:
    raise SystemExit("ContinuousRegion exists but Piecewise solver patch is incomplete")

CHARACTERISTICS.write_text(characteristics_text, encoding="utf-8")
