import ast

import matplotlib
matplotlib.use("Agg")
import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def test_plot_parser_accepts_optional_title_and_axis_label_strings():
    statement = parse_cell(
        'plot(M(x), x, 0, L, title="Diagrama de momento", '
        'xlabel="Longitud", ylabel="Momento flector")'
    )[0]
    call = statement.expression.body

    assert [item.arg for item in call.keywords] == ["title", "xlabel", "ylabel"]
    assert [item.value.value for item in call.keywords] == [
        "Diagrama de momento",
        "Longitud",
        "Momento flector",
    ]
    assert all(isinstance(item.value, ast.Constant) for item in call.keywords)


def test_envelope_parser_accepts_presentation_options_with_multiple_responses():
    statement = parse_cell(
        'envelope(M_D(x), M_L(x), x, 0, L, '
        'title="Envolvente de momento", ylabel="Momento")'
    )[0]
    call = statement.expression.body

    assert [item.arg for item in call.keywords] == ["title", "ylabel"]


def test_plot_parser_allows_one_sweep_together_with_presentation_options():
    statement = parse_cell(
        'plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m], '
        'title="Comparación", xlabel="Posición")'
    )[0]
    call = statement.expression.body

    assert [item.arg for item in call.keywords] == ["q", "title", "xlabel"]
    assert isinstance(call.keywords[0].value, ast.List)


def test_plot_and_envelope_reject_non_string_or_empty_presentation_options():
    invalid = [
        'plot(M(x), x, 0, L, title=3)',
        'plot(M(x), x, 0, L, xlabel="   ")',
        'envelope(M_A(x), M_B(x), x, 0, L, ylabel=["Momento"])',
    ]

    for source in invalid:
        with pytest.raises(EngSyntaxError, match="non-empty string"):
            parse_cell(source)


def test_plot_still_rejects_more_than_one_actual_sweep_parameter():
    with pytest.raises(EngSyntaxError, match="at most one sweep parameter"):
        parse_cell(
            'plot(M(x), x, 0, L, q=[1, 2], P=[3, 4], title="Casos")'
        )


def test_plot_engine_transports_presentation_options_without_changing_sampling():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nq := 10*kN/m\nL := 6*m")

    result = eval_cell(
        engine,
        'plot(M(x), x, 0, L, title="Diagrama de momento flector", '
        'xlabel="Longitud", ylabel="Momento")',
    )[-1]

    assert len(result.x_values) == 201
    assert result.title == "Diagrama de momento flector"
    assert result.xlabel == "Longitud"
    assert result.ylabel == "Momento"


def test_plot_metadata_can_coexist_with_parameter_sweep():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nL := 6*m")

    result = eval_cell(
        engine,
        'plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m], '
        'title="Dos cargas", ylabel="Momento")',
    )[-1]

    assert len(result.series) == 2
    assert result.title == "Dos cargas"
    assert result.ylabel == "Momento"


def test_custom_plot_labels_keep_units_automatic():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nq := 10*kN/m\nL := 6*m")
    result = eval_cell(
        engine,
        'plot(M(x), x, 0, L, title="Diagrama de momento flector", '
        'xlabel="Longitud", ylabel="Momento")',
    )[-1]

    axis = render_plot(result).axes[0]

    assert axis.get_title() == "Diagrama de momento flector"
    assert axis.get_xlabel() == "Longitud [m]"
    assert axis.get_ylabel() == "Momento [kN·m]"
    assert axis.yaxis_inverted()


def test_custom_signed_envelope_labels_keep_units_automatic():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_A(x) = q*x*(L-x)/2\n"
        "M_B(x) = -0.5*q*x*(L-x)/2\n"
        "q := 8*kN/m\nL := 6*m",
    )
    result = eval_cell(
        engine,
        'envelope(M_A(x), M_B(x), x, 0, L, '
        'title="Envolvente última", xlabel="Longitud", ylabel="Momento")',
    )[-1]

    axis = render_plot(result).axes[0]

    assert axis.get_title() == "Envolvente última"
    assert axis.get_xlabel() == "Longitud [m]"
    assert axis.get_ylabel() == "Momento [kN·m]"


def test_custom_magnitude_envelope_title_and_labels_override_only_requested_text():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V_A(x) = 6*kN - 4*kN/m*x\n"
        "V_B(x) = -9*kN + 1*kN/m*x\n"
        "L := 2*m",
    )
    result = eval_cell(
        engine,
        'envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L, '
        'title="Envolvente de corte", ylabel="Corte")',
    )[-1]

    axis = render_plot(result).axes[0]

    assert axis.get_title() == "Envolvente de corte"
    assert axis.get_xlabel() == "x [m]"
    assert axis.get_ylabel() == "Corte [kN]"
