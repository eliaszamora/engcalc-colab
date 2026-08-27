import ast

import pytest

from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.models import ParsedNumericAssignment
from engcalc_colab.parser import parse_cell


def test_numeric_assignment_is_parsed_separately_from_symbolic_assignment():
    item = parse_cell("q := 2.8*tonf/m")[0]

    assert isinstance(item, ParsedNumericAssignment)
    assert item.target == "q"
    assert ast.unparse(item.expression) == "2.8 * tonf / m"


def test_numeric_assignment_preserves_blank_before():
    items = parse_cell("A = q*L\n\nq := 2.8*tonf/m")

    assert isinstance(items[1], ParsedNumericAssignment)
    assert items[1].blank_before is True


def test_numeric_function_target_is_rejected():
    with pytest.raises(EngSyntaxError, match="numeric assignment target"):
        parse_cell("M(x) := 2*kN*m")


def test_numeric_is_reserved_as_assignment_target():
    with pytest.raises(EngSyntaxError, match="reserved"):
        parse_cell("numeric = 3")


def test_numeric_assignment_normalizes_caret_power():
    item = parse_cell("I := 8.5e8*mm^4")[0]

    assert ast.unparse(item.expression) == "850000000.0 * mm ** 4"
