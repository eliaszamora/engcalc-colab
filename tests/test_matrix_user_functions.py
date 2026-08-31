import pytest
import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_rotation_matrix_function_binds_symbolically():
    engine = EngineeringEngine()
    run(
        engine,
        "R(theta) = [cos(theta), -sin(theta); sin(theta), cos(theta)]",
    )

    result = run(engine, "A = R(phi)")

    phi = engine.resolve_symbol("phi")
    expected = sp.ImmutableMatrix(
        [[sp.cos(phi), -sp.sin(phi)], [sp.sin(phi), sp.cos(phi)]]
    )
    assert isinstance(result.value, sp.ImmutableMatrix)
    assert result.value == expected


def test_structural_stiffness_function_remains_exact_matrix():
    engine = EngineeringEngine()
    run(
        engine,
        "k(E, I, L) = [12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L]",
    )

    result = run(engine, "K = k(E0, I0, L0)")

    E0, I0, L0 = tuple(engine.resolve_symbol(name) for name in "E0 I0 L0".split())
    expected = sp.ImmutableMatrix(
        [
            [12 * E0 * I0 / L0**3, 6 * E0 * I0 / L0**2],
            [6 * E0 * I0 / L0**2, 4 * E0 * I0 / L0],
        ]
    )
    assert isinstance(result.value, sp.ImmutableMatrix)
    assert result.value == expected


def test_matrix_function_parameter_binding_is_simultaneous():
    engine = EngineeringEngine()
    run(engine, "swap(x, y) = [x, y; y, x]")

    result = run(engine, "A = swap(y, x)")

    x, y = tuple(engine.resolve_symbol(name) for name in "x y".split())
    assert result.value == sp.ImmutableMatrix([[y, x], [x, y]])


def test_matrix_function_parameter_shadows_global_symbolic_value():
    engine = EngineeringEngine()
    run(engine, "theta = 7")
    run(
        engine,
        "R(theta) = [cos(theta), -sin(theta); sin(theta), cos(theta)]",
    )

    result = run(engine, "A = R(0)")

    assert result.value == sp.eye(2).as_immutable()


@pytest.mark.parametrize(
    ("call", "received"),
    [("R()", 0), ("R(a, b)", 2)],
)
def test_matrix_function_preserves_exact_arity_diagnostics(call, received):
    engine = EngineeringEngine()
    run(
        engine,
        "R(theta) = [cos(theta), -sin(theta); sin(theta), cos(theta)]",
    )

    with pytest.raises(
        EngEvaluationError,
        match=rf"function 'R' expects 1 arguments \(theta\), received {received}",
    ):
        run(engine, f"A = {call}")


def test_inverse_trig_nodes_inside_matrix_function_preserve_exact_node_semantics():
    engine = EngineeringEngine()
    run(engine, "angles(x, a) = [atan(x/a), asin(x/a)]")

    result = run(engine, "A = angles(1, 2)")

    assert isinstance(result.value, sp.ImmutableMatrix)
    assert result.value[0, 0].func == sp.atan
    assert result.value[0, 0].args == (sp.Rational(1, 2),)
    assert result.value[0, 1].func == sp.asin
    assert result.value[0, 1].args == (sp.Rational(1, 2),)
