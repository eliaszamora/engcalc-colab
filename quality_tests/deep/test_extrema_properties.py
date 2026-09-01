"""Deep Property Gate — generated coverage for `extrema(...)`.

The maximum and minimum families are Level A: the vertex is chosen before EngCalc
runs. The sign-flip property is Level C and marked as such, because it compares two
EngCalc runs against each other and could stay green while both share the same
omission.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings

from quality_tests.deep.strategies import curvature, offset, root_value
from quality_tests.helpers import assert_close_sequence, evaluate_cell, role_xs

pytestmark = pytest.mark.quality_deep


@pytest.mark.evidence_a
@settings(max_examples=60)
@given(vertex=root_value, k=curvature, c=offset)
def test_known_interior_maximum(vertex, k, c):
    result = evaluate_cell(f"f(x) = -{k}*(x - {vertex})^2 + {c}\nextrema(f(x), x, -5, 5)")
    assert_close_sequence(role_xs(result, "global_max"), [vertex], abs_tol=1e-9)


@pytest.mark.evidence_a
@settings(max_examples=60)
@given(vertex=root_value, k=curvature, c=offset)
def test_known_interior_minimum(vertex, k, c):
    """New Level A coverage: the audit reached minima only through sign-flip."""
    result = evaluate_cell(f"f(x) = {k}*(x - {vertex})^2 + {c}\nextrema(f(x), x, -5, 5)")
    assert_close_sequence(role_xs(result, "global_min"), [vertex], abs_tol=1e-9)


@pytest.mark.evidence_c
@settings(max_examples=40)
@given(vertex=root_value, k=curvature)
def test_sign_flip_swaps_global_roles(vertex, k):
    upward = evaluate_cell(f"f(x) = {k}*(x - {vertex})^2\nextrema(f(x), x, -5, 5)")
    downward = evaluate_cell(f"f(x) = -{k}*(x - {vertex})^2\nextrema(f(x), x, -5, 5)")
    assert role_xs(upward, "global_min") == role_xs(downward, "global_max")
