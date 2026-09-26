r"""A unit written in brackets beside its number is a unit, whatever the sheet calls its names.

He uses `m`, `s` and `N` as names - a mass, a spacing, an axial force - and the same letters
are the metre, the second and the newton (2026-09-26). Written `6*m`, which one is meant is
decided by a rule: a value the sheet gave `m` outranks the metre. So `k := 2000*kN/m` read
kN per metre the first time a cell ran and kN per kilogram the second, once `m := 500*kg`
was below it - a wrong number, measured on 0.40.0.

`6[m]`, `10[kN/m]`, `6000[mm^2]`: what stands in brackets after a number is a unit and
nothing else, so no name of the sheet can take its place and no second run can change it.
He chose the brackets, and not to see them on the page: the memoria reads `6.00 m` as
before. `6*m` still works as it did.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def magics(monkeypatch):
    return magic.EngMagics()


def run(magics, source: str, monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magics.eng("", source)
    return " ".join(item.data for item in captured if isinstance(item, Math)), console.getvalue()


@pytest.mark.parametrize(
    "source, row",
    [
        ("L := 6[m]\n", r"L & = & \displaystyle 6.00\,\mathrm{m}"),
        ("q := 10[kN/m]\n", r"q & = & \displaystyle 10.00\,\frac{\mathrm{kN}}{\mathrm{m}}"),
        ("A := 6000[mm^2]\n", r"A & = & \displaystyle 6000.00\,\mathrm{mm}^{2}"),
        ("E := 200000[MPa]\n", r"E & = & \displaystyle 200000.00\,\mathrm{MPa}"),
        ("F := -6[kN]\n", r"F & = & \displaystyle -6.00\,\mathrm{kN}"),
        ("w := 2.8[tonf/m]\n", r"w & = & \displaystyle 2.80\,\frac{\mathrm{tonf}}{\mathrm{m}}"),
    ],
)
def test_a_value_in_brackets_reads_as_it_always_did(magics, monkeypatch, source, row):
    page, console = run(magics, source, monkeypatch)
    assert not console, console
    assert row in page, page


def test_the_page_shows_no_brackets_and_no_inner_name(magics, monkeypatch):
    page, _console = run(magics, "q := 10[kN/m]\nL := 6[m]\nM = q*L^2/8\nnumeric(M)\n", monkeypatch)
    assert "__" not in page, page
    assert r"\mathrm{m}]" not in page and "[m" not in page, page
    assert r"45.00\,\mathrm{kN} \cdot \mathrm{m}" in page, page


def test_a_name_that_is_a_unit_letter_is_the_sheet_s_name(magics, monkeypatch):
    page, console = run(magics, "m := 500[kg]\nx := 4*m\n", monkeypatch)
    assert not console, console
    assert r"x & = & \displaystyle 2000.00\,\mathrm{kg}" in page, page


def test_a_second_run_reads_as_the_first(magics, monkeypatch):
    sheet = "k := 2000[kN/m]\nm := 500[kg]\nw = sqrt(k/m)\nnumeric(w)\n"
    first, first_console = run(magics, sheet, monkeypatch)
    second, second_console = run(magics, sheet, monkeypatch)
    assert not first_console and not second_console, (first_console, second_console)
    assert first == second, (first, second)
    assert r"k & = & \displaystyle 2000.00\,\frac{\mathrm{kN}}{\mathrm{m}}" in second, second
    assert "63.25" in second, second


def test_a_formula_line_takes_a_unit_in_brackets(magics, monkeypatch):
    page, console = run(magics, "F = 5[kN]*x\nx := 2[m]\nnumeric(F)\n", monkeypatch)
    assert not console, console
    assert r"10.00\,\mathrm{kN} \cdot \mathrm{m}" in page, page


def test_a_matrix_takes_units_in_brackets(magics, monkeypatch):
    page, console = run(magics, "K := [2[kN/m], 0[kN/m]; 0[kN/m], 3[kN/m]]\n", monkeypatch)
    assert not console, console
    assert "3.00" in page and r"\frac{\mathrm{kN}}{\mathrm{m}}" in page, page


def test_what_is_not_a_unit_is_said_with_its_line(magics, monkeypatch):
    _page, console = run(magics, "a := 1[m]\nL := 6[metre_x]\n", monkeypatch)
    assert "line 2" in console and "metre_x" in console, console


def test_an_index_is_still_an_index(magics, monkeypatch):
    page, console = run(magics, "K := [1[m], 2[m]; 3[m], 4[m]]\nk := K[2,1]\n", monkeypatch)
    assert not console, console
    assert r"k & = & \displaystyle K_{2,1} = 3.00\,\mathrm{m}" in page, page


def test_a_sheet_cannot_take_the_names_the_brackets_use(magics, monkeypatch):
    _page, console = run(magics, "__u_m := 3\n", monkeypatch)
    assert "line 1" in console and "reserved" in console, console
