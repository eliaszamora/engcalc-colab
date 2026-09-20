r"""What `solve` writes is in the page's units, upright, like everything around it.

Found by a visual pass over 0.31.5, on a sheet written to draw the blocks no reference
page draws. One cell, four rows:

    w² = 25/s²          the `s` italic
    w = −5/s (−5.00 1/s)    italic in the answer, upright in the number beside it
    v² = 25/s²          the `s` upright, one block below
    discarded by v > 0: −5/s    italic again

`_print_Symbol` sets a name upright when the caller says it is a unit, and every row
that reads right is a row whose renderer was told. Three were not: the equations and the
answers of a `solve` with more than one answer, and the row that says what `assume` ruled
out. They call the printer with no unit names at all, so `s` is a variable to them.

It is the defect #96 removed from the working rows - "a unit written into a formula is
set as a unit" - in the paths it did not reach, and the page shows both spellings of the
same second within four lines.
"""

import re

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")


@pytest.fixture
def page(monkeypatch):
    def run(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return run


TWO_ANSWERS = "solve(eq(w^2, 25/s^2), w)\n"
ONE_ANSWER = "assume(v > 0)\nsolve(eq(v^2, 25/s^2), v)\n"


def test_the_equation_of_a_solve_with_two_answers_is_in_units(page):
    assert r"w^{2} = \frac{25}{\mathrm{s}^{2}}" in page(TWO_ANSWERS)


def test_each_answer_of_a_solve_with_two_answers_is_in_units(page):
    written = page(TWO_ANSWERS)
    assert r"\displaystyle \frac{5}{\mathrm{s}}" in written, written
    assert r"\displaystyle - \frac{5}{\mathrm{s}}" in written, written


def test_what_an_assumption_ruled_out_is_in_units(page):
    assert r"\text{discarded by } v > 0:\;\; - \frac{5}{\mathrm{s}}" in page(ONE_ANSWER)


@pytest.mark.parametrize("source", [TWO_ANSWERS, ONE_ANSWER])
def test_no_row_sets_the_second_as_a_variable(source, page):
    """The whole point, asked over the block rather than row by row: one spelling.

    A second set as a unit is `\\mathrm{s}`; set as a variable it is a bare `{s}`, which
    is what this looks for - every `{s}` on the block has to be the one inside a
    `\\mathrm`.
    """
    written = page(source)
    loose = re.findall(r"(?<!\\mathrm)\{s\}", written)
    assert not loose, written


# --- what must not move ---------------------------------------------------------------


def test_the_numbers_are_untouched(page):
    written = page(TWO_ANSWERS)
    assert r"-5.00\,\frac{1}{\mathrm{s}}" in written, written
    assert r"5.00\,\frac{1}{\mathrm{s}}" in written, written


def test_a_name_the_sheet_gave_a_value_to_is_still_a_name(page):
    """`s` is a unit here. Where the sheet stores a value under a name, it is that value,
    and this must not turn it upright - the same precedence the arithmetic uses."""
    written = page("s := 2*m\nsolve(eq(2*y, 6*s), y)\n")
    assert r"6 s" in written, written
    assert r"6\,\mathrm{s}" not in written, written


def test_a_system_of_equations_still_reads_as_it_did(page):
    written = page(
        "L := 6*m\nq := 10*kN/m\n"
        "eqFy = eq(R_A + R_B, q*L)\neqMA = eq(R_B*L, q*L*L/2)\n"
        "solve(eqFy, eqMA, R_A, R_B)\n"
    )
    assert r"\displaystyle R_{A} & = & \displaystyle \frac{q L}{2}" in written, written
