from decimal import Decimal
import math

import pytest
import sympy as sp

import engcalc_colab.characteristics.candidates as candidates
import engcalc_colab.characteristics.fallback as fallback
from engcalc_colab.characteristics import normalize_analysis_domain
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ExtremaResult, IntersectionsResult, RootsResult
from engcalc_colab.numeric import NumericContext
from engcalc_colab.parser import parse_cell


def evaluate_cell(engine: EngineeringEngine, source: str):
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


def _root_magnitudes(result: RootsResult):
    return tuple(float(point.x_quantity.magnitude) for point in result.points)


def test_n1_decimal_quadratic_roots_do_not_silently_disappear():
    result = evaluate_cell(
        EngineeringEngine(),
        "f(x) = 2.87*x^2 + -12.50459*x + 6.4876637\n"
        "roots(f(x), x, 0, 5)",
    )

    assert isinstance(result, RootsResult)
    assert _root_magnitudes(result) == pytest.approx(
        (0.602, 3.755),
        rel=1e-9,
        abs=1e-9,
    )


@pytest.mark.parametrize(
    ("a", "r1", "r2"),
    [
        ("1.25", "0.75", "4.25"),
        ("2.87", "0.602", "3.755"),
        ("0.83", "1.125", "7.375"),
        ("3.41", "2.250", "5.625"),
        ("1.07", "0.333", "8.444"),
        ("4.20", "3.125", "6.875"),
    ],
)
def test_n1_decimal_quadratic_family_preserves_known_roots(a, r1, r2):
    a_value = Decimal(a)
    r1_value = Decimal(r1)
    r2_value = Decimal(r2)
    linear = -(a_value * (r1_value + r2_value))
    constant = a_value * r1_value * r2_value
    source = (
        f"f(x) = {a_value}*x^2 + ({linear})*x + ({constant})\n"
        "roots(f(x), x, 0, 10)"
    )

    result = evaluate_cell(EngineeringEngine(), source)

    assert isinstance(result, RootsResult)
    assert _root_magnitudes(result) == pytest.approx(
        (float(r1_value), float(r2_value)),
        rel=1e-9,
        abs=1e-9,
    )


def test_n1_float_empty_exact_discovery_is_not_authoritative():
    x = sp.Symbol("x", real=True)
    expression = (
        sp.Float("2.87") * x**2
        - sp.Float("12.50459") * x
        + sp.Float("6.4876637")
    )

    discovery = candidates._coerce_exact_discovery(
        candidates._exact_real_solution_set(expression, x)
    )

    assert discovery.candidates == ()
    assert discovery.complete is False


@pytest.mark.parametrize(
    ("epsilon", "expected"),
    [
        ("1e-6", (0.999, 1.001)),
        ("1e-12", (0.999999, 1.000001)),
    ],
)
def test_n2_float_exact_candidates_accept_numerical_roundoff(epsilon, expected):
    result = evaluate_cell(
        EngineeringEngine(),
        f"roots((x-1)^2 - {epsilon}, x, 0, 2)",
    )

    assert isinstance(result, RootsResult)
    assert _root_magnitudes(result) == pytest.approx(
        expected,
        rel=1e-9,
        abs=1e-9,
    )
    assert all(point.provenance == "exact" for point in result.points)


def test_n2_materially_wrong_exact_candidate_is_rejected():
    context = NumericContext()
    x = sp.Symbol("x", real=True)
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(2))
    expression = (x - 1) ** 2 - sp.Float("1e-6")

    outcome = candidates._evaluate_root_candidate(
        expression,
        x,
        sp.Float("0.9"),
        domain,
        context,
        overrides=None,
        source_label=None,
    )

    assert outcome.point is None


def _engineering_response_engine():
    engine = EngineeringEngine()
    evaluate_cell(
        engine,
        "L := 6*m\n"
        "q := 12*kN/m\n"
        "V(x) = q*(L/2-x)\n"
        "M(x) = q*x*(L-x)/2",
    )
    return engine


def test_n3_roots_resolve_unit_literals_in_response_expression():
    result = evaluate_cell(
        _engineering_response_engine(),
        "roots(V(x) - 6*kN, x, 0, L)",
    )

    assert isinstance(result, RootsResult)
    assert len(result.points) == 1
    assert result.points[0].x_quantity.to("m").magnitude == pytest.approx(2.5)


def test_n3_extrema_resolve_unit_literals_in_response_expression():
    result = evaluate_cell(
        _engineering_response_engine(),
        "extrema(M(x) - 20*kN*m, x, 0, L)",
    )

    assert isinstance(result, ExtremaResult)
    assert len(result.points) == 3
    peak = next(point for point in result.points if "global_max" in point.roles)
    assert peak.x_quantity.to("m").magnitude == pytest.approx(3.0)
    assert peak.value_quantity.to("kN*m").magnitude == pytest.approx(34.0)


def test_n3_intersections_resolve_unit_literals_in_response_expression():
    result = evaluate_cell(
        _engineering_response_engine(),
        "intersections(M(x), 20*kN*m + 0*x, x, 0, L)",
    )

    assert isinstance(result, IntersectionsResult)
    assert len(result.points) == 2
    expected = (
        (18.0 - math.sqrt(204.0)) / 6.0,
        (18.0 + math.sqrt(204.0)) / 6.0,
    )
    actual = tuple(point.x_quantity.to("m").magnitude for point in result.points)
    assert actual == pytest.approx(expected, rel=1e-9, abs=1e-9)
    assert all(
        point.value_quantity.to("kN*m").magnitude == pytest.approx(20.0)
        for point in result.points
    )


def test_n3_fallback_works_with_boundary_resolved_unit_literals():
    context = NumericContext()
    x = sp.Symbol("x", real=True)
    L = sp.Symbol("L", real=True)
    q = sp.Symbol("q", real=True)
    kN = sp.Symbol("kN", real=True)
    context.values["L"] = context.ureg.Quantity(6, "m")
    context.values["q"] = context.ureg.Quantity(12, "kN/m")
    expression = q * (L / 2 - x) - 6 * kN
    domain = normalize_analysis_domain(context, sp.Integer(0), L)
    overrides = context.unit_literal_overrides(expression)

    points = fallback._fallback_roots(
        expression,
        x,
        domain,
        context,
        overrides=overrides,
        source_label=None,
    )

    assert len(points) == 1
    assert points[0].x_quantity.to("m").magnitude == pytest.approx(2.5)


def test_n4_extrema_simplifies_decidable_abs_symbolic_boundary_values():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "a := 3*m\n"
        "L := 6*m\n"
        "s(x) = piecewise(x-a, x < a, 2*(x-a))\n"
        "extrema(abs(s(x)), x, 0, L)",
    )

    assert isinstance(result, ExtremaResult)
    lower = min(result.points, key=lambda point: point.x_quantity.to("m").magnitude)
    upper = max(result.points, key=lambda point: point.x_quantity.to("m").magnitude)
    a_symbol = engine.resolve_symbol("a")
    L_symbol = engine.resolve_symbol("L")

    assert lower.value_quantity.to("m").magnitude == pytest.approx(3.0)
    assert upper.value_quantity.to("m").magnitude == pytest.approx(6.0)
    assert sp.simplify(lower.value_symbolic - a_symbol) == 0
    assert sp.simplify(upper.value_symbolic - (2 * L_symbol - 2 * a_symbol)) == 0
