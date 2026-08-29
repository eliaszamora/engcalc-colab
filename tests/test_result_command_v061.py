import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_aligned_results, render_result


def evaluate(engine: EngineeringEngine, source: str):
    statement = parse_cell(source)[0]
    return engine.evaluate(statement)


def test_result_named_scalar_renders_formula_and_final_without_substitution():
    engine = EngineeringEngine()
    evaluate(engine, "M_A = q*L^2/8")
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")

    rendered = render_result(evaluate(engine, "result(M_A)"))

    assert rendered.startswith(r"M_{A} = ")
    assert r"\frac{q L^{2}}{8}" in rendered
    assert "5.60" in rendered
    assert "2.80" not in rendered
    assert "4.00" not in rendered
    assert rendered.count(" = ") == 2


def test_result_target_unit_converts_final_without_showing_substitution():
    engine = EngineeringEngine()
    evaluate(engine, "M_A = q*L^2/8")
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")

    rendered = render_result(evaluate(engine, "result(M_A, kN*m)"))
    final_latex = rendered.split(" = ")[-1]

    assert "2.80" not in rendered
    assert "4.00" not in rendered
    assert "54.92" in final_latex
    assert r"\mathrm{kN}" in final_latex
    assert r"\mathrm{tonf}" not in final_latex


def test_result_partial_function_renders_formula_then_evaluated_function_only():
    engine = EngineeringEngine()
    evaluate(engine, "M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2")
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")

    rendered = render_result(evaluate(engine, "result(M(x))"))

    assert rendered.startswith(r"M\left(x\right) = ")
    assert "q" in rendered
    assert "2.80" not in rendered
    assert "4.00" not in rendered
    assert "5.60" in rendered
    assert "7.00" in rendered
    assert "1.40" in rendered
    assert rendered.count(" = ") == 2


def test_result_aligned_output_uses_formula_and_final_as_two_stages():
    engine = EngineeringEngine()
    evaluate(engine, "M_A = q*L^2/8")
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")

    rendered = render_aligned_results([evaluate(engine, "result(M_A)")])

    assert rendered.count(" & = & ") == 2
    assert rendered.count(r"\\[8pt]") == 1
    assert r"\\[2pt]" not in rendered
    assert "2.80" not in rendered
    assert "4.00" not in rendered


def test_numeric_keeps_existing_detailed_formula_substitution_result_behavior():
    engine = EngineeringEngine()
    evaluate(engine, "M_A = q*L^2/8")
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")

    rendered = render_result(evaluate(engine, "numeric(M_A)"))

    assert "2.80" in rendered
    assert "4.00" in rendered
    assert rendered.count(" = ") == 3


def test_result_is_reserved_as_a_public_command_name():
    with pytest.raises(EngSyntaxError, match="reserved identifier 'result'"):
        parse_cell("result = 3")
