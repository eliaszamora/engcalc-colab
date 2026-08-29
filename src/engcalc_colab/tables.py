from __future__ import annotations

import math

from pint.errors import DimensionalityError

from .errors import EngEvaluationError
from .numeric import NumericContext


_COUNT_ERROR = "table count must be a dimensionless integer >= 2"
_RANGE_ERROR = "table range endpoints have incompatible units"
_POINTS_ERROR = "table points have incompatible units"
_AMBIGUOUS_POINT_ERROR = (
    "nonzero dimensionless table point cannot be mixed with dimensional points. "
    "Use table(M(x), x, [0, 1, 2], m) to declare the point unit once"
)


def _as_quantity(context: NumericContext, value):
    return context._as_quantity(value)


def _normalize_count(context: NumericContext, count) -> int:
    if isinstance(count, bool):
        raise EngEvaluationError(_COUNT_ERROR)

    quantity = _as_quantity(context, count)
    if not quantity.dimensionless:
        raise EngEvaluationError(_COUNT_ERROR)

    try:
        magnitude = float(quantity.to_base_units().magnitude)
    except (TypeError, ValueError, OverflowError) as exc:
        raise EngEvaluationError(_COUNT_ERROR) from exc

    if not math.isfinite(magnitude) or not magnitude.is_integer():
        raise EngEvaluationError(_COUNT_ERROR)

    normalized = int(magnitude)
    if normalized < 2:
        raise EngEvaluationError(_COUNT_ERROR)
    return normalized


def normalize_uniform_points(
    context: NumericContext,
    lower,
    upper,
    count,
):
    """Return a unit-normalized uniform table grid, preserving range direction."""
    normalized_count = _normalize_count(context, count)
    lower_quantity = _as_quantity(context, lower)
    upper_quantity = _as_quantity(context, upper)

    if lower_quantity.dimensionless and not upper_quantity.dimensionless:
        if float(lower_quantity.magnitude) != 0.0:
            raise EngEvaluationError(_RANGE_ERROR)
        lower_quantity = context.ureg.Quantity(0, upper_quantity.units)
    elif upper_quantity.dimensionless and not lower_quantity.dimensionless:
        if float(upper_quantity.magnitude) != 0.0:
            raise EngEvaluationError(_RANGE_ERROR)
        upper_quantity = context.ureg.Quantity(0, lower_quantity.units)

    try:
        upper_quantity = upper_quantity.to(lower_quantity.units)
    except DimensionalityError as exc:
        raise EngEvaluationError(_RANGE_ERROR) from exc

    delta = upper_quantity - lower_quantity
    return tuple(
        lower_quantity + delta * (index / (normalized_count - 1))
        for index in range(normalized_count)
    )


def normalize_explicit_points(
    context: NumericContext,
    points,
    declared_unit=None,
):
    """Normalize explicit table points without mutating the numeric context."""
    quantities = tuple(_as_quantity(context, point) for point in points)

    if declared_unit is not None:
        normalized = []
        for quantity in quantities:
            if quantity.dimensionless:
                normalized.append(
                    context.ureg.Quantity(quantity.magnitude, declared_unit)
                )
                continue
            try:
                normalized.append(quantity.to(declared_unit))
            except DimensionalityError as exc:
                raise EngEvaluationError(_POINTS_ERROR) from exc
        return tuple(normalized)

    dimensional = next(
        (quantity for quantity in quantities if not quantity.dimensionless),
        None,
    )
    if dimensional is None:
        return quantities

    canonical_unit = dimensional.units
    normalized = []
    for quantity in quantities:
        if quantity.dimensionless:
            if float(quantity.magnitude) != 0.0:
                raise EngEvaluationError(_AMBIGUOUS_POINT_ERROR)
            normalized.append(context.ureg.Quantity(0, canonical_unit))
            continue
        try:
            normalized.append(quantity.to(canonical_unit))
        except DimensionalityError as exc:
            raise EngEvaluationError(_POINTS_ERROR) from exc
    return tuple(normalized)
