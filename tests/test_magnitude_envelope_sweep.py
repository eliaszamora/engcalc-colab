import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def test_magnitude_sweep_keeps_signed_cases_and_abs_governing_curve():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*(L/2-x)\nL := 4*m")

    result = eval_cell(
        engine,
        "envelope(abs(V(x)), x, 0, L, q=[2*kN/m, 4*kN/m, -5*kN/m])",
    )[-1]

    assert result.source_labels == (
        "q = 2 kN/m",
        "q = 4 kN/m",
        "q = -5 kN/m",
    )
    assert result.source_series[2].y_values[0].to("kN").magnitude == pytest.approx(-10.0)
    assert result.series[0].y_values[0].to("kN").magnitude == pytest.approx(10.0)
    assert result.governing_max[0] == 2
    assert result.governing_signed[0].to("kN").magnitude == pytest.approx(-10.0)


def test_magnitude_sweep_does_not_mutate_parameter_or_x():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V(x) = q*(L/2-x)\nq := 2.8*tonf/m\nL := 4*m\nx := 1*m",
    )

    eval_cell(
        engine,
        "envelope(abs(V(x)), x, 0, L, q=[2*kN/m, 4*kN/m])",
    )

    assert engine.numeric_context.get("q").to("tonf/m").magnitude == pytest.approx(2.8)
    assert engine.numeric_context.get("x").to("m").magnitude == pytest.approx(1.0)


def test_magnitude_envelope_normalizes_compatible_units_before_comparison():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V_A(x) = -q_A*x\nV_B(x) = q_B*x\n"
        "q_A := 1*kN/m\nq_B := 1500*N/m\nL := 2*m",
    )

    result = eval_cell(
        engine,
        "envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)",
    )[-1]

    assert result.series[0].y_values[-1].to("kN").magnitude == pytest.approx(3.0)
    assert result.governing_signed[-1].to("kN").magnitude == pytest.approx(3.0)
