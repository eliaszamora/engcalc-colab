r"""A 1x1 matrix is printed as the number it holds, not as a matrix of one.

The frame memoria's answer - the whole point of the sheet - read

    k_eq  =  [70303.22] kN/m

because a static condensation stays 1x1 all the way through: `K_dd + K_id^T C` is a 1x1
plus a 1x1. Mathematically it *is* a matrix, and SymPy prints it as one. MATLAB and
Mathcad both print a 1x1 as a scalar, and so does an engineer writing the line by hand.

The sheet's own author worked around it on the next line, `keep k_e = k_eq[1, 1]`, which
is the signal that the brackets were in the way.

**Three stages, not one.** A 1x1 result prints brackets in the definition, in the
substitution and in the value:

    k  =  [2 a]
       =  [2 (3.00 kN)]
       =  [6.00] kN

so fixing only the value would have left a page that brackets its formula and not its
answer, which is worse than bracketing both. Two places cover all three: an override on
the LaTeX printer that `_NumericSubstitutionLatexPrinter` inherits, and the cell
assembler the numeric matrix path uses.
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

    return run


def _rows(latex: str) -> list[str]:
    out = []
    for row in latex.split(r"\\[8pt]"):
        row = row.replace(r"\displaystyle", "").replace(r"\end{array}", "")
        row = row.split("& = &")[-1].strip()
        if row:
            out.append(row)
    return out


CONDENSATION = "a := 3*kN\nS = [1, 0]\nK = [2, 0; 0, 5]\nk = S*K*transpose(S)\n"


def test_the_definition_of_a_one_by_one_has_no_brackets(cell):
    rows = _rows(cell(CONDENSATION))
    assert rows[-1] == "2", rows


def test_the_substitution_and_the_value_have_none_either(cell):
    """All three stages or none: a page that brackets its formula and not its answer is
    worse than one that brackets both."""
    rows = _rows(cell(CONDENSATION + "v = k*a\nnumeric(v)\n"))
    assert all(r"\begin{matrix}" not in row for row in rows[-3:]), rows[-3:]
    assert "6.00" in rows[-1], rows
    assert r"\mathrm{kN}" in rows[-1], rows


def test_the_frame_answer_reads_as_a_number(cell):
    """The line this is for: a lateral stiffness from a static condensation."""
    sheet = (
        "K = [4, 6, 0; 6, 24, 6; 0, 6, 4]\n"
        "S_i = [1, 0, 0; 0, 0, 1]\n"
        "S_d = [0, 1, 0]\n"
        "K_ii = S_i*K*transpose(S_i)\n"
        "K_id = S_i*K*transpose(S_d)\n"
        "K_dd = S_d*K*transpose(S_d)\n"
        "k_eq = K_dd + transpose(K_id)*(-inv(K_ii)*K_id)\n"
        "numeric(k_eq)\n"
    )
    final = _rows(cell(sheet))[-1]
    assert r"\begin{matrix}" not in final, final
    assert "6.00" in final, final


# --- what must not move ---------------------------------------------------------------

@pytest.mark.parametrize(
    "definition, shape",
    [
        ("M = [1, 2]", "1x2"),
        ("M = [1; 2]", "2x1"),
        ("M = [1, 2; 3, 4]", "2x2"),
    ],
)
def test_every_other_shape_keeps_its_brackets(cell, definition, shape):
    """One is the only number of cells a reader cannot tell from a scalar. A 1x2 is
    still visibly a matrix and must stay one."""
    final = _rows(cell(definition + "\n"))[-1]
    assert r"\begin{matrix}" in final, (shape, final)


def test_a_one_by_one_of_quantities_keeps_its_unit(cell):
    """Dropping the brackets must not drop what is outside them."""
    final = _rows(cell("a := 5*kN\nM = [a]\nnumeric(M)\n"))[-1]
    assert "5.00" in final, final
    assert r"\mathrm{kN}" in final, final
    assert r"\begin{matrix}" not in final, final


def test_the_value_is_untouched(cell):
    """Presentation only, as everywhere else in this renderer."""
    rows = _rows(cell(CONDENSATION + "v = k*a\nnumeric(v)\n"))
    assert "6.00" in rows[-1], rows
