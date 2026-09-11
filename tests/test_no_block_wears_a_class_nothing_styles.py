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
"""

import re

import pytest

import engcalc_colab.magic as magic


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
            for data in (getattr(obj, "data", "") for obj in captured)
            if data.startswith("<")
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
    """The general statement. A class name promises a rule exists; nothing checked it."""
    for block in blocks(SHEET):
        used = set(re.findall(r'class="([^"]+)"', block))
        used = {name for value in used for name in value.split()}
        defined = set(re.findall(r"\.([A-Za-z][A-Za-z0-9_-]*)\s*\{", block))
        assert used <= defined, (sorted(used - defined), block[:200])


def test_every_table_on_a_page_is_the_same_size(blocks):
    """Three tables in two sizes is what the reader actually sees.

    A first draft collected the sizes into one set and asked for a single element, and
    passed before the fix - because only one of the three declared a size at all, so the
    set had one member and the other two were at the browser's 16 px. Each has to state
    one, and they have to agree.
    """
    sizes = []
    for block in blocks(SHEET):
        if "<table" not in block:
            continue
        declared = re.findall(r"font-size:\s*([0-9.]+rem)", block)
        assert declared, block[:200]
        sizes.append(declared[0])
    assert len(sizes) >= 3, sizes
    assert len(set(sizes)) == 1, sizes


def test_the_cells_of_every_table_are_given_room(blocks):
    """`padding:1px` is the browser's default, which is what a cell gets when nobody
    says otherwise - and it is why `0.00 cm to 266.67 cm` and `U1(x)` sat against each
    other."""
    for block in blocks(SHEET):
        if "<table" not in block:
            continue
        assert "padding:" in block, block[:200]


# --- what must not move ---------------------------------------------------------------


def test_the_blocks_still_say_what_they_said(blocks):
    """Styling is not content. Every one of these was on the page before."""
    page = "".join(blocks(SHEET))
    for text in ("Governing", "Summary", "Extrema", "kgf" if False else "kN·m"):
        assert text in page, (text, page[:200])


def test_the_table_block_keeps_the_style_that_works(blocks):
    """`engcalc-table` is not part of this defect - its class *is* styled - so it is left
    exactly as it is. The two blocks being fixed use inline attributes instead, because a
    `<style>` does not survive a `Markdown` output (measured in Colab) and the next change
    moves them there; writing them with a rule block would be writing them twice."""
    tables = [block for block in blocks(SHEET) if "engcalc-table" in block]
    assert tables, "no table block"
    assert "<style>" in tables[0], tables[0][:200]
