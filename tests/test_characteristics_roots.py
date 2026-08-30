import ast

import pytest
import sympy as sp

from engcalc_colab.characteristics import (
    AnalysisDomain,
    normalize_analysis_domain,
    solve_roots_exact,
)
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.numeric import NumericContext


def _assign(context: NumericContext, name: str, source: str):
    return context.assign(name, ast.parse(source, mode="eval"))


def test_normalize_analysis_domain_preserves_symbolic_bounds_and_physical_unit():
    context = NumericContext()
    _assign(context, "L", "6*m")
    L = sp.Symbol("L")

    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    assert isinstance(domain, AnalysisDomain)
    assert domain.lower_symbolic == 0
    assert domain.upper_symbolic == L
    assert domain.lower_quantity.to("m").magnitude == 0
    assert domain.upper_quantity.to("m").magnitude == 6
    assert domain.unit == context.ureg.meter


def test_domain_adapts_exact_dimensionless_zero_to_dimensional_endpoint():
    context = NumericContext()
    _assign(context, "L", "6000*mm")
    L = sp.Symbol("L")

    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    assert domain.lower_quantity.units == domain.upper_quantity.units
    assert domain.lower_quantity.to("mm").magnitude == 0
    assert domain.upper_quantity.to("mm").magnitude == 6000


@pytest.mark.parametrize(
    ("lower", "upper"),
    [
        (sp.Integer(2), sp.Integer(2)),
        (sp.Integer(3), sp.Integer(2)),
    ],
)
def test_domain_rejects_zero_width_and_reversed_bounds(lower, upper):
    context = NumericContext()

    with pytest.raises(EngEvaluationError, match="lower < upper"):
        normalize_analysis_domain(context, lower, upper)


def test_domain_rejects_incompatible_bound_units():
    context = NumericContext()
    _assign(context, "L", "2*m")
    _assign(context, "T", "3*s")

    with pytest.raises(EngEvaluationError, match="incompatible units"):
        normalize_analysis_domain(context, sp.Symbol("L"), sp.Symbol("T"))


def test_domain_rejects_nonfinite_bound():
    context = NumericContext()

    with pytest.raises(EngEvaluationError, match="finite"):
        normalize_analysis_domain(context, sp.Integer(0), sp.oo)


def test_domain_rejects_unresolved_bound_with_characteristic_diagnostic():
    context = NumericContext()

    with pytest.raises(EngEvaluationError, match="domain bound must be numerically resolvable"):
        normalize_analysis_domain(context, sp.Integer(0), sp.Symbol("L"))


def test_exact_polynomial_roots_preserve_symbolic_locations_and_physical_order():
    context = NumericContext()
    _assign(context, "L", "6*m")
    x, L = sp.symbols("x L")
    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    points, intervals, unresolved = solve_roots_exact(
        (x - L / 3) * (x - 2 * L / 3),
        x,
        domain,
        context,
        source_label="V(x)",
    )

    assert [sp.simplify(point.x_symbolic) for point in points] == [L / 3, 2 * L / 3]
    assert [point.x_quantity.to("m").magnitude for point in points] == [2, 4]
    assert all(point.provenance == "exact" for point in points)
    assert all(point.source_label == "V(x)" for point in points)
    assert intervals == ()
    assert unresolved is False


def test_repeated_root_is_deduplicated():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_roots_exact((x - 2) ** 2, x, domain, context)

    assert [point.x_symbolic for point in points] == [sp.Integer(2)]
    assert intervals == ()
    assert unresolved is False


def test_closed_domain_includes_endpoint_roots():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, _, unresolved = solve_roots_exact(x * (x - 4), x, domain, context)

    assert [point.x_symbolic for point in points] == [sp.Integer(0), sp.Integer(4)]
    assert unresolved is False


def test_roots_outside_domain_are_filtered():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    points, intervals, unresolved = solve_roots_exact(x - 5, x, domain, context)

    assert points == ()
    assert intervals == ()
    assert unresolved is False


def test_expression_with_no_real_roots_returns_empty_exact_result():
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(-2), sp.Integer(2))

    points, intervals, unresolved = solve_roots_exact(x**2 + 1, x, domain, context)

    assert points == ()
    assert intervals == ()
    assert unresolved is False


def test_dimensional_response_root_preserves_zero_response_unit():
    context = NumericContext()
    _assign(context, "L", "6*m")
    _assign(context, "q", "12*kN/m")
    x, L, q = sp.symbols("x L q")
    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    points, intervals, unresolved = solve_roots_exact(
        q * (x - L / 2),
        x,
        domain,
        context,
        source_label="V(x)",
    )

    assert len(points) == 1
    point = points[0]
    assert sp.simplify(point.x_symbolic - L / 2) == 0
    assert point.x_quantity.to("m").magnitude == 3
    assert point.value_symbolic == 0
    assert point.value_quantity.to("kN").magnitude == pytest.approx(0.0)
    assert intervals == ()
    assert unresolved is False


def test_exact_solver_reports_unresolved_without_inventing_sampled_answer(monkeypatch):
    context = NumericContext()
    x = sp.Symbol("x")
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    monkeypatch.setattr(sp, "solveset", lambda *args, **kwargs: sp.ConditionSet(x, sp.true, sp.S.Reals))
    monkeypatch.setattr(sp, "solve", lambda *args, **kwargs: [])

    points, intervals, unresolved = solve_roots_exact(sp.sin(x) - x / 2, x, domain, context)

    assert points == ()
    assert intervals == ()
    assert unresolved is True
