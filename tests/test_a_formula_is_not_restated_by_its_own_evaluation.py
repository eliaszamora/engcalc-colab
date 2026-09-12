r"""A definition immediately followed by its evaluation prints the formula once.

`## v0.23.2 an equation is written once` fixed this shape for `solve`: an equation
passed by name is already on the page under that name, so the solve leaves it there. The
same repeat survives one call along:

    M = q*L^2/8
    numeric(M)

    M   =   q L^2 / 8            <- the definition
    M   =   q L^2 / 8            <- the evaluation's opening stage
        =   (10.00 kN/m)(6.00 m)^2 / 8
        =   45.00 kN*m

It is on the repository's own reference memoria, twice - `d_max` and `d_adm` both do it.

The discriminator is *not* the one v0.23.2 used. "The argument is a name already bound"
would also strip the formula from an evaluation written far below its definition, and
there that row is the only thing on the page saying which formula is being evaluated:

    M = q*L^2/8
    V = q*L/2
    numeric(V)
    numeric(M)      <- four rows below M's definition; the formula earns its place

What is wrong is narrower and can be stated exactly: the block's opening row is, character
for character, the row immediately above it. Nothing else is touched, and the rule cannot
over-apply, because it compares rendered rows rather than reasoning about names.

Dropping that row leaves the block well formed on its own. Every row after the first
already carries an empty left-hand side, so the definition simply becomes the opening of
the derivation and the array's alignment is unchanged.
"""

import re

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.renderer import render_aligned_results


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> str:
        captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def _rows(latex: str) -> list[str]:
    body = latex.split(r"\begin{array}{lcl}")[-1].split(r"\end{array}")[0]
    rows = []
    for chunk in body.split(r"\\"):
        chunk = chunk.strip()
        if chunk.startswith("["):
            chunk = chunk.split("]", 1)[-1].strip()
        if chunk:
            rows.append(chunk)
    return rows


BEAM = "q := 10*kN/m\nL := 6*m\n"


def test_a_definition_and_its_evaluation_print_the_formula_once(cell):
    rows = _rows(cell(BEAM + "M = q*L**2/8\nnumeric(M)\n"))
    formula_rows = [row for row in rows if r"\frac{q L^{2}}{8}" in row]
    assert len(formula_rows) == 1, rows


def test_the_derivation_still_reads_as_one_block(cell):
    """Dropping the repeat must leave a whole derivation, not a headless one."""
    rows = _rows(cell(BEAM + "M = q*L**2/8\nnumeric(M)\n"))
    tail = rows[-3:]
    assert tail[0].startswith(r"\displaystyle M & = &"), tail
    assert r"\frac{q L^{2}}{8}" in tail[0], tail
    assert tail[1].startswith("& = &"), tail
    assert tail[2].startswith("& = &") and "45.00" in tail[2], tail


def test_an_evaluation_away_from_its_definition_still_shows_the_formula(cell):
    """The case that makes the v0.23.2 rule the wrong one to copy here."""
    rows = _rows(cell(BEAM + "M = q*L**2/8\nV = q*L/2\nnumeric(V)\nnumeric(M)\n"))
    formula_rows = [row for row in rows if r"\frac{q L^{2}}{8}" in row]
    assert len(formula_rows) == 2, rows


def test_an_inline_expression_is_untouched(cell):
    """No name, nothing above to repeat."""
    rows = _rows(cell(BEAM + "numeric(q*L**2/8)\n"))
    assert any("45.00" in row for row in rows), rows
    assert any(r"\frac{q L^{2}}{8}" in row for row in rows), rows


def test_the_compact_result_alias_prints_the_formula_once(cell):
    """`result(...)` skips the substitution stage but opens the same way."""
    rows = _rows(cell(BEAM + "M = q*L**2/8\nresult(M)\n"))
    formula_rows = [row for row in rows if r"\frac{q L^{2}}{8}" in row]
    assert len(formula_rows) == 1, rows
    assert any("45.00" in row for row in rows), rows


def test_a_block_is_never_emptied(cell):
    """A single-row result whose row repeats the one above has nothing left once the
    repeat is dropped. Two identical definitions are a sheet's own business, and
    swallowing the second would be a worse answer than printing it."""
    rows = _rows(cell(BEAM + "M = q*L**2/8\nM = q*L**2/8\n"))
    formula_rows = [row for row in rows if r"\frac{q L^{2}}{8}" in row]
    assert len(formula_rows) == 2, rows


def test_no_two_consecutive_rows_are_identical_on_the_reference_memoria(cell):
    """The page-level invariant, on the sheet `tools/render_memoria.py` drives. It had
    two of these before, and no contract could see them."""
    import pathlib

    source = pathlib.Path("tools/memoria.eng").read_text(encoding="utf-8")
    latex = cell(source)
    for blob in latex.split(r"\begin{array}{lcl}")[1:]:
        rows = _rows(r"\begin{array}{lcl}" + blob)
        repeats = [a for a, b in zip(rows, rows[1:]) if a == b]
        assert not repeats, repeats


def test_an_evaluation_repeated_twice_keeps_both_formulas(cell):
    """Which row above is compared, and the contract the first draft did not have.

    Two `numeric(M)` in a row: the second block's opening equals the *first* row of the
    block above it, and not its last. Comparing against the wrong end of the previous
    block swallows the second derivation's formula while every other test here passes.
    Repeating an evaluation is unusual, and printing it whole is the only honest answer
    when a sheet does.
    """
    rows = _rows(cell(BEAM + "M = q*L**2/8\nnumeric(M)\nnumeric(M)\n"))
    formula_rows = [row for row in rows if r"\frac{q L^{2}}{8}" in row]
    assert len(formula_rows) == 2, rows
    assert len([row for row in rows if "45.00" in row]) == 2, rows


def test_a_suppressed_block_keeps_its_own_row_spacings(cell):
    """The spacings are computed from the whole block and then the first row is
    dropped, so the rows that remain keep the spacing they would have had.

    A mutation survived the first draft for want of this. A wrapped substitution marks
    its continuation `4pt` where a new stage is `8pt` - the difference between a line
    that continues and a line that says something new. Replacing them all with the
    between-results `8pt` changed the page and no test saw it, because every other test
    here uses a block short enough not to wrap.

    The block used to be the deflection, and the deflection stopped wrapping once a
    fraction was measured across instead of end to end - its wrapping *was* a defect. A
    long product has no fraction to stack, so it still needs the rows.
    """
    latex = cell(
        "a := 1.11*m\nb := 2.22*m\nc := 3.33*m\nd := 4.44*m\ne := 5.55*m\n"
        "f := 6.66*m\ng := 7.77*m\nh := 8.88*m\ni := 9.99*m\n"
        "I_z := 80e6*mm**4\n"
        "p = a*b*c*d*e*f*g*h*i*I_z\nnumeric(p)\n"
    )
    body = latex.split(r"\displaystyle a b c d e f g h i I_{z}")[-1]
    spacings = re.findall(r"\\\\\[(\d+pt)\]", body)
    assert spacings == ["8pt", "4pt", "8pt"], spacings


def test_render_aligned_results_accepts_an_empty_list():
    assert render_aligned_results([]) == ""
