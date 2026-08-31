import math

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ExtremaResult, IntersectionsResult, RootsResult
from engcalc_colab.parser import parse_cell


def evaluate_cell(engine: EngineeringEngine, source: str):
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("roots(log(x) - 1, x, 1, 10)", (math.e,)),
        (
            "roots(exp(x) - 3*x, x, 0, 3)",
            (0.619061286735945, 1.512134551657842),
        ),
        ("roots(x^5 - x - 1, x, 0, 2)", (1.167303978261419,)),
    ],
)
def test_v092_audit_roots_are_not_silent_false_negatives(source, expected):
    result = evaluate_cell(EngineeringEngine(), source)
    assert isinstance(result, RootsResult)
    actual = tuple(float(point.x_quantity.magnitude) for point in result.points)
    assert actual == pytest.approx(expected, rel=1e-9, abs=1e-10)


def test_v092_audit_log_intersection_is_found():
    result = evaluate_cell(
        EngineeringEngine(),
        "intersections(log(x), 1 + 0*x, x, 1, 10)",
    )
    assert isinstance(result, IntersectionsResult)
    assert len(result.points) == 1
    assert float(result.points[0].x_quantity.magnitude) == pytest.approx(
        math.e,
        rel=1e-9,
    )


def test_v092_audit_abs_extrema_has_global_minimum_at_cusp():
    result = evaluate_cell(
        EngineeringEngine(),
        "u(x) = abs(x - 2)\n"
        "extrema(u(x), x, 0, 4)",
    )
    assert isinstance(result, ExtremaResult)
    minimum = next(point for point in result.points if "global_min" in point.roles)
    assert float(minimum.x_quantity.magnitude) == pytest.approx(2.0)
    assert float(minimum.value_quantity.magnitude) == pytest.approx(0.0)


def test_engine_symbols_are_real_by_contract():
    engine = EngineeringEngine()
    assert engine.resolve_symbol("x").is_real is True


def test_dimensional_abs_extrema_keeps_units_and_cusp_minimum():
    result = evaluate_cell(
        EngineeringEngine(),
        "L := 4*m\n"
        "q := 2*kN/m\n"
        "M(x) = q*(x-L/2)\n"
        "extrema(abs(M(x)), x, 0, L)",
    )
    minimum = next(point for point in result.points if "global_min" in point.roles)
    assert minimum.x_quantity.to("m").magnitude == pytest.approx(2.0)
    assert minimum.value_quantity.to("kN").magnitude == pytest.approx(0.0)
