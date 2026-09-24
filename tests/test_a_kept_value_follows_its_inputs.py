r"""The number a kept name stands for follows the values it is made of.

    E := 200*GPa ; A := 500*mm^2 ; L := 4*m
    keep a = E*A/L
    z = 2*a
    E := 100*GPa
    numeric(z)       50000 kN/m      - the 25000 `a` was when it was kept
    numeric(a)       12500 kN/m      - the `a` it is

`keep` makes a name stand for itself in a formula, and to let `numeric` substitute it
the engine stores the number it stands for - once, when the name is kept. A value that
changed afterwards left that number behind, and one page answered two different things
for the same `a` in silence. And a name kept *before* its values were settled had no
number at all, so `numeric(z)` asked for a value for `a` that the sheet had given.

Found on 2026-09-24 while letting kept names through `subs` and `simplify`, which would
have carried both into more formulas. The number is taken again whenever a value is
settled, and dropped when it can no longer be computed.
"""

import contextlib
import io
import re

import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

VALUES = "E := 200*GPa\nA := 500*mm^2\nL := 4*m\n"


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


def answers(page: str) -> list[str]:
    """The figure each `numeric` block ends on, in kN/m."""
    return re.findall(r"(\d+\.\d+)\\,\\frac\{\\mathrm\{kN\}\}\{\\mathrm\{m\}\} (?=\\\\\[|\\end)", page)


def test_a_kept_value_follows_a_value_settled_after_it(sheet):
    page, console = sheet(VALUES + "keep a = E*A/L\nz = 2*a\nE := 100*GPa\nnumeric(z)\nnumeric(a)\n")
    assert not console, console
    found = answers(page)
    assert "25000.00" in found and "12500.00" in found, found
    assert "50000.00" not in found, found


def test_a_name_kept_before_its_values_is_given_one_when_they_are(sheet):
    page, console = sheet("keep a = E*A/L\n" + VALUES + "z = 2*a\nnumeric(z)\n")
    assert "engcalc:" not in console, console
    assert "50000.00" in answers(page), page


def test_the_substitution_row_shows_the_kept_value_it_used(sheet):
    page, console = sheet(VALUES + "keep a = E*A/L\nz = 2*a\nE := 100*GPa\nnumeric(z)\n")
    assert not console, console
    assert r"2\,\left(12500.00\,\frac{\mathrm{kN}}{\mathrm{m}}\right)" in page, page


def test_a_kept_name_whose_values_are_not_all_settled_still_asks_for_them(sheet):
    page, console = sheet("keep a = E*A/L\nE := 200*GPa\nz = 2*a\nnumeric(z)\n")
    assert "numeric evaluation requires values for" in console, console
