r"""`dot(u, v)` and `cross(u, v)`.

A dot product was written `transpose(u)*v`, which is right and reads as matrix algebra
rather than as the scalar it is, and a cross product - the moment of a force about a
point, `r × F` - could not be written at all: `unsupported function 'cross'`. Both are
lines of any three-dimensional statics or frame geometry.

**`dot` takes two vectors of one length, in either orientation, and gives a scalar;
`cross` takes two of length three and gives a vector in the first one's orientation.**
Units carry through as they do for any product.
"""

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngCalcError
from engcalc_colab.parser import parse_cell

from conftest import block_text


def run(source: str):
    engine = EngineeringEngine()
    for statement in parse_cell(source):
        engine.evaluate(statement)
    return engine


def test_a_dot_product_is_the_scalar_transpose_gives():
    engine = run("u = [1; 2; 3]\nv = [4; 5; 6]\nd = dot(u, v)\nt = transpose(u)*v\n")

    assert engine.namespace["d"] == 32
    assert engine.namespace["d"] == engine.namespace["t"][0, 0]


def test_a_dot_product_does_not_mind_orientation():
    engine = run("u = [1, 2, 3]\nv = [4; 5; 6]\nd = dot(u, v)\n")

    assert engine.namespace["d"] == 32


def test_a_cross_product_follows_the_right_hand():
    engine = run("i = [1; 0; 0]\nj = [0; 1; 0]\nk = cross(i, j)\nm = cross(j, i)\n")

    assert engine.namespace["k"].tolist() == [[0], [0], [1]]
    assert engine.namespace["m"].tolist() == [[0], [0], [-1]]


def test_a_cross_product_keeps_the_first_vector_s_orientation():
    engine = run("a = [1, 2, 3]\nb = [4; 5; 6]\nc = cross(a, b)\n")

    assert engine.namespace["c"].tolist() == [[-3, 6, -3]]


def test_the_moment_of_a_force_carries_its_units(monkeypatch, capsys):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng(
        "", "r = [2*m; 0*m; 1*m]\nF = [0*kN; 5*kN; 0*kN]\nM_O = cross(r, F)\nnumeric(M_O)\n"
    )
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    page = block_text("".join(str(getattr(obj, "data", "")) for obj in captured))
    final = page.rsplit("& = & \\displaystyle", 1)[-1]
    assert "-5.00" in final and "10.00" in final and "kN·m" in final, final


# --- what must be refused -------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("d = dot([1; 2], [1; 2; 3])", "dot takes two vectors of one length; they are 2 and 3 long"),
        ("d = dot([1, 2; 3, 4], [1; 2])", "dot takes two vectors; the first is 2x2"),
        ("d = dot(x, [1; 2])", "dot takes two vectors; the first is not a matrix"),
        ("c = cross([1; 2], [3; 4])", "cross takes two vectors of length 3; they are 2 and 2 long"),
    ],
)
def test_vectors_that_do_not_fit_are_refused_by_shape(source, message):
    with pytest.raises(EngCalcError, match=message):
        run(source + "\n")
