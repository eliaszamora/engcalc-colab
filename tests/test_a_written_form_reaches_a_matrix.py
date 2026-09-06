r"""What a matrix is written with survives into the page, as it does for a scalar.

Found by working a matrix frame analysis. `keep` marks a name a later formula shows
instead of expanding, and it stopped at the edge of a matrix:

    keep A_c = b*d
    z = 2*A_c                  ->  2 A_c            the scalar path
    M = [A_c, 0; 0, A_c]       ->  [b d, 0; 0, b d] the matrix path

On the frame sheet the consequence was not cosmetic. A local stiffness matrix written in
`E`, `A_c`, `I_c` and `L_c` printed every entry expanded into `b_c d_c^3/12` and
`sqrt((-x_1 + x_2)^2 + (-y_1 + y_2)^2)`, and one row of the assembled `K_1` reached
**1889 characters**. The formulation was on the page and unreadable.

The cause is one line. `_written_form` returns None unless the value is an `sp.Expr`, and
a matrix is a `Basic` but not an `Expr`, so no matrix ever had a written form to show.
The cells themselves were never the problem: `_evaluate_matrix_literal` visits each one
through the evaluator, so `_WrittenFormEvaluator` already reaches them.

`_agrees_with` needed the second change. Its check subtracts and asks `== 0`, which is
False for a zero matrix rather than True, so every matrix would have been discarded as
disagreeing even when it agreed.
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


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


SECTION = "b := 300*mm\nd := 450*mm\nkeep A_c = b*d\nkeep I_c = b*d**3/12\n"


def test_a_kept_name_stands_for_itself_inside_a_matrix(cell):
    """`A_{c}` and not `\\mathrm{A}_{c}`: a single-letter base with a subscript is a
    quantity and stays italic. The upright rule is for a name of several letters."""
    final = _final(cell(SECTION + "M = [A_c, 0; 0, I_c]\n"))
    assert "A_{c}" in final, final
    assert "I_{c}" in final, final
    assert "b d" not in final, final


def test_the_matrix_still_evaluates_to_the_same_numbers(cell):
    """Presentation only. 300 x 450 = 135000 mm^2, and 300 x 450^3/12 = 2.278e9 mm^4."""
    final = _final(cell(SECTION + "M = [A_c, 0; 0, I_c]\nnumeric(M)\n"))
    assert "135000.00" in final or "1.35" in final, final


def test_a_coefficient_written_in_a_denominator_survives_in_a_matrix(cell):
    """The other half of the written form, which also stopped at the matrix edge."""
    final = _final(cell(
        "fc := 25*MPa\nfy := 420*MPa\nAs := 1935*mm**2\nb := 300*mm\n"
        "M = [As*fy/(0.85*fc*b)]\n"
    ))
    assert "0.85" in final, final
    assert "1.18" not in final, final


def test_a_matrix_built_on_an_unmarked_definition_still_expands(cell):
    """`keep` stays opt-in inside a matrix exactly as it is outside one."""
    final = _final(cell("b := 300*mm\nd := 450*mm\nA_c = b*d\nM = [A_c, 0; 0, A_c]\n"))
    assert "b d" in final, final


def test_a_matrix_whose_written_form_disagrees_is_not_shown():
    """`_agrees_with` is what decides, and a zero *matrix* is not `== 0`. Checking a
    matrix the way a scalar is checked discards every matrix, including the ones that
    agree - which is how this arrived in the first draft."""
    import sympy as sp

    from engcalc_colab.engine import _agrees_with

    x, y = sp.symbols("x y")
    honest = sp.Matrix([[x, 0], [0, y]])
    assert _agrees_with(honest, sp.Matrix([[x, 0], [0, y]]))
    assert not _agrees_with(honest, sp.Matrix([[x, 0], [0, x]]))
    assert not _agrees_with(honest, sp.Matrix([[x, 0]]))
