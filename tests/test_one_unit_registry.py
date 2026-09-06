r"""One Pint registry for the process, which is what Pint asks for.

Every `NumericContext` built its own `UnitRegistry`. Pint re-parses its unit definition
file on each one - about 155 ms - and the suite builds an engine 724 times across 120
files, so more than half of a six-minute run was spent reading the same file again.
Measured on the whole suite: **453 s with a registry per engine, 179 s with one shared**,
1624 passing either way.

Speed is the smaller half. Pint's own guidance is one registry per application, because
quantities built by two registries cannot be combined at all:

    ValueError: Cannot operate with Quantity and Quantity of different registries

A notebook holds one context, so nothing reached that today. It is a hazard removed
rather than a bug fixed, and the contracts below are what sharing has to keep true: the
definitions a context adds must be added once, and a reset must clear the sheet's values
without taking the units with it.
"""

import ast

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.numeric import NumericContext, engineering_registry


def expr(text: str) -> ast.Expression:
    return ast.parse(text.replace("^", "**"), mode="eval")


def test_every_context_shares_one_registry():
    assert NumericContext().ureg is NumericContext().ureg
    assert NumericContext().ureg is engineering_registry()


def test_quantities_from_two_contexts_can_be_combined():
    """The reason this is not only a speed change. Two registries make two kinds of
    quantity that refuse to meet, and Pint says so in as many words."""
    force = NumericContext().evaluate_expression(expr("5*kN"))
    span = NumericContext().evaluate_expression(expr("2*m"))
    moment = force * span
    assert moment.to("kN*m").magnitude == pytest.approx(10.0)


def test_a_definition_the_registry_needs_is_added_once():
    """`tonf` is not one of Pint's own units; the context defines it. Defined on a shared
    registry it must be defined once - a second context redefining it is the failure this
    change could introduce, and it would surface as an exception on the second engine a
    notebook builds."""
    for _ in range(3):
        context = NumericContext()
        value = context.evaluate_expression(expr("2.8*tonf/m"))
        assert value.to("kN/m").magnitude == pytest.approx(2.8 * 9.80665)


def test_a_reset_clears_the_values_and_keeps_the_units(monkeypatch):
    """A shared registry outlives a reset, and must: `%eng_reset` clears the sheet, not
    the definition of a kilonewton. The values do go."""
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    magics.eng("", "q := 2.8*tonf/m\n")
    assert "q" in magics.engine.numeric_context.values

    magics.eng_reset("")
    assert magics.engine.numeric_context.values == {}

    captured.clear()
    magics.eng("", "q := 2.8*tonf/m\nL := 6*m\n")
    latex = "".join(getattr(obj, "data", "") for obj in captured)
    assert r"\mathrm{tonf}" in latex, latex
    assert "6.00" in latex, latex


def test_a_context_does_not_carry_another_context_s_values():
    """Sharing the registry must not leak the sheet. Values stay per context."""
    first = NumericContext()
    first.assign("q", expr("10*kN/m"))
    assert NumericContext().get("q") is None
