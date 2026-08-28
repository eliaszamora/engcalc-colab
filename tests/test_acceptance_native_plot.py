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
