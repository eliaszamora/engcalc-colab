"""`integrate(expr, x)` — the indefinite integral.

Step 1.2. On its own it unblocks nothing, which the measured gap map said plainly: the
only exercise needing it also needs scalar equation systems. Together with 1.1 it makes
the elastic curve derivable from scratch instead of quoted, which is the acceptance test
at the bottom of this file.

The constant of integration is written by the engineer, not invented by EngCalc:

    theta(x) = integrate(M(x)/(E*I), x) + C1

That is what you do on paper, and it avoids EngCalc having to name symbols nobody asked
for. `C1` is an ordinary free symbol and the boundary conditions determine it.
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


def test_the_indefinite_integral_is_the_antiderivative():
    result = run_cell(EngineeringEngine(), "a = integrate(x^2, x)")[-1]
    assert str(result.value) == "x**3/3"


def test_no_constant_of_integration_is_invented():
    """SymPy omits it and so does EngCalc. The engineer writes the one they need."""
    result = run_cell(EngineeringEngine(), "a = integrate(x, x)")[-1]
    assert str(result.value) == "x**2/2"

    written = run_cell(EngineeringEngine(), "b = integrate(x, x) + C1")[-1]
    assert "C1" in str(written.value)


def test_the_alias_accepts_the_indefinite_form_too():
    result = run_cell(EngineeringEngine(), "a = integral(x^2, x)")[-1]
    assert str(result.value) == "x**3/3"


def test_the_definite_form_is_unchanged():
    result = run_cell(EngineeringEngine(), "a = integrate(x^2, x, 0, 1)")[-1]
    assert str(result.value) == "1/3"


def test_the_indefinite_integral_works_entry_by_entry_on_a_matrix():
    result = run_cell(EngineeringEngine(), "A = integrate([x, x^2; 1, 0], x)")[-1]
    assert result.value is not None
    assert "x**2/2" in str(result.value)


def test_three_arguments_are_refused_with_a_message_naming_both_forms():
    """Two arguments or four. Three is a missing bound, and saying so helps."""
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(EngineeringEngine(), "a = integrate(x^2, x, 0)")
    message = str(excinfo.value)
    assert "2" in message and "4" in message


def test_the_rendered_input_shows_an_integral_without_bounds():
    import engcalc_colab.renderer as renderer

    result = run_cell(EngineeringEngine(), "a = integrate(x^2, x)")[-1]
    latex = renderer.render_result(result)
    assert r"\int" in latex
    assert "_{" not in latex.split(r"\int")[1][:12], (
        f"an indefinite integral must carry no bounds: {latex!r}"
    )


# ---------------------------------------------------------------------------
# Acceptance: the elastic curve, derived rather than quoted
# ---------------------------------------------------------------------------


def test_the_elastic_curve_is_derived_symbolically_from_scratch():
    """E4 of the gap map: integrate the moment twice and let the boundary conditions
    determine the constants.

    This is the exercise that needed both 1.1 and 1.2, and the reason the indefinite
    integral was scheduled alongside scalar systems rather than before them. The
    constants come out as the textbook values for a simply supported beam under uniform
    load, derived rather than quoted.

    Numeric evaluation of the resulting `v(x)` is a **separate, newly measured gap** and
    is deliberately not asserted here. A function definition captures its free symbols,
    and `numeric(...)` resolves symbols from the numeric context - values given with
    `:=` - not from the symbolic namespace where a solved constant lands. Recorded in
    the gap map; it is not what this step was for.
    """
    engine = EngineeringEngine()
    run_cell(
        engine,
        "L := 6*m\n"
        "q := 10*kN/m\n"
        "E := 200*GPa\n"
        "I_z := 80e6*mm**4\n"
        "R_A = q*L/2\n"
        "V(x) = R_A - q*x\n"
        "M(x) = integrate(V(x), x, 0, x)\n"
        "theta(x) = integrate(M(x)/(E*I_z), x) + C1\n"
        "v(x) = integrate(theta(x), x) + C2\n"
        "solve(eq(subs(v(x), x, 0), 0), eq(subs(v(x), x, L), 0), C1, C2)\n",
    )

    # v(0) = 0 puts no constant term in the deflection, and the slope constant is the
    # textbook -qL^3/(24EI).
    assert str(engine.namespace["C2"]) == "0"
    assert str(engine.namespace["C1"]) == "-L**3*q/(24*E*I_z)"


def test_the_moment_follows_from_integrating_the_shear():
    """The step before it, which needs only the definite form with a symbolic bound."""
    engine = EngineeringEngine()
    results = run_cell(
        engine,
        "L := 6*m\nq := 10*kN/m\nR_A = q*L/2\n"
        "V(x) = R_A - q*x\nM(x) = integrate(V(x), x, 0, x)\nnumeric(subs(M(x), x, L/2))",
    )
    assert float(results[-1].quantity.to("kN*m").magnitude) == pytest.approx(45.0)
