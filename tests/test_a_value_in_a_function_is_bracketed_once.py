r"""A value put into a function's parentheses is not bracketed a second time.

Seen in his exercise 2.1 on 2026-09-25: `u = (delta_ab*sin(phi) - ...)/sin(theta + phi)`
substituted as `sin((0.93 rad))`. The substitution row brackets every value it puts in
place of a name, so a value beside another factor stays one thing - `2 (0.50 rad)` - but
a function that writes its own parentheses around its argument already does that, and the
second pair says nothing: `sin(0.93 rad)`, `max(45.00 kN, 30.00 kN)`, `f(3.00 m)`.

Only where the function's parentheses stand directly around the value. A value inside a
product, a sum or a power keeps its brackets, and so does one under a radical, between
bars or up in an exponent, which have no parentheses of their own.
"""

import contextlib
import io

import pint
import pytest
import sympy as sp
from IPython.display import Math

import engcalc_colab.magic as magic
from engcalc_colab.renderer import RenderSettings, _NumericSubstitutionLatexPrinter

UNITS = pint.get_application_registry()
a, b = sp.symbols("a b")
VALUES = {"a": UNITS.Quantity(0.5, "rad"), "b": UNITS.Quantity(0.9, "rad")}
A = r"0.50\,\mathrm{rad}"
B = r"0.90\,\mathrm{rad}"


def printed(expr) -> str:
    return _NumericSubstitutionLatexPrinter(VALUES, RenderSettings()).doprint(expr)


@pytest.mark.parametrize(
    "expr, shown",
    [
        (sp.sin(a), rf"\sin{{\left({A} \right)}}"),
        (sp.log(a), rf"\log{{\left({A} \right)}}"),
        (sp.atan(a), rf"\operatorname{{atan}}{{\left({A} \right)}}"),
        (sp.sin(a) ** 2, rf"\sin^{{2}}{{\left({A} \right)}}"),
        (sp.Function("f")(a), rf"f\left({A}\right)"),
        (sp.Max(a, b), rf"\max\left({A}, {B}\right)"),
    ],
)
def test_a_value_alone_in_a_function_takes_the_function_s_parentheses(expr, shown):
    assert printed(expr) == shown


@pytest.mark.parametrize(
    "expr, kept",
    [
        (sp.sin(2 * a), rf"2\,\left({A}\right)"),
        (sp.cos(a + b), rf"\left({A}\right) + \left({B}\right)"),
        (sp.sqrt(a), rf"\sqrt{{\left({A}\right)}}"),
        (sp.Abs(a), rf"\left|{{\left({A}\right)}}\right|"),
        (sp.exp(a), rf"e^{{\left({A}\right)}}"),
        (a**2, rf"\left({A}\right)^{{2}}"),
    ],
)
def test_a_value_with_no_parentheses_of_the_function_around_it_keeps_its_own(expr, kept):
    assert kept in printed(expr), printed(expr)


def test_his_exercise_reads_sin_of_the_angle(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng(
            "", "phi := atan(4/3)\nd := 2*mm\nkeep u = d*sin(phi)\nnumeric(u)\n"
        )
    assert not console.getvalue(), console.getvalue()
    page = " ".join(item.data for item in captured if isinstance(item, Math))
    # The angle reads in degrees (test_an_angle_reads_in_degrees).
    assert r"\sin{\left(53.13^{\circ} \right)}" in page, page
    assert r"\left(\left(" not in page, page
