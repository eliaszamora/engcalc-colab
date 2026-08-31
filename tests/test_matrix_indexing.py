import sympy as sp
import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError, EngSyntaxError
from engcalc_colab.parser import parse_cell


def eval_cell(engine, source):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def value_of(engine, source):
    return eval_cell(engine, source)[-1].value


def test_general_matrix_uses_one_based_two_index_lookup():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a, b; c, d]")
    assert value_of(engine, "x = A[2,1]") == engine.resolve_symbol("c")
    assert value_of(engine, "y = A[1,2]") == engine.resolve_symbol("b")


def test_row_and_column_vectors_accept_one_based_single_index_lookup():
    engine = EngineeringEngine()
    eval_cell(engine, "r = [a, b, c]\nv = [x; y; z]")
    assert value_of(engine, "p = r[2]") == engine.resolve_symbol("b")
    assert value_of(engine, "q = v[3]") == engine.resolve_symbol("z")


def test_two_indices_are_also_valid_for_row_and_column_vectors():
    engine = EngineeringEngine()
    eval_cell(engine, "r = [a, b, c]\nv = [x; y; z]")
    assert value_of(engine, "p = r[1,3]") == engine.resolve_symbol("c")
    assert value_of(engine, "q = v[2,1]") == engine.resolve_symbol("y")


@pytest.mark.parametrize("source", [
    "x = A[0,1]",
    "x = A[-1,1]",
    "x = A[1.5,1]",
    "x = A[i,1]",
])
def test_matrix_indices_must_be_positive_exact_integers(source):
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a, b; c, d]")
    with pytest.raises(EngEvaluationError, match="matrix indices must be positive integers"):
        eval_cell(engine, source)


def test_general_matrix_requires_two_indices():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a, b; c, d]")
    with pytest.raises(EngEvaluationError, match="general matrix indexing requires two indices"):
        eval_cell(engine, "x = A[1]")


def test_matrix_index_rejects_too_many_indices():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a, b; c, d]")
    with pytest.raises(EngEvaluationError, match="matrix indexing expects one vector index or two matrix indices"):
        eval_cell(engine, "x = A[1,1,1]")


def test_matrix_index_reports_out_of_range_coordinates():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [a, b; c, d]")
    with pytest.raises(EngEvaluationError, match=r"matrix index \[3,1\] is out of range for shape 2x2"):
        eval_cell(engine, "x = A[3,1]")


def test_indexing_non_matrix_is_rejected():
    engine = EngineeringEngine()
    eval_cell(engine, "a = x + 1")
    with pytest.raises(EngEvaluationError, match="matrix indexing requires a matrix"):
        eval_cell(engine, "y = a[1]")


def test_python_slice_syntax_remains_rejected():
    with pytest.raises(EngSyntaxError, match="matrix slicing is unsupported"):
        parse_cell("x = A[1:2]")
