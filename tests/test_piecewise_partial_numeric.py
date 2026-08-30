import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import PartialNumericEvaluationResult
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def define_piecewise(engine: EngineeringEngine) -> None:
    run(engine, "q(x) = piecewise(q1, x < a, q2, x <= L, 0)")
    run(engine, "q1 := 8*kN/m")
    run(engine, "q2 := 4*kN/m")
    run(engine, "a := 3*m")
    run(engine, "L := 6*m")


def test_piecewise_partial_numeric_keeps_only_interval_variable_unresolved():
    engine = EngineeringEngine()
    define_piecewise(engine)

    result = run(engine, "numeric(q(x))")

    assert isinstance(result, PartialNumericEvaluationResult)
    assert result.unresolved_symbols == ("x",)
    assert result.piecewise_evaluation is not None
    assert result.piecewise_evaluation.interval_variable == "x"


def test_piecewise_partial_numeric_carries_branch_values_breakpoints_and_default_unit():
    engine = EngineeringEngine()
    define_piecewise(engine)

    result = run(engine, "numeric(q(x))")
    piecewise = result.piecewise_evaluation

    assert piecewise is not None
    assert len(piecewise.branches) == 3

    first, second, default = piecewise.branches
    assert first.operator == "<"
    assert first.breakpoint.to("m").magnitude == pytest.approx(3.0)
    assert first.value.to("kN/m").magnitude == pytest.approx(8.0)

    assert second.operator == "<="
    assert second.breakpoint.to("m").magnitude == pytest.approx(6.0)
    assert second.value.to("kN/m").magnitude == pytest.approx(4.0)

    assert default.operator is None
    assert default.breakpoint is None
    assert default.value.to("kN/m").magnitude == pytest.approx(0.0)


def test_piecewise_partial_numeric_preserves_reversed_relation_orientation():
    engine = EngineeringEngine()
    run(engine, "q(x) = piecewise(q1, a < x, 0)")
    run(engine, "q1 := 8*kN/m")
    run(engine, "a := 3*m")

    result = run(engine, "numeric(q(x))")
    branch = result.piecewise_evaluation.branches[0]

    assert branch.operator == ">"
    assert branch.breakpoint.to("m").magnitude == pytest.approx(3.0)
    assert branch.value.to("kN/m").magnitude == pytest.approx(8.0)


def test_piecewise_partial_numeric_target_unit_requires_fully_numeric_result():
    engine = EngineeringEngine()
    define_piecewise(engine)

    with pytest.raises(
        EngEvaluationError,
        match=r"target-unit conversion requires a fully numeric result: x",
    ):
        run(engine, "numeric(q(x), N/m)")


def test_non_piecewise_partial_numeric_keeps_piecewise_payload_none():
    engine = EngineeringEngine()
    run(engine, "E := 200*GPa")
    run(engine, "A := 2000*mm^2")
    run(engine, "N(x) = E*A*x")

    result = run(engine, "numeric(N(x))")

    assert isinstance(result, PartialNumericEvaluationResult)
    assert result.piecewise_evaluation is None
