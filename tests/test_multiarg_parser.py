import pytest

from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell


def test_parser_records_ordered_multi_argument_signature():
    stmt = parse_cell("M(x, q, L) = q*x*(L-x)/2")[0]

    assert stmt.target == "M"
    assert stmt.parameters == ("x", "q", "L")
    assert stmt.parameter is None


def test_one_argument_definition_keeps_compatibility_property():
    stmt = parse_cell("V(x) = q*(L-x)")[0]

    assert stmt.parameters == ("x",)
    assert stmt.parameter == "x"


def test_unused_parameter_is_legal():
    stmt = parse_cell("f(x, y) = 5")[0]

    assert stmt.parameters == ("x", "y")


@pytest.mark.parametrize(
    "source, message",
    [
        ("f() = 1", "user functions require at least one parameter"),
        ("f(x, x) = x", "duplicate function parameter 'x'"),
        ("f(x, sin) = x", "reserved function parameter 'sin'"),
        ("f(pi, x) = x", "reserved function parameter 'pi'"),
        ("f(x=1, y) = y", "invalid function parameter 'x=1'"),
    ],
)
def test_invalid_function_signatures_are_rejected(source, message):
    with pytest.raises(EngSyntaxError, match=message):
        parse_cell(source)
