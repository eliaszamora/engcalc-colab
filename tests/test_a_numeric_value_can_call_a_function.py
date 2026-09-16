r"""`M_max := M(L/2)` stores the moment at midspan, as `numeric(M(L/2))` already computes it.

A beam, and its design moment taken as a value:

    M(x) = q x (L - x)/2
    M_max := M(L/2)        engcalc: line 4: unsupported numeric function

The cell stopped there, and the message did not name a function. `M_max = M(L/2)` and
`numeric(M(L/2))` both worked; only the form that says "this is a number" did not.

**Why.** `:=` is evaluated by `NumericContext`, which walks the expression over Pint
quantities and knows the mathematical functions - `sqrt`, `sin`, `log` - and nothing the
sheet defined. The functions live in the engine, and so does the evaluation that
substitutes quantities into one: guards, piecewise branches and all.

**So a `:=` whose right side calls a function the sheet defined is evaluated by that same
engine path**, and the value is stored and shown as any `:=` value is. A name that is
neither a function of the sheet nor one EngCalc knows is still refused, and the refusal now
says which name it was.
"""

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell

from conftest import block_text


def page(monkeypatch, source: str) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", source)
    return block_text("".join(str(getattr(obj, "data", "")) for obj in captured))


BEAM = "L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L - x)/2\n"


def run(source: str) -> EngineeringEngine:
    engine = EngineeringEngine()
    for statement in parse_cell(source):
        engine.evaluate(statement)
    return engine


def test_the_design_moment_as_a_value(monkeypatch, capsys):
    text = page(monkeypatch, BEAM + "M_max := M(L/2)\n")
    capsys.readouterr()

    assert r"M_max & = & \displaystyle 45.00 kN·m \endarray" in text, text


def test_the_value_is_used_like_any_other(monkeypatch, capsys):
    text = page(monkeypatch, BEAM + "M_max := M(L/2)\nM_d = 1.5*M_max\nnumeric(M_d)\n")
    capsys.readouterr()

    assert "(45.00 kN·m)" in text, text
    assert text.rstrip().endswith("67.50 kN·m \\endarray"), text


def test_a_function_inside_an_expression(monkeypatch, capsys):
    text = page(monkeypatch, BEAM + "M_2 := 2*M(L/2)\n")
    capsys.readouterr()

    assert r"M_2 & = & \displaystyle 90.00 kN·m \endarray" in text, text


def test_a_function_left_waiting_for_a_value_is_refused():
    with pytest.raises(EngEvaluationError, match="values for: x"):
        run(BEAM + "M_x := M(x)\n")


def test_a_function_that_answers_a_matrix_is_refused_by_name():
    """`:=` holds one quantity; a matrix was refused before and still is, now saying so."""
    with pytest.raises(EngEvaluationError, match=r"'K_1 := \.\.\.' needs a single numeric value"):
        run("K_e(k) = [k, -k; -k, k]\nK_1 := K_e(3*kN/m)\n")


def test_an_unknown_function_is_named():
    with pytest.raises(EngEvaluationError, match="'foo'"):
        run(BEAM + "a := foo(3)\n")


# --- what must not move ---------------------------------------------------------------


def test_a_value_from_names_and_units(monkeypatch, capsys):
    text = page(monkeypatch, "L := 6*m\nq := 10*kN/m\na := q*L^2/8\n")
    capsys.readouterr()

    assert r"a & = & \displaystyle 45.00 kN·m \endarray" in text, text


def test_a_mathematical_function(monkeypatch, capsys):
    text = page(monkeypatch, "A := 9*m^2\nb := sqrt(A)\n")
    capsys.readouterr()

    assert r"b & = & \displaystyle 3.00 m \endarray" in text, text
