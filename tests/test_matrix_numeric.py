import pytest

from engcalc_colab import models
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def require_matrix_result(result):
    result_type = getattr(models, "NumericMatrixEvaluationResult", None)
    assert result_type is not None, "NumericMatrixEvaluationResult is not implemented"
    assert isinstance(result, result_type)
    return result.quantity_matrix


def test_numeric_homogeneous_matrix_preserves_shape_units_and_magnitudes():
    engine = EngineeringEngine()
    run(engine, "k1 := 20*kN/mm")
    run(engine, "k2 := 15*kN/mm")
    run(engine, "K = [k1, -k1; -k1, k1+k2]")

    result = run(engine, "numeric(K)")
    matrix = require_matrix_result(result)

    assert (matrix.rows, matrix.cols) == (2, 2)
    assert matrix.entry(0, 0).to("kN/mm").magnitude == pytest.approx(20)
    assert matrix.entry(0, 1).to("kN/mm").magnitude == pytest.approx(-20)
    assert matrix.entry(1, 0).to("kN/mm").magnitude == pytest.approx(-20)
    assert matrix.entry(1, 1).to("kN/mm").magnitude == pytest.approx(35)
    assert result.display_name == "K"


def test_numeric_homogeneous_matrix_accepts_one_common_target_unit():
    engine = EngineeringEngine()
    run(engine, "k1 := 20*kN/mm")
    run(engine, "k2 := 15*kN/mm")
    run(engine, "K = [k1, -k1; -k1, k1+k2]")

    matrix = require_matrix_result(run(engine, "numeric(K, N/mm)"))

    assert matrix.entry(0, 0).to("N/mm").magnitude == pytest.approx(20_000)
    assert matrix.entry(0, 1).to("N/mm").magnitude == pytest.approx(-20_000)
    assert matrix.entry(1, 0).to("N/mm").magnitude == pytest.approx(-20_000)
    assert matrix.entry(1, 1).to("N/mm").magnitude == pytest.approx(35_000)


def test_numeric_heterogeneous_structural_stiffness_matrix_keeps_per_cell_units():
    engine = EngineeringEngine()
    run(engine, "E := 200*GPa")
    run(engine, "I := 450e6*mm^4")
    run(engine, "L := 6000*mm")
    run(
        engine,
        "K = [12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L]",
    )

    matrix = require_matrix_result(run(engine, "numeric(K)"))

    assert matrix.entry(0, 0).to("kN/mm").magnitude == pytest.approx(5)
    assert matrix.entry(0, 1).to("kN").magnitude == pytest.approx(15_000)
    assert matrix.entry(1, 0).to("kN").magnitude == pytest.approx(15_000)
    assert matrix.entry(1, 1).to("kN*mm").magnitude == pytest.approx(60_000_000)


def test_numeric_heterogeneous_matrix_rejects_one_global_target_unit():
    engine = EngineeringEngine()
    run(engine, "E := 200*GPa")
    run(engine, "I := 450e6*mm^4")
    run(engine, "L := 6000*mm")
    run(
        engine,
        "K = [12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L]",
    )

    with pytest.raises(
        EngEvaluationError,
        match=r"target unit|heterogeneous|matrix",
    ):
        run(engine, "numeric(K, kN/mm)")


def test_exact_zeros_are_adaptable_in_homogeneous_matrix_and_convert_with_target():
    engine = EngineeringEngine()
    run(engine, "k1 := 20*kN/mm")
    run(engine, "k2 := 15*kN/mm")
    run(engine, "A = [k1, 0; 0, k2]")

    raw = require_matrix_result(run(engine, "numeric(A)"))
    converted = require_matrix_result(run(engine, "numeric(A, N/mm)"))

    assert len(raw.adaptable_zeros) == 2
    assert converted.entry(0, 1).to("N/mm").magnitude == pytest.approx(0)
    assert converted.entry(1, 0).to("N/mm").magnitude == pytest.approx(0)


def test_exact_zero_without_unique_heterogeneous_context_stays_dimensionless():
    engine = EngineeringEngine()
    run(engine, "E := 200*GPa")
    run(engine, "I := 450e6*mm^4")
    run(engine, "L := 6000*mm")
    run(engine, "A = [E/L, 0; 0, E*I/L]")

    matrix = require_matrix_result(run(engine, "numeric(A)"))

    assert matrix.entry(0, 1).dimensionless
    assert matrix.entry(1, 0).dimensionless
    assert len(matrix.adaptable_zeros) == 2


def test_matrix_numeric_unit_error_reports_one_based_output_coordinate():
    engine = EngineeringEngine()
    run(engine, "a := 1*kN")
    run(engine, "b := 1*m")
    run(engine, "A = [1, 2; a+b, 4]")

    with pytest.raises(
        EngEvaluationError,
        match=r"matrix numeric evaluation has incompatible units at \[2,1\]",
    ):
        run(engine, "numeric(A)")


def test_numeric_matrix_valued_user_function_uses_existing_numeric_argument_binding():
    engine = EngineeringEngine()
    run(
        engine,
        "k(E, I, L) = [12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L]",
    )
    run(engine, "E0 := 200*GPa")
    run(engine, "I0 := 450e6*mm^4")
    run(engine, "L0 := 6000*mm")

    result = run(engine, "numeric(k(E0, I0, L0))")
    matrix = require_matrix_result(result)

    assert result.display_name == "k"
    assert matrix.entry(0, 0).to("kN/mm").magnitude == pytest.approx(5)
    assert matrix.entry(1, 1).to("kN*mm").magnitude == pytest.approx(60_000_000)


def test_result_command_uses_same_full_matrix_numeric_evaluation_path():
    engine = EngineeringEngine()
    run(engine, "k := 20*kN/mm")
    run(engine, "A = [k, 0; 0, k]")

    numeric_result = run(engine, "numeric(A)")
    compact_result = run(engine, "result(A)")

    numeric_matrix = require_matrix_result(numeric_result)
    compact_matrix = require_matrix_result(compact_result)
    assert compact_matrix.entries == numeric_matrix.entries
    assert compact_matrix.adaptable_zeros == numeric_matrix.adaptable_zeros
