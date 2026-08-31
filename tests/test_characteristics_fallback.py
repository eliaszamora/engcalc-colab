import math

import pytest
import sympy as sp

import engcalc_colab.characteristics as characteristics
from engcalc_colab.characteristics import (
    normalize_analysis_domain,
    solve_extrema_exact,
    solve_intersections_exact,
    solve_roots_exact,
)
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.numeric import NumericContext


def _force_exact_solver_unresolved(monkeypatch):
    monkeypatch.setattr(
        characteristics,
        "_exact_real_solution_set",
        lambda expression, variable: ((), True),
    )


def _x_magnitudes(points):
    return tuple(float(point.x_quantity.magnitude) for point in points)


def test_numeric_fallback_is_marked_approximate(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))
    _force_exact_solver_unresolved(monkeypatch)

    points, intervals, unresolved = solve_roots_exact(
        sp.sin(x) - sp.Rational(1, 2),
        x,
        domain,
        context,
    )

    assert intervals == ()
    assert unresolved is False
    assert len(points) == 2
    assert all(point.provenance == "numeric" for point in points)
    assert _x_magnitudes(points) == pytest.approx(
        (math.pi / 6, 5 * math.pi / 6),
        rel=1e-9,
        abs=1e-10,
    )


def test_numeric_fallback_is_deterministic(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))
    _force_exact_solver_unresolved(monkeypatch)

    first, _, first_unresolved = solve_roots_exact(
        sp.sin(x) - sp.Rational(1, 2),
        x,
        domain,
        context,
    )
    second, _, second_unresolved = solve_roots_exact(
        sp.sin(x) - sp.Rational(1, 2),
        x,
        domain,
        context,
    )

    assert first_unresolved is False
    assert second_unresolved is False
    assert _x_magnitudes(first) == _x_magnitudes(second)
    assert tuple(point.provenance for point in first) == tuple(
        point.provenance for point in second
    )


def test_numeric_fallback_recovers_even_multiplicity_root(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))
    _force_exact_solver_unresolved(monkeypatch)

    points, intervals, unresolved = solve_roots_exact(
        (x - sp.sqrt(2)) ** 2,
        x,
        domain,
        context,
    )

    assert intervals == ()
    assert unresolved is False
    assert len(points) == 1
    assert points[0].provenance == "numeric"
    assert float(points[0].x_quantity.magnitude) == pytest.approx(
        math.sqrt(2),
        rel=1e-9,
        abs=1e-10,
    )


def test_numeric_fallback_deduplicates_grid_seed_and_refined_root(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))
    _force_exact_solver_unresolved(monkeypatch)

    points, intervals, unresolved = solve_roots_exact(x - 2, x, domain, context)

    assert intervals == ()
    assert unresolved is False
    assert len(points) == 1
    assert points[0].provenance == "numeric"
    assert float(points[0].x_quantity.magnitude) == pytest.approx(2.0, abs=1e-12)


