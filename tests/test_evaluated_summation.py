"""`numeric(...)` evaluates a symbolic summation.

Step 3.1. `sum(expr, i, lower, upper)` already builds the right thing and already renders
as a real sigma - `S = \sum_{i=1}^{n} i P` - which is what a memoria should show. The only
missing piece was that `numeric(...)` could not turn it into a number.

**No second function is added.** A `summation()` alongside `sum()` would invent a second
name for one operation and break the pattern the whole language runs on: the symbolic
layer keeps the formula and `numeric(...)` produces the value. `M(x) = q*x*(L-x)/2` stays
symbolic and `numeric(M(x))` gives the number; a sum behaves the same way.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def test_a_summation_of_loads_evaluates_with_units():
    """E17 of the gap map: five loads of 10 kN, growing linearly."""
    engine = EngineeringEngine()
    result = run_cell(
        engine, "n := 5\nP := 10*kN\nS = sum(P*i, i, 1, n)\nnumeric(S)"
    )[-1]
    # 10 kN * (1+2+3+4+5)
    assert float(result.quantity.to("kN").magnitude) == pytest.approx(150.0)


def test_the_symbolic_form_is_still_a_sigma():
    """What the reader sees does not change; only what numeric can do with it."""
    import engcalc_colab.renderer as renderer

    engine = EngineeringEngine()
    results = run_cell(engine, "n := 5\nP := 10*kN\nS = sum(P*i, i, 1, n)")
    latex = renderer.render_result(results[-1])
    assert r"\sum" in latex, latex


def test_a_dimensionless_summation():
    engine = EngineeringEngine()
    result = run_cell(engine, "n := 4\nS = sum(i^2, i, 1, n)\nnumeric(S)")[-1]
    assert float(result.quantity.magnitude) == pytest.approx(30.0)  # 1+4+9+16


def test_the_index_does_not_leak_into_the_body():
    """`i` is bound by the sum, not a value from the sheet."""
    engine = EngineeringEngine()
    result = run_cell(engine, "i := 99*m\nS = sum(i, i, 1, 3)\nnumeric(S)")[-1]
    assert float(result.quantity.magnitude) == pytest.approx(6.0)


def test_bounds_must_be_dimensionless():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "L := 3*m\nS = sum(i, i, 1, L)\nnumeric(S)")
    assert "dimensionless" in str(excinfo.value).lower()


def test_a_genuinely_empty_range_is_zero():
    engine = EngineeringEngine()
    result = run_cell(engine, "S = sum(i, i, 1, 0)\nnumeric(S)")[-1]
    assert float(result.quantity.magnitude) == pytest.approx(0.0)


def test_reversed_bounds_agree_with_sympy_on_both_paths():
    """The two paths must not disagree about the same construct.

    A summation without units is evaluated by SymPy itself, further up the evaluator;
    one carrying units goes term by term through EngCalc's own branch. Only the units
    decide which path is taken, so the answer must not.

    SymPy's convention for reversed bounds is the negative of the sum between them, so
    `sum(i, i, 3, 1)` is -2. The first draft of the EngCalc branch returned 0, which
    would have made the same expression give two different answers depending on whether
    a kilonewton appeared in it.
    """
    plain = run_cell(EngineeringEngine(), "S = sum(i, i, 3, 1)\nnumeric(S)")[-1]
    assert float(plain.quantity.magnitude) == pytest.approx(-2.0)

    with_units = run_cell(
        EngineeringEngine(), "P := 10*kN\nS = sum(P*i, i, 3, 1)\nnumeric(S)"
    )[-1]
    assert float(with_units.quantity.to("kN").magnitude) == pytest.approx(-20.0)


def test_an_absurd_range_carrying_units_is_refused_rather_than_hanging():
    """A notebook that stops responding is worse than one that says no.

    Only the unit-carrying path needs this guard: without units SymPy finds a closed
    form and answers a ten-million-term sum in under a second. With units the sum is
    built term by term, and a mistyped limit would lock up a Colab session.
    """
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "P := 10*kN\nS = sum(P*i, i, 1, 10000000)\nnumeric(S)")
    assert "terms" in str(excinfo.value).lower()
