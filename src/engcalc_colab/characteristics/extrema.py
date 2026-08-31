from __future__ import annotations

import math
from typing import Any

import sympy as sp
from pint.errors import DimensionalityError

from ..errors import EngEvaluationError
from ..models import CharacteristicInterval, CharacteristicPoint
from .candidates import (
    _candidate_in_domain,
    _deduplicate_root_points,
    _normalize_candidate_quantity,
    _ordered_unique_points,
)
from .domain import (
    AnalysisDomain,
    ContinuousRegion,
    _analysis_variable,
    _has_explicit_nonfinite_value,
    _quantity_is_zero,
)
from .piecewise_analysis import (
    _partition_piecewise_regions,
    _point_is_covered_by_interval,
    _select_piecewise_branch,
)
from .roots import solve_roots_exact



def _simplify_decidable_abs(
    expression: sp.Expr,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> sp.Expr:
    simplified = sp.simplify(sp.sympify(expression))
    replacements: dict[sp.Expr, sp.Expr] = {}
    for absolute in simplified.atoms(sp.Abs):
        argument = sp.sympify(absolute.args[0])
        fixed_overrides = context.unit_literal_overrides(argument, overrides)
        try:
            _, quantity = context.evaluate_symbolic(
                argument,
                overrides=fixed_overrides,
            )
            magnitude = float(quantity.magnitude)
        except (EngEvaluationError, TypeError, ValueError, OverflowError):
            continue
        if not math.isfinite(magnitude):
            continue
        if magnitude > 0.0:
            replacements[absolute] = argument
        elif magnitude < 0.0:
            replacements[absolute] = -argument
        else:
            replacements[absolute] = sp.Integer(0)
    if replacements:
        simplified = simplified.xreplace(replacements)
    return sp.simplify(simplified)

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
    candidate_quantity=None,
    provenance: str = "exact",
) -> CharacteristicPoint | None:
    candidate = sp.sympify(candidate)
    fixed_overrides = context.unit_literal_overrides(candidate, overrides)
    if candidate_quantity is None:
        try:
            _, x_quantity = context.evaluate_symbolic(candidate, overrides=fixed_overrides)
            x_quantity = _normalize_candidate_quantity(context, x_quantity, domain)
        except EngEvaluationError:
            return None
    else:
        try:
            x_quantity = _normalize_candidate_quantity(context, candidate_quantity, domain)
        except EngEvaluationError:
            return None
    if not _candidate_in_domain(x_quantity, domain):
        return None

    symbolic_value = _simplify_decidable_abs(
        expression.subs(variable, candidate),
        context,
        overrides=fixed_overrides,
    )
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
        provenance=provenance,
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
        value_symbolic=_simplify_decidable_abs(
            expression, context, overrides=overrides
        ),
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


def _solve_continuous_extrema_exact(
    expression,
    variable,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None = None,
    source_label: str | None = None,
):
    expression = sp.simplify(sp.sympify(expression))
    variable = _analysis_variable(variable, expression)
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

    independent_factor, dependent_factor = expression.as_independent(
        variable,
        as_Add=False,
    )
    if (
        dependent_factor.func == sp.Abs
        and variable not in independent_factor.free_symbols
    ):
        inner_expression = sp.sympify(dependent_factor.args[0])
        cusp_points, cusp_intervals, cusp_unresolved = solve_roots_exact(
            inner_expression,
            variable,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
        )
        stationary_candidates = list(cusp_points)
        derivative_unresolved = bool(cusp_unresolved or cusp_intervals)

        inner_derivative = sp.simplify(sp.diff(inner_expression, variable))
        if variable in inner_derivative.free_symbols:
            smooth_points, smooth_intervals, smooth_unresolved = solve_roots_exact(
                inner_derivative,
                variable,
                domain,
                context,
                overrides=overrides,
                source_label=source_label,
            )
            stationary_candidates.extend(smooth_points)
            derivative_unresolved = bool(
                derivative_unresolved or smooth_unresolved or smooth_intervals
            )
        stationary_points = _deduplicate_root_points(stationary_candidates, domain)
    else:
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
            candidate_quantity=stationary.x_quantity,
            provenance=stationary.provenance,
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
        value_symbolic=_simplify_decidable_abs(
            expression, context, overrides=overrides
        ),
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
        value_symbolic=_simplify_decidable_abs(
            value_symbolic, context, overrides=overrides
        ),
        value_quantity=value_quantity,
        provenance="exact",
        side=side,
        roles=("boundary",),
        source_label=source_label,
    )
    return point, False, False, False


def _piecewise_selected_boundary_point(
    expression: sp.Expr,
    variable: sp.Symbol,
    boundary_symbolic: sp.Expr,
    boundary_quantity,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
    source_label: str | None,
) -> CharacteristicPoint | None:
    folded = sp.piecewise_fold(sp.sympify(expression))
    branch_expression = folded
    if isinstance(folded, sp.Piecewise):
        try:
            _, branch_expression = _select_piecewise_branch(
                folded,
                variable,
                boundary_quantity,
                context,
                overrides=overrides,
            )
        except EngEvaluationError:
            return None
    return _evaluate_extrema_candidate(
        sp.sympify(branch_expression),
        variable,
        sp.sympify(boundary_symbolic),
        domain,
        context,
        overrides=overrides,
        source_label=source_label,
        roles=("boundary",),
        candidate_quantity=boundary_quantity,
    )


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


