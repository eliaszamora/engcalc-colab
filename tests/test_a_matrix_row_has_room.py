r"""The rows of a matrix are set as far apart as its columns.

    k_v = [12EI/L^3  6EI/L^2 ...
           6EI/L^2   4EI/L   ...        the L^3 of one row sat on the 6EI of the next

A matrix joined its rows with a bare `\\`, and every cell is set in display style so a
fraction is not smaller than the `0` beside it. A display fraction is tall, and between
one row's denominator and the next row's numerator there was 5.7 px at 14 px type, where
the columns stand at least 14 px apart. He asked on 2026-09-23, reading `k_v` in his
matrix derivation, whether the entries were touching, and chose the separation that makes
the two the same: `\\[6pt]`, measured at 14.2 px between rows of `k_v`.

Every matrix, symbolic or numeric, is built by `_matrix_from_cells_latex`, so all of them
take it. The width estimator reads the separator as nothing, the way it reads a `cases`
separator: it adds height, not width.
"""

import pytest

from IPython.display import Math

import engcalc_colab.magic as magic
from engcalc_colab.renderer import _latex_visual_width, _matrix_from_cells_latex

ROW = r"\\[6pt]"


@pytest.fixture
def page(monkeypatch, capsys):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        assert "engcalc:" not in capsys.readouterr().out
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def test_the_rows_of_a_stiffness_matrix_have_room(page):
    shown = page("k = [12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L]\n")
    assert rf"\frac{{6 E I}}{{L^{{2}}}}{ROW}\displaystyle \frac{{6 E I}}{{L^{{2}}}}" in shown, shown


def test_a_numeric_matrix_has_the_same_room(page):
    shown = page("K = [2*kN/m, -1*kN/m; -1*kN/m, 2*kN/m]\nnumeric(K)\n")
    body = shown[shown.rindex(r"\begin{matrix}"):]
    assert ROW in body, body
    assert r"\\\displaystyle" not in body, body


def test_a_column_has_it_too(page):
    shown = page("F = [0; -P; 0]\n")
    assert shown.count(ROW) == 2, shown


def test_every_row_boundary_has_it():
    latex = _matrix_from_cells_latex([["a", "b"], ["c", "d"], ["e", "f"]])
    assert latex.count(ROW) == 2, latex
    assert latex.replace(ROW, "").count(r"\\") == 0, latex


def test_a_single_row_has_no_separator():
    latex = _matrix_from_cells_latex([["a", "b", "c"]])
    assert r"\\" not in latex, latex


def test_a_one_by_one_is_still_its_number():
    assert _matrix_from_cells_latex([["5"]]) == "5"


def test_the_room_costs_no_width():
    """Height only: a matrix is not judged wider, and so not split sooner, for it."""
    rows = [[r"\frac{12 E I}{L^{3}}", r"\frac{6 E I}{L^{2}}"], [r"\frac{6 E I}{L^{2}}", r"\frac{4 E I}{L}"]]
    spaced = _matrix_from_cells_latex(rows)
    bare = spaced.replace(ROW, r"\\")
    assert _latex_visual_width(spaced) == _latex_visual_width(bare)
