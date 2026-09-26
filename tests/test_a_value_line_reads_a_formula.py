r"""A `:=` line reads a name the sheet defined with `=`, as it already read a matrix.

His exercise 2.1, 2026-09-25: `delta_ab = F_ab*L_ab/(E*A_ab)` then
`D := [delta_ab; delta_ac]` stopped at "unknown numeric name 'delta_ab'", and the sheet
had to write each formula again inside `D`. A `:=` line already read a matrix the sheet
built with `=` (`d := solve(K, F)`) and a name it kept (`keep a = ...`); a plain scalar
formula was the one thing it could not read. He left the choice to me (2026-09-26).

It reads the formula's number with the values settled so far, which is what a `:=` line
means: a value, taken when it is written - as `y := 2*x` does. A formula that still needs
a value says which. Only a name that read as nothing before is read this way: a formula
named like a unit (`m`, `s`, `N`) still reads as the unit it did, with the notice it had,
so no sheet that worked changes.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str):
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), console.getvalue()

    return run


def test_a_value_line_reads_a_scalar_formula(sheet):
    page, console = sheet("a := 2*m\nz = 4*a\nw := z + a\n")
    assert not console, console
    assert r"w & = & \displaystyle 10.00\,\mathrm{m}" in page, page


def test_his_matrix_reads_the_two_elongations(sheet):
    page, console = sheet(
        "E := 200000*MPa\nA_ab := 6000*mm^2\nA_ac := 8000*mm^2\nF_ab := 400.6*kN\n"
        "F_ac := -277.8*kN\nL_ab := sqrt(6^2 + 4^2)*m\nL_ac := 5*m\n"
        "delta_ab = F_ab*L_ab/(E*A_ab)\ndelta_ac = F_ac*L_ac/(E*A_ac)\n"
        "C := [6*m/L_ab, 4*m/L_ab; -3*m/L_ac, 4*m/L_ac]\nD := [delta_ab; delta_ac]\n"
        "d := solve(C, D)\nnumeric(d, mm)\n"
    )
    assert not console, console
    assert "2.41" in page and "0.72" in page, page


def test_the_value_is_the_one_settled_when_the_line_is_written(sheet):
    page, console = sheet("a := 2*m\nz = 4*a\nw := z\na := 3*m\nnumeric(z)\n")
    assert not console, console
    assert r"w & = & \displaystyle 8.00\,\mathrm{m}" in page, page
    assert r"12.00\,\mathrm{m}" in page, page


def test_a_formula_that_still_needs_a_value_says_which(sheet):
    _page, console = sheet("z = 4*b\nw := z\n")
    assert "line 2" in console and "z" in console and "b" in console, console
    assert "unknown numeric name" not in console, console


def test_a_formula_of_a_value_line_reads_on_in_a_formula(sheet):
    # And what the value line computed is a value like any other.
    page, console = sheet("a := 2*m\nz = 4*a\nw := 2*z\nnumeric(w)\n")
    assert not console, console
    assert r"16.00\,\mathrm{m}" in page, page


def test_a_formula_named_like_a_unit_still_reads_as_the_unit(sheet):
    # As before this change: `m` on a `:=` line is the metre, whatever `m = ...` said.
    page, _console = sheet("a := 2*kg\nm = 3*a\nx := 4*m\n")
    assert r"x & = & \displaystyle 4.00\,\mathrm{m}" in page, page
