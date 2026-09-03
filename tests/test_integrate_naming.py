"""`integrate` is the name; `integral` was retired.

The operation has not changed. In 0.11.0 it became reachable under the name every
mathematical Python user already knows, on the principle of not inventing names for
operations that have recognised ones - `diff` is left alone for exactly that reason.

`integral` was then kept as a permanent alias, for memorias written under the old name.
There turned out to be none: EngCalc had never been run in a notebook by anyone. So the
reason for carrying a second name for one operation was void, and the alias is retired
rather than carried forever.

What survives is the message. The old name is still in this repository's design history
and in the version notes, so someone can read it and type it; being told `integral` is
unknown would be true and useless. It names the replacement instead.
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


def test_integrate_computes_the_definite_integral():
    result = evaluate(EngineeringEngine(), "a = integrate(x^2, x, 0, 1)")
    assert str(result.value) == "1/3"


def test_integrate_works_on_matrices():
    result = evaluate(EngineeringEngine(), "A = integrate([x, x^2; x^3, 1], x, 0, 1)")
    assert result.value is not None


def test_a_flexibility_integral_still_reaches_a_number():
    """The worked example the alias was kept for, written under the canonical name."""
    engine = EngineeringEngine()
    result = evaluate(
        engine,
        "L := 6*m\nE := 200*GPa\nI_z := 120e6*mm**4\n"
        "M_1(x) = x\nf = integrate(M_1(x)^2/(E*I_z), x, 0, L)\nnumeric(f)",
    )
    assert result.quantity is not None


def test_the_retired_name_says_what_to_write_instead():
    """"unsupported function 'integral'" would be true and no help at all.

    The old name is in the design documents and in the 0.11.0 version note, so it is
    readable and typeable by someone who never saw this change.
    """
    with pytest.raises(EngSyntaxError) as excinfo:
        evaluate(EngineeringEngine(), "a = integral(x^2, x, 0, 1)")
    message = str(excinfo.value)

    assert "'integral' was renamed to 'integrate'" in message
    assert "write integrate(...) instead" in message


def test_the_retired_name_is_refused_wherever_it_appears():
    """Not only as an assignment: a standalone call and a nested one too.

    A retirement enforced in one position and not another is worse than none, because
    the sheet works until the line moves.
    """
    for source in (
        "integral(x^2, x, 0, 1)",
        "f(x) = 2*integral(x, x, 0, 1)",
        "A = [integral(x, x, 0, 1), 0; 0, 1]",
    ):
        with pytest.raises(EngSyntaxError) as excinfo:
            evaluate(EngineeringEngine(), source)
        assert "renamed" in str(excinfo.value), source


def test_the_name_is_free_for_an_engineer_to_use():
    """Retiring it hands the name back.

    `integral` is no longer reserved, so a sheet may call a quantity by that name. That
    is the compensation for the retirement and it is worth pinning: leaving the name
    reserved but broken would take something away without giving anything back.
    """
    engine = EngineeringEngine()
    result = evaluate(engine, "integral := 5*kN*m\nnumeric(integral)")
    assert result.quantity.to("kN*m").magnitude == pytest.approx(5.0)


def test_the_error_names_the_function_that_was_called():
    """A message naming a function the engineer did not type is its own small defect."""
    # Two arguments is the indefinite integral since 0.13.0, so the example that
    # exercises the arity message is three: a bound was forgotten.
    with pytest.raises(EngEvaluationError) as excinfo:
        evaluate(EngineeringEngine(), "a = integrate(x^2, x, 0)")
    assert "integrate expects" in str(excinfo.value)


def test_integrate_is_reserved_like_every_other_operation():
    with pytest.raises(EngSyntaxError):
        evaluate(EngineeringEngine(), "integrate := 3")
