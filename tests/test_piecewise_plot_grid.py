import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import PlotResult
from engcalc_colab.parser import parse_cell


def eval_cell(engine, source):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def x_magnitudes(result):
    return [point.to("m").magnitude for point in result.x_values]


def test_piecewise_plot_augments_201_point_grid_with_exact_breakpoint():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "q(x) = piecewise(q1, x < a, q2, x <= L, 0)\n"
        "q1 := 8*kN/m\nq2 := 4*kN/m\na := 2.345*m\nL := 6*m",
    )

    result = eval_cell(engine, "plot(q(x), x, 0, L)")[-1]
    xs = x_magnitudes(result)

    assert isinstance(result, PlotResult)
    assert len(xs) == 202
    assert any(value == pytest.approx(2.345, abs=1e-12) for value in xs)
    assert len(result.series[0].y_values) == len(result.x_values)


def test_piecewise_multi_series_uses_union_of_breakpoints_on_one_shared_grid():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "qA(x) = piecewise(q1, x < a, 0)\n"
        "qB(x) = piecewise(q2, x < b, 0)\n"
        "q1 := 8*kN/m\nq2 := 4*kN/m\n"
        "a := 2.345*m\nb := 4.567*m\nL := 6*m",
    )

    result = eval_cell(engine, "plot(qA(x), qB(x), x, 0, L)")[-1]
    xs = x_magnitudes(result)

    assert len(xs) == 203
    assert any(value == pytest.approx(2.345, abs=1e-12) for value in xs)
    assert any(value == pytest.approx(4.567, abs=1e-12) for value in xs)
    assert all(len(series.y_values) == len(result.x_values) for series in result.series)


def test_piecewise_parameter_sweep_uses_union_of_case_breakpoints():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "q(x) = piecewise(q1, x < a, 0)\n"
        "q1 := 8*kN/m\nL := 6*m",
    )

    result = eval_cell(
        engine,
        "plot(q(x), x, 0, L, a=[2.345*m, 4.567*m])",
    )[-1]
    xs = x_magnitudes(result)

    assert len(xs) == 203
    assert len(result.series) == 2
    assert any(value == pytest.approx(2.345, abs=1e-12) for value in xs)
    assert any(value == pytest.approx(4.567, abs=1e-12) for value in xs)
    assert all(len(series.y_values) == len(result.x_values) for series in result.series)


def test_piecewise_envelope_inherits_shared_enriched_grid():
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
    xs = x_magnitudes(result)

    assert len(xs) == 203
    assert any(value == pytest.approx(2.345, abs=1e-12) for value in xs)
    assert any(value == pytest.approx(4.567, abs=1e-12) for value in xs)
    assert all(len(series.y_values) == len(result.x_values) for series in result.series)


def test_piecewise_plot_rejects_unresolved_breakpoint_with_corrective_diagnostic():
    engine = EngineeringEngine()
    eval_cell(engine, "q(x) = piecewise(q1, x < a, 0)\nq1 := 8*kN/m\nL := 6*m")

    with pytest.raises(EngEvaluationError, match=r"Piecewise breakpoint.*a"):
        eval_cell(engine, "plot(q(x), x, 0, L)")


def test_non_piecewise_plot_retains_exact_201_point_baseline():
    engine = EngineeringEngine()
    eval_cell(engine, "q(x) = q1*x/L\nq1 := 8*kN/m\nL := 6*m")

    result = eval_cell(engine, "plot(q(x), x, 0, L)")[-1]

    assert len(result.x_values) == 201
