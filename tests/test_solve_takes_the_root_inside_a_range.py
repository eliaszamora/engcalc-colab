r"""`solve(eq(...), c, 0*cm, d)`: the one root inside a range, with `=` and with `:=`.

    c := solve(eq(b*c^2/2, n*A_s*(d - c)), c, 0*cm, d)

The neutral axis of a cracked section is a quadratic with two roots, one negative; the
engineer wants the one between 0 and d. `solve` without a range answers both and says to
use `roots`; `:=` refused it outright ("unsupported numeric function"), and so did a
transcendental equation, which has no closed form at all. He asked for it on 2026-09-25
(*"solve numérico con intervalo"*, then *"sigue con el solve"*). The root is found the way
`roots(...)` finds it - exactly where it can be, numerically where it cannot - and a
range holding no root or more than one is refused with what it holds.
"""

import contextlib
import io
import math

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


BEAM = "b := 30*cm\nn := 9\nA_s := 5.55*cm^2\nd := 44*cm\n"
EQUATION = "eq(b*c^2/2, n*A_s*(d - c))"


def rows(page: str, name: str) -> str:
    return page.split(name + r" & = & ", 1)[1].split(r"\end{array}", 1)[0]


def test_a_value_defined_by_the_root_inside_the_range(sheet):
    page, console = sheet(BEAM + f"c := solve({EQUATION}, c, 0*cm, d)\ny := 2*c\n")
    assert not console, console
    assert r"c & = & \displaystyle 10.55\,\mathrm{cm}" in page, page
    assert r"y & = & \displaystyle 21.11\,\mathrm{cm}" in page, page


def test_the_equation_is_written_above_the_value(sheet):
    page, _console = sheet(BEAM + f"c := solve({EQUATION}, c, 0*cm, d)\n")
    equation = page.split(r"c & = & \displaystyle 10.55", 1)[0].rsplit(r"d & = &", 1)[1]
    assert r"\frac{b c^{2}}{2}" in equation and "=" in equation, equation


def test_the_same_with_equals_keeps_its_formula_and_numeric_gives_the_number(sheet):
    page, console = sheet(BEAM + f"c_n = solve({EQUATION}, c, 0*cm, d)\nnumeric(c_n)\n")
    assert not console, console
    assert r"10.55\,\mathrm{cm}" in page, page


def test_an_equation_with_no_closed_form(sheet):
    page, console = sheet(f"r := solve(eq(x, cos(x)), x, 0, 1)\n")
    assert not console, console
    root = 0.7390851332151607
    assert r"r & = & \displaystyle 0.74" in page, page
    assert math.isclose(root, math.cos(root))


def test_a_cubic(sheet):
    page, console = sheet(BEAM + "c := solve(eq(b*c^3/3 + n*A_s*(d - c)^2, 1e5*cm^4), c, 0*cm, d)\n")
    assert not console, console
    # By bisection, independently: b c³/3 + n As (d - c)² - 1e5 changes sign once in (0, 44):
    # 96703 - 1e5 < 0 at c = 0, and it only falls to its minimum at 10.55 before rising.
    f = lambda c: 30 * c**3 / 3 + 9 * 5.55 * (44 - c) ** 2 - 1e5
    lo, hi = 0.0, 44.0
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(lo) * f(mid) > 0 else (lo, mid)
    assert rf"c & = & \displaystyle {lo:.2f}\,\mathrm{{cm}}" in page, (lo, page)


@pytest.mark.parametrize(
    "line, words",
    [
        ("c := solve(eq(b*c^2/2, n*A_s*(d - c)), c, 20*cm, d)\n", ("line 5", "no root", "20.00")),
        ("c := solve(eq((c - 5*cm)*(c - 10*cm), 0*cm^2), c, 0*cm, d)\n", ("line 5", "5.00", "10.00", "narrow")),
        ("c := solve(eq(b*c^2/2, n*A_s*(d - c)), c, 0*cm)\n", ("line 5", "lower", "upper")),
    ],
)
def test_a_range_that_does_not_hold_one_root_says_what_it_holds(sheet, line, words):
    _page, console = sheet(BEAM + line)
    for word in words:
        assert word in console, (word, console)


def test_a_change_of_sign_across_a_pole_is_not_a_root(sheet):
    # 1/(c - 20 cm) goes from minus to plus at 20 cm without ever being zero.
    _page, console = sheet(BEAM + "c := solve(eq(1/(c - 20*cm), 0/cm), c, 0*cm, d)\n")
    assert "no root" in console, console


def test_a_bare_zero_for_the_lower_bound_takes_the_upper_bound_s_unit(sheet):
    # The cubic has no closed form worth finding, so this is the path in numbers.
    page, console = sheet(BEAM + "c := solve(eq(b*c^3/3 + n*A_s*(d - c)^2, 1e5*cm^4), c, 0, d)\n")
    assert not console, console
    assert r"c & = & \displaystyle" in page and r"\mathrm{cm}" in page.split(r"c & = &", 1)[1], page
