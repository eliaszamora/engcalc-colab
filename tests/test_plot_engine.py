import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import PlotResult
from engcalc_colab.parser import parse_cell


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def test_plot_reuses_function_and_numeric_state():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = 5*q*L/8 - q*x")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 4*m")
    result = eval_cell(engine, "plot(V(x), x, 0, L)")[-1]

    assert isinstance(result, PlotResult)
    assert result.display_label == "V(x)"
    assert len(result.x_values) == 201
    assert result.x_values[-1].to("m").magnitude == 4
    assert len(result.series) == 1
    assert result.series[0].display_label == "V(x)"


def test_plot_moment_preserves_dimensional_zero_at_right_boundary():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 4*m")
    result = eval_cell(engine, "plot(M(x), x, 0, L)")[-1]

    assert result.y_values[0].to("tonf*m").magnitude == -5.6
    assert abs(result.y_values[-1].to("tonf*m").magnitude) < 1e-12
    assert not result.y_values[-1].dimensionless
    assert result.series[0].is_moment


def test_plot_locally_overrides_preexisting_numeric_x():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = 5*q*L/8 - q*x")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 4*m\nx := 2.5*m")
    result = eval_cell(engine, "plot(V(x), x, 0, L)")[-1]

    assert len(result.x_values) == 201
    assert engine.numeric_context.get("x").to("m").magnitude == 2.5


def test_plot_builds_multiple_expression_series_on_one_shared_grid():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_D(x) = q_D*x*(L-x)/2\n"
        "M_L(x) = q_L*x*(L-x)/2\n"
        "q_D := 8*kN/m\nq_L := 5*kN/m\nL := 6*m",
    )

    result = eval_cell(engine, "plot(M_D(x), M_L(x), x, 0, L)")[-1]

    assert isinstance(result, PlotResult)
    assert len(result.x_values) == 201
    assert len(result.series) == 2
    assert [series.display_label for series in result.series] == ["M_D(x)", "M_L(x)"]
    assert result.display_label == "M(x)"
    assert all(series.is_moment for series in result.series)
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(36.0)
    assert result.series[1].y_values[100].to("kN*m").magnitude == pytest.approx(22.5)


def test_plot_parameter_sweep_builds_one_series_per_value():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nL := 6*m")

    result = eval_cell(
        engine,
        "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])",
    )[-1]

    assert result.display_label == "M(x)"
    assert len(result.series) == 3
    assert all(series.is_moment for series in result.series)
    assert [
        series.y_values[100].to("kN*m").magnitude
        for series in result.series
    ] == pytest.approx([22.5, 45.0, 67.5])
    assert all("q =" in series.display_label for series in result.series)


def test_plot_sweep_does_not_mutate_existing_parameter_or_x_value():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M(x) = q*x*(L-x)/2\n"
        "q := 2.8*tonf/m\nL := 6*m\nx := 1.5*m",
    )

    eval_cell(engine, "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])")

    assert engine.numeric_context.get("q").to("tonf/m").magnitude == pytest.approx(2.8)
    assert engine.numeric_context.get("x").to("m").magnitude == pytest.approx(1.5)


def test_plot_rejects_sweep_of_plotting_variable():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = x^2\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="plot sweep parameter 'x' cannot be the plotting variable",
    ):
        eval_cell(engine, "plot(M(x), x, 0, L, x=[0.5*m, 1.0*m])")


def test_plot_rejects_sweep_parameter_absent_from_expanded_expression():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x\nq := 5*kN/m\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="plot sweep parameter 'P' is not used in the plotted expression",
    ):
        eval_cell(engine, "plot(M(x), x, 0, L, P=[1*kN, 2*kN])")


def test_plot_rejects_incompatible_sweep_value_dimensions():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x^2\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="plot sweep values have incompatible units",
    ):
        eval_cell(engine, "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN])")


def test_plot_rejects_multiple_expressions_with_sweep():
    engine = EngineeringEngine()
    with pytest.raises(
        EngEvaluationError,
        match="plot parameter sweep requires exactly one expression",
    ):
        eval_cell(engine, "plot(q*x, q*x^2, x, 0, 2, q=[1, 2])")


def test_plot_rejects_series_with_incompatible_y_dimensions():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V(x) = q*(L-x)\nM(x) = q*(L-x)^2\nq := 5*kN/m\nL := 2*m",
    )
    with pytest.raises(
        EngEvaluationError,
        match="plot series have incompatible y dimensions",
    ):
        eval_cell(engine, "plot(V(x), M(x), x, 0, L)")


def test_plot_rejects_mixed_moment_and_non_moment_series_even_with_same_dimensions():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_A(x) = q*x^2\nR(x) = q*x^2\nq := 5*kN/m\nL := 2*m",
    )
    with pytest.raises(
        EngEvaluationError,
        match="plot cannot mix moment and non-moment series on one axis",
    ):
        eval_cell(engine, "plot(M_A(x), R(x), x, 0, L)")


def test_plot_reports_missing_non_plot_symbol():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = 5*q*L/8 - q*x\nL := 4*m")
    with pytest.raises(EngEvaluationError) as exc_info:
        eval_cell(engine, "plot(V(x), x, 0, L)")
    assert str(exc_info.value).startswith("line 1:")
    assert "numeric evaluation requires values for: q" in str(exc_info.value)


def test_plot_requires_identifier_variable_and_minimum_positional_arguments():
    engine = EngineeringEngine()
    cases = [
        (
            "plot(x, x, 0)",
            "plot expects at least 4 positional arguments: expression[, ...], variable, start, end",
        ),
        ("plot(x, x + 1, 0, 4)", "plot variable must be a symbolic identifier"),
    ]
    for source, expected in cases:
        with pytest.raises(EngEvaluationError, match=expected.replace("[", r"\[").replace("]", r"\]")):
            eval_cell(engine, source)


def test_plot_cannot_be_assigned_to_symbol():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError, match="plot must be a standalone statement"):
        eval_cell(engine, "A = plot(x, x, 0, 4)")


def test_plot_abs_samples_nonnegative_shear_values():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*(L/2-x)\nq := 4*kN/m\nL := 4*m")
    result = eval_cell(engine, "plot(abs(V(x)), x, 0, L)")[-1]

    values = [item.to("kN").magnitude for item in result.series[0].y_values]
    assert values[0] == pytest.approx(8.0)
    assert values[100] == pytest.approx(0.0)
    assert values[-1] == pytest.approx(8.0)
    assert min(values) >= 0.0
    assert not result.series[0].is_moment


def test_plot_abs_preserves_moment_classification_from_inner_function():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nq := 4*kN/m\nL := 4*m")
    result = eval_cell(engine, "plot(abs(M(x)), x, 0, L)")[-1]

    assert result.series[0].is_moment


def test_plot_accepts_direct_multiarg_response():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M(x, q, L) = q*x*(L-x)/2\n"
        "qD := 4*kN/m\n"
        "L := 5*m",
    )

    result = eval_cell(engine, "plot(M(x, qD, L), x, 0*m, L)")[-1]

    assert isinstance(result, PlotResult)
    assert len(result.x_values) == 201
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(12.5)


def test_specialized_multiarg_function_plots_normally():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M(x, q, L) = q*x*(L-x)/2\n"
        "M_D(x) = M(x, qD, L)\n"
        "qD := 4*kN/m\n"
        "L := 5*m",
    )

    result = eval_cell(engine, "plot(M_D(x), x, 0*m, L)")[-1]

    assert isinstance(result, PlotResult)
    assert len(result.x_values) == 201
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(12.5)
