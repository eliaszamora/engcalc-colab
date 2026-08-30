import sympy as sp
import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError, EngSyntaxError
from engcalc_colab.models import MatrixShape
from engcalc_colab.parser import parse_cell


def eval_cell(engine, source):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def value_of(engine, source):
    return eval_cell(engine, source)[-1].value


def test_identity_builds_immutable_exact_matrix():
    engine = EngineeringEngine()
    value = value_of(engine, "I = identity(3)")
    assert isinstance(value, sp.ImmutableMatrix)
    assert value == sp.eye(3).as_immutable()


def test_zeros_builds_requested_immutable_shape():
    engine = EngineeringEngine()
    value = value_of(engine, "Z = zeros(2,3)")
    assert isinstance(value, sp.ImmutableMatrix)
    assert value.shape == (2, 3)
    assert value == sp.zeros(2, 3).as_immutable()


def test_diag_builds_immutable_diagonal_matrix():
    engine = EngineeringEngine()
    value = value_of(engine, "D = diag(a,b,c)")
    a, b, c = sp.symbols("a b c")
    assert isinstance(value, sp.ImmutableMatrix)
    assert value == sp.diag(a, b, c).as_immutable()


@pytest.mark.parametrize("source", [
    "I = identity(0)",
    "I = identity(-1)",
    "I = identity(2.5)",
    "I = identity(n)",
    "Z = zeros(0,2)",
    "Z = zeros(2,0)",
    "Z = zeros(-1,2)",
    "Z = zeros(2,-1)",
    "Z = zeros(2.5,3)",
    "Z = zeros(m,3)",
])
def test_matrix_constructor_dimensions_must_be_positive_exact_integers(source):
    engine = EngineeringEngine()
    with pytest.raises(
        EngEvaluationError,
        match="matrix dimensions must be positive exact integers",
    ):
        eval_cell(engine, source)


def test_diag_requires_at_least_one_scalar_entry():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError, match="diag expects at least one scalar entry"):
        eval_cell(engine, "D = diag()")


def test_diag_rejects_matrix_entries():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1,2;3,4]")
    with pytest.raises(EngEvaluationError, match="diag entries must be scalar"):
        eval_cell(engine, "D = diag(A, 2)")


def test_transpose_returns_immutable_matrix():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a,b,c; d,e,f]")
    value = value_of(engine, "T = transpose(A)")
    a, b, c, d, e, f = sp.symbols("a b c d e f")
    assert isinstance(value, sp.ImmutableMatrix)
    assert value == sp.ImmutableMatrix([[a, d], [b, e], [c, f]])


def test_determinant_is_exact_scalar_expression():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a,b; c,d]")
    value = value_of(engine, "delta = det(A)")
    a, b, c, d = sp.symbols("a b c d")
    assert sp.expand(value - (a*d - b*c)) == 0


def test_inverse_is_exact_and_immutable():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a,b; c,d]")
    inverse = value_of(engine, "Ai = inv(A)")
    assert isinstance(inverse, sp.ImmutableMatrix)
    assert sp.simplify(inverse * engine.namespace["A"] - sp.eye(2)) == sp.zeros(2)


def test_trace_is_exact_scalar_expression():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a,b; c,d]")
    value = value_of(engine, "t = trace(A)")
    a, d = sp.symbols("a d")
    assert value == a + d


def test_size_returns_immutable_matrix_shape_model():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a,b,c; d,e,f]")
    value = value_of(engine, "s = size(A)")
    assert isinstance(value, MatrixShape)
    assert value == MatrixShape(rows=2, cols=3)
    with pytest.raises(Exception):
        value.rows = 4


@pytest.mark.parametrize("source, message", [
    ("d = det(R)", "det requires a square matrix"),
    ("t = trace(R)", "trace requires a square matrix"),
    ("X = inv(R)", "inv requires a square matrix"),
])
def test_square_only_functions_reject_rectangular_matrices(source, message):
    engine = EngineeringEngine()
    eval_cell(engine, "R = [1,2,3; 4,5,6]")
    with pytest.raises(EngEvaluationError, match=message):
        eval_cell(engine, source)


def test_inverse_reports_singular_matrix_concisely():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1,2; 2,4]")
    with pytest.raises(EngEvaluationError, match="inv requires a nonsingular matrix"):
        eval_cell(engine, "Ai = inv(A)")


@pytest.mark.parametrize("source, message", [
    ("x = transpose(2)", "transpose requires a matrix"),
    ("x = det(2)", "det requires a matrix"),
    ("x = inv(2)", "inv requires a matrix"),
    ("x = trace(2)", "trace requires a matrix"),
    ("x = size(2)", "size requires a matrix"),
])
def test_exact_matrix_functions_reject_scalar_arguments(source, message):
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError, match=message):
        eval_cell(engine, source)


def test_constructor_and_function_names_are_reserved_identifiers():
    reserved = (
        "identity", "zeros", "diag", "transpose", "det", "inv", "trace", "size"
    )
    for name in reserved:
        with pytest.raises(EngSyntaxError, match=f"reserved identifier '{name}'"):
            parse_cell(f"{name} = 2")


def test_matrix_constructor_and_function_keyword_arguments_remain_unsupported():
    for source in (
        "I = identity(n=3)",
        "Z = zeros(rows=2, cols=3)",
        "T = transpose(A=A)",
    ):
        with pytest.raises(EngSyntaxError, match="keyword arguments are unsupported"):
            parse_cell(source)
