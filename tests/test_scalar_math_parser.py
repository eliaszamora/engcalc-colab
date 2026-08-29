import pytest

from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell


_SCALAR_FUNCTIONS = (
    "sqrt",
    "sin",
    "cos",
    "tan",
    "asin",
    "acos",
    "atan",
    "exp",
    "log",
)


@pytest.mark.parametrize(
    "source",
    [
        "a = sqrt(x)",
        "b = sin(theta)",
        "c = cos(theta)",
        "d = tan(theta)",
        "e = asin(r)",
        "f = acos(r)",
        "g = atan(r)",
        "h = exp(z)",
        "i = log(z)",
        "p = pi",
    ],
)
def test_scalar_math_syntax_is_accepted(source):
    assert parse_cell(source)


@pytest.mark.parametrize("name", _SCALAR_FUNCTIONS + ("pi",))
def test_scalar_math_public_names_are_reserved_assignment_targets(name):
    with pytest.raises(EngSyntaxError, match=rf"reserved identifier '{name}'"):
        parse_cell(f"{name} = 1")


@pytest.mark.parametrize("name", _SCALAR_FUNCTIONS + ("pi",))
def test_scalar_math_public_names_are_reserved_numeric_assignment_targets(name):
    with pytest.raises(EngSyntaxError, match=rf"reserved identifier '{name}'"):
        parse_cell(f"{name} := 1")


@pytest.mark.parametrize("name", _SCALAR_FUNCTIONS + ("pi",))
def test_scalar_math_public_names_are_reserved_function_parameters(name):
    with pytest.raises(EngSyntaxError, match=rf"reserved function parameter '{name}'"):
        parse_cell(f"f({name}) = {name}")
