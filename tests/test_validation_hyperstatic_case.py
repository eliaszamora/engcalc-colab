import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_result


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def run(engine: EngineeringEngine, source: str):
    return run_cell(engine, source)[0]


def test_complete_hyperstatic_case_supports_symbolic_to_numeric_workflow():
    engine = EngineeringEngine()

    run_cell(
        engine,
        """
V_A0 = q*L
M_A0 = q*L^2/2
V_0(x) = V_A0 - q*x
M_0(x) = -M_A0 + V_A0*x - q*x^2/2

V_A1 = -1
M_A1 = -L
V_1(x) = V_A1
M_1(x) = -M_A1 + V_A1*x

Delta_B0 = integrate(M_0(x)*M_1(x)/(E*I), x, 0, L)
f_11 = integrate(M_1(x)^2/(E*I), x, 0, L)
Delta_B = Delta_B0 + V_B*f_11
V_B = solve(Delta_B = 0, V_B)

V_A = q*L - V_B
M_A = q*L^2/2 - V_B*L
V(x) = expand(V_0(x) + V_B*V_1(x))
M(x) = expand(M_0(x) + V_B*M_1(x))

q := 2.8*tonf/m
L := 4*m
E := 200*GPa
I := 8.5e8*mm^4
""",
    )

    delta = run(engine, "numeric(Delta_B0)")
    flexibility = run(engine, "numeric(f_11)")
    vb = run(engine, "numeric(V_B)")
    va = run(engine, "numeric(V_A)")
    ma = run(engine, "numeric(M_A)")

    assert delta.quantity.to("mm").magnitude == pytest.approx(-5.168681411764705)
    assert flexibility.quantity.to("mm/kN").magnitude == pytest.approx(0.12549019607843137)
    assert vb.quantity.to("tonf").magnitude == pytest.approx(4.2)
    assert va.quantity.to("tonf").magnitude == pytest.approx(7.0)
    assert ma.quantity.to("tonf*m").magnitude == pytest.approx(5.6)

    assert str(engine.namespace["V_B"]) == "3*L*q/8"
    assert str(engine.namespace["V_A"]) == "5*L*q/8"
    assert str(engine.namespace["M_A"]) == "L**2*q/8"


def test_complete_hyperstatic_case_evaluates_internal_force_functions_at_points():
    engine = EngineeringEngine()

    run_cell(
        engine,
        """
V(x) = 5*q*L/8 - q*x
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2
q := 2.8*tonf/m
L := 4*m
x := 2.5*m
""",
    )

    shear = run(engine, "numeric(V(x))")
    moment = run(engine, "numeric(M(x))")
    end_moment = run(engine, "numeric(M(L))")

    assert shear.quantity.to("tonf").magnitude == pytest.approx(0.0, abs=1e-12)
    assert moment.quantity.to("tonf*m").magnitude == pytest.approx(3.15)
    assert end_moment.quantity.to("tonf*m").magnitude == pytest.approx(0.0, abs=1e-12)


def test_numeric_user_function_render_preserves_call_label():
    engine = EngineeringEngine()
    run(engine, "M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2")
    run(engine, "q := 2.8*tonf/m")
    run(engine, "L := 4*m")
    run(engine, "x := 2.5*m")

    result = run(engine, "numeric(M(x))")
    latex = render_result(result)

    assert latex.startswith(r"M\left(x\right) = ")
    assert "3.15" in latex
    assert r"\mathrm{tonf}" in latex
    assert r"\mathrm{m}" in latex


def test_numeric_user_function_with_symbolic_argument_preserves_call_label():
    engine = EngineeringEngine()
    run(engine, "M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2")
    run(engine, "q := 2.8*tonf/m")
    run(engine, "L := 4*m")

    result = run(engine, "numeric(M(L))")
    latex = render_result(result)

    assert latex.startswith(r"M\left(L\right) = ")
    assert "0.00" in latex


def test_numeric_user_function_keeps_unassigned_parameter_symbolic():
    engine = EngineeringEngine()
    run(engine, "V(x) = 5*q*L/8 - q*x")
    run(engine, "q := 2.8*tonf/m")
    run(engine, "L := 2*m")

    result = run(engine, "numeric(V(x))")
    latex = render_result(result)

    assert result.unresolved_symbols == ("x",)
    assert set(result.substitutions) == {"L", "q"}
    assert latex.startswith(r"V\left(x\right) = ")
    assert "2.00" in latex
    assert "2.80" in latex
    assert r"\mathrm{tonf}" in latex
    assert latex.endswith("x")


def test_partial_numeric_shear_evaluates_known_coefficients():
    engine = EngineeringEngine()
    run(engine, "V(x) = 5*q*L/8 - q*x")
    run(engine, "q := 2.8*tonf/m")
    run(engine, "L := 2*m")

    latex = render_result(run(engine, "numeric(V(x))"))
    final_latex = latex.split(" = ")[-1]

    assert "3.50" in final_latex
    assert "2.80" in final_latex
    assert r"\mathrm{tonf}" in final_latex
    assert "2.00" not in final_latex
    assert r"\frac{5" not in final_latex
    assert r"\left(" not in final_latex
    assert final_latex.endswith("x")


def test_partial_numeric_moment_evaluates_constant_linear_and_quadratic_coefficients():
    engine = EngineeringEngine()
    run(engine, "M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2")
    run(engine, "q := 2.8*tonf/m")
    run(engine, "L := 2*m")

    latex = render_result(run(engine, "numeric(M(x))"))
    final_latex = latex.split(" = ")[-1]

    assert final_latex.count("1.40") == 2
    assert "3.50" in final_latex
    assert r"x^{2}" in final_latex
    assert "2.00" not in final_latex
    assert r"\left(" not in final_latex


def test_numeric_partial_function_requires_all_non_parameter_values():
    engine = EngineeringEngine()
    run(engine, "V(x) = 5*q*L/8 - q*x")
    run(engine, "L := 2*m")

    with pytest.raises(EngEvaluationError, match="numeric evaluation requires values for: q"):
        run(engine, "numeric(V(x))")


def test_direct_numeric_expression_does_not_guess_a_free_parameter():
    engine = EngineeringEngine()
    run(engine, "q := 2.8*tonf/m")

    with pytest.raises(EngEvaluationError, match="numeric evaluation requires values for: x"):
        run(engine, "numeric(q*x)")
