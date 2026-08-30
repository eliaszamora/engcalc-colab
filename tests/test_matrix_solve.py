import sympy as sp
import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import NumericMatrixEvaluationResult
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_matrix_solve_returns_exact_column_solution_and_satisfies_system():
    engine = EngineeringEngine()
    run(engine, "K = [k1+k2, -k2; -k2, k2]")
    run(engine, "F = [P; 0]")

    result = run(engine, "u = solve(K, F)")

    K = engine.namespace["K"]
    F = engine.namespace["F"]
    u = result.value
    assert isinstance(u, sp.ImmutableMatrix)
    assert u.shape == (2, 1)
    assert (K * u - F).applyfunc(sp.simplify) == sp.zeros(2, 1)


def test_matrix_solve_rejects_nonsquare_coefficient_matrix():
    engine = EngineeringEngine()
    run(engine, "A = [1, 0, 0; 0, 1, 0]")
    run(engine, "b = [1; 2]")

    with pytest.raises(EngEvaluationError, match=r"solve matrix A must be square"):
        run(engine, "solve(A, b)")


def test_matrix_solve_rejects_row_vector_rhs():
    engine = EngineeringEngine()
    run(engine, "A = identity(2)")
    run(engine, "b = [1, 2]")

    with pytest.raises(EngEvaluationError, match=r"solve matrix rhs must be a column vector"):
        run(engine, "solve(A, b)")


def test_matrix_solve_rejects_rhs_with_wrong_row_count():
    engine = EngineeringEngine()
    run(engine, "A = identity(2)")
    run(engine, "b = [1; 2; 3]")

    with pytest.raises(
        EngEvaluationError,
        match=r"solve matrix rhs row count must match A",
    ):
        run(engine, "solve(A, b)")


def test_matrix_solve_rejects_singular_or_nonunique_system():
    engine = EngineeringEngine()
    run(engine, "A = [1, 2; 2, 4]")
    run(engine, "b = [1; 2]")

    with pytest.raises(
        EngEvaluationError,
        match=r"solve matrix system requires a unique solution",
    ):
        run(engine, "solve(A, b)")


def test_numeric_exact_matrix_solution_has_displacement_units():
    engine = EngineeringEngine()
    run(engine, "K = [k1+k2, -k2; -k2, k2]")
    run(engine, "F = [P; 0]")
    run(engine, "u = solve(K, F)")
    run(engine, "k1 := 20*kN/mm")
    run(engine, "k2 := 15*kN/mm")
    run(engine, "P := 30*kN")

    result = run(engine, "numeric(u)")

    assert isinstance(result, NumericMatrixEvaluationResult)
    assert result.quantity_matrix.rows == 2
    assert result.quantity_matrix.cols == 1
    assert result.quantity_matrix.entry(0, 0).to("mm").magnitude == pytest.approx(1.5)
    assert result.quantity_matrix.entry(1, 0).to("mm").magnitude == pytest.approx(1.5)


def test_mixed_translation_rotation_stiffness_product_evaluates_force_and_moment_cells():
    engine = EngineeringEngine()
    run(
        engine,
        "K = [12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L]",
    )
    run(engine, "d = [u; theta]")
    run(engine, "Q = K*d")
    run(engine, "E := 200*GPa")
    run(engine, "I := 450e6*mm^4")
    run(engine, "L := 6000*mm")
    run(engine, "u := 2*mm")
    run(engine, "theta := 0.01")

    result = run(engine, "numeric(Q)")

    assert isinstance(result, NumericMatrixEvaluationResult)
    assert result.quantity_matrix.rows == 2
    assert result.quantity_matrix.cols == 1
    assert result.quantity_matrix.entry(0, 0).to("kN").magnitude == pytest.approx(0.4)
    assert result.quantity_matrix.entry(1, 0).to("kN*mm").magnitude == pytest.approx(1650.0)


def test_scalar_solve_contract_remains_unchanged():
    engine = EngineeringEngine()

    result = run(engine, "root = solve(x + 2 = 0, x)")

    assert result.value == -2
