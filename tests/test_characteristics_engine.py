import pytest
import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import ExtremaResult, IntersectionsResult, RootsResult
from engcalc_colab.parser import parse_cell


def evaluate_cell(engine: EngineeringEngine, source: str):
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


def test_engine_roots_returns_typed_result_with_units():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "L := 6*m\n"
        "V(x) = x - L/2\n"
        "roots(V(x), x, 0, L)",
    )

    assert isinstance(result, RootsResult)
    assert result.statement.source == "roots(V(x), x, 0, L)"
    assert result.display_label == "V(x)"
    assert result.variable == "x"
    assert result.lower_quantity.to("m").magnitude == pytest.approx(0.0)
    assert result.upper_quantity.to("m").magnitude == pytest.approx(6.0)
    assert len(result.points) == 1
    assert sp.simplify(result.points[0].x_symbolic - engine.resolve_symbol("L") / 2) == 0
    assert result.points[0].x_quantity.to("m").magnitude == pytest.approx(3.0)


def test_engine_intersections_returns_typed_result_with_common_value():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "L := 6*m\n"
        "f(x) = x\n"
        "g(x) = L - x\n"
        "intersections(f(x), g(x), x, 0, L)",
    )

    assert isinstance(result, IntersectionsResult)
    assert result.left_label == "f(x)"
    assert result.right_label == "g(x)"
    assert result.variable == "x"
    assert len(result.points) == 1
    point = result.points[0]
    assert sp.simplify(point.x_symbolic - engine.resolve_symbol("L") / 2) == 0
    assert point.x_quantity.to("m").magnitude == pytest.approx(3.0)
    assert point.value_quantity.to("m").magnitude == pytest.approx(3.0)


def test_engine_extrema_returns_typed_result_with_unbounded_flags_and_roles():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "L := 6*m\n"
        "q := 10*kN/m\n"
        "M(x) = q*x*(L-x)/2\n"
        "extrema(M(x), x, 0, L)",
    )

    assert isinstance(result, ExtremaResult)
    assert result.display_label == "M(x)"
    assert result.variable == "x"
    assert result.unbounded_above is False
    assert result.unbounded_below is False
    peak = next(point for point in result.points if "global_max" in point.roles)
    assert sp.simplify(peak.x_symbolic - engine.resolve_symbol("L") / 2) == 0
    assert peak.x_quantity.to("m").magnitude == pytest.approx(3.0)
    assert peak.value_quantity.to("kN*m").magnitude == pytest.approx(45.0)


def test_engine_characteristics_accept_indexed_matrix_scalar_response():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "K(x) = [x-2, 0; 0, x+1]\n"
        "roots(K(x)[1,1], x, 0, 4)",
    )

    assert isinstance(result, RootsResult)
    assert len(result.points) == 1
    assert result.points[0].x_symbolic == sp.Integer(2)
    assert result.points[0].x_quantity.magnitude == pytest.approx(2.0)


def test_engine_characteristics_reject_whole_matrix_with_actionable_diagnostic():
    engine = EngineeringEngine()
    evaluate_cell(engine, "K(x) = [x-2, 0; 0, x+1]")

    with pytest.raises(
        EngEvaluationError,
        match=r"line 1: roots response must be scalar; index the matrix first, for example A\[1,1\]",
    ):
        evaluate_cell(engine, "roots(K(x), x, 0, 4)")


def test_engine_intersections_reject_incompatible_response_dimensions_with_line_number():
    engine = EngineeringEngine()
    source = (
        "L := 4*m\n"
        "q := 2*kN/m\n"
        "V(x) = q*x\n"
        "d(x) = x\n"
        "intersections(V(x), d(x), x, 0, L)"
    )

    with pytest.raises(
        EngEvaluationError,
        match=r"line 5: intersections responses have incompatible dimensions",
    ):
        evaluate_cell(engine, source)


def test_engine_characteristic_unresolved_bound_is_operation_specific_and_line_numbered():
    engine = EngineeringEngine()
    source = (
        "f(x) = x - 1\n"
        "roots(f(x), x, 0, L)"
    )

    with pytest.raises(
        EngEvaluationError,
        match=r"line 2: roots domain bound must be numerically resolvable",
    ):
        evaluate_cell(engine, source)


def test_engine_extrema_reversed_domain_diagnostic_names_operation_and_line():
    engine = EngineeringEngine()
    source = (
        "f(x) = -(x-1)^2\n"
        "extrema(f(x), x, 4, 0)"
    )

    with pytest.raises(
        EngEvaluationError,
        match=r"line 2: extrema domain requires lower < upper",
    ):
        evaluate_cell(engine, source)


def _task6_seeded_engine():
    engine = EngineeringEngine()
    evaluate_cell(
        engine,
        "L := 6*m\n"
        "q := 12*kN/m\n"
        "M(x) = q*x*(L-x)/2\n"
        "M2(x) = q*x*(L-x)/3\n"
        "V(x) = q*(L/2-x)",
    )
    return engine


def test_direct_unit_literals_are_consistent_across_domain_bearing_apis():
    engine = _task6_seeded_engine()

    roots = evaluate_cell(engine, "roots(V(x), x, 0*m, 6*m)")
    extrema = evaluate_cell(engine, "extrema(M(x), x, 0*m, 6000*mm)")
    intersections = evaluate_cell(
        engine, "intersections(M(x), M2(x), x, 0*m, 6*m)"
    )
    plot = evaluate_cell(engine, "plot(M(x), x, 0*m, 6*m)")
    table = evaluate_cell(engine, "table(M(x), x, 0*m, 6*m, 5)")

    assert roots.points[0].x_quantity.to("m").magnitude == pytest.approx(3.0)
    peak = next(point for point in extrema.points if "global_max" in point.roles)
    assert peak.x_quantity.to("mm").magnitude == pytest.approx(3000.0)
    assert len(intersections.points) == 2
    assert plot.x_values[-1].to("m").magnitude == pytest.approx(6.0)
    assert table.point_values[-1].to("m").magnitude == pytest.approx(6.0)


def test_direct_unit_literal_bounds_reject_incompatible_domain_units():
    engine = _task6_seeded_engine()
    with pytest.raises(EngEvaluationError, match="incompatible"):
        evaluate_cell(engine, "roots(V(x), x, 0*m, 2*s)")
