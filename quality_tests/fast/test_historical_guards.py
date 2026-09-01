"""Fast Gate — permanent guards for families with a demonstrated defect history.

Each guard corresponds to a defect that reached a released state. They live in one
file so that a future reviewer can see, in one place, exactly which historical
failures the gate is contracted to keep out.

Sensitivity evidence for these guards is recorded in the project context: a guard
that cannot fail against the state it exists to catch is not a guard. An import or
collection error is never accepted as that evidence.
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
# H4-A — symbolically incomplete factor with an independently known root
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "c"),
    [
        (0.5, 2.0, 1.0),
        (-1.25, 3.0, -4.0),
        (2.0, 1.5, 2.0),
        (-2.0, 4.0, 5.0),
        (1.75, 0.5, -2.5),
        (-0.75, 6.0, 3.0),
    ],
)
def test_partial_symbolic_polynomial_keeps_numeric_fallback(a, b, c):
    """`solve()` exposes only the easy factor, so the fallback must recover the rest.

    With ``b > 0`` the quintic derivative ``5*x**4 + b`` is strictly positive, so
    the quintic is strictly increasing and has exactly one real root. That count is
    established by calculus and the location by bisection, so neither side of the
    comparison uses the solver under test.

    This is the replacement for the audit's H4, whose expected root came from
    ``sp.solveset`` and therefore shared machinery with EngCalc. An earlier
    candidate replacement embedded the root in the coefficients, which let SymPy
    factor it out and left the guard green against the very implementation it
    existed to catch.
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


# --------------------------------------------------------------------------
# A-1 — complex candidates must not surface as an internal error
# --------------------------------------------------------------------------


def test_a1_registered_parameter_matches_literal_control():
    """The same function must behave identically with a literal and a parameter.

    Before the correction the parameterized form raised a Python ``TypeError``
    from ``float()`` on a complex magnitude, while the literal form answered
    correctly. The disagreement between the two is the defect.
    """
    literal = evaluate_cell("f(x) = x^2 + 1\nroots(f(x), x, -2, 2)")
    parameterized = evaluate_cell("a := 1\nf(x) = x^2 + a\nroots(f(x), x, -2, 2)")
    assert characteristic_xs(parameterized) == characteristic_xs(literal) == []


def test_a1_unit_aware_response_that_never_reaches_the_level():
    """Asking where a response reaches a value it never reaches is a valid query."""
    result = evaluate_cell(
        "L := 6*m\nq := 12*kN/m\nM(x) = q*x*(L-x)/2\n"
        "roots(M(x) + 1*kN*m, x, 0, L)"
    )
    assert characteristic_xs(result) == []


def test_a1_intersections_with_registered_parameter():
    result = evaluate_cell(
        "k := 5\nh(x) = k + x^2\nintersections(h(x), 0*x, x, -3, 3)"
    )
    assert characteristic_xs(result) == []


# --------------------------------------------------------------------------
# A-2 — open region edge coinciding with a domain bound
# --------------------------------------------------------------------------


def test_a2_left_limit_is_reported_when_breakpoint_is_the_upper_bound():
    """The supremum is approached and never attained, so it must not be a maximum.

    Before the correction both endpoints were labelled ``global_max`` with value
    zero, contradicted by ``s(2 m) = 2 m``.
    """
    result = evaluate_cell(
        "a := 3*m\ns(x) = piecewise(x, x < a, x - a)\nextrema(s(x), x, 0, a)"
    )

    left = [point for point in result.points if point.side == "left"]
    assert len(left) == 1
    assert left[0].x_quantity.to("m").magnitude == pytest.approx(3.0)
    assert left[0].value_quantity.to("m").magnitude == pytest.approx(3.0)

    attained = [point for point in result.points if point.side == "at"]
    assert attained
    assert not any("global_max" in point.roles for point in attained)
    assert any("global_min" in point.roles for point in attained)


def test_a2_interior_breakpoint_behaviour_is_unchanged():
    """Control: with the breakpoint inside the domain the maximum is attained."""
    result = evaluate_cell(
        "a := 3*m\nL := 6*m\ns(x) = piecewise(x, x < a, x - a)\n"
        "extrema(s(x), x, 0, L)"
    )
    assert_close_sequence(role_xs(result, "global_max", "m"), [6.0], abs_tol=1e-9)


