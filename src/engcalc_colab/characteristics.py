from __future__ import annotations

import math

import mpmath as mp
from dataclasses import dataclass
from typing import Any

import sympy as sp
from pint.errors import DimensionalityError

from .errors import EngEvaluationError
from .models import CharacteristicInterval, CharacteristicPoint
from .piecewise import extract_symbolic_breakpoints


_FALLBACK_SCAN_COUNT = 1025
_FALLBACK_REL_RESIDUAL_TOL = 1e-9
_FALLBACK_X_DEDUP_REL_TOL = 1e-10


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


def _characteristic_literal_unit_overrides(
    context,
    expression: sp.Expr,
    overrides: dict[str, Any] | None,
) -> dict[str, Any]:
    """Resolve unit aliases that remain symbolic inside characteristic expressions.

    Symbolic formulas intentionally keep names such as ``m`` as SymPy symbols.
    During physical validation of a characteristic point, however, a unit literal
    such as ``7*m`` must be interpreted through the same Pint unit registry as
    numeric input. Explicit overrides and stored numeric values always win.
    """
    fixed = dict(overrides or {})
    for symbol in sp.sympify(expression).free_symbols:
        name = symbol.name
        if name in fixed or name in context.values:
            continue
        try:
            fixed[name] = context.resolve_target_unit_name(name)
        except EngEvaluationError:
            continue
    return fixed


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
    fixed_overrides = _characteristic_literal_unit_overrides(
        context,
        expression,
        overrides,
    )
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




