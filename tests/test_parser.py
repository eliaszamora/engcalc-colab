import ast
import pytest

from engcalc_colab import __version__
from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.models import ParsedStatement
from engcalc_colab.parser import parse_cell


def test_package_version_and_statement_model():
    stmt = ParsedStatement(3, "A = q*L", "A", None, ast.parse("q*L", mode="eval"))
    assert __version__ == "0.9.1"
    assert stmt.line_no == 3
    assert stmt.target == "A"
    assert stmt.blank_before is False


def test_parser_ignores_comments_and_converts_power():
    stmts = parse_cell("# comment\n\nM_0 = -q/2*(L-x)^2")
    assert len(stmts) == 1
    assert stmts[0].target == "M_0"
    assert "**" in ast.unparse(stmts[0].expression)


def test_parser_recognizes_function_assignment():
    stmt = parse_cell("V(x) = R_A - q*x")[0]
    assert stmt.target == "V"
    assert stmt.parameter == "x"


def test_parser_rewrites_equality_only_inside_solve():
    stmt = parse_cell("R_B = solve(Delta_B + R_B*f_BB = 0, R_B)")[0]
    assert ast.unparse(stmt.expression) == "solve(eq(Delta_B + R_B * f_BB, 0), R_B)"


def test_parser_rejects_attribute_access():
    with pytest.raises(EngSyntaxError, match="unsupported syntax"):
        parse_cell("A = obj.attr")


def test_parser_rejects_subscript_access():
    with pytest.raises(EngSyntaxError, match="unsupported syntax"):
        parse_cell("A = values[0]")


def test_parser_rejects_unapproved_function_calls():
    with pytest.raises(EngSyntaxError, match="function 'open' is not allowed"):
        parse_cell("A = open(x)")


def test_parser_allows_sum_notation():
    stmt = parse_cell("R = sum(F_i*i, i, 1, n)")[0]
    assert ast.unparse(stmt.expression) == "sum(F_i * i, i, 1, n)"


def test_parser_allows_numeric_call():
    stmt = parse_cell("numeric(M_0)")[0]
    assert ast.unparse(stmt.expression) == "numeric(M_0)"


def test_parser_rewrites_result_call_to_numeric():
    stmt = parse_cell("result(M_0)")[0]
    assert ast.unparse(stmt.expression) == "numeric(M_0)"


def test_parser_preserves_function_assignment_parameter_tuple():
    stmt = parse_cell("M(x) = q*x*(L-x)/2")[0]
    assert stmt.parameters == ("x",)


def test_parser_rejects_zero_argument_function_assignment():
    with pytest.raises(EngSyntaxError, match="at least one parameter"):
        parse_cell("f() = x + 1")


def test_parser_rejects_duplicate_function_parameters():
    with pytest.raises(EngSyntaxError, match="duplicate function parameter"):
        parse_cell("f(x, x) = x")


def test_parser_rejects_keyword_function_arguments():
    with pytest.raises(EngSyntaxError, match="keyword arguments are not supported"):
        parse_cell("f(x=1)")
