r"""A name is a value or a function, never both.

Found by a coverage-and-mutation hunt over the engine and the parser, which asked a
different question from the usual one: not "is this new change held up" but "which guards
does the suite never even reach". Sixty-four `raise` statements in `engine.py` and
`parser.py` had never been executed, and typing the mistakes each was written for turned
up this one.

`redefinition conflict` fires when a *symbolic* scalar is redefined as a function:

    a = 2*x        then  a(x) = x     ->  "'a' is already a scalar"

It never fires for a *numeric* one, in either direction, because it checks
`self.namespace` and `a := 2*m` stores in `numeric_context.values`:

    a := 2*m       then  a(x) = x     ->  silence
    a(x) = x       then  a := 2*m     ->  silence

What the sheet then shows is a name meaning two things at once:

    a     = 2.00 m
    a(x)  = x^2
    a     = a = (2.00 m) = 2.00 m
    b     = a(3) = 9.00

Redefining a name as the *same* kind is not this and stays allowed: `a := 2*m` followed
by `a := 3*m` is an engineer correcting a value, which is what a sheet is for.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def run(engine, source):
    for statement in parse_cell(source):
        engine.evaluate(statement)


# --- the hole ------------------------------------------------------------------------

def test_a_numeric_scalar_cannot_become_a_function():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError, match="already a scalar"):
        run(engine, "a := 2*m\na(x) = x\n")


def test_a_function_cannot_become_a_numeric_scalar():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError, match="already a function"):
        run(engine, "a(x) = x\na := 2*m\n")


# --- what was already guarded and must stay ------------------------------------------

def test_a_symbolic_scalar_cannot_become_a_function():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError, match="already a scalar"):
        run(engine, "a = 2*x\na(x) = x\n")


def test_a_function_cannot_become_a_symbolic_scalar():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError, match="already a function"):
        run(engine, "a(x) = x\na = 2*x\n")


# --- correcting a value is not redefining a name --------------------------------------

def test_a_numeric_value_can_be_corrected():
    engine = EngineeringEngine()
    run(engine, "a := 2*m\na := 3*m\n")
    assert engine.numeric_context.get("a").magnitude == pytest.approx(3.0)


def test_a_symbolic_value_can_be_corrected():
    engine = EngineeringEngine()
    run(engine, "a = 2*x\na = 3*x\n")


def test_a_function_can_be_corrected():
    engine = EngineeringEngine()
    run(engine, "a(x) = x\na(x) = x**2\n")


def test_a_reset_clears_the_conflict():
    engine = EngineeringEngine()
    run(engine, "a := 2*m\n")
    engine.reset()
    run(engine, "a(x) = x\n")
