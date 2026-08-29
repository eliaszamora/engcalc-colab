import pytest
import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("a = sqrt(x)", lambda x: sp.sqrt(x)),
        ("a = sin(x)", sp.sin),
        ("a = cos(x)", sp.cos),
        ("a = tan(x)", sp.tan),
        ("a = asin(x)", sp.asin),
        ("a = acos(x)", sp.acos),
        ("a = atan(x)", sp.atan),
        ("a = exp(x)", sp.exp),
        ("a = log(x)", sp.log),
    ],
)
def test_scalar_math_functions_map_to_fixed_sympy_operations(source, expected):
    engine = EngineeringEngine()
    result = run(engine, source)
    x = sp.Symbol("x")

    assert result.value == expected(x)


def test_pi_resolves_to_exact_sympy_constant():
    engine = EngineeringEngine()

    result = run(engine, "p = pi")

    assert result.value == sp.pi
    assert result.value.is_number is True


@pytest.mark.parametrize("name", ("sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "exp", "log"))
def test_scalar_math_functions_require_exactly_one_argument(name):
    engine = EngineeringEngine()

    with pytest.raises(EngEvaluationError, match=rf"{name} expects 1 argument"):
        run(engine, f"a = {name}(x, y)")


def test_scalar_math_composes_inside_user_function_symbolically():
    engine = EngineeringEngine()

    result = run(engine, "f(x) = sin(pi*x) + sqrt(x^2)")

    x = sp.Symbol("x")
    assert result.value == sp.sin(sp.pi * x) + sp.sqrt(x**2)
