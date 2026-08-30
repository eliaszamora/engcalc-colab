import pytest
from matplotlib.collections import PolyCollection

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot


def eval_cell(engine, source):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def define_jump(engine, operator="<"):
    eval_cell(
        engine,
        f"q(x) = piecewise(q1, x {operator} a, q2, x <= L, 0)\n"
        "q1 := 8*kN/m\nq2 := 4*kN/m\na := 2.345*m\nL := 6*m",
    )


def response_lines(axis):
    return [line for line in axis.lines if line.get_linewidth() >= 1.9]


def test_piecewise_jump_is_split_without_polyline_bridge_for_right_owned_breakpoint():
    engine = EngineeringEngine()
    define_jump(engine, "<")
    result = eval_cell(engine, "plot(q(x), x, 0, L)")[-1]
    breakpoint_index = next(
        index for index, point in enumerate(result.x_values)
        if point.to("m").magnitude == pytest.approx(2.345, abs=1e-12)
    )
    assert result.series[0].segment_starts == (breakpoint_index,)
    figure = render_plot(result)
    axis = figure.axes[0]
    lines = response_lines(axis)
    assert len(lines) == 2
    assert max(lines[0].get_xdata()) < 2.345
    assert min(lines[1].get_xdata()) == pytest.approx(2.345)
    assert len([item for item in axis.collections if isinstance(item, PolyCollection)]) == 2


def test_piecewise_left_owned_breakpoint_splits_after_exact_endpoint():
    engine = EngineeringEngine()
    define_jump(engine, "<=")
    result = eval_cell(engine, "plot(q(x), x, 0, L)")[-1]
    breakpoint_index = next(
        index for index, point in enumerate(result.x_values)
        if point.to("m").magnitude == pytest.approx(2.345, abs=1e-12)
    )
    assert result.series[0].segment_starts == (breakpoint_index + 1,)
    figure = render_plot(result)
    lines = response_lines(figure.axes[0])
    assert max(lines[0].get_xdata()) == pytest.approx(2.345)
    assert min(lines[1].get_xdata()) > 2.345


def test_piecewise_continuous_transition_is_still_segmented_without_changing_extrema():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "q(x) = piecewise(q1*x/a, x < a, q1, x <= L, 0)\n"
        "q1 := 8*kN/m\na := 2.345*m\nL := 6*m",
    )
    result = eval_cell(engine, "plot(q(x), x, 0, L)")[-1]
    figure = render_plot(result)
    assert len(result.series[0].segment_starts) >= 1
    assert len(response_lines(figure.axes[0])) >= 2
    assert len(figure.axes[0].texts) >= 1


def test_piecewise_moment_remains_positive_downward_and_characteristics_survive():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M(x) = piecewise(M1, x < a, M2, x <= L, 0)\n"
        "M1 := 8*kN*m\nM2 := -4*kN*m\na := 2.345*m\nL := 6*m",
    )
    result = eval_cell(engine, "plot(M(x), x, 0, L)")[-1]
    figure = render_plot(result)
    axis = figure.axes[0]
    assert axis.yaxis_inverted()
    assert len(axis.texts) >= 2
    assert len(response_lines(axis)) >= 2


def test_piecewise_multi_series_segments_keep_one_legend_identity_per_series():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "qA(x) = piecewise(q1, x < a, 0)\n"
        "qB(x) = piecewise(q2, x < b, 0)\n"
        "q1 := 8*kN/m\nq2 := 4*kN/m\n"
        "a := 2.345*m\nb := 4.567*m\nL := 6*m",
    )
    result = eval_cell(engine, "plot(qA(x), qB(x), x, 0, L)")[-1]
    figure = render_plot(result)
    legend = figure.axes[0].get_legend()
    labels = [text.get_text() for text in legend.get_texts()]
    assert labels == ["qA(x)", "qB(x)"]
    assert len(response_lines(figure.axes[0])) == 4


def test_piecewise_envelope_sources_and_fill_are_segmented_at_union_breakpoints():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "q(x) = piecewise(q1, x < a, 0)\n"
        "q1 := 8*kN/m\nL := 6*m",
    )
    result = eval_cell(
        engine,
        "envelope(q(x), x, 0, L, a=[2.345*m, 4.567*m])",
    )[-1]
    figure = render_plot(result)
    fills = [item for item in figure.axes[0].collections if isinstance(item, PolyCollection)]
    assert result.series[0].segment_starts
    assert len(fills) >= 3
