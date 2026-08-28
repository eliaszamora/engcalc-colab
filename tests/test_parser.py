import ast
import pytest

from engcalc_colab import __version__
from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.models import ParsedStatement
from engcalc_colab.parser import parse_cell


def test_package_version_and_statement_model():
    stmt = ParsedStatement(3, "A = q*L", "A", None, ast.parse("q*L", mode="eval"))
    assert __version__ == "0.2.0"
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


def test_parser_rejects_reserved_target():
    with pytest.raises(EngSyntaxError, match="reserved"):
        parse_cell("solve = 3")


def test_parser_rejects_dunder_call_with_concise_line_error():
    with pytest.raises(EngSyntaxError, match=r"line 1: unsupported function '__import__'"):
        parse_cell('A = __import__("os")')


def test_parser_reports_line_for_unbalanced_parentheses():
    with pytest.raises(EngSyntaxError, match=r"line 2: unbalanced parentheses"):
        parse_cell("# heading\nA = (q*L")


def test_parser_reserves_sum_as_builtin_operation():
    with pytest.raises(EngSyntaxError, match="reserved"):
        parse_cell("sum = 3")


def test_parser_marks_blank_line_as_output_group_separator():
    stmts = parse_cell("A = 1\n\n\n# next group\nB = 2\n# same group\nC = 3")
    assert [stmt.blank_before for stmt in stmts] == [False, True, False]
