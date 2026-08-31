"""Guard against over-claiming exact completeness for symbolic polynomials.

A polynomial response can contain a factor that ``solve()`` resolves and another
factor that remains a ``ConditionSet`` until registered parameters are given
numeric values. Exact discovery must remain incomplete in that case so the
numeric fallback can recover the unresolved real roots.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import RootsResult
from engcalc_colab.parser import parse_cell


def _run(source: str):
    engine = EngineeringEngine()
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


def test_symbolic_polynomial_partial_solve_does_not_suppress_fallback_roots():
    result = _run(
        """
a := 0
b := -1
f(x) = (x - a)*(x^5 + b*x + 1)
roots(f(x), x, -2, 2)
"""
    )

    assert isinstance(result, RootsResult)
    magnitudes = sorted(float(point.x_quantity.magnitude) for point in result.points)
    assert magnitudes == pytest.approx([-1.1673039782614187, 0.0], rel=1e-9, abs=1e-10)
    assert {point.provenance for point in result.points} == {"exact", "numeric"}
