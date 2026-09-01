"""Deep Property Gate — generated coverage for unit-aware characteristics."""

from __future__ import annotations

import pytest
from hypothesis import given, settings

from quality_tests.deep.strategies import distributed_load, span_length
from quality_tests.helpers import (
    assert_close_sequence,
    characteristic_xs,
    evaluate_cell,
)

pytestmark = pytest.mark.quality_deep


@pytest.mark.evidence_a
@settings(max_examples=60)
@given(load=distributed_load, length=span_length)
def test_unit_aware_shear_root_at_midspan(load, length):
    """V(x) = q*(L/2 - x) vanishes at midspan whatever the units carried."""
    result = evaluate_cell(
        f"q := {load}*kN/m\nL := {length}*m\nV(x) = q*(L/2 - x)\n"
        "roots(V(x), x, 0, L)"
    )
    assert_close_sequence(
        characteristic_xs(result, "m"), [length / 2], abs_tol=1e-9
    )


@pytest.mark.evidence_c
@settings(max_examples=60)
@given(load=distributed_load, length=span_length)
def test_metre_millimetre_equivalence(load, length):
    """Complementary evidence: the unit system must not move a physical point."""
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
