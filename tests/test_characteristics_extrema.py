import ast

import pytest
import sympy as sp

from engcalc_colab.characteristics import (
    normalize_analysis_domain,
    solve_extrema_exact,
)
from engcalc_colab.numeric import NumericContext


def _assign(context: NumericContext, name: str, source: str):
    return context.assign(name, ast.parse(source, mode="eval"))


def _point_at(points, expected):
    return next(
        point
        for point in points
        if sp.simplify(point.x_symbolic - expected) == 0
    )


def test_quadratic_has_exact_interior_global_maximum():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unbounded_above, unbounded_below, unresolved = solve_extrema_exact(
        -(x - 2) ** 2 + 5,
        x,
        domain,
        context,
        source_label="M(x)",
    )

    peak = _point_at(points, sp.Integer(2))
    assert "local_max" in peak.roles
    assert "global_max" in peak.roles
    assert sp.simplify(peak.value_symbolic - 5) == 0
    assert peak.provenance == "exact"
    assert peak.side == "at"
    assert peak.source_label == "M(x)"
    assert intervals == ()
    assert unbounded_above is False
    assert unbounded_below is False
    assert unresolved is False


def test_monotonic_response_assigns_boundary_and_global_roles_to_endpoints():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, up, down, unresolved = solve_extrema_exact(
        x,
        x,
        domain,
        context,
    )

    lower = _point_at(points, sp.Integer(0))
    upper = _point_at(points, sp.Integer(4))
    assert lower.roles == ("boundary", "global_min")
    assert upper.roles == ("boundary", "global_max")
    assert intervals == ()
    assert not up and not down and not unresolved


def test_multiple_stationary_points_keep_local_roles_without_promoting_all_to_global():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(-3), sp.Integer(3))

    points, intervals, up, down, unresolved = solve_extrema_exact(
        x**4 - 4 * x**2,
        x,
        domain,
        context,
    )

    center = _point_at(points, sp.Integer(0))
    left_min = _point_at(points, -sp.sqrt(2))
    right_min = _point_at(points, sp.sqrt(2))
    left_boundary = _point_at(points, sp.Integer(-3))
    right_boundary = _point_at(points, sp.Integer(3))

    assert "local_max" in center.roles
    assert "global_max" not in center.roles
    assert "local_min" in left_min.roles and "global_min" in left_min.roles
    assert "local_min" in right_min.roles and "global_min" in right_min.roles
    assert "boundary" in left_boundary.roles and "global_max" in left_boundary.roles
    assert "boundary" in right_boundary.roles and "global_max" in right_boundary.roles
    assert intervals == ()
    assert not up and not down and not unresolved


def test_constant_domain_returns_one_global_max_min_interval_locus():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, up, down, unresolved = solve_extrema_exact(
        sp.Integer(3),
        x,
        domain,
        context,
    )

    assert points == ()
    assert len(intervals) == 1
    interval = intervals[0]
    assert interval.role == "global_max_min"
    assert interval.lower_symbolic == 0
    assert interval.upper_symbolic == 4
    assert interval.lower_closed is True
    assert interval.upper_closed is True
    assert interval.value_symbolic == 3
    assert interval.value_quantity.magnitude == pytest.approx(3.0)
    assert not up and not down and not unresolved


def test_dimensional_extremum_preserves_exact_location_and_moment_units():
    context = NumericContext()
    _assign(context, "L", "4*m")
    _assign(context, "q", "10*kN/m")
    x, L, q = sp.symbols("x L q")
    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    points, intervals, up, down, unresolved = solve_extrema_exact(
        q * x * (L - x),
        x,
        domain,
        context,
        source_label="M(x)",
    )

    peak = _point_at(points, L / 2)
    assert peak.x_quantity.to("m").magnitude == pytest.approx(2.0)
    assert sp.simplify(peak.value_symbolic - q * L**2 / 4) == 0
    assert peak.value_quantity.to("kN*m").magnitude == pytest.approx(40.0)
    assert "local_max" in peak.roles
    assert "global_max" in peak.roles
    assert intervals == ()
    assert not up and not down and not unresolved


def test_interior_pole_reports_both_unbounded_directions_without_finite_point_at_pole():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unbounded_above, unbounded_below, unresolved = solve_extrema_exact(
        1 / (x - 2),
        x,
        domain,
        context,
    )

    assert all(sp.simplify(point.x_symbolic - 2) != 0 for point in points)
    assert intervals == ()
    assert unbounded_above is True
    assert unbounded_below is True
    assert unresolved is False
