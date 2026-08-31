import pytest
import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_simplify_maps_over_matrix_entries():
    engine = EngineeringEngine()
    run(engine, "A = [(x^2 - 1)/(x - 1), (x^2 - x)/x]")

    result = run(engine, "B = simplify(A)")

    x = engine.resolve_symbol("x")
    assert isinstance(result.value, sp.ImmutableMatrix)
    assert result.value == sp.ImmutableMatrix([[x + 1, x - 1]])


def test_expand_maps_over_matrix_entries():
    engine = EngineeringEngine()
    run(engine, "A = [(x + 1)^2, (x - 1)*(x + 1)]")

    result = run(engine, "B = expand(A)")

    x = engine.resolve_symbol("x")
    assert result.value == sp.ImmutableMatrix(
        [[x**2 + 2*x + 1, x**2 - 1]]
    )


def test_factor_maps_over_matrix_entries():
    engine = EngineeringEngine()
    run(engine, "A = [x^2 - 1, x^2 + 2*x + 1]")

    result = run(engine, "B = factor(A)")

    x = engine.resolve_symbol("x")
    assert result.value == sp.ImmutableMatrix(
        [[(x - 1)*(x + 1), (x + 1)**2]]
    )


def test_subs_maps_over_matrix_entries():
    engine = EngineeringEngine()
    run(engine, "A = [x, x^2; x + 1, 2*x]")

    result = run(engine, "B = subs(A, x, 2)")

    assert result.value == sp.ImmutableMatrix([[2, 4], [3, 4]])


def test_diff_maps_over_matrix_entries_and_returns_immutable_matrix():
    engine = EngineeringEngine()
    run(engine, "A = [x^2, sin(x); x^3, 2*x]")

    result = run(engine, "B = diff(A, x)")

    x = engine.resolve_symbol("x")
    assert isinstance(result.value, sp.ImmutableMatrix)
    assert result.value == sp.ImmutableMatrix(
        [[2*x, sp.cos(x)], [3*x**2, 2]]
    )


def test_definite_integral_maps_over_matrix_entries():
    engine = EngineeringEngine()
    run(engine, "A = [x, x^2; 1, 2*x]")

    result = run(engine, "B = integral(A, x, 0, L)")

    L = engine.resolve_symbol("L")
    assert isinstance(result.value, sp.ImmutableMatrix)
    assert result.value == sp.ImmutableMatrix(
        [[L**2 / 2, L**3 / 3], [L, L**2]]
    )


def test_matrix_piecewise_derivative_is_entrywise_and_preserves_breakpoint_union():
    engine = EngineeringEngine()
    run(
        engine,
        "q(x) = [piecewise(x^2, x < a, x, x <= L, 0); "
        "piecewise(2*x, x < b, 3*x, x <= L, 0)]",
    )

    result = run(engine, "dq(x) = diff(q(x), x)")

    assert isinstance(result.value, sp.ImmutableMatrix)
    assert all(entry.has(sp.Piecewise) for entry in result.value)
    assert not any(entry.has(sp.DiracDelta) for entry in result.value)
    function = engine.functions["dq"]
    assert function.derivative_variable == "x"
    assert set(function.derivative_breakpoints) == {
        engine.resolve_symbol("a"),
        engine.resolve_symbol("b"),
        engine.resolve_symbol("L"),
    }


def test_scalar_trig_remains_invalid_for_whole_matrix():
    engine = EngineeringEngine()
    run(engine, "A = [x, 0; 0, x]")

    with pytest.raises(EngEvaluationError, match=r"matrix|symbolic evaluation failed"):
        run(engine, "B = sin(A)")
