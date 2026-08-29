import pytest

import engcalc_colab.errors as errors
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_diagnostic_hint_exposes_stable_numeric_bridge_codes():
    assert hasattr(errors, "diagnostic_hint")

    direct = errors.diagnostic_hint("direct_numeric_argument", example="M(2.5*m)")
    unknown = errors.diagnostic_hint("unknown_numeric_name", name="q_missing")
    incompatible = errors.diagnostic_hint("incompatible_function_units", function="f")
    unresolved = errors.diagnostic_hint("unresolved_numeric_symbols", names=("L",))

    assert "numeric(M(2.5*m))" in direct
    assert "q_missing :=" in unknown
    assert "f" in incompatible
    assert "L" in unresolved


def test_unknown_numeric_name_error_names_value_and_gives_assignment_hint():
    engine = EngineeringEngine()

    with pytest.raises(
        EngEvaluationError,
        match=r"unknown numeric name 'q_missing'.*q_missing :=",
    ):
        run(engine, "q := q_missing*kN/m")


def test_numeric_function_dimension_error_names_function_and_expected_fix():
    engine = EngineeringEngine()
    run(engine, "f(x) = L + x")
    run(engine, "L := 1*m")

    with pytest.raises(
        EngEvaluationError,
        match=r"incompatible units while evaluating numeric function 'f'.*compatible units",
    ):
        run(engine, "numeric(f(2*kN))")


def test_unresolved_numeric_symbols_error_names_values_and_gives_hint():
    engine = EngineeringEngine()
    run(engine, "A = q*L")
    run(engine, "q := 2*kN/m")

    with pytest.raises(
        EngEvaluationError,
        match=r"numeric evaluation requires values for: L.*L :=",
    ):
        run(engine, "numeric(A)")
