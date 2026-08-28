from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_aligned_results, render_result


def evaluate(engine: EngineeringEngine, source: str):
    item = parse_cell(source)[0]
    return engine.evaluate(item)


def evaluate_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def test_numeric_assignment_renders_quantity_with_upright_units():
    engine = EngineeringEngine()

    result = evaluate(engine, "q := 2.8*tonf/m")
    latex = render_result(result)

    assert latex.startswith("q = ")
    assert "2.80" in latex
    assert r"\mathrm{tonf}" in latex
    assert r"\mathrm{m}" in latex


def test_named_numeric_evaluation_renders_formula_substitution_and_result():
    engine = EngineeringEngine()
    evaluate(engine, "V_B = 3*q*L/8")
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")

    result = evaluate(engine, "numeric(V_B)")
    latex = render_result(result)

    assert latex.startswith(r"V_{B} = ")
    assert r"\frac{3 q L}{8}" in latex
    assert "2.80" in latex
    assert "4.00" in latex
    assert "4.20" in latex
    assert latex.count(" = ") == 3
    assert r"\mathrm{tonf}" in latex
    assert r"\mathrm{m}" in latex


def test_direct_numeric_expression_uses_formula_as_left_side():
    engine = EngineeringEngine()
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")

    result = evaluate(engine, "numeric(q*L^2/8)")
    latex = render_result(result)

    assert latex.startswith(r"\frac{q L^{2}}{8} = ")
    assert "5.60" in latex
    assert r"\mathrm{tonf}" in latex
    assert r"\mathrm{m}" in latex


def test_numeric_rows_preserve_three_column_layout_and_spacing():
    engine = EngineeringEngine()
    results = evaluate_cell(
        engine,
        "q := 2.8*tonf/m\nL := 4*m\n\nP := q*L",
    )

    latex = render_aligned_results(results)

    assert r"\begin{array}{lcl}" in latex
    assert r"\\[4pt]" in latex
    assert r"\\[8pt]" in latex
    assert latex.count(" & = & ") == 3
