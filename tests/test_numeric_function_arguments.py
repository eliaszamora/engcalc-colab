import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import NumericEvaluationResult, PartialNumericEvaluationResult
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_numeric_function_accepts_direct_unit_expression():
    engine = EngineeringEngine()
    run(engine, "M(x) = q*x*(L-x)/2")
    run(engine, "q := 10*kN/m")
    run(engine, "L := 6*m")

    result = run(engine, "numeric(M(2.5*m))")

    assert isinstance(result, NumericEvaluationResult)
    assert result.quantity.to("kN*m").magnitude == pytest.approx(43.75)


def test_numeric_function_accepts_expression_using_known_numeric_length():
    engine = EngineeringEngine()
    run(engine, "V(x) = q*(L-x)")
    run(engine, "q := 10*kN/m")
    run(engine, "L := 6*m")

    result = run(engine, "numeric(V(L/2))")

    assert isinstance(result, NumericEvaluationResult)
    assert result.quantity.to("kN").magnitude == pytest.approx(30.0)


def test_numeric_parameter_function_accepts_direct_load_quantity():
    engine = EngineeringEngine()
    run(engine, "R(q) = 5*q*L/8")
    run(engine, "L := 4*m")

    result = run(engine, "numeric(R(4*tonf/m))")

    assert isinstance(result, NumericEvaluationResult)
    assert result.quantity.to("tonf").magnitude == pytest.approx(10.0)


def test_numeric_function_keeps_lone_unassigned_name_as_partial_symbol():
    engine = EngineeringEngine()
    run(engine, "M(x) = q*x*(L-x)/2")
    run(engine, "q := 10*kN/m")
    run(engine, "L := 6*m")

    result = run(engine, "numeric(M(x))")

    assert isinstance(result, PartialNumericEvaluationResult)
    assert result.unresolved_symbols == ("x",)
