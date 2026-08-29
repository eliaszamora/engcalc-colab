import ast

import pytest

from engcalc_colab import models
from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell


def _table_call(source: str) -> ast.Call:
    statement = parse_cell(source)[0]
    call = statement.expression.body
    assert isinstance(call, ast.Call)
    assert isinstance(call.func, ast.Name)
    assert call.func.id == "table"
    return call


def test_table_uniform_form_is_accepted():
    call = _table_call("table(M(x), x, 0, L, 21)")
    assert len(call.args) == 5
    assert call.keywords == []


def test_table_uniform_form_accepts_multiple_responses():
    call = _table_call("table(M_D(x), M_U(x), x, 0, L, 21)")
    assert len(call.args) == 6


def test_table_explicit_points_with_declared_unit_are_accepted():
    call = _table_call("table(M(x), x, [0, 1, 1.5, 2], m)")
    assert isinstance(call.args[-2], ast.List)
    assert len(call.args[-2].elts) == 4


def test_table_fully_explicit_compatible_quantities_are_accepted():
    call = _table_call("table(M(x), x, [0*m, 50*cm, 1*m])")
    assert isinstance(call.args[-1], ast.List)
    assert len(call.args[-1].elts) == 3


def test_arbitrary_list_literal_remains_rejected_outside_table():
    with pytest.raises(EngSyntaxError, match="unsupported syntax 'List'"):
        parse_cell("A = [0, 1, 2]")


def test_table_is_reserved_as_scalar_assignment_target():
    with pytest.raises(EngSyntaxError, match="reserved identifier 'table'"):
        parse_cell("table = 3")


def test_table_is_reserved_as_user_function_name():
    with pytest.raises(EngSyntaxError, match="reserved identifier 'table'"):
        parse_cell("table(x) = x")


def test_table_requires_at_least_one_response_expression():
    with pytest.raises(EngSyntaxError, match="table requires at least one response expression"):
        parse_cell("table(x, 0, L, 21)")


def test_table_variable_must_be_symbolic_identifier_uniform_form():
    with pytest.raises(EngSyntaxError, match="table variable must be a symbolic identifier"):
        parse_cell("table(M(x), x + 1, 0, L, 21)")


def test_table_variable_must_be_symbolic_identifier_explicit_form():
    with pytest.raises(EngSyntaxError, match="table variable must be a symbolic identifier"):
        parse_cell("table(M(x), x + 1, [0, 1, 2], m)")


def test_table_rejects_empty_explicit_point_list():
    with pytest.raises(EngSyntaxError, match="table point list cannot be empty"):
        parse_cell("table(M(x), x, [])")


def test_table_rejects_nested_point_lists():
    with pytest.raises(EngSyntaxError, match="unsupported table point syntax 'List'"):
        parse_cell("table(M(x), x, [[0], [1]])")


def test_table_rejects_point_list_comprehensions():
    with pytest.raises(EngSyntaxError, match="unsupported table point syntax 'ListComp'"):
        parse_cell("table(M(x), x, [v for v in x])")


def test_table_rejects_keyword_arguments():
    with pytest.raises(EngSyntaxError, match="keyword arguments are unsupported"):
        parse_cell("table(M(x), x, 0, L, count=21)")


def test_table_rejects_unsupported_call_shape():
    with pytest.raises(EngSyntaxError, match="unsupported table call shape"):
        parse_cell("table(M(x), x, 0)")


def test_table_result_models_are_defined_and_frozen():
    assert hasattr(models, "TableColumn")
    assert hasattr(models, "TableResult")

    column = models.TableColumn(
        display_label="M(x)",
        unit="kN*m",
        values=(1, 2),
    )
    result = models.TableResult(
        statement=parse_cell("table(M(x), x, 0, L, 2)")[0],
        variable="x",
        point_unit="m",
        point_values=(0, 1),
        columns=(column,),
        mode="uniform",
    )

    assert result.columns == (column,)
    assert result.mode == "uniform"
    with pytest.raises(Exception):
        result.mode = "explicit"
