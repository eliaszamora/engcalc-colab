"""`assume` decides which of several answers is the answer.

Euler buckling is the case that exposed the gap. `P_cr = pi^2*E*I/(K*L)^2` is even in
L, so solving it for L returns a symmetric pair, and `assume(Lk > 0)` did not collapse
them. The assumption reached the unknown's symbol - `Lk.is_positive` was already True -
but a length being positive says nothing about the sign of `pi*sqrt(E*I/kN)/K`, whose
every symbol is unsigned. SymPy kept both roots and was right to.

The information that settles it is on the page: `E := 200*GPa`, `I := 40e6*mm**4`,
`K := 1.0`. That is what an engineer reads off their own sheet when they cross out the
negative root. So the numeric context is asked second, and only when SymPy has no
opinion.

Three rules keep this from becoming a solver that quietly loses answers:

- without `assume`, nothing is discarded, however obvious the sign looks;
- an answer that cannot be evaluated survives, because ignorance is not refutation;
- if every answer would go, none does - that is a statement about the problem.

And whatever is discarded is shown. An engineer given one answer has no way to know two
were found, and the difference between "there was one" and "I ruled one out" is the
difference between arithmetic and a decision.
"""

import pytest
import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import EvaluationResult, ParsedHeading
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_aligned_results


EULER = """E := 200*GPa
I := 40e6*mm**4
K := 1.0
P_cr(Lk) = pi^2*E*I/(K*Lk)^2
"""


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def run_lines(source: str):
    """Run line by line, as a sheet does, so `assume` precedes the symbols it binds."""
    engine = EngineeringEngine()
    results = []
    for line in [ln for ln in source.strip().splitlines() if ln.strip()]:
        results.extend(run_cell(engine, line))
    return engine, results


def test_euler_buckling_length_resolves_to_the_positive_root():
    """The exercise that motivated this, checked against the answer by hand.

    P_cr = pi^2*E*I/(K*L)^2 = 500 kN with E = 200 GPa and I = 40e6 mm^4 gives
    E*I = 8000 kN*m^2, so L = pi*sqrt(8000/500) = 4*pi = 12.566 m. Computed here rather
    than read off the run, so a solver that returned the negative root, or half of it,
    or the answer in millimetres, would fail.
    """
    engine, results = run_lines(
        "assume(Lk > 0)\n" + EULER + "L_max = solve(eq(P_cr(Lk), 500*kN), Lk)"
    )

    value = results[-1].value
    assert value.is_number is False  # still symbolic in E, I, K, kN

    context = engine.numeric_context
    _substitutions, quantity = context.evaluate_symbolic(
        value, overrides=context.unit_literal_overrides(value)
    )
    assert quantity.to("m").magnitude == pytest.approx(4 * 3.141592653589793, rel=1e-9)


def test_the_answer_is_a_single_value_that_the_sheet_can_go_on_to_use():
    """Assigning is the point. Two answers cannot be assigned, and E14 stopped there."""
    engine, results = run_lines(
        "assume(Lk > 0)\n" + EULER + "L_max = solve(eq(P_cr(Lk), 500*kN), Lk)"
    )
    assert "L_max" in engine.namespace
    assert isinstance(results[-1], EvaluationResult)


def test_the_discarded_root_is_named_and_so_is_the_reason():
    engine, results = run_lines(
        "assume(Lk > 0)\n" + EULER + "L_max = solve(eq(P_cr(Lk), 500*kN), Lk)"
    )
    discarded = results[-1].discarded

    assert discarded is not None
    assert discarded.variable == "Lk"
    assert discarded.condition == "positive"
    assert len(discarded.values) == 1

    context = engine.numeric_context
    ruled_out = discarded.values[0]
    _substitutions, quantity = context.evaluate_symbolic(
        ruled_out, overrides=context.unit_literal_overrides(ruled_out)
    )
    # Not merely "a root went away": the one that went is the negative one.
    assert quantity.to("m").magnitude == pytest.approx(-4 * 3.141592653589793, rel=1e-9)


def test_the_sheet_shows_the_discard():
    """A discard the reader cannot see is a solver that silently found one answer."""
    _engine, results = run_lines(
        "assume(Lk > 0)\n" + EULER + "L_max = solve(eq(P_cr(Lk), 500*kN), Lk)"
    )
    rendered = render_aligned_results([results[-1]])

    assert r"\text{discarded by }" in rendered
    assert "Lk > 0" in rendered

    # The note must carry the root itself. Counting `sqrt` across the whole rendering
    # proves nothing: the kept root has two of its own, so "1 root discarded" would
    # satisfy that while telling the reader nothing they could check. Read the note.
    note = rendered.split(r"\text{discarded by }", 1)[1]
    assert "sqrt" in note
    assert "-" in note.split(":", 1)[1][:40]


