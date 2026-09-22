"""How a plot samples its response.

Four of these contracts were written in 0.3.0 against `NumericContext.sample_symbolic`,
the sampler of the first native plot. Plotting has sampled through
`build_plot_sample_points` and `sample_symbolic_points` since piecewise breakpoints
arrived, and 0.4.0 kept the old method only as a wrapper for these tests, so they held a
path no page used. They hold the live path now and the old method is gone.

Measured before the move, by breaking the live sampler and running the whole suite: other
contracts already caught an override leaking into the context, the plot variable being
written into it, and a missing last point. Nothing caught a fixed value of the same name
outranking the plot variable - that mutant passed all 2541. The fourth contract below is
the first to hold it on the path the page takes.
"""

import ast

import pytest
import sympy as sp

from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.numeric import NumericContext


def _sampled(context, expression, start, end, count, overrides=None):
    points = context.build_plot_sample_points(
        [(expression, overrides)], "x", start, end, count=count
    )
    return points, context.sample_symbolic_points(expression, "x", points, overrides=overrides)


def test_dimensionless_zero_is_promoted_to_dimensional_end_unit():
    context = NumericContext()
    start, end = context.normalize_plot_bounds(
        context.ureg.Quantity(0),
        4 * context.ureg.m,
    )
    assert start.to("m").magnitude == 0
    assert end.to("m").magnitude == 4
    assert start.units == end.units


def test_sampling_contains_201_points_and_both_endpoints():
    context = NumericContext()
    context.values["q"] = 2.8 * context.ureg.tonf / context.ureg.m
    context.values["L"] = 4 * context.ureg.m
    q, L, x = sp.symbols("q L x")
    expression = 5*q*L/8 - q*x

    xs, ys = _sampled(context, expression, 0 * context.ureg.m, 4 * context.ureg.m, 201)

    assert len(xs) == 201
    assert len(ys) == 201
    assert xs[0].to("m").magnitude == 0
    assert xs[-1].to("m").magnitude == 4
    assert ys[0].to("tonf").magnitude == pytest.approx(7.0)


def test_sampling_merges_fixed_parameter_override_without_mutating_context():
    context = NumericContext()
    context.assign("q", ast.parse("2.8*tonf/m", mode="eval"))
    q, x = sp.symbols("q x")
    override = 5 * context.ureg.kN / context.ureg.m

    xs, ys = _sampled(
        context, q*x, 0 * context.ureg.m, 2 * context.ureg.m, 201, overrides={"q": override}
    )

    assert ys[-1].to("kN").magnitude == pytest.approx(10.0)
    assert context.get("q").to("tonf/m").magnitude == pytest.approx(2.8)


def test_plot_variable_sample_wins_over_same_name_in_fixed_overrides():
    context = NumericContext()
    x = sp.Symbol("x")

    xs, ys = _sampled(
        context, x, 0 * context.ureg.m, 2 * context.ureg.m, 3, overrides={"x": 99 * context.ureg.m}
    )

    assert [value.to("m").magnitude for value in ys] == pytest.approx([0, 1, 2])


def test_existing_plot_variable_value_is_not_mutated_by_sampling():
    context = NumericContext()
    context.values["x"] = 2.5 * context.ureg.m
    context.values["q"] = 2.8 * context.ureg.tonf / context.ureg.m
    context.values["L"] = 4 * context.ureg.m
    q, L, x = sp.symbols("q L x")

    _sampled(context, 5*q*L/8 - q*x, 0 * context.ureg.m, 4 * context.ureg.m, 201)

    assert context.values["x"].to("m").magnitude == 2.5


def test_incompatible_plot_bounds_fail_concisely():
    context = NumericContext()
    try:
        context.normalize_plot_bounds(0 * context.ureg.m, 4 * context.ureg.s)
    except EngEvaluationError as exc:
        assert "plot bounds have incompatible units" in str(exc)
    else:
        raise AssertionError("expected EngEvaluationError")


def test_plot_end_must_be_greater_than_start():
    context = NumericContext()
    try:
        context.normalize_plot_bounds(4 * context.ureg.m, 4 * context.ureg.m)
    except EngEvaluationError as exc:
        assert "plot end must be greater than start" in str(exc)
    else:
        raise AssertionError("expected EngEvaluationError")
