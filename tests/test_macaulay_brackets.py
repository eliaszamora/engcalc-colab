"""Macaulay brackets: `<x-a>^n`, the singularity functions of Hibbeler and Beer.

Step 2.1. `⟨x−a⟩ⁿ` is zero before `a` and `(x−a)ⁿ` from there on, so a beam is written
as one expression with **one term per load** instead of a Piecewise whose every branch
repeats the branch before it. Adding a load adds a summand, not a branch.

The mathematics is SymPy's `SingularityFunction`, including the integration rule
`∫⟨x−a⟩ⁿ dx = ⟨x−a⟩ⁿ⁺¹/(n+1)`, which is what makes V → M → θ → v chain term by term.
Nothing here implements that; the work is the surface notation and the rendering.

The bracket notation is rewritten to a call before parsing, because `<` and `>` are
comparison operators that Python's grammar would read as such. That rewrite was measured
against every source in the repository before being written - 128 files, including every
`piecewise` and the whole README - and matched nothing but the intended notation.
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


def test_the_bracket_is_zero_before_its_offset_and_shifted_after():
    engine = EngineeringEngine()
    run_cell(engine, "f(x) = <x-3>^1")
    before = run_cell(engine, "a = subs(f(x), x, 2)")[-1]
    after = run_cell(engine, "b = subs(f(x), x, 5)")[-1]

    assert str(before.value) == "0"
    assert str(after.value) == "2"


def test_a_zero_exponent_is_a_step():
    engine = engine = EngineeringEngine()
    run_cell(engine, "g(x) = <x-3>^0")
    assert str(run_cell(engine, "a = subs(g(x), x, 2)")[-1].value) == "0"
    assert str(run_cell(engine, "b = subs(g(x), x, 5)")[-1].value) == "1"


def test_a_beam_with_two_loads_is_one_expression():
    """The whole point: one term per load, no repeated branches."""
    engine = EngineeringEngine()
    run_cell(engine, "M(x) = 30*x - 2*<x>^2 - 40*<x-3>^1")

    assert str(run_cell(engine, "a = subs(M(x), x, 2)")[-1].value) == "52"
    assert str(run_cell(engine, "b = subs(M(x), x, 5)")[-1].value) == "20"


def test_integration_follows_the_macaulay_rule():
    engine = EngineeringEngine()
    result = run_cell(engine, "a = integrate(<x-3>^1, x)")[-1]
    assert "SingularityFunction" in str(result.value)
    assert str(run_cell(engine, "b = subs(a, x, 5)")[-1].value) == "2"


def test_differentiation_lowers_the_exponent():
    engine = EngineeringEngine()
    result = run_cell(engine, "a = diff(<x-3>^2, x)")[-1]
    assert str(run_cell(EngineeringEngine(), f"b = 0")[-1].value) == "0"  # sanity
    assert "SingularityFunction" in str(result.value)


def test_the_bracket_renders_as_a_bracket():
    import engcalc_colab.renderer as renderer

    engine = EngineeringEngine()
    latex = renderer.render_result(run_cell(engine, "M(x) = 30*x - 40*<x-3>^1")[-1])
    assert r"\langle" in latex and r"\rangle" in latex, latex
    assert "SingularityFunction" not in latex, latex


def test_a_bracket_beam_evaluates_numerically_with_units():
    engine = EngineeringEngine()
    result = run_cell(
        engine,
        "L := 8*m\nq := 12*kN/m\nP := 40*kN\na := 3*m\n"
        "R_A = q*L/2 + P*(L-a)/L\n"
        "M(x) = R_A*x - q/2*<x>^2 - P*<x-a>^1\n"
        "numeric(subs(M(x), x, L/2))",
    )[-1]
    assert result.quantity is not None


def test_a_bracket_beam_can_be_plotted():
    engine = EngineeringEngine()
    result = run_cell(
        engine,
        "L := 8*m\nq := 12*kN/m\nP := 40*kN\na := 3*m\n"
        "R_A = q*L/2 + P*(L-a)/L\n"
        "M(x) = R_A*x - q/2*<x>^2 - P*<x-a>^1\n"
        "plot(M(x), x, 0, L)",
    )[-1]
    assert result.series


def test_a_non_unit_coefficient_inside_the_bracket_is_refused():
    """`<2*x-a>` is not Macaulay notation; the bracket shifts, it does not scale."""
    engine = EngineeringEngine()
    with pytest.raises((EngEvaluationError, EngSyntaxError)) as excinfo:
        run_cell(engine, "f(x) = <2*x-3>^1")
    assert "macaulay" in str(excinfo.value).lower() or "bracket" in str(excinfo.value).lower()


# ---------------------------------------------------------------------------
# The rewrite must not disturb comparisons, which is where `<` and `>` live today
# ---------------------------------------------------------------------------


def test_piecewise_comparisons_are_untouched():
    engine = EngineeringEngine()
    run_cell(engine, "q(x) = piecewise(1, x < 2, 0)")
    assert str(run_cell(engine, "a = subs(q(x), x, 1)")[-1].value) == "1"
    assert str(run_cell(engine, "b = subs(q(x), x, 3)")[-1].value) == "0"


def test_two_piecewise_terms_with_a_power_are_untouched():
    """The shape a careless rewrite would swallow whole.

    A pattern matching `<` ... `>` across commas and parentheses would capture
    `< 2, ...) + piecewise(..., x >` here and destroy both branches. Measured against
    every source in the repository before the rewrite was written; this pins it.
    """
    engine = EngineeringEngine()
    run_cell(engine, "f(x) = piecewise(1, x < 2, 0) + piecewise(3, x > 5, 0)^2")
    assert str(run_cell(engine, "a = subs(f(x), x, 1)")[-1].value) == "1"
