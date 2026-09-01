"""Fast Gate — Level A constructive coverage for Piecewise characteristics.

Expected topology is derived from EngCalc's public Piecewise contract — source
branch order decides ownership at a boundary, and a strict comparison leaves the
breakpoint to the following branch — rather than read off the current output.
That derivation is what promotes the operator/bound matrix from the audit's
Level B invariant to Level A here: the tests assert which branch owns the edge,
which side is reported, and which role each attained point carries, not merely
that the reported roles do not contradict each other.
"""

from __future__ import annotations

import pytest

from quality_tests.helpers import (
    assert_close_sequence,
    characteristic_xs,
    evaluate_cell,
)

pytestmark = pytest.mark.evidence_a


# --------------------------------------------------------------------------
# roots across a breakpoint
# --------------------------------------------------------------------------


@pytest.mark.parametrize("operator", ["<", "<=", ">", ">="])
@pytest.mark.parametrize("breakpoint_value", [1.5, 2.5, 4.0])
def test_continuous_response_has_its_root_at_the_breakpoint(operator, breakpoint_value):
    """Both branches vanish at the breakpoint, so the root is there whoever owns it."""
    if operator in ("<", "<="):
        body = (
            f"piecewise(x - {breakpoint_value}, x {operator} a, "
            f"2*(x - {breakpoint_value}))"
        )
    else:
        body = (
            f"piecewise(2*(x - {breakpoint_value}), x {operator} a, "
            f"x - {breakpoint_value})"
        )
    result = evaluate_cell(
        f"a := {breakpoint_value}\ng(x) = {body}\nroots(g(x), x, 0, 6)"
    )
    assert_close_sequence(
        characteristic_xs(result), [breakpoint_value], abs_tol=1e-9
    )


@pytest.mark.parametrize("operator", ["<", "<=", ">", ">="])
def test_pure_jump_never_produces_a_root(operator):
    """Neither branch is ever zero, so the discontinuity must not be read as one."""
    result = evaluate_cell(
        f"a := 3.0\np1 := 1\np2 := -1\n"
        f"f(x) = piecewise(p1, x {operator} a, p2)\nroots(f(x), x, 0, 6)"
    )
    assert characteristic_xs(result) == []


# --------------------------------------------------------------------------
# operator x bound topology  (Level A promotion of the audit's H2 invariant)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("operator", "expected_at", "expected_left"),
    [
        # s(x) = piecewise(x, x OP a, x - a) analysed on [0, a], a = 3.
        #
        # "<"  : [0,a) owned by x, the bound itself by x-a, so the supremum a is
        #        approached and never attained and no point may claim global_max.
        ("<", {0.0: (0.0, {"global_min"}), 3.0: (0.0, {"global_min"})}, 3.0),
        # "<=" : the bound belongs to the rising branch, so a is attained there.
        ("<=", {0.0: (0.0, {"global_min"}), 3.0: (3.0, {"global_max"})}, None),
        # ">"  : never true on [0,a], so the default branch owns the whole domain.
        (">", {0.0: (-3.0, {"global_min"}), 3.0: (0.0, {"global_max"})}, None),
        # ">=" : true only at the bound, which the first branch then owns.
        (">=", {0.0: (-3.0, {"global_min"}), 3.0: (3.0, {"global_max"})}, 0.0),
    ],
)
def test_breakpoint_on_upper_bound_topology(operator, expected_at, expected_left):
    result = evaluate_cell(
        f"a := 3\ns(x) = piecewise(x, x {operator} a, x - a)\nextrema(s(x), x, 0, a)"
    )

    attained = {
        float(point.x_quantity.magnitude): (
            float(point.value_quantity.magnitude),
            {role for role in point.roles if role.startswith("global_")},
        )
        for point in result.points
        if point.side == "at"
    }
    assert set(attained) == set(expected_at)
    for x, (expected_value, expected_roles) in expected_at.items():
        got_value, got_roles = attained[x]
        assert got_value == pytest.approx(expected_value, abs=1e-9), (x, attained)
        assert got_roles == expected_roles, (x, attained)

    left = [point for point in result.points if point.side == "left"]
    if expected_left is None:
        assert left == []
    else:
        assert len(left) == 1
        assert float(left[0].value_quantity.magnitude) == pytest.approx(
            expected_left, abs=1e-9
        )


