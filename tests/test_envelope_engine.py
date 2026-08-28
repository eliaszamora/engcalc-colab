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
