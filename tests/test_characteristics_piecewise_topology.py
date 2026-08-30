import pytest
import sympy as sp

from engcalc_colab.characteristics import normalize_analysis_domain, solve_roots_exact
from engcalc_colab.numeric import NumericContext


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
