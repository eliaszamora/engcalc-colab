from IPython.display import Math

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.magic import _display_equation_group
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_aligned_results


def evaluate(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_short_four_term_substitution_stays_on_one_mathjax_row():
    engine = EngineeringEngine()
    evaluate(engine, "S = a + b - c + d")
    evaluate(engine, "a := 1*kN")
    evaluate(engine, "b := 2*kN")
    evaluate(engine, "c := 3*kN")
    evaluate(engine, "d := 4*kN")

    latex = render_aligned_results([evaluate(engine, "numeric(S)")])

    # formula -> substitution -> final result, with no continuation row
    assert latex.count(r"\\[2pt]") == 2
    assert latex.count(" & = & ") == 3


def test_long_substitution_wraps_only_when_visual_budget_is_exceeded():
    engine = EngineeringEngine()
    evaluate(engine, "M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2")
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")
    evaluate(engine, "x := 2.5*m")

    latex = render_aligned_results([evaluate(engine, "numeric(M(x))")])

    # The first two substituted terms share a row; only the third continues.
    # Stages: formula -> substitution row 1 -> continuation -> final result.
    assert latex.count(r"\\[2pt]") == 3
    assert latex.count(" & & ") == 1
    assert "3.15" in latex


def test_final_numeric_result_is_always_a_separate_row():
    engine = EngineeringEngine()
    evaluate(engine, "V = q*L")
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")

    latex = render_aligned_results([evaluate(engine, "numeric(V)")])

    assert latex.count(" & = & ") == 3
    assert latex.count(r"\\[2pt]") == 2
    assert "11.20" in latex


def test_numeric_groups_use_mathjax_display_not_html(monkeypatch):
    engine = EngineeringEngine()
    evaluate(engine, "V = q*L")
    evaluate(engine, "q := 2.8*tonf/m")
    evaluate(engine, "L := 4*m")
    result = evaluate(engine, "numeric(V)")

    displayed = []
    monkeypatch.setattr("engcalc_colab.magic.display", displayed.append)

    _display_equation_group([result])

    assert len(displayed) == 1
    assert isinstance(displayed[0], Math)
