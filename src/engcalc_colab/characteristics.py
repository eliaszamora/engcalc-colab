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
