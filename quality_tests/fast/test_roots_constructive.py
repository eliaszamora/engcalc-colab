"""Fast Gate — Level A constructive coverage for `roots(...)`.

Every expected answer is known before EngCalc executes: the polynomials are built
from selected roots, or their real-root count follows analytically. No expectation
is obtained from SymPy, because an oracle sharing the solver under test can fail
the same way as the implementation and still report agreement.

Case counts follow the Task 3 GitHub Actions calibration: redundancy is spent on
the families with a demonstrated defect history, not spread evenly.
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
    ("coeff", "roots"),
    [
        (1.0, [1.5]),
        (-2.25, [-3.5]),
        (2.5, [-1.25, 2.0]),
        (-1.75, [0.5, 4.25]),
        (3.0, [-3.0, 0.5, 2.75]),
        (-0.5, [-4.5, -1.0, 3.25]),
    ],
)
def test_roots_factored_polynomial(coeff, roots):
    """Degrees 1-3, both leading-coefficient signs, roots chosen in advance."""
    factors = "*".join(f"(x - {r})" for r in roots)
    result = evaluate_cell(f"f(x) = {coeff}*{factors}\nroots(f(x), x, -5, 5)")
    assert_close_sequence(characteristic_xs(result), sorted(roots))


@pytest.mark.parametrize(
    ("a", "r1", "r2"),
    [
        # The four reproductions that failed before the N-1 correction.
        (2.87, 0.602, 3.755),
        (1.01, 0.313, 2.619),
        (1.87, 1.35, 3.245),
        (2.13, 0.783, 2.802),
        # Additional decimal coefficients across both signs and root positions.
        (-1.55, 0.45, 4.6),
        (0.6, 0.474, 3.478),
        (4.75, 1.234, 3.55),
        (-3.2, 2.1, 4.85),
        (1.0, 0.05, 4.95),
        (-0.35, 1.669, 2.861),
        (2.69, 0.125, 1.375),
        (-4.4, 3.05, 4.4),
    ],
)
def test_roots_expanded_decimal_polynomial(a, r1, r2):
    """N-1 family. Historically 8 of 20 random members lost roots in silence.

    Written expanded so the coefficients are ordinary engineering decimals, which
    is the form that triggered the defect; the roots remain known by construction.
    """
    b = -a * (r1 + r2)
    c = a * r1 * r2
    result = evaluate_cell(f"f(x) = {a}*x^2 + {b}*x + {c}\nroots(f(x), x, 0, 5)")
    assert_close_sequence(characteristic_xs(result), [r1, r2], rel_tol=1e-6)


@pytest.mark.parametrize("r", [-2.5, 0.0, 1.75, 4.25])
def test_roots_repeated_even_multiplicity(r):
    """No sign change at the root, so a bracketing search alone would miss it."""
    result = evaluate_cell(f"f(x) = 2.0*(x - {r})^2\nroots(f(x), x, -5, 5)")
    assert_close_sequence(characteristic_xs(result), [r])


@pytest.mark.parametrize("a", [1.0, 0.25, 4.75])
@pytest.mark.parametrize("degree", [2, 4])
def test_roots_registered_parameter_without_real_roots(a, degree):
    """A-1 family: candidates turn complex only after the parameter is substituted."""
    result = evaluate_cell(f"a := {a}\nf(x) = x^{degree} + a\nroots(f(x), x, -5, 5)")
    assert characteristic_xs(result) == []


@pytest.mark.parametrize(("a", "root"), [(4.0, 2.0), (2.25, 1.5), (0.25, 0.5)])
def test_roots_registered_parameter_with_real_roots(a, root):
    """Guard against over-filtering: the same shape with a negative constant."""
    result = evaluate_cell(f"a := {a}\nf(x) = x^2 - a\nroots(f(x), x, -5, 5)")
    assert_close_sequence(characteristic_xs(result), [-root, root])


@pytest.mark.parametrize(
    "roots",
    [
        [-2.0, 0.5, 1.5, 3.0],
        [-1.0, 0.25, 1.75, 2.5, 4.0],
        [-4.0, -1.5, 1.0, 3.5],
    ],
)
def test_roots_higher_degree(roots):
    factors = "*".join(f"(x - {r})" for r in roots)
    result = evaluate_cell(f"f(x) = {factors}\nroots(f(x), x, -5, 5)")
    assert_close_sequence(characteristic_xs(result), sorted(roots), rel_tol=1e-5)


@pytest.mark.parametrize("exponent", [-9, -6, -3, 3, 6, 9])
def test_roots_extreme_response_scales(exponent):
    """A relative residual criterion must hold across twelve orders of magnitude."""
    result = evaluate_cell(
        f"f(x) = 1e{exponent}*(x - 1.5)*(x + 1.0)\nroots(f(x), x, -5, 5)"
    )
    assert_close_sequence(characteristic_xs(result), [-1.0, 1.5])


@pytest.mark.parametrize(
    ("r", "lo", "hi"),
    [
        (1.25, 1.25, 4.0),
        (3.5, 0.0, 3.5),
        (-2.0, -2.0, 1.0),
        (0.0, -3.0, 0.0),
    ],
)
def test_root_exactly_on_a_domain_bound_is_included(r, lo, hi):
    result = evaluate_cell(f"f(x) = (x - {r})*(x - {r + 9})\nroots(f(x), x, {lo}, {hi})")
    assert_close_sequence(characteristic_xs(result), [r])


@pytest.mark.parametrize(("r", "lo", "hi"), [(7.5, 0.0, 5.0), (-6.25, -5.0, 5.0)])
def test_root_outside_the_domain_is_excluded(r, lo, hi):
    result = evaluate_cell(f"f(x) = (x - {r})\nroots(f(x), x, {lo}, {hi})")
    assert characteristic_xs(result) == []
