"""Deep Property Gate — Level A coverage for `governing(...)`.

Two straight lines are built from a crossover point chosen in advance, so where the
answer must change is known before EngCalc runs, and so is which response is larger on
each side. Nothing here asks the solver what it should have said.

`governing` is how a load combination is read off an envelope, and it has had example
contracts only since 0.19.0.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quality_tests.helpers import evaluate_cell

pytestmark = [pytest.mark.evidence_a, pytest.mark.quality_deep]

_SPAN = 6.0
_CROSSOVER = st.integers(min_value=60, max_value=540).map(lambda n: n / 100)
_SLOPE = st.integers(min_value=10, max_value=300).map(lambda n: n / 100)


def _labels_and_bounds(result):
    return [
        (
            interval.label,
            float(interval.lower_quantity.magnitude),
            float(interval.upper_quantity.magnitude),
        )
        for interval in result.intervals
    ]


@settings(max_examples=60)
@given(crossover=_CROSSOVER, rise=_SLOPE, fall=_SLOPE)
def test_the_boundary_sits_where_the_two_responses_are_equal(crossover, rise, fall):
    """`A` rises through the crossover and `B` falls through it, so they meet there.

    `A(x) = rise*(x - c)` and `B(x) = fall*(c - x)` are both zero at `c` and have
    opposite slopes, so `B` is larger before it and `A` after. The boundary is `c` by
    construction, not by asking.
    """
    assume(0.4 < crossover < _SPAN - 0.4)

    result = evaluate_cell(
        f"L := {_SPAN}*m\n"
        f"A(x) = {rise}*(x - {crossover}*m)\n"
        f"B(x) = {fall}*({crossover}*m - x)\n"
        "governing(A(x), B(x), x, 0, L)"
    )
    intervals = _labels_and_bounds(result)

    assert len(intervals) == 2, intervals
    assert intervals[0][0] == "B(x)"
    assert intervals[1][0] == "A(x)"
    assert intervals[0][2] == pytest.approx(crossover, abs=1e-6)
    assert intervals[1][1] == pytest.approx(crossover, abs=1e-6)


@settings(max_examples=60)
@given(rise=_SLOPE, factor=st.integers(min_value=110, max_value=400).map(lambda n: n / 100))
def test_a_response_larger_everywhere_governs_the_whole_span(rise, factor):
    """No crossover, so no boundary.

    A report split into two intervals would mean the search invented a boundary where
    the responses only touch, which is what happens at a support and is not a crossover.
    """
    result = evaluate_cell(
        f"L := {_SPAN}*m\n"
        f"A(x) = {rise * factor}*x*(L - x)\n"
        f"B(x) = {rise}*x*(L - x)\n"
        "governing(A(x), B(x), x, 0, L)"
    )
    intervals = _labels_and_bounds(result)

    assert len(intervals) == 1, intervals
    assert intervals[0][0] == "A(x)"
    assert intervals[0][1] == pytest.approx(0.0, abs=1e-9)
    assert intervals[0][2] == pytest.approx(_SPAN, abs=1e-9)


@settings(max_examples=40)
@given(crossover=_CROSSOVER, rise=_SLOPE, fall=_SLOPE)
def test_the_intervals_cover_the_span_without_gap_or_overlap(crossover, rise, fall):
    """Every point of the span is governed by exactly one response.

    A gap leaves a stretch of beam with no combination attached to it; an overlap says
    two govern the same stretch. Both are silent in a report that names the right labels
    at the right ends, which the property above checks and this does not duplicate.
    """
    assume(0.4 < crossover < _SPAN - 0.4)

    result = evaluate_cell(
        f"L := {_SPAN}*m\n"
        f"A(x) = {rise}*(x - {crossover}*m)\n"
        f"B(x) = {fall}*({crossover}*m - x)\n"
        "governing(A(x), B(x), x, 0, L)"
    )
    intervals = sorted(_labels_and_bounds(result), key=lambda item: item[1])

    assert intervals[0][1] == pytest.approx(0.0, abs=1e-9)
    assert intervals[-1][2] == pytest.approx(_SPAN, abs=1e-9)
    for left, right in zip(intervals, intervals[1:]):
        assert left[2] == pytest.approx(right[1], abs=1e-6), intervals
