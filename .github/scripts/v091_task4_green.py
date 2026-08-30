from pathlib import Path

PATH = Path("src/engcalc_colab/characteristics.py")
text = PATH.read_text(encoding="utf-8")

if "def solve_intersections_exact(" in text:
    raise SystemExit("Task 4 solver already present; guarded patch will not reapply")

required = [
    "def _exact_real_solution_set(",
    "def _normalize_piecewise_breakpoint_quantity(",
    "def _select_piecewise_branch(",
    "def _point_is_covered_by_interval(",
    "def solve_roots_exact(",
]
for marker in required:
    if marker not in text:
        raise SystemExit(f"Task 4 patch guard failed: missing {marker}")

append = r'''


@dataclass(frozen=True)
class IntersectionRegion:
    left_expression: sp.Expr
    right_expression: sp.Expr
    lower_symbolic: sp.Expr
    upper_symbolic: sp.Expr
    lower_quantity: Any
    upper_quantity: Any


def _quantity_is_zero(quantity) -> bool:
    try:
        return float(quantity.magnitude) == 0.0
    except (TypeError, ValueError, OverflowError):
        return False


def _compatible_response_quantities(
    left_expression: sp.Expr,
    right_expression: sp.Expr,
    left_quantity,
    right_quantity,
    context,
):
    left_expression = sp.sympify(left_expression)
    right_expression = sp.sympify(right_expression)

    if (
        left_quantity.dimensionless
        and not right_quantity.dimensionless
        and _quantity_is_zero(left_quantity)
        and sp.simplify(left_expression) == 0
    ):
        left_quantity = context.ureg.Quantity(0, right_quantity.units)
    if (
        right_quantity.dimensionless
        and not left_quantity.dimensionless
        and _quantity_is_zero(right_quantity)
        and sp.simplify(right_expression) == 0
    ):
        right_quantity = context.ureg.Quantity(0, left_quantity.units)

    try:
        right_quantity = right_quantity.to(left_quantity.units)
    except DimensionalityError as exc:
        raise EngEvaluationError(
            "intersections responses have incompatible dimensions"
        ) from exc
    return left_quantity, right_quantity


def _evaluate_response_pair(
    left_expression: sp.Expr,
    right_expression: sp.Expr,
    variable: sp.Symbol,
    x_quantity,
    context,
    *,
    overrides: dict[str, Any] | None,
):
    sample_overrides = dict(overrides or {})
    sample_overrides[variable.name] = x_quantity
    try:
        _, left_quantity = context.evaluate_symbolic(
            left_expression,
            overrides=sample_overrides,
        )
        _, right_quantity = context.evaluate_symbolic(
            right_expression,
            overrides=sample_overrides,
        )
    except EngEvaluationError:
        return None
    return _compatible_response_quantities(
        left_expression,
        right_expression,
        left_quantity,
        right_quantity,
        context,
    )


def _active_scalar_expression(
    expression: sp.Expr,
    variable: sp.Symbol,
    point_quantity,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> sp.Expr:
    folded = sp.piecewise_fold(sp.sympify(expression))
    if not isinstance(folded, sp.Piecewise):
        return folded
    _, branch = _select_piecewise_branch(
        folded,
        variable,
        point_quantity,
        context,
        overrides=overrides,
    )
    return sp.sympify(branch)


def _intersection_boundaries(
    left_expression: sp.Expr,
    right_expression: sp.Expr,
    variable: sp.Symbol,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> tuple[tuple[sp.Expr, Any], ...]:
    raw: list[sp.Expr] = [domain.lower_symbolic, domain.upper_symbolic]
    for expression in (left_expression, right_expression):
        raw.extend(extract_symbolic_breakpoints(expression, variable.name))

    candidates: list[tuple[float, sp.Expr, Any]] = []
    lower = float(domain.lower_quantity.to(domain.unit).magnitude)
    upper = float(domain.upper_quantity.to(domain.unit).magnitude)
    span = abs(upper - lower)
    tolerance = 1e-12 * max(1.0, abs(lower), abs(upper), span)

    for symbolic in raw:
        symbolic = sp.sympify(symbolic)
        if symbolic == domain.lower_symbolic:
            quantity = domain.lower_quantity
        elif symbolic == domain.upper_symbolic:
            quantity = domain.upper_quantity
        else:
            quantity = _normalize_piecewise_breakpoint_quantity(
                context,
                symbolic,
                domain,
                overrides=overrides,
            )
        magnitude = float(quantity.to(domain.unit).magnitude)
        if magnitude < lower - tolerance or magnitude > upper + tolerance:
            continue
        candidates.append((magnitude, symbolic, quantity.to(domain.unit)))

    candidates.sort(key=lambda item: item[0])
    unique: list[tuple[sp.Expr, Any]] = []
    previous: float | None = None
    for magnitude, symbolic, quantity in candidates:
        if previous is not None and math.isclose(
            magnitude,
            previous,
            rel_tol=1e-12,
            abs_tol=tolerance,
        ):
            continue
        unique.append((symbolic, quantity))
        previous = magnitude
    return tuple(unique)


def _partition_intersection_regions(
    left_expression: sp.Expr,
    right_expression: sp.Expr,
    variable: sp.Symbol,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> tuple[IntersectionRegion, ...]:
    boundaries = _intersection_boundaries(
        left_expression,
        right_expression,
        variable,
        domain,
        context,
        overrides=overrides,
    )
    regions: list[IntersectionRegion] = []
    for index in range(len(boundaries) - 1):
        lower_symbolic, lower_quantity = boundaries[index]
        upper_symbolic, upper_quantity = boundaries[index + 1]
        midpoint = lower_quantity + (upper_quantity - lower_quantity) / 2
        left_branch = _active_scalar_expression(
            left_expression,
            variable,
            midpoint,
            context,
            overrides=overrides,
        )
        right_branch = _active_scalar_expression(
            right_expression,
            variable,
            midpoint,
            context,
            overrides=overrides,
        )
        pair = _evaluate_response_pair(
            left_branch,
            right_branch,
            variable,
            midpoint,
            context,
            overrides=overrides,
        )
        if pair is None:
            raise EngEvaluationError(
                "intersections responses could not be evaluated on the requested domain"
            )
        regions.append(
            IntersectionRegion(
                left_expression=left_branch,
                right_expression=right_branch,
                lower_symbolic=sp.sympify(lower_symbolic),
                upper_symbolic=sp.sympify(upper_symbolic),
                lower_quantity=lower_quantity,
                upper_quantity=upper_quantity,
            )
        )
    return tuple(regions)


def _candidate_strictly_inside_intersection_region(
    quantity,
    region: IntersectionRegion,
    domain: AnalysisDomain,
) -> bool:
    magnitude = float(quantity.to(domain.unit).magnitude)
    lower = float(region.lower_quantity.to(domain.unit).magnitude)
    upper = float(region.upper_quantity.to(domain.unit).magnitude)
    tolerance = 1e-12 * max(1.0, abs(lower), abs(upper), abs(upper - lower))
    return lower + tolerance < magnitude < upper - tolerance


def _intersection_source_label(
    left_label: str | None,
    right_label: str | None,
) -> str | None:
    if left_label and right_label:
        return f"{left_label} = {right_label}"
    return left_label or right_label


def _evaluate_intersection_candidate(
    left_expression: sp.Expr,
    right_expression: sp.Expr,
    variable: sp.Symbol,
    candidate: sp.Expr,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
    left_label: str | None,
    right_label: str | None,
) -> CharacteristicPoint | None:
    fixed_overrides = dict(overrides or {})
    try:
        _, x_quantity = context.evaluate_symbolic(candidate, overrides=fixed_overrides)
    except EngEvaluationError:
        return None
    x_quantity = _normalize_candidate_quantity(context, x_quantity, domain)
    if not _candidate_in_domain(x_quantity, domain):
        return None

    left_symbolic = sp.simplify(sp.sympify(left_expression).subs(variable, candidate))
    right_symbolic = sp.simplify(sp.sympify(right_expression).subs(variable, candidate))
    pair = _evaluate_response_pair(
        sp.sympify(left_expression),
        sp.sympify(right_expression),
        variable,
        x_quantity,
        context,
        overrides=fixed_overrides,
    )
    if pair is None:
        return None
    left_quantity, right_quantity = pair

    exact_equal = sp.simplify(left_symbolic - right_symbolic) == 0
    if not exact_equal:
        try:
            left_magnitude = float(left_quantity.magnitude)
            right_magnitude = float(right_quantity.magnitude)
        except (TypeError, ValueError, OverflowError):
            return None
        scale = max(1.0, abs(left_magnitude), abs(right_magnitude))
        if not math.isclose(
            left_magnitude,
            right_magnitude,
            rel_tol=1e-12,
            abs_tol=1e-12 * scale,
        ):
            return None

    return CharacteristicPoint(
        x_symbolic=sp.sympify(candidate),
        x_quantity=x_quantity,
        value_symbolic=left_symbolic,
        value_quantity=left_quantity,
        provenance="exact",
        side="at",
        roles=("intersection",),
        source_label=_intersection_source_label(left_label, right_label),
    )


def _coincident_interval(
    left_expression: sp.Expr,
    right_expression: sp.Expr,
    variable: sp.Symbol,
    region: IntersectionRegion,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
    left_label: str | None,
    right_label: str | None,
) -> CharacteristicInterval:
    lower_point = _evaluate_intersection_candidate(
        left_expression,
        right_expression,
        variable,
        region.lower_symbolic,
        domain,
        context,
        overrides=overrides,
        left_label=left_label,
        right_label=right_label,
    )
    upper_point = _evaluate_intersection_candidate(
        left_expression,
        right_expression,
        variable,
        region.upper_symbolic,
        domain,
        context,
        overrides=overrides,
        left_label=left_label,
        right_label=right_label,
    )
    return CharacteristicInterval(
        lower_symbolic=region.lower_symbolic,
        upper_symbolic=region.upper_symbolic,
        lower_quantity=region.lower_quantity,
        upper_quantity=region.upper_quantity,
        role="coincident",
        provenance="exact",
        lower_closed=lower_point is not None,
        upper_closed=upper_point is not None,
    )


def _merge_coincident_intervals(
    intervals: list[CharacteristicInterval],
    domain: AnalysisDomain,
) -> tuple[CharacteristicInterval, ...]:
    if not intervals:
        return ()
    intervals.sort(
        key=lambda item: float(item.lower_quantity.to(domain.unit).magnitude)
    )
    merged: list[CharacteristicInterval] = [intervals[0]]
    span = abs(
        float(domain.upper_quantity.to(domain.unit).magnitude)
        - float(domain.lower_quantity.to(domain.unit).magnitude)
    )
    tolerance = 1e-12 * max(1.0, span)
    for item in intervals[1:]:
        previous = merged[-1]
        previous_upper = float(previous.upper_quantity.to(domain.unit).magnitude)
        current_lower = float(item.lower_quantity.to(domain.unit).magnitude)
        touching = math.isclose(
            previous_upper,
            current_lower,
            rel_tol=1e-12,
            abs_tol=tolerance,
        )
        if touching and previous.upper_closed and item.lower_closed:
            merged[-1] = CharacteristicInterval(
                lower_symbolic=previous.lower_symbolic,
                upper_symbolic=item.upper_symbolic,
                lower_quantity=previous.lower_quantity,
                upper_quantity=item.upper_quantity,
                role="coincident",
                provenance="exact",
                lower_closed=previous.lower_closed,
                upper_closed=item.upper_closed,
            )
        else:
            merged.append(item)
    return tuple(merged)


def solve_intersections_exact(
    left_expression,
    right_expression,
    variable,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None = None,
    left_label: str | None = None,
    right_label: str | None = None,
):
    left_expression = sp.sympify(left_expression)
    right_expression = sp.sympify(right_expression)
    if isinstance(variable, str):
        variable = sp.Symbol(variable)
    if not isinstance(variable, sp.Symbol):
        raise EngEvaluationError("intersections variable must be a symbolic identifier")

    regions = _partition_intersection_regions(
        left_expression,
        right_expression,
        variable,
        domain,
        context,
        overrides=overrides,
    )

    points: list[CharacteristicPoint] = []
    intervals: list[CharacteristicInterval] = []
    unresolved_any = False

    for region in regions:
        difference = sp.simplify(
            region.left_expression - region.right_expression
        )
        if difference == 0 or difference.is_zero is True:
            intervals.append(
                _coincident_interval(
                    left_expression,
                    right_expression,
                    variable,
                    region,
                    domain,
                    context,
                    overrides=overrides,
                    left_label=left_label,
                    right_label=right_label,
                )
            )
            continue

        candidates, unresolved = _exact_real_solution_set(difference, variable)
        unresolved_any = unresolved_any or unresolved
        if unresolved:
            continue
        for candidate in candidates:
            candidate = sp.sympify(candidate)
            try:
                _, x_quantity = context.evaluate_symbolic(
                    candidate,
                    overrides=dict(overrides or {}),
                )
                x_quantity = _normalize_candidate_quantity(
                    context,
                    x_quantity,
                    domain,
                )
            except EngEvaluationError:
                continue
            if not _candidate_strictly_inside_intersection_region(
                x_quantity,
                region,
                domain,
            ):
                continue
            point = _evaluate_intersection_candidate(
                left_expression,
                right_expression,
                variable,
                candidate,
                domain,
                context,
                overrides=overrides,
                left_label=left_label,
                right_label=right_label,
            )
            if point is not None:
                points.append(point)

    boundaries = _intersection_boundaries(
        left_expression,
        right_expression,
        variable,
        domain,
        context,
        overrides=overrides,
    )
    for candidate, _ in boundaries:
        point = _evaluate_intersection_candidate(
            left_expression,
            right_expression,
            variable,
            candidate,
            domain,
            context,
            overrides=overrides,
            left_label=left_label,
            right_label=right_label,
        )
        if point is not None:
            points.append(point)

    merged_intervals = _merge_coincident_intervals(intervals, domain)
    ordered_points = _ordered_unique_points(points, domain)
    visible_points = tuple(
        point
        for point in ordered_points
        if not any(
            _point_is_covered_by_interval(point, interval, domain)
            for interval in merged_intervals
        )
    )
    return visible_points, merged_intervals, unresolved_any
'''

PATH.write_text(text + append, encoding="utf-8")
