"""Deep Property Gate — generated Level A coverage for `intersections(...)`."""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quality_tests.deep.strategies import (
    lead_coefficient,
    offset,
    root_value,
    sufficiently_separated,
)
from quality_tests.helpers import (
    assert_close_sequence,
    characteristic_xs,
    evaluate_cell,
)

pytestmark = [pytest.mark.evidence_a, pytest.mark.quality_deep]


@settings(max_examples=80)
@given(
    coeff=lead_coefficient,
    crossings=st.lists(root_value, min_size=1, max_size=2, unique=True),
    shift=offset,
)
def test_intersections_from_known_difference(coeff, crossings, shift):
    """The two responses differ by a factored polynomial with chosen roots."""
    assume(sufficiently_separated(crossings))
    difference = "*".join(f"(x - {r})" for r in crossings)
    result = evaluate_cell(
        f"f(x) = {shift}*x + 1\n"
        f"g(x) = {shift}*x + 1 + {coeff}*{difference}\n"
        "intersections(f(x), g(x), x, -5, 5)"
    )
    assert_close_sequence(
        characteristic_xs(result), sorted(crossings), rel_tol=1e-5
    )


@settings(max_examples=60)
@given(coeff=lead_coefficient, r=root_value)
def test_tangential_contact(coeff, r):
    result = evaluate_cell(
        f"f(x) = {coeff}*(x - {r})^2\ng(x) = 0*x\n"
        "intersections(f(x), g(x), x, -5, 5)"
    )
    assert_close_sequence(characteristic_xs(result), [r])
