"""`numeric(...)` resolves names the symbolic namespace defines.

The gap step 1.2 uncovered. A definition captures its free symbols, so `v(x)` written
before its integration constants are known keeps `C1` and `C2` in it. Until now
`numeric(...)` looked only at the numeric context - the values given with `:=` - so the
elastic curve could be derived symbolically and never reach a number.

The measurement that authorised this is worth recording, because the first attempt at it
was worthless. A probe placed in a fallback path passed all 1166 tests and appeared to
show zero blast radius; it had simply never run. Only after a probe was checked to
actually fix the failing case - and only then - did the same 1166-test result mean
anything.
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


def test_a_name_defined_after_the_expression_is_resolved():
    engine = EngineeringEngine()
    result = run_cell(
        engine, "v(x) = x + C1\nC1 = 5\nnumeric(subs(v(x), x, 2))"
    )[-1]
    assert float(result.quantity.magnitude) == pytest.approx(7.0)


def test_a_chain_of_definitions_is_followed():
    engine = EngineeringEngine()
    result = run_cell(engine, "a = b\nb = c\nc = 2\nnumeric(a)")[-1]
    assert float(result.quantity.magnitude) == pytest.approx(2.0)


def test_the_elastic_curve_reaches_a_number():
    """The exercise this exists for, checked against the closed form.

    Integrate the shear twice, write the constants as an engineer does, let the boundary
    conditions determine them, and evaluate. The midspan deflection must be
    -5qL⁴/(384 E I).
    """
    engine = EngineeringEngine()
    result = run_cell(
        engine,
        "L := 6*m\nq := 10*kN/m\nE := 200*GPa\nI_z := 80e6*mm**4\n"
        "R_A = q*L/2\n"
        "V(x) = R_A - q*x\n"
        "M(x) = integrate(V(x), x, 0, x)\n"
        "theta(x) = integrate(M(x)/(E*I_z), x) + C1\n"
        "v(x) = integrate(theta(x), x) + C2\n"
        "solve(eq(subs(v(x), x, 0), 0), eq(subs(v(x), x, L), 0), C1, C2)\n"
        "numeric(subs(v(x), x, L/2))",
    )[-1]

    closed_form = -5 * 10 * 6**4 / (384 * 200e6 * 80e-6) * 1000
    assert float(result.quantity.to("mm").magnitude) == pytest.approx(closed_form, rel=1e-9)


def test_the_numeric_context_still_works_as_before():
    """Values given with `:=` were always resolved and still are."""
    engine = EngineeringEngine()
    result = run_cell(engine, "y = 2*k\nk := 5*kN\nnumeric(y)")[-1]
    assert float(result.quantity.to("kN").magnitude) == pytest.approx(10.0)


def test_a_name_with_no_value_anywhere_still_says_so():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "y = 2*w\nnumeric(y)")
    assert "requires values for" in str(excinfo.value)
    assert "w" in str(excinfo.value)


def test_a_self_referential_definition_does_not_hang():
    """`b = a` captures the symbol `b`, so substitution reaches a fixed point.

    The loop stops when a pass changes nothing, rather than after a fixed count, and
    what remains is reported as an ordinary missing value - which is the right thing to
    say about a name defined in terms of itself.
    """
    engine = EngineeringEngine()
    run_cell(engine, "a = b\nb = a")
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "numeric(a)")
    assert "requires values for" in str(excinfo.value)
