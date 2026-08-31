import ast

import pytest
import sympy as sp

from engcalc_colab.characteristics import normalize_analysis_domain, solve_roots_exact
from engcalc_colab.numeric import NumericContext


def _assign(context: NumericContext, name: str, source: str):
    return context.assign(name, ast.parse(source, mode="eval"))


@pytest.mark.parametrize(
    ("condition_factory", "expected_upper_closed"),
    [
        (lambda x: x < 2, False),
        (lambda x: x <= 2, True),
    ],
)
def test_zero_interval_preserves_breakpoint_open_closed_topology(
    condition_factory,
    expected_upper_closed,
):
    context = NumericContext()
    x = sp.Symbol("x")
    expression = sp.Piecewise(
        (0, condition_factory(x)),
        (1, True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_roots_exact(expression, x, domain, context)

    assert points == ()
    assert len(intervals) == 1
    interval = intervals[0]
    assert interval.lower_quantity.magnitude == pytest.approx(0.0)
    assert interval.upper_quantity.magnitude == pytest.approx(2.0)
    assert interval.lower_closed is True
    assert interval.upper_closed is expected_upper_closed
    assert unresolved is False


def test_dimensional_piecewise_breakpoint_preserves_symbolic_root_and_zero_unit():
    context = NumericContext()
    _assign(context, "L", "6*m")
    _assign(context, "q", "12*kN/m")
    x, L, q = sp.symbols("x L q")
    expression = sp.Piecewise(
        (0, x < L / 2),
        (q * (x - 2 * L / 3), True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    points, intervals, unresolved = solve_roots_exact(expression, x, domain, context)

    assert len(points) == 1
    assert sp.simplify(points[0].x_symbolic - 2 * L / 3) == 0
    assert points[0].x_quantity.to("m").magnitude == pytest.approx(4.0)
    assert len(intervals) == 1
    interval = intervals[0]
    assert interval.lower_symbolic == 0
    assert sp.simplify(interval.upper_symbolic - L / 2) == 0
    assert interval.lower_quantity.to("m").magnitude == pytest.approx(0.0)
    assert interval.upper_quantity.to("m").magnitude == pytest.approx(3.0)
    assert interval.lower_closed is True
    assert interval.upper_closed is False
    assert interval.value_quantity.to("kN").magnitude == pytest.approx(0.0)
    assert unresolved is False
