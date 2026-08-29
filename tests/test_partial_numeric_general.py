import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import PartialNumericEvaluationResult
from engcalc_colab.parser import parse_cell


def run(engine, source):
    return engine.evaluate(parse_cell(source)[0])


def test_known_arguments_are_substituted_and_x_remains():
    engine = EngineeringEngine()
    run(engine, "M(x, q, L) = q*x*(L-x)/2")
    run(engine, "qD := 10*kN/m")
    run(engine, "L := 4*m")
    result = run(engine, "numeric(M(x, qD, L))")
    assert isinstance(result, PartialNumericEvaluationResult)
    assert result.unresolved_symbols == ("x",)
    assert result.substitutions["q"].to("kN/m").magnitude == 10
    assert result.substitutions["L"].to("m").magnitude == 4


def test_multiple_unresolved_symbols_are_allowed():
    engine = EngineeringEngine()
    run(engine, "M(x, q, L) = q*x*(L-x)/2")
    run(engine, "L := 4*m")
    result = run(engine, "numeric(M(x, q, L))")
    assert result.unresolved_symbols == ("q", "x")


def test_caller_side_unresolved_name_replaces_local_parameter_name():
    engine = EngineeringEngine()
    run(engine, "f(x, p) = p*x")
    result = run(engine, "numeric(f(x, q))")
    assert result.unresolved_symbols == ("q", "x")


def test_known_context_symbol_inside_body_is_also_substituted():
    engine = EngineeringEngine()
    run(engine, "M(x, q) = q*x*(L-x)/2")
    run(engine, "qD := 10*kN/m")
    run(engine, "L := 4*m")
    result = run(engine, "numeric(M(x, qD))")
    assert result.unresolved_symbols == ("x",)
    assert result.substitutions["q"].to("kN/m").magnitude == 10
    assert result.substitutions["L"].to("m").magnitude == 4


def test_nonpolynomial_partial_is_valid_without_evaluated_terms():
    engine = EngineeringEngine()
    run(engine, "v(x, A, L) = A*sin(pi*x/L)")
    run(engine, "A := 20*mm")
    run(engine, "L := 4*m")
    result = run(engine, "numeric(v(x, A, L))")
    assert isinstance(result, PartialNumericEvaluationResult)
    assert result.unresolved_symbols == ("x",)
    assert result.evaluated_terms is None
    assert result.substitutions["A"].to("mm").magnitude == 20
    assert result.substitutions["L"].to("m").magnitude == 4


def test_target_unit_is_rejected_for_partial_result():
    engine = EngineeringEngine()
    run(engine, "M(x, q, L) = q*x*(L-x)/2")
    run(engine, "qD := 10*kN/m")
    run(engine, "L := 4*m")
    with pytest.raises(
        EngEvaluationError,
        match="target-unit conversion requires a fully numeric result",
    ):
        run(engine, "numeric(M(x, qD, L), kN*m)")
