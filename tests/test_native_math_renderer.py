from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_responsive_results


def evaluate(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_responsive_renderer_emits_native_math_instead_of_raw_dollar_latex():
    engine = EngineeringEngine()
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")
    evaluate(engine, "x := 2.5*m")
    evaluate(engine, "V(x) = 5*q*L/8 - q*x")

    html = render_responsive_results([evaluate(engine, "numeric(V(x))")])

    assert "<math" in html
    assert "</math>" in html
    assert "$" not in html
    assert "flex-wrap:wrap" in html


def test_responsive_native_math_preserves_one_flex_item_per_additive_term():
    engine = EngineeringEngine()
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")
    evaluate(engine, "x := 2.5*m")
    evaluate(engine, "M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2")

    html = render_responsive_results([evaluate(engine, "numeric(M(x))")])
    substitution = html.split('data-stage="substitution"', 1)[1].split('data-stage="result"', 1)[0]

    assert substitution.count('class="engcalc-term"') == 3
    assert substitution.count("<math") >= 3
    assert "$" not in substitution
    assert "<br" not in substitution
