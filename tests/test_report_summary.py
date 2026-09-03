"""`report(...)` marks a result; `summary()` collects them.

In a memoria of sixty lines the four numbers that matter are scattered among the working.
`report(M_max)` evaluates and shows the value exactly as `numeric(...)` does, and also
records it; `summary()` prints what was recorded.

This is the code helping rather than the code checking. It computes nothing new and
judges nothing - `check(...)` was deliberately left out of the roadmap for that reason -
it saves the reader from scrolling.

No existing name is displaced. `result(...)` already means "show the formula and the
final value, without the substitution stage" and keeps that meaning; `report(...)` is
about what belongs in the summary, which is a different question.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


_MEMORIA = """L := 6*m
q := 10*kN/m
M_max = q*L^2/8
report(M_max)
R_A = q*L/2
report(R_A)
summary()
"""


def test_report_shows_the_value_like_numeric_does():
    engine = EngineeringEngine()
    results = run_cell(engine, "L := 6*m\nq := 10*kN/m\nM_max = q*L^2/8\nreport(M_max)")
    assert float(results[-1].quantity.to("kN*m").magnitude) == pytest.approx(45.0)


def test_the_summary_collects_every_reported_value_in_order():
    engine = EngineeringEngine()
    result = run_cell(engine, _MEMORIA)[-1]

    assert [name for name, _ in result.entries] == ["M_max", "R_A"]
    assert float(result.entries[0][1].to("kN*m").magnitude) == pytest.approx(45.0)
    assert float(result.entries[1][1].to("kN").magnitude) == pytest.approx(30.0)


def test_a_value_that_was_not_reported_stays_out_of_the_summary():
    """The summary is what was marked, not everything that was computed."""
    engine = EngineeringEngine()
    result = run_cell(
        engine,
        "L := 6*m\nq := 10*kN/m\nM_max = q*L^2/8\nV_max = q*L/2\nreport(M_max)\nsummary()",
    )[-1]
    assert [name for name, _ in result.entries] == ["M_max"]


def test_reporting_the_same_name_twice_replaces_it_in_place():
    """A recomputed result is the same result, not a second row.

    Two rows for one name would be a summary that contradicts itself, and appending
    would put the correction at the bottom rather than where the reader expects it.
    """
    engine = EngineeringEngine()
    result = run_cell(
        engine,
        "L := 6*m\nq := 10*kN/m\nM = q*L^2/8\nreport(M)\nR = q*L/2\nreport(R)\n"
        "q := 20*kN/m\nM = q*L^2/8\nreport(M)\nsummary()",
    )[-1]

    assert [name for name, _ in result.entries] == ["M", "R"]
    assert float(result.entries[0][1].to("kN*m").magnitude) == pytest.approx(90.0)


def test_the_summary_renders_a_row_per_entry():
    import engcalc_colab.renderer as renderer

    engine = EngineeringEngine()
    html = renderer.render_result(run_cell(engine, _MEMORIA)[-1])
    assert html.count("<tr>") == 2
    # As mathematics, matching the working above rather than as the literal source text.
    # A memoria that writes M_max one way in the derivation and another in the summary
    # reads like two different quantities.
    assert r"\(M_{max}\)" in html and r"\(R_{A}\)" in html
    assert not [char for char in html if ord(char) < 32]


def test_the_summary_shows_a_value_the_way_the_working_above_showed_it():
    """`d = L/300` is 20.00 mm in the working; the summary said 0.02 m.

    A computed value carries no author-declared unit, so `numeric(...)` renders it in the
    unit of its own dimension. The summary rendered the same quantity as declared and put
    `0.02 m` two lines under `20.00 mm`. Nobody saw it because nobody had looked at the
    two side by side until the memoria was rendered and read.
    """
    import engcalc_colab.renderer as renderer

    engine = EngineeringEngine()
    html = renderer.render_result(
        run_cell(engine, "L := 6*m\nd = L/300\nreport(d)\nsummary()")[-1]
    )
    assert "20.00" in html and "mm" in html
    assert "0.02" not in html


def test_an_empty_summary_says_so_rather_than_printing_nothing():
    """An empty table looks like a working feature with nothing to show."""
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "summary()")
    # The model refuses an empty summary too, but with "a summary must carry at least
    # one reported value" prefixed by "symbolic evaluation failed" - true, and no help.
    # The engine guard earns its place by saying what to do, so that is what is pinned.
    assert "mark a value with report" in str(excinfo.value)


def test_summary_takes_no_arguments():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError):
        run_cell(engine, "L := 6*m\nM = L\nreport(M)\nsummary(M)")


def test_report_must_be_a_standalone_statement():
    """Its value is shown where it is written; assigning it would hide that."""
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError):
        run_cell(engine, "L := 6*m\nM = L\nx = report(M)")


def test_a_reset_clears_what_was_reported():
    """A fresh sheet has an empty summary, like it has an empty namespace.

    Nothing in this file exercised `reset()`, so a mutation that left the register
    behind passed every contract. A summary carrying values from a previous sheet is
    the worst kind of wrong: plausible, and about the wrong problem.
    """
    engine = EngineeringEngine()
    run_cell(engine, "L := 6*m\nM = L\nreport(M)")
    assert engine.reported

    engine.reset()
    assert not engine.reported

    with pytest.raises(EngEvaluationError):
        run_cell(engine, "summary()")
