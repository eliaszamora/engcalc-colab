from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import sympy as sp

from ..errors import EngEvaluationError


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


def _analysis_variable(variable, *expressions):
    if isinstance(variable, sp.Symbol):
        return variable
    if not isinstance(variable, str):
        return variable
    for expression in expressions:
        symbols = sorted(
            (
                item
                for item in sp.sympify(expression).free_symbols
                if item.name == variable
            ),
            key=sp.default_sort_key,
        )
        if symbols:
            return symbols[0]
    return sp.Symbol(variable, real=True)


def _has_explicit_nonfinite_value(expression: sp.Expr) -> bool:
    expression = sp.sympify(expression)
    return expression.has(sp.oo, -sp.oo, sp.zoo, sp.nan) or expression.is_finite is False


def _evaluate_domain_bound(context, expression: sp.Expr):
    if _has_explicit_nonfinite_value(expression):
        raise EngEvaluationError("characteristic domain bounds must be finite")
    try:
        _, quantity = context.evaluate_symbolic(
            expression,
            overrides=context.unit_literal_overrides(expression),
        )
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
    *,
    lower_quantity=None,
    upper_quantity=None,
) -> AnalysisDomain:
    lower_symbolic = sp.sympify(lower_expression)
    upper_symbolic = sp.sympify(upper_expression)
    lower = (
        lower_quantity
        if lower_quantity is not None
        else _evaluate_domain_bound(context, lower_symbolic)
    )
    upper = (
        upper_quantity
        if upper_quantity is not None
        else _evaluate_domain_bound(context, upper_symbolic)
    )

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


def _quantity_is_zero(quantity) -> bool:
    try:
        return float(quantity.magnitude) == 0.0
    except (TypeError, ValueError, OverflowError):
        return False


def denominator_scan(expression: sp.Expr, variable: sp.Symbol, domain: AnalysisDomain):
    """What a denominator of `expression` does between the domain's ends, by its numbers:
    `("pole", x)` where it reaches zero - a change of sign, or a dip to nothing (`sin(x)^2`
    touches zero without changing sign) - `("clear", None)` when it stays well away from
    zero everywhere, `(None, None)` when it cannot be told (another symbol, a unit, a value
    that is not a number). Used where SymPy's own account of the singularities is a family
    it cannot place (`sqrt(n π)` for `1/sin(x^2)`) and the analysis would otherwise give
    up (N6h, 0.53.0)."""
    try:
        lower = float(domain.lower_quantity.to(domain.unit).magnitude)
        upper = float(domain.upper_quantity.to(domain.unit).magnitude)
        denominator = sp.denom(sp.together(expression))
        if denominator.free_symbols != {variable}:
            return None, None
        values = sp.lambdify(variable, denominator, "math")
        steps = 4000
        xs = [lower + (upper - lower) * step / steps for step in range(steps + 1)]
        ys = [float(values(x)) for x in xs]
    except Exception:  # noqa: BLE001 - not told rather than told wrong
        return None, None
    if not all(math.isfinite(y) for y in ys):
        return None, None
    largest = max(abs(y) for y in ys)
    if largest == 0:
        return "pole", (lower + upper) / 2
    for index in range(1, len(ys)):
        if ys[index - 1] == 0 or ys[index - 1] * ys[index] < 0:
            return "pole", (xs[index - 1] + xs[index]) / 2
    smallest = min(range(len(ys)), key=lambda index: abs(ys[index]))
    if abs(ys[smallest]) < 1e-6 * largest:
        return "pole", xs[smallest]
    if abs(ys[smallest]) > 1e-3 * largest:
        return "clear", None
    return None, None
