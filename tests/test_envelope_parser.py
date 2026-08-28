import ast

import pytest

from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell


def test_envelope_accepts_multiple_positional_response_expressions():
    statement = parse_cell("envelope(M_D(x), M_L(x), x, 0, L)")[0]
    call = statement.expression.body
    assert call.func.id == "envelope"
    assert len(call.args) == 5
    assert call.keywords == []


def test_envelope_name_is_reserved_as_assignment_target():
    with pytest.raises(EngSyntaxError, match="reserved identifier 'envelope'"):
        parse_cell("envelope = 3")


def test_envelope_accepts_one_restricted_parameter_sweep_keyword():
    statement = parse_cell(
        "envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])"
    )[0]
    call = statement.expression.body
    assert len(call.args) == 4
    assert len(call.keywords) == 1
    assert call.keywords[0].arg == "q"
    assert isinstance(call.keywords[0].value, ast.List)
    assert len(call.keywords[0].value.elts) == 2


def test_envelope_rejects_more_than_one_sweep_keyword():
    with pytest.raises(
        EngSyntaxError,
        match="envelope accepts at most one sweep parameter",
    ):
        parse_cell("envelope(M(x), x, 0, L, q=[1], P=[2])")


def test_envelope_rejects_empty_or_non_list_sweep_values():
    with pytest.raises(EngSyntaxError, match="envelope sweep list cannot be empty"):
        parse_cell("envelope(M(x), x, 0, L, q=[])")
    with pytest.raises(EngSyntaxError, match="envelope sweep values must be a list"):
        parse_cell("envelope(M(x), x, 0, L, q=5*kN/m)")


def test_envelope_sweep_rejects_comprehensions_nested_lists_and_unpacking():
    invalid = [
        "envelope(M(x), x, 0, L, q=[v for v in x])",
        "envelope(M(x), x, 0, L, q=[[1], [2]])",
        "envelope(M(x), x, 0, L, q=[*q_values])",
    ]
    for source in invalid:
        with pytest.raises(EngSyntaxError, match="unsupported"):
            parse_cell(source)


def test_keyword_arguments_remain_rejected_for_non_display_calls():
    with pytest.raises(EngSyntaxError, match="keyword arguments are unsupported"):
        parse_cell("simplify(x, q=[1, 2])")


def test_general_list_and_dictionary_syntax_remains_disabled():
    with pytest.raises(EngSyntaxError, match="unsupported syntax 'List'"):
        parse_cell("A = [1, 2]")
    with pytest.raises(EngSyntaxError, match="unsupported syntax 'Dict'"):
        parse_cell("A = {1: 2}")
