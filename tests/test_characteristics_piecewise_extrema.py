import ast

import pytest
import sympy as sp

from engcalc_colab.characteristics import normalize_analysis_domain, solve_extrema_exact
from engcalc_colab.numeric import NumericContext


def _assign(context: NumericContext, name: str, source: str):
    return context.assign(name, ast.parse(source, mode="eval"))


def _points_at(points, expected):
    return [
        point
        for point in points
        if sp.simplify(point.x_symbolic - expected) == 0
    ]


def test_discontinuous_piecewise_preserves_left_at_right_values():
    context = NumericContext()
    x = sp.Symbol("x")
    expr = sp.Piecewise(
        (x, x < 2),
        (10, x <= 2),
        (4 - x, True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, up, down, unresolved = solve_extrema_exact(
        expr,
        x,
        domain,
        context,
    )

    at_two = _points_at(points, sp.Integer(2))
    by_side = {point.side: float(point.value_quantity.magnitude) for point in at_two}
    assert by_side == {"left": 2.0, "at": 10.0, "right": 2.0}
    assert intervals == ()
    assert not up and not down and not unresolved


def test_breakpoint_actual_value_can_govern_global_maximum():
    context = NumericContext()
    x = sp.Symbol("x")
    expr = sp.Piecewise(
        (x, x < 2),
        (10, x <= 2),
        (4 - x, True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, _, _, _, unresolved = solve_extrema_exact(expr, x, domain, context)

    at_point = next(point for point in _points_at(points, 2) if point.side == "at")
    assert "boundary" in at_point.roles
    assert "global_max" in at_point.roles
    assert "local_max" in at_point.roles
    assert unresolved is False


def test_constant_piecewise_subinterval_can_be_global_maximum_locus():
    context = NumericContext()
    x = sp.Symbol("x")
    expr = sp.Piecewise(
        (5, x < 2),
        (4 - (x - 3) ** 2, True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, up, down, unresolved = solve_extrema_exact(
        expr,
        x,
        domain,
        context,
    )

    assert len(intervals) == 1
    locus = intervals[0]
    assert locus.role == "global_max"
    assert locus.lower_symbolic == 0
    assert locus.upper_symbolic == 2
    assert locus.lower_closed is True
    assert locus.upper_closed is False
    assert locus.value_symbolic == 5
    assert float(locus.value_quantity.magnitude) == 5.0
    assert all("global_max" not in point.roles for point in points)
    assert not up and not down and not unresolved


def test_non_governing_constant_piecewise_region_is_not_reported_as_extremum_locus():
    context = NumericContext()
    x = sp.Symbol("x")
    expr = sp.Piecewise(
        (sp.Rational(1, 2), x < 2),
        ((x - 3) ** 2, True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    _, intervals, _, _, unresolved = solve_extrema_exact(expr, x, domain, context)

    assert intervals == ()
    assert unresolved is False


def test_jump_does_not_create_fake_stationary_extremum():
    context = NumericContext()
    x = sp.Symbol("x")
    expr = sp.Piecewise(
        (-x, x < 2),
        (x + 10, True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, up, down, unresolved = solve_extrema_exact(
        expr,
        x,
        domain,
        context,
    )

    assert not any(
        "local_max" in point.roles or "local_min" in point.roles
        for point in points
    )
    assert intervals == ()
    assert not up and not down and not unresolved


def test_piecewise_regions_recompute_global_roles_after_merge():
    context = NumericContext()
    x = sp.Symbol("x")
    expr = sp.Piecewise(
        (-(x - 1) ** 2 + 3, x < 2),
        (-(x - 3) ** 2 + 8, True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, up, down, unresolved = solve_extrema_exact(
        expr,
        x,
        domain,
        context,
    )

    first_peak = next(point for point in points if sp.simplify(point.x_symbolic - 1) == 0)
    second_peak = next(point for point in points if sp.simplify(point.x_symbolic - 3) == 0)
    assert "local_max" in first_peak.roles
    assert "global_max" not in first_peak.roles
    assert "local_max" in second_peak.roles
    assert "global_max" in second_peak.roles
    assert intervals == ()
    assert not up and not down and not unresolved


def test_dimensional_piecewise_breakpoint_preserves_exact_location_and_force_units():
    context = NumericContext()
    _assign(context, "L", "4*m")
    _assign(context, "q", "10*kN/m")
    x, L, q = sp.symbols("x L q")
    expr = sp.Piecewise(
        (q * x, x < L / 2),
        (2 * q * x, True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    points, intervals, up, down, unresolved = solve_extrema_exact(
        expr,
        x,
        domain,
        context,
        source_label="V(x)",
    )

    at_break = _points_at(points, L / 2)
    by_side = {point.side: point.value_quantity.to("kN").magnitude for point in at_break}
    assert by_side["left"] == pytest.approx(20.0)
    assert by_side["at"] == pytest.approx(40.0)
    assert by_side["right"] == pytest.approx(40.0)
    assert all(point.x_quantity.to("m").magnitude == pytest.approx(2.0) for point in at_break)
    assert all(point.source_label == "V(x)" for point in at_break)
    assert intervals == ()
    assert not up and not down and not unresolved


def test_continuous_piecewise_cusp_is_classified_from_same_region_neighbors():
    context = NumericContext()
    x = sp.Symbol("x")
    expr = sp.Piecewise(
        (-x, x < 0),
        (x, True),
        evaluate=False,
    )
    domain = normalize_analysis_domain(context, sp.Integer(-2), sp.Integer(2))

    points, intervals, up, down, unresolved = solve_extrema_exact(
        expr,
        x,
        domain,
        context,
    )

    at_zero = next(point for point in _points_at(points, 0) if point.side == "at")
    assert "local_min" in at_zero.roles
    assert "global_min" in at_zero.roles
    assert intervals == ()
    assert not up and not down and not unresolved


def test_piecewise_boundary_value_symbolic_is_selected_governing_branch():
    context = NumericContext()
    _assign(context, "a", "3*m")
    _assign(context, "L", "6*m")
    x, a, L = sp.symbols("x a L", real=True)
    expr = sp.Piecewise((x-a, x < a), (2*(x-a), True), evaluate=False)
    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    points, _, _, _, unresolved = solve_extrema_exact(expr, x, domain, context)
    lower = next(point for point in points if sp.simplify(point.x_symbolic) == 0)
    upper = next(point for point in points if sp.simplify(point.x_symbolic-L) == 0)
    assert sp.simplify(lower.value_symbolic + a) == 0
    assert sp.simplify(upper.value_symbolic - 2*(L-a)) == 0
    assert lower.value_quantity.to("m").magnitude == pytest.approx(-3.0)
    assert upper.value_quantity.to("m").magnitude == pytest.approx(6.0)
    assert unresolved is False


def test_continuous_piecewise_breakpoint_emits_only_at_with_dimensional_zero():
    context = NumericContext()
    _assign(context, "a", "3*m")
    _assign(context, "L", "6*m")
    x, a, L = sp.symbols("x a L", real=True)
    expr = sp.Piecewise((x-a, x < a), (2*(x-a), True), evaluate=False)
    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    points, _, _, _, unresolved = solve_extrema_exact(expr, x, domain, context)
    at_a = [point for point in points if sp.simplify(point.x_symbolic-a) == 0]
    assert [point.side for point in at_a] == ["at"]
    assert at_a[0].value_quantity.to("m").magnitude == pytest.approx(0.0)
    assert unresolved is False
