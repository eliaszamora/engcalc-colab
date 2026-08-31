from __future__ import annotations

import math
from typing import Any

import mpmath as mp
import sympy as sp
from pint.errors import DimensionalityError

from ..errors import EngEvaluationError
from ..models import CharacteristicPoint
from .domain import AnalysisDomain


_FALLBACK_SCAN_COUNT = 1025


_FALLBACK_REL_RESIDUAL_TOL = 1e-9


_FALLBACK_X_DEDUP_REL_TOL = 1e-10


def _deduplicate_root_points(points, domain):
    from .candidates import _deduplicate_root_points as deduplicate

    return deduplicate(points, domain)


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
