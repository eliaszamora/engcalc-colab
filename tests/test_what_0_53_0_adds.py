r"""What 0.53.0 corrects, from the inventory of open findings."""

import contextlib
import io
import time

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str) -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), out.getvalue()

    return run


# N6h: `extrema` of a sine or a cosine in a denominator did not come back in 100 s.


def test_extrema_with_a_sine_in_a_denominator_answers(sheet):
    started = time.perf_counter()
    page, printed = sheet("extrema(cos(x) + 1/sin(x), x, 0.5, 2.5)\n")
    assert time.perf_counter() - started < 20
    assert not printed, printed
    assert r"\text{value} \approx 0.65" in page and "global min" in page, page


def test_extrema_away_from_a_pole_answers(sheet):
    page, printed = sheet("extrema(1/sin(x^2), x, 1, 1.7)\n")
    assert not printed, printed
    # √(π/2), exact: the slope's numerator, `-2x cos x²`, is solved as it stands.
    assert r"\dfrac{\sqrt{2} \sqrt{\pi}}{2}" in page and "global min" in page and r"4.02" in page, page


@pytest.mark.parametrize(
    ("source", "where"),
    [("extrema(1/sin(x^2), x, 1, 2)\n", "x = 1.772"), ("extrema(sin(x) + 1/cos(x/1000), x, 0, 3000)\n", "x = 1571")],
)
def test_extrema_across_a_pole_says_where(sheet, source, where):
    started = time.perf_counter()
    page, printed = sheet(source)
    assert time.perf_counter() - started < 40
    assert "goes to infinity inside the interval" in printed and where in printed, printed


# B6: `roots` of a cubic in four names took 45 s to refuse in the analysis's own words.


@pytest.mark.parametrize(
    ("source", "names"),
    [
        ("roots(a*x^3 + b*x^2 + c*x - e, x, 0, 10)\n", "give a, b, c, e a value"),
        ("extrema(P/sin(t), t, 0.1, 3)\n", "give P a value"),
    ],
)
def test_a_name_without_a_value_is_said_at_once(sheet, source, names):
    started = time.perf_counter()
    page, printed = sheet(source)
    assert time.perf_counter() - started < 5
    assert names in printed, printed


def test_a_kept_name_with_a_value_still_finds_its_root(sheet):
    page, printed = sheet(
        "E := 200[GPa]\nA := 1000[mm^2]\nL := 2[m]\nkeep k = E*A/L\nroots(k*x - 1[kN], x, 0[m], 1[m])\n"
    )
    assert not printed, printed
    assert r"\text{root}" in page, page


# C5i: a hyperbolic function of an angle was refused; sin and cos take degrees.


@pytest.mark.parametrize(
    ("source", "shown"),
    [("x := cosh(30[deg])\n", r"x & = & \displaystyle 1.14"), ("y := sinh(45[deg])\n", r"y & = & \displaystyle 0.87")],
)
def test_a_hyperbolic_function_of_an_angle(sheet, source, shown):
    page, printed = sheet(source)
    assert not printed, printed
    assert shown in page, page


def test_a_hyperbolic_function_of_a_length_is_still_refused(sheet):
    page, printed = sheet("w := cosh(2[m])\n")
    assert "cosh requires a dimensionless argument" in printed, printed


# A4: a placeholder holding an operation between two operands.


@pytest.mark.parametrize(
    ("source", "shown"),
    [
        ("% op = '+'\n% u = 'kN'\ny := 2[kN] {op} 3[{u}]\n", r"y & = & \displaystyle 5.00\,\mathrm{kN}"),
        ("% for s in ['+', '-']:\nz := 5 {s} 2\n% end\n", r"z & = & \displaystyle 3.00"),
        ("% q = ' + 3'\nw := (2*4){q}\n", r"w & = & \displaystyle 11.00"),
    ],
)
def test_a_placeholder_holding_an_operation(sheet, source, shown):
    page, printed = sheet(source)
    assert not printed, printed
    assert shown in page, page
