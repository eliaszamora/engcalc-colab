"""Deep Property Gate — generated Level A coverage for `roots(...)`.

Example counts are per property, taken from design §5.2 and the measured cost
ranking: cheap properties can afford breadth, and the historically critical
expanded-decimal family keeps its budget even though it costs more than its
siblings.
"""

from __future__ import annotations

import pytest
import sympy as sp
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quality_tests.deep.strategies import (
    lead_coefficient,
    positive_parameter,
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
    roots=st.lists(root_value, min_size=1, max_size=3, unique=True),
)
def test_factored_polynomial_roots(coeff, roots):
    assume(sufficiently_separated(roots))
    factors = "*".join(f"(x - {r})" for r in roots)
    result = evaluate_cell(f"f(x) = {coeff}*{factors}\nroots(f(x), x, -5, 5)")
    assert_close_sequence(characteristic_xs(result), sorted(roots))


@settings(max_examples=80)
@given(
    coeff=lead_coefficient,
    roots=st.lists(root_value, min_size=2, max_size=3, unique=True),
)
def test_expanded_decimal_polynomial_roots(coeff, roots):
    """N-1 family. Expanding is what produced the decimal coefficients that failed."""
    assume(sufficiently_separated(roots))
    x = sp.Symbol("x")
    expanded = sp.expand(coeff * sp.prod([x - r for r in roots]))
    source = f"f(x) = {sp.sstr(expanded)}".replace("**", "^")
    result = evaluate_cell(f"{source}\nroots(f(x), x, -5, 5)")
    assert_close_sequence(characteristic_xs(result), sorted(roots), rel_tol=1e-5)


@settings(max_examples=60)
@given(coeff=lead_coefficient, r=root_value)
def test_repeated_root(coeff, r):
    result = evaluate_cell(f"f(x) = {coeff}*(x - {r})^2\nroots(f(x), x, -5, 5)")
    assert_close_sequence(characteristic_xs(result), [r])


@settings(max_examples=80)
@given(a=positive_parameter)
def test_registered_parameter_without_real_roots(a):
    """A-1 family: the candidates only turn complex after substitution."""
    result = evaluate_cell(f"a := {a}\nf(x) = x^2 + a\nroots(f(x), x, -5, 5)")
    assert characteristic_xs(result) == []


@settings(max_examples=80)
@given(a=positive_parameter)
def test_registered_parameter_with_real_roots(a):
    """Mirror of the previous property, guarding against over-filtering."""
    result = evaluate_cell(f"a := {a}\nf(x) = x^2 - a\nroots(f(x), x, -5, 5)")
    expected = sorted(v for v in (-(a**0.5), a**0.5) if -5 <= v <= 5)
    assert_close_sequence(characteristic_xs(result), expected)


@settings(max_examples=80)
@given(r=root_value, lo=st.integers(min_value=-50, max_value=-1).map(lambda n: n / 10))
def test_root_on_the_lower_domain_bound(r, lo):
    """A root sitting exactly on a bound belongs to the domain."""
    result = evaluate_cell(f"f(x) = (x - {r})*(x - {r + 9})\nroots(f(x), x, {r}, {r + 2})")
    assert_close_sequence(characteristic_xs(result), [r])


@settings(max_examples=80)
@given(r=st.integers(min_value=600, max_value=900).map(lambda n: n / 100))
def test_root_outside_the_domain(r):
    result = evaluate_cell(f"f(x) = (x - {r})\nroots(f(x), x, 0, 5)")
    assert characteristic_xs(result) == []
