r"""A unit the page writes as `1/s` can be asked for as `1/s`.

The page writes a circular frequency as `374.98 1/s`, an eigenvalue as `1/s²` and a
curvature as `1/m`, and the README says a target unit "may contain products, divisions
and powers". Typing the page's own spelling back answered

    numeric(w, 1/s)    ->  engcalc: line 2: target unit must be a unit expression

and stopped the cell there, while `numeric(w, s**-1)` - the same unit, spelled the way
nobody writes it - worked. Found by the audit of 0.31.14; the check that refused it is as
old as target units themselves (0.2.4).

The target unit is evaluated node by node, and the `1` is a constant like the `2` of
`mm^2`: a number. `1 / s` is then a number over a unit, which Pint answers with a
*quantity* - one second to the minus one, with a magnitude - and `evaluate_unit_expression`
rightly refuses a quantity, because a magnitude in a target unit would be thrown away.

So the rule is the reciprocal, and only the reciprocal: **a `1` over a unit is that
unit's inverse.** Any other number over a unit is still not a unit. Taking the unit off
whatever quantity arrived would have made the same fix in one line, and it would also
have read `numeric(w, 2/s)` as `1/s` without a word - the one outcome worse than the
error it replaces.

A table's declared point unit goes through the same evaluator, so it takes `1/s` too.

Each contract below compares the reciprocal with the `**-1` spelling that already worked,
*and* checks the console and the value on its own. The comparison alone is not enough:
when the line fails, the page still ends on the row above it, and for `w := 374.98/s`
that row reads `374.98 1/s` - exactly the number a contract would look for.
"""

import ast

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.numeric import NumericContext


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


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


def _unit(text: str):
    return NumericContext().evaluate_unit_expression(ast.parse(text, mode="eval"))


FREQUENCY = "w := 374.98/s\n"
# The mass is `m_s`, not `m`: each contract runs two cells through one engine, and a
# stored `m` outranks the metre on the second run, so `2000*kN/m` would read per kilogram.
MODE = "k := 2000*kN/m\nm_s := 500*kg\nw2 = k/m_s\n"
CURVATURE = "M := 30*kN*m\nE := 200*GPa\nI := 1.5e8*mm^4\nkappa = M/(E*I)\n"


# --- the unit itself ---------------------------------------------------------------

def test_one_over_a_second_is_the_inverse_second():
    unit = _unit("1/s")
    assert not hasattr(unit, "magnitude"), unit
    assert unit == _unit("s**-1")


def test_one_over_a_compound_unit_is_its_inverse():
    assert _unit("1/(kg*m)") == _unit("kg**-1*m**-1")


def test_a_radian_per_second_keeps_its_radian():
    """Pint holds that `rad == 1`, so a rule asking only "is it 1?" reads `rad/s` as `1/s`.

    A circular frequency is conventionally asked for in radians per second; the radian is
    the one thing on that row that says it is not a frequency in hertz.
    """
    assert _unit("rad/s") == _unit("rad*s**-1")
    assert _unit("rad/s") != _unit("1/s")


def test_a_number_other_than_one_over_a_unit_is_still_refused():
    """`2/s` is not a unit. Reading it as `1/s` would drop the 2 in silence."""
    with pytest.raises(EngEvaluationError, match="target unit must be a unit expression"):
        _unit("2/s")


# --- on the page -------------------------------------------------------------------

def test_a_frequency_can_be_asked_for_in_one_over_seconds(cell, capsys):
    page = cell(FREQUENCY + "numeric(w, 1/s)\n")
    assert capsys.readouterr().out == ""
    assert _final(page) == r"\displaystyle 374.98\,\frac{1}{\mathrm{s}}", _final(page)
    assert page == cell(FREQUENCY + "numeric(w, s**-1)\n")


def test_an_eigenvalue_can_be_asked_for_in_one_over_seconds_squared(cell, capsys):
    page = cell(MODE + "numeric(w2, 1/s**2)\n")
    assert capsys.readouterr().out == ""
    assert _final(page) == r"\displaystyle 4000.00\,\frac{1}{\mathrm{s}^{2}}", _final(page)
    assert page == cell(MODE + "numeric(w2, s**-2)\n")


def test_a_curvature_can_be_asked_for_in_one_over_metres(cell, capsys):
    page = cell(CURVATURE + "numeric(kappa, 1/m)\n")
    assert capsys.readouterr().out == ""
    assert _final(page) == r"\displaystyle 0.001\,\frac{1}{\mathrm{m}}", _final(page)
    assert page == cell(CURVATURE + "numeric(kappa, m**-1)\n")


def test_result_takes_the_reciprocal_too(cell, capsys):
    page = cell(FREQUENCY + "result(w, 1/s)\n")
    assert capsys.readouterr().out == ""
    assert page == cell(FREQUENCY + "result(w, s**-1)\n")


def test_a_reciprocal_inside_a_product_is_a_unit(cell, capsys):
    """`kN*(1/m)` is `kN/m`: the rule holds wherever the `1` sits, not only on top."""
    page = cell("k := 2000*kN/m\nnumeric(k, kN*(1/m))\n")
    assert capsys.readouterr().out == ""
    assert page == cell("k := 2000*kN/m\nnumeric(k, kN/m)\n")


def test_two_over_a_second_still_stops_the_cell(cell, capsys):
    cell(FREQUENCY + "numeric(w, 2/s)\n")
    assert "target unit must be a unit expression" in capsys.readouterr().out
