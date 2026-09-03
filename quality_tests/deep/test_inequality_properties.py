"""Deep Property Gate — Level A coverage for `solve(inequality, x, lower, upper)`.

The Gate was built for `characteristics/` in 0.9.x. Thirteen releases of features were
added after it and none of them gained a property, so all of them rest on the examples
their author happened to think of. This is the first of those to be covered, and it is
first because its correctness has a definition anyone can check: the region reported is
the set of points where the inequality holds, and nothing else.

The oracle is a polynomial evaluated in plain Python from its own coefficients. It never
asks EngCalc anything, which is what keeps this Level A rather than a solver confirming
itself.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quality_tests.deep.strategies import (
    lead_coefficient,
    root_value,
    sufficiently_separated,
)
from quality_tests.helpers import (
    evaluate_cell,
    inequality_regions,
    inside_any_region,
)

pytestmark = [pytest.mark.evidence_a, pytest.mark.quality_deep]

_LOWER, _UPPER = -5.0, 5.0
# Points are judged away from a boundary. Whether the boundary itself belongs to the
# answer is decided by the closure properties below, exactly, rather than by sampling a
# float against a root.
_BOUNDARY_MARGIN = 1e-6


def _sample_points(count: int = 41) -> list[float]:
    step = (_UPPER - _LOWER) / (count - 1)
    return [_LOWER + index * step for index in range(count)]


@settings(max_examples=60)
@given(
    coeff=lead_coefficient,
    roots=st.lists(root_value, min_size=1, max_size=3, unique=True),
    strict=st.booleans(),
    above=st.booleans(),
)
def test_the_region_is_exactly_where_the_polynomial_satisfies_the_comparison(
    coeff, roots, strict, above
):
    """Every sampled point agrees with the sign computed in plain arithmetic.

    This is the property the whole feature reduces to. A solver that reported the
    complement, or lost a region, or shifted a boundary, disagrees at some point of a
    41-point sweep for some draw.
    """
    assume(sufficiently_separated(roots))
    assume(all(_LOWER + 0.2 < r < _UPPER - 0.2 for r in roots))

    factors = "*".join(f"(x - {r})" for r in roots)
    operator = (">" if strict else ">=") if above else ("<" if strict else "<=")
    result = evaluate_cell(
        f"f(x) = {coeff}*{factors}\nsolve(f(x) {operator} 0, x, {_LOWER}, {_UPPER})"
    )
    regions = inequality_regions(result)

    for point in _sample_points():
        value = coeff
        for root in roots:
            value *= point - root
        if abs(value) < 1e-9:
            continue  # a sampled root; the closure properties decide those
        holds = value > 0 if above else value < 0
        assert inside_any_region(point, regions, _BOUNDARY_MARGIN) == holds, (
            f"x={point} value={value} operator={operator} regions={regions}"
        )


@settings(max_examples=40)
@given(coeff=lead_coefficient, left=root_value, right=root_value)
def test_a_strict_comparison_opens_its_boundaries_and_a_loose_one_closes_them(
    coeff, left, right
):
    """The boundary is a root, so it belongs to `>=` and not to `>`.

    Asserted as a pair on the same polynomial. Either alone passes against a build that
    hard-codes one closure and never reads the operator.
    """
    assume(right - left > 0.5)
    assume(_LOWER + 0.2 < left < right < _UPPER - 0.2)

    body = f"f(x) = {abs(coeff)}*(x - {left})*(x - {right})\n"
    strict = inequality_regions(
        evaluate_cell(body + f"solve(f(x) < 0, x, {_LOWER}, {_UPPER})")
    )
    loose = inequality_regions(
        evaluate_cell(body + f"solve(f(x) <= 0, x, {_LOWER}, {_UPPER})")
    )

    assert len(strict) == 1 and len(loose) == 1
    assert strict[0][2] is False and strict[0][3] is False
    assert loose[0][2] is True and loose[0][3] is True
    assert strict[0][0] == pytest.approx(left, abs=1e-6)
    assert strict[0][1] == pytest.approx(right, abs=1e-6)


@settings(max_examples=40)
@given(
    coeff=lead_coefficient,
    roots=st.lists(root_value, min_size=1, max_size=2, unique=True),
)
def test_the_ends_of_the_domain_are_closed_because_they_are_not_roots(coeff, roots):
    """A bound the engineer wrote is in the domain; only a root can exclude a point.

    A build that treated every interval end as a root would open `[0, ...` at the start
    of a span, quietly excluding the support.
    """
    assume(sufficiently_separated(roots))
    assume(all(_LOWER + 0.2 < r < _UPPER - 0.2 for r in roots))

    factors = "*".join(f"(x - {r})" for r in roots)
    result = evaluate_cell(
        f"f(x) = {coeff}*{factors}\nsolve(f(x) > 0, x, {_LOWER}, {_UPPER})"
    )
    for lower, upper, lower_closed, upper_closed in inequality_regions(result):
        if lower == pytest.approx(_LOWER, abs=1e-9):
            assert lower_closed
        if upper == pytest.approx(_UPPER, abs=1e-9):
            assert upper_closed


@settings(max_examples=40)
@given(coeff=lead_coefficient, root=root_value)
def test_a_touching_root_splits_a_strict_region_and_joins_a_loose_one(coeff, root):
    """`(x - r)^2` touches zero without crossing it.

    Under `> 0` the answer is two regions with r excluded; under `>= 0` it is one. This
    is the shape that catches merging neighbours without reading the operator, and every
    other property here is blind to it: their regions are separated by genuine sign
    changes, where the boundary is excluded on both sides anyway.
    """
    assume(_LOWER + 0.5 < root < _UPPER - 0.5)

    body = f"g(x) = {abs(coeff)}*(x - {root})^2\n"
    strict = inequality_regions(
        evaluate_cell(body + f"solve(g(x) > 0, x, {_LOWER}, {_UPPER})")
    )
    loose = inequality_regions(
        evaluate_cell(body + f"solve(g(x) >= 0, x, {_LOWER}, {_UPPER})")
    )

    assert len(strict) == 2, strict
    assert strict[0][1] == pytest.approx(root, abs=1e-6)
    assert strict[0][3] is False and strict[1][2] is False
    assert len(loose) == 1, loose
