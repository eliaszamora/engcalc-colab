r"""A block that Colab renders as HTML carries no LaTeX, because none of it typesets.

#120 established the fact by measuring it in Colab: inside a `display(HTML(...))` output,
**nothing** typesets - not `\(...\)`, not `$...$`, not `\[...\]`, not an explicit
`MathJax.typeset()` call. Colab isolates it. #120 fixed the narrative, which was the one
place anybody had looked.

The rest of it stayed, and stayed invisible, because no reference sheet in the repository
used the calls that produce these blocks. Between them the two sheets exercised eleven of
the language's forty-seven calls, and `governing`, `extrema`, `summary` and `table` were
not among them. A third benchmark - a beam with load cases and combinations - was written
to reach them, and the engineer ran it in Colab. His screenshots:

    Extrema — U1(x)
    Domain: \(0.00\,\mathrm{m}\) to \(6.00\,\mathrm{m}\)
    \(x\) = \(\frac{L}{2}\) (\(3.00\,\mathrm{m}\)) · value = ...

    Summary
    \(M_{u}\)          \(183.60\,\mathrm{kN} \cdot \mathrm{m}\)

Two sources, one cause:

* `_characteristic_math` wraps everything it is given in `\(...\)`. Every characteristic
  block - `governing`, `extrema`, `roots`, `intersections`, `summary` - funnels through it.
* `_magnitude_text` returns `3.51 \times 10^{-8}` for a value outside the readable band,
  and a table cell puts that straight into a `<td>`.

**Plain text, not a `Markdown` output.** Markdown would let the mathematics typeset, the
way #120's narrative does, but it rests on an assumption about how Colab treats raw HTML
inside a markdown output that has *not* been measured - and assuming how Colab renders is
precisely what cost four releases. The table's own column headers already read well as
plain text: `f(x) [m⁵]`, from `format(unit, "~P")`. This does the same for the rest.

The Math outputs are untouched: those *are* typeset in Colab, and they are where the
mathematics of a memoria lives.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> str:
        captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    run.objects = captured
    return run


def _html_blocks(cell_run) -> str:
    """Only what the notebook renders as HTML, taken by output type.

    A cell emits Math rows too, and those *are* typeset in Colab and are meant to carry
    LaTeX; asserting over the whole page fails on the ordinary working. Two drafts of
    this helper split the concatenated string instead, and the second one still caught
    the Math because a characteristic block opens with a `<style>` tag and the split
    landed on `<div`. The display objects already carry the distinction - `HTML` against
    `Math` - so it is read from there rather than guessed from markup.
    """
    from IPython.display import HTML

    return "".join(
        obj.data for obj in cell_run.objects if isinstance(obj, HTML)
    )


def _run_then_blocks(cell_run, source: str) -> str:
    cell_run(source)
    return _html_blocks(cell_run)


BEAM = (
    "L := 6*m\n"
    "qD := 18*kN/m\n"
    "qL := 12*kN/m\n"
    "M_D(x) = qD*x*(L - x)/2\n"
    "M_L(x) = qL*x*(L - x)/2\n"
    "case D = M_D(x)\n"
    "case Lv = M_L(x)\n"
    "combo U1 = 1.2*D + 1.6*Lv\n"
    "combo U2 = 1.4*D\n"
)


# --- no LaTeX where it cannot typeset --------------------------------------------------

def test_a_summary_carries_no_latex(cell):
    block = _run_then_blocks(cell, "M_u := 183.6*kN*m\nreport(M_u)\nsummary()\n")
    assert r"\(" not in block, block
    assert r"\mathrm" not in block, block
    assert "183.60" in block, block


def test_a_governing_block_carries_no_latex(cell):
    block = _run_then_blocks(cell, BEAM + "governing(U1(x), U2(x), x, 0, L)\n")
    assert r"\(" not in block, block
    assert r"\mathrm" not in block, block


def test_an_extrema_block_carries_no_latex(cell):
    block = _run_then_blocks(cell, BEAM + "extrema(U1(x), x, 0, L)\n")
    assert r"\(" not in block, block
    assert r"\mathrm" not in block, block


def test_a_table_cell_outside_the_band_carries_no_latex(cell):
    """The second source, and the one that was missed while reporting the first: a
    magnitude too small for a decimal render goes into a `<td>` as `\\times 10^{-8}`."""
    latex = cell("I := 0.0000000234*m**4\nL := 3*m\nf(x) = I*x\ntable(f(x), x, 0, L, 3)\n")
    assert r"\times" not in latex, latex
    assert "×10" in latex, latex


# --- and it still says what it said ----------------------------------------------------

def test_a_summary_still_names_its_values(cell):
    """`Mᵤ` rather than `M_u`: a name goes through SymPy's pretty printer, which gives a
    bare symbol its Greek letter and its subscript. `delta` reads `δ`, which is what an
    engineer wrote it to mean."""
    block = _run_then_blocks(
        cell, "M_u := 183.6*kN*m\ndelta := 3.99*mm\nreport(M_u)\nreport(delta)\nsummary()\n"
    )
    assert "Mᵤ" in block, block
    assert "δ" in block, block
    assert "183.60" in block and "kN" in block, block
    assert "3.99" in block and "mm" in block, block


def test_a_governing_block_still_names_its_intervals(cell):
    latex = cell(BEAM + "governing(U1(x), U2(x), x, 0, L)\n")
    assert "U1(x)" in latex, latex
    assert "6.00" in latex and "m" in latex, latex


def test_an_extrema_block_still_names_its_points(cell):
    latex = cell(BEAM + "extrema(U1(x), x, 0, L)\n")
    assert "3.00" in latex, latex
    assert "global max" in latex, latex


# --- what must not move ---------------------------------------------------------------

def test_a_math_row_still_uses_latex(cell):
    """The typeset path, which Colab *does* render, and where the mathematics of a
    memoria lives. Stripping LaTeX from it would be the opposite defect."""
    latex = cell("q := 4*kN/m\nL := 5*m\nM = q*L^2/8\nnumeric(M)\n")
    assert r"\mathrm{kN}" in latex, latex
    assert r"\frac" in latex or r"\cdot" in latex, latex


def test_an_expression_stays_on_one_line(cell):
    """The line dividing the two printers, which nothing else was watching.

    SymPy's `pretty` gives a bare symbol its Greek letter, and that is why it is used at
    all - but on anything with a fraction or a power it draws two or three lines of box
    characters, and these go inside a table cell. A mutant that pretty-printed everything
    passed all 1952 tests.
    """
    import sympy as sp

    from engcalc_colab.renderer import _characteristic_symbolic_math

    span = sp.Symbol("L")
    assert _characteristic_symbolic_math(span) == "L"
    assert _characteristic_symbolic_math(span / 2) == "L/2"
    for value in (span / 2, span**2 + 1, sp.sqrt(span) / 3):
        assert "\n" not in _characteristic_symbolic_math(value), value


def test_a_greek_name_keeps_its_letter(cell):
    """The reason `pretty` is used for a symbol in the first place."""
    import sympy as sp

    from engcalc_colab.renderer import _characteristic_symbolic_math

    assert _characteristic_symbolic_math(sp.Symbol("delta")) == "δ"
    assert _characteristic_symbolic_math(sp.Symbol("theta_1")) == "θ₁"


def test_a_reported_name_cannot_inject_markup(cell):
    """These blocks are HTML, so what goes into them is escaped. Plain text is not the
    same as unescaped text, and swapping one for the other is how an escape gets lost."""
    from engcalc_colab.renderer import _characteristic_math

    assert "<b>" not in _characteristic_math("<b>x</b>")
    assert "&lt;b&gt;" in _characteristic_math("<b>x</b>")
