r"""The rows of a matrix have room, and so does a matrix from the one above it.

    k_v = [12EI/L^3  6EI/L^2 ...
           6EI/L^2   4EI/L   ...        the L^3 of one row sat on the 6EI of the next

A matrix joined its rows with a bare `\\`, and every cell is set in display style so a
fraction is not smaller than the `0` beside it. He asked on 2026-09-23, reading `k_v` in his
matrix derivation, whether the entries were touching. 0.33.1 answered `\\[6pt]`, measured in
the preview; 0.33.2 answered `\\[12pt]`, chosen by eye in his Colab. Both were measured
against the wrong model of the renderer, and the second found two things the first missed.

**Colab typesets with KaTeX 0.16.28, not MathJax.** Asked from inside an output on
2026-09-23: `window.MathJax` is absent, `katex.version` is 0.16.28, loaded from gstatic. And
KaTeX reads `\\[len]` as LaTeX does (`\@argarraycr`): the row is made *at least* `len` plus
a strut's depth deep - nothing is added to a row already deeper. MathJax, in the preview,
adds `len` every time. So:

- Between two rows of a matrix `len` does what it says only for rows no deeper than it.
  That is every row of fractions, which is what `12pt` was chosen on, and the one tall
  kind a matrix of this repository holds.
- Between two rows of the *working*, a matrix is deeper than any `\\[8pt]`, and two matrices
  one above the other touched: `T_f` on `K_f`, `K_22c` on `F_c` on `d_c`. `24pt` still
  touched under a four-row stiffness matrix. What adds room whatever the depth is a row of
  its own, the spacer `_computed_block` already uses, `\rule{0pt}{0.7em}`: in KaTeX an
  empty row is a strut's full height and depth. Put wherever a row of the working holds a
  matrix, above or below.

**A matrix of plain entries does not need a fraction's room.** `12pt` between `c_θ` and
`-s_θ` read loose; `3pt` read like the fraction matrix at `12pt` beside it. The room
between two rows is `12pt` when either holds something tall - a fraction, an integral, a
sum - and `3pt` otherwise.

Every matrix, symbolic or numeric, is built by `_matrix_from_cells_latex`. The width
estimator reads a row's space as nothing: it adds height, not width.
"""

import pytest

from IPython.display import Math

import engcalc_colab.magic as magic
from engcalc_colab.renderer import (
    _MATRIX_PLAIN_ROW_SEPARATOR as PLAIN,
    _MATRIX_ROW_SEPARATOR as TALL,
    _latex_visual_width,
    _matrix_from_cells_latex,
)

SPACER = r"\rule{0pt}{0.7em}"


@pytest.fixture
def page(monkeypatch, capsys):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        assert "engcalc:" not in capsys.readouterr().out
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


# --- inside a matrix -------------------------------------------------------------------


def test_the_rows_of_a_stiffness_matrix_have_room(page):
    shown = page("k = [12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L]\n")
    assert rf"\frac{{6 E I}}{{L^{{2}}}}{TALL}\displaystyle \frac{{6 E I}}{{L^{{2}}}}" in shown, shown


def test_a_matrix_in_units_per_length_takes_the_room_of_its_entries(page):
    """The formula's entries are `2 kN/m`, set as fractions, and tall; the value takes the
    common unit out, `[2.00, -1.00; ...] kN/m`, and its entries are plain numbers."""
    shown = page("K = [2*kN/m, -1*kN/m; -1*kN/m, 2*kN/m]\nnumeric(K)\n")
    first = shown[shown.index(r"\begin{matrix}"):shown.index(r"\end{matrix}")]
    last = shown[shown.rindex(r"\begin{matrix}"):shown.rindex(r"\end{matrix}")]
    assert TALL in first and PLAIN not in first, first
    assert PLAIN in last and TALL not in last, last


def test_a_matrix_of_plain_entries_has_less(page):
    shown = page("T = [c, s; -s, c]\n")
    assert PLAIN in shown and TALL not in shown, shown


