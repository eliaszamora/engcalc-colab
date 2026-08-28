import ast

import pytest

from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.models import PlotResult, PlotSeries
from engcalc_colab.parser import parse_cell


def test_plot_call_is_accepted_by_restricted_parser():
    statement = parse_cell("plot(M(x), x, 0, L)")[0]
    assert statement.target is None
    assert statement.expression.body.func.id == "plot"
    assert len(statement.expression.body.args) == 4


def test_plot_name_is_reserved_as_assignment_target():
    with pytest.raises(EngSyntaxError, match="reserved identifier 'plot'"):
        parse_cell("plot = 3")


def test_plot_accepts_multiple_positional_expressions():
    statement = parse_cell("plot(M_D(x), M_L(x), x, 0, L)")[0]
    call = statement.expression.body
    assert call.func.id == "plot"
    assert len(call.args) == 5
    assert call.keywords == []


def test_plot_accepts_one_restricted_parameter_sweep_keyword():
    statement = parse_cell(
        "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])"
    )[0]
    call = statement.expression.body
    assert len(call.args) == 4
    assert len(call.keywords) == 1
    assert call.keywords[0].arg == "q"
    assert isinstance(call.keywords[0].value, ast.List)
    assert len(call.keywords[0].value.elts) == 2


def test_non_plot_keyword_arguments_remain_rejected():
    with pytest.raises(EngSyntaxError, match="keyword arguments are unsupported"):
        parse_cell("simplify(x, mode=[1])")


def test_plot_rejects_more_than_one_sweep_keyword():
    with pytest.raises(
        EngSyntaxError,
        match="plot accepts at most one sweep parameter",
    ):
        parse_cell("plot(M(x), x, 0, L, q=[1], P=[2])")


def test_plot_rejects_empty_or_non_list_sweep_values():
    with pytest.raises(EngSyntaxError, match="plot sweep list cannot be empty"):
        parse_cell("plot(M(x), x, 0, L, q=[])")
    with pytest.raises(EngSyntaxError, match="plot sweep values must be a list"):
        parse_cell("plot(M(x), x, 0, L, q=5*kN/m)")


def test_list_syntax_is_not_enabled_outside_plot_sweep():
    with pytest.raises(EngSyntaxError, match="unsupported syntax 'List'"):
        parse_cell("A = [1, 2]")


def test_plot_sweep_rejects_comprehensions_nested_lists_and_unpacking():
    invalid = [
        "plot(M(x), x, 0, L, q=[v for v in x])",
        "plot(M(x), x, 0, L, q=[[1], [2]])",
        "plot(M(x), x, 0, L, q=[*q_values])",
    ]
    for source in invalid:
        with pytest.raises(EngSyntaxError, match="unsupported"):
            parse_cell(source)


def test_plot_result_exposes_single_series_y_values_for_compatibility():
    statement = parse_cell("plot(M(x), x, 0, L)")[0]
    series = PlotSeries("M(x)", (1, 2), True)
    result = PlotResult(statement, "M(x)", "x", (0, 1), (series,))
    assert result.y_values == (1, 2)


def test_plot_result_does_not_fake_single_y_values_for_multi_series():
    statement = parse_cell("plot(A(x), B(x), x, 0, L)")[0]
    result = PlotResult(
        statement,
        "Comparison",
        "x",
        (0, 1),
        (
            PlotSeries("A(x)", (1, 2), False),
            PlotSeries("B(x)", (3, 4), False),
        ),
    )
    with pytest.raises(AttributeError, match="multi-series"):
        _ = result.y_values
