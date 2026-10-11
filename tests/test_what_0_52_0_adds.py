r"""What 0.52.0 adds and corrects, from the inventory of open findings."""

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


def test_numeric_under_a_value_does_not_say_it_twice(sheet):
    page, printed = sheet("f(I) = 2*I\ny = f(1e8[mm^4])\nnumeric(y)\n")
    assert not printed, printed
    assert page.count(r"2.00 \times 10^{8}\,\mathrm{mm}^{4}") == 1, page


def test_numeric_under_a_formula_still_works_it_out(sheet):
    page, printed = sheet("a := 2[m]\ny = 3*a\nnumeric(y)\n")
    assert not printed, printed
    assert r"3\,\left(2.00\,\mathrm{m}\right)" in page and r"6.00\,\mathrm{m}" in page, page


# C10c: values set in a `% if` inside a loop were printed after its table, one by one.


def test_a_value_under_an_if_is_a_column_of_the_loop_table(sheet):
    page, printed = sheet(
        "% for i in range(1, 4):\na_{i} := {i}*1[m]\nc_{i} := 2*a_{i}\n% if {i} > 1:\nb_{i} := 3*a_{i}\n% end\n% end\n"
    )
    assert not printed, printed
    assert r"b_{i}\,[\mathrm{m}]" in page and r"\text{---}" in page, page
    assert r"\text{si}\ i > 1" in page and "Como" not in page and r"b_{2} & =" not in page, page


def test_one_value_and_one_under_an_if_make_a_table(sheet):
    page, printed = sheet("% for i in range(1, 3):\na_{i} := {i}*1[m]\n% if a_{i} > 1.5[m]:\nb_{i} := 2*a_{i}\n% end\n% end\n")
    assert not printed, printed
    assert r"\text{si}\ a_{i} > 1.5\,\mathrm{m}" in page and r"1 & 1.00 & \text{---}" in page, page


def test_an_if_with_an_else_keeps_its_rows(sheet):
    page, printed = sheet(
        "% for i in range(1, 3):\na_{i} := {i}*1[m]\nc_{i} := 2*a_{i}\n% if {i} > 1:\nb_{i} := 3*a_{i}\n% else:\nb_{i} := a_{i}\n% end\n% end\n"
    )
    assert not printed, printed
    assert "Como" in page, page


# C6a: an increment of an angle read as one italic word.


@pytest.mark.parametrize(
    ("source", "shown"),
    [("dtheta := 2\n", r"d\theta & ="), ("deltaphi := 3\n", r"\delta\phi & ="), ("dtheta_A := 4\n", r"d\theta_{A} & =")],
)
def test_an_increment_of_an_angle(sheet, source, shown):
    page, printed = sheet(source)
    assert not printed, printed
    assert shown in page and r"\mathit{d" not in page, page


@pytest.mark.parametrize(("source", "shown"), [("dx := 1[m]\n", r"\mathit{dx}"), ("dpi := 6\n", r"\mathit{dpi}")])
def test_other_names_beginning_with_d_stay_words(sheet, source, shown):
    page, printed = sheet(source)
    assert shown in page, page


# C7c, C8k: a function the sheet has not defined, inside an integral or a differential
# equation.


def test_an_undefined_width_inside_an_integral(sheet):
    page, printed = sheet("y = integrate(b(y)*y, y, 0, h)\n")
    assert not printed, printed
    assert r"b\left(y\right)" in page and r"\int" in page, page


def test_a_differential_equation(sheet):
    page, printed = sheet("v = dsolve(eq(diff(v(x), x, 2), -w*x/(E*I)), v(x))\n")
    assert not printed, printed
    assert r"C_{1} + x C_{2} - \frac{w x^{3}}{6 E I}" in page, page


def test_an_unknown_function_elsewhere_is_still_a_typo(sheet):
    page, printed = sheet("q = sni(x)\n")
    assert "unsupported function 'sni'" in printed, printed


# The audit of 0.52.0.


@pytest.mark.parametrize("source", ["q = integrate(b(y)**2, y)\n", "q = diff(v(x)**2, x)\n"])
def test_a_power_of_an_undefined_function_is_written(sheet, source):
    page, printed = sheet(source)
    assert not printed, printed
    assert r"\right)^{2}" in page, page


@pytest.mark.parametrize(
    "source",
    ["q = integrate(sni(x), x)\n", "b := 0.3[m]\nq = integrate(b(y)*y, y, 0, 1)\n", "q = integrate(x*y, x, 0, f(2))\n"],
)
def test_a_slip_inside_an_integral_is_still_said(sheet, source):
    page, printed = sheet(source)
    assert "unsupported function" in printed, printed


def test_the_constants_of_dsolve_take_the_boundary_conditions(sheet):
    page, printed = sheet(
        "v = dsolve(eq(diff(v(x), x, 2), -w*x/(E*I)), v(x))\n"
        "solve(eq(subs(v, x, 0), 0), eq(subs(v, x, L), 0), C_1, C_2)\nv_s = v\n"
    )
    assert not printed, printed
    assert r"C_{2} & = & \displaystyle \frac{w L^{2}}{6 E I}" in page, page
    assert r"v_{s} & = & \displaystyle \frac{w x L^{2}}{6 E I} - \frac{w x^{3}}{6 E I}" in page, page


def test_a_default_an_if_changes_keeps_its_rows(sheet):
    page, printed = sheet(
        "% for i in range(1, 4):\neps_{i} := 0.002*{i}\nphi_{i} := 0.90\n% if eps_{i} < 0.005:\n"
        "phi_{i} := 0.65 + (eps_{i} - 0.002)*250/3\n% end\n% end\n"
    )
    assert not printed, printed
    assert "Como" in page and r"\text{---}" not in page and r"\phi_{1} & = & \displaystyle 0.65" in page, page


def test_an_if_that_changes_its_loop_s_only_value_keeps_its_reason(sheet):
    page, printed = sheet("% for i in range(1, 4):\nb_{i} := {i}*1[m]\n% if {i} > 1:\nb_{i} := 3*b_{i}\n% end\n% end\n")
    assert not printed, printed
    assert page.count("Como") == 2, page


@pytest.mark.parametrize(
    ("condition", "rule"),
    [
        ("{i} > 1 and a_{i} < 2.5[m]", r"i > 1\ \text{y}\ a_{i} < 2.5\,\mathrm{m}"),
        ("{i} == 2 or {i} == 3", r"i = 2\ \text{o}\ i = 3"),
    ],
)
def test_a_condition_of_two_comparisons_reads_in_words(sheet, condition, rule):
    page, printed = sheet(
        f"% for i in range(1, 4):\na_{{i}} := {{i}}*1[m]\nc_{{i}} := 2*a_{{i}}\n% if {condition}:\nb_{{i}} := 3*a_{{i}}\n% end\n% end\n"
    )
    assert not printed, printed
    assert rule in page, page
