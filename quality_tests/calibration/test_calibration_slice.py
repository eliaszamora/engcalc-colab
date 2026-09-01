"""Temporary calibration slice — deleted in Task 8.

One or two representative Level A cases per required partition of design §6.1, so
GitHub Actions can measure per-partition cost before the permanent corpus is
dimensioned. Sizing must follow measurement, not precede it.

No random generation here: every expected answer is known by construction.
"""

from __future__ import annotations

import pytest

from quality_tests.helpers import (
    assert_close_sequence,
    bisect_monotone_quintic,
    characteristic_xs,
    evaluate_cell,
    role_xs,
)

pytestmark = pytest.mark.evidence_a


# --------------------------------------------------------------------------
# roots
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("coeff", "roots"),
    [
        (1.0, [1.5]),
        (2.5, [-1.25, 2.0]),
        (-1.75, [-3.0, 0.5, 2.75]),
    ],
)
def test_roots_factored(coeff, roots):
    factors = "*".join(f"(x - {r})" for r in roots)
    result = evaluate_cell(f"f(x) = {coeff}*{factors}\nroots(f(x), x, -5, 5)")
    assert_close_sequence(characteristic_xs(result), sorted(roots))


@pytest.mark.parametrize(
    ("a", "r1", "r2"),
    [
        (2.87, 0.602, 3.755),
        (1.01, 0.313, 2.619),
        (-1.87, 1.35, 3.245),
    ],
)
def test_roots_expanded_decimal(a, r1, r2):
    """N-1 family: expanded decimal coefficients, historically 8/20 silent losses."""
    b = -a * (r1 + r2)
    c = a * r1 * r2
    result = evaluate_cell(
        f"f(x) = {a}*x^2 + {b}*x + {c}\nroots(f(x), x, 0, 5)"
    )
    assert_close_sequence(characteristic_xs(result), [r1, r2], rel_tol=1e-6)


@pytest.mark.parametrize("r", [-2.5, 1.75])
def test_roots_repeated(r):
    result = evaluate_cell(f"f(x) = 2.0*(x - {r})^2\nroots(f(x), x, -5, 5)")
    assert_close_sequence(characteristic_xs(result), [r])


@pytest.mark.parametrize("a", [1.0, 4.75])
def test_roots_registered_parameter_no_real_roots(a):
    """A-1 family: complex candidates must not surface as an internal error."""
    result = evaluate_cell(f"a := {a}\nf(x) = x^2 + a\nroots(f(x), x, -5, 5)")
    assert characteristic_xs(result) == []


@pytest.mark.parametrize(("a", "root"), [(4.0, 2.0), (2.25, 1.5)])
def test_roots_registered_parameter_with_real_roots(a, root):
    result = evaluate_cell(f"a := {a}\nf(x) = x^2 - a\nroots(f(x), x, -5, 5)")
    assert_close_sequence(characteristic_xs(result), [-root, root])


@pytest.mark.parametrize("roots", [[-2.0, 0.5, 1.5, 3.0], [-1.0, 0.25, 1.75, 2.5, 4.0]])
def test_roots_higher_degree(roots):
    factors = "*".join(f"(x - {r})" for r in roots)
    result = evaluate_cell(f"f(x) = {factors}\nroots(f(x), x, -5, 5)")
    assert_close_sequence(characteristic_xs(result), sorted(roots), rel_tol=1e-5)


@pytest.mark.parametrize("exponent", [-9, -3, 3, 9])
def test_roots_extreme_scales(exponent):
    result = evaluate_cell(
        f"f(x) = 1e{exponent}*(x - 1.5)*(x + 1.0)\nroots(f(x), x, -5, 5)"
    )
    assert_close_sequence(characteristic_xs(result), [-1.0, 1.5])


# --------------------------------------------------------------------------
# domain boundaries
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("r", "lo", "hi"), [(1.25, 1.25, 4.0), (3.5, 0.0, 3.5)])
def test_root_exactly_on_domain_bound(r, lo, hi):
    result = evaluate_cell(f"f(x) = (x - {r})\nroots(f(x), x, {lo}, {hi})")
    assert_close_sequence(characteristic_xs(result), [r])


def test_root_outside_domain_is_excluded():
    result = evaluate_cell("f(x) = (x - 7.5)\nroots(f(x), x, 0, 5)")
    assert characteristic_xs(result) == []


