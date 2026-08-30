import pytest

from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell


@pytest.mark.parametrize(
    "source",
    [
        "q(x) = piecewise(q1, x < a, 0)",
        "q(x) = piecewise(q1, x <= a, q2, x <= L, 0)",
        "q(x) = piecewise(q1, a < x, q2, x <= L, 0)",
        "q(x) = piecewise(q1, x < L/2, 0)",
    ],
)
def test_piecewise_valid_forms_parse(source):
    parsed = parse_cell(source)

    assert len(parsed) == 1
    assert parsed[0].target == "q"
    assert parsed[0].parameters == ("x",)


@pytest.mark.parametrize(
    "source",
    [
        "q(x) = piecewise(q1, x < a)",
        "q(x) = piecewise(q1, x < a, q2, x < L)",
        "q(x) = piecewise(q1, 0 <= x < a, 0)",
        "q(x) = piecewise(q1, x < a and x > 0, 0)",
        "q(x) = piecewise(q1, M(x) > 0, 0)",
        "q(x) = piecewise(q1, 2*x < a, 0)",
        "q(x) = piecewise(q1, x == a, 0)",
        "A = x < a",
    ],
)
def test_piecewise_rejects_unsupported_condition_shapes(source):
    with pytest.raises(EngSyntaxError):
        parse_cell(source)


def test_piecewise_rejects_mixed_interval_variables():
    with pytest.raises(EngSyntaxError):
        parse_cell("q(x, y) = piecewise(q1, x < a, q2, y < b, 0)")


def test_piecewise_rejects_keywords():
    with pytest.raises(EngSyntaxError, match="keyword arguments are unsupported"):
        parse_cell("q(x) = piecewise(q1, x < a, default=0)")


@pytest.mark.parametrize(
    "source",
    [
        "piecewise = 3",
        "piecewise(x) = x",
        "f(piecewise) = piecewise + 1",
    ],
)
def test_piecewise_is_reserved_identifier(source):
    with pytest.raises(EngSyntaxError, match="reserved"):
        parse_cell(source)
