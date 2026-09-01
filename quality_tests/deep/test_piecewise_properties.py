"""Deep Property Gate — generated Level A coverage for Piecewise characteristics.

These are the most expensive properties in the suite, roughly ten times the cost of
the cheapest, so their example counts are deliberately lower. The budget is set per
property rather than per family precisely because the spread inside this family is
that wide.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings

from quality_tests.deep.strategies import piecewise_breakpoint, piecewise_operator
from quality_tests.helpers import (
    assert_close_sequence,
    characteristic_xs,
    evaluate_cell,
    role_xs,
)

pytestmark = [pytest.mark.evidence_a, pytest.mark.quality_deep]


@settings(max_examples=40)
@given(breakpoint_value=piecewise_breakpoint, operator=piecewise_operator)
def test_continuous_root_at_the_breakpoint(breakpoint_value, operator):
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


@settings(max_examples=40)
@given(breakpoint_value=piecewise_breakpoint, operator=piecewise_operator)
def test_jump_never_produces_a_root(breakpoint_value, operator):
    result = evaluate_cell(
        f"a := {breakpoint_value}\np1 := 1\np2 := -1\n"
        f"f(x) = piecewise(p1, x {operator} a, p2)\nroots(f(x), x, 0, 6)"
    )
    assert characteristic_xs(result) == []


@settings(max_examples=60)
@given(breakpoint_value=piecewise_breakpoint)
def test_breakpoint_on_upper_bound_has_no_attained_maximum(breakpoint_value):
    """A-2 family: the supremum is approached from the left and never reached."""
    result = evaluate_cell(
        f"a := {breakpoint_value}\ns(x) = piecewise(x, x < a, x - a)\n"
        "extrema(s(x), x, 0, a)"
    )
    left = [point for point in result.points if point.side == "left"]
    assert len(left) == 1
    assert float(left[0].value_quantity.magnitude) == pytest.approx(
        breakpoint_value, abs=1e-9
    )
    attained = [point for point in result.points if point.side == "at"]
    assert attained
    assert not any("global_max" in point.roles for point in attained)


@settings(max_examples=60)
@given(breakpoint_value=piecewise_breakpoint)
def test_breakpoint_on_lower_bound_attains_both_roles(breakpoint_value):
    """With `>=` the first branch owns the whole interval, so both roles land."""
    result = evaluate_cell(
        f"a := {breakpoint_value}\nL := 6\ns(x) = piecewise(x, x >= a, x - a)\n"
        "extrema(s(x), x, a, L)"
    )
    assert_close_sequence(role_xs(result, "global_min"), [breakpoint_value], abs_tol=1e-9)
    assert_close_sequence(role_xs(result, "global_max"), [6.0], abs_tol=1e-9)
