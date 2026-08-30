from pathlib import Path

PATH = Path("src/engcalc_colab/characteristics.py")
text = PATH.read_text(encoding="utf-8")

if "def _solve_piecewise_extrema_exact(" in text:
    raise SystemExit("Task 6 Piecewise extrema solver already present; guarded patch will not reapply")

marker = "\ndef solve_extrema_exact(\n"
if text.count(marker) != 1:
    raise SystemExit("Task 6 patch guard failed: expected exactly one solve_extrema_exact definition")

text = text.replace(marker, "\ndef _solve_continuous_extrema_exact(\n", 1)

append = r'''


def _piecewise_region_domain(region: ContinuousRegion) -> AnalysisDomain:
    return AnalysisDomain(
        lower_symbolic=region.lower_symbolic,
        upper_symbolic=region.upper_symbolic,
        lower_quantity=region.lower_quantity,
        upper_quantity=region.upper_quantity,
        unit=region.lower_quantity.units,
    )


def _point_without_global_roles(point: CharacteristicPoint) -> CharacteristicPoint:
    roles = tuple(
        role for role in point.roles if role not in {"global_max", "global_min"}
    )
    return _extrema_point_with_roles(point, roles)


def _constant_piecewise_region_interval(
    region: ContinuousRegion,
    variable: sp.Symbol,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> CharacteristicInterval:
    expression = sp.simplify(sp.sympify(region.expression))
    midpoint = region.lower_quantity + (region.upper_quantity - region.lower_quantity) / 2
    sample_overrides = dict(overrides or {})
    sample_overrides[variable.name] = midpoint
    try:
        _, value_quantity = context.evaluate_symbolic(
            expression,
            overrides=sample_overrides,
        )
    except EngEvaluationError as exc:
        raise EngEvaluationError(
            "constant Piecewise extrema region must be numerically resolvable: "
            + str(exc)
        ) from None
    if not _extrema_quantity_is_finite(value_quantity):
        raise EngEvaluationError("constant Piecewise extrema region must be finite")
    return CharacteristicInterval(
        lower_symbolic=region.lower_symbolic,
        upper_symbolic=region.upper_symbolic,
        lower_quantity=region.lower_quantity,
        upper_quantity=region.upper_quantity,
        role="constant",
        provenance="exact",
        value_symbolic=expression,
        value_quantity=value_quantity,
        lower_closed=region.lower_closed,
        upper_closed=region.upper_closed,
    )


def _piecewise_one_sided_point(
    region: ContinuousRegion,
    variable: sp.Symbol,
    breakpoint_symbolic: sp.Expr,
    breakpoint_quantity,
    context,
    *,
    side: str,
    overrides: dict[str, Any] | None,
    source_label: str | None,
):
    direction = "-" if side == "left" else "+"
    try:
        value_symbolic = sp.limit(
            sp.sympify(region.expression),
            variable,
            breakpoint_symbolic,
            dir=direction,
        )
    except (NotImplementedError, ValueError, TypeError):
        return None, False, False, True

    if value_symbolic == sp.oo:
        return None, True, False, False
    if value_symbolic == -sp.oo:
        return None, False, True, False
    if value_symbolic in (sp.zoo, sp.nan) or _has_explicit_nonfinite_value(value_symbolic):
        return None, False, False, True

    try:
        _, value_quantity = context.evaluate_symbolic(
            sp.sympify(value_symbolic),
            overrides=dict(overrides or {}),
        )
    except EngEvaluationError:
        return None, False, False, True
    if not _extrema_quantity_is_finite(value_quantity):
        return None, False, False, True

    point = CharacteristicPoint(
        x_symbolic=sp.sympify(breakpoint_symbolic),
        x_quantity=breakpoint_quantity,
        value_symbolic=sp.simplify(value_symbolic),
        value_quantity=value_quantity,
        provenance="exact",
        side=side,
        roles=("boundary",),
        source_label=source_label,
    )
    return point, False, False, False


def _piecewise_near_breakpoint_quantity(
    region: ContinuousRegion,
    breakpoint_quantity,
    domain: AnalysisDomain,
    *,
    side: str,
):
    breakpoint = float(breakpoint_quantity.to(domain.unit).magnitude)
    if side == "left":
        interior = float(region.lower_quantity.to(domain.unit).magnitude)
        span = breakpoint - interior
        if span <= 0:
            return None
        magnitude = breakpoint - span * 1e-6
    else:
        interior = float(region.upper_quantity.to(domain.unit).magnitude)
        span = interior - breakpoint
        if span <= 0:
            return None
        magnitude = breakpoint + span * 1e-6
    if not math.isfinite(magnitude):
        return None
    return context_quantity = None


def _piecewise_local_role_at_breakpoint(
    expression: sp.Expr,
    variable: sp.Symbol,
    at_point: CharacteristicPoint,
    left_region: ContinuousRegion,
    right_region: ContinuousRegion,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> str | None:
    breakpoint = float(at_point.x_quantity.to(domain.unit).magnitude)
    left_bound = float(left_region.lower_quantity.to(domain.unit).magnitude)
    right_bound = float(right_region.upper_quantity.to(domain.unit).magnitude)
    left_span = breakpoint - left_bound
    right_span = right_bound - breakpoint
    if left_span <= 0 or right_span <= 0:
        return None

    left_x = context.ureg.Quantity(breakpoint - left_span * 1e-6, domain.unit)
    right_x = context.ureg.Quantity(breakpoint + right_span * 1e-6, domain.unit)
    left_value = _evaluate_extrema_nearby(
        sp.sympify(left_region.expression),
        variable,
        left_x,
        context,
        overrides=overrides,
    )
    right_value = _evaluate_extrema_nearby(
        sp.sympify(right_region.expression),
        variable,
        right_x,
        context,
        overrides=overrides,
    )
    center_value = at_point.value_quantity
    if left_value is None or right_value is None or center_value is None:
        return None

    quantities = (left_value, center_value, right_value)
    canonical_unit = next(
        (quantity.units for quantity in quantities if not quantity.dimensionless),
        center_value.units,
    )
    try:
        left_mag = _extrema_magnitude_in_unit(left_value, canonical_unit, context)
        center_mag = _extrema_magnitude_in_unit(center_value, canonical_unit, context)
        right_mag = _extrema_magnitude_in_unit(right_value, canonical_unit, context)
    except EngEvaluationError:
        return None

    scale = max(1.0, abs(left_mag), abs(center_mag), abs(right_mag))
    tolerance = 1e-14 * scale
    if center_mag > left_mag + tolerance and center_mag > right_mag + tolerance:
        return "local_max"
    if center_mag < left_mag - tolerance and center_mag < right_mag - tolerance:
        return "local_min"
    return None


def _same_extrema_value(
    left_quantity,
    right_quantity,
    context,
) -> bool:
    quantities = (left_quantity, right_quantity)
    canonical_unit = next(
        (quantity.units for quantity in quantities if not quantity.dimensionless),
        left_quantity.units,
    )
    try:
        left = _extrema_magnitude_in_unit(left_quantity, canonical_unit, context)
        right = _extrema_magnitude_in_unit(right_quantity, canonical_unit, context)
    except EngEvaluationError:
        return False
    scale = max(1.0, abs(left), abs(right))
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12 * scale)


def _ordered_unique_extrema_points(
    points: list[CharacteristicPoint],
    domain: AnalysisDomain,
) -> tuple[CharacteristicPoint, ...]:
    side_order = {"left": 0, "at": 1, "right": 2}
    points.sort(
        key=lambda point: (
            float(point.x_quantity.to(domain.unit).magnitude),
            side_order.get(point.side, 1),
        )
    )
    span = abs(
        float(domain.upper_quantity.to(domain.unit).magnitude)
        - float(domain.lower_quantity.to(domain.unit).magnitude)
    )
    tolerance = 1e-12 * max(1.0, span)
    unique: list[CharacteristicPoint] = []
    for point in points:
        duplicate_index = None
        current_x = float(point.x_quantity.to(domain.unit).magnitude)
        for index in range(len(unique) - 1, -1, -1):
            previous = unique[index]
            previous_x = float(previous.x_quantity.to(domain.unit).magnitude)
            if current_x - previous_x > tolerance:
                break
            if point.side != previous.side:
                continue
            if math.isclose(
                current_x,
                previous_x,
                rel_tol=1e-12,
                abs_tol=tolerance,
            ):
                duplicate_index = index
                break
        if duplicate_index is None:
            unique.append(point)
            continue
        previous = unique[duplicate_index]
        roles = tuple(dict.fromkeys((*previous.roles, *point.roles)))
        unique[duplicate_index] = _extrema_point_with_roles(previous, roles)
    unique.sort(
        key=lambda point: (
            float(point.x_quantity.to(domain.unit).magnitude),
            side_order.get(point.side, 1),
        )
    )
    return tuple(unique)


def _piecewise_global_roles(
    points: list[CharacteristicPoint],
    intervals: list[CharacteristicInterval],
    domain: AnalysisDomain,
    context,
    *,
    unbounded_above: bool,
    unbounded_below: bool,
):
    attained_points = [
        point
        for point in points
        if point.side == "at" and point.value_quantity is not None
    ]
    attained_intervals = [
        interval for interval in intervals if interval.value_quantity is not None
    ]
    quantities = [point.value_quantity for point in attained_points] + [
        interval.value_quantity for interval in attained_intervals
    ]
    if not quantities:
        return _ordered_unique_extrema_points(points, domain), ()

    canonical_unit = next(
        (quantity.units for quantity in quantities if not quantity.dimensionless),
        quantities[0].units,
    )
    magnitudes = [
        _extrema_magnitude_in_unit(quantity, canonical_unit, context)
        for quantity in quantities
    ]
    maximum = max(magnitudes)
    minimum = min(magnitudes)
    scale = max(1.0, *(abs(value) for value in magnitudes))
    tolerance = 1e-12 * scale

    classified_points: list[CharacteristicPoint] = []
    for point in points:
        roles = [
            role for role in point.roles if role not in {"global_max", "global_min"}
        ]
        if point.side == "at" and point.value_quantity is not None:
            magnitude = _extrema_magnitude_in_unit(
                point.value_quantity,
                canonical_unit,
                context,
            )
            if not unbounded_above and math.isclose(
                magnitude, maximum, rel_tol=1e-12, abs_tol=tolerance
            ):
                roles.append("global_max")
            if not unbounded_below and math.isclose(
                magnitude, minimum, rel_tol=1e-12, abs_tol=tolerance
            ):
                roles.append("global_min")
        classified_points.append(_extrema_point_with_roles(point, tuple(dict.fromkeys(roles))))

    retained_intervals: list[CharacteristicInterval] = []
    for interval in intervals:
        if interval.value_quantity is None:
            continue
        magnitude = _extrema_magnitude_in_unit(
            interval.value_quantity,
            canonical_unit,
            context,
        )
        is_max = not unbounded_above and math.isclose(
            magnitude, maximum, rel_tol=1e-12, abs_tol=tolerance
        )
        is_min = not unbounded_below and math.isclose(
            magnitude, minimum, rel_tol=1e-12, abs_tol=tolerance
        )
        if not is_max and not is_min:
            continue
        role = "global_max_min" if is_max and is_min else "global_max" if is_max else "global_min"
        retained_intervals.append(
            CharacteristicInterval(
                lower_symbolic=interval.lower_symbolic,
                upper_symbolic=interval.upper_symbolic,
                lower_quantity=interval.lower_quantity,
                upper_quantity=interval.upper_quantity,
                role=role,
                provenance=interval.provenance,
                value_symbolic=interval.value_symbolic,
                value_quantity=interval.value_quantity,
                lower_closed=interval.lower_closed,
                upper_closed=interval.upper_closed,
            )
        )

    visible_points: list[CharacteristicPoint] = []
    for point in classified_points:
        removable = (
            point.side == "at"
            and not any(role in {"local_max", "local_min"} for role in point.roles)
        )
        if removable:
            covered = False
            for interval in retained_intervals:
                if not _point_is_covered_by_interval(point, interval, domain):
                    continue
                if point.value_quantity is None or interval.value_quantity is None:
                    continue
                if _same_extrema_value(point.value_quantity, interval.value_quantity, context):
                    covered = True
                    break
            if covered:
                continue
        visible_points.append(point)

    retained_intervals.sort(
        key=lambda interval: float(interval.lower_quantity.to(domain.unit).magnitude)
    )
    return (
        _ordered_unique_extrema_points(visible_points, domain),
        tuple(retained_intervals),
    )


def _solve_piecewise_extrema_exact(
    expression: sp.Expr,
    variable: sp.Symbol,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
    source_label: str | None,
):
    regions = _partition_piecewise_regions(
        expression,
        variable,
        domain,
        context,
        overrides=overrides,
    )
    if not regions:
        raise EngEvaluationError(
            "piecewise characteristic domain could not be partitioned safely"
        )

    points: list[CharacteristicPoint] = []
    constant_intervals: list[CharacteristicInterval] = []
    unbounded_above = False
    unbounded_below = False
    unresolved = False

    for region in regions:
        branch_expression = sp.simplify(sp.sympify(region.expression))
        region_domain = _piecewise_region_domain(region)
        if variable not in branch_expression.free_symbols:
            constant_intervals.append(
                _constant_piecewise_region_interval(
                    region,
                    variable,
                    context,
                    overrides=overrides,
                )
            )
            continue

        region_points, _, region_up, region_down, region_unresolved = (
            _solve_continuous_extrema_exact(
                branch_expression,
                variable,
                region_domain,
                context,
                overrides=overrides,
                source_label=source_label,
            )
        )
        unbounded_above = unbounded_above or region_up
        unbounded_below = unbounded_below or region_down
        unresolved = unresolved or region_unresolved
        for point in region_points:
            if _quantity_strictly_inside_domain(point.x_quantity, region_domain):
                points.append(_point_without_global_roles(point))

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

    for index in range(len(regions) - 1):
        left_region = regions[index]
        right_region = regions[index + 1]
        breakpoint_symbolic = sp.sympify(left_region.upper_symbolic)
        breakpoint_quantity = left_region.upper_quantity

        left_point, left_up, left_down, left_unresolved = _piecewise_one_sided_point(
            left_region,
            variable,
            breakpoint_symbolic,
            breakpoint_quantity,
            context,
            side="left",
            overrides=overrides,
            source_label=source_label,
        )
        right_point, right_up, right_down, right_unresolved = _piecewise_one_sided_point(
            right_region,
            variable,
            breakpoint_symbolic,
            breakpoint_quantity,
            context,
            side="right",
            overrides=overrides,
            source_label=source_label,
        )
        unbounded_above = unbounded_above or left_up or right_up
        unbounded_below = unbounded_below or left_down or right_down
        unresolved = unresolved or left_unresolved or right_unresolved
        if left_point is not None:
            points.append(left_point)

        at_point = _evaluate_extrema_candidate(
            expression,
            variable,
            breakpoint_symbolic,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
            roles=("boundary",),
        )
        if at_point is not None:
            local_role = _piecewise_local_role_at_breakpoint(
                expression,
                variable,
                at_point,
                left_region,
                right_region,
                domain,
                context,
                overrides=overrides,
            )
            if local_role is not None:
                at_point = _extrema_point_with_roles(
                    at_point,
                    tuple(dict.fromkeys((*at_point.roles, local_role))),
                )
            points.append(at_point)
        if right_point is not None:
            points.append(right_point)

    return (*_piecewise_global_roles(
        points,
        constant_intervals,
        domain,
        context,
        unbounded_above=unbounded_above,
        unbounded_below=unbounded_below,
    ), unbounded_above, unbounded_below, unresolved)


def solve_extrema_exact(
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
        raise EngEvaluationError("extrema variable must be a symbolic identifier")
    if expression.has(sp.Piecewise):
        return _solve_piecewise_extrema_exact(
            expression,
            variable,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
        )
    return _solve_continuous_extrema_exact(
        expression,
        variable,
        domain,
        context,
        overrides=overrides,
        source_label=source_label,
    )
'''

# Remove a deliberately unreachable helper stub before writing; keeping this guard
# makes accidental partial edits visible rather than silently changing product code.
append = append.replace(
    '''\n\ndef _piecewise_near_breakpoint_quantity(\n    region: ContinuousRegion,\n    breakpoint_quantity,\n    domain: AnalysisDomain,\n    *,\n    side: str,\n):\n    breakpoint = float(breakpoint_quantity.to(domain.unit).magnitude)\n    if side == "left":\n        interior = float(region.lower_quantity.to(domain.unit).magnitude)\n        span = breakpoint - interior\n        if span <= 0:\n            return None\n        magnitude = breakpoint - span * 1e-6\n    else:\n        interior = float(region.upper_quantity.to(domain.unit).magnitude)\n        span = interior - breakpoint\n        if span <= 0:\n            return None\n        magnitude = breakpoint + span * 1e-6\n    if not math.isfinite(magnitude):\n        return None\n    return context_quantity = None\n''',
    "",
)

PATH.write_text(text + append, encoding="utf-8")
