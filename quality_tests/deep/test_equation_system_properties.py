"""Deep Property Gate — Level A coverage for `solve` on systems, and for `assume`.

Both are constructed backwards, which is what makes the oracle independent: the answer
is chosen first and the problem is built from it in plain Python, so EngCalc is never
asked what it should have said.

A system is the shape a statics sheet is written in - sum the forces, sum the moments,
solve for the reactions - and it has had example contracts only since 0.12.0.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quality_tests.helpers import evaluate_cell

pytestmark = [pytest.mark.evidence_a, pytest.mark.quality_deep]

_VALUE = st.integers(min_value=-40, max_value=40).map(lambda n: n / 4)
_COEFF = st.integers(min_value=-8, max_value=8).filter(lambda n: n != 0)


@settings(max_examples=80)
@given(
    a=_VALUE,
    b=_VALUE,
    c11=_COEFF,
    c12=_COEFF,
    c21=_COEFF,
    c22=_COEFF,
)
def test_a_two_by_two_system_returns_the_answer_it_was_built_from(a, b, c11, c12, c21, c22):
    """The unknowns are chosen, then the equations are written to have them.

    The right-hand sides are computed here in plain arithmetic, so a solver that
    returned the coefficients, or the unknowns crossed, or one of them twice, fails.
    """
    assume(c11 * c22 - c12 * c21 != 0)

    result = evaluate_cell(
        f"e1 = eq({c11}*u + {c12}*v, {c11 * a + c12 * b})\n"
        f"e2 = eq({c21}*u + {c22}*v, {c21 * a + c22 * b})\n"
        "solve(e1, e2, u, v)"
    )
    answers = dict(result.solutions)

    assert list(answers) == ["u", "v"], result.solutions
    assert float(answers["u"]) == pytest.approx(a, abs=1e-9)
    assert float(answers["v"]) == pytest.approx(b, abs=1e-9)


@settings(max_examples=40)
@given(a=_VALUE, b=_VALUE, c=_VALUE)
def test_a_three_by_three_system_keeps_every_unknown_with_its_own_name(a, b, c):
    """Three unknowns, and each must come back under the name it was asked for.

    Two unknowns cannot see a rotation - swapping them is the same as negating a
    coefficient in some draws. Three can.
    """
    result = evaluate_cell(
        f"e1 = eq(p + q + r, {a + b + c})\n"
        f"e2 = eq(p - q, {a - b})\n"
        f"e3 = eq(q - r, {b - c})\n"
        "solve(e1, e2, e3, p, q, r)"
    )
    answers = dict(result.solutions)

    assert list(answers) == ["p", "q", "r"]
    assert float(answers["p"]) == pytest.approx(a, abs=1e-9)
    assert float(answers["q"]) == pytest.approx(b, abs=1e-9)
    assert float(answers["r"]) == pytest.approx(c, abs=1e-9)


@settings(max_examples=60)
@given(
    positive=st.integers(min_value=1, max_value=400).map(lambda n: n / 10),
    negative=st.integers(min_value=1, max_value=400).map(lambda n: n / 10),
)
def test_a_declared_sign_keeps_the_root_that_has_it(positive, negative):
    """`(xr + p)*(xr - q)` has roots `-p` and `q`, and `assume(xr > 0)` keeps `q`.

    The roots are written in terms of names rather than numbers on purpose. SymPy drops
    any root whose sign it can determine, so with numeric roots the filter never runs
    and the property would pass against a build that has none. With `p` and `q` as
    unsigned symbols carrying `:=` values, only the sheet can decide, which is the path
    under test.
    """
    result = evaluate_cell(
        "assume(xr > 0)\n"
        f"p := {positive}\n"
        f"q := {negative}\n"
        "f(xr) = (xr + p)*(xr - q)\n"
        "xr_1 = solve(eq(f(xr), 0), xr)\n"
        "numeric(xr_1)"
    )
    assert float(result.quantity.magnitude) == pytest.approx(negative, rel=1e-9)


@settings(max_examples=40)
@given(
    positive=st.integers(min_value=1, max_value=400).map(lambda n: n / 10),
    negative=st.integers(min_value=1, max_value=400).map(lambda n: n / 10),
)
def test_without_the_declaration_both_roots_stand(positive, negative):
    """The other half. Nothing is discarded on a sheet that stated nothing.

    A build that filtered by sign regardless of `assume` would satisfy the property
    above on every draw and be wrong about what the engineer asked for.
    """
    result = evaluate_cell(
        f"p := {positive}\n"
        f"q := {negative}\n"
        "f(xr) = (xr + p)*(xr - q)\n"
        "solve(eq(f(xr), 0), xr)"
    )
    assert len(result.solutions) == 2
    assert result.discarded is None
