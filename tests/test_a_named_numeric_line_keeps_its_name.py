r"""`d = numeric(...)` and `d = result(...)`: the row is written under its name.

His exercise 2.1 (2026-09-25): `delta_ac = result(F_ac*L_ac/(E*A_ac))` put the formula in
the column a name goes in, so `δ_ac` was nowhere on the page, and showed the substitution
`result` exists to leave out - `result` was recognised by the line starting with
`result(`, which a named line does not. He asked for the fix (*"corrige el numeric"*).
The name is also kept on the sheet, as a `=` line keeps its formula, so a later line
can read it.
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


DATA = "E := 200000*MPa\nA := 8000*mm^2\nF := 277.8*kN\nL := 5*m\n"
SUBSTITUTED = r"\left(277.80\,\mathrm{kN}\right)"


def after(page: str, row: str) -> str:
    return page.split(row, 1)[1]


def test_numeric_under_a_name_is_written_under_it(sheet):
    page, console = sheet(DATA + "d = numeric(F*L/(E*A))\n")
    assert not console, console
    rows = after(page, r"d & = & \displaystyle \frac{F L}{E A}")
    assert SUBSTITUTED in rows and r"0.87\,\mathrm{mm}" in rows, rows


def test_result_under_a_name_leaves_the_substitution_out(sheet):
    page, console = sheet(DATA + "d = result(F*L/(E*A))\n")
    assert not console, console
    rows = after(page, r"d & = & \displaystyle \frac{F L}{E A}")
    assert SUBSTITUTED not in rows and r"0.87\,\mathrm{mm}" in rows, rows


@pytest.mark.parametrize("call", ["numeric", "result"])
def test_the_name_can_be_read_afterwards(sheet, call):
    page, console = sheet(DATA + f"d = {call}(F*L/(E*A))\ny = 2*d\nnumeric(y)\n")
    assert not console, console
    assert r"1.74\,\mathrm{mm}" in after(page, r"y & = &"), page


def test_result_on_its_own_line_is_unchanged(sheet):
    page, console = sheet(DATA + "result(F*L/(E*A))\n")
    assert not console, console
    assert r"\frac{F L}{E A} & = & \displaystyle 0.87\,\mathrm{mm}" in page, page