# --------------------------------------------------------------------------
# intersections
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("expected", "shift"),
    [
        ([1.0], 2.0),
        ([1.0, 3.0], 2.0),
        ([-1.5, 2.25], -2.0),
    ],
)
def test_intersections_from_known_difference(expected, shift):
    difference = "*".join(f"(x - {r})" for r in expected)
    result = evaluate_cell(
        f"f(x) = {shift}*x + 1\n"
        f"g(x) = {shift}*x + 1 + 1.5*{difference}\n"
        "intersections(f(x), g(x), x, -5, 5)"
    )
    assert_close_sequence(characteristic_xs(result), sorted(expected), rel_tol=1e-5)


@pytest.mark.parametrize("r", [-1.5, 2.0])
def test_intersections_tangency(r):
    result = evaluate_cell(
        f"f(x) = 1.5*(x - {r})^2\ng(x) = 0*x\nintersections(f(x), g(x), x, -5, 5)"
    )
    assert_close_sequence(characteristic_xs(result), [r])


# --------------------------------------------------------------------------
# extrema
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("v", "k", "c"), [(1.25, 2.0, 3.0), (-2.5, 0.75, -1.0)])
def test_extrema_known_interior_maximum(v, k, c):
    result = evaluate_cell(f"f(x) = -{k}*(x - {v})^2 + {c}\nextrema(f(x), x, -5, 5)")
    assert_close_sequence(role_xs(result, "global_max"), [v], abs_tol=1e-9)


@pytest.mark.parametrize(("v", "k", "c"), [(0.75, 1.5, -2.0), (-1.5, 3.0, 1.0)])
def test_extrema_known_interior_minimum(v, k, c):
    """New Level A coverage: the audit only exercised minima metamorphically."""
    result = evaluate_cell(f"f(x) = {k}*(x - {v})^2 + {c}\nextrema(f(x), x, -5, 5)")
    assert_close_sequence(role_xs(result, "global_min"), [v], abs_tol=1e-9)


@pytest.mark.parametrize(("k", "lo", "hi"), [(2.0, 0.0, 4.0), (-2.0, 0.0, 4.0)])
def test_extrema_at_domain_boundaries(k, lo, hi):
    """New Level A coverage: a monotone response has unambiguous boundary roles."""
    result = evaluate_cell(f"f(x) = {k}*x + 1.0\nextrema(f(x), x, {lo}, {hi})")
    expected_max, expected_min = (hi, lo) if k > 0 else (lo, hi)
    assert_close_sequence(role_xs(result, "global_max"), [expected_max], abs_tol=1e-9)
    assert_close_sequence(role_xs(result, "global_min"), [expected_min], abs_tol=1e-9)


@pytest.mark.evidence_c
@pytest.mark.parametrize(("v", "k"), [(1.0, 2.0), (-1.75, 0.5)])
def test_extrema_sign_flip_swaps_roles(v, k):
    upward = evaluate_cell(f"f(x) = {k}*(x - {v})^2\nextrema(f(x), x, -5, 5)")
    downward = evaluate_cell(f"f(x) = -{k}*(x - {v})^2\nextrema(f(x), x, -5, 5)")
    assert role_xs(upward, "global_min") == role_xs(downward, "global_max")


# --------------------------------------------------------------------------
# Piecewise
# --------------------------------------------------------------------------


@pytest.mark.parametrize("operator", ["<", "<=", ">", ">="])
def test_piecewise_continuous_root_at_breakpoint(operator):
    breakpoint_value = 2.5
    if operator in ("<", "<="):
        body = f"piecewise(x - {breakpoint_value}, x {operator} a, 2*(x - {breakpoint_value}))"
    else:
        body = f"piecewise(2*(x - {breakpoint_value}), x {operator} a, x - {breakpoint_value})"
    result = evaluate_cell(f"a := {breakpoint_value}\ng(x) = {body}\nroots(g(x), x, 0, 6)")
    assert_close_sequence(characteristic_xs(result), [breakpoint_value], abs_tol=1e-9)


@pytest.mark.parametrize("operator", ["<", ">="])
def test_piecewise_jump_is_never_a_root(operator):
    result = evaluate_cell(
        f"a := 3.0\np1 := 1\np2 := -1\n"
        f"f(x) = piecewise(p1, x {operator} a, p2)\nroots(f(x), x, 0, 6)"
    )
    assert characteristic_xs(result) == []


