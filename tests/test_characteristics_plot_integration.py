import sympy as sp
import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import PlotResult
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import _characteristic_requests, render_plot


def evaluate_cell(engine: EngineeringEngine, source: str):
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


def _global_point(series, role: str):
    return next(point for point in series.characteristics if role in point.roles)


def test_plot_characteristic_peak_is_exact_not_sampled():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "f(x) = -(x - 1/3)^2 + 2\n"
        "plot(f(x), x, 0, 1)",
    )

    assert isinstance(result, PlotResult)
    peak = _global_point(result.series[0], "global_max")
    assert peak.x_symbolic == sp.Rational(1, 3)
    assert float(peak.x_quantity.magnitude) == pytest.approx(1 / 3)
    assert len(result.x_values) == 201
    assert all(
        abs(float(quantity.magnitude) - 1 / 3) > 1e-12
        for quantity in result.x_values
    )


def test_characteristic_requests_use_authoritative_exact_plot_point():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "f(x) = -(x - 1/3)^2 + 2\n"
        "plot(f(x), x, 0, 1)",
    )

    maximum = next(
        request for request in _characteristic_requests(result)
        if request.role == "max"
    )

    assert float(maximum.x_quantity.magnitude) == pytest.approx(1 / 3)
    assert float(maximum.y_quantity.magnitude) == pytest.approx(2.0)
    assert all(
        abs(float(quantity.magnitude) - float(maximum.x_quantity.magnitude)) > 1e-12
        for quantity in result.x_values
    )


def test_single_series_renderer_anchors_annotation_at_exact_characteristic():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "f(x) = -(x - 1/3)^2 + 2\n"
        "plot(f(x), x, 0, 1)",
    )

    figure = render_plot(result)
    annotations = figure.axes[0].texts

    assert any(
        abs(float(annotation.xy[0]) - 1 / 3) < 1e-12
        and abs(float(annotation.xy[1]) - 2.0) < 1e-12
        for annotation in annotations
    )


def test_multi_series_plot_carries_independent_exact_characteristics():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "f(x) = -(x - 1/3)^2 + 2\n"
        "g(x) = -(x - 2/3)^2 + 3\n"
        "plot(f(x), g(x), x, 0, 1)",
    )

    first = _global_point(result.series[0], "global_max")
    second = _global_point(result.series[1], "global_max")

    assert first.x_symbolic == sp.Rational(1, 3)
    assert second.x_symbolic == sp.Rational(2, 3)
    assert float(first.value_quantity.magnitude) == pytest.approx(2.0)
    assert float(second.value_quantity.magnitude) == pytest.approx(3.0)


def test_parameter_sweep_passes_override_into_exact_characteristics():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "f(x) = -(x - q)^2 + 2\n"
        "plot(f(x), x, 0, 1, q=[1/3, 2/3])",
    )

    peaks = [_global_point(series, "global_max") for series in result.series]
    q_symbol = engine.resolve_symbol("q")

    assert [float(point.x_quantity.magnitude) for point in peaks] == pytest.approx(
        [1 / 3, 2 / 3]
    )
    assert [point.x_symbolic for point in peaks] == [q_symbol, q_symbol]
    assert [float(point.value_quantity.magnitude) for point in peaks] == pytest.approx(
        [2.0, 2.0]
    )


def test_piecewise_breakpoint_global_maximum_uses_exact_breakpoint_location():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "f(x) = piecewise(x, x < 1/3, 10, x <= 1/3, 1-x)\n"
        "plot(f(x), x, 0, 1)",
    )

    peak = _global_point(result.series[0], "global_max")
    maximum = next(
        request for request in _characteristic_requests(result)
        if request.role == "max"
    )

    # Piecewise sampling may deliberately inject the breakpoint into the 201-point
    # plotting grid. The authoritative contract is therefore the symbolic point and
    # rendered request coordinate, not absence from the adaptive sample grid.
    assert peak.x_symbolic == sp.Rational(1, 3)
    assert peak.side == "at"
    assert float(peak.x_quantity.magnitude) == pytest.approx(1 / 3)
    assert float(peak.value_quantity.magnitude) == pytest.approx(10.0)
    assert float(maximum.x_quantity.magnitude) == pytest.approx(1 / 3)
    assert float(maximum.y_quantity.magnitude) == pytest.approx(10.0)


def test_moment_characteristic_request_remains_visually_inverted_and_exact():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "M(x) = -(x - 1/3)^2 + 2\n"
        "plot(M(x), x, 0, 1)",
    )

    maximum = next(
        request for request in _characteristic_requests(result)
        if request.role == "max"
    )

    assert result.series[0].is_moment
    assert maximum.inverted is True
    assert float(maximum.x_quantity.magnitude) == pytest.approx(1 / 3)


def test_constant_plot_does_not_expand_extremum_interval_into_duplicate_markers():
    engine = EngineeringEngine()
    result = evaluate_cell(engine, "plot(5, x, 0, 1)")

    assert result.series[0].characteristics == ()
    assert len(_characteristic_requests(result)) == 1


def test_envelope_deliberately_keeps_sampled_characteristic_path_until_v092():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "f(x) = -(x - 1/3)^2 + 2\n"
        "g(x) = -(x - 2/3)^2 + 3\n"
        "envelope(f(x), g(x), x, 0, 1)",
    )

    assert result.kind == "envelope"
    assert all(series.characteristics == () for series in result.series)
    requests = _characteristic_requests(result)
    assert requests
    assert all(
        any(request.x_quantity is sample for sample in result.x_values)
        for request in requests
    )
