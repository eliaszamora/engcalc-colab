import ast

import pytest
import sympy as sp

from engcalc_colab.characteristics import (
    normalize_analysis_domain,
    solve_intersections_exact,
)
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.numeric import NumericContext


def _assign(context: NumericContext, name: str, source: str):
    return context.assign(name, ast.parse(source, mode="eval"))


def test_polynomial_intersections_are_exact_and_keep_common_response():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_intersections_exact(
        x**2,
        2 * x,
        x,
        domain,
        context,
        left_label="M1(x)",
        right_label="M2(x)",
    )

    assert [point.x_symbolic for point in points] == [sp.Integer(0), sp.Integer(2)]
    assert [sp.simplify(point.value_symbolic) for point in points] == [0, 4]
    assert all(point.roles == ("intersection",) for point in points)
    assert all(point.provenance == "exact" for point in points)
    assert intervals == ()
    assert unresolved is False


def test_endpoint_intersection_is_included():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_intersections_exact(
        x,
        sp.Integer(0),
        x,
        domain,
        context,
    )

    assert [point.x_symbolic for point in points] == [sp.Integer(0)]
    assert intervals == ()
    assert unresolved is False


def test_no_intersection_returns_empty_exact_result():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_intersections_exact(
        x + 1,
        sp.Integer(0),
        x,
        domain,
        context,
    )

    assert points == ()
    assert intervals == ()
    assert unresolved is False


def test_identical_responses_return_closed_coincident_domain_interval():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_intersections_exact(
        x + 1,
        x + 1,
        x,
        domain,
        context,
    )

    assert points == ()
    assert len(intervals) == 1
    interval = intervals[0]
    assert interval.role == "coincident"
    assert interval.lower_symbolic == 0
    assert interval.upper_symbolic == 4
    assert interval.lower_closed is True
    assert interval.upper_closed is True
    assert unresolved is False


def test_dimensional_intersection_preserves_exact_symbolic_location_and_force_value():
    context = NumericContext()
    _assign(context, "L", "4*m")
    _assign(context, "q", "10*kN/m")
    _assign(context, "P", "20*kN")
    x, L, q, P = sp.symbols("x L q P")
    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    points, intervals, unresolved = solve_intersections_exact(
        q * x,
        P - q * x,
        x,
        domain,
        context,
        left_label="V1(x)",
        right_label="V2(x)",
    )

    assert len(points) == 1
    point = points[0]
    assert sp.simplify(point.x_symbolic - P / (2 * q)) == 0
    assert point.x_quantity.to("m").magnitude == pytest.approx(1.0)
    assert sp.simplify(point.value_symbolic - P / 2) == 0
    assert point.value_quantity.to("kN").magnitude == pytest.approx(10.0)
    assert intervals == ()
    assert unresolved is False


def test_incompatible_response_dimensions_are_rejected_before_symbolic_subtraction():
    context = NumericContext()
    _assign(context, "L", "4*m")
    _assign(context, "q", "10*kN/m")
    x, L, q = sp.symbols("x L q")
    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    with pytest.raises(EngEvaluationError, match="intersections responses have incompatible dimensions"):
        solve_intersections_exact(q * x, x, x, domain, context)


def test_piecewise_intersection_is_solved_inside_its_governing_region():
    context = NumericContext()
    x = sp.Symbol("x")
    left = sp.Piecewise((x, x < 2), (x + 2, True), evaluate=False)
    right = sp.Integer(1)
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_intersections_exact(
        left,
        right,
        x,
        domain,
        context,
    )

    assert [point.x_symbolic for point in points] == [sp.Integer(1)]
    assert intervals == ()
    assert unresolved is False


def test_piecewise_jump_crossing_without_actual_equality_is_not_intersection():
    context = NumericContext()
    x = sp.Symbol("x")
    left = sp.Piecewise((-1, x < 2), (1, True), evaluate=False)
    right = sp.Integer(0)
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_intersections_exact(
        left,
        right,
        x,
        domain,
        context,
    )

    assert points == ()
    assert intervals == ()
    assert unresolved is False


def test_piecewise_coincident_subinterval_preserves_open_breakpoint_topology():
    context = NumericContext()
    x = sp.Symbol("x")
    left = sp.Piecewise((x, x < 2), (x + 1, True), evaluate=False)
    right = x
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_intersections_exact(
        left,
        right,
        x,
        domain,
        context,
    )

    assert points == ()
    assert len(intervals) == 1
    interval = intervals[0]
    assert interval.role == "coincident"
    assert interval.lower_symbolic == 0
    assert interval.upper_symbolic == 2
    assert interval.lower_closed is True
    assert interval.upper_closed is False
    assert unresolved is False


def test_piecewise_union_uses_breakpoints_from_both_responses():
    context = NumericContext()
    x = sp.Symbol("x")
    left = sp.Piecewise((x, x < 1), (x + 1, True), evaluate=False)
    right = sp.Piecewise((x + 2, x < 3), (x + 1, True), evaluate=False)
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_intersections_exact(
        left,
        right,
        x,
        domain,
        context,
    )

    assert points == ()
    assert len(intervals) == 1
    interval = intervals[0]
    assert interval.role == "coincident"
    assert interval.lower_symbolic == 3
    assert interval.upper_symbolic == 4
    assert interval.lower_closed is True
    assert interval.upper_closed is True
    assert unresolved is False


def test_indexed_immutable_matrix_scalar_is_valid_intersection_response():
    context = NumericContext()
    x = sp.Symbol("x")
    matrix = sp.ImmutableMatrix([[x**2, 0], [0, 1]])
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_intersections_exact(
        matrix[0, 0],
        2 * x,
        x,
        domain,
        context,
    )

    assert [point.x_symbolic for point in points] == [sp.Integer(0), sp.Integer(2)]
    assert intervals == ()
    assert unresolved is False


def test_incomplete_intersection_discovery_merges_exact_hint_and_fallback(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(3))
    unresolved_set = sp.ConditionSet(
        x,
        sp.Eq(sp.exp(x) - 3*x, 0, evaluate=False),
        sp.S.Reals,
    )

    monkeypatch.setattr(sp, "solveset", lambda *args, **kwargs: unresolved_set)
    monkeypatch.setattr(
        sp,
        "solve",
        lambda *args, **kwargs: [-sp.LambertW(-sp.Rational(1, 3))],
    )

    points, intervals, unresolved = solve_intersections_exact(
        sp.exp(x),
        3*x,
        x,
        domain,
        context,
        left_label="f(x)",
        right_label="g(x)",
    )

    assert intervals == ()
    assert unresolved is False
    assert tuple(float(point.x_quantity.magnitude) for point in points) == pytest.approx(
        (0.619061286735945, 1.512134551657842),
        rel=1e-9,
        abs=1e-10,
    )
    assert tuple(point.provenance for point in points) == ("exact", "numeric")
    assert all(point.roles == ("intersection",) for point in points)
