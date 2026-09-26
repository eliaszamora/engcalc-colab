r"""A letter the sheet made a name is that name; where it could still be the unit, the line stops.

Measured on 0.40.0 (2026-09-26): `a := 2*kg`, `m = 3*a`, `x := 4*m` gave `4.00 m` - the
metre, while `m := 6*kg` then `x := 4*m` gave the mass; and the single degree of freedom
`k := 2000*kN/m`, `m := 500*kg`, run twice, read `k = 4.00 kN/kg` the second time. He uses
`m`, `s` and `N` as names and asked for more than a notice.

Two rules, with `6[m]` (test_a_unit_in_brackets) as the way to write a unit that cannot be
mistaken:

- a name the sheet defined, with `:=` or with `=`, is that name wherever it is written
  after - `x := 4*m` is four times the mass either way;
- where such a letter stands beside another unit - `2000*kN/m`, `5*m/s` - it could be
  either, and the line stops and says to write the unit in brackets: `2000[kN/m]`. A wrong
  number is replaced by a line that asks, and nothing is decided in silence.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


def run(magics, source: str, monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magics.eng("", source)
    return " ".join(item.data for item in captured if isinstance(item, Math)), console.getvalue()


@pytest.fixture
def magics():
    return magic.EngMagics()


def test_a_formula_named_m_is_the_formula(magics, monkeypatch):
    page, console = run(magics, "a := 2*kg\nm = 3*a\nx := 4*m\n", monkeypatch)
    assert not console, console
    assert r"x & = & \displaystyle 24.00\,\mathrm{kg}" in page, page


def test_a_value_named_m_is_the_value(magics, monkeypatch):
    page, _console = run(magics, "m := 500*kg\nx := 4*m\n", monkeypatch)
    assert r"x & = & \displaystyle 2000.00\,\mathrm{kg}" in page, page


@pytest.mark.parametrize(
    "source, written",
    [
        ("m := 500*kg\nv := 5*m/s\n", "5*m/s"),
        ("m := 500*kg\nk := 2000*kN/m\n", "2000*kN/m"),
        ("s := 20*cm\nf := 3/s\nw := 2*rad/s\n", "2*rad/s"),
        ("m := 500*kg\nF = 3*kN*m\n", "3*kN*m"),
    ],
)
def test_a_name_beside_a_unit_stops_the_line(magics, monkeypatch, source, written):
    _page, console = run(magics, source, monkeypatch)
    last = len(source.splitlines())
    assert f"line {last}" in console and "[" in console, console
    assert "brackets" in console, console


def test_a_second_run_stops_instead_of_a_wrong_number(magics, monkeypatch):
    sheet = "k := 2000*kN/m\nm := 500*kg\n"
    run(magics, sheet, monkeypatch)
    page, console = run(magics, sheet, monkeypatch)
    assert "line 1" in console and "2000[kN/m]" in console, console
    assert r"\frac{\mathrm{kN}}{\mathrm{kg}}" not in page, page


def test_a_unit_letter_no_name_took_is_a_unit(magics, monkeypatch):
    page, console = run(magics, "k := 2000*kN/m\nv := 5*m/s\n", monkeypatch)
    assert not console, console
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in page and r"\frac{\mathrm{m}}{\mathrm{s}}" in page, page


def test_brackets_settle_it(magics, monkeypatch):
    page, console = run(magics, "m := 500[kg]\nk := 2000[kN/m]\nv := 5[m/s]\n", monkeypatch)
    assert not console, console
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in page and r"\frac{\mathrm{m}}{\mathrm{s}}" in page, page
