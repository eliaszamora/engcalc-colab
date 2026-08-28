import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import NumericAssignmentResult, NumericEvaluationResult
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    item = parse_cell(source)[0]
    return engine.evaluate(item)


def test_numeric_assignment_and_named_evaluation_preserve_symbolic_formula():
    engine = EngineeringEngine()
    run(engine, "V_B = 3*q*L/8")

    q_result = run(engine, "q := 2.8*tonf/m")
    run(engine, "L := 4*m")
    result = run(engine, "numeric(V_B)")

    assert isinstance(q_result, NumericAssignmentResult)
    assert isinstance(result, NumericEvaluationResult)
    assert result.display_name == "V_B"
    assert result.quantity.to("tonf").magnitude == pytest.approx(4.2)
    assert str(engine.namespace["V_B"]) == "3*L*q/8"


def test_numeric_moment_and_reassignment_change_only_numeric_result():
    engine = EngineeringEngine()
    run(engine, "M_A = q*L^2/8")
    run(engine, "q := 2.8*tonf/m")
    run(engine, "L := 4*m")

    first = run(engine, "numeric(M_A)")
    symbolic_before = engine.namespace["M_A"]
    run(engine, "q := 3.5*tonf/m")
    second = run(engine, "numeric(M_A)")

    assert first.quantity.to("tonf*m").magnitude == pytest.approx(5.6)
    assert second.quantity.to("tonf*m").magnitude == pytest.approx(7.0)
    assert engine.namespace["M_A"] == symbolic_before


def test_numeric_accepts_direct_symbolic_expression():
    engine = EngineeringEngine()
    run(engine, "q := 2.8*tonf/m")
    run(engine, "L := 4*m")

    result = run(engine, "numeric(q*L^2/8)")

    assert isinstance(result, NumericEvaluationResult)
    assert result.display_name is None
    assert result.quantity.to("tonf*m").magnitude == pytest.approx(5.6)


def test_numeric_evaluates_user_function_with_numeric_parameter():
    engine = EngineeringEngine()
    run(engine, "V(x) = 5*q*L/8 - q*x")
    run(engine, "q := 2.8*tonf/m")
    run(engine, "L := 4*m")
    run(engine, "x := 2*m")

    result = run(engine, "numeric(V(x))")

    assert result.quantity.to("tonf").magnitude == pytest.approx(1.4)


def test_numeric_missing_values_are_line_aware():
    engine = EngineeringEngine()
    run(engine, "M_A = q*L^2/8")
    run(engine, "q := 2.8*tonf/m")

    with pytest.raises(EngEvaluationError, match=r"line 1: numeric evaluation requires values for: L"):
        run(engine, "numeric(M_A)")


def test_numeric_requires_exactly_one_argument():
    engine = EngineeringEngine()

    with pytest.raises(EngEvaluationError, match=r"line 1: numeric expects 1 argument: expression"):
        run(engine, "numeric(q, L)")


def test_reset_clears_symbolic_and_numeric_state():
    engine = EngineeringEngine()
    run(engine, "A = q*L")
    run(engine, "q := 2.8*tonf/m")

    engine.reset()

    assert engine.namespace == {}
    assert engine.functions == {}
    assert engine.symbols == {}
    assert engine.numeric_context.values == {}
