r"""A matrix built from blocks: `[r, zeros(3, 3); zeros(3, 3), r]`.

The engineer's frame memoria writes the rotation of a frame element as six rows typed out
in full, although it is one 3x3 rotation twice down a diagonal:

    R_1 = [ c_c, s_c, 0,   0,   0, 0;
           -s_c, c_c, 0,   0,   0, 0;
              0,   0, 1,   0,   0, 0;
              0,   0, 0, c_c, s_c, 0;
              0,   0, 0,-s_c, c_c, 0;
              0,   0, 0,   0,   0, 1]

A literal with a matrix in it was refused - `matrix literal cells must be scalar` - so a
matrix could not be assembled from the parts the method is written in: a rotation from
its nodal block, an element stiffness from its four quadrants, a partitioned system from
`K_ff`, `K_fr`, `K_rf`, `K_rr`.

**Each cell may now be a matrix.** A row places its blocks side by side and must give them
one height; the rows are stacked and must give one width. A plain number or name in a row
of blocks is a 1x1 block. A literal of scalars reads exactly as before.
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


def test_a_rotation_is_its_nodal_block_twice():
    """His `R_1`, typed in full, against the same matrix built from `r`."""
    engine = run(
        "R_1 = [ c_c, s_c, 0, 0, 0, 0; -s_c, c_c, 0, 0, 0, 0; 0, 0, 1, 0, 0, 0; "
        "0, 0, 0, c_c, s_c, 0; 0, 0, 0, -s_c, c_c, 0; 0, 0, 0, 0, 0, 1]\n"
        "r = [c_c, s_c, 0; -s_c, c_c, 0; 0, 0, 1]\n"
        "R = [r, zeros(3, 3); zeros(3, 3), r]\n"
    )

    assert engine.namespace["R"] == engine.namespace["R_1"]


def test_blocks_of_different_shapes_meet_at_their_edges():
    engine = run("P = [1, 2; 3, 4]\nQ = [5; 6]\nS = [7, 8]\nZ = [P, Q; S, 9]\n")

    assert engine.namespace["Z"].tolist() == [[1, 2, 5], [3, 4, 6], [7, 8, 9]]


def test_a_row_of_blocks_and_a_column_of_blocks():
    engine = run("P = [1, 2; 3, 4]\nQ = [5; 6]\nS = [7, 8]\nH = [P, Q]\nV = [P; S]\n")

    assert engine.namespace["H"].tolist() == [[1, 2, 5], [3, 4, 6]]
    assert engine.namespace["V"].tolist() == [[1, 2], [3, 4], [7, 8]]


def test_a_partitioned_stiffness_evaluates_with_its_units(monkeypatch, capsys):
    """Four quadrants in kN/m, assembled and evaluated like any matrix."""
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng(
        "",
        "k := 2000*kN/m\n"
        "K_ff = [2*k, -k; -k, k]\nK_fr = [-k; 0*kN/m]\nK_rf = [-k, 0*kN/m]\nK_rr = [k]\n"
        "K = [K_ff, K_fr; K_rf, K_rr]\nnumeric(K)\n",
    )
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    page = block_text("".join(str(getattr(obj, "data", "")) for obj in captured))
    final = page.rsplit("& = & \\displaystyle", 1)[-1]
    assert "4.00" in final and "-2.00" in final and "kN/m" in final, final


# --- what must be refused -------------------------------------------------------------


@pytest.mark.parametrize(
    ("literal", "message"),
    [
        ("[P, S]", "row 1 of the matrix has blocks 2 and 1 rows tall"),
        ("[P; Q]", "the rows of the matrix are 2 and 1 columns wide"),
    ],
)
def test_blocks_that_do_not_meet_are_refused_by_shape(literal, message):
    with pytest.raises(EngCalcError, match=message):
        run(f"P = [1, 2; 3, 4]\nQ = [5; 6]\nS = [7, 8]\nZ = {literal}\n")


# --- what must not move ---------------------------------------------------------------


def test_a_literal_of_scalars_is_untouched():
    engine = run("k = [a, b; c, d]\nv = [1, 2, 3]\n")

    assert str(engine.namespace["k"]) == "Matrix([[a, b], [c, d]])"
    assert engine.namespace["v"].tolist() == [[1, 2, 3]]
