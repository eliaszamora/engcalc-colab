from dataclasses import FrozenInstanceError

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import PlotResult, PlotSeries
from engcalc_colab.parser import parse_cell


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def test_plot_result_can_transport_envelope_metadata_immutably():
    statement = parse_cell("plot(A(x), B(x), x, 0, L)")[0]
    source = (
        PlotSeries("A(x)", (1, 3), False),
        PlotSeries("B(x)", (2, 2), False),
    )
    displayed = (
        PlotSeries("max", (2, 3), False),
        PlotSeries("min", (1, 2), False),
    )
    result = PlotResult(
        statement,
        "Comparison",
        "x",
        (0, 1),
        displayed,
        kind="envelope",
        source_series=source,
        source_labels=("A(x)", "B(x)"),
        governing_max=(1, 0),
        governing_min=(0, 1),
    )

    assert result.kind == "envelope"
    assert result.source_series == source
    assert result.source_labels == ("A(x)", "B(x)")
    assert result.governing_max == (1, 0)
    assert result.governing_min == (0, 1)

    with pytest.raises(FrozenInstanceError):
        result.kind = "plot"


def test_plot_result_defaults_preserve_v050_transport():
    statement = parse_cell("plot(x, x, 0, 1)")[0]
    series = PlotSeries("x", (1, 2), False)
    result = PlotResult(statement, "x", "x", (0, 1), (series,))

    assert result.envelope_mode is None
    assert result.governing_signed is None


def test_plot_result_can_transport_magnitude_metadata():
    statement = parse_cell("envelope(abs(A(x)), abs(B(x)), x, 0, 1)")[0]
    source = (
        PlotSeries("A(x)", (-1, 2), False),
        PlotSeries("B(x)", (3, -4), False),
    )
    result = PlotResult(
        statement,
        "V(x)",
        "x",
        (0, 1),
        (PlotSeries("|V|_max(x)", (3, 4), False),),
        kind="envelope",
        source_series=source,
        source_labels=("A(x)", "B(x)"),
        governing_max=(1, 1),
        envelope_mode="magnitude",
        governing_signed=(3, -4),
    )

    assert result.envelope_mode == "magnitude"
    assert result.governing_signed == (3, -4)


def test_envelope_multiple_expressions_computes_signed_pointwise_max_min():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_A(x) = q*x*(L-x)/2\n"
        "M_B(x) = -0.5*q*x*(L-x)/2\n"
        "q := 8*kN/m\nL := 6*m",
    )

    result = eval_cell(
        engine,
        "envelope(M_A(x), M_B(x), x, 0, L)",
    )[-1]

    assert isinstance(result, PlotResult)
    assert result.kind == "envelope"
    assert result.display_label == "M(x)"
    assert len(result.x_values) == 201
    assert len(result.series) == 2
    assert result.series[0].display_label == "M_max(x)"
    assert result.series[1].display_label == "M_min(x)"
    assert result.series[0].is_moment
    assert result.series[1].is_moment
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(36.0)
    assert result.series[1].y_values[100].to("kN*m").magnitude == pytest.approx(-18.0)


def test_envelope_retains_source_series_labels_and_governing_indices():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_A(x) = q*x*(L-x)/2\n"
        "M_B(x) = -0.5*q*x*(L-x)/2\n"
        "q := 8*kN/m\nL := 6*m",
    )
    result = eval_cell(engine, "envelope(M_A(x), M_B(x), x, 0, L)")[-1]

    assert [item.display_label for item in result.source_series] == [
        "M_A(x)",
        "M_B(x)",
    ]
    assert result.source_labels == ("M_A(x)", "M_B(x)")
    assert len(result.governing_max) == 201
    assert len(result.governing_min) == 201
    assert result.governing_max[100] == 0
    assert result.governing_min[100] == 1


def test_envelope_rejects_single_non_sweep_source():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x\nq := 5*kN/m\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="envelope requires at least two response series",
    ):
        eval_cell(engine, "envelope(M(x), x, 0, L)")


def test_envelope_cannot_be_assigned_to_symbol():
    engine = EngineeringEngine()
    with pytest.raises(
        EngEvaluationError,
        match="envelope must be a standalone statement",
    ):
        eval_cell(engine, "A = envelope(x, 2*x, x, 0, 4)")


def test_envelope_parameter_sweep_reduces_source_series_and_keeps_governing_cases():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nL := 6*m")

    result = eval_cell(
        engine,
        "envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])",
    )[-1]

    assert len(result.source_series) == 3
    assert len(result.series) == 2
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(67.5)
    assert result.series[1].y_values[100].to("kN*m").magnitude == pytest.approx(22.5)
    assert result.governing_max[100] == 2
    assert result.governing_min[100] == 0


def test_envelope_sweep_does_not_mutate_existing_parameter_or_x_value():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M(x) = q*x*(L-x)/2\n"
        "q := 2.8*tonf/m\nL := 6*m\nx := 1.5*m",
    )

    eval_cell(
        engine,
        "envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])",
    )

    assert engine.numeric_context.get("q").to("tonf/m").magnitude == pytest.approx(2.8)
    assert engine.numeric_context.get("x").to("m").magnitude == pytest.approx(1.5)


def test_envelope_rejects_sweep_of_plotting_variable():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = x^2\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="envelope sweep parameter 'x' cannot be the plotting variable",
    ):
        eval_cell(engine, "envelope(M(x), x, 0, L, x=[0.5*m, 1.0*m])")


def test_envelope_rejects_sweep_that_expands_to_one_source_series():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="envelope requires at least two response series",
    ):
        eval_cell(engine, "envelope(M(x), x, 0, L, q=[5*kN/m])")


def test_envelope_rejects_sweep_parameter_absent_from_expanded_expression():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x\nq := 5*kN/m\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="envelope sweep parameter 'P' is not used in the plotted expression",
    ):
        eval_cell(engine, "envelope(M(x), x, 0, L, P=[1*kN, 2*kN])")


def test_envelope_rejects_incompatible_sweep_value_dimensions():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x^2\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="envelope sweep values have incompatible units",
    ):
        eval_cell(engine, "envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN])")


def test_envelope_normalizes_compatible_source_units_before_comparison():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "R_A(x) = q_A*x\n"
        "R_B(x) = q_B*x\n"
        "q_A := 1*kN/m\nq_B := 500*N/m\nL := 2*m",
    )
    result = eval_cell(engine, "envelope(R_A(x), R_B(x), x, 0, L)")[-1]

    assert result.source_series[0].y_values[100].to("kN").magnitude == pytest.approx(1.0)
    assert result.source_series[1].y_values[100].to("kN").magnitude == pytest.approx(0.5)
    assert result.series[0].y_values[100].to("kN").magnitude == pytest.approx(1.0)
    assert result.series[1].y_values[100].to("kN").magnitude == pytest.approx(0.5)


def test_envelope_rejects_series_with_incompatible_y_dimensions():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V(x) = q*(L-x)\nM(x) = q*(L-x)^2\nq := 5*kN/m\nL := 2*m",
    )
    with pytest.raises(
        EngEvaluationError,
        match="envelope series have incompatible y dimensions",
    ):
        eval_cell(engine, "envelope(V(x), M(x), x, 0, L)")


def test_envelope_rejects_mixed_moment_and_non_moment_series_even_with_same_dimensions():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_A(x) = q*x^2\nR(x) = q*x^2\nq := 5*kN/m\nL := 2*m",
    )
    with pytest.raises(
        EngEvaluationError,
        match="envelope cannot mix moment and non-moment series on one axis",
    ):
        eval_cell(engine, "envelope(M_A(x), R(x), x, 0, L)")