def _fallback_response_quantity(
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
    try:
        magnitude = float(quantity.magnitude)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(magnitude):
        return None
    return quantity


def _fallback_magnitude_in_unit(quantity, canonical_unit, context):
    if quantity is None:
        return None
    if quantity.dimensionless and canonical_unit != context.ureg.dimensionless:
        try:
            magnitude = float(quantity.magnitude)
        except (TypeError, ValueError, OverflowError):
            return None
        if magnitude != 0.0:
            return None
        return 0.0
    try:
        converted = quantity.to(canonical_unit)
        magnitude = float(converted.magnitude)
    except (DimensionalityError, TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(magnitude):
        return None
    return magnitude


def _fallback_canonical_unit(quantities, context):
    for quantity in quantities:
        if quantity is not None and not quantity.dimensionless:
            return quantity.units
    for quantity in quantities:
        if quantity is not None:
            return quantity.units
    return context.ureg.dimensionless


def _fallback_root_point(
    expression: sp.Expr,
    variable: sp.Symbol,
    x_magnitude: float,
    domain: AnalysisDomain,
    context,
    canonical_unit,
    response_scale: float,
    *,
    overrides: dict[str, Any] | None,
    source_label: str | None,
) -> CharacteristicPoint | None:
    if not math.isfinite(x_magnitude):
        return None
    lower = float(domain.lower_quantity.to(domain.unit).magnitude)
    upper = float(domain.upper_quantity.to(domain.unit).magnitude)
    span = abs(upper - lower)
    x_tolerance = _FALLBACK_X_DEDUP_REL_TOL * max(1.0, span)
    if x_magnitude < lower - x_tolerance or x_magnitude > upper + x_tolerance:
        return None
    if x_magnitude < lower:
        x_magnitude = lower
    elif x_magnitude > upper:
        x_magnitude = upper

    x_quantity = context.ureg.Quantity(x_magnitude, domain.unit)
    value_quantity = _fallback_response_quantity(
        expression,
        variable,
        x_quantity,
        context,
        overrides=overrides,
    )
    residual = _fallback_magnitude_in_unit(value_quantity, canonical_unit, context)
    if residual is None:
        return None
    relative_residual = abs(residual) / max(1.0, response_scale)
    if relative_residual > _FALLBACK_REL_RESIDUAL_TOL:
        return None

    return CharacteristicPoint(
        x_symbolic=sp.Float(x_magnitude, 17),
        x_quantity=x_quantity,
        value_symbolic=sp.Float(residual, 17),
        value_quantity=value_quantity,
        provenance="numeric",
        side="at",
        roles=("root",),
        source_label=source_label,
    )


def _deduplicate_root_points(
    points: list[CharacteristicPoint],
    domain: AnalysisDomain,
) -> tuple[CharacteristicPoint, ...]:
    if not points:
        return ()
    points = sorted(
        points,
        key=lambda point: float(point.x_quantity.to(domain.unit).magnitude),
    )
    span = abs(
        float(domain.upper_quantity.to(domain.unit).magnitude)
        - float(domain.lower_quantity.to(domain.unit).magnitude)
    )
    tolerance = _FALLBACK_X_DEDUP_REL_TOL * max(1.0, span)
    unique: list[CharacteristicPoint] = []
    for point in points:
        if not unique:
            unique.append(point)
            continue
        current = float(point.x_quantity.to(domain.unit).magnitude)
        previous = float(unique[-1].x_quantity.to(domain.unit).magnitude)
        if math.isclose(current, previous, rel_tol=0.0, abs_tol=tolerance):
            if unique[-1].provenance == "numeric" and point.provenance == "exact":
                unique[-1] = point
            continue
        unique.append(point)
    return tuple(unique)


def _fallback_roots(
    expression: sp.Expr,
    variable: sp.Symbol,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None = None,
    source_label: str | None = None,
) -> tuple[CharacteristicPoint, ...]:
    expression = sp.sympify(expression)
    lower = float(domain.lower_quantity.to(domain.unit).magnitude)
    upper = float(domain.upper_quantity.to(domain.unit).magnitude)
    span = upper - lower
    if not math.isfinite(lower) or not math.isfinite(upper) or span <= 0:
        raise EngEvaluationError(
            "characteristic numerical fallback could not validate a solution set"
        )

    x_magnitudes = tuple(
        lower + span * (index / (_FALLBACK_SCAN_COUNT - 1))
        for index in range(_FALLBACK_SCAN_COUNT)
    )
    quantities = tuple(
        _fallback_response_quantity(
            expression,
            variable,
            context.ureg.Quantity(x_magnitude, domain.unit),
            context,
            overrides=overrides,
        )
        for x_magnitude in x_magnitudes
    )
    canonical_unit = _fallback_canonical_unit(quantities, context)
    values = tuple(
        _fallback_magnitude_in_unit(quantity, canonical_unit, context)
        for quantity in quantities
    )
    finite_values = [value for value in values if value is not None]
    if not finite_values:
        raise EngEvaluationError(
            "characteristic numerical fallback could not validate a solution set"
        )
    response_scale = max(abs(value) for value in finite_values)

    def residual_callback(value):
        x_magnitude = float(value)
        quantity = _fallback_response_quantity(
            expression,
            variable,
            context.ureg.Quantity(x_magnitude, domain.unit),
            context,
            overrides=overrides,
        )
        residual = _fallback_magnitude_in_unit(quantity, canonical_unit, context)
        if residual is None or not math.isfinite(residual):
            raise ValueError("non-finite characteristic residual")
        return residual

    candidate_magnitudes: list[float] = []
    denominator = max(1.0, response_scale)

    # Grid seeds already satisfying the residual contract.
    for x_magnitude, value in zip(x_magnitudes, values):
        if value is None:
            continue
        if abs(value) / denominator <= _FALLBACK_REL_RESIDUAL_TOL:
            candidate_magnitudes.append(x_magnitude)

    def refine(left: float, right: float):
        if not (math.isfinite(left) and math.isfinite(right)) or left == right:
            return
        try:
            root = mp.findroot(
                residual_callback,
                (mp.mpf(str(left)), mp.mpf(str(right))),
                tol=mp.mpf("1e-14"),
                maxsteps=100,
            )
            root_float = float(root)
        except (ValueError, TypeError, ZeroDivisionError, OverflowError, ArithmeticError):
            return
        if math.isfinite(root_float):
            candidate_magnitudes.append(root_float)

    # Sign-changing brackets are guaranteed to remain inside this one continuous
    # AnalysisDomain. Piecewise callers invoke this once per ContinuousRegion.
    for index in range(_FALLBACK_SCAN_COUNT - 1):
        left_value = values[index]
        right_value = values[index + 1]
        if left_value is None or right_value is None:
            continue
        if left_value * right_value < 0.0:
            refine(x_magnitudes[index], x_magnitudes[index + 1])

    # Even-multiplicity roots do not change sign. Strict local minima of |f|
    # supply deterministic neighboring starting values for the same refinement.
    for index in range(1, _FALLBACK_SCAN_COUNT - 1):
        left_value = values[index - 1]
        center_value = values[index]
        right_value = values[index + 1]
        if left_value is None or center_value is None or right_value is None:
            continue
        if abs(center_value) < abs(left_value) and abs(center_value) < abs(right_value):
            refine(x_magnitudes[index - 1], x_magnitudes[index + 1])

    validated: list[CharacteristicPoint] = []
    for x_magnitude in candidate_magnitudes:
        point = _fallback_root_point(
            expression,
            variable,
            x_magnitude,
            domain,
            context,
            canonical_unit,
            response_scale,
            overrides=overrides,
            source_label=source_label,
        )
        if point is not None:
            validated.append(point)

    ordered = _deduplicate_root_points(validated, domain)
    if not ordered:
        raise EngEvaluationError(
            "characteristic numerical fallback could not validate a solution set"
        )
    return ordered

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
            return (
                _fallback_roots(
                    expression,
                    variable,
                    domain,
                    context,
                    overrides=overrides,
                    source_label=source_label,
                ),
                (),
                False,
            )

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
        return _deduplicate_root_points(points, domain), (), False

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
        if unresolved:
            region_domain = AnalysisDomain(
                lower_symbolic=region.lower_symbolic,
                upper_symbolic=region.upper_symbolic,
                lower_quantity=region.lower_quantity,
                upper_quantity=region.upper_quantity,
                unit=domain.unit,
            )
            fallback_points = _fallback_roots(
                branch_expression,
                variable,
                region_domain,
                context,
                overrides=overrides,
                source_label=source_label,
            )
            for point in fallback_points:
                if _candidate_in_region(point.x_quantity, region, domain):
                    points.append(point)
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

    ordered_points = _deduplicate_root_points(points, domain)
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




def _evaluate_numeric_intersection_candidate(
    left_expression: sp.Expr,
    right_expression: sp.Expr,
    variable: sp.Symbol,
    root_point: CharacteristicPoint,
    context,
    *,
    overrides: dict[str, Any] | None,
    left_label: str | None,
    right_label: str | None,
) -> CharacteristicPoint | None:
    pair = _evaluate_response_pair(
        left_expression,
        right_expression,
        variable,
        root_point.x_quantity,
        context,
        overrides=overrides,
    )
    if pair is None:
        return None
    left_quantity, right_quantity = pair
    try:
        left_magnitude = float(left_quantity.magnitude)
        right_magnitude = float(right_quantity.to(left_quantity.units).magnitude)
    except (DimensionalityError, TypeError, ValueError, OverflowError):
        return None
    scale = max(1.0, abs(left_magnitude), abs(right_magnitude))
    if not math.isclose(
        left_magnitude,
        right_magnitude,
        rel_tol=_FALLBACK_REL_RESIDUAL_TOL,
        abs_tol=_FALLBACK_REL_RESIDUAL_TOL * scale,
    ):
        return None
    symbolic_value = sp.simplify(
        sp.sympify(left_expression).subs(variable, root_point.x_symbolic)
    )
    return CharacteristicPoint(
        x_symbolic=root_point.x_symbolic,
        x_quantity=root_point.x_quantity,
        value_symbolic=symbolic_value,
        value_quantity=left_quantity,
        provenance="numeric",
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
        if unresolved:
            region_domain = AnalysisDomain(
                lower_symbolic=region.lower_symbolic,
                upper_symbolic=region.upper_symbolic,
                lower_quantity=region.lower_quantity,
                upper_quantity=region.upper_quantity,
                unit=domain.unit,
            )
            fallback_points = _fallback_roots(
                difference,
                variable,
                region_domain,
                context,
                overrides=overrides,
                source_label=_intersection_source_label(left_label, right_label),
            )
            for root_point in fallback_points:
                if not _candidate_strictly_inside_intersection_region(
                    root_point.x_quantity,
                    region,
                    domain,
                ):
                    continue
                point = _evaluate_numeric_intersection_candidate(
                    left_expression,
                    right_expression,
                    variable,
                    root_point,
                    context,
                    overrides=overrides,
                    left_label=left_label,
                    right_label=right_label,
                )
                if point is not None:
                    points.append(point)
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
    ordered_points = _deduplicate_root_points(points, domain)
    visible_points = tuple(
        point
        for point in ordered_points
        if not any(
            _point_is_covered_by_interval(point, interval, domain)
            for interval in merged_intervals
        )
    )
    return visible_points, merged_intervals, unresolved_any



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
    fixed_overrides = dict(overrides or {})
    candidate = sp.sympify(candidate)
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