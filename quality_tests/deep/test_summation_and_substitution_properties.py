"""Deep Property Gate — Level A coverage for `sum(...)` and `subs(...)`.

Both have closed forms anyone can write down, so the oracle is arithmetic rather than a
second run of EngCalc.

`subs` is the operation every worked sheet leans on - a moment law is written once and
read at midspan, at a support, under a load - and it has had example contracts only.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quality_tests.helpers import evaluate_cell

pytestmark = [pytest.mark.evidence_a, pytest.mark.quality_deep]

_TERM = st.integers(min_value=-20, max_value=20).filter(lambda n: n != 0)
_COUNT = st.integers(min_value=1, max_value=40)
_POINT = st.integers(min_value=-400, max_value=400).map(lambda n: n / 100)
_COEFFS = st.lists(
    st.integers(min_value=-30, max_value=30).map(lambda n: n / 10),
    min_size=1,
    max_size=4,
)


@settings(max_examples=80)
@given(coefficient=_TERM, count=_COUNT)
def test_an_arithmetic_series_matches_its_closed_form(coefficient, count):
    """`sum(k*i, i, 1, n)` is `k*n*(n+1)/2`.

    The closed form is the oracle. A summation off by one term - the first or the last -
    is the classic defect here and it changes the answer by `k` or by `k*n`, which this
    sees at every draw.
    """
    result = evaluate_cell(f"S = sum({coefficient}*i, i, 1, {count})\nnumeric(S)")
    expected = coefficient * count * (count + 1) / 2
    assert float(result.quantity.magnitude) == pytest.approx(expected, rel=1e-9)


@settings(max_examples=60)
@given(coefficient=_TERM, lower=st.integers(1, 20), extra=st.integers(0, 20))
def test_a_series_that_starts_away_from_one_still_matches(coefficient, lower, extra):
    """Both bounds carry information, and a lower bound assumed to be 1 is a real defect.

    A sum from `a` to `b` of `k*i` is `k*(b*(b+1) - (a-1)*a)/2`.
    """
    upper = lower + extra
    result = evaluate_cell(
        f"S = sum({coefficient}*i, i, {lower}, {upper})\nnumeric(S)"
    )
    expected = coefficient * (upper * (upper + 1) - (lower - 1) * lower) / 2
    assert float(result.quantity.magnitude) == pytest.approx(expected, rel=1e-9)


@settings(max_examples=60)
@given(count=_COUNT)
def test_a_sum_of_squares_matches_its_closed_form(count):
    """`sum(i^2, i, 1, n)` is `n*(n+1)*(2n+1)/6`.

    A second closed form, because a linear term alone cannot see an index that is off by
    a constant: `sum(k*(i+1))` and `sum(k*i)` differ by `k*n`, which a wrong `k` could
    absorb. A quadratic term cannot be absorbed that way.
    """
    result = evaluate_cell(f"S = sum(i^2, i, 1, {count})\nnumeric(S)")
    expected = count * (count + 1) * (2 * count + 1) / 6
    assert float(result.quantity.magnitude) == pytest.approx(expected, rel=1e-9)


@settings(max_examples=80)
@given(coefficients=_COEFFS, point=_POINT)
def test_substituting_a_value_evaluates_the_polynomial_there(coefficients, point):
    """`subs(f(x), x, v)` is the polynomial at `v`, computed here in plain arithmetic."""
    terms = " + ".join(
        f"{coefficient}*x^{power}" for power, coefficient in enumerate(coefficients)
    )
    result = evaluate_cell(f"f(x) = {terms}\nnumeric(subs(f(x), x, {point}))")

    expected = sum(
        coefficient * point**power for power, coefficient in enumerate(coefficients)
    )
    assert float(result.quantity.magnitude) == pytest.approx(
        expected, rel=1e-9, abs=1e-9
    )


@settings(max_examples=60)
@given(coefficients=_COEFFS, first=_POINT, second=_POINT)
def test_substituting_two_variables_puts_each_value_in_its_own_place(
    coefficients, first, second
):
    """The failure this exists for is a swap, so the two values are different.

    With `x` and `y` both replaced by the same number, a substitution that crossed them
    would agree with one that did not.
    """
    assume(abs(first - second) > 0.2)

    terms = " + ".join(
        f"{coefficient}*x^{power}*y" for power, coefficient in enumerate(coefficients)
    )
    result = evaluate_cell(
        f"g(x) = {terms}\nnumeric(subs(g(x), x, {first}, y, {second}))"
    )
    expected = second * sum(
        coefficient * first**power for power, coefficient in enumerate(coefficients)
    )
    assert float(result.quantity.magnitude) == pytest.approx(
        expected, rel=1e-9, abs=1e-9
    )
