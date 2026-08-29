import pytest
from IPython.display import Math
from matplotlib.figure import Figure

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import PartialNumericEvaluationResult, PlotResult
from engcalc_colab.parser import parse_cell


def run_cell(source: str):
    engine = EngineeringEngine()
    return engine, [engine.evaluate(stmt) for stmt in parse_cell(source)]


def test_scalar_math_plot_samples_unit_aware_sine_response():
    _, results = run_cell(
        """
f(x) = A*sin(pi*x/L)
A := 10*mm
L := 4*m
plot(f(x), x, 0, L)
"""
    )
    result = results[-1]

    assert isinstance(result, PlotResult)
    assert len(result.x_values) == 201
    assert result.x_values[0].to("m").magnitude == pytest.approx(0.0)
    assert result.x_values[-1].to("m").magnitude == pytest.approx(4.0)
    assert result.series[0].y_values[0].to("mm").magnitude == pytest.approx(0.0, abs=1e-12)
    assert result.series[0].y_values[100].to("mm").magnitude == pytest.approx(10.0)
    assert result.series[0].y_values[-1].to("mm").magnitude == pytest.approx(0.0, abs=1e-12)


def test_scalar_math_partial_numeric_keeps_pre_071_boundary_explicit():
    _, results = run_cell(
        """
f(x) = A*sin(pi*x/L)
A := 10*mm
L := 4*m
numeric(f(x))
"""
    )
    result = results[-1]

    assert isinstance(result, PartialNumericEvaluationResult)
    assert result.unresolved_symbols == ("x",)
    assert result.evaluated_terms is None


def test_eng_magic_accepts_scalar_math_and_plot(monkeypatch, capsys):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "f(x) = A*sin(pi*x/L)\n"
        "A := 10*mm\n"
        "L := 4*m\n"
        "theta := sin(30*deg)\n"
        "plot(f(x), x, 0, L)",
    )

    assert capsys.readouterr().out == ""
    assert len(displayed) == 2
    assert isinstance(displayed[0], Math)
    assert isinstance(displayed[1], Figure)
    assert "0.50" in displayed[0].data
