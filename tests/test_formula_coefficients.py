r"""A coefficient in a formula is a displayed number like every other one.

Seen in the rendered ACI beam, not reported by a test. `a = As*fy/(0.85*fc*b)` puts
1/(2*0.85) into the expression for `a - a/2`, and SymPy prints a Float at its full binary
precision, so the memoria carried

    0.588235294117647

through the formula and again through the substitution stage. Fifteen digits in the
middle of a page whose every result is shown to two decimals.

The rule is narrow on purpose: **shorten a number longer than the page's precision, and
never reshape one that is not**. A first draft rounded every Float and trimmed trailing
zeros, which read well - `1.2 DL + 1.6 LL` rather than `1.20 DL + 1.60 LL` - until the
suite caught it turning the `1.0` of `0.9*D - 1.0*Lv` into `1`, deleting a load factor an
engineer writes on purpose. What was typed is left exactly as typed, which is the rule
this renderer already follows for units.
"""

import pytest
import sympy as sp

import engcalc_colab.magic as magic
from engcalc_colab.renderer import RenderSettings, _latex


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> str:
        captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def test_a_derived_coefficient_is_not_fifteen_digits_long():
    """The reported case: 1/(2*0.85), which is what `a/2` leaves in the expression."""
    assert _latex(sp.sympify("1/(2*0.85)")) == "0.59"


def test_the_memoria_does_not_carry_the_long_decimal(cell):
    """End to end, the way it was seen: the whole block, formula and substitution."""
    latex = cell(
        "fc := 29.9922*MPa\nfy := 413.6854*MPa\nb := 304.8*mm\n"
        "As := 1935.48*mm**2\nd := 446.05*mm\nphi := 0.9\n"
        "a = As*fy/(0.85*fc*b)\n"
        "phiMn = phi*As*fy*(d - a/2)\n"
        "numeric(phiMn)\n"
    )
    assert "0.588235294117647" not in latex, latex
    assert "0.59" in latex, latex


@pytest.mark.parametrize(
    "written",
    ["1.0", "0.9", "1.2", "1.6", "0.85", "2.55", "0.5", "3.0"],
)
def test_a_number_the_engineer_typed_is_left_exactly_as_typed(written):
    """`1.0` is a load factor. Trimming it to `1` deletes something deliberate.

    Everything here is already no longer than the page's precision, so the rule has
    nothing to shorten and must not touch it - not to pad it to two decimals either.
    """
    assert _latex(sp.Float(written)) == written


def test_a_load_factor_of_one_survives_in_a_combination(cell):
    """The case the suite caught, kept where a reader would meet it."""
    latex = cell(
        "L := 6*m\nqD := 8*kN/m\nqL := 12*kN/m\n"
        "M_D(x) = qD*x*(L-x)/2\nM_Lv(x) = qL*x*(L-x)/2\n"
        "case D = M_D(x)\ncase Lv = M_Lv(x)\n"
        "combo U = 0.9*D - 1.0*Lv\n"
    )
    assert "1.0" in latex, latex
    assert "0.9" in latex, latex


def test_a_small_coefficient_becomes_scientific_rather_than_zero():
    """Rounding to two decimals alone would print 0.00 and lose the number entirely."""
    assert _latex(sp.sympify("0.0001234567890123")) == r"1.23 \times 10^{-4}"


def test_scientific_notation_uses_one_symbol_across_the_page():
    r"""SymPy writes its own exponents with `\cdot`, and the rest of the page uses `\times`.

    Left alone this puts both on one page. It is the smaller half of this fix and it
    only shows for a coefficient small enough that SymPy reaches for an exponent itself.
    """
    rendered = _latex(sp.Float("1e-8"))
    assert r"\times 10^{-8}" in rendered, rendered
    assert r"\cdot 10" not in rendered, rendered


def test_the_page_precision_governs_this_too():
    """One setting for the whole page: `%eng_config precision=4` moves the coefficient."""
    coarse = _latex(sp.sympify("1/(2*0.85)"), settings=RenderSettings(precision=2))
    fine = _latex(sp.sympify("1/(2*0.85)"), settings=RenderSettings(precision=6))
    assert coarse == "0.59", coarse
    assert fine == "0.588235", fine


def test_the_precision_also_decides_what_counts_as_too_long():
    """Not only how the rounded form is written, but which numbers are rounded at all.

    A mutation that hardcoded the threshold at two survived every other contract here,
    because they all round the same number the same way whatever the threshold is.
    `0.1234` at precision 6 is short enough to be left alone; a fixed threshold would
    round it and hand back `0.123400`, which is longer than what was typed.
    """
    assert _latex(sp.Float("0.1234"), settings=RenderSettings(precision=6)) == "0.1234"
    assert _latex(sp.Float("0.1234"), settings=RenderSettings(precision=2)) == "0.12"


def test_integers_are_untouched():
    """`x**2` and `q*L**2/8` must not acquire decimals; only Floats go through this."""
    assert _latex(sp.sympify("x**2/8")) == r"\frac{x^{2}}{8}"
