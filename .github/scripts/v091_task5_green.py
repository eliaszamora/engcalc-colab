from pathlib import Path

PATH = Path("src/engcalc_colab/characteristics.py")
text = PATH.read_text(encoding="utf-8")

if "def solve_extrema_exact(" in text:
    raise SystemExit("Task 5 extrema solver already present; guarded patch will not reapply")

required = [
    "def normalize_analysis_domain(",
    "def _normalize_candidate_quantity(",
    "def _candidate_in_domain(",
    "def _ordered_unique_points(",
    "def solve_roots_exact(",
    "def solve_intersections_exact(",
]
for marker in required:
    if marker not in text:
        raise SystemExit(f"Task 5 patch guard failed: missing {marker}")

append = r'''


def _extrema_quantity_is_finite(quantity) -> bool:
    try:
        return math.isfinite(float(quantity.magnitude))
    except (TypeError, ValueError, OverflowError):
        return False


def _extrema_point_with_roles(
    point: CharacteristicPoint,
    roles: tuple[str, ...],
) -> CharacteristicPoint:
    return CharacteristicPoint(
        x_symbolic=point.x_symbolic,
        x_quantity=point.x_quantity,
        value_symbolic=point.value_symbolic,
        value_quantity=point.value_quantity,
        provenance=point.provenance,
        side=point.side,
        roles=roles,
        source_label=point.source_label,
    )


def _evaluate_extrema_candidate(
    expression: sp.Expr,
    variable: sp.Symbol,
    candidate: sp.Expr,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
    source_label: str | None,
    roles: tuple[str, ...],
) -> CharacteristicPoint | None:
    fixed_overrides = dict(overrides or {})
    candidate = sp.sympify(candidate)
    try:
        _, x_quantity = context.evaluate_symbolic(candidate, overrides=fixed_overrides)
        x_quantity = _normalize_candidate_quantity(context, x_quantity, domain)
    except EngEvaluationError:
        return None
    if not _candidate_in_domain(x_quantity, domain):
        return None

    symbolic_value = sp.simplify(expression.subs(variable, candidate))
    if _has_explicit_nonfinite_value(symbolic_value):
        return None

    sample_overrides = dict(fixed_overrides)
    sample_overrides[variable.name] = x_quantity
    try:
        _, value_quantity = context.evaluate_symbolic(
            expression,
            overrides=sample_overrides,
        )
    except EngEvaluationError:
        return None
    if not _extrema_quantity_is_finite(value_quantity):
        return None

    return CharacteristicPoint(
        x_symbolic=candidate,
        x_quantity=x_quantity,
        value_symbolic=symbolic_value,
        value_quantity=value_quantity,
        provenance="exact",
        side="at",
        roles=roles,
        source_label=source_label,
    )


def _quantity_strictly_inside_domain(quantity, domain: AnalysisDomain) -> bool:
    magnitude = float(quantity.to(domain.unit).magnitude)
    lower = float(domain.lower_quantity.to(domain.unit).magnitude)
    upper = float(domain.upper_quantity.to(domain.unit).magnitude)
    tolerance = 1e-12 * max(1.0, abs(lower), abs(upper), abs(upper - lower))
    return lower + tolerance < magnitude < upper - tolerance


def _evaluate_extrema_nearby(
    expression: sp.Expr,
    variable: sp.Symbol,
    x_quantity,
    context,
    *,
    overrides: dict[str, Any] | None,
):
    sample_overrides = dict(overrides or {})
    sample_overrides[variable.name] = x_quantity
    try:
        _, quantity = context.evaluate_symbolic(
            expression,
            overrides=sample_overrides,
        )
    except EngEvaluationError:
        return None
    if not _extrema_quantity_is_finite(quantity):
        return None
    return quantity


def _classify_stationary_role(
    expression: sp.Expr,
    variable: sp.Symbol,
    point: CharacteristicPoint,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> str | None:
    second = sp.simplify(
        sp.diff(expression, variable, 2).subs(variable, point.x_symbolic)
    )
    if second.is_positive is True:
        return "local_min"
    if second.is_negative is True:
        return "local_max"

    center = float(point.x_quantity.to(domain.unit).magnitude)
    lower = float(domain.lower_quantity.to(domain.unit).magnitude)
    upper = float(domain.upper_quantity.to(domain.unit).magnitude)
    left_span = center - lower
    right_span = upper - center
    adjacent_span = min(left_span, right_span)
    if adjacent_span <= 0:
        return None
    offset = adjacent_span * 1e-6
    if offset <= 0 or not math.isfinite(offset):
        return None

    left_x = context.ureg.Quantity(center - offset, domain.unit)
    right_x = context.ureg.Quantity(center + offset, domain.unit)
    left_value = _evaluate_extrema_nearby(
        expression,
        variable,
        left_x,
        context,
        overrides=overrides,
    )
    right_value = _evaluate_extrema_nearby(
        expression,
        variable,
        right_x,
        context,
        overrides=overrides,
    )
    if left_value is None or right_value is None or point.value_quantity is None:
        return None

    center_quantity = point.value_quantity
    canonical = center_quantity.units
    try:
        left_mag = float(left_value.to(canonical).magnitude)
        center_mag = float(center_quantity.to(canonical).magnitude)
        right_mag = float(right_value.to(canonical).magnitude)
    except DimensionalityError:
        return None
    scale = max(1.0, abs(left_mag), abs(center_mag), abs(right_mag))
    tolerance = 1e-14 * scale
    if center_mag > left_mag + tolerance and center_mag > right_mag + tolerance:
        return "local_max"
    if center_mag < left_mag - tolerance and center_mag < right_mag - tolerance:
        return "local_min"
    return None


def _extrema_canonical_unit(points: list[CharacteristicPoint]):
    for point in points:
        quantity = point.value_quantity
        if quantity is not None and not quantity.dimensionless:
            return quantity.units
    for point in points:
        quantity = point.value_quantity
        if quantity is not None:
            return quantity.units
    return None


def _extrema_magnitude_in_unit(quantity, canonical_unit, context) -> float:
    if quantity.dimensionless and canonical_unit != context.ureg.dimensionless:
        if float(quantity.magnitude) != 0.0:
            raise EngEvaluationError("extrema response values have incompatible dimensions")
        return 0.0
    try:
        converted = quantity.to(canonical_unit)
    except DimensionalityError as exc:
        raise EngEvaluationError(
            "extrema response values have incompatible dimensions"
        ) from exc
    return float(converted.magnitude)


def _assign_global_extrema_roles(
    points: list[CharacteristicPoint],
    domain: AnalysisDomain,
    context,
    *,
    unbounded_above: bool,
    unbounded_below: bool,
) -> tuple[CharacteristicPoint, ...]:
    if not points:
        return ()
    canonical_unit = _extrema_canonical_unit(points)
    if canonical_unit is None:
        return _ordered_unique_points(points, domain)

    magnitudes = [
        _extrema_magnitude_in_unit(point.value_quantity, canonical_unit, context)
        for point in points
    ]
    finite_magnitudes = [value for value in magnitudes if math.isfinite(value)]
    if not finite_magnitudes:
        return _ordered_unique_points(points, domain)

    maximum = max(finite_magnitudes)
    minimum = min(finite_magnitudes)
    scale = max(1.0, *(abs(value) for value in finite_magnitudes))
    tolerance = 1e-12 * scale

    classified: list[CharacteristicPoint] = []
    for point, magnitude in zip(points, magnitudes):
        roles = list(point.roles)
        if not unbounded_above and math.isclose(
            magnitude, maximum, rel_tol=1e-12, abs_tol=tolerance
        ):
            if "global_max" not in roles:
                roles.append("global_max")
        if not unbounded_below and math.isclose(
            magnitude, minimum, rel_tol=1e-12, abs_tol=tolerance
        ):
            if "global_min" not in roles:
                roles.append("global_min")
        classified.append(_extrema_point_with_roles(point, tuple(roles)))
    return _ordered_unique_points(classified, domain)


def _constant_extrema_interval(
    expression: sp.Expr,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> CharacteristicInterval:
    try:
        _, value_quantity = context.evaluate_symbolic(
            expression,
            overrides=dict(overrides or {}),
        )
    except EngEvaluationError as exc:
        raise EngEvaluationError(
            "constant extrema response must be numerically resolvable: " + str(exc)
        ) from None
    if not _extrema_quantity_is_finite(value_quantity):
        raise EngEvaluationError("constant extrema response must be finite")
    return CharacteristicInterval(
        lower_symbolic=domain.lower_symbolic,
        upper_symbolic=domain.upper_symbolic,
        lower_quantity=domain.lower_quantity,
        upper_quantity=domain.upper_quantity,
        role="global_max_min",
        provenance="exact",
        value_symbolic=expression,
        value_quantity=value_quantity,
        lower_closed=True,
        upper_closed=True,
    )


def _continuous_unbounded_directions(
    expression: sp.Expr,
    variable: sp.Symbol,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> tuple[bool, bool, bool]:
    try:
        singular_set = sp.singularities(expression, variable)
    except (NotImplementedError, ValueError, TypeError):
        return False, False, True

    if singular_set is sp.S.EmptySet:
        return False, False, False
    if not isinstance(singular_set, sp.FiniteSet):
        return False, False, True

    unbounded_above = False
    unbounded_below = False
    unresolved = False
    for singularity in singular_set:
        singularity = sp.sympify(singularity)
        try:
            _, x_quantity = context.evaluate_symbolic(
                singularity,
                overrides=dict(overrides or {}),
            )
            x_quantity = _normalize_candidate_quantity(context, x_quantity, domain)
        except EngEvaluationError:
            unresolved = True
            continue
        if not _quantity_strictly_inside_domain(x_quantity, domain):
            continue
        for direction in ("-", "+"):
            try:
                limit = sp.limit(
                    expression,
                    variable,
                    singularity,
                    dir=direction,
                )
            except (NotImplementedError, ValueError, TypeError):
                unresolved = True
                continue
            if limit == sp.oo:
                unbounded_above = True
            elif limit == -sp.oo:
                unbounded_below = True
            elif limit in (sp.zoo, sp.nan):
                unresolved = True
    return unbounded_above, unbounded_below, unresolved


def solve_extrema_exact(
    expression,
    variable,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None = None,
    source_label: str | None = None,
):
    expression = sp.simplify(sp.sympify(expression))
    if isinstance(variable, str):
        variable = sp.Symbol(variable)
    if not isinstance(variable, sp.Symbol):
        raise EngEvaluationError("extrema variable must be a symbolic identifier")
    if expression.has(sp.Piecewise):
        raise EngEvaluationError(
            "Piecewise extrema require region-aware extrema analysis"
        )

    if variable not in expression.free_symbols:
        interval = _constant_extrema_interval(
            expression,
            domain,
            context,
            overrides=overrides,
        )
        return (), (interval,), False, False, False

    unbounded_above, unbounded_below, singularity_unresolved = (
        _continuous_unbounded_directions(
            expression,
            variable,
            domain,
            context,
            overrides=overrides,
        )
    )

    points: list[CharacteristicPoint] = []
    for endpoint in (domain.lower_symbolic, domain.upper_symbolic):
        point = _evaluate_extrema_candidate(
            expression,
            variable,
            endpoint,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
            roles=("boundary",),
        )
        if point is not None:
            points.append(point)

    derivative = sp.simplify(sp.diff(expression, variable))
    stationary_points, stationary_intervals, derivative_unresolved = solve_roots_exact(
        derivative,
        variable,
        domain,
        context,
        overrides=overrides,
        source_label=source_label,
    )
    if stationary_intervals:
        derivative_unresolved = True

    for stationary in stationary_points:
        if not _quantity_strictly_inside_domain(stationary.x_quantity, domain):
            continue
        point = _evaluate_extrema_candidate(
            expression,
            variable,
            stationary.x_symbolic,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
            roles=(),
        )
        if point is None:
            continue
        role = _classify_stationary_role(
            expression,
            variable,
            point,
            domain,
            context,
            overrides=overrides,
        )
        if role is not None:
            point = _extrema_point_with_roles(point, (role,))
        points.append(point)

    classified = _assign_global_extrema_roles(
        points,
        domain,
        context,
        unbounded_above=unbounded_above,
        unbounded_below=unbounded_below,
    )
    unresolved = bool(derivative_unresolved or singularity_unresolved)
    return classified, (), unbounded_above, unbounded_below, unresolved
'''

PATH.write_text(text + append, encoding="utf-8")
