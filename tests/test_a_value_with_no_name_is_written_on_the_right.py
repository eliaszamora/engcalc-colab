r"""A value with no name on its left is written in the right-hand column.

The engineer's first three-storey modal memoria on 0.31.0, in Colab:

    lam                                                            =  de|
    {λ = 897.61 1/s², m = 1 ; λ = 5634.70 1/s², m = 1 ; λ = 11982.85 1/s², m = 1}
    w₁                                                             =  √|
                                                                   =  29|
    T₁                                                             =  2|

Every `=` on the block pushed to the right edge, and every result cut off by it.

**Why.** A block is one `lcl` array: names, `=`, values. `numeric(lam)` answers with a
set and no name, and a row with nothing to put left of an `=` was written entirely in the
first column - `{λ = …} & &`. That set is about 700 px wide, so the name column of the
whole block became 700 px wide, and a 900 px notebook had 200 px left for every value on
it. The rule dates from when such a row was a short expression like `x² + 1`; a matrix,
an eigenvalue set or a long expression breaks it.

**So such a row is written in the right-hand column**, with the values - where an
equation `solve` shows already sits (` & & k - m w² = 0`) - and the name column is only
ever as wide as a name. Still no `=` that nobody wrote.
"""

import re

import engcalc_colab.magic as magic

from conftest import without_spacer_rows


def page(monkeypatch, source: str) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", source)
    # The room a matrix is given is not a row; see test_a_matrix_row_has_room.
    return without_spacer_rows("".join(str(getattr(obj, "data", "")) for obj in captured))


def left_cells(math: str) -> list[str]:
    """The first cell of every row of every aligned array."""
    cells = []
    for block in re.findall(r"\\begin\{array\}\{lcl\}(.*?)\\end\{array\}", math, re.S):
        depth = 0
        row = ""
        rows = []
        index = 0
        while index < len(block):
            if block.startswith("\\begin{matrix}", index):
                depth += 1
            elif block.startswith("\\end{matrix}", index):
                depth -= 1
            if depth == 0 and block.startswith("\\\\", index):
                rows.append(row)
                row = ""
                index = block.find("]", index) + 1 if block.startswith("\\\\[", index) else index + 2
                continue
            row += block[index]
            index += 1
        rows.append(row)
        for text in rows:
            depth = 0
            for position, char in enumerate(text):
                if text.startswith("\\begin{matrix}", position):
                    depth += 1
                elif text.startswith("\\end{matrix}", position):
                    depth -= 1
                elif char == "&" and depth == 0:
                    cells.append(text[:position].strip())
                    break
    return cells


MODES = (
    "k_1 := 2500*kN/m\nk_2 := 2000*kN/m\nk_3 := 1500*kN/m\n"
    "m_1 := 550*kg\nm_2 := 500*kg\nm_3 := 450*kg\n"
    "K = [k_1 + k_2, -k_2, 0; -k_2, k_2 + k_3, -k_3; 0, -k_3, k_3]\n"
    "M = diag(m_1, m_2, m_3)\n"
    "lam = eigenvals(inv(M)*K)\nnumeric(lam)\n"
    "w_1 = sqrt(lam[1])\nnumeric(w_1)\n"
)


def test_the_eigenvalue_set_does_not_widen_the_name_column(monkeypatch, capsys):
    math = page(monkeypatch, MODES)
    capsys.readouterr()

    assert r"\lambda=897.61" in math, math
    for cell in left_cells(math):
        assert r"\lambda=" not in cell, cell
        assert len(cell) < 40, cell


def test_the_set_is_in_the_value_column(monkeypatch, capsys):
    math = page(monkeypatch, MODES)
    capsys.readouterr()

    assert re.search(r"\\\\\[\d+pt\]\s*& & \\displaystyle \\left\\\{\\lambda=897\.61", math), math


def test_a_short_expression_goes_there_too_without_an_equals(monkeypatch, capsys):
    math = page(monkeypatch, "x^2 + 1\n")
    capsys.readouterr()

    assert r" & & \displaystyle x^{2} + 1" in math, math
    assert " & = & " not in math, math


def test_a_bare_matrix_is_in_the_value_column(monkeypatch, capsys):
    math = page(monkeypatch, "A = [1, 2; 3, 4]\nA^2\n")
    capsys.readouterr()

    assert r" & & \displaystyle \left[\begin{matrix}\displaystyle 7" in math, math
