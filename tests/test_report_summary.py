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
    assert "M_max" in html and "R_A" in html
    assert not [char for char in html if ord(char) < 32]


def test_an_empty_summary_says_so_rather_than_printing_nothing():
    """An empty table looks like a working feature with nothing to show."""
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "summary()")
    assert "report" in str(excinfo.value).lower()


def test_summary_takes_no_arguments():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError):
        run_cell(engine, "L := 6*m\nM = L\nreport(M)\nsummary(M)")


def test_report_must_be_a_standalone_statement():
    """Its value is shown where it is written; assigning it would hide that."""
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError):
        run_cell(engine, "L := 6*m\nM = L\nx = report(M)")
