from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import sympy as sp
from pint.errors import DimensionalityError

from .errors import EngEvaluationError
from .models import CharacteristicPoint


@dataclass(frozen=True)
class AnalysisDomain:
    lower_symbolic: sp.Expr
    upper_symbolic: sp.Expr
    lower_quantity: Any
    upper_quantity: Any
    unit: Any


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
        # Infinite zero loci are represented explicitly by Task 3, together with
        # Piecewise interval ownership. Do not invent sampled roots here.
        return (), (), False

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
