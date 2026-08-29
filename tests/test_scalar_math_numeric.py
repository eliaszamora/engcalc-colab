import math

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import NumericAssignmentResult, NumericEvaluationResult
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_sin_converts_degrees_to_radians():
    engine = EngineeringEngine()

    result = run(engine, "s := sin(30*deg)")

    assert isinstance(result, NumericAssignmentResult)
    assert result.quantity.dimensionless
    assert result.quantity.magnitude == pytest.approx(0.5)


def test_cos_accepts_pi_in_numeric_expression():
    engine = EngineeringEngine()

    result = run(engine, "c := cos(pi)")

    assert result.quantity.dimensionless
    assert result.quantity.magnitude == pytest.approx(-1.0)


def test_sqrt_propagates_engineering_units():
    engine = EngineeringEngine()

    result = run(engine, "r := sqrt(9*m^2)")

    assert result.quantity.to("m").magnitude == pytest.approx(3.0)


def test_inverse_trig_returns_radians():
    engine = EngineeringEngine()

    result = run(engine, "a := atan(1)")

    assert result.quantity.to("rad").magnitude == pytest.approx(math.pi / 4)


def test_numeric_inverse_trig_converts_to_degrees():
    engine = EngineeringEngine()

    result = run(engine, "numeric(atan(1), deg)")

    assert isinstance(result, NumericEvaluationResult)
    assert result.quantity.to("deg").magnitude == pytest.approx(45.0)


def test_exp_and_log_accept_dimensionless_values():
    engine = EngineeringEngine()

    exp_result = run(engine, "e2 := exp(2)")
    log_result = run(engine, "l2 := log(exp(2))")

    assert exp_result.quantity.dimensionless
    assert exp_result.quantity.magnitude == pytest.approx(math.exp(2))
    assert log_result.quantity.dimensionless
    assert log_result.quantity.magnitude == pytest.approx(2.0)


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("bad := log(2*m)", "log requires a dimensionless argument"),
        ("bad := exp(2*m)", "exp requires a dimensionless argument"),
        ("bad := sin(2*m)", "sin requires a dimensionless or angle argument"),
        ("bad := asin(2*m)", "asin requires a dimensionless argument"),
    ],
)
def test_scalar_math_rejects_incompatible_dimensions(source, message):
    engine = EngineeringEngine()

    with pytest.raises(EngEvaluationError, match=message):
        run(engine, source)


def test_numeric_user_function_evaluates_trig_expression_with_pi():
    engine = EngineeringEngine()
    run(engine, "f(x) = A*sin(pi*x/L)")
    run(engine, "A := 10*mm")
    run(engine, "L := 4*m")

    result = run(engine, "numeric(f(2*m), mm)")

    assert isinstance(result, NumericEvaluationResult)
    assert result.quantity.to("mm").magnitude == pytest.approx(10.0)
