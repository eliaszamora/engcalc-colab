r"""A number keeps the figures it was typed with: `0.90*b` is `0.90 b`, not `0.9 b`.

A code writes its factors with their figures - ACI's 0.90, a load factor of 1.20 - and the
memoria is checked against the code. The parser read `0.90` as the float 0.9 and the zero
was gone before anything could print it. Asked for on 2026-09-25 among the points still
open (*"aborda el 1 y 2 y 3 y 4"*).

Only what was typed: a value the algebra produced prints as it always has, and `0.9`
typed as `0.9` stays `0.9`.
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


def definition(page: str, name: str) -> str:
    return page.split(name + r" & = & \displaystyle ", 1)[1].split(r"\\", 1)[0]


def test_a_trailing_zero_stays(sheet):
    page, console = sheet("b := 30*cm\na = 0.90*b\n")
    assert not console, console
    assert definition(page, "a").startswith(r"0.90"), page


def test_it_stays_in_the_substitution_too(sheet):
    page, console = sheet("b := 30*cm\nc := 2*cm\na = 1.20*b + c\nnumeric(a)\n")
    assert not console, console
    block = page.split(r"a & = & ", 1)[1]
    assert block.count("1.20") >= 2, block
    assert r"38.00\,\mathrm{cm}" in block, block


def test_a_number_typed_short_stays_short(sheet):
    page, console = sheet("b := 30*cm\na = 0.9*b\n")
    assert not console, console
    assert definition(page, "a").startswith(r"0.9 "), page


def test_a_matrix_line_keeps_it_as_well(sheet):
    page, console = sheet("K = [2*kN/m, -1*kN/m; -1*kN/m, 1*kN/m]\nF = [0*kN; 10*kN]\nd := 1.50*solve(K, F)\n")
    assert not console, console
    assert "1.50" in page, page


def test_a_table_column_of_zeros_takes_the_unit_of_its_kind(sheet):
    """`table(M(x), x, 0, L, 2)` has stations at the supports only, where a simply
    supported moment is zero, and its header read `M(x) [N·m]` on a kN sheet: a column of
    zeros has no size to choose a unit by. It takes the unit the moment reads in between.
    Asked for with the other open points on 2026-09-25."""
    page, console = sheet("L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\ntable(M(x), x, 0, L, 2)\n")
    assert not console, console
    header = page.split(r"\begin{array}{l|r}", 1)[1].split(r"\hline", 1)[0]
    assert r"\mathrm{kN} \cdot \mathrm{m}" in header, header
