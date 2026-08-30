import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError, EngSyntaxError
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


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("A = [a, b;\n c, d", r"line 1: unclosed matrix literal"),
        ("A = [a, b; c, d, e]", "matrix literal rows must have the same number of columns"),
        ("A = [a, [b,c]; d, e]", "nested matrix literals are unsupported"),
    ],
)
def test_matrix_literal_diagnostics_remain_engcalc_syntax_errors(source, message):
    with pytest.raises(EngSyntaxError, match=message):
        parse_cell(source)


def test_zero_based_matrix_index_reports_one_based_contract():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1, 2; 3, 4]")
    with pytest.raises(EngEvaluationError, match="matrix indices must be positive integers"):
        eval_cell(engine, "x = A[0,1]")


def test_singular_inverse_does_not_leak_sympy_exception_type():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1, 2; 2, 4]")
    with pytest.raises(EngEvaluationError, match="inv requires a nonsingular matrix") as exc_info:
        eval_cell(engine, "Ai = inv(A)")
    assert "NonInvertibleMatrixError" not in str(exc_info.value)


def test_matrix_numeric_incompatibility_reports_one_based_cell_not_pint_exception():
    engine = EngineeringEngine()
    eval_cell(engine, "a := 1*kN\nb := 1*m\nA = [1, 2; a+b, 4]")
    with pytest.raises(
        EngEvaluationError,
        match=r"matrix numeric evaluation has incompatible units at \[2,1\]",
    ) as exc_info:
        eval_cell(engine, "numeric(A)")
    assert "DimensionalityError" not in str(exc_info.value)


def test_heterogeneous_matrix_target_unit_rejection_is_matrix_level_diagnostic():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "E := 200*GPa\n"
        "I := 450e6*mm^4\n"
        "L := 6000*mm\n"
        "K = [12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L]",
    )
    with pytest.raises(EngEvaluationError) as exc_info:
        eval_cell(engine, "numeric(K, kN/mm)")
    message = str(exc_info.value).lower()
    assert "matrix" in message
    assert "target unit" in message or "incompatible units" in message
    assert "dimensionalityerror" not in message


def test_nonunique_matrix_solve_uses_engcalc_diagnostic():
    engine = EngineeringEngine()
    eval_cell(engine, "A = [1, 2; 2, 4]\nb = [1; 2]")
    with pytest.raises(
        EngEvaluationError,
        match="solve matrix system requires a unique solution",
    ):
        eval_cell(engine, "solve(A, b)")


def test_heterogeneous_guarded_analysis_uses_operation_specific_diagnostic():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "E := 200*GPa\n"
        "I := 450e6*mm^4\n"
        "L := 6000*mm\n"
        "K = [12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L]",
    )
    with pytest.raises(
        EngEvaluationError,
        match=r"matrix operation 'rref' requires a dimensionless or common-scale matrix",
    ):
        eval_cell(engine, "numeric(rref(K))")
