import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import NumericEvaluationResult
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_numeric_direct_multiarg_quantities():
    engine = EngineeringEngine()
    run(engine, "M(x, q, L) = q*x*(L-x)/2")

    result = run(engine, "numeric(M(2*m, 10*kN/m, 4*m), kN*m)")

    assert isinstance(result, NumericEvaluationResult)
    assert result.quantity.to("kN*m").magnitude == pytest.approx(20.0)
    assert result.display_arguments is not None
    assert len(result.display_arguments) == 3
    assert result.display_argument is None


def test_numeric_context_values_bind_to_local_parameters():
    engine = EngineeringEngine()
    run(engine, "M(x, q, L) = q*x*(L-x)/2")
    run(engine, "qD := 10*kN/m")
    run(engine, "L := 4*m")

    result = run(engine, "numeric(M(2*m, qD, L), kN*m)")

    assert result.quantity.to("kN*m").magnitude == pytest.approx(20.0)


def test_numeric_expression_argument_binds_to_local_parameter():
    engine = EngineeringEngine()
    run(engine, "M(x, q, L) = q*x*(L-x)/2")
    run(engine, "qD := 4*kN/m")
    run(engine, "qL := 2*kN/m")
    run(engine, "L := 5*m")

    result = run(
        engine,
        "numeric(M(2*m, 1.2*qD + 1.6*qL, L), kN*m)",
    )

    assert result.quantity.to("kN*m").magnitude == pytest.approx(24.0)


def test_local_parameter_shadows_same_named_numeric_context_value():
    engine = EngineeringEngine()
    run(engine, "L := 5*m")
    run(engine, "f(L) = 2*L")

    result = run(engine, "numeric(f(3*m), m)")

    assert result.quantity.to("m").magnitude == pytest.approx(6.0)


def test_dimensional_zero_is_preserved_in_multiarg_call():
    engine = EngineeringEngine()
    run(engine, "f(x, q, L) = q*(L-x)")

    result = run(engine, "numeric(f(0*m, 4*kN/m, 5*m), kN)")

    assert result.quantity.to("kN").magnitude == pytest.approx(20.0)


def test_nested_user_function_argument_can_be_fully_numeric():
    engine = EngineeringEngine()
    run(engine, "qU(qD, qL) = 1.2*qD + 1.6*qL")
    run(engine, "M(x, q, L) = q*x*(L-x)/2")
    run(engine, "qD := 4*kN/m")
    run(engine, "qL := 2*kN/m")
    run(engine, "L := 5*m")

    result = run(engine, "numeric(M(2*m, qU(qD, qL), L), kN*m)")

    assert result.quantity.to("kN*m").magnitude == pytest.approx(24.0)


def test_unused_unresolved_parameter_does_not_force_partial_numeric_result():
    engine = EngineeringEngine()
    run(engine, "f(x, y) = x")

    result = run(engine, "numeric(f(2*m, y))")

    assert isinstance(result, NumericEvaluationResult)
    assert result.quantity.to("m").magnitude == pytest.approx(2.0)


def test_unused_unresolved_parameter_allows_target_unit_conversion():
    engine = EngineeringEngine()
    run(engine, "f(x, y) = x")

    result = run(engine, "numeric(f(2*m, y), cm)")

    assert isinstance(result, NumericEvaluationResult)
    assert result.quantity.to("cm").magnitude == pytest.approx(200.0)
