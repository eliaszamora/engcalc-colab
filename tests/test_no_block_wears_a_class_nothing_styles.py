r"""Three tables on one page, and two of them were never styled.

`governing` and `summary` emit `<div class="engcalc-characteristic">` — singular. The
only rules anyone ever wrote are for `engcalc-characteristics` — plural, on the block that
`extrema` and `roots` use. One letter, and nothing in the page matches, so both blocks
fall back to the browser's defaults.

Measured in a browser rather than argued from a screenshot:

    block                     font-size   cell padding   row rule
    engcalc-characteristic      16 px         1 px         none      <- governing
    engcalc-table            14.72 px      4.5 x 9.9 px    yes
    engcalc-characteristic      16 px         1 px         none      <- summary

The columns do line up - a `<table>` does that much unaided - so what the reader sees is
not a broken table but three tables in two sizes, two of them with their cells touching.

The general statement is the one that would have caught it and is the first contract
below: **a block must not wear a class nothing defines.** A class name is a promise that
a rule exists somewhere, and nothing checked the promise.

The fix uses inline `style=` attributes rather than a `<style>` block, and that is
deliberate. A `<style>` does not survive a `Markdown` output - measured in Colab - and the
next change moves these blocks to `Markdown` so their mathematics finally typesets.
Inline styles work in both, so this is the implementation that does not have to be written
twice.

**The blocks are `Math` outputs now** (`test_a_computed_block_is_written_like_the_working`),
so there is no class and no inline style left to get wrong, and "the same size" is MathJax's
for all of them. What this file asked stays asked, of the form a `Math` block can take: one
frame for every block, and room between a table's cells.
"""

import pytest

import engcalc_colab.magic as magic
from conftest import block_text


@pytest.fixture
def blocks(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> list[str]:
        captured.clear()
        magics.eng("", source)
        return [
            data
            for data in (str(getattr(obj, "data", "")) for obj in captured)
            if r"\phantom{0} \\[-4pt]" in data
        ]

    return run


SHEET = (
    "L := 6.00*m\n"
    "qD := 18*kN/m\n"
    "qL := 12*kN/m\n"
    "P := 40*kN\n"
    "M_D(x) = qD*x*(L - x)/2\n"
    "M_L(x) = qL*x*(L - x)/2\n"
    "M_P(x) = P*x/2\n"
    "case D = M_D(x)\n"
    "case Lv = M_L(x)\n"
    "case Mo = M_P(x)\n"
    "combo U1 = 1.2*D + 1.6*Lv\n"
    "combo U2 = 1.2*D + 1.6*Mo\n"
    "governing(U1(x), U2(x), x, 0, L)\n"
    "table(U1(x), U2(x), x, 0, L, 4)\n"
    "extrema(U1(x), x, 0, L)\n"
    "M_u = U1(L/2)\n"
    "report(M_u)\n"
    "summary()\n"
)


def test_no_block_wears_a_class_nothing_styles(blocks):
    """The general statement, which a `Math` block keeps by carrying no markup at all."""
    found = blocks(SHEET)
    assert len(found) == 4, len(found)
    for block in found:
        assert "class=" not in block and "<" not in block, block[:200]


def test_every_table_on_a_page_is_the_same_size(blocks):
    """Three tables in two sizes is what the reader saw. Every block now opens with the one
    frame, so none of them can be set at a size of its own."""
    frames = {block.split(r"\textbf")[0].split(r"\begin{array}{l|")[0] for block in blocks(SHEET)}
    assert frames == {r"\hspace{0.2em}\begin{array}{l} \phantom{0} \\[-4pt] \displaystyle "}, frames


def test_the_cells_of_every_table_are_given_room(blocks):
    """`0.00 cm to 266.67 cm` and `U1(x)` sat against each other. A span and the response
    that governs it are a quad apart, and a table's rows are spaced."""
    found = blocks(SHEET)
    governing = next(block for block in found if "Governing" in block)
    assert r"& \qquad" in governing, governing
    table = next(block for block in found if r"\hline" in block)
    assert r"\\[3pt]" in table, table


# --- what must not move ---------------------------------------------------------------


def test_the_blocks_still_say_what_they_said(blocks):
    """Styling is not content. Every one of these was on the page before."""
    page = block_text("".join(blocks(SHEET)))
    for text in ("Governing", "Summary", "Extrema", "kN·m"):
        assert text in page, (text, page[:200])
