"""Shared helpers for the permanent EngCalc Quality Gate.

These helpers drive EngCalc through its ordinary public entry points only. The
numerical oracle here must stay independent of the machinery under test: it uses
plain floating-point arithmetic and must never import SymPy or call EngCalc's
solving helpers, because an oracle sharing the solver could fail in the same way
as the implementation and still report agreement.
"""

from __future__ import annotations

import math
from typing import Any

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell


def evaluate_cell(source: str) -> Any:
    """Evaluate one ``%%eng`` cell and return the last statement result."""
    engine = EngineeringEngine()
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


def characteristic_xs(result: Any, unit: str | None = None) -> list[float]:
    """Sorted characteristic abscissae, optionally converted to ``unit``."""
    values: list[float] = []
    for point in result.points:
        quantity = point.x_quantity
        if unit is not None:
            quantity = quantity.to(unit)
        values.append(float(quantity.magnitude))
    return sorted(values)


def role_xs(result: Any, role: str, unit: str | None = None) -> list[float]:
    """Sorted abscissae of every point carrying ``role``."""
    values: list[float] = []
    for point in result.points:
        if role not in point.roles:
            continue
        quantity = point.x_quantity
        if unit is not None:
            quantity = quantity.to(unit)
        values.append(float(quantity.magnitude))
    return sorted(values)


def assert_close_sequence(
    actual: list[float],
    expected: list[float],
    *,
    rel_tol: float = 1e-6,
    abs_tol: float = 1e-6,
) -> None:
    """Compare two ordered numeric sequences with an explicit tolerance."""
    assert len(actual) == len(expected), (actual, expected)
    for got, want in zip(actual, expected):
        assert math.isclose(got, want, rel_tol=rel_tol, abs_tol=abs_tol), (
            actual,
            expected,
        )


def bisect_monotone_quintic(
    b: float,
    c: float,
    *,
    lo: float = -50.0,
    hi: float = 50.0,
    iterations: int = 300,
) -> float:
    """Locate the unique real root of ``x**5 + b*x + c`` for ``b > 0``.

    With ``b > 0`` the derivative ``5*x**4 + b`` is strictly positive, so the
    quintic is strictly increasing and has exactly one real root. The count is
    therefore established analytically and the location by bisection, with no
    symbolic solver involved on either side.
    """
    if b <= 0:
        raise ValueError("b must be positive for the quintic to be monotone")

    def value(x: float) -> float:
        return x**5 + b * x + c

    while value(lo) > 0:
        lo *= 2.0
    while value(hi) < 0:
        hi *= 2.0

    for _ in range(iterations):
        midpoint = (lo + hi) / 2.0
        if value(lo) * value(midpoint) <= 0:
            hi = midpoint
        else:
            lo = midpoint

    return (lo + hi) / 2.0


def inequality_regions(result: Any) -> list[tuple[float, float, bool, bool]]:
    """Each reported region as (lower, upper, lower_closed, upper_closed)."""
    return [
        (
            float(interval.lower_quantity.magnitude),
            float(interval.upper_quantity.magnitude),
            interval.lower_closed,
            interval.upper_closed,
        )
        for interval in result.intervals
    ]


def inside_any_region(value: float, regions, tolerance: float = 0.0) -> bool:
    """Plain-arithmetic membership, deliberately not asking EngCalc anything."""
    for lower, upper, lower_closed, upper_closed in regions:
        after_start = value > lower + tolerance or (lower_closed and value >= lower - tolerance)
        before_end = value < upper - tolerance or (upper_closed and value <= upper + tolerance)
        if after_start and before_end:
            return True
    return False


def macaulay(x: float, offset: float, order: int) -> float:
    """`<x - a>^n`, from its definition rather than from EngCalc."""
    return (x - offset) ** order if x >= offset else 0.0
