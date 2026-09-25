r"""A name defined again reads its last definition, whichever way each was written.

    Vu = max(a, b)
    Vu := 5000*kgf
    W = 2*Vu

The page said `Vu = 5000.00 kgf` and then went on computing with `max(a, b)`: a `:=` line
stored the number beside the formula and left the formula in front of it. A matrix already
dropped its formula on `:=` (`K = [...]` then `K := solve(K, F)`); a scalar did not. Found on
2026-09-25 rendering his shear design with `% if`, where a branch redefining a name is the
whole point, and present in 0.38.0 without it.
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


def after(page: str, row: str) -> str:
    return page.split(row, 1)[1]


@pytest.mark.parametrize("declaration", ["", "keep "])
def test_a_formula_redefined_as_a_number_reads_the_number(sheet, declaration):
    page, console = sheet(
        f"a := 3*kN\nb := 4*kN\n{declaration}Vu = max(a, b)\nVu := 5000*kgf\nW = 2*Vu\nnumeric(W)\n"
    )
    assert not console, console
    rest = after(page, r"W & = & ")
    assert r"\max" not in rest, rest
    assert r"10000.00\,\mathrm{kgf}" in rest or r"10.00\,\mathrm{tonf}" in rest, rest


def test_a_number_redefined_as_a_formula_reads_the_formula(sheet):
    page, console = sheet("a := 3*kN\nb := 4*kN\nVu := 5000*kgf\nVu = max(a, b)\nW = 2*Vu\nnumeric(W)\n")
    assert not console, console
    rest = after(page, r"W & = & ")
    assert r"8.00\,\mathrm{kN}" in rest, rest


def test_numeric_of_the_name_itself_reads_the_number(sheet):
    page, console = sheet("a := 3*kN\nb := 4*kN\nVu = max(a, b)\nVu := 5000*kgf\nnumeric(Vu)\n")
    assert not console, console
    rest = after(page, r"\mathrm{Vu} & = & \displaystyle 5000.00")
    assert r"\max" not in rest and "4.00" not in rest, rest
