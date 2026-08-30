import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def eval_cell(engine, source):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def test_matrix_addition_shape_mismatch_is_concise():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1, 2; 3, 4]\nr = [1, 2]")
    with pytest.raises(EngEvaluationError, match="matrix addition dimension mismatch: left is 2x2, right is 1x2"):
        eval_cell(engine, "C = A + r")


def test_matrix_subtraction_shape_mismatch_is_concise():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1, 2; 3, 4]\nr = [1, 2]")
    with pytest.raises(EngEvaluationError, match="matrix subtraction dimension mismatch: left is 2x2, right is 1x2"):
        eval_cell(engine, "C = A - r")


def test_matrix_multiplication_shape_mismatch_is_concise():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1, 2; 3, 4]\nB = [1, 2, 3; 4, 5, 6; 7, 8, 9]")
    with pytest.raises(EngEvaluationError, match="matrix multiplication dimension mismatch: left is 2x2, right is 3x3"):
        eval_cell(engine, "C = A*B")


def test_matrix_scalar_addition_is_rejected_in_both_orders():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1, 2; 3, 4]")
    for source in ("C = A + 2", "C = 2 + A"):
        with pytest.raises(EngEvaluationError, match="matrix addition requires two matrices with the same shape"):
            eval_cell(engine, source)


def test_matrix_scalar_subtraction_is_rejected_in_both_orders():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1, 2; 3, 4]")
    for source in ("C = A - 2", "C = 2 - A"):
        with pytest.raises(EngEvaluationError, match="matrix subtraction requires two matrices with the same shape"):
            eval_cell(engine, source)


def test_matrix_division_requires_scalar_denominator():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1, 2; 3, 4]\nB = [2, 0; 0, 2]")
    with pytest.raises(EngEvaluationError, match="matrix division requires a scalar denominator"):
        eval_cell(engine, "C = A/B")
    with pytest.raises(EngEvaluationError, match="division by a matrix is unsupported"):
        eval_cell(engine, "C = 2/A")


def test_matrix_power_requires_square_matrix():
    engine = EngineeringEngine()
    eval_cell(engine, "r = [1, 2, 3]")
    with pytest.raises(EngEvaluationError, match="matrix power requires a square matrix"):
        eval_cell(engine, "R = r^2")


def test_matrix_power_requires_exact_integer_exponent():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1, 2; 3, 4]")
    for source in ("R = A^0.5", "R = A^x"):
        with pytest.raises(EngEvaluationError, match="matrix exponent must be an exact integer"):
            eval_cell(engine, source)
