r"""A computed block's room above and below is a strut, not a character with no ink.

Selecting the roots block of the engineer's frame and copying it gave

    0Roots — V(x)Domain: 0.00 m to 6.00 mx = L/2 (3.00 m) · root0

A zero at each end. `_computed_block` made its room with `\phantom{0}`, and a phantom
reserves the space of a character by *being* that character with the ink left off - so
the zero is in the block's text, in the MathML beside it, and in anything that reads the
page as text: a block pasted into a report, a search over the notebook, a diff of two
runs.

A screen reader was never affected. MathJax emits `<mphantom>` and readers skip it,
which is why this is a small defect and not a large one; it is still two characters the
block does not say.

A strut of the same height says nothing and takes the same room. Measured in MathJax at
the page's own width, not assumed: `\rule{0pt}{0.7em}` in those two rows gives a table
101.8 px tall, against 101.8 px for the phantom, with the same four row heights. Without
the rows at all the same block is 54.3 px, which is what the rows are there for.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic
from conftest import _computed_block_text, block_text

matplotlib.use("Agg")


SHEET = """L := 6*m
qD := 18*kN/m
V(x) = qD*(L/2 - x)
M(x) = qD*x*(L - x)/2
M2(x) = 1.5*M(x)
roots(V(x), x, 0, L)
extrema(M(x), x, 0, L)
table(M(x), x, 0, L, 3)
governing(M(x), M2(x), x, 0, L)
M_u = M(L/2)
report(M_u)
summary()
"""

SPACER = r"\rule{0pt}{0.7em}"
OPENS = r"\hspace{0.2em}\begin{array}{l} " + SPACER + r" \\[-4pt] "
CLOSES = r" \\[4pt] " + SPACER + r" \end{array}"


def rows_of(block: str) -> str:
    """Just the rows: the block with its frame and its two spacer rows taken off."""
    assert block.startswith(OPENS) and block.endswith(CLOSES), block[:120]
    return block[len(OPENS) : -len(CLOSES)]


@pytest.fixture
def blocks(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", SHEET)
    found = [
        item.data
        for item in captured
        if isinstance(item, Math) and r"\rule{0pt}{0.7em} \\[-4pt]" in item.data
    ]
    assert found, "no computed block reached the notebook"
    return found


def test_no_computed_block_makes_room_with_a_character(blocks):
    """Five kinds of block in one cell, because they share one frame and one defect."""
    assert len(blocks) == 5
    for block in blocks:
        assert r"\phantom" not in block, block[:120]


def test_the_room_is_still_there_above_and_below(blocks):
    for block in blocks:
        assert block.startswith(OPENS + r"\displaystyle "), block[:120]
        assert block.endswith(CLOSES), block[-60:]


def test_the_room_adds_nothing_to_what_the_block_says(blocks):
    """The block read as text is the block without its two spacer rows, read as text.

    This is the question the defect answers no to, asked so that it cannot be answered
    by a helper. `conftest.block_text` used to strip `\\phantom{0}` by name, which is
    why no contract in this repository ever saw the zeros: the reader saw them and the
    tests did not. That line is gone, so a spacer that says anything shows up here.
    """
    for block in blocks:
        whole = " ".join(_computed_block_text(block).split())
        rows = " ".join(_computed_block_text(rows_of(block)).split())
        assert whole == rows, block[:120]


def test_each_block_still_says_what_it_said(blocks):
    """The room is what changed. Nothing above it or below it may have moved."""
    page = " ".join(block_text(block) for block in blocks)
    assert "Roots — V(x)" in page
    assert "Extrema — M(x)" in page
    assert "Domain: 0.00 m to 6.00 m" in page
    assert "x = L/2 (3.00 m)" in page
    assert "Governing along x" in page
    assert "Summary" in page and "M_u" in page.replace(" ", "").replace("Mu", "M_u")
