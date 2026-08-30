import ast

import pytest

from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell


@pytest.mark.parametrize(
    ("source", "call_name", "variable_index"),
    [
        ("roots(V(x), x, 0, L)", "roots", 1),
        ("extrema(M(x), x, 0, L)", "extrema", 1),
        ("intersections(M1(x), M2(x), x, 0, L)", "intersections", 2),
    ],
)
def test_characteristic_calls_parse_as_standalone_statements(
    source,
    call_name,
    variable_index,
):
    statement = parse_cell(source)[0]

    assert statement.target is None
    assert isinstance(statement.expression.body, ast.Call)
    assert statement.expression.body.func.id == call_name
    assert isinstance(statement.expression.body.args[variable_index], ast.Name)
    assert statement.expression.body.args[variable_index].id == "x"


@pytest.mark.parametrize(
    "source",
    [
        "roots(V(x), x, 0)",
        "roots(V(x), x, 0, L, 2)",
        "extrema(M(x), x, 0)",
        "extrema(M(x), x, 0, L, 2)",
        "intersections(M1(x), M2(x), x, 0)",
        "intersections(M1(x), M2(x), x, 0, L, 2)",
    ],
)
def test_characteristic_calls_reject_wrong_arity(source):
    with pytest.raises(EngSyntaxError, match="expects"):
        parse_cell(source)


@pytest.mark.parametrize(
    "source",
    [
        "roots(V(x), x + 1, 0, L)",
        "extrema(M(x), x + 1, 0, L)",
        "intersections(M1(x), M2(x), x + 1, 0, L)",
        "roots(V(x), pi, 0, L)",
    ],
)
def test_characteristic_calls_require_direct_symbolic_variable(source):
    with pytest.raises(EngSyntaxError, match="variable must be a symbolic identifier"):
        parse_cell(source)


@pytest.mark.parametrize(
    "source",
    [
        "R = roots(V(x), x, 0, L)",
        "R(x) = extrema(M(x), x, 0, L)",
        "numeric(roots(V(x), x, 0, L))",
        "abs(extrema(M(x), x, 0, L))",
        "table(roots(V(x), x, 0, L), x, 0, L, 5)",
    ],
)
def test_characteristic_calls_reject_assignment_and_nesting(source):
    with pytest.raises(EngSyntaxError, match="must be a standalone statement"):
        parse_cell(source)


@pytest.mark.parametrize("name", ["roots", "extrema", "intersections"])
def test_characteristic_call_names_are_reserved(name):
    with pytest.raises(EngSyntaxError, match="reserved identifier"):
        parse_cell(f"{name} = 3")


def test_characteristic_calls_reject_keywords():
    with pytest.raises(EngSyntaxError, match="keyword arguments are unsupported"):
        parse_cell("roots(V(x), x, 0, L, tol=1e-6)")
