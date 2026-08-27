from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_result


def test_integral_render_contains_integral_and_result():
    engine = EngineeringEngine()
    for stmt in parse_cell("M = -q/2*(L-x)^2\nm = L-x"):
        engine.evaluate(stmt)
    result = engine.evaluate(parse_cell("Delta_B = integral(M*m/(E*I), x, 0, L)")[0])
    latex = render_result(result)
    assert r"\int" in latex
    assert r"\Delta" in latex or "Delta" in latex
    assert r"\frac" in latex


def test_function_assignment_renders_function_left_hand_side():
    engine = EngineeringEngine()
    result = engine.evaluate(parse_cell("V(x) = R_A - q*x")[0])
    latex = render_result(result)
    assert "V" in latex and "x" in latex and "R" in latex
