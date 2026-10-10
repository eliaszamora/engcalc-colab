r"""What 0.51.0 adds and corrects, from the inventory of open findings.

- C5a: `numeric(d)` of a matrix defined just above repeated its formula, a unit written as a
  measurement (`10*kN`) set in italic as a name.
- C2k: `solve(e1, x)` of an equation already on the page answered `2` with nothing on its left.
- C10k: a matrix typed as numbers was written twice, as typed and with decimals.
- C8j, C6i: `cot`, `sec`, `csc` and `heaviside`.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str) -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), out.getvalue()

    return run


def test_numeric_of_a_matrix_defined_above_does_not_repeat_it(sheet):
    page, printed = sheet(
        "E := 200[GPa]\nI := 1e8[mm^4]\nL := 3[m]\nK = E*I/L^3*[12, 6*L; 6*L, 4*L^2]\n"
        "d = solve(K, [10*kN; 0*kN*m])\nnumeric(d)\n"
    )
    assert not printed, printed
    assert r"\mathit{kN}" not in page, page
    assert page.count(r"\displaystyle d & = &") == 1, page
    assert r"4.50\,\mathrm{mm}" in page, page


def test_a_solve_of_an_equation_on_the_page_names_its_unknown(sheet):
    page, printed = sheet("e1 = eq(2*x + 1, 5)\nsolve(e1, x)\n")
    assert not printed, printed
    assert r"\displaystyle x & = & \displaystyle 2" in page, page


@pytest.mark.parametrize(
    ("source", "once"),
    [
        ("v := [1; 2; 3]\n", r"v & = & \displaystyle \left[\begin{matrix}\displaystyle 1.00"),
        ("w := [1[kN]; -2[kN]]\n", r"w & = & \displaystyle \left[\begin{matrix}\displaystyle 1.00"),
    ],
)
def test_a_matrix_typed_as_numbers_is_written_once(sheet, source, once):
    page, printed = sheet(source)
    assert not printed, printed
    assert once in page and page.count(r"\begin{matrix}") == 1, page


def test_a_matrix_typed_in_two_units_keeps_what_was_typed(sheet):
    page, printed = sheet("u := [500[mm]; 2[m]]\n")
    assert not printed, printed
    assert r"500\,\mathrm{mm}" in page and page.count(r"\begin{matrix}") == 2, page


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("theta := 30[deg]\nc := cot(theta)\n", r"c & = & \displaystyle 1.73"),
        ("s := sec(60[deg])\n", r"s & = & \displaystyle 2.00"),
        ("q := csc(30[deg])\n", r"q & = & \displaystyle 2.00"),
        ("y = cot(x) + sec(x)\n", r"\cot{\left(x \right)} + \sec{\left(x \right)}"),
    ],
)
def test_the_reciprocal_functions(sheet, source, expected):
    page, printed = sheet(source)
    assert not printed, printed
    assert expected in page, page


def test_a_load_that_starts_at_a_point(sheet):
    page, printed = sheet(
        "a := 2[m]\nw(x) = 5[kN/m]*heaviside(x - a)\nw_1 := w(1[m])\nw_3 := w(3[m])\n"
        "W = integrate(w(x), x, 0[m], 4[m])\nnumeric(W)\n"
    )
    assert not printed, printed
    assert r"w_{1} & = & \displaystyle 0.00" in page and r"w_{3} & = & \displaystyle 5.00" in page, page
    assert r"= & \displaystyle 10.00\,\mathrm{kN}" in page and r"\theta" not in page, page
