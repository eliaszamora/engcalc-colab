import pytest
import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_multiarg_function_binds_positionally():
    engine = EngineeringEngine()
    run(engine, "f(x, a, b) = a*x + b")

    result = run(engine, "y = f(t, 2, 3)")

    t = engine.resolve_symbol("t")
    assert sp.simplify(result.value - (2*t + 3)) == 0


def test_parameter_binding_is_simultaneous_not_sequential():
    engine = EngineeringEngine()
    run(engine, "swap(x, y) = x - y")

    result = run(engine, "z = swap(y, x)")

    x, y = tuple(engine.resolve_symbol(name) for name in "x y".split())
    assert sp.expand(result.value) == y - x


def test_function_parameter_shadows_same_named_symbolic_context_value():
    engine = EngineeringEngine()
    run(engine, "L = 5")
    run(engine, "f(L) = 2*L")

    result = run(engine, "y = f(3)")

    assert result.value == 6


def test_nested_multiarg_user_functions_compose_symbolically():
    engine = EngineeringEngine()
    run(engine, "qU(qD, qL) = 1.2*qD + 1.6*qL")
    run(engine, "M(x, q, L) = q*x*(L-x)/2")

    result = run(engine, "M_U(x) = M(x, qU(qD, qL), L)")

    assert {item.name for item in result.value.free_symbols} == {
        "x",
        "qD",
        "qL",
        "L",
    }


def test_multiarg_function_rejects_too_few_arguments_with_signature():
    engine = EngineeringEngine()
    run(engine, "M(x, q, L) = q*x*(L-x)/2")

    with pytest.raises(
        EngEvaluationError,
        match=r"function 'M' expects 3 arguments \(x, q, L\), received 2",
    ):
        run(engine, "y = M(x, q)")


def test_multiarg_function_rejects_too_many_arguments_with_signature():
    engine = EngineeringEngine()
    run(engine, "M(x, q, L) = q*x*(L-x)/2")

    with pytest.raises(
        EngEvaluationError,
        match=r"function 'M' expects 3 arguments \(x, q, L\), received 4",
    ):
        run(engine, "y = M(x, q, L, E)")


def test_redefinition_replaces_signature_instead_of_overloading():
    engine = EngineeringEngine()
    run(engine, "f(x) = x + 1")
    run(engine, "f(x, a) = x + a")

    with pytest.raises(EngEvaluationError, match="expects 2 arguments"):
        run(engine, "y = f(1)")

    result = run(engine, "y = f(1, 2)")
    assert result.value == 3


def test_multiarg_substitution_preserves_inverse_trig_node():
    engine = EngineeringEngine()
    run(engine, "theta(x, a) = atan(x/a)")

    result = run(engine, "value = theta(1, 2)")

    assert result.value.func == sp.atan
    assert result.value.args == (sp.Rational(1, 2),)