def test_a2_non_strict_breakpoint_still_attains_its_maximum():
    """Control: with `<=` the endpoint belongs to the rising branch."""
    result = evaluate_cell(
        "a := 3*m\ns(x) = piecewise(x, x <= a, x - a)\nextrema(s(x), x, 0, a)"
    )
    peak = [point for point in result.points if "global_max" in point.roles]
    assert len(peak) == 1
    assert peak[0].value_quantity.to("m").magnitude == pytest.approx(3.0)


def test_a2_interior_extremum_inside_the_open_region_is_preserved():
    """Control: the open region's interior maximum was never the defect."""
    result = evaluate_cell(
        "a := 4*m\nq := 12*kN/m\n"
        "M(x) = piecewise(q*x*(a-x)/2, x < a, 0*kN*m)\n"
        "extrema(M(x), x, 0, a)"
    )
    peak = [point for point in result.points if "global_max" in point.roles]
    assert len(peak) == 1
    assert peak[0].x_quantity.to("m").magnitude == pytest.approx(2.0)
    assert peak[0].value_quantity.to("kN*m").magnitude == pytest.approx(24.0)


# --------------------------------------------------------------------------
# N-2 — floating-point residual must not disqualify a genuine root
# --------------------------------------------------------------------------


@pytest.mark.parametrize("epsilon", [1e-6, 1e-9, 1e-12])
def test_n2_near_double_root_is_not_rejected_by_roundoff(epsilon):
    """Both roots are real and well separated; the residual is float noise.

    An exact-equality zero test discarded them, because ``simplify`` leaves a
    residue of order 1e-21 that is not literally ``0.0``.
    """
    offset = epsilon**0.5
    result = evaluate_cell(f"f(x) = (x - 1)^2 - {epsilon}\nroots(f(x), x, 0, 2)")
    assert_close_sequence(
        characteristic_xs(result),
        [1.0 - offset, 1.0 + offset],
        rel_tol=1e-6,
        abs_tol=1e-9,
    )


@pytest.mark.parametrize("epsilon", [1e-6, 1e-12])
def test_n2_near_miss_parabola_has_no_roots(epsilon):
    """The mirror guard: a response that approaches zero must not gain a root."""
    result = evaluate_cell(f"f(x) = (x - 1)^2 + {epsilon}\nroots(f(x), x, 0, 2)")
    assert characteristic_xs(result) == []


# --------------------------------------------------------------------------
# N-3 — unit literals must resolve on every evaluation path
# --------------------------------------------------------------------------


def test_n3_roots_resolve_unit_literals_in_the_response():
    result = evaluate_cell(
        "L := 6*m\nq := 12*kN/m\nV(x) = q*(L/2 - x)\n"
        "roots(V(x) - 6*kN, x, 0, L)"
    )
    assert_close_sequence(characteristic_xs(result, "m"), [2.5], abs_tol=1e-9)


def test_n3_extrema_resolve_unit_literals_in_the_response():
    """This path returned an empty result in silence, which is worse than an error."""
    result = evaluate_cell(
        "L := 6*m\nq := 12*kN/m\nM(x) = q*x*(L-x)/2\n"
        "extrema(M(x) - 20*kN*m, x, 0, L)"
    )
    assert len(result.points) == 3
    peak = [point for point in result.points if "global_max" in point.roles]
    assert len(peak) == 1
    assert peak[0].x_quantity.to("m").magnitude == pytest.approx(3.0)
    assert peak[0].value_quantity.to("kN*m").magnitude == pytest.approx(34.0)


def test_n3_intersections_resolve_unit_literals_in_the_response():
    result = evaluate_cell(
        "L := 6*m\nq := 12*kN/m\nM(x) = q*x*(L-x)/2\n"
        "intersections(M(x), 20*kN*m + 0*x, x, 0, L)"
    )
    assert_close_sequence(
        characteristic_xs(result, "m"),
        [0.6195238572, 5.380476143],
        rel_tol=1e-8,
    )
