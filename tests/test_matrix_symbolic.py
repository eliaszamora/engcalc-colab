import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell


def eval_cell(engine, source):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def value_of(engine, source):
    return eval_cell(engine, source)[-1].value


def test_matrix_assignment_builds_immutable_matrix():
    engine = EngineeringEngine()
    value = value_of(engine, "A = [a, b; c, d]")
    assert isinstance(value, sp.ImmutableMatrix)
    assert value.shape == (2, 2)
    assert value == sp.ImmutableMatrix([[sp.Symbol("a"), sp.Symbol("b")], [sp.Symbol("c"), sp.Symbol("d")]])


def test_row_and_column_vector_orientation_is_preserved():
    engine = EngineeringEngine()
    row = value_of(engine, "r = [a, b, c]")
    col = value_of(engine, "v = [a; b; c]")
    assert isinstance(row, sp.ImmutableMatrix)
    assert isinstance(col, sp.ImmutableMatrix)
    assert row.shape == (1, 3)
    assert col.shape == (3, 1)


def test_matrix_addition_and_subtraction_are_exact():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a, b; c, d]\nB = [1, 2; 3, 4]")
    plus = value_of(engine, "C = A + B")
    minus = value_of(engine, "D = A - B")
    assert isinstance(plus, sp.ImmutableMatrix)
    assert plus == sp.ImmutableMatrix([[sp.Symbol("a") + 1, sp.Symbol("b") + 2], [sp.Symbol("c") + 3, sp.Symbol("d") + 4]])
    assert minus == sp.ImmutableMatrix([[sp.Symbol("a") - 1, sp.Symbol("b") - 2], [sp.Symbol("c") - 3, sp.Symbol("d") - 4]])


def test_scalar_matrix_multiplication_and_division_preserve_immutable_matrix():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a, b; c, d]")
    left = value_of(engine, "L = 2*A")
    right = value_of(engine, "R = A*2")
    divided = value_of(engine, "D = A/2")
    expected = sp.ImmutableMatrix([[2*sp.Symbol("a"), 2*sp.Symbol("b")], [2*sp.Symbol("c"), 2*sp.Symbol("d")]])
    assert left == expected
    assert right == expected
    assert isinstance(left, sp.ImmutableMatrix)
    assert isinstance(right, sp.ImmutableMatrix)
    assert isinstance(divided, sp.ImmutableMatrix)
    assert divided == sp.ImmutableMatrix([[sp.Symbol("a")/2, sp.Symbol("b")/2], [sp.Symbol("c")/2, sp.Symbol("d")/2]])


def test_matrix_multiplication_is_mathematical_not_elementwise():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a, b; c, d]\nB = [e, f; g, h]")
    product = value_of(engine, "C = A*B")
    a, b, c, d, e, f, g, h = sp.symbols("a b c d e f g h")
    assert product == sp.ImmutableMatrix([[a*e + b*g, a*f + b*h], [c*e + d*g, c*f + d*h]])


def test_row_times_column_and_column_times_row_keep_matrix_shapes():
    engine = EngineeringEngine()
    eval_cell(engine, "r = [a, b, c]\nv = [x; y; z]")
    dot_matrix = value_of(engine, "p = r*v")
    outer = value_of(engine, "Q = v*r")
    a, b, c, x, y, z = sp.symbols("a b c x y z")
    assert isinstance(dot_matrix, sp.ImmutableMatrix)
    assert dot_matrix.shape == (1, 1)
    assert dot_matrix[0, 0] == a*x + b*y + c*z
    assert isinstance(outer, sp.ImmutableMatrix)
    assert outer.shape == (3, 3)
    assert outer == sp.ImmutableMatrix([[a*x, b*x, c*x], [a*y, b*y, c*y], [a*z, b*z, c*z]])


def test_integer_matrix_powers_are_exact_and_immutable():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a, b; c, d]")
    identity = value_of(engine, "I2 = A^0")
    square = value_of(engine, "A2 = A^2")
    inverse = value_of(engine, "Ai = A^-1")
    assert isinstance(identity, sp.ImmutableMatrix)
    assert identity == sp.eye(2).as_immutable()
    assert isinstance(square, sp.ImmutableMatrix)
    assert square == (sp.ImmutableMatrix([[sp.Symbol("a"), sp.Symbol("b")], [sp.Symbol("c"), sp.Symbol("d")]]) ** 2)
    assert isinstance(inverse, sp.ImmutableMatrix)
    assert sp.simplify(inverse * engine.namespace["A"] - sp.eye(2)) == sp.zeros(2)
