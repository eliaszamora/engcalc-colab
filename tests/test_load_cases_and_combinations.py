"""`case` and `combo` — a load combination whose factors survive onto the page.

I measured this as sugar over plain functions and deferred it, twice. The argument I
then built for it - that case names like `D` and `L` collide with quantities like span
and modulus - is false, and the measurement says so: `L := 6*m` and `L(x) = ...` coexist
in EngCalc today, and `numeric(subs(L(x), x, L/2))` answers correctly.

What is true came out of rendering the sheet and reading it. Written as an ordinary
definition, `U1(x) = 1.2*D(x) + 1.6*Lv(x)` renders as

    U1(x) = 0.6*qD*x*(L - x) + 0.8*qL*x*(L - x)

because 1.2/2 is 0.6. The number is right and the load combination is gone: a reviewer
checking 1.2 and 1.6 against the code that requires them cannot, because the page no
longer contains them. That is not sugar.

So a combination keeps its terms as written, and carries the expanded expression beside
them for `plot`, `governing` and `numeric` to use.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError, EngSyntaxError
from engcalc_colab.models import (
    LoadCaseResult,
    LoadCombinationResult,
    ParsedHeading,
)
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_aligned_results


BEAM = """L := 6*m
qD := 8*kN/m
qL := 12*kN/m
M_D(x) = qD*x*(L-x)/2
M_Lv(x) = qL*x*(L-x)/2
case D = M_D(x)
case Lv = M_Lv(x)
"""


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def run(source: str):
    engine = EngineeringEngine()
    results = []
    for line in [ln for ln in source.strip().splitlines() if ln.strip()]:
        results.extend(run_cell(engine, line))
    return engine, [result for result in results if result is not None]


def test_a_combination_keeps_the_factors_it_was_written_with():
    """The whole reason this exists."""
    _engine, results = run(BEAM + "combo U1 = 1.2*D + 1.6*Lv")
    result = results[-1]

    assert isinstance(result, LoadCombinationResult)
    assert [(str(factor), case) for factor, case in result.terms] == [
        ("1.20000000000000", "D"),
        ("1.60000000000000", "Lv"),
    ]

    latex = render_aligned_results([result])
    assert "1.2" in latex and "1.6" in latex
    # And the case names, not their bodies.
    assert r"D\left(x\right)" in latex
    assert "qD" not in latex, latex


def test_the_same_combination_as_a_plain_function_loses_them():
    """The defect, pinned as a contrast rather than described in a comment.

    If a later change made an ordinary definition keep its structure, this fails and the
    feature can be reconsidered on evidence instead of memory.
    """
    _engine, results = run(
        "L := 6*m\n"
        "qD := 8*kN/m\n"
        "qL := 12*kN/m\n"
        "M_D(x) = qD*x*(L-x)/2\n"
        "M_Lv(x) = qL*x*(L-x)/2\n"
        "U1(x) = 1.2*M_D(x) + 1.6*M_Lv(x)"
    )
    latex = render_aligned_results([results[-1]])

    assert "1.2" not in latex, latex
    assert "0.6" in latex


def test_the_combination_computes_what_the_plain_form_computes():
    """Same number, different page. A combination that read well and totalled wrong
    would be worse than the problem it fixes.

    1.2*(8*36/8) + 1.6*(12*36/8) = 1.2*36 + 1.6*54 = 129.6 kN*m at midspan.
    """
    _engine, results = run(
        BEAM + "combo U1 = 1.2*D + 1.6*Lv\nnumeric(subs(U1(x), x, L/2))"
    )
    assert results[-1].quantity.to("kN*m").magnitude == pytest.approx(129.6)


def test_a_case_is_a_function_the_rest_of_the_sheet_can_use():
    _engine, results = run(BEAM + "numeric(subs(D(x), x, L/2))")
    assert results[-1].quantity.to("kN*m").magnitude == pytest.approx(36.0)


def test_a_combination_can_be_plotted_and_compared_like_any_response():
    """`governing` and `plot` take it without knowing it is a combination."""
    _engine, results = run(
        BEAM
        + "combo U1 = 1.2*D + 1.6*Lv\n"
        + "combo U2 = 1.4*D\n"
        + "governing(U1(x), U2(x), x, 0, L)"
    )
    governing = results[-1]
    assert len(governing.intervals) == 1
    assert governing.intervals[0].label == "U1(x)"


def test_a_negative_factor_reads_as_a_subtraction():
    """`0.9D - 1.0W` is a real combination, and `+ -1.0 W(x)` is not how it is written."""
    _engine, results = run(
        BEAM + "combo U3 = 0.9*D - 1.0*Lv"
    )
    latex = render_aligned_results([results[-1]])
    assert "- 1.0" in latex or "-1.0" in latex, latex
    assert "+ -" not in latex


def test_a_combination_that_names_no_case_says_which_ones_exist():
    engine, _results = run(BEAM)
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "combo U1 = 1.2*qD")
    message = str(excinfo.value)
    assert "names no load case" in message
    assert "D" in message and "Lv" in message


def test_cases_of_different_variables_cannot_be_combined():
    """Adding a moment along `x` to one along `y` is not a combination of anything."""
    engine, _results = run(BEAM + "N_D(y) = qD*y\ncase Dy = N_D(y)")
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "combo U1 = 1.2*D + 1.0*Dy")
    assert "share one variable" in str(excinfo.value)


def test_a_combination_must_be_a_sum_of_factored_cases():
    """`D*Lv` is not a load combination, and silently expanding it would be worse."""
    engine, _results = run(BEAM)
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "combo U1 = D*Lv")
    assert "sum of factored load cases" in str(excinfo.value)


def test_a_case_needs_exactly_one_variable():
    engine, _results = run("qD := 8*kN/m\nL := 6*m")
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "case D = qD*L")
    assert "exactly one variable" in str(excinfo.value)


def test_a_case_cannot_take_a_name_that_is_already_defined():
    engine, _results = run(BEAM)
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "case M_D = M_D(x)")
    assert "already defined" in str(excinfo.value)


def test_reset_clears_the_declared_cases():
    """A fresh sheet has no cases, like it has no namespace.

    A combination that silently referred to a previous problem's cases is the worst kind
    of wrong: it computes, and about the wrong loads.
    """
    engine, _results = run(BEAM)
    assert engine.load_cases

    engine.reset()
    assert not engine.load_cases
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "combo U1 = 1.2*D")
    assert "declare one first" in str(excinfo.value)


def test_the_keyword_needs_a_plain_name():
    engine = EngineeringEngine()
    with pytest.raises(EngSyntaxError) as excinfo:
        run_cell(engine, "case 3 = x")
    assert "plain name" in str(excinfo.value)


def test_a_case_result_carries_its_variable():
    _engine, results = run(BEAM)
    case = results[-1]
    assert isinstance(case, LoadCaseResult)
    assert case.name == "Lv"
    assert case.variable == "x"
