r"""A `=` line whose names all hold values ends on its value.

    E = 200*GPa
    A_ba = 6000*mm^2
    F_ba = 400.6*kN
    L_ba = sqrt(6^2 + 4^2)*m
    delta_ba = F_ba*L_ba/E/A_ba

His exercise 2.1 (2026-09-25). The page ended on `6.68e-4 kN·m·√13/(mm²·GPa)`: the
names were replaced by their values and the units never reduced, so there was no number
to read. A `=` line keeps its formula in symbols, which is what `=` is for; but once every
name in it has a value there is nothing symbolic left, and the page owes the reader the
number. It is now written as `numeric` writes one - the formula in its names, the values
put in, the result - and only when the value would not already read as a number in a
unit: `L = 6*m` and `M = q*L^2/8` over values (`45 kN·m`) are left as they were.

Two more from the same cell, fixed with it (he asked for 2, 3 and 4):
- `sqrt(6^2 + 4^2)*m` said `'m' is read as a unit, and nothing on the sheet writes it as
  one` - it does, beside a number worked out from numbers.
- `L_ba = sqrt(6^2 + 4^2)*m` read `m √(4² + 6²)`: the unit before the number.
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
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), console.getvalue()

    return run


def rows_of(page: str, name: str) -> str:
    """The rows written under `name`, up to the next name."""
    rest = page.split(name + r" & = & ", 1)[1]
    return rest.split(r"\\[8pt] \displaystyle ", 1)[0]


EXERCISE = (
    "E = 200*GPa\nA_ba = 6000*mm^2\nF_ba = 400.6*kN\nL_ba = sqrt(6^2 + 4^2)*m\n"
    "delta_ba = F_ba*L_ba/E/A_ba\n"
)


def test_his_exercise_ends_on_the_elongation(sheet):
    page, _console = sheet(EXERCISE)
    rows = rows_of(page, r"\delta_{ba}")
    # The formula in its names, then the numbers, then the value in a unit of its kind.
    assert r"\frac{F_{ba} L_{ba}}{E A_{ba}}" in rows, rows
    assert r"2.41\,\mathrm{mm}" in rows, rows
    assert r"\sqrt{13}" not in rows and r"\mathrm{GPa}}" not in rows.rsplit("&", 1)[-1], rows


def test_the_values_are_put_into_the_formula(sheet):
    page, _console = sheet(EXERCISE)
    rows = rows_of(page, r"\delta_{ba}")
    assert r"400.60\,\mathrm{kN}" in rows and r"200.00\,\mathrm{GPa}" in rows, rows


def test_a_length_worked_out_from_numbers_ends_on_its_value(sheet):
    page, _console = sheet("L_ba = sqrt(6^2 + 4^2)*m\n")
    rows = rows_of(page, r"L_{ba}")
    assert r"7.21\,\mathrm{m}" in rows, rows
    # The number before its unit, as it was written, and the sum inside as it was written
    # too: `6² + 4²` (test_a_sum_keeps_the_order_it_was_written_in).
    assert r"\sqrt{6^{2} + 4^{2}}\,\mathrm{m}" in rows and r"\mathrm{m}\,\sqrt" not in rows, rows


@pytest.mark.parametrize(
    "source, name, row",
    [
        ("L = 6*m\n", "L", r"L & = & \displaystyle 6\,\mathrm{m}"),
        ("L = 6*m\nq = 10*kN/m\nM = q*L^2/8\n", "M", r"M & = & \displaystyle 45\,\mathrm{kN} \cdot \mathrm{m}"),
    ],
)
def test_a_value_that_already_reads_as_a_number_is_left_alone(sheet, source, name, row):
    page, console = sheet(source)
    assert not console, console
    assert row in page, page
    assert page.count(name + " & = &") == 1 and r"\left(" not in page, page


def test_a_formula_with_a_name_still_free_stays_a_formula(sheet):
    page, _console = sheet("q = 10*kN/m\nM = q*L^2/8\n")
    rows = rows_of(page, "M")
    assert "L^{2}" in rows and "& = &" not in rows, rows


@pytest.mark.parametrize(
    "line",
    ["L_ba := sqrt(6^2 + 4^2)*m\n", "L_ba = sqrt(6^2 + 4^2)*m\n", "L := (6 + 4)*m\n", "A := 2^3*m^2\n"],
)
def test_a_unit_beside_a_number_worked_out_from_numbers_is_written_as_one(sheet, line):
    _page, console = sheet(line)
    assert "read as a unit" not in console, console


def test_a_letter_alone_in_a_formula_still_says_so(sheet):
    _page, console = sheet("x := 3*kN\ny = x/m\n")
    assert "'m' is read as a unit" in console, console


def test_units_that_reduce_against_each_other_end_on_a_value(sheet):
    # A whole number in front, and still not a number in a unit: kN·m over mm.
    page, _console = sheet("F = 2*kN*m/mm\n")
    assert r"2000.00\,\mathrm{kN}" in rows_of(page, "F"), page


def test_a_fraction_in_front_ends_on_a_value(sheet):
    # SymPy keeps 400/6000 as 1/15.
    page, _console = sheet("s = 400*kN/(6000*mm^2)\n")
    assert "66.67" in rows_of(page, "s"), page


def test_a_unit_beside_arithmetic_on_a_name_is_still_a_letter(sheet):
    # `x + 1` is worked out from a value of the sheet, not from numbers alone.
    _page, console = sheet("x := 4\ny = sqrt(x + 1)*m\n")
    assert "'m' is read as a unit" in console, console
