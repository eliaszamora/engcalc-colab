"""Scalar equation systems: `solve(eq1, eq2, R_A, R_B)`.

Step 1.1. The largest gap the measured feature gap map found, and how statics is
actually written: sum the forces, sum the moments, solve for the reactions.

The call shape is `solve(eq_1, ..., eq_n, x_1, ..., x_n)` - n equations followed by n
unknowns. The existing two-argument form is the n = 1 case of exactly that rule, which
is why it needs no special case and keeps working unchanged.

The unknowns are named as trailing arguments and the results come back labelled, which
is what every established system does: SymPy returns a dict, Mathematica rules, Maxima
`[x = ...]`, TI-Nspire `x=... and y=...`. Positional destructuring was rejected because
`R_B, R_A = solve(eq1, eq2, R_A, R_B)` would cross the values silently.
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


_STATICS = """L := 6*m
q := 10*kN/m
eqFy = eq(R_A + R_B, q*L)
eqMA = eq(R_B*L, q*L*L/2)
solve(eqFy, eqMA, R_A, R_B)
"""


def test_a_two_by_two_statics_system_is_solved():
    engine = EngineeringEngine()
    result = run_cell(engine, _STATICS)[-1]

    assert str(engine.namespace["R_A"]) == "L*q/2"
    assert str(engine.namespace["R_B"]) == "L*q/2"
    assert [name for name, _ in result.solutions] == ["R_A", "R_B"]


def test_the_unknowns_are_defined_and_usable_afterwards():
    """Solving the system leaves the reactions known, as it does on paper."""
    engine = EngineeringEngine()
    run_cell(engine, _STATICS)
    result = run_cell(engine, "V(x) = R_A - q*x\nnumeric(subs(V(x), x, 0*m))")[-1]

    assert result.quantity.to("kN").magnitude == pytest.approx(30.0)


def test_each_unknown_is_rendered_on_its_own_labelled_line():
    """A memoria shows both reactions, not an anonymous vector."""
    import engcalc_colab.renderer as renderer

    engine = EngineeringEngine()
    result = run_cell(engine, _STATICS)[-1]
    latex = renderer.render_aligned_results([result])

    assert latex.count("R_{A}") >= 1
    assert latex.count("R_{B}") >= 1
    assert r"\begin{array}" in latex and r"\end{array}" in latex

    # Rows of the sheet's own array, so the unknowns share its `=` column. This used to
    # render a nested single-column array which `_standard_result_row` then split on its
    # first " = ", injecting `& = &` into an environment declared `{l}`: one solution
    # picked up separators, the rest had none, and the block drifted left of the
    # equations above it. Counting `\displaystyle` could not see that - the mangled
    # version had the same count.
    rows = latex.split(r"\\")
    solution_rows = [row for row in rows if "R_{A} & = &" in row or "R_{B} & = &" in row]
    assert len(solution_rows) == 2, latex
    assert r"\begin{array}" not in "".join(solution_rows)
    # A control character reached this template once, from an escape in the source that
    # turned `\begin` into a backspace, and the assertions above still passed while the
    # output read `egin{array}`. Nothing but the eye caught it.
    assert not [char for char in latex if ord(char) < 32], (
        f"control character in rendered LaTeX: {latex!r}"
    )


def test_boundary_conditions_for_an_elastic_curve():
    """The other half of why this matters: C1 and C2 come out together."""
    engine = EngineeringEngine()
    results = run_cell(
        engine,
        "v(x) = x^3/6 + C1*x + C2\n"
        "bc1 = eq(subs(v(x), x, 0), 0)\n"
        "bc2 = eq(subs(v(x), x, 6), 0)\n"
        "solve(bc1, bc2, C1, C2)\n",
    )
    assert str(engine.namespace["C2"]) == "0"
    assert [name for name, _ in results[-1].solutions] == ["C1", "C2"]


def test_a_three_by_three_system():
    engine = EngineeringEngine()
    run_cell(
        engine,
        "e1 = eq(a + b + c, 6)\ne2 = eq(b, 2)\ne3 = eq(c, 3)\nsolve(e1, e2, e3, a, b, c)\n",
    )
    assert str(engine.namespace["a"]) == "1"


def test_the_existing_single_unknown_form_is_unchanged():
    engine = EngineeringEngine()
    results = run_cell(engine, "f(x) = 2*x - 4\nz = solve(f(x), x)")
    assert str(results[-1].value) == "2"


def test_the_matrix_form_is_unchanged():
    engine = EngineeringEngine()
    results = run_cell(engine, "A = [2, 0; 0, 4]\nb = [4; 8]\nx = solve(A, b)")
    assert results[-1].value is not None


def test_an_odd_argument_count_is_refused_with_a_clear_message():
    """n equations and n unknowns, so the count is even. Anything else is a mistake."""
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "e1 = eq(a + b, 3)\ne2 = eq(a - b, 1)\nsolve(e1, e2, a)")
    assert "equations" in str(excinfo.value)


def test_an_unknown_must_be_an_identifier():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError):
        run_cell(engine, "e1 = eq(a + b, 3)\ne2 = eq(a - b, 1)\nsolve(e1, e2, a, b + 1)")


def test_a_system_with_no_solution_says_so():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "e1 = eq(a + b, 1)\ne2 = eq(a + b, 2)\nsolve(e1, e2, a, b)")
    assert "no solution" in str(excinfo.value).lower()


def test_a_system_cannot_be_assigned_to_a_single_name():
    """There is no single value to bind. The unknowns are the result."""
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError):
        run_cell(engine, "e1 = eq(a + b, 3)\ne2 = eq(a - b, 1)\ns = solve(e1, e2, a, b)")


def test_an_odd_count_above_the_minimum_is_also_refused():
    """`solve(e1, e2, a)` is refused by the minimum alone, so it proves nothing.

    A mutation accepting any odd count passed every other contract in this file,
    because the only odd case tested had three arguments and three is below the
    four-argument minimum. Five arguments is the case that separates the rules.
    """
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(
            engine,
            "e1 = eq(a + b, 3)\ne2 = eq(a - b, 1)\ne3 = eq(c, 1)\nsolve(e1, e2, e3, a, b)",
        )
    assert "even" in str(excinfo.value)


def test_an_unknown_written_inline_is_free_even_if_the_name_has_a_value():
    """Every named unknown is free while the solve reads its equations.

    Note where this applies. An equation stored first — `e1 = eq(a + b, 3)` — is built
    when that line runs, so a name already carrying a value is substituted into it there
    and no later override can recover it. That is consistent with the rest of the
    language, where `M(x) = q*x*(L-x)/2` also captures `q` at definition. The override
    matters for equations written inside the call, and that is what this pins.
    """
    engine = EngineeringEngine()
    run_cell(engine, "a = 10\nsolve(eq(a + b, 3), eq(a - b, 1), a, b)")

    assert str(engine.namespace["a"]) == "2"
    assert str(engine.namespace["b"]) == "1"


def test_repeating_an_unknown_is_refused():
    """`solve(e1, e2, a, a)` is two equations and one unknown wearing a disguise."""
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "e1 = eq(a + b, 3)\ne2 = eq(a - b, 1)\nsolve(e1, e2, a, a)")
    assert "distinct" in str(excinfo.value)
