"""`assume(L > 0, E > 0)` — what the engineer already knows, told to the engine.

Step 3.3. On paper you know a length is positive and write `sqrt(L^2) = L` without
thinking. SymPy needs to be told, and the difference is real: with `L` merely real,
`sqrt(L^2)` simplifies to `Abs(L)`; with `L` positive it simplifies to `L`.

**Assumptions must come before the symbol is used, and that is enforced.** A SymPy symbol
carries its assumptions in its identity - `Symbol('L', real=True)` and
`Symbol('L', positive=True)` are *different symbols* - so an assumption declared after
`L` already appears in an expression would apply to a symbol nothing references, and do
nothing at all. Silently. Refusing it is the only honest option.

Comparisons stay where they already were: allowed in specific call positions, as
`piecewise(...)` has always allowed them, rather than becoming general expressions. This
step does not deliver "first-class comparisons"; it delivers `assume`.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError, EngSyntaxError
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def test_a_positive_length_simplifies_its_own_square_root():
    """E16 of the gap map."""
    engine = EngineeringEngine()
    run_cell(engine, "assume(L > 0)")
    result = run_cell(engine, "a = simplify(sqrt(L^2))")[-1]
    assert str(result.value) == "L"


def test_without_the_assumption_it_stays_an_absolute_value():
    """The contrast, so the feature is shown to be doing the work."""
    result = run_cell(EngineeringEngine(), "a = simplify(sqrt(L^2))")[-1]
    assert str(result.value) == "Abs(L)"


def test_several_assumptions_in_one_call():
    engine = EngineeringEngine()
    run_cell(engine, "assume(L > 0, E > 0, I_z > 0)")
    result = run_cell(engine, "a = simplify(sqrt(L^2*E^2))")[-1]
    assert str(result.value) == "E*L"


def test_the_four_comparisons_against_zero():
    engine = EngineeringEngine()
    run_cell(engine, "assume(a > 0, b >= 0, c < 0, d <= 0)")
    assert engine.resolve_symbol("a").is_positive is True
    assert engine.resolve_symbol("b").is_nonnegative is True
    assert engine.resolve_symbol("c").is_negative is True
    assert engine.resolve_symbol("d").is_nonpositive is True


def test_an_assumption_after_first_use_is_refused():
    """Otherwise it would apply to a symbol nothing references, and do nothing.

    This is the whole reason the rule exists: SymPy symbols carry their assumptions in
    their identity, so a late assumption is not a weak assumption - it is no assumption,
    with no sign that anything went wrong.
    """
    engine = EngineeringEngine()
    run_cell(engine, "f(x) = L*x")
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "assume(L > 0)")
    message = str(excinfo.value)
    assert "already" in message.lower()
    assert "L" in message


def test_a_comparison_against_something_other_than_zero_is_refused():
    """`L > 5` is not a symbol assumption and pretending otherwise would mislead."""
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "assume(L > 5)")
    assert "zero" in str(excinfo.value).lower()


def test_the_subject_must_be_a_plain_symbol():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError):
        run_cell(engine, "assume(L*2 > 0)")


def test_comparisons_are_still_refused_outside_the_places_that_take_them():
    """This step does not make comparisons general expressions."""
    with pytest.raises(EngSyntaxError):
        run_cell(EngineeringEngine(), "a = L > 0")


def test_piecewise_comparisons_are_untouched():
    engine = EngineeringEngine()
    run_cell(engine, "q(x) = piecewise(1, x < 2, 0)")
    assert str(run_cell(engine, "a = subs(q(x), x, 1)")[-1].value) == "1"
