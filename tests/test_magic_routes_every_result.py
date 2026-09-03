"""What the magic hands to the notebook, for every kind of result.

Three merged features produced broken notebook output while every contract passed, because
the contracts called the renderers directly and never asked whether the magic would route
anything to them:

- `solve(M(x) > 20*kN*m, x, 0, L)` raised `AttributeError: 'InequalityResult' object has
  no attribute 'value'` and killed the cell. Shipped in 0.23.0.
- `governing(...)` and `summary()` had their finished HTML embedded inside
  `\\begin{array}`, so the reader saw `\\[\\hspace{0.2em}\\begin{array}{lcl}` as literal
  text next to the values. Shipped in 0.19.0 and 0.20.0 respectively, and visible in
  every release since.

None of this was found by a test. It was found the first time the product was driven end
to end and looked at, which had never happened: every check until then asserted that a
LaTeX string contained a substring, and a string that renders as garbage contains all the
same substrings.

The routing now goes through the `CharacteristicResult` and `HtmlBlockResult` unions in
the renderer rather than tuples written out in the magic, so a result type added to a
union is routed without anyone remembering. The last test here is the one that would have
caught all three.
"""

import matplotlib
import pytest
from IPython.display import HTML, Math

matplotlib.use("Agg")


def run_cell(monkeypatch, source: str):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng("", source)
    return displayed


BEAM = """L := 6*m
q := 10*kN/m
M(x) = q*x*(L-x)/2
"""


def test_an_inequality_reaches_the_notebook_instead_of_killing_the_cell(monkeypatch):
    displayed = run_cell(monkeypatch, BEAM + "solve(M(x) > 20*kN*m, x, 0, L)")

    assert [type(item) for item in displayed] == [Math, HTML]
    assert "satisfies the inequality" in displayed[-1].data
    assert "0.76" in displayed[-1].data


def test_governing_reaches_the_notebook_as_its_own_block(monkeypatch):
    displayed = run_cell(
        monkeypatch,
        "L := 6*m\n"
        "qD := 8*kN/m\n"
        "M1(x) = 1.2*qD*x*(L-x)/2\n"
        "M2(x) = 1.4*qD*x*(L-x)/2\n"
        "governing(M1(x), M2(x), x, 0, L)",
    )

    assert type(displayed[-1]) is HTML
    assert "Governing" in displayed[-1].data


def test_a_summary_reaches_the_notebook_as_a_table(monkeypatch):
    displayed = run_cell(monkeypatch, BEAM + "d = L/300\nreport(d)\nsummary()")

    assert type(displayed[-1]) is HTML
    assert "<table>" in displayed[-1].data
    assert "Summary" in displayed[-1].data


def test_equation_rows_before_and_after_a_block_stay_in_source_order(monkeypatch):
    """A block flushes the pending equations and the ones after it start a new group.

    Out of order, a memoria says the answer before the working that produced it.
    """
    displayed = run_cell(
        monkeypatch,
        BEAM + "d = L/300\nreport(d)\nsummary()\nz = 2*L",
    )
    assert [type(item) for item in displayed] == [Math, HTML, Math]
    assert "z" in displayed[-1].data


def test_no_latex_row_ever_carries_html_markup(monkeypatch):
    """The signature of the defect, asserted over every block-producing feature at once.

    `render_result` returns finished HTML for a summary and a governing report. Anything
    that puts one in the aligned array embeds a <div> inside \\begin{array}, and MathJax
    prints the markup rather than rendering it. Checking for an `engcalc-` class inside a
    Math payload catches that for any result type, including ones added later - which is
    the point, since three were added and none was routed.
    """
    displayed = run_cell(
        monkeypatch,
        "L := 6*m\n"
        "q := 10*kN/m\n"
        "assume(w > 0)\n"
        "M(x) = q*x*(L-x)/2\n"
        "eqFy = eq(R_A + R_B, q*L)\n"
        "eqMA = eq(R_B*L, q*L*L/2)\n"
        "solve(eqFy, eqMA, R_A, R_B)\n"
        "solve(M(x) > 20*kN*m, x, 0, L)\n"
        "roots(M(x), x, 0, L)\n"
        "d = L/300\n"
        "report(d)\n"
        "summary()",
    )

    assert displayed, "the cell displayed nothing at all"
    for item in displayed:
        if isinstance(item, Math):
            assert "engcalc-" not in item.data, (
                "HTML markup inside a LaTeX row: " + item.data[:200]
            )
            assert "<div" not in item.data
            assert "<table" not in item.data


def test_every_result_the_engine_produces_is_routed_somewhere(monkeypatch):
    """No result may reach the notebook as an unrendered repr.

    A type the magic does not know falls through to the equation group, where it is
    either mangled or raises. Both happened. This asserts the positive: each block
    feature produces an HTML block of its own.
    """
    displayed = run_cell(
        monkeypatch,
        "L := 6*m\n"
        "q := 10*kN/m\n"
        "M(x) = q*x*(L-x)/2\n"
        "roots(M(x), x, 0, L)\n"
        "solve(M(x) > 20*kN*m, x, 0, L)\n"
        "d = L/300\n"
        "report(d)\n"
        "summary()",
    )

    blocks = [item.data for item in displayed if isinstance(item, HTML)]
    assert len(blocks) == 3
    assert any("Roots" in block for block in blocks)
    assert any("satisfies the inequality" in block for block in blocks)
    assert any("Summary" in block for block in blocks)
