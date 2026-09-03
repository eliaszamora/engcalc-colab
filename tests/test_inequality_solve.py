"""`solve(M(x) > 20*kN*m, x, 0, L)` - where on the beam the moment exceeds a value.

The answer to an inequality is a region, so this returns intervals. Their boundaries are
the roots of `lhs - rhs`, which means this is the roots machinery with a sign test on
top rather than a second solver - and the roots machinery is what the whole Quality Gate
was built to protect.

SymPy cannot take this problem directly. `solve_univariate_inequality` on
`q*x*(L - x)/2 > 20*kN*m` raises NotImplementedError, because q, L, kN and m are unsigned
free symbols in the symbolic layer. Substitute what the sheet's `:=` lines say and the
same call returns `Interval.open(3 - sqrt(5), 3 + sqrt(5))`. The values are what make the
question answerable, which is why this goes through the numeric context.

The domain is required, and that is a deviation from what a CAS does - TI-Nspire and
Mathematica both answer `x^2 - 6x + 4 < 0` with no domain at all. The reason is units:
without bounds the variable has none, and "between 0.76 and 5.24" is not an engineering
answer. It is also, for a beam, simply the beam.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError, EngSyntaxError
from engcalc_colab.models import InequalityResult, ParsedHeading
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_characteristic_result


BEAM = """L := 6*m
q := 10*kN/m
M(x) = q*x*(L-x)/2
"""

# M(x) = 5*x*(6 - x), so M > 20 is 5x^2 - 30x + 20 < 0, x^2 - 6x + 4 < 0, and the
# boundaries are 3 -/+ sqrt(5). Worked here rather than read off a run.
LOWER = 3 - 5 ** 0.5
UPPER = 3 + 5 ** 0.5


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


def bounds(result: InequalityResult):
    """Every interval as (lower, upper, lower_closed, upper_closed) in metres."""
    return [
        (
            pytest.approx(float(interval.lower_quantity.to("m").magnitude), abs=1e-9),
            pytest.approx(float(interval.upper_quantity.to("m").magnitude), abs=1e-9),
            interval.lower_closed,
            interval.upper_closed,
        )
        for interval in result.intervals
    ]


def test_the_moment_exceeds_its_limit_between_the_two_crossings():
    _engine, results = run_lines(BEAM + "solve(M(x) > 20*kN*m, x, 0, L)")
    result = results[-1]

    assert isinstance(result, InequalityResult)
    assert bounds(result) == [(LOWER, UPPER, False, False)]


def test_a_strict_comparison_opens_the_ends_and_a_non_strict_one_closes_them():
    """The boundary is where the two sides are equal, so it belongs to `>=` and not `>`.

    Asserted as a pair. Checking either alone passes against an implementation that
    hard-codes one closure and ignores the operator entirely.
    """
    _engine, strict = run_lines(BEAM + "solve(M(x) > 20*kN*m, x, 0, L)")
    _engine, loose = run_lines(BEAM + "solve(M(x) >= 20*kN*m, x, 0, L)")

    assert bounds(strict[-1]) == [(LOWER, UPPER, False, False)]
    assert bounds(loose[-1]) == [(LOWER, UPPER, True, True)]


def test_the_opposite_comparison_gives_the_rest_of_the_beam():
    """Two regions, and the ends of the domain are closed because they are not roots.

    x = 0 and x = L are bounds the engineer wrote. The inequality holds there and there
    is nothing to exclude, so treating every interval end as a root would wrongly open
    them.
    """
    _engine, results = run_lines(BEAM + "solve(M(x) < 20*kN*m, x, 0, L)")

    assert bounds(results[-1]) == [
        (pytest.approx(0.0, abs=1e-9), LOWER, True, False),
        (UPPER, pytest.approx(6.0, abs=1e-9), False, True),
    ]


def test_a_touching_root_splits_a_strict_region_and_joins_a_non_strict_one():
    """`(x - 3*m)^2` touches zero without crossing it.

    Under `> 0` the answer is [0, 3) and (3, 6]: the response is positive on both sides
    and zero at the touch, which the comparison excludes. Under `>= 0` it is all of
    [0, 6].

    This is the case that catches merging neighbours unconditionally. Every other
    inequality here has regions separated by a genuine sign change, where the boundary is
    excluded on both sides anyway, so a merge that ignores the operator passes all of
    them and quietly hands back the one point the inequality rules out.
    """
    _engine, strict = run_lines(
        "L := 6*m\ng(x) = (x - 3*m)^2\nsolve(g(x) > 0*m^2, x, 0, L)"
    )
    _engine, loose = run_lines(
        "L := 6*m\ng(x) = (x - 3*m)^2\nsolve(g(x) >= 0*m^2, x, 0, L)"
    )

    assert bounds(strict[-1]) == [
        (pytest.approx(0.0, abs=1e-9), pytest.approx(3.0, abs=1e-9), True, False),
        (pytest.approx(3.0, abs=1e-9), pytest.approx(6.0, abs=1e-9), False, True),
    ]
    assert bounds(loose[-1]) == [
        (pytest.approx(0.0, abs=1e-9), pytest.approx(6.0, abs=1e-9), True, True)
    ]


def test_an_inequality_nothing_satisfies_reports_nothing():
    """The peak moment is 45 kN*m, so 100 is out of reach everywhere on the span."""
    _engine, results = run_lines(BEAM + "solve(M(x) > 100*kN*m, x, 0, L)")
    assert results[-1].intervals == ()


def test_an_inequality_everything_satisfies_reports_the_whole_span():
    _engine, results = run_lines(BEAM + "solve(M(x) >= 0*kN*m, x, 0, L)")
    assert bounds(results[-1]) == [
        (pytest.approx(0.0, abs=1e-9), pytest.approx(6.0, abs=1e-9), True, True)
    ]


def test_the_answer_carries_the_unit_the_domain_gave_it():
    """The whole reason the domain is required.

    `L := 6*m` makes the bounds metres, so the crossings are metres. Without a domain the
    variable has no unit and the answer is two bare numbers.
    """
    _engine, results = run_lines(BEAM + "solve(M(x) > 20*kN*m, x, 0, L)")
    interval = results[-1].intervals[0]
    assert interval.lower_quantity.to("mm").magnitude == pytest.approx(
        LOWER * 1000, rel=1e-9
    )


def test_an_inequality_without_a_domain_says_what_is_missing():
    engine, _ = run_lines(BEAM)
    with pytest.raises(EngSyntaxError) as excinfo:
        run_cell(engine, "solve(M(x) > 20*kN*m, x)")
    message = str(excinfo.value)
    assert "solve(M(x) > 20*kN*m, x, 0, L)" in message
    assert "unit" in message


def test_a_region_cannot_be_assigned_to_a_name():
    engine, _ = run_lines(BEAM)
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(engine, "z = solve(M(x) > 20*kN*m, x, 0, L)")
    assert "region" in str(excinfo.value)


def test_the_equation_forms_of_solve_still_work():
    """`>=` contains an `=`, and the rewrite that turns `solve(a = b, x)` into
    `eq(a, b)` used to seize on it and produce `eq(M(x) >, 2)` - reported to the
    engineer as invalid syntax in their own line. Both forms are pinned here so
    narrowing that rewrite cannot cost the feature it exists for.
    """
    _engine, bare = run_lines("solve(2*y = 10, y)")
    _engine, wrapped = run_lines("solve(eq(2*y, 10), y)")
    assert bare[-1].value == 5
    assert wrapped[-1].value == 5


def test_an_equality_comparator_points_at_the_equation_forms():
    engine = EngineeringEngine()
    with pytest.raises(EngSyntaxError) as excinfo:
        run_cell(engine, "solve(2*y == 10, y)")
    message = str(excinfo.value)
    assert "solve(a = b, x)" in message
    assert "eq(a, b)" in message


def test_the_region_is_rendered_with_its_brackets():
    _engine, results = run_lines(BEAM + "solve(M(x) > 20*kN*m, x, 0, L)")
    rendered = render_characteristic_result(results[-1])

    assert "satisfies the inequality" in rendered
    # The brackets are the answer's open/closed ends, so they have to survive rendering.
    assert "(" in rendered and ")" in rendered
    assert "0.76" in rendered and "5.24" in rendered
