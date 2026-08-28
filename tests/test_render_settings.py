import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import RenderSettings, render_aligned_results


def _evaluate_all(source: str):
    engine = EngineeringEngine()
    results = []
    for statement in parse_cell(source):
        results.append(engine.evaluate(statement))
    return results


def test_render_settings_defaults_preserve_current_two_decimal_output():
    settings = RenderSettings()
    assert settings.precision == 2
    assert settings.zero_tolerance == pytest.approx(1e-10)

    results = _evaluate_all("q := 2.845*tonf/m")
    latex = render_aligned_results(results, settings=settings)
    assert "2.85" in latex


def test_precision_applies_to_numeric_assignments_and_final_results():
    results = _evaluate_all(
        "q := 2.81234*tonf/m\n"
        "L := 4*m\n"
        "V = q*L\n"
        "numeric(V)"
    )

    latex = render_aligned_results(
        results,
        settings=RenderSettings(precision=4),
    )

    assert "2.8123" in latex
    assert "11.2494" in latex


def test_zero_tolerance_is_display_only_and_does_not_mutate_quantity():
    results = _evaluate_all("r := 0.000005*tonf")
    result = results[0]
    original_magnitude = float(result.quantity.magnitude)

    latex = render_aligned_results(
        results,
        settings=RenderSettings(precision=8, zero_tolerance=1e-5),
    )

    assert "0.00000000" in latex
    assert "0.00000500" not in latex
    assert float(result.quantity.magnitude) == pytest.approx(original_magnitude)


def test_zero_tolerance_applies_to_partial_function_coefficients():
    results = _evaluate_all(
        "M(x) = a + b*x\n"
        "a := 0.000005*tonf*m\n"
        "b := 1.23456*tonf\n"
        "numeric(M(x))"
    )

    latex = render_aligned_results(
        results,
        settings=RenderSettings(precision=3, zero_tolerance=1e-5),
    )

    assert "1.235" in latex
    assert "0.000005" not in latex


def test_render_settings_reject_invalid_values():
    with pytest.raises(ValueError, match="precision"):
        RenderSettings(precision=-1)
    with pytest.raises(ValueError, match="precision"):
        RenderSettings(precision=11)
    with pytest.raises(ValueError, match="zero_tolerance"):
        RenderSettings(zero_tolerance=-1)
