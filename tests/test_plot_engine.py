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


def test_plot_moment_preserves_dimensional_zero_at_right_boundary():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 4*m")
    result = eval_cell(engine, "plot(M(x), x, 0, L)")[-1]

    assert result.y_values[0].to("tonf*m").magnitude == -5.6
    assert abs(result.y_values[-1].to("tonf*m").magnitude) < 1e-12
    assert not result.y_values[-1].dimensionless


def test_plot_locally_overrides_preexisting_numeric_x():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = 5*q*L/8 - q*x")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 4*m\nx := 2.5*m")
    result = eval_cell(engine, "plot(V(x), x, 0, L)")[-1]

    assert len(result.x_values) == 201
    assert engine.numeric_context.get("x").to("m").magnitude == 2.5


def test_plot_reports_missing_non_plot_symbol():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = 5*q*L/8 - q*x\nL := 4*m")
    try:
        eval_cell(engine, "plot(V(x), x, 0, L)")
    except EngEvaluationError as exc:
        assert str(exc).startswith("line 1:")
        assert "numeric evaluation requires values for: q" in str(exc)
    else:
        raise AssertionError("expected EngEvaluationError")


def test_plot_requires_identifier_variable_and_four_arguments():
    engine = EngineeringEngine()
    cases = [
        ("plot(x, x, 0)", "plot expects 4 arguments: expression, variable, start, end"),
        ("plot(x, x + 1, 0, 4)", "plot variable must be a symbolic identifier"),
    ]
    for source, expected in cases:
        try:
            eval_cell(engine, source)
        except EngEvaluationError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError("expected EngEvaluationError")


def test_plot_cannot_be_assigned_to_symbol():
    engine = EngineeringEngine()
    try:
        eval_cell(engine, "A = plot(x, x, 0, 4)")
    except EngEvaluationError as exc:
        assert "plot must be a standalone statement" in str(exc)
    else:
        raise AssertionError("expected EngEvaluationError")
