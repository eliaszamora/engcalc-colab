import math

import pytest
import sympy as sp

import engcalc_colab.characteristics as characteristics
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
        characteristics,
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
