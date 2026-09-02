"""`solve` with more than one solution shows them all instead of refusing.

Step 1.3. Until now a second solution raised `AmbiguousSolveError`, whose message said
"v0.1 requires one" - a contract from the earliest version that nobody had revisited. It
is not a mathematical limit; SymPy returns the list.

The shape follows the system form: **many answers make it a standalone statement.** There
is nothing single to bind, so assigning it is refused with a message that names the tool
for the job it is usually being asked to do.

That tool already exists. `roots(f(x), x, a, b)` selects the root inside a physical
domain, with units, which is what an engineer actually wants when an equation has a
symmetric pair. Measured: the Euler buckling length of gap-map exercise E14 comes out as
12.57 m from `roots` today, and no `assume` would have helped - declaring the unknown
positive does not filter SymPy's answer, because the sign of `K` is still unknown.
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


def test_two_solutions_are_both_returned():
    result = run_cell(EngineeringEngine(), "solve(x^2 - 4, x)")[-1]
    assert [str(value) for _, value in result.solutions] == ["-2", "2"]


def test_every_solution_is_labelled_with_its_unknown():
    result = run_cell(EngineeringEngine(), "solve(x^2 - 5*x + 6, x)")[-1]
    assert [name for name, _ in result.solutions] == ["x", "x"]
    assert [str(value) for _, value in result.solutions] == ["2", "3"]


def test_each_solution_is_rendered_on_its_own_line():
    import engcalc_colab.renderer as renderer

    latex = renderer.render_result(run_cell(EngineeringEngine(), "solve(x^2 - 4, x)")[-1])
    assert latex.count(r"\displaystyle") == 3, latex  # the equation, then both solutions
    assert not [char for char in latex if ord(char) < 32]


def test_three_real_solutions_are_all_returned():
    result = run_cell(EngineeringEngine(), "solve(x^3 - 6*x^2 + 11*x - 6, x)")[-1]
    assert [str(value) for _, value in result.solutions] == ["1", "2", "3"]


def test_complex_roots_are_excluded_by_the_symbol_being_real_not_by_this_path():
    """Where the exclusion happens matters, so it is pinned here.

    `x^3 - 1` has one real root and two complex ones. EngCalc returns one solution, and
    **the solve path discards nothing**: engine symbols are declared real, an approved
    0.9.2 contract, so SymPy never offers the complex pair in the first place.

    Written because the first draft of this file assumed the opposite and asserted that
    three solutions would come back. Believing a solve path silently drops answers, when
    the real cause is a deliberate contract two releases earlier, is the kind of mistake
    that leads to 'fixing' something that was right.
    """
    import sympy as sp

    engine = EngineeringEngine()
    symbol = engine.resolve_symbol("x")
    assert symbol.assumptions0.get("real") is True
    assert sp.solve(symbol**3 - 1, symbol) == [1]

    results = run_cell(engine, "z = solve(x^3 - 1, x)")
    assert str(results[-1].value) == "1"


def test_a_multi_solution_solve_cannot_be_assigned_and_says_what_to_use():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "y = solve(x^2 - 4, x)")
    message = str(excinfo.value)
    assert "roots" in message, message


def test_a_single_solution_still_binds_exactly_as_before():
    results = run_cell(EngineeringEngine(), "z = solve(2*x - 4, x)")
    assert str(results[-1].value) == "2"


def test_a_single_solution_standalone_is_unchanged_too():
    """It stays an ordinary expression, so nothing about the old path moves."""
    results = run_cell(EngineeringEngine(), "f(x) = 2*x - 4\nsolve(f(x), x)")
    assert str(results[-1].value) == "2"


def test_no_solution_still_says_so():
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(EngineeringEngine(), "solve(eq(x, x + 1), x)")
    assert "no solution" in str(excinfo.value).lower()


def test_the_physical_root_is_still_the_job_of_roots():
    """E14 of the gap map, solvable today, and the reason 1.3 is small.

    `solve` gives the algebra: a symmetric pair. `roots` gives the answer an engineer
    wants: the one inside a domain, in metres.
    """
    engine = EngineeringEngine()
    result = run_cell(
        engine,
        "E := 200*GPa\nI := 40e6*mm**4\nK := 1.0\n"
        "g(Lk) = pi^2*E*I/(K*Lk)^2 - 500*kN\nroots(g(Lk), Lk, 0.5*m, 20*m)",
    )[-1]
    assert len(result.points) == 1
    assert float(result.points[0].x_quantity.to("m").magnitude) == pytest.approx(12.566, rel=1e-3)
