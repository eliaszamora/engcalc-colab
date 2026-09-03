import pytest
import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import NumericEvaluationResult
from engcalc_colab.parser import parse_cell


def eval_cell(engine, source):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def test_piecewise_integral_remains_symbolic_and_is_numerically_evaluable():
    engine = EngineeringEngine()
    results = eval_cell(
        engine,
        "q(x) = piecewise(q1, x < a, q2, x <= L, 0)\n"
        "I = integrate(q(x), x, 0, L)\n"
        "q1 := 8*kN/m\nq2 := 4*kN/m\na := 3*m\nL := 6*m\n"
        "numeric(I)",
    )
    symbolic = results[1].value
    numeric = results[-1]
    assert symbolic.has(sp.Piecewise) or symbolic.has(sp.Min) or symbolic.has(sp.Max)
    assert isinstance(numeric, NumericEvaluationResult)
    assert numeric.quantity.to("kN").magnitude == pytest.approx(36.0)


def test_piecewise_derivative_evaluates_branchwise_away_from_breakpoints():
    engine = EngineeringEngine()
    results = eval_cell(
        engine,
        "q(x) = piecewise(c1*x^2, x < a, c2*x, x <= L, 0)\n"
        "dq(x) = diff(q(x), x)\n"
        "c1 := 2*kN/m^3\nc2 := 5*kN/m^2\na := 3*m\nL := 6*m\n"
        "numeric(dq(2*m))\nnumeric(dq(4*m))",
    )
    left, right = results[-2:]
    assert left.quantity.to("kN/m^2").magnitude == pytest.approx(8.0)
    assert right.quantity.to("kN/m^2").magnitude == pytest.approx(5.0)
    derivative_expression = engine.functions["dq"].expression
    assert derivative_expression.has(sp.Piecewise)
    assert not derivative_expression.has(sp.DiracDelta)


@pytest.mark.parametrize("operator", ["<", "<="])
def test_numeric_piecewise_derivative_is_undefined_at_explicit_breakpoint(operator):
    engine = EngineeringEngine()
    eval_cell(
        engine,
        f"q(x) = piecewise(c1*x^2, x {operator} a, c2*x, x <= L, 0)\n"
        "dq(x) = diff(q(x), x)\n"
        "c1 := 2*kN/m^3\nc2 := 5*kN/m^2\na := 3*m\nL := 6*m",
    )
    with pytest.raises(
        EngEvaluationError,
        match=r"derivative.*undefined.*Piecewise breakpoint.*3",
    ):
        eval_cell(engine, "numeric(dq(3*m))")


def test_ordinary_piecewise_numeric_still_owns_its_breakpoint():
    engine = EngineeringEngine()
    results = eval_cell(
        engine,
        "q(x) = piecewise(q1, x < a, q2, x <= L, 0)\n"
        "q1 := 8*kN/m\nq2 := 4*kN/m\na := 3*m\nL := 6*m\n"
        "numeric(q(3*m))",
    )
    assert results[-1].quantity.to("kN/m").magnitude == pytest.approx(4.0)
