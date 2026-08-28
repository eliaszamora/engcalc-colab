import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import PlotResult
from engcalc_colab.parser import parse_cell


def test_native_plot_end_to_end():
    engine = EngineeringEngine()
    cell = """
V(x) = 5*q*L/8 - q*x
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2
q := 2.8*tonf/m
L := 4*m
plot(V(x), x, 0, L)
plot(M(x), x, 0, L)
"""
    results = [engine.evaluate(stmt) for stmt in parse_cell(cell)]
    plots = [result for result in results if isinstance(result, PlotResult)]
    assert len(plots) == 2
    shear, moment = plots
    assert len(shear.x_values) == 201
    assert shear.x_values[0].to("m").magnitude == 0
    assert shear.x_values[-1].to("m").magnitude == 4
    assert shear.y_values[0].to("tonf").magnitude == 7.0
    assert abs(moment.y_values[-1].to("tonf*m").magnitude) < 1e-12
    assert not moment.y_values[-1].dimensionless


def test_multicurve_plot_end_to_end():
    engine = EngineeringEngine()
    cell = """
M_D(x) = q_D*x*(L-x)/2
M_L(x) = q_L*x*(L-x)/2
q_D := 8*kN/m
q_L := 5*kN/m
L := 6*m
plot(M_D(x), M_L(x), x, 0, L)
"""
    result = [engine.evaluate(stmt) for stmt in parse_cell(cell)][-1]

    assert isinstance(result, PlotResult)
    assert len(result.series) == 2
    assert len(result.x_values) == 201
    assert result.display_label == "M(x)"
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(36.0)
    assert result.series[1].y_values[100].to("kN*m").magnitude == pytest.approx(22.5)


def test_parameter_sweep_plot_end_to_end():
    engine = EngineeringEngine()
    cell = """
M(x) = q*x*(L-x)/2
L := 6*m
plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
"""
    result = [engine.evaluate(stmt) for stmt in parse_cell(cell)][-1]

    assert isinstance(result, PlotResult)
    assert len(result.series) == 3
    assert result.display_label == "M(x)"
    assert result.series[-1].y_values[100].to("kN*m").magnitude == pytest.approx(67.5)


def test_multiple_expression_envelope_end_to_end():
    engine = EngineeringEngine()
    cell = """
M_A(x) = q*x*(L-x)/2
M_B(x) = -0.5*q*x*(L-x)/2
q := 8*kN/m
L := 6*m
envelope(M_A(x), M_B(x), x, 0, L)
"""
    result = [engine.evaluate(stmt) for stmt in parse_cell(cell)][-1]

    assert isinstance(result, PlotResult)
    assert result.kind == "envelope"
    assert len(result.source_series) == 2
    assert len(result.series) == 2
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(36.0)
    assert result.series[1].y_values[100].to("kN*m").magnitude == pytest.approx(-18.0)


def test_parameter_sweep_envelope_end_to_end():
    engine = EngineeringEngine()
    cell = """
M(x) = q*x*(L-x)/2
L := 6*m
envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
"""
    result = [engine.evaluate(stmt) for stmt in parse_cell(cell)][-1]

    assert isinstance(result, PlotResult)
    assert result.kind == "envelope"
    assert len(result.source_series) == 3
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(67.5)
    assert result.series[1].y_values[100].to("kN*m").magnitude == pytest.approx(22.5)
    assert result.governing_max[100] == 2
    assert result.governing_min[100] == 0
