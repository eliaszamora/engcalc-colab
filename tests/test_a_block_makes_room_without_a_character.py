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

Since 2026-09-25 a block has no room of its own at all: the room between any two blocks is
one rule, the magic's spacer (`magic.BLOCK_SPACER`, see `test_one_spacing_rule`), measured
in his Colab. What this file still pins is that nothing in a block is a character with no
ink, and that each block stands apart from the next.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic
from conftest import block_text
from engcalc_colab.magic import BLOCK_SPACER

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

OPENS = r"\hspace{0.2em}\begin{array}{l} "


@pytest.fixture
def captured(monkeypatch):
    shown = []
    monkeypatch.setattr(magic, "display", shown.append)
    magic.EngMagics().eng("", SHEET)
    return shown


@pytest.fixture
def blocks(captured):
    found = [item.data for item in captured if isinstance(item, Math) and item.data.startswith(OPENS)]
    assert found, "no computed block reached the notebook"
    return found


def test_no_computed_block_makes_room_with_a_character(blocks):
    """Five kinds of block in one cell, because they share one frame and one defect."""
    assert len(blocks) == 5
    for block in blocks:
        assert r"\phantom" not in block, block[:120]


def test_a_block_carries_no_room_of_its_own(blocks):
    for block in blocks:
        assert block.startswith(OPENS + r"\displaystyle "), block[:120]
        assert r"\rule{0pt}{0.7em}" not in block, block[:120]


def test_each_block_stands_apart_by_the_one_rule(captured):
    """Between any two outputs of the cell, the same spacer - and none inside a block."""
    for before, after in zip(captured, captured[1:]):
        is_room = [getattr(item, "data", None) == BLOCK_SPACER for item in (before, after)]
        assert any(is_room), (before, after)
        assert not all(is_room), (before, after)


def test_each_block_still_says_what_it_said(blocks):
    """The room is what changed. Nothing above it or below it may have moved."""
    page = " ".join(block_text(block) for block in blocks)
    assert "Roots — V(x)" in page
    assert "Extrema — M(x)" in page
    assert "Domain: 0.00 m to 6.00 m" in page
    assert "x = L/2 (3.00 m)" in page
    assert "Governing along x" in page
    assert "Summary" in page and "M_u" in page.replace(" ", "").replace("Mu", "M_u")