def test_without_an_assumption_both_answers_survive():
    """The unsigned case is not a defect to be tidied away; it is the honest answer.

    Nothing about the sheet has changed except that the engineer did not say a length is
    positive, so both roots stand and the statement cannot be an assignment.
    """
    engine = EngineeringEngine()
    for line in [ln for ln in EULER.strip().splitlines() if ln.strip()]:
        run_cell(engine, line)

    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "L_max = solve(eq(P_cr(Lk), 500*kN), Lk)")
    assert "2 solutions" in str(excinfo.value)

    results = run_cell(engine, "solve(eq(P_cr(Lk), 500*kN), Lk)")
    assert len(results[-1].solutions) == 2
    assert results[-1].discarded is None


def test_an_answer_that_cannot_be_evaluated_is_kept():
    """Ignorance is not refutation.

    The roots of `xr^2 + 3*a*xr + 2*a^2` are `-a` and `-2a`. SymPy cannot place either
    on a side of zero, since `a` is unsigned, and neither can the numeric context, since
    `a` was never given a value. Both survive. Discarding on a failed evaluation is how
    a solver loses correct answers while looking more decisive than it is.
    """
    _engine, results = run_lines(
        "assume(xr > 0)\nf(xr) = xr^2 + 3*a*xr + 2*a^2\nsolve(eq(f(xr), 0), xr)"
    )
    result = results[-1]
    assert len(result.solutions) == 2
    assert result.discarded is None


def test_an_assumption_that_rules_out_everything_rules_out_nothing():
    """Emptying the solution set would hide the finding instead of reporting it.

    The roots are `-a` and `-2a` with `a := 3.0`, so both are negative once evaluated,
    and the engineer said the unknown is positive. One of the two is wrong, and that is
    worth seeing; a run that returned no answers would look like a solver that failed
    rather than a premise that is false.

    SymPy cannot reach this on its own - `a` is unsigned, so it returns both roots - and
    that is what makes it a test of the filter rather than of SymPy.
    """
    _engine, results = run_lines(
        "assume(xr > 0)\na := 3.0\nf(xr) = xr^2 + 3*a*xr + 2*a^2\nsolve(eq(f(xr), 0), xr)"
    )
    result = results[-1]
    assert len(result.solutions) == 2
    values = {sp.sstr(sp.sympify(v)) for _n, v in result.solutions}
    assert values == {"-a", "-2*a"}
    assert result.discarded is None


def test_sympy_has_already_dropped_whatever_it_could_decide():
    """The reason there is no symbolic branch in the filter.

    `assume(xr > 0)` makes the unknown positive and `sp.solve` honours it, so the -2 of
    `xr^2 = 4` never reaches the filter at all. Pinned because the obvious design - ask
    `value.is_positive` first, fall back to numbers - would be dead code resting on the
    opposite belief, and dead code that looks like a safety net is worse than none.
    """
    engine, results = run_lines("assume(xr > 0)\nf(xr) = xr^2\nxr_1 = solve(eq(f(xr), 4), xr)")
    assert sp.sympify(results[-1].value) == sp.Integer(2)
    assert results[-1].discarded is None
    assert engine.numeric_context.values == {}


def test_a_decided_answer_goes_and_an_undecided_one_beside_it_stays():
    """The two verdicts have to be told apart, not merged into "not kept".

    `(xr + a)*(xr - b)` has roots `-a` and `b`. With `a := 3.0` the first evaluates to
    -3 and is refuted; `b` has no value and stays undecided. One goes, one stays.

    Every other case here has all its answers in the same state, so a filter that
    dropped the undecided ones along with the refuted ones would pass all of them: with
    nothing left to keep, the empty-set guard puts everything back and the result looks
    untouched. This is the case that separates the two.
    """
    _engine, results = run_lines(
        "assume(xr > 0)\na := 3.0\nf(xr) = (xr + a)*(xr - b)\nsolve(eq(f(xr), 0), xr)"
    )
    result = results[-1]

    # One survivor, so it is a value rather than a list of candidates to read.
    assert isinstance(result, EvaluationResult)
    assert sp.sstr(sp.sympify(result.value)) == "b"
    assert result.discarded is not None
    assert [sp.sstr(v) for v in result.discarded.values] == ["-a"]


def test_the_alignment_guard_still_holds_with_the_note():
    """The renderer refuses to lay out rows it has not accounted for.

    That guard is why a note row cannot be added anywhere without being sized, and it
    only fires when a result carrying a note is rendered beside others.
    """
    engine, results = run_lines(
        "assume(Lk > 0)\n"
        + EULER
        + "L_max = solve(eq(P_cr(Lk), 500*kN), Lk)\n"
        + "L_b = L_max/2"
    )
    rendered = render_aligned_results([r for r in results if r is not None])
    assert r"\text{discarded by }" in rendered
