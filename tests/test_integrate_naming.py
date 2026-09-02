"""`integrate` is the canonical name; `integral` remains a permanent alias.

The operation already existed and is unchanged. What changes is that it is reachable
under the name every mathematical Python user already knows, on the principle of not
inventing names for operations that have recognised ones. `diff` is left alone for the
same reason - it is already the recognised name.

`integral` is kept working rather than deprecated, because it appears in existing
memorias and in the documented worked examples.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError, EngSyntaxError
from engcalc_colab.parser import parse_cell


def evaluate(engine: EngineeringEngine, source: str):
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


def test_integrate_is_accepted_and_agrees_with_integral():
    canonical = evaluate(EngineeringEngine(), "a = integrate(x^2, x, 0, 1)")
    alias = evaluate(EngineeringEngine(), "a = integral(x^2, x, 0, 1)")

    assert canonical.value == alias.value
    assert str(canonical.value) == "1/3"


def test_integral_still_works_as_a_permanent_alias():
    """Existing memorias and the documented worked examples use `integral`."""
    engine = EngineeringEngine()
    result = evaluate(
        engine,
        "L := 6*m\nE := 200*GPa\nI_z := 120e6*mm**4\n"
        "M_1(x) = x\nf = integral(M_1(x)^2/(E*I_z), x, 0, L)\nnumeric(f)",
    )
    assert result.quantity is not None


def test_integrate_works_on_matrices_like_integral():
    engine = EngineeringEngine()
    canonical = evaluate(engine, "A = integrate([x, x^2; x^3, 1], x, 0, 1)")
    alias = evaluate(EngineeringEngine(), "A = integral([x, x^2; x^3, 1], x, 0, 1)")
    assert canonical.value == alias.value


def test_the_error_names_the_function_that_was_called():
    """A message naming a function the engineer did not type is its own small defect."""
    # Two arguments is the indefinite integral since 0.13.0, so the example that
    # exercises the arity message is three: a bound was forgotten.
    with pytest.raises(EngEvaluationError) as excinfo:
        evaluate(EngineeringEngine(), "a = integrate(x^2, x, 0)")
    assert "integrate expects" in str(excinfo.value)

    with pytest.raises(EngEvaluationError) as excinfo:
        evaluate(EngineeringEngine(), "a = integral(x^2, x, 0)")
    assert "integral expects" in str(excinfo.value)


def test_integrate_is_reserved_like_every_other_operation():
    with pytest.raises(EngSyntaxError):
        evaluate(EngineeringEngine(), "integrate := 3")
