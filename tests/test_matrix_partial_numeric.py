import pytest
import sympy as sp

from engcalc_colab import models
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def require_partial_matrix_result(result):
    result_type = getattr(models, "PartialMatrixNumericEvaluationResult", None)
    assert result_type is not None, "PartialMatrixNumericEvaluationResult is not implemented"
    assert isinstance(result, result_type)
    return result


def test_partial_numeric_matrix_preserves_symbolic_matrix_known_units_and_unresolved_symbol():
    engine = EngineeringEngine()
    run(engine, "E := 200*GPa")
    run(engine, "A = [E*x, x^2; 0, E]")

    result = require_partial_matrix_result(run(engine, "numeric(A)"))

    assert result.symbolic_matrix == engine.namespace["A"]
    assert result.unresolved_symbols == ("x",)
    assert result.substitutions["E"].to("GPa").magnitude == pytest.approx(200)
    assert result.display_name == "A"


def test_partial_numeric_matrix_unresolved_symbols_are_deterministically_sorted():
    engine = EngineeringEngine()
    run(engine, "E := 200*GPa")
    run(engine, "A = [E*z + y, x; 0, E]")

    result = require_partial_matrix_result(run(engine, "numeric(A)"))

    assert result.unresolved_symbols == ("x", "y", "z")


def test_partial_numeric_matrix_target_unit_requires_fully_numeric_result():
    engine = EngineeringEngine()
    run(engine, "E := 200*GPa")
    run(engine, "A = [E*x, 0; 0, E*x]")

    with pytest.raises(
        EngEvaluationError,
        match=r"target-unit conversion requires a fully numeric result.*x",
    ):
        run(engine, "numeric(A, kN)")


def test_result_command_uses_same_partial_matrix_evaluation_path():
    engine = EngineeringEngine()
    run(engine, "E := 200*GPa")
    run(engine, "A = [E*x, x; 0, E]")

    numeric_result = require_partial_matrix_result(run(engine, "numeric(A)"))
    result_result = require_partial_matrix_result(run(engine, "result(A)"))

    assert result_result.symbolic_matrix == numeric_result.symbolic_matrix
    assert result_result.unresolved_symbols == numeric_result.unresolved_symbols
    assert result_result.substitutions["E"].to("GPa").magnitude == pytest.approx(200)


def test_partial_numeric_matrix_valued_function_uses_caller_side_unresolved_names():
    engine = EngineeringEngine()
    run(engine, "F(x, p) = [p*x, x^2; 0, p]")
    run(engine, "P := 10*kN")

    result = require_partial_matrix_result(run(engine, "numeric(F(x, P))"))

    assert result.unresolved_symbols == ("x",)
    assert result.substitutions["p"].to("kN").magnitude == pytest.approx(10)
    assert result.display_name == "F"


def test_partial_numeric_matrix_keeps_exact_symbolic_matrix_not_quantity_atoms():
    engine = EngineeringEngine()
    run(engine, "E := 200*GPa")
    run(engine, "A = [E*x, x; 0, E]")

    result = require_partial_matrix_result(run(engine, "numeric(A)"))

    assert isinstance(result.symbolic_matrix, sp.ImmutableMatrix)
    assert all(not hasattr(entry, "units") for entry in result.symbolic_matrix)
