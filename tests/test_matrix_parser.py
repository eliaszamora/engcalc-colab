import ast

import pytest

from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell


def test_row_vector_literal_is_valid_normal_expression():
    stmt = parse_cell("r = [a, b, c]")[0]
    assert stmt.target == "r"
    assert isinstance(stmt.expression.body, ast.List)


def test_semicolon_matrix_literal_records_two_rectangular_rows():
    stmt = parse_cell("A = [a, b; c, d]")[0]
    assert stmt.target == "A"
    assert len(stmt.matrix_literals) == 1
    literal = stmt.matrix_literals[0].literal
    assert len(literal.rows) == 2
    assert [len(row) for row in literal.rows] == [2, 2]


def test_multiline_column_vector_is_one_statement_from_starting_line():
    stmt = parse_cell("v = [a;\n     b;\n     c]")[0]
    assert stmt.line_no == 1
    assert len(stmt.matrix_literals) == 1
    assert [len(row) for row in stmt.matrix_literals[0].literal.rows] == [1, 1, 1]


def test_matrix_cells_allow_nested_scalar_calls_with_commas():
    stmt = parse_cell("A = [f(a, b), g(c, d); h(x), 1]")[0]
    literal = stmt.matrix_literals[0].literal
    assert [len(row) for row in literal.rows] == [2, 2]


def test_matrix_cell_allows_piecewise_scalar_expression():
    stmt = parse_cell("K(x) = [piecewise(k1, x < L/2, k2), 0; 0, k3]")[0]
    assert len(stmt.matrix_literals) == 1
    assert len(stmt.matrix_literals[0].literal.rows) == 2


def test_table_point_list_remains_contextual_collection():
    stmt = parse_cell("table(M(x), x, [0*m, 1*m, 2*m])")[0]
    assert stmt.matrix_literals == ()
    assert isinstance(stmt.expression.body.args[-1], ast.List)


def test_plot_sweep_list_remains_contextual_collection():
    stmt = parse_cell("plot(M(x), x, 0*m, L, q=[5*kN/m, 10*kN/m])")[0]
    assert stmt.matrix_literals == ()
    assert isinstance(stmt.expression.body.keywords[0].value, ast.List)


def test_empty_normal_matrix_literal_is_rejected():
    with pytest.raises(EngSyntaxError, match="matrix literal cannot be empty"):
        parse_cell("A = []")


def test_semicolon_only_matrix_literal_is_rejected():
    with pytest.raises(EngSyntaxError, match="matrix literal row cannot be empty"):
        parse_cell("A = [;]")


def test_matrix_rows_must_have_equal_width():
    with pytest.raises(EngSyntaxError, match="matrix literal rows must have the same number of columns"):
        parse_cell("A = [a, b; c, d, e]")


def test_nested_matrix_literals_are_rejected():
    for source in ("A = [[a,b], [c,d]]", "A = [a, [b,c]; d, e]"):
        with pytest.raises(EngSyntaxError, match="nested matrix literals are unsupported"):
            parse_cell(source)


def test_unclosed_multiline_matrix_reports_starting_line():
    with pytest.raises(EngSyntaxError, match=r"line 1: unclosed matrix literal"):
        parse_cell("A = [a, b;\n     c, d")
