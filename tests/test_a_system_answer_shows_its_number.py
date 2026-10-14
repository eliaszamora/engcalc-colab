r"""C6h: `solve` of a system answered in names, never in numbers, even with every name valued.

`a := 2.5; b := 3.7; solve(eq(a*x + b*y, 1), eq(b*x - a*y, 2), x, y)` gave
`x = (a + 2b)/(a^2 + b^2)` and no `0.50`; his Example 2.1 needed a `result(a_x, mm)` per
unknown. Each answer of a system is now followed by its number on a row of its own when
the sheet's values give one. The answer itself - what `numeric`, `result` and later lines
read - is not touched, and a single equation's `solve` is not changed.
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
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), out.getvalue()

    return run


EXAMPLE_2_1 = """E := 200000*MPa
A_ba := 6000*mm^2
A_ac := 8000*mm^2
F_ba := 400.6*kN
F_ac := 277.8*kN
L_ba := sqrt(6^2 + 4^2)*m
L_ac := 5*m
theta := atan(4/6)
phi := atan(4/3)
delta_ba := F_ba*L_ba/(E*A_ba)
delta_ac := F_ac*L_ac/(E*A_ac)
solve(
    eq(delta_ba, a_x*cos(theta) + a_y*sin(theta)),
    eq(delta_ac, a_x*cos(phi) - a_y*sin(phi)),
    a_x, a_y
)
"""


def test_example_2_1_shows_each_displacement(sheet):
    page, printed = sheet(EXAMPLE_2_1)
    assert not printed, printed
    # By hand: a_x = 2.411 mm, a_y = 0.723 mm.
    assert r"& = & \displaystyle 2.41\,\mathrm{mm}" in page, page
    assert r"& = & \displaystyle 0.72\,\mathrm{mm}" in page, page
    # The formulas stay, each before its number (δ_ba is also 2.41 mm, on its own row above).
    a_x = page.index(r"a_{x} & = & \displaystyle \frac{\delta_{ac}")
    a_y = page.index(r"a_{y} & = & \displaystyle \frac{\delta_{ba}")
    assert a_x < page.rindex(r"2.41\,\mathrm{mm}") < a_y < page.rindex(r"0.72\,\mathrm{mm}"), page
    assert page.count(r"2.41\,\mathrm{mm}") == 2 and page.count(r"0.72\,\mathrm{mm}") == 1, page


def test_a_system_with_valued_coefficients(sheet):
    page, printed = sheet("a := 2.5\nb := 3.7\nsolve(eq(a*x + b*y, 1), eq(b*x - a*y, 2), x, y)\n")
    assert not printed, printed
    assert r"x & = & \displaystyle \frac{a + 2 b}{a^{2} + b^{2}}" in page, page
    assert r"& = & \displaystyle 0.50" in page and r"& = & \displaystyle -0.0652" in page, page


def test_a_system_of_numbers_is_written_once(sheet):
    page, printed = sheet("solve(eq(2*x + y, 5), eq(x - y, 1), x, y)\n")
    assert not printed, printed
    assert r"x & = & \displaystyle 2" in page and r"y & = & \displaystyle 1" in page, page
    assert r" & = & \displaystyle 2.00" not in page and r" & = & \displaystyle 1.00" not in page, page


def test_a_symbolic_system_stays_symbolic(sheet):
    page, printed = sheet("solve(eq(a*x + b*y, 1), eq(b*x - a*y, 2), x, y)\n")
    assert not printed, printed
    assert r"x & = & \displaystyle \frac{a + 2 b}{a^{2} + b^{2}} \end" not in page  # not last
    assert page.count(r" & = & \displaystyle") == 2, page


def test_a_system_with_a_name_without_value_stays_a_formula(sheet):
    page, printed = sheet("a := 2.5\nsolve(eq(a*x + b*y, 1), eq(x - y, 0), x, y)\n")
    assert not printed, printed
    assert r"x & = & \displaystyle \frac{1}{a + b}" in page, page
    assert page.count(r" & = & \displaystyle") == 3, page  # a, x, y: no number rows


def test_only_the_answers_with_values_get_a_number(sheet):
    page, printed = sheet("a := 2\nsolve(eq(x, a), eq(y, c*x), x, y)\n")
    assert not printed, printed
    # `a := 2` writes 2.00 once; x's number writes it again, under `x = a`.
    assert r"x & = & \displaystyle a" in page and page.count(r"& = & \displaystyle 2.00") == 2, page
    assert r"y & = & \displaystyle a c \end{array}" in page, page


def test_a_system_in_units(sheet):
    page, printed = sheet(
        "P := 10[kN]\nk_1 := 2[kN/mm]\nk_2 := 3[kN/mm]\n"
        "solve(eq(k_1*u + k_2*(u - v), P), eq(k_2*(v - u), 0[kN]), u, v)\n"
    )
    assert not printed, printed
    assert page.count(r"& = & \displaystyle 5.00\,\mathrm{mm}") == 2, page


def test_incompatible_units_give_no_number_and_no_error(sheet):
    page, printed = sheet("solve(eq(x + y, 1[m]), eq(x - y, 1[s]), x, y)\n")
    assert not printed, printed
    assert page.count(r" & = & \displaystyle") == 2, page


def test_one_equation_one_unknown_is_unchanged(sheet):
    page, printed = sheet("k := 2[kN/mm]\nsolve(eq(k*u, 10[kN]), u)\n")
    assert not printed, printed
    assert r"u & = & \displaystyle \frac{10\,\mathrm{kN}}{k} \end{array}" in page, page


def test_several_answers_of_one_unknown_are_unchanged(sheet):
    page, printed = sheet("solve(eq(x^2, 4), x)\n")
    assert not printed, printed
    assert r"x & = & \displaystyle -2\;\;\left(-2.00\right)" in page, page
    assert r"x & = & \displaystyle 2\;\;\left(2.00\right)" in page, page


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("solve(eq(x + y, 1), eq(x + y, 2), x, y)\n", "solve found no solution for x, y"),
        ("solve(eq(x^2 + y^2, -1), eq(x - y, 0), x, y)\n", "solve found no solution for x, y"),
        ("solve(eq(x^2 + y^2, 2), eq(x - y, 0), x, y)\n", "solve returned 2 solutions for x, y"),
    ],
)
def test_systems_without_one_answer_say_so_as_before(sheet, source, message):
    page, printed = sheet(source)
    assert message in printed, printed


def test_numeric_and_result_read_the_answers_as_before(sheet):
    page, printed = sheet(
        "P := 10[kN]\nk_1 := 2[kN/mm]\nk_2 := 3[kN/mm]\n"
        "solve(eq(k_1*u + k_2*(u - v), P), eq(k_2*(v - u), 0[kN]), u, v)\n"
        "numeric(u)\nresult(v, mm)\nw = 2*u\n"
    )
    assert not printed, printed
    assert r"\frac{\left(10.00\,\mathrm{kN}\right)}{\left(2.00\,\frac{\mathrm{kN}}{\mathrm{mm}}\right)}" in page
    assert r"w & = & \displaystyle \frac{2 P}{k_{1}}" in page, page
