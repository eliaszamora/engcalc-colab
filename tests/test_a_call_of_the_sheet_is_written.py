r"""`M_u = U1(L/2)` is written as a call before what it expands to.

    M_u = U1(L/2)
        = 0.15 qD L^2 + 0.2 qL L^2
        = 0.15 (18.00 kN/m) (6.00 m)^2 + 0.2 (12.00 kN/m) (6.00 m)^2
        = 183.60 kN·m

The row read `M_u = 0.15 qD L^2 + 0.2 qL L^2`: which combination, and where along the
beam, were gone from the page, and a reviewer had to work backwards from the coefficients.
Found on `tools/viga.eng` and on the frame's design; dealt with among the pending points
he asked for (*"abarques todos esos puntos pendientes"*).

Only a named line whose whole right side is one call to a function or combination of the
sheet. The call stands on a row of its own, and what it expands to opens the rows of the
evaluation below it rather than being said twice.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic

BEAM = (
    "L := 6*m\nqD := 18*kN/m\nqL := 12*kN/m\n"
    "M_D(x) = qD*x*(L - x)/2\nM_L(x) = qL*x*(L - x)/2\n"
    "case D = M_D(x)\ncase Lv = M_L(x)\ncombo U1 = 1.2*D + 1.6*Lv\n"
)


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


def block(page: str, name: str) -> list[str]:
    start = page.index(name + " & = & ")
    rows = page[start:].split(r"\end{array}", 1)[0]
    return [row.strip() for row in rows.split(r"\\") if "& = &" in row]


def test_the_call_opens_the_rows(sheet):
    page, console = sheet(BEAM + "keep M_u = U1(L/2)\nnumeric(M_u)\n")
    assert not console, console
    rows = block(page, "M_{u}")
    assert rows[0].endswith(r"U_{1}\left(\frac{L}{2}\right)"), rows
    assert "0.15" in rows[1] and "qD" in rows[1], rows
    assert rows[-1].endswith(r"183.60\,\mathrm{kN} \cdot \mathrm{m}"), rows
    # Said once: the formula the call expands to is not repeated under the name.
    assert sum("0.15" in row and "qD" in row and "18.00" not in row for row in rows) == 1, rows


def test_a_function_of_the_sheet_is_written_as_called(sheet):
    page, console = sheet("q := 10*kN/m\nL := 5*m\nM(x) = q*x*(L - x)/2\nM_1 = M(2*m)\nnumeric(M_1)\n")
    assert not console, console
    rows = block(page, "M_{1}")
    assert r"M\left(2\,\mathrm{m}\right)" in rows[0], rows
    assert rows[-1].endswith(r"30.00\,\mathrm{kN} \cdot \mathrm{m}"), rows


def test_a_call_inside_a_larger_formula_is_not_split_out(sheet):
    page, console = sheet(BEAM + "y = 2*U1(L/2)\n")
    assert not console, console
    assert r"U_{1}\left(\frac{L}{2}" not in page, page


def test_a_function_definition_is_untouched(sheet):
    page, console = sheet(BEAM)
    assert not console, console
    assert r"U_{1}\left(x\right) & = & \displaystyle 1.2" in page, page
