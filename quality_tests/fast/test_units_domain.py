"""Fast Gate — Level A coverage for unit-aware and domain-edge characteristics.

Unit literals appear both in the response and in the domain bounds, because the
release history contains a defect for each: a literal in the response silently
produced an empty extrema result, and unit literals in bounds were rejected in
some APIs while accepted in others.
"""

from __future__ import annotations

import pytest

from quality_tests.helpers import (
    assert_close_sequence,
    characteristic_xs,
    evaluate_cell,
    role_xs,
)

# Evidence level is declared per test: this module mixes authoritative
# Level A constructive cases with complementary Level C ones, and a module
# marker would make the complementary tests count as Level A too.


# --------------------------------------------------------------------------
# unit-aware responses
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("load", "length", "target"),
    [
        (12.0, 6.0, 2.5),
        (4.5, 8.0, 6.0),
        (25.0, 3.5, 0.75),
        (7.25, 10.0, 9.5),
    ],
)
@pytest.mark.evidence_a
def test_unit_aware_root_location(load, length, target):
    result = evaluate_cell(
        f"q := {load}*kN/m\nL := {length}*m\nxr := {target}*m\n"
        "V(x) = q*(x - xr)\nroots(V(x), x, 0, L)"
    )
    assert_close_sequence(characteristic_xs(result, "m"), [target], abs_tol=1e-9)


@pytest.mark.parametrize(("load", "length"), [(12.0, 6.0), (4.0, 9.0)])
@pytest.mark.evidence_a
def test_unit_aware_extremum_of_a_simply_supported_moment(load, length):
    """The classic parabola: peak at midspan with value q*L^2/8."""
    result = evaluate_cell(
        f"q := {load}*kN/m\nL := {length}*m\nM(x) = q*x*(L-x)/2\n"
        "extrema(M(x), x, 0, L)"
    )
    peak = [point for point in result.points if "global_max" in point.roles]
    assert len(peak) == 1
    assert peak[0].x_quantity.to("m").magnitude == pytest.approx(length / 2)
    assert peak[0].value_quantity.to("kN*m").magnitude == pytest.approx(
        load * length**2 / 8
    )


@pytest.mark.parametrize("bound_literal", ["6*m", "6000*mm"])
@pytest.mark.evidence_a
def test_unit_literals_are_accepted_in_domain_bounds(bound_literal):
    """A literal bound must be resolvable, not only a registered parameter."""
    result = evaluate_cell(
        f"q := 12*kN/m\nV(x) = q*(3*m - x)\nroots(V(x), x, 0, {bound_literal})"
    )
    assert_close_sequence(characteristic_xs(result, "m"), [3.0], abs_tol=1e-9)


# --------------------------------------------------------------------------
# dimensional zero
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("load", "length"), [(12.0, 6.0), (18.0, 4.0)])
@pytest.mark.evidence_a
def test_dimensional_zero_offset_matches_the_bare_response(load, length):
    """Subtracting a dimensional zero must not change the answer."""
    setup = f"q := {load}*kN/m\nL := {length}*m\nM(x) = q*x*(L-x)/2\n"
    bare = evaluate_cell(setup + "roots(M(x), x, 0, L)")
    offset = evaluate_cell(setup + "roots(M(x) - 0*kN*m, x, 0, L)")
    assert_close_sequence(
        characteristic_xs(bare, "m"), [0.0, length], abs_tol=1e-9
    )
    assert_close_sequence(
        characteristic_xs(offset, "m"), characteristic_xs(bare, "m"), abs_tol=1e-12
    )


@pytest.mark.evidence_a
def test_identically_zero_response_is_reported_as_an_interval():
    result = evaluate_cell("z(x) = 0*x\nroots(z(x), x, 0, 4)")
    assert characteristic_xs(result) == []
    assert len(result.intervals) == 1
    assert result.intervals[0].role == "roots"


# --------------------------------------------------------------------------
# domain edges with units
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("target", "lo", "hi"), [(2.0, 2.0, 6.0), (5.0, 1.0, 5.0)])
@pytest.mark.evidence_a
def test_unit_aware_root_on_a_domain_bound(target, lo, hi):
    result = evaluate_cell(
        f"q := 10*kN/m\nxr := {target}*m\nV(x) = q*(x - xr)\n"
        f"roots(V(x), x, {lo}*m, {hi}*m)"
    )
    assert_close_sequence(characteristic_xs(result, "m"), [target], abs_tol=1e-9)


@pytest.mark.evidence_a
def test_unit_aware_root_outside_the_domain_is_excluded():
    result = evaluate_cell(
        "q := 10*kN/m\nxr := 9*m\nV(x) = q*(x - xr)\nroots(V(x), x, 0*m, 5*m)"
    )
    assert characteristic_xs(result) == []


@pytest.mark.evidence_a
def test_incompatible_response_dimensions_are_rejected():
    """A moment and a shear cannot intersect; that must be an error, not a point."""
    from engcalc_colab.errors import EngEvaluationError

    with pytest.raises(EngEvaluationError):
        evaluate_cell(
            "L := 6*m\nq := 12*kN/m\nM(x) = q*x*(L-x)/2\nV(x) = q*(L/2 - x)\n"
            "intersections(M(x), V(x), x, 0, L)"
        )


# --------------------------------------------------------------------------
# metamorphic: unit system must not move a physical point
# --------------------------------------------------------------------------


@pytest.mark.evidence_c
@pytest.mark.parametrize(("load", "length"), [(12.0, 6.0), (4.5, 8.0)])
def test_metre_millimetre_equivalence(load, length):
    """Complementary evidence: same problem, two unit systems, same location."""
    in_metres = evaluate_cell(
        f"q := {load}*kN/m\nL := {length}*m\nV(x) = q*(L/2 - x)\n"
        "roots(V(x), x, 0, L)"
    )
    in_millimetres = evaluate_cell(
        f"q := {load}*kN/m\nL := {length * 1000}*mm\nV(x) = q*(L/2 - x)\n"
        "roots(V(x), x, 0, L)"
    )
    assert_close_sequence(
        characteristic_xs(in_metres, "m"),
        characteristic_xs(in_millimetres, "m"),
        abs_tol=1e-12,
    )


@pytest.mark.evidence_c
def test_extrema_roles_survive_a_unit_change():
    in_metres = evaluate_cell(
        "q := 12*kN/m\nL := 6*m\nM(x) = q*x*(L-x)/2\nextrema(M(x), x, 0, L)"
    )
    in_millimetres = evaluate_cell(
        "q := 12*kN/m\nL := 6000*mm\nM(x) = q*x*(L-x)/2\nextrema(M(x), x, 0, L)"
    )
    assert_close_sequence(
        role_xs(in_metres, "global_max", "m"),
        role_xs(in_millimetres, "global_max", "m"),
        abs_tol=1e-12,
    )