def test_piecewise_breakpoint_equals_upper_bound():
    """A-2 family: the open edge must expose its one-sided limit and no false max."""
    result = evaluate_cell(
        "a := 3.0\ns(x) = piecewise(x, x < a, x - a)\nextrema(s(x), x, 0, a)"
    )
    left = [p for p in result.points if p.side == "left"]
    assert len(left) == 1
    assert abs(float(left[0].value_quantity.magnitude) - 3.0) < 1e-9
    attained = [p for p in result.points if p.side == "at"]
    assert not any("global_max" in p.roles for p in attained)


def test_piecewise_breakpoint_equals_lower_bound():
    result = evaluate_cell(
        "a := 3.0\ns(x) = piecewise(x, x < a, x - a)\nextrema(s(x), x, a, 6)"
    )
    assert_close_sequence(role_xs(result, "global_max"), [6.0], abs_tol=1e-9)
    assert_close_sequence(role_xs(result, "global_min"), [3.0], abs_tol=1e-9)


@pytest.mark.parametrize(("high", "low"), [(1, -1), (5, 2)])
def test_piecewise_interval_roles_around_jump(high, low):
    result = evaluate_cell(
        f"a := 3.0\np1 := {high}\np2 := {low}\n"
        f"f(x) = piecewise(p1, x < a, p2)\nextrema(f(x), x, 0, 6)"
    )
    by_role = {
        interval.role: float(interval.value_quantity.magnitude)
        for interval in result.intervals
        if interval.value_quantity is not None
    }
    assert by_role.get("global_max") == max(high, low)
    assert by_role.get("global_min") == min(high, low)


# --------------------------------------------------------------------------
# units, dimensional zero, matrix
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("q", "length", "target"), [(12.0, 6.0, 2.5), (4.5, 8.0, 6.0)])
def test_roots_with_units(q, length, target):
    result = evaluate_cell(
        f"q := {q}*kN/m\nL := {length}*m\nxr := {target}*m\n"
        "V(x) = q*(x - xr)\nroots(V(x), x, 0, L)"
    )
    assert_close_sequence(characteristic_xs(result), [target], abs_tol=1e-9)


@pytest.mark.parametrize(("q", "length"), [(12.0, 6.0)])
def test_dimensional_zero_offset(q, length):
    result = evaluate_cell(
        f"q := {q}*kN/m\nL := {length}*m\nM(x) = q*x*(L-x)/2\n"
        "roots(M(x) - 0*kN*m, x, 0, L)"
    )
    assert_close_sequence(characteristic_xs(result), [0.0, length], abs_tol=1e-9)


@pytest.mark.evidence_c
def test_metre_millimetre_equivalence():
    in_metres = evaluate_cell(
        "q := 12.0*kN/m\nL := 6.0*m\nV(x) = q*(L/2 - x)\nroots(V(x), x, 0, L)"
    )
    in_millimetres = evaluate_cell(
        "q := 12.0*kN/m\nL := 6000.0*mm\nV(x) = q*(L/2 - x)\nroots(V(x), x, 0, L)"
    )
    assert_close_sequence(
        characteristic_xs(in_metres, "m"),
        characteristic_xs(in_millimetres, "m"),
        abs_tol=1e-12,
    )


@pytest.mark.parametrize(("length", "offset"), [(6.0, 1.5), (4.0, 2.5)])
def test_indexed_matrix_scalar_response(length, offset):
    result = evaluate_cell(
        f"L := {length}*m\nt := {offset}*m\n"
        "K(x) = [x + L, 0; 0, 2*x + L]\n"
        "roots(K(x)[1,1] - L - t, x, 0, L)"
    )
    assert_close_sequence(characteristic_xs(result), [offset], abs_tol=1e-9)


# --------------------------------------------------------------------------
# H4-A: symbolically incomplete factor with an independently known root
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "c"),
    [
        (0.5, 2.0, 1.0),
        (-1.25, 3.0, -4.0),
        (2.0, 1.5, 2.0),
        (-2.0, 4.0, 5.0),
    ],
)
def test_partial_symbolic_polynomial_keeps_numeric_fallback(a, b, c):
    """The quintic stays symbolically unresolved, so the fallback must recover it.

    Its root count is proved by monotonicity and its location by bisection; no
    symbolic solver participates in forming the expectation.
    """
    difficult_root = bisect_monotone_quintic(b, c)
    result = evaluate_cell(
        f"a := {a}\nb := {b}\n"
        f"f(x) = (x - a)*(x^5 + b*x + {c})\n"
        "roots(f(x), x, -5, 5)"
    )
    assert_close_sequence(
        characteristic_xs(result),
        sorted([a, difficult_root]),
        rel_tol=1e-8,
        abs_tol=1e-8,
    )
