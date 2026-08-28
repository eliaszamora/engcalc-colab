import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def test_magnitude_envelope_keeps_signed_sources_and_one_abs_max_branch():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V_A(x) = R_A - q_A*x\n"
        "V_B(x) = R_B + q_B*x\n"
        "R_A := 6*kN\nq_A := 4*kN/m\n"
        "R_B := -2*kN\nq_B := 5*kN/m\nL := 2*m",
    )

    result = eval_cell(
        engine,
        "envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)",
    )[-1]

    assert result.envelope_mode == "magnitude"
    assert result.display_label == "V(x)"
    assert len(result.series) == 1
    assert result.series[0].display_label == "|V|_max(x)"
    assert result.source_labels == ("V_A(x)", "V_B(x)")
    assert [
        series.y_values[0].to("kN").magnitude
        for series in result.source_series
    ] == pytest.approx([6.0, -2.0])
    assert [
        series.y_values[-1].to("kN").magnitude
        for series in result.source_series
    ] == pytest.approx([-2.0, 8.0])
    assert result.series[0].y_values[0].to("kN").magnitude == pytest.approx(6.0)
    assert result.series[0].y_values[-1].to("kN").magnitude == pytest.approx(8.0)
    assert len(result.governing_max) == 201
    assert result.governing_min is None


def test_magnitude_envelope_retains_negative_signed_governing_value():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V_A(x) = R_A + q_A*x\n"
        "V_B(x) = R_B - q_B*x\n"
        "R_A := -9*kN\nq_A := 1*kN/m\n"
        "R_B := 3*kN\nq_B := 1*kN/m\nL := 2*m",
    )

    result = eval_cell(
        engine,
        "envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)",
    )[-1]

    assert result.series[0].y_values[0].to("kN").magnitude == pytest.approx(9.0)
    assert result.governing_signed[0].to("kN").magnitude == pytest.approx(-9.0)
    assert result.governing_max[0] == 0


def test_envelope_rejects_mixed_absolute_and_signed_sources():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V_A(x) = R_A - q*x\nV_B(x) = R_B + q*x\n"
        "R_A := 6*kN\nR_B := -2*kN\nq := 2*kN/m\nL := 2*m",
    )

    with pytest.raises(
        EngEvaluationError,
        match="envelope cannot mix absolute and signed response series",
    ):
        eval_cell(engine, "envelope(abs(V_A(x)), V_B(x), x, 0, L)")


def test_signed_envelope_explicitly_reports_signed_mode():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V_A(x) = R_A - q*x\nV_B(x) = R_B + q*x\n"
        "R_A := 6*kN\nR_B := -2*kN\nq := 2*kN/m\nL := 2*m",
    )

    result = eval_cell(engine, "envelope(V_A(x), V_B(x), x, 0, L)")[-1]

    assert result.envelope_mode == "signed"
    assert len(result.series) == 2
