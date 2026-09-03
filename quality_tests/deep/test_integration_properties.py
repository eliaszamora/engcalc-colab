"""Deep Property Gate — coverage for `integrate(...)`, definite and indefinite.

Measured motive: a definite integral that silently dropped its bounds still let 14 of 18
gap-map exercises run end to end, and an elastic curve derived by double integration is
the whole of E4 and E9. Both rest on this.

The Level A oracle is the closed form of a monomial integral in plain Python. The
antiderivative properties are marked Level B, because they check EngCalc against itself
- a self-consistent pair of wrong answers would pass them, which is exactly why they sit
beside the Level A ones rather than instead of them.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quality_tests.deep.strategies import lead_coefficient
from quality_tests.helpers import evaluate_cell

_COEFF = lead_coefficient
_ORDER = st.integers(min_value=0, max_value=4)
_BOUND = st.integers(min_value=-400, max_value=400).map(lambda n: n / 100)


@pytest.mark.evidence_a
@pytest.mark.quality_deep
@settings(max_examples=80)
@given(coeff=_COEFF, order=_ORDER, lower=_BOUND, upper=_BOUND)
def test_a_monomial_integrates_to_its_closed_form(coeff, order, lower, upper):
    """`integrate(k*x^n, x, a, b)` is `k*(b^(n+1) - a^(n+1))/(n+1)`."""
    assume(abs(upper - lower) > 0.05)

    result = evaluate_cell(
        f"f(x) = {coeff}*x^{order}\n"
        f"S = integrate(f(x), x, {lower}, {upper})\n"
        "numeric(S)"
    )
    power = order + 1
    expected = coeff * (upper**power - lower**power) / power
    assert float(result.quantity.magnitude) == pytest.approx(
        expected, rel=1e-9, abs=1e-9
    )


@pytest.mark.evidence_a
@pytest.mark.quality_deep
@settings(max_examples=60)
@given(coeff=_COEFF, order=_ORDER, upper=_BOUND)
def test_reversing_the_bounds_reverses_the_sign(coeff, order, upper):
    """The sign is the half of a definite integral a dropped bound cannot get right.

    A build that ignored its bounds and returned the antiderivative would give the same
    magnitude for both orders, so this separates "evaluated the bounds" from "computed
    an antiderivative and stopped".
    """
    assume(abs(upper) > 0.05)

    body = f"f(x) = {coeff}*x^{order}\n"
    forward = evaluate_cell(body + f"S = integrate(f(x), x, 0, {upper})\nnumeric(S)")
    backward = evaluate_cell(body + f"S = integrate(f(x), x, {upper}, 0)\nnumeric(S)")

    assert float(forward.quantity.magnitude) == pytest.approx(
        -float(backward.quantity.magnitude), rel=1e-9, abs=1e-12
    )


@pytest.mark.evidence_a
@pytest.mark.quality_deep
@settings(max_examples=60)
@given(coeff=_COEFF, order=_ORDER, upper=_BOUND)
def test_the_indefinite_integral_is_the_antiderivative_of_the_same_monomial(
    coeff, order, upper
):
    """`integrate(k*x^n, x)` is `k*x^(n+1)/(n+1)`, with no constant invented.

    Checked against the closed form rather than against the definite integral, so this
    stays Level A: a pair of wrong answers agreeing with each other would satisfy the
    comparison and not this.
    """
    result = evaluate_cell(
        f"f(x) = {coeff}*x^{order}\n"
        "F(x) = integrate(f(x), x)\n"
        f"numeric(subs(F(x), x, {upper}))"
    )
    power = order + 1
    assert float(result.quantity.magnitude) == pytest.approx(
        coeff * upper**power / power, rel=1e-9, abs=1e-9
    )


@pytest.mark.evidence_b
@pytest.mark.quality_deep
@settings(max_examples=40)
@given(coeff=_COEFF, order=_ORDER, middle=_BOUND, upper=_BOUND)
def test_a_definite_integral_splits_at_an_interior_point(coeff, order, middle, upper):
    """Level B, and labelled so: both halves come from the same machinery.

    It is kept because it is the one property that exercises three bound pairs against
    each other, and a bound handled inconsistently across sign or magnitude shows up
    here without anyone choosing the case.
    """
    assume(abs(upper) > 0.2 and abs(middle) > 0.05 and abs(upper - middle) > 0.05)

    body = f"f(x) = {coeff}*x^{order}\n"
    whole = evaluate_cell(body + f"S = integrate(f(x), x, 0, {upper})\nnumeric(S)")
    first = evaluate_cell(body + f"S = integrate(f(x), x, 0, {middle})\nnumeric(S)")
    second = evaluate_cell(body + f"S = integrate(f(x), x, {middle}, {upper})\nnumeric(S)")

    assert float(whole.quantity.magnitude) == pytest.approx(
        float(first.quantity.magnitude) + float(second.quantity.magnitude),
        rel=1e-9,
        abs=1e-9,
    )