def test_numeric_fallback_never_brackets_across_piecewise_jump(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    expr = sp.Piecewise(
        (x - 1, x < 2),
        (x - 3, True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))
    _force_exact_solver_unresolved(monkeypatch)

    points, intervals, unresolved = solve_roots_exact(expr, x, domain, context)

    assert intervals == ()
    assert unresolved is False
    assert _x_magnitudes(points) == pytest.approx((1.0, 3.0), abs=1e-10)
    assert all(abs(value - 2.0) > 1e-6 for value in _x_magnitudes(points))
    assert all(point.provenance == "numeric" for point in points)


def test_piecewise_exact_and_numeric_roots_can_coexist(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    expr = sp.Piecewise(
        (x - 1, x < 2),
        (sp.sin(x - 3), True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    def selective_exact_solver(expression, variable):
        expression = sp.sympify(expression)
        if sp.simplify(expression - (x - 1)) == 0:
            return (sp.Integer(1),), False
        return (), True

    monkeypatch.setattr(
        characteristics,
        "_exact_real_solution_set",
        selective_exact_solver,
    )

    points, intervals, unresolved = solve_roots_exact(expr, x, domain, context)

    assert intervals == ()
    assert unresolved is False
    assert _x_magnitudes(points) == pytest.approx((1.0, 3.0), abs=1e-10)
    assert tuple(point.provenance for point in points) == ("exact", "numeric")


def test_numeric_fallback_does_not_use_public_plot_sampling(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))
    _force_exact_solver_unresolved(monkeypatch)

    def forbidden_plot_sampling(*args, **kwargs):
        raise AssertionError(
            "characteristic fallback must not use build_plot_sample_points"
        )

    monkeypatch.setattr(
        NumericContext,
        "build_plot_sample_points",
        forbidden_plot_sampling,
    )

    points, _, unresolved = solve_roots_exact(
        sp.sin(x) - sp.Rational(1, 2),
        x,
        domain,
        context,
    )

    assert unresolved is False
    assert len(points) == 2


def test_dimensional_numeric_fallback_preserves_physical_coordinate(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    L = sp.Symbol("L")
    context.values["L"] = context.ureg.Quantity(6, "m")
    domain = normalize_analysis_domain(context, sp.Integer(0), L)
    _force_exact_solver_unresolved(monkeypatch)

    points, intervals, unresolved = solve_roots_exact(
        sp.sin(sp.pi * x / L) - sp.Rational(1, 2),
        x,
        domain,
        context,
    )

    assert intervals == ()
    assert unresolved is False
    assert len(points) == 2
    assert tuple(point.x_quantity.to("m").magnitude for point in points) == pytest.approx(
        (1.0, 5.0),
        rel=1e-9,
        abs=1e-10,
    )
    assert all(point.provenance == "numeric" for point in points)


def test_unresolved_region_without_validated_root_raises_instead_of_guessing(
    monkeypatch,
):
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))
    _force_exact_solver_unresolved(monkeypatch)

    with pytest.raises(
        EngEvaluationError,
        match="characteristic numerical fallback could not validate a solution set",
    ):
        solve_roots_exact(sp.exp(x) + 1, x, domain, context)


def test_intersections_use_numeric_fallback_when_exact_solver_is_unresolved(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))
    _force_exact_solver_unresolved(monkeypatch)

    points, intervals, unresolved = solve_intersections_exact(
        sp.sin(x),
        sp.Rational(1, 2),
        x,
        domain,
        context,
    )

    assert intervals == ()
    assert unresolved is False
    assert len(points) == 2
    assert _x_magnitudes(points) == pytest.approx(
        (math.pi / 6, 5 * math.pi / 6),
        rel=1e-9,
        abs=1e-10,
    )
    assert all(point.provenance == "numeric" for point in points)


def test_extrema_uses_numeric_derivative_fallback_with_numeric_provenance(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))
    _force_exact_solver_unresolved(monkeypatch)

    points, intervals, up, down, unresolved = solve_extrema_exact(
        sp.sin(x),
        x,
        domain,
        context,
    )

    assert intervals == ()
    assert not up and not down
    assert unresolved is False
    peak = min(
        points,
        key=lambda point: abs(float(point.x_quantity.magnitude) - math.pi / 2),
    )
    assert float(peak.x_quantity.magnitude) == pytest.approx(
        math.pi / 2,
        rel=1e-9,
        abs=1e-10,
    )
    assert peak.provenance == "numeric"
    assert "local_max" in peak.roles
    assert "global_max" in peak.roles


def test_fallback_contract_constants_are_fixed():
    assert characteristics._FALLBACK_SCAN_COUNT == 1025
    assert characteristics._FALLBACK_REL_RESIDUAL_TOL == pytest.approx(1e-9)
    assert characteristics._FALLBACK_X_DEDUP_REL_TOL == pytest.approx(1e-10)