def test_a_column_of_plain_entries_has_less(page):
    shown = page("F = [0; -P; 0]\n")
    assert shown.count(PLAIN) == 2 and TALL not in shown, shown


def test_a_boundary_takes_the_room_of_its_taller_row():
    """`[0; P L^3/(3EI); 0]`: both boundaries touch the fraction, so both are tall."""
    latex = _matrix_from_cells_latex([["0"], [r"\frac{P L^{3}}{3 E I}"], ["0"], ["1"]])
    assert latex.count(TALL) == 2, latex
    assert latex.count(PLAIN) == 1, latex


@pytest.mark.parametrize(
    "cell",
    [
        r"\frac{a}{b}",
        r"- \dfrac{a}{b}",
        r"\int\limits_{0}^{L} x\, dx",
        r"\sum_{i=1}^{n} x_{i}",
        r"\left(\begin{matrix} a \\ b \end{matrix}\right)",
    ],
)
def test_what_counts_as_tall(cell):
    latex = _matrix_from_cells_latex([["0"], [cell]])
    assert TALL in latex, latex


@pytest.mark.parametrize("cell", [r"c_{\theta}^{2}", r"2.00\,\mathrm{kN}", r"\sqrt{2}", r"a b"])
def test_what_does_not(cell):
    latex = _matrix_from_cells_latex([["0"], [cell]])
    assert PLAIN in latex and TALL not in latex, latex


def test_a_single_row_has_no_separator():
    latex = _matrix_from_cells_latex([["a", "b", "c"]])
    assert r"\\" not in latex, latex


def test_a_one_by_one_is_still_its_number():
    assert _matrix_from_cells_latex([["5"]]) == "5"


def test_the_room_costs_no_width():
    """Height only: a matrix is not judged wider, and so not split sooner, for it."""
    rows = [[r"\frac{12 E I}{L^{3}}", r"\frac{6 E I}{L^{2}}"], [r"\frac{6 E I}{L^{2}}", r"\frac{4 E I}{L}"]]
    spaced = _matrix_from_cells_latex(rows)
    bare = spaced.replace(TALL, r"\\")
    assert _latex_visual_width(spaced) == _latex_visual_width(bare)


# --- between rows of the working ---------------------------------------------------------


def _between(shown: str, above: str, below: str) -> str:
    """What stands between the row that holds `above` and the next row that holds `below`."""
    start = shown.index(above) + len(above)
    return shown[start:shown.index(below, start)]


def test_two_matrices_one_above_the_other_have_a_spacer_between(page):
    shown = page("T = [c, s; -s, c]\nK = [12*E*I/L^3, 0; 0, E*A/L]\n")
    between = _between(shown, r"\end{matrix}\right]", r"K & = &")
    assert SPACER in between, between


def test_a_matrix_and_the_row_below_it(page):
    shown = page("F = [0; -P; 0]\nx = P/L\n")
    between = _between(shown, r"\end{matrix}\right]", r"x & = &")
    assert SPACER in between, between


def test_a_row_and_the_matrix_below_it(page):
    shown = page("x = P/L\nF = [0; -P; 0]\n")
    between = _between(shown, r"\frac{P}{L}", r"F & = &")
    assert SPACER in between, between


def test_the_stages_of_one_matrix_have_it_too(page):
    """`numeric(K)` stacks the formula's matrix over the value's."""
    shown = page("k_1 := 2000*kN/m\nK = [k_1, -k_1; -k_1, k_1]\nnumeric(K)\n")
    last = shown[shown.rindex(r"\displaystyle K & = &"):]
    assert last.count(SPACER) >= 1, last


def test_rows_without_a_matrix_are_as_they_were(page):
    shown = page("N_b = E*A*(u_2 - u_1)/L\nf_1 = -N_b\n")
    assert SPACER not in shown, shown
    assert r"\\[8pt] \displaystyle f_{1}" in shown, shown
