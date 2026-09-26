r"""A row holding a fraction keeps its room from the row below it.

`R_A = qL/2` above `R_B = qL/2` read with the denominator of one on the numerator of the
next, 0-4 px apart, in the memoria of the simply supported beam (seen on 2026-09-25; he
asked for what I noticed to be corrected). Colab's KaTeX reads `\\[4pt]` as the least depth
a row has - LaTeX's rule - and a fraction is already deeper than that, ~0.69 em, so the
space added nothing: two rows stood box to box. Matrices had the same defect (0.33.3) and
got a spacer row. A row holding a fraction now takes its depth on top of the space it was
given, so the room between it and the next is the room the page meant.
"""

import pytest

from engcalc_colab.renderer import _row_break

FRACTION = r"\displaystyle R_{A} & = & \displaystyle \frac{q L}{2}"
PLAIN = r"\displaystyle L & = & \displaystyle 6.00\,\mathrm{m}"


@pytest.mark.parametrize("spacing, deeper", [("4pt", "13pt"), ("8pt", "17pt"), ("16pt", "25pt")])
def test_a_fraction_above_takes_its_depth_on_top_of_the_space(spacing, deeper):
    assert _row_break(spacing, FRACTION, PLAIN) == rf"\\[{deeper}]"


def test_a_plain_row_above_keeps_the_space_it_was_given():
    # Only the row above: the space is the least depth of the row it follows.
    assert _row_break("8pt", PLAIN, FRACTION) == r"\\[8pt]"


def test_a_matrix_keeps_its_own_room():
    matrix = r"\displaystyle K & = & \left[\begin{matrix}1 & 2\\3 & 4\end{matrix}\right]"
    assert r"\rule{0pt}{0.7em}" in _row_break("8pt", matrix, PLAIN)