@pytest.mark.parametrize(
    ("operator", "expected_at", "expected_right"),
    [
        # s(x) = piecewise(x, x OP a, x - a) analysed on [a, L], a = 3, L = 6, so
        # the breakpoint is the lower bound.
        #
        # "<"  : false at the bound, so x-a owns the whole interval: 0 rising to 3.
        ("<", {3.0: (0.0, {"global_min"}), 6.0: (3.0, {"global_max"})}, None),
        # "<=" : the bound belongs to x, giving 3 there, while (a,L] belongs to
        #        x-a and starts near 0. The maximum 3 is attained at both ends and
        #        the infimum 0 is approached from the right without being reached,
        #        so no point may claim global_min. This is the lower-bound mirror
        #        of the A-2 family.
        ("<=", {3.0: (3.0, {"global_max"}), 6.0: (3.0, {"global_max"})}, 0.0),
        # ">"  : true only above the bound, so the bound keeps x-a = 0 while the
        #        rest rises along x to 6.
        (">", {3.0: (0.0, {"global_min"}), 6.0: (6.0, {"global_max"})}, 3.0),
        # ">=" : true throughout, so x owns the whole interval: 3 rising to 6.
        (">=", {3.0: (3.0, {"global_min"}), 6.0: (6.0, {"global_max"})}, None),
    ],
)
def test_breakpoint_on_lower_bound_topology(operator, expected_at, expected_right):
    result = evaluate_cell(
        f"a := 3\nL := 6\ns(x) = piecewise(x, x {operator} a, x - a)\n"
        "extrema(s(x), x, a, L)"
    )

    attained = {
        float(point.x_quantity.magnitude): (
            float(point.value_quantity.magnitude),
            {role for role in point.roles if role.startswith("global_")},
        )
        for point in result.points
        if point.side == "at"
    }
    assert set(attained) == set(expected_at)
    for x, (expected_value, expected_roles) in expected_at.items():
        got_value, got_roles = attained[x]
        assert got_value == pytest.approx(expected_value, abs=1e-9), (x, attained)
        assert got_roles == expected_roles, (x, attained)

    right = [point for point in result.points if point.side == "right"]
    if expected_right is None:
        assert right == []
    else:
        assert len(right) == 1
        assert float(right[0].value_quantity.magnitude) == pytest.approx(
            expected_right, abs=1e-9
        )


# --------------------------------------------------------------------------
# interval roles around a discontinuity
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("high", "low"),
    [(1, -1), (5, 2), (-2, -7), (0, -4)],
)
def test_interval_roles_around_a_jump(high, low):
    """Two constant branches: each side is a constant locus, not a point."""
    result = evaluate_cell(
        f"a := 3.0\np1 := {high}\np2 := {low}\n"
        f"f(x) = piecewise(p1, x < a, p2)\nextrema(f(x), x, 0, 6)"
    )
    by_role = {
        interval.role: float(interval.value_quantity.magnitude)
        for interval in result.intervals
        if interval.value_quantity is not None
    }
    assert by_role.get("global_max") == pytest.approx(max(high, low))
    assert by_role.get("global_min") == pytest.approx(min(high, low))


def test_one_sided_values_are_reported_at_a_discontinuity():
    """A genuine jump must expose both one-sided values at the breakpoint."""
    result = evaluate_cell(
        "a := 3.0\np1 := 1\np2 := -1\n"
        "f(x) = piecewise(p1, x < a, p2)\nextrema(f(x), x, 0, 6)"
    )
    sides = {
        point.side: float(point.value_quantity.magnitude)
        for point in result.points
        if point.side != "at"
    }
    assert sides == {"left": pytest.approx(1.0), "right": pytest.approx(-1.0)}


def test_continuous_breakpoint_does_not_fabricate_one_sided_values():
    """Where the response is continuous there is nothing one-sided to report."""
    result = evaluate_cell(
        "a := 3\ng(x) = piecewise(x - a, x < a, 2*(x - a))\nextrema(g(x), x, 0, 6)"
    )
    assert [point for point in result.points if point.side != "at"] == []


# --------------------------------------------------------------------------
# interior behaviour must survive the partition
# --------------------------------------------------------------------------


def test_interior_extremum_inside_a_branch_is_found():
    result = evaluate_cell(
        "a := 4*m\nq := 12*kN/m\n"
        "M(x) = piecewise(q*x*(a-x)/2, x < a, 0*kN*m)\n"
        "extrema(M(x), x, 0, a)"
    )
    peak = [point for point in result.points if "global_max" in point.roles]
    assert len(peak) == 1
    assert peak[0].x_quantity.to("m").magnitude == pytest.approx(2.0)
    assert peak[0].value_quantity.to("kN*m").magnitude == pytest.approx(24.0)


def test_pole_inside_a_branch_does_not_create_a_root():
    """A branch that is never zero contributes no root even where it blows up."""
    result = evaluate_cell(
        "a := 3.0\nL := 6\np(x) = piecewise(1/(x - a), x < a, x)\n"
        "roots(p(x), x, 1, L)"
    )
    assert characteristic_xs(result) == []