def _extrema_point_with_value_quantity(
    point: CharacteristicPoint,
    value_quantity,
) -> CharacteristicPoint:
    return CharacteristicPoint(
        x_symbolic=point.x_symbolic,
        x_quantity=point.x_quantity,
        value_symbolic=point.value_symbolic,
        value_quantity=value_quantity,
        provenance=point.provenance,
        side=point.side,
        roles=point.roles,
        source_label=point.source_label,
    )


def _normalize_piecewise_zero_units(
    records: tuple[CharacteristicPoint | None, ...],
    context,
) -> tuple[CharacteristicPoint | None, ...]:
    canonical_unit = next(
        (
            point.value_quantity.units
            for point in records
            if point is not None
            and point.value_quantity is not None
            and not point.value_quantity.dimensionless
        ),
        None,
    )
    if canonical_unit is None:
        return records

    normalized: list[CharacteristicPoint | None] = []
    for point in records:
        if point is None or point.value_quantity is None:
            normalized.append(point)
            continue
        quantity = point.value_quantity
        if (
            quantity.dimensionless
            and _quantity_is_zero(quantity)
            and sp.simplify(point.value_symbolic) == 0
        ):
            point = _extrema_point_with_value_quantity(
                point,
                context.ureg.Quantity(0, canonical_unit),
            )
        normalized.append(point)
    return tuple(normalized)


def _piecewise_breakpoint_records(
    left_point: CharacteristicPoint | None,
    at_point: CharacteristicPoint | None,
    right_point: CharacteristicPoint | None,
    context,
) -> tuple[CharacteristicPoint, ...]:
    left_point, at_point, right_point = _normalize_piecewise_zero_units(
        (left_point, at_point, right_point),
        context,
    )
    if (
        left_point is not None
        and at_point is not None
        and right_point is not None
        and _same_extrema_value(
            left_point.value_quantity,
            at_point.value_quantity,
            context,
        )
        and _same_extrema_value(
            at_point.value_quantity,
            right_point.value_quantity,
            context,
        )
    ):
        return (at_point,)
    return tuple(
        point
        for point in (left_point, at_point, right_point)
        if point is not None
    )


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
    # One-sided limits are values the response approaches without reaching. They
    # never earn a global role themselves, but a limit beyond every attained
    # value proves the corresponding extreme is not attained by any point.
    side_magnitudes = [
        _extrema_magnitude_in_unit(point.value_quantity, canonical_unit, context)
        for point in points
        if point.side != "at" and point.value_quantity is not None
    ]
    scale = max(1.0, *(abs(value) for value in (*magnitudes, *side_magnitudes)))
    tolerance = 1e-12 * scale
    unattained_above = any(value > maximum + tolerance for value in side_magnitudes)
    unattained_below = any(value < minimum - tolerance for value in side_magnitudes)

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
            if (
                not unbounded_above
                and not unattained_above
                and math.isclose(magnitude, maximum, rel_tol=1e-12, abs_tol=tolerance)
            ):
                roles.append("global_max")
            if (
                not unbounded_below
                and not unattained_below
                and math.isclose(magnitude, minimum, rel_tol=1e-12, abs_tol=tolerance)
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

    for endpoint_symbolic, endpoint_quantity in (
        (domain.lower_symbolic, domain.lower_quantity),
        (domain.upper_symbolic, domain.upper_quantity),
    ):
        point = _piecewise_selected_boundary_point(
            expression,
            variable,
            endpoint_symbolic,
            endpoint_quantity,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
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

        at_point = _piecewise_selected_boundary_point(
            expression,
            variable,
            breakpoint_symbolic,
            breakpoint_quantity,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
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

        points.extend(
            _piecewise_breakpoint_records(
                left_point,
                at_point,
                right_point,
                context,
            )
        )

    # A region edge that is open *and* coincides with an analysis-domain bound has
    # no neighbouring region to pair with, so the loop above never reaches it. Its
    # one-sided limit is still the only description of how the response behaves
    # there, and without it an unattained supremum is invisible to role assignment.
    for region, side, edge_symbolic, edge_quantity, is_closed in (
        (
            regions[0],
            "right",
            regions[0].lower_symbolic,
            regions[0].lower_quantity,
            regions[0].lower_closed,
        ),
        (
            regions[-1],
            "left",
            regions[-1].upper_symbolic,
            regions[-1].upper_quantity,
            regions[-1].upper_closed,
        ),
    ):
        if is_closed:
            continue
        edge_point, edge_up, edge_down, edge_unresolved = _piecewise_one_sided_point(
            region,
            variable,
            sp.sympify(edge_symbolic),
            edge_quantity,
            context,
            side=side,
            overrides=overrides,
            source_label=source_label,
        )
        unbounded_above = unbounded_above or edge_up
        unbounded_below = unbounded_below or edge_down
        unresolved = unresolved or edge_unresolved
        if edge_point is not None:
            points.append(edge_point)

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
    variable = _analysis_variable(variable, expression)
    if not isinstance(variable, sp.Symbol):
        raise EngEvaluationError("extrema variable must be a symbolic identifier")

    resolved_overrides = context.unit_literal_overrides(expression, overrides)
    if expression.has(sp.Piecewise):
        return _solve_piecewise_extrema_exact(
            expression,
            variable,
            domain,
            context,
            overrides=resolved_overrides,
            source_label=source_label,
        )
    return _solve_continuous_extrema_exact(
        expression,
        variable,
        domain,
        context,
        overrides=resolved_overrides,
        source_label=source_label,
    )
