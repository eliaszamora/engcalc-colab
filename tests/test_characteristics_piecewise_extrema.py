import sympy as sp

from engcalc_colab.characteristics import normalize_analysis_domain, solve_extrema_exact
from engcalc_colab.numeric import NumericContext


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
        (2, x < 2),
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
