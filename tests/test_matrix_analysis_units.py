import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import EvaluationResult, NumericEvaluationResult, NumericMatrixEvaluationResult
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def define_homogeneous_matrix(engine: EngineeringEngine):
    run(engine, "k := 10*kN/mm")
    run(engine, "A = [2*k, 0; 0, 3*k]")


def define_heterogeneous_beam_matrix(engine: EngineeringEngine):
    run(engine, "E := 200*GPa")
    run(engine, "I := 450e6*mm^4")
    run(engine, "L := 6000*mm")
    run(
        engine,
        "K = [12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L]",
    )


def test_numeric_norm_accepts_homogeneous_common_scale_and_keeps_unit():
    engine = EngineeringEngine()
    define_homogeneous_matrix(engine)

    result = run(engine, "numeric(norm(A))")

    assert isinstance(result, NumericEvaluationResult)
    assert result.quantity.to("kN/mm").magnitude == pytest.approx((13.0) ** 0.5 * 10.0)


def test_numeric_rank_accepts_dimensionless_or_common_scale_source():
    engine = EngineeringEngine()
    define_homogeneous_matrix(engine)

    result = run(engine, "numeric(rank(A))")

    assert isinstance(result, NumericEvaluationResult)
    assert result.quantity.dimensionless
    assert result.quantity.magnitude == 2


def test_numeric_rref_accepts_homogeneous_source_and_returns_dimensionless_matrix():
    engine = EngineeringEngine()
    define_homogeneous_matrix(engine)

    result = run(engine, "numeric(rref(A))")

    assert isinstance(result, NumericMatrixEvaluationResult)
    assert result.quantity_matrix.rows == 2
    assert result.quantity_matrix.cols == 2
    assert result.quantity_matrix.entry(0, 0).dimensionless
    assert result.quantity_matrix.entry(0, 0).magnitude == 1
    assert result.quantity_matrix.entry(1, 1).magnitude == 1


def test_numeric_eigenvals_accept_homogeneous_source_and_preserve_common_unit():
    engine = EngineeringEngine()
    define_homogeneous_matrix(engine)

    result = run(engine, "numeric(eigenvals(A))")

    assert isinstance(result, EvaluationResult)
    eigenvalues = result.value
    assert type(eigenvalues).__name__ == "EigenvalueSet"
    assert tuple(entry.multiplicity for entry in eigenvalues.entries) == (1, 1)
    assert tuple(
        entry.value.to("kN/mm").magnitude for entry in eigenvalues.entries
    ) == pytest.approx((20.0, 30.0))


def test_dimensionless_matrix_analysis_numeric_path_is_accepted():
    engine = EngineeringEngine()
    run(engine, "A = [3, 0; 0, 4]")

    norm_result = run(engine, "numeric(norm(A))")
    eigen_result = run(engine, "numeric(eigenvals(A))")

    assert norm_result.quantity.dimensionless
    assert norm_result.quantity.magnitude == 5
    assert tuple(entry.value.magnitude for entry in eigen_result.value.entries) == pytest.approx((3, 4))
    assert all(entry.value.dimensionless for entry in eigen_result.value.entries)


@pytest.mark.parametrize("operation", ["rank", "rref", "norm", "eigenvals", "eigenvects"])
def test_heterogeneous_matrix_rejects_guarded_numeric_analysis(operation):
    engine = EngineeringEngine()
    define_heterogeneous_beam_matrix(engine)

    with pytest.raises(
        EngEvaluationError,
        match=rf"matrix operation '{operation}' requires a dimensionless or common-scale matrix",
    ):
        run(engine, f"numeric({operation}(K))")


def test_assigned_guarded_rref_preserves_source_provenance_until_numeric():
    engine = EngineeringEngine()
    define_heterogeneous_beam_matrix(engine)
    run(engine, "R = rref(K)")

    with pytest.raises(
        EngEvaluationError,
        match=r"matrix operation 'rref' requires a dimensionless or common-scale matrix",
    ):
        run(engine, "numeric(R)")


def test_matrix_user_function_propagates_substituted_numeric_guard():
    engine = EngineeringEngine()
    run(
        engine,
        "R(E, I, L) = rref([12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L])",
    )
    run(engine, "E0 := 200*GPa")
    run(engine, "I0 := 450e6*mm^4")
    run(engine, "L0 := 6000*mm")

    with pytest.raises(
        EngEvaluationError,
        match=r"matrix operation 'rref' requires a dimensionless or common-scale matrix",
    ):
        run(engine, "numeric(R(E0, I0, L0))")
