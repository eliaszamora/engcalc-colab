"""`numeric(...)` reads a unit literal as the unit, the way `:=` always has.

In the symbolic layer a unit is an ordinary free symbol, so `M = 5*kN` stores an
expression containing `Symbol('kN')`. Asking for its number used to fail with

    requires values for: kN. Define the missing numeric values first,
    for example: kN := <value>*<unit>

which is advice nobody should follow. Meanwhile `sigma := N/A` on the very same sheet
resolved `N` to newtons without complaint, because the numeric assignment path has read
undefined unit aliases as units since the beginning. The two paths disagreed; this is
not a new rule, it is the existing one reaching the other path.

None of the 1203 tests that passed before this change ever reached it. That was measured
rather than assumed - a counter on the new branch stayed at zero across the whole suite -
which is why these contracts exist. A green suite is evidence of no regression and no
evidence at all that a change works, and the two have to be established separately.

What this deliberately does NOT settle: `N`, `m` and `s` are unit aliases and also
perfectly ordinary variable names. A sheet that writes `sigma = N/A` meaning axial force
and never defines `N` is now told, quietly, that sigma is one newton per unit area. That
was already true of `:=` before this change and is pinned below rather than hidden, so
the day someone decides to warn about it, the decision is visible.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import (
    NumericMatrixEvaluationResult,
    ParsedHeading,
    PartialMatrixNumericEvaluationResult,
)
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_result


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def run_lines(source: str):
    engine = EngineeringEngine()
    results = []
    for line in [ln for ln in source.strip().splitlines() if ln.strip()]:
        results.extend(run_cell(engine, line))
    return engine, results


def test_a_symbolic_expression_carrying_a_unit_reaches_a_number():
    _engine, results = run_lines("M = 5*kN\nnumeric(M)")
    assert results[-1].quantity.to("kN").magnitude == pytest.approx(5.0)


def test_the_unit_stays_a_unit_in_the_substitution_stage():
    """Nobody writes "kN = 1 kN" under their working.

    The unit resolves for the arithmetic and never joins the substitutions, so the
    printer renders it as itself. Pinned because the obvious implementation - put the
    resolved unit in the substitutions dict - crashes the renderer outright, a Pint Unit
    having no magnitude, and the near miss is to "fix" that by substituting `1*kN` and
    printing a line no engineer would write.
    """
    _engine, results = run_lines(
        "E := 200*GPa\nA := 100*mm**2\nP = E*A/kN\nnumeric(P)"
    )
    rendered = render_result(results[-1])

    assert "kN" in rendered
    assert "200.00" in rendered  # E did reach the substitution stage
    assert r"1.00\,\mathrm{kN}" not in rendered


def test_euler_buckling_reaches_its_number():
    """E14 end to end, checked by hand.

    P_cr = pi^2*E*I/(K*L)^2 = 500 kN with E*I = 8000 kN*m^2 gives L = pi*sqrt(16) = 4*pi
    metres. The `kN` reaching `numeric` came out of the solve, from the `500*kN` the
    engineer wrote, so this is the line the exercise actually stops on.
    """
    _engine, results = run_lines(
        "E := 200*GPa\n"
        "I := 40e6*mm**4\n"
        "K := 1.0\n"
        "assume(Lk > 0)\n"
        "P_cr(Lk) = pi^2*E*I/(K*Lk)^2\n"
        "L_max = solve(eq(P_cr(Lk), 500*kN), Lk)\n"
        "numeric(L_max)"
    )
    quantity = results[-1].quantity
    assert quantity.to("m").magnitude == pytest.approx(4 * 3.141592653589793, rel=1e-9)


def test_a_defined_value_beats_the_unit_of_the_same_name():
    """`m := 4.0` means the sheet's `m` is 4, not metres.

    This is the precedence that makes the change safe to have at all, and it is the one
    an implementation gets wrong by resolving units first. Reversed, `2*m` would come
    back as two metres on a sheet that plainly said otherwise.
    """
    _engine, results = run_lines("m := 4.0\nx = 2*m\nnumeric(x)")
    quantity = results[-1].quantity
    assert quantity.dimensionless
    assert float(quantity.magnitude) == pytest.approx(8.0)


def test_a_name_that_is_not_a_unit_is_still_missing():
    """The diagnostic that matters most is the one that must survive.

    Resolving unit literals must not turn "you forgot to define this" into a number.
    """
    engine, _ = run_lines("y = p*q")
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "numeric(y)")
    message = str(excinfo.value)
    assert "requires values for: p, q" in message


def test_numeric_now_agrees_with_the_assignment_path():
    """The two paths gave different answers to the same question; that was the defect.

    `a := N` has always been one newton. `b = N` then `numeric(b)` used to refuse. This
    asserts they agree rather than asserting either one in isolation, because the defect
    was the disagreement.
    """
    engine, results = run_lines("a := N\nb = N\nnumeric(b)")
    assert results[-1].quantity == engine.numeric_context.values["a"]


def test_a_matrix_of_forces_evaluates_instead_of_reporting_itself_partial():
    """The same rule on the matrix path.

    Without it a column of forces comes back as a partial evaluation - every entry left
    symbolic - because `kN` looks like a name nobody defined. That is not an error the
    reader can act on; it is the matrix quietly declining to be a matrix of numbers.
    """
    _engine, results = run_lines("Fv = [3*kN; 4*kN]\nnumeric(Fv)")
    result = results[-1]

    assert isinstance(result, NumericMatrixEvaluationResult)
    assert not isinstance(result, PartialMatrixNumericEvaluationResult)
    assert result.quantity_matrix.entry(0, 0).to("kN").magnitude == pytest.approx(3.0)
    assert result.quantity_matrix.entry(1, 0).to("kN").magnitude == pytest.approx(4.0)


def test_a_matrix_with_a_free_variable_is_still_reported_partial():
    """Units resolving must not collapse the partial path that exists for free variables.

    `x` is the variable the matrix is a function of, not a value anyone forgot.
    """
    _engine, results = run_lines("Kx = [3*kN; 4*kN*x]\nnumeric(Kx)")
    assert isinstance(results[-1], PartialMatrixNumericEvaluationResult)


def test_an_undefined_axial_force_reads_as_newtons():
    """Pinned as a known hazard, not as a desirable outcome.

    `N` is axial force in any structures memoria and also the alias for newton. A sheet
    that writes `sigma = N/A` and never defines `N` is told sigma is one newton per unit
    area, with no complaint. This is what `:=` has always done - `sigma := N/A` gives the
    same - so the change did not introduce it, and making the two paths agree is what
    makes it visible in one place.

    If EngCalc ever warns here, this contract is the thing that has to be rewritten, and
    that is the point of it.
    """
    engine, results = run_lines("A := 100*mm**2\nsigma = N/A\nnumeric(sigma)")
    through_numeric = results[-1].quantity

    run_cell(engine, "sigma_2 := N/A")
    assert through_numeric == engine.numeric_context.values["sigma_2"]
    assert through_numeric.to("N/mm**2").magnitude == pytest.approx(0.01)
