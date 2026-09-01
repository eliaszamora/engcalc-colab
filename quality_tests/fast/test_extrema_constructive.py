"""Fast Gate — Level A constructive coverage for `extrema(...)`.

Interior extrema come from parabolas whose vertex is chosen in advance. Boundary
extrema use a monotone response, so the roles at each end are unambiguous without
introducing interior critical points that would blur the assertion.

The interior-minimum and boundary families are new Level A coverage added by this
gate: the property-based audit exercised minima only metamorphically, and never
exercised boundary roles as a family of their own.
"""

from __future__ import annotations

import pytest

from quality_tests.helpers import (
    assert_close_sequence,
    evaluate_cell,
    role_xs,
)

# Evidence level is declared per test: this module mixes authoritative
# Level A constructive cases with complementary Level C ones, and a module
# marker would make the complementary tests count as Level A too.


@pytest.mark.parametrize(
    ("vertex", "curvature", "offset"),
    [
        (1.25, 2.0, 3.0),
        (-2.5, 0.75, -1.0),
        (0.0, 4.5, 0.5),
        (3.75, 1.25, -2.25),
    ],
)
@pytest.mark.evidence_a
def test_known_interior_maximum(vertex, curvature, offset):
    result = evaluate_cell(
        f"f(x) = -{curvature}*(x - {vertex})^2 + {offset}\nextrema(f(x), x, -5, 5)"
    )
    assert_close_sequence(role_xs(result, "global_max"), [vertex], abs_tol=1e-9)


@pytest.mark.parametrize(
    ("vertex", "curvature", "offset"),
    [
        (0.75, 1.5, -2.0),
        (-1.5, 3.0, 1.0),
        (2.25, 0.5, 0.0),
        (-3.5, 2.75, 4.0),
    ],
)
@pytest.mark.evidence_a
def test_known_interior_minimum(vertex, curvature, offset):
    """New Level A coverage: the audit only reached minima through sign-flip."""
    result = evaluate_cell(
        f"f(x) = {curvature}*(x - {vertex})^2 + {offset}\nextrema(f(x), x, -5, 5)"
    )
    assert_close_sequence(role_xs(result, "global_min"), [vertex], abs_tol=1e-9)


@pytest.mark.parametrize(
    ("slope", "lo", "hi"),
    [
        (2.0, 0.0, 4.0),
        (-2.0, 0.0, 4.0),
        (0.75, -3.0, 1.5),
        (-1.25, -3.0, 1.5),
    ],
)
@pytest.mark.evidence_a
def test_extrema_at_domain_boundaries(slope, lo, hi):
    """New Level A coverage: a monotone response puts both roles on the bounds."""
    result = evaluate_cell(f"f(x) = {slope}*x + 1.0\nextrema(f(x), x, {lo}, {hi})")
    expected_max, expected_min = (hi, lo) if slope > 0 else (lo, hi)
    assert_close_sequence(role_xs(result, "global_max"), [expected_max], abs_tol=1e-9)
    assert_close_sequence(role_xs(result, "global_min"), [expected_min], abs_tol=1e-9)


@pytest.mark.parametrize(("lo", "hi"), [(0.0, 4.0), (-2.5, 1.0)])
@pytest.mark.evidence_a
def test_constant_response_is_reported_as_an_interval(lo, hi):
    """A constant attains its extremes everywhere, which is an interval fact."""
    result = evaluate_cell(f"f(x) = 3.5 + 0*x\nextrema(f(x), x, {lo}, {hi})")
    assert result.points == ()
    assert len(result.intervals) == 1
    assert result.intervals[0].role == "global_max_min"


@pytest.mark.evidence_c
@pytest.mark.parametrize(("vertex", "curvature"), [(1.0, 2.0), (-1.75, 0.5), (3.0, 1.25)])
def test_sign_flip_swaps_global_extrema_roles(vertex, curvature):
    """Complementary metamorphic evidence, not counted toward Level A coverage.

    An invariance like this can stay green while both executions share the same
    systematic omission, which is why it does not substitute for the constructive
    minimum family above.
    """
    upward = evaluate_cell(
        f"f(x) = {curvature}*(x - {vertex})^2\nextrema(f(x), x, -5, 5)"
    )
    downward = evaluate_cell(
        f"f(x) = -{curvature}*(x - {vertex})^2\nextrema(f(x), x, -5, 5)"
    )
    assert role_xs(upward, "global_min") == role_xs(downward, "global_max")
