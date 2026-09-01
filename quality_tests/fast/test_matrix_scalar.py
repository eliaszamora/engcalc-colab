"""Fast Gate — Level A coverage for indexed matrix scalars as characteristic responses.

A matrix entry reached through 1-based indexing is a scalar response and must be
accepted by the characteristic APIs; a whole matrix is not, and must be rejected
with a scalar-response diagnostic rather than silently analysed.
"""

from __future__ import annotations

import pytest

from engcalc_colab.errors import EngEvaluationError

from quality_tests.helpers import (
    assert_close_sequence,
    characteristic_xs,
    evaluate_cell,
    role_xs,
)

pytestmark = pytest.mark.evidence_a


@pytest.mark.parametrize(
    ("length", "offset"),
    [(6.0, 1.5), (4.0, 2.5), (10.0, 0.75), (3.0, 3.0)],
)
def test_indexed_entry_is_a_valid_root_response(length, offset):
    """K(x)[1,1] = x + L, so K(x)[1,1] - L - t vanishes exactly at x = t."""
    result = evaluate_cell(
        f"L := {length}*m\nt := {offset}*m\n"
        "K(x) = [x + L, 0; 0, 2*x + L]\n"
        "roots(K(x)[1,1] - L - t, x, 0, L)"
    )
    assert_close_sequence(characteristic_xs(result, "m"), [offset], abs_tol=1e-9)


@pytest.mark.parametrize(("length", "expected_max"), [(6.0, 6.0), (4.0, 4.0)])
def test_indexed_entry_is_a_valid_extrema_response(length, expected_max):
    """The second diagonal entry is monotone, so its roles sit on the bounds."""
    result = evaluate_cell(
        f"L := {length}*m\nK(x) = [x + L, 0; 0, 2*x + L]\n"
        "extrema(K(x)[2,2], x, 0, L)"
    )
    assert_close_sequence(role_xs(result, "global_max", "m"), [expected_max], abs_tol=1e-9)
    assert_close_sequence(role_xs(result, "global_min", "m"), [0.0], abs_tol=1e-9)


@pytest.mark.parametrize("call", ["roots", "extrema"])
def test_whole_matrix_is_rejected_as_a_response(call):
    with pytest.raises(EngEvaluationError):
        evaluate_cell(
            "L := 6*m\nK(x) = [x + L, 0; 0, 2*x + L]\n"
            f"{call}(K(x), x, 0, L)"
        )
