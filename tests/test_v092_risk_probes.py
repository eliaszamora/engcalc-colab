import time

import pytest
import sympy as sp

from engcalc_colab.characteristics import normalize_analysis_domain, solve_roots_exact
from engcalc_colab.numeric import NumericContext


def test_near_zero_value_is_not_promoted_to_root():
    context = NumericContext()
    x = sp.Symbol("x", real=True)
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(2))

    points, intervals, unresolved = solve_roots_exact(
        x - sp.Float("1.000000000000000001"),
        x,
        domain,
        context,
    )

    assert intervals == ()
    assert unresolved is False
    assert len(points) == 1
    assert abs(float(points[0].x_quantity.magnitude) - 1.0) < 1e-12


def test_unknown_realness_hint_cannot_create_complex_or_confident_empty_result(
    monkeypatch,
):
    context = NumericContext()
    x = sp.Symbol("x", real=True)
    u = sp.Symbol("u")  # is_real is None
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(2))
    unresolved_set = sp.ConditionSet(
        x,
        sp.Eq(x - 1, 0, evaluate=False),
        sp.S.Reals,
    )

    monkeypatch.setattr(sp, "solveset", lambda *args, **kwargs: unresolved_set)
    monkeypatch.setattr(sp, "solve", lambda *args, **kwargs: [u])

    points, intervals, unresolved = solve_roots_exact(x - 1, x, domain, context)

    assert intervals == ()
    assert unresolved is False
    assert len(points) == 1
    assert float(points[0].x_quantity.magnitude) == pytest.approx(1.0)
    magnitude = points[0].x_quantity.magnitude
    assert not hasattr(magnitude, "imag") or magnitude.imag == 0


def test_candidate_simplification_fixture_completes_without_pathological_delay():
    context = NumericContext()
    x = sp.Symbol("x", real=True)
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(2))
    expression = sp.expand(
        (x - 1) * sum((x + sp.Integer(i)) ** 2 for i in range(1, 35))
    )

    started = time.perf_counter()
    points, intervals, unresolved = solve_roots_exact(
        expression,
        x,
        domain,
        context,
    )
    elapsed = time.perf_counter() - started

    assert intervals == ()
    assert unresolved is False
    assert any(
        abs(float(point.x_quantity.magnitude) - 1.0) < 1e-12
        for point in points
    )
    assert elapsed < 15.0
