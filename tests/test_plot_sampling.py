import sympy as sp

from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.numeric import NumericContext


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

    xs, ys = context.sample_symbolic(
        expression, "x", 0 * context.ureg.m, 4 * context.ureg.m, count=201
    )

    assert len(xs) == 201
    assert len(ys) == 201
    assert xs[0].to("m").magnitude == 0
    assert xs[-1].to("m").magnitude == 4
    assert ys[0].to("tonf").magnitude == 7.0


def test_existing_plot_variable_value_is_not_mutated_by_sampling():
    context = NumericContext()
    context.values["x"] = 2.5 * context.ureg.m
    context.values["q"] = 2.8 * context.ureg.tonf / context.ureg.m
    context.values["L"] = 4 * context.ureg.m
    q, L, x = sp.symbols("q L x")

    context.sample_symbolic(
        5*q*L/8 - q*x,
        "x",
        0 * context.ureg.m,
        4 * context.ureg.m,
        count=201,
    )

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
