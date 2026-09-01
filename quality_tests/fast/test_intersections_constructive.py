"""Fast Gate — Level A constructive coverage for `intersections(...)`.

Crossovers are built by adding a factored difference to a base response, so the
crossing abscissae are the chosen roots of that difference. The expectation is
never recomputed afterwards with SymPy.
"""

from __future__ import annotations

import pytest

from quality_tests.helpers import (
    assert_close_sequence,
    characteristic_xs,
    evaluate_cell,
)

pytestmark = pytest.mark.evidence_a


@pytest.mark.parametrize(
    ("crossings", "shift", "scale"),
    [
        # one crossover, positive and negative response shift
        ([1.0], 2.0, 1.5),
        ([-2.25], -2.0, 0.75),
        # multiple crossovers, both shift signs
        ([1.0, 3.0], 2.0, 1.5),
        ([-1.5, 2.25], -2.0, 1.0),
        ([-3.5, 0.25, 2.75], 1.25, -0.5),
        # ordinary decimal coefficients
        ([0.375, 4.125], -1.75, 2.25),
    ],
)
def test_intersections_from_known_difference(crossings, shift, scale):
    """f and g differ by a factored polynomial whose roots are chosen in advance."""
    difference = "*".join(f"(x - {r})" for r in crossings)
    result = evaluate_cell(
        f"f(x) = {shift}*x + 1\n"
        f"g(x) = {shift}*x + 1 + {scale}*{difference}\n"
        "intersections(f(x), g(x), x, -5, 5)"
    )
    assert_close_sequence(
        characteristic_xs(result), sorted(crossings), rel_tol=1e-5
    )


@pytest.mark.parametrize(("r", "scale"), [(-1.5, 1.5), (2.0, 0.5), (0.0, 3.25)])
def test_intersections_tangency(r, scale):
    """Contact without crossing: the difference has an even-multiplicity root."""
    result = evaluate_cell(
        f"f(x) = {scale}*(x - {r})^2\n"
        "g(x) = 0*x\n"
        "intersections(f(x), g(x), x, -5, 5)"
    )
    assert_close_sequence(characteristic_xs(result), [r])


@pytest.mark.parametrize("separation", [4.0, 0.5])
def test_parallel_responses_never_intersect(separation):
    """Guard against fabricated crossings when none exist."""
    result = evaluate_cell(
        f"f(x) = 2.0*x + 1\ng(x) = 2.0*x + 1 + {separation}\n"
        "intersections(f(x), g(x), x, -5, 5)"
    )
    assert characteristic_xs(result) == []


def test_coincident_responses_report_an_interval():
    """Identical responses overlap everywhere; that is an interval, not a point."""
    result = evaluate_cell(
        "f(x) = 2.0*x + 1\ng(x) = 2.0*x + 1\nintersections(f(x), g(x), x, 0, 4)"
    )
    assert characteristic_xs(result) == []
    assert len(result.intervals) == 1
    assert result.intervals[0].role == "coincident"
