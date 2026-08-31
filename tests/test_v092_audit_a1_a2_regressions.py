"""Regression contracts for post-remediation audit findings A-1 and A-2.

A-1: complex exact candidates must be discarded instead of surfacing an internal
     ``float()`` TypeError as an EngCalc evaluation failure.
A-2: an analysis domain whose upper bound coincides with a strict Piecewise
     breakpoint must still expose the left-sided limit of the open region, and
     must not report an attained global maximum that the response never reaches.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ExtremaResult, IntersectionsResult, RootsResult
from engcalc_colab.parser import parse_cell


def run(engine, source):
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


# --------------------------------------------------------------------------
# A-1 — complex candidates are not real roots
# --------------------------------------------------------------------------


def test_a1_roots_with_registered_parameter_reports_no_real_roots():
    engine = EngineeringEngine()
    result = run(
        engine,
        """
a := 1
f(x) = x^2 + a
roots(f(x), x, -2, 2)
""",
    )
    assert isinstance(result, RootsResult)
    assert result.points == ()
    assert result.intervals == ()


def test_a1_registered_parameter_matches_literal_control():
    """The same function must behave identically with a literal constant."""
    literal = run(
        EngineeringEngine(),
        """
f(x) = x^2 + 1
roots(f(x), x, -2, 2)
""",
    )
    parameterized = run(
        EngineeringEngine(),
        """
a := 1
f(x) = x^2 + a
roots(f(x), x, -2, 2)
""",
    )
    assert len(parameterized.points) == len(literal.points) == 0


def test_a1_intersections_with_registered_parameter_reports_no_crossing():
    engine = EngineeringEngine()
    result = run(
        engine,
        """
k := 5
h(x) = k + x^2
intersections(h(x), 0*x, x, -3, 3)
""",
    )
    assert isinstance(result, IntersectionsResult)
    assert result.points == ()


def test_a1_unit_aware_response_that_never_reaches_the_level():
    engine = EngineeringEngine()
    result = run(
        engine,
        """
L := 6*m
q := 12*kN/m
M(x) = q*x*(L-x)/2
roots(M(x) + 1*kN*m, x, 0, L)
""",
    )
    assert isinstance(result, RootsResult)
    assert result.points == ()


def test_a1_real_roots_of_the_same_shape_are_still_found():
    """Guard against over-filtering: a negative parameter has real roots."""
    engine = EngineeringEngine()
    result = run(
        engine,
        """
a := -4
f(x) = x^2 + a
roots(f(x), x, -3, 3)
""",
    )
    assert isinstance(result, RootsResult)
    magnitudes = sorted(
        float(point.x_quantity.magnitude) for point in result.points
    )
    assert magnitudes == pytest.approx([-2.0, 2.0])


# --------------------------------------------------------------------------
# A-2 — open region edge coinciding with the domain bound
# --------------------------------------------------------------------------


def _roles(result, *, side):
    return [point.roles for point in result.points if point.side == side]


def test_a2_left_limit_is_reported_when_breakpoint_is_the_upper_bound():
    engine = EngineeringEngine()
    result = run(
        engine,
        """
a := 3*m
s(x) = piecewise(x, x < a, x - a)
extrema(s(x), x, 0, a)
""",
    )
    assert isinstance(result, ExtremaResult)
    left_points = [point for point in result.points if point.side == "left"]
    assert len(left_points) == 1
    assert left_points[0].x_quantity.to("m").magnitude == pytest.approx(3.0)
    assert left_points[0].value_quantity.to("m").magnitude == pytest.approx(3.0)


def test_a2_unattained_supremum_is_not_reported_as_global_max():
    engine = EngineeringEngine()
    result = run(
        engine,
        """
a := 3*m
s(x) = piecewise(x, x < a, x - a)
extrema(s(x), x, 0, a)
""",
    )
    attained = [point for point in result.points if point.side == "at"]
    assert attained, "the domain endpoints must still be reported"
    # s(2 m) = 2 m > 0, so no point valued 0 can be the global maximum.
    assert not any("global_max" in point.roles for point in attained)
    assert any("global_min" in point.roles for point in attained)


def test_a2_interior_breakpoint_behaviour_is_unchanged():
    engine = EngineeringEngine()
    result = run(
        engine,
        """
a := 3*m
L := 6*m
s(x) = piecewise(x, x < a, x - a)
extrema(s(x), x, 0, L)
""",
    )
    peak = [point for point in result.points if "global_max" in point.roles]
    assert len(peak) == 1
    assert peak[0].x_quantity.to("m").magnitude == pytest.approx(6.0)
    assert peak[0].value_quantity.to("m").magnitude == pytest.approx(3.0)


def test_a2_non_strict_breakpoint_still_attains_its_maximum():
    engine = EngineeringEngine()
    result = run(
        engine,
        """
a := 3*m
s(x) = piecewise(x, x <= a, x - a)
extrema(s(x), x, 0, a)
""",
    )
    peak = [point for point in result.points if "global_max" in point.roles]
    assert len(peak) == 1
    assert peak[0].value_quantity.to("m").magnitude == pytest.approx(3.0)


def test_a2_interior_extremum_inside_the_open_region_is_preserved():
    engine = EngineeringEngine()
    result = run(
        engine,
        """
a := 4*m
q := 12*kN/m
M(x) = piecewise(q*x*(a-x)/2, x < a, 0*kN*m)
extrema(M(x), x, 0, a)
""",
    )
    peak = [point for point in result.points if "global_max" in point.roles]
    assert len(peak) == 1
    assert peak[0].x_quantity.to("m").magnitude == pytest.approx(2.0)
    assert peak[0].value_quantity.to("kN*m").magnitude == pytest.approx(24.0)
