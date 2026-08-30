from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import sympy as sp
from pint.errors import DimensionalityError

from .errors import EngEvaluationError
from .models import CharacteristicInterval, CharacteristicPoint
from .piecewise import extract_symbolic_breakpoints


@dataclass(frozen=True)
class AnalysisDomain:
    lower_symbolic: sp.Expr
    upper_symbolic: sp.Expr
    lower_quantity: Any
    upper_quantity: Any
    unit: Any


@dataclass(frozen=True)
class ContinuousRegion:
    expression: sp.Expr
    lower_symbolic: sp.Expr
    upper_symbolic: sp.Expr
    lower_quantity: Any
    upper_quantity: Any
    lower_closed: bool
    upper_closed: bool


def _has_explicit_nonfinite_value(expression: sp.Expr) -> bool:
    expression = sp.sympify(expression)
    return expression.has(sp.oo, -sp.oo, sp.zoo, sp.nan) or expression.is_finite is False


def _evaluate_domain_bound(context, expression: sp.Expr):
    if _has_explicit_nonfinite_value(expression):
        raise EngEvaluationError("characteristic domain bounds must be finite")
    try:
        _, quantity = context.evaluate_symbolic(expression)
    except EngEvaluationError as exc:
        raise EngEvaluationError(
            "characteristic domain bound must be numerically resolvable: " + str(exc)
        ) from None
    try:
        magnitude = float(quantity.magnitude)
    except (TypeError, ValueError, OverflowError) as exc:
        raise EngEvaluationError("characteristic domain bounds must be finite") from exc
    if not math.isfinite(magnitude):
        raise EngEvaluationError("characteristic domain bounds must be finite")
    return quantity


def normalize_analysis_domain(
    context,
    lower_expression,
    upper_expression,
) -> AnalysisDomain:
    lower_symbolic = sp.sympify(lower_expression)
    upper_symbolic = sp.sympify(upper_expression)
    lower = _evaluate_domain_bound(context, lower_symbolic)
    upper = _evaluate_domain_bound(context, upper_symbolic)

    try:
        lower, upper = context.normalize_plot_bounds(lower, upper)
    except EngEvaluationError as exc:
        message = str(exc)
        if "incompatible units" in message:
            raise EngEvaluationError(
                "characteristic domain bounds have incompatible units"
            ) from None
        if "greater than start" in message:
            raise EngEvaluationError(
                "characteristic domain requires lower < upper"
            ) from None
        raise

    lower_magnitude = float(lower.magnitude)
    upper_magnitude = float(upper.magnitude)
    if not math.isfinite(lower_magnitude) or not math.isfinite(upper_magnitude):
        raise EngEvaluationError("characteristic domain bounds must be finite")
    if not lower_magnitude < upper_magnitude:
        raise EngEvaluationError("characteristic domain requires lower < upper")

    return AnalysisDomain(
        lower_symbolic=lower_symbolic,
        upper_symbolic=upper_symbolic,
        lower_quantity=lower,
        upper_quantity=upper,
        unit=lower.units,
    )


def _exact_real_solution_set(expression: sp.Expr, variable: sp.Symbol):
    equation = sp.Eq(expression, 0)
    try:
        solution_set = sp.solveset(equation, variable, domain=sp.S.Reals)
    except (NotImplementedError, ValueError, TypeError):
        solution_set = None

    if solution_set is sp.S.EmptySet:
        return (), False
    if isinstance(solution_set, sp.FiniteSet):
        return tuple(solution_set), False
    if solution_set is sp.S.Reals:
        return (), False

    try:
        solutions = sp.solve(equation, variable)
    except (NotImplementedError, ValueError, TypeError):
        return (), True

    if not solutions:
        return (), True
    if isinstance(solutions, dict):
        solutions = [solutions.get(variable)]
    if not isinstance(solutions, (list, tuple, set, sp.FiniteSet)):
        solutions = [solutions]

    candidates = []
    for candidate in solutions:
        if candidate is None:
            continue
        candidate = sp.sympify(candidate)
        if variable in candidate.free_symbols:
            return (), True
        if candidate.is_real is False:
            continue
        candidates.append(candidate)
    return tuple(candidates), False


def _normalize_candidate_quantity(context, quantity, domain: AnalysisDomain):
    if quantity.dimensionless and not domain.lower_quantity.dimensionless:
        if float(quantity.magnitude) != 0.0:
            raise EngEvaluationError("root location has incompatible units")
        quantity = context.ureg.Quantity(0, domain.unit)
    try:
        return quantity.to(domain.unit)
    except DimensionalityError as exc:
        raise EngEvaluationError("root location has incompatible units") from exc


def _candidate_in_domain(quantity, domain: AnalysisDomain) -> bool:
    magnitude = float(quantity.to(domain.unit).magnitude)
    lower = float(domain.lower_quantity.magnitude)
    upper = float(domain.upper_quantity.magnitude)
    tolerance = 1e-12 * max(1.0, abs(lower), abs(upper), abs(upper - lower))
    return lower - tolerance <= magnitude <= upper + tolerance


def _evaluate_root_candidate(
    expression: sp.Expr,
    variable: sp.Symbol,
    candidate: sp.Expr,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
    source_label: str | None,
) -> CharacteristicPoint | None:
    fixed_overrides = dict(overrides or {})
    try:
        _, x_quantity = context.evaluate_symbolic(candidate, overrides=fixed_overrides)
    except EngEvaluationError:
        return None
    x_quantity = _normalize_candidate_quantity(context, x_quantity, domain)
    if not _candidate_in_domain(x_quantity, domain):
        return None

    symbolic_value = sp.simplify(expression.subs(variable, candidate))
    exact_zero = symbolic_value == 0 or symbolic_value.is_zero is True

    sample_overrides = dict(fixed_overrides)
    sample_overrides[variable.name] = x_quantity
    try:
        _, value_quantity = context.evaluate_symbolic(
            expression,
            overrides=sample_overrides,
        )
    except EngEvaluationError:
        return None

    if not exact_zero:
        try:
            numeric_zero = float(value_quantity.magnitude) == 0.0
        except (TypeError, ValueError, OverflowError):
            numeric_zero = False
        if not numeric_zero:
            return None

    return CharacteristicPoint(
        x_symbolic=candidate,
        x_quantity=x_quantity,
        value_symbolic=sp.Integer(0) if exact_zero else symbolic_value,
        value_quantity=value_quantity,
        provenance="exact",
        side="at",
        roles=("root",),
        source_label=source_label,
    )


def _ordered_unique_points(
    points: list[CharacteristicPoint],
    domain: AnalysisDomain,
) -> tuple[CharacteristicPoint, ...]:
    points.sort(
        key=lambda point: float(point.x_quantity.to(domain.unit).magnitude)
    )
    unique: list[CharacteristicPoint] = []
    span = abs(
        float(domain.upper_quantity.magnitude)
        - float(domain.lower_quantity.magnitude)
    )
    tolerance = 1e-12 * max(1.0, span)
    for point in points:
        if unique:
            current = float(point.x_quantity.to(domain.unit).magnitude)
            previous = float(unique[-1].x_quantity.to(domain.unit).magnitude)
            if math.isclose(current, previous, rel_tol=1e-12, abs_tol=tolerance):
                continue
        unique.append(point)
    return tuple(unique)


def _normalize_piecewise_breakpoint_quantity(
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
