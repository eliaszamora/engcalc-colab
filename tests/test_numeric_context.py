import ast

import pytest
import sympy as sp

from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.numeric import NumericContext


def expr(text: str) -> ast.Expression:
    return ast.parse(text.replace("^", "**"), mode="eval")


def test_assigns_engineering_quantity_with_tonf():
    ctx = NumericContext()

    q = ctx.assign("q", expr("2.8*tonf/m"))

    assert q.to("tonf/m").magnitude == pytest.approx(2.8)


def test_numeric_values_can_reference_previous_numeric_values():
    ctx = NumericContext()
    ctx.assign("q", expr("2.8*tonf/m"))
    ctx.assign("L", expr("4*m"))

    p = ctx.assign("P", expr("q*L"))

    assert p.to("tonf").magnitude == pytest.approx(11.2)


def test_evaluate_expression_returns_quantity_without_persisting_assignment():
    ctx = NumericContext()

    value = ctx.evaluate_expression(expr("5*kN/m"))

    assert value.to("kN/m").magnitude == pytest.approx(5.0)
    assert ctx.values == {}


def test_evaluate_expression_can_reference_existing_numeric_values_without_mutation():
    ctx = NumericContext()
    ctx.assign("q_ref", expr("5*kN/m"))
    before = dict(ctx.values)

    value = ctx.evaluate_expression(expr("2*q_ref"))

    assert value.to("kN/m").magnitude == pytest.approx(10.0)
    assert ctx.values == before


def test_tonf_conversion_uses_engineering_definition():
    ctx = NumericContext()

    force = ctx.assign("F", expr("1*tonf"))

    assert force.to("kN").magnitude == pytest.approx(9.80665)


def test_symbolic_expression_evaluates_with_pint_quantities():
    ctx = NumericContext()
    q, L = sp.symbols("q L")
    ctx.assign("q", expr("2.8*tonf/m"))
    ctx.assign("L", expr("4*m"))

    substitutions, value = ctx.evaluate_symbolic(3*q*L/8)

    assert set(substitutions) == {"q", "L"}
    assert value.to("tonf").magnitude == pytest.approx(4.2)


def test_target_unit_expression_supports_compound_engineering_units():
    ctx = NumericContext()

    unit = ctx.evaluate_unit_expression(expr("kN*m"))
    converted = (5.6 * ctx.ureg.tonf * ctx.ureg.m).to(unit)

    assert converted.magnitude == pytest.approx(54.91724)
    assert "kilonewton" in str(unit)
    assert "meter" in str(unit)


def test_target_unit_expression_supports_powers():
    ctx = NumericContext()

    unit = ctx.evaluate_unit_expression(expr("mm^4"))

    assert str(unit) == "millimeter ** 4"


def test_target_unit_expression_rejects_unknown_names():
    ctx = NumericContext()

    with pytest.raises(EngEvaluationError, match="unknown target unit 'banana'"):
        ctx.evaluate_unit_expression(expr("banana"))


def test_missing_numeric_symbol_is_reported_in_sorted_order():
    ctx = NumericContext()
    q, L, E = sp.symbols("q L E")
    ctx.assign("q", expr("2.8*tonf/m"))

    with pytest.raises(EngEvaluationError, match=r"requires values for: E, L"):
        ctx.evaluate_symbolic(q*L/E)


def test_unknown_numeric_name_is_rejected():
    ctx = NumericContext()

    with pytest.raises(EngEvaluationError, match="unknown numeric name 'banana'"):
        ctx.assign("q", expr("2.8*banana/m"))


def test_incompatible_numeric_units_are_concise():
    ctx = NumericContext()

    with pytest.raises(EngEvaluationError, match="incompatible units"):
        ctx.assign("bad", expr("2*m + 3*kN"))


def test_numeric_context_reset_clears_values():
    ctx = NumericContext()
    ctx.assign("L", expr("4*m"))

    ctx.reset()

    assert ctx.get("L") is None
