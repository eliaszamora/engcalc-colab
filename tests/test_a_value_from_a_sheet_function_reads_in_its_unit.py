r"""`k_1 := k(4*m)` reads `16000.00 kN·m`, not `1.60 × 10¹⁰ GPa·mm⁴/m`.

A `:=` value keeps the unit it was written in - `q := 2.8*tonf/m` stays in tonf/m - and
the test for "written in" was that the line wrote any unit at all. `k_1 := k(4*m)` wrote a
metre, as the argument, and its value came out in the gigapascals and millimetres of `E`
and `I` inside `k`: a unit nobody wrote, kept as if chosen. A value keeps its unit only
when every part of that unit was written on the line. Found on 2026-09-25 while looking at
how `for` would be written; he asked for it to be fixed.
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


def row(page: str, name: str) -> str:
    return page.split(name + r" & = & \displaystyle ", 1)[1].split(r"\\", 1)[0]


def test_a_value_from_a_function_reads_in_the_unit_of_its_kind(sheet):
    page, console = sheet("E := 200*GPa\nI := 8e7*mm^4\nk(L) = 4*E*I/L\nk_1 := k(4*m)\n")
    assert not console, console
    value = row(page, "k_{1}")
    assert r"16000.00\,\mathrm{kN} \cdot \mathrm{m}" in value, value
    assert "GPa" not in value, value


@pytest.mark.parametrize(
    "line, shown",
    [
        ("q := 2.8*tonf/m\n", r"2.80\,\frac{\mathrm{tonf}}{\mathrm{m}}"),
        ("A_c := 30*cm*30*cm\n", r"900.00\,\mathrm{cm}^{2}"),
        ("b := 500*mm\n", r"500.00\,\mathrm{mm}"),
    ],
)
def test_a_value_written_in_its_unit_keeps_it(sheet, line, shown):
    page, console = sheet(line)
    assert not console, console
    assert shown in page, page


def test_it_is_substituted_in_that_unit_too(sheet):
    page, console = sheet("E := 200*GPa\nI := 8e7*mm^4\nk(L) = 4*E*I/L\nk_1 := k(4*m)\nM = 2*k_1\nnumeric(M)\n")
    assert not console, console
    assert "GPa" not in page.split(r"M & = &", 1)[1], page
