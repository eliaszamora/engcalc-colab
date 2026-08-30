import pytest
import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell


def _define_function(engine: EngineeringEngine, source: str, name: str = "q"):
    statement = parse_cell(source)[0]
    engine.evaluate(statement)
    return engine.functions[name].expression


def test_piecewise_builds_sympy_piecewise_in_source_order():
    engine = EngineeringEngine()

    expression = _define_function(
        engine,
        "q(x) = piecewise(q1, x < a, q2, x <= L, 0)",
    )

    x = engine.resolve_symbol("x")
    a = engine.resolve_symbol("a")
    L = engine.resolve_symbol("L")
    q1 = engine.resolve_symbol("q1")
    q2 = engine.resolve_symbol("q2")

    assert isinstance(expression, sp.Piecewise)
    assert expression.args == (
        (q1, sp.StrictLessThan(x, a)),
        (q2, sp.LessThan(x, L)),
        (sp.Integer(0), sp.true),
    )


def test_piecewise_strict_and_inclusive_bounds_control_endpoint_ownership():
    engine = EngineeringEngine()

    expression = _define_function(
        engine,
        "q(x) = piecewise(1, x < 0, 2, x <= 1, 3)",
    )
    x = engine.resolve_symbol("x")

    assert expression.subs(x, -1) == 1
    assert expression.subs(x, 0) == 2
    assert expression.subs(x, 1) == 2
    assert expression.subs(x, 2) == 3


def test_piecewise_preserves_reversed_comparison_orientation():
    engine = EngineeringEngine()

    expression = _define_function(
        engine,
        "q(x) = piecewise(q1, a < x, 0)",
    )

    x = engine.resolve_symbol("x")
    a = engine.resolve_symbol("a")
    assert expression.args[0][1] == sp.StrictLessThan(a, x)


def test_piecewise_allows_nested_piecewise_branch_values():
    engine = EngineeringEngine()

    expression = _define_function(
        engine,
        "q(x) = piecewise(piecewise(q1, x < a, q2), x < L, 0)",
    )

    assert isinstance(expression, sp.Piecewise)
    assert isinstance(expression.args[0][0], sp.Piecewise)


def test_piecewise_rejects_mixed_interval_variables_before_symbolic_evaluation():
    with pytest.raises(EngSyntaxError):
        parse_cell("q(x, y) = piecewise(q1, x < a, q2, y < b, 0)")
