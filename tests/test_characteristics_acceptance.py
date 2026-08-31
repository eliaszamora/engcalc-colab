import math

import pytest
import sympy as sp

import engcalc_colab.characteristics.candidates as candidates
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ExtremaResult, IntersectionsResult, RootsResult
from engcalc_colab.parser import parse_cell


def evaluate_cell(engine: EngineeringEngine, source: str):
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


def test_v091_characteristics_end_to_end_engineering_worksheet(monkeypatch):
    engine = EngineeringEngine()
    evaluate_cell(
        engine,
        "L := 6*m\n"
        "q := 12*kN/m\n"
        "M(x) = q*x*(L-x)/2\n"
        "V(x) = q*(L/2-x)\n"
        "M2(x) = q*x*(L-x)/3\n"
        "K(x) = [x + L, 0; 0, 2*x + L]",
    )

    extrema = evaluate_cell(engine, "extrema(M(x), x, 0, L)")
    roots = evaluate_cell(engine, "roots(V(x), x, 0, L)")
    intersections = evaluate_cell(
        engine,
        "intersections(M(x), M2(x), x, 0, L)",
    )
    matrix_root = evaluate_cell(
        engine,
        "roots(K(x)[1,1] - 7*m, x, 0, L)",
    )

    assert isinstance(extrema, ExtremaResult)
    peak = next(point for point in extrema.points if "global_max" in point.roles)
    assert sp.simplify(peak.x_symbolic - engine.resolve_symbol("L") / 2) == 0
    assert peak.x_quantity.to("m").magnitude == pytest.approx(3.0)
    assert peak.value_quantity.to("kN*m").magnitude == pytest.approx(54.0)
    assert peak.provenance == "exact"

    assert isinstance(roots, RootsResult)
    assert len(roots.points) == 1
    shear_zero = roots.points[0]
    assert sp.simplify(shear_zero.x_symbolic - engine.resolve_symbol("L") / 2) == 0
    assert shear_zero.x_quantity.to("m").magnitude == pytest.approx(3.0)
    assert shear_zero.provenance == "exact"

    assert isinstance(intersections, IntersectionsResult)
    assert len(intersections.points) == 2
    assert [point.x_quantity.to("m").magnitude for point in intersections.points] == pytest.approx(
        [0.0, 6.0]
    )
    assert all(point.value_quantity.to("kN*m").magnitude == pytest.approx(0.0) for point in intersections.points)
    assert all(point.provenance == "exact" for point in intersections.points)

    assert isinstance(matrix_root, RootsResult)
    assert len(matrix_root.points) == 1
    assert matrix_root.points[0].x_quantity.to("m").magnitude == pytest.approx(1.0)
    assert matrix_root.points[0].provenance == "exact"

    jump = evaluate_cell(
        engine,
        "J(x) = piecewise(-1, x < 2, 1)\n"
        "roots(J(x), x, 0, 4)",
    )
    assert isinstance(jump, RootsResult)
    assert jump.points == ()
    assert jump.intervals == ()

    monkeypatch.setattr(
        candidates,
        "_exact_real_solution_set",
        lambda expression, variable: ((), True),
    )
    fallback = evaluate_cell(
        engine,
        "F(x) = sin(x) - 1/2\n"
        "roots(F(x), x, 0, 4)",
    )
    assert isinstance(fallback, RootsResult)
    assert len(fallback.points) == 2
    assert all(point.provenance == "numeric" for point in fallback.points)
    assert [float(point.x_quantity.magnitude) for point in fallback.points] == pytest.approx(
        [math.pi / 6, 5 * math.pi / 6],
        rel=1e-9,
        abs=1e-10,
    )


def test_v091_user_facing_fallback_example_is_naturally_numeric():
    engine = EngineeringEngine()
    result = evaluate_cell(engine, "roots(cos(x) - x, x, 0, 1)")

    assert isinstance(result, RootsResult)
    assert len(result.points) == 1
    point = result.points[0]
    assert point.provenance == "numeric"
    assert float(point.x_quantity.magnitude) == pytest.approx(
        0.7390851332151607,
        rel=1e-9,
        abs=1e-10,
    )


def test_v092_audit_remediations_end_to_end_without_monkeypatching():
    engine = EngineeringEngine()

    root_cases = [
        ("roots(log(x)-1, x, 1, 10)", (math.e,)),
        (
            "roots(exp(x)-3*x, x, 0, 3)",
            (0.619061286735945, 1.512134551657842),
        ),
        ("roots(x^5-x-1, x, 0, 2)", (1.167303978261419,)),
    ]
    for source, expected in root_cases:
        result = evaluate_cell(engine, source)
        assert isinstance(result, RootsResult)
        actual = tuple(float(point.x_quantity.magnitude) for point in result.points)
        assert actual == pytest.approx(expected, rel=1e-9, abs=1e-10)

    intersection = evaluate_cell(
        engine,
        "intersections(log(x), 1+0*x, x, 1, 10)",
    )
    assert isinstance(intersection, IntersectionsResult)
    assert len(intersection.points) == 1
    assert float(intersection.points[0].x_quantity.magnitude) == pytest.approx(
        math.e,
        rel=1e-9,
        abs=1e-10,
    )

    extrema = evaluate_cell(engine, "extrema(abs(x-2), x, 0, 4)")
    assert isinstance(extrema, ExtremaResult)
    minimum = next(point for point in extrema.points if "global_min" in point.roles)
    assert float(minimum.x_quantity.magnitude) == pytest.approx(2.0)
    assert float(minimum.value_quantity.magnitude) == pytest.approx(0.0)


def test_v092_direct_unit_literal_root_bounds_are_natural_end_to_end():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "L := 6*m\n"
        "V(x) = x-L/2\n"
        "roots(V(x), x, 0*m, 6000*mm)",
    )

    assert isinstance(result, RootsResult)
    assert len(result.points) == 1
    point = result.points[0]
    assert point.x_quantity.to("m").magnitude == pytest.approx(3.0)
    assert point.provenance == "exact"


def test_v092_continuous_piecewise_extrema_preserve_selected_boundary_value():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "a := 3*m\n"
        "L := 6*m\n"
        "f(x) = piecewise(x-a, x < a, 2*(x-a))\n"
        "extrema(f(x), x, 0*m, L)",
    )

    assert isinstance(result, ExtremaResult)
    at_break = [
        point
        for point in result.points
        if point.x_quantity.to("m").magnitude == pytest.approx(3.0)
    ]
    assert [point.side for point in at_break] == ["at"]
    assert at_break[0].value_quantity.to("m").magnitude == pytest.approx(0.0)

    lower = next(
        point
        for point in result.points
        if point.x_quantity.to("m").magnitude == pytest.approx(0.0)
    )
    upper = next(
        point
        for point in result.points
        if point.x_quantity.to("m").magnitude == pytest.approx(6.0)
    )
    assert lower.value_quantity.to("m").magnitude == pytest.approx(-3.0)
    assert upper.value_quantity.to("m").magnitude == pytest.approx(6.0)
