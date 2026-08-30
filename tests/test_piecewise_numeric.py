import pytest
import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import NumericEvaluationResult
from engcalc_colab.numeric import NumericContext
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    statement = parse_cell(source)[0]
    return engine.evaluate(statement)


def define_standard_piecewise(engine: EngineeringEngine) -> None:
    run(engine, "q(x) = piecewise(q1, x < a, q2, x <= L, 0)")
    run(engine, "q1 := 8*kN/m")
    run(engine, "q2 := 4*kN/m")
    run(engine, "a := 300*cm")
    run(engine, "L := 6*m")


def test_piecewise_numeric_compares_compatible_length_units_and_preserves_endpoints():
    engine = EngineeringEngine()
    define_standard_piecewise(engine)

    left = run(engine, "numeric(q(2*m))")
    at_breakpoint = run(engine, "numeric(q(3*m))")
    middle = run(engine, "numeric(q(5*m))")

    assert isinstance(left, NumericEvaluationResult)
    assert left.quantity.to("kN/m").magnitude == pytest.approx(8.0)
    assert at_breakpoint.quantity.to("kN/m").magnitude == pytest.approx(4.0)
    assert middle.quantity.to("kN/m").magnitude == pytest.approx(4.0)


def test_piecewise_numeric_allows_dimensional_quantity_compared_with_exact_zero():
    engine = EngineeringEngine()
    run(engine, "f(x) = piecewise(1, x >= 0, 0)")

    positive = run(engine, "numeric(f(2*m))")
    zero = run(engine, "numeric(f(0*m))")

    assert positive.quantity.dimensionless
    assert positive.quantity.magnitude == pytest.approx(1.0)
    assert zero.quantity.dimensionless
    assert zero.quantity.magnitude == pytest.approx(1.0)


def test_piecewise_numeric_rejects_dimensionally_incompatible_comparison():
    engine = EngineeringEngine()
    run(engine, "f(x) = piecewise(1, x < a, 0)")
    run(engine, "a := 3*kN")

    with pytest.raises(EngEvaluationError, match=r"line 1: .*incompatible units"):
        run(engine, "numeric(f(2*m))")


def test_piecewise_numeric_rejects_nonzero_dimensionless_vs_dimensional_comparison():
    engine = EngineeringEngine()
    run(engine, "f(x) = piecewise(1, x < a, 0)")
    run(engine, "a := 3")

    with pytest.raises(EngEvaluationError, match=r"line 1: .*nonzero dimensionless"):
        run(engine, "numeric(f(2*m))")


def test_piecewise_numeric_selects_default_and_inherits_dimensional_response_unit():
    engine = EngineeringEngine()
    define_standard_piecewise(engine)

    result = run(engine, "numeric(q(8*m))")

    assert result.quantity.to("kN/m").magnitude == pytest.approx(0.0)


def test_piecewise_numeric_target_unit_conversion_uses_normal_numeric_contract():
    engine = EngineeringEngine()
    define_standard_piecewise(engine)

    result = run(engine, "numeric(q(2*m), N/m)")

    assert result.quantity.to("N/m").magnitude == pytest.approx(8000.0)


def test_piecewise_numeric_accepts_compatible_branch_units():
    engine = EngineeringEngine()
    run(engine, "q(x) = piecewise(q1, x < a, q2, x <= L, 0)")
    run(engine, "q1 := 8*kN/m")
    run(engine, "q2 := 4000*N/m")
    run(engine, "a := 3*m")
    run(engine, "L := 6*m")

    first = run(engine, "numeric(q(2*m))")
    second = run(engine, "numeric(q(5*m))")
    default = run(engine, "numeric(q(8*m))")

    assert first.quantity.to("kN/m").magnitude == pytest.approx(8.0)
    assert second.quantity.to("kN/m").magnitude == pytest.approx(4.0)
    assert default.quantity.to("kN/m").magnitude == pytest.approx(0.0)


def test_piecewise_leading_exact_zero_inherits_unit_from_resolvable_branch():
    engine = EngineeringEngine()
    run(engine, "q(x) = piecewise(0, x < a, q2, x <= L, 0)")
    run(engine, "q2 := 4*kN/m")
    run(engine, "a := 3*m")
    run(engine, "L := 6*m")

    result = run(engine, "numeric(q(2*m))")

    assert result.quantity.to("kN/m").magnitude == pytest.approx(0.0)


def test_piecewise_zero_unit_inference_rejects_incompatible_resolvable_branches():
    engine = EngineeringEngine()
    run(engine, "q(x) = piecewise(q1, x < a, q2, x <= L, 0)")
    run(engine, "q1 := 8*kN")
    run(engine, "q2 := 4*m")
    run(engine, "a := 3*m")
    run(engine, "L := 6*m")

    with pytest.raises(EngEvaluationError, match=r"line 1: .*incompatible.*branch units"):
        run(engine, "numeric(q(8*m))")


def test_piecewise_zero_unit_inference_rejects_nonzero_dimensionless_branch_mixture():
    engine = EngineeringEngine()
    run(engine, "q(x) = piecewise(q1, x < a, c, x <= L, 0)")
    run(engine, "q1 := 8*kN")
    run(engine, "c := 3")
    run(engine, "a := 3*m")
    run(engine, "L := 6*m")

    with pytest.raises(EngEvaluationError, match=r"line 1: .*nonzero dimensionless.*branch"):
        run(engine, "numeric(q(8*m))")


def test_piecewise_numeric_supports_restricted_min_max_with_compatible_units():
    context = NumericContext()
    q1, q2 = sp.symbols("q1 q2")
    context.values["q1"] = 8 * context.ureg.kN / context.ureg.m
    context.values["q2"] = 4000 * context.ureg.N / context.ureg.m

    _, minimum = context.evaluate_symbolic(sp.Min(q1, q2, evaluate=False))
    _, maximum = context.evaluate_symbolic(sp.Max(q1, q2, evaluate=False))

    assert minimum.to("kN/m").magnitude == pytest.approx(4.0)
    assert maximum.to("kN/m").magnitude == pytest.approx(8.0)


def test_piecewise_numeric_min_max_normalize_exact_zero_to_dimensional_unit():
    context = NumericContext()
    q = sp.Symbol("q")
    context.values["q"] = 4 * context.ureg.kN / context.ureg.m

    _, minimum = context.evaluate_symbolic(sp.Min(q, sp.Integer(0), evaluate=False))
    _, maximum = context.evaluate_symbolic(sp.Max(q, sp.Integer(0), evaluate=False))

    assert minimum.to("kN/m").magnitude == pytest.approx(0.0)
    assert maximum.to("kN/m").magnitude == pytest.approx(4.0)
