r"""A part of a matrix: `K[[1,3],[1,3]]`, `K[1:2, 1:2]`, `K[2, :]`.

The engineer's frame memoria condenses a 3x3 stiffness onto its one dynamic degree of
freedom, and to take the parts of `K` it needed it built selection matrices by hand:

    S_i = [1, 0, 0; 0, 0, 1]
    S_d = [0, 1, 0]
    K_ii = S_i*K*transpose(S_i)
    K_id = S_i*K*transpose(S_d)

That is correct and it is how the method is derived, but it is the long way to say "rows
1 and 3, columns 1 and 3", and on a frame of thirty degrees of freedom the selection
matrices are thirty columns wide. `K[1:2, 1:2]` was refused - `matrix slicing is
unsupported` - and `K[[1,3],[1,3]]` said `matrix indices must be positive integers`.

**Indices are counted from one, and a range includes both ends**, as the rest of the
language already counts (`K[1, 1]` is the upper-left entry) and as MATLAB and every
structural text write a partition: `K[1:2, 1:2]` is rows 1 and 2. A list of indices takes
those rows or columns in that order, and `:` alone takes all of them.
"""

import re

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngCalcError
from engcalc_colab.parser import parse_cell

from conftest import block_text


def run(source: str):
    engine = EngineeringEngine()
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return engine, result


FRAME = (
    "E := 210*GPa\nI_c := 227812.5*cm^4\nL_c := 370*cm\nA_d := 6.25*cm^2\nL_d := 622*cm\n"
    "K = [4*E*I_c/L_c, 6*E*I_c/L_c^2, 0; 6*E*I_c/L_c^2, 24*E*I_c/L_c^3 + A_d*E/L_d, "
    "6*E*I_c/L_c^2; 0, 6*E*I_c/L_c^2, 4*E*I_c/L_c]\n"
    "S_i = [1, 0, 0; 0, 0, 1]\nS_d = [0, 1, 0]\n"
)


def test_the_condensation_parts_are_the_selection_matrices_parts():
    """His own derivation is the reference: the part taken by index is the same matrix
    the selection matrices build."""
    engine, _ = run(
        FRAME
        + "K_ii = K[[1, 3], [1, 3]]\nK_id = K[[1, 3], 2]\nK_dd = K[2, 2]\n"
        + "P_ii = S_i*K*transpose(S_i)\nP_id = S_i*K*transpose(S_d)\nP_dd = S_d*K*transpose(S_d)\n"
    )
    namespace = engine.namespace

    assert namespace["K_ii"] == namespace["P_ii"]
    assert namespace["K_id"] == namespace["P_id"]
    assert namespace["K_dd"] == namespace["P_dd"][0, 0]


def test_a_range_includes_both_ends():
    engine, _ = run("A = [1, 2, 3; 4, 5, 6; 7, 8, 9]\nB = A[1:2, 2:3]\n")

    assert engine.namespace["B"].tolist() == [[2, 3], [5, 6]]


def test_a_colon_takes_a_whole_row_or_column():
    engine, _ = run("A = [1, 2, 3; 4, 5, 6; 7, 8, 9]\nr = A[2, :]\nc = A[:, 3]\n")

    assert engine.namespace["r"].tolist() == [[4, 5, 6]]
    assert engine.namespace["c"].tolist() == [[3], [6], [9]]


def test_an_open_range_runs_to_the_edge():
    engine, _ = run("A = [1, 2, 3; 4, 5, 6; 7, 8, 9]\nB = A[2:, :2]\n")

    assert engine.namespace["B"].tolist() == [[4, 5], [7, 8]]


def test_a_list_takes_rows_in_the_order_written():
    engine, _ = run("A = [1, 2, 3; 4, 5, 6; 7, 8, 9]\nB = A[[3, 1], [1, 3]]\n")

    assert engine.namespace["B"].tolist() == [[7, 9], [1, 3]]


def test_a_part_of_a_vector_keeps_its_orientation():
    engine, _ = run("u = [1; 2; 3; 4]\nv = u[2:3]\nr = [1, 2, 3, 4]\ns = r[[1, 4]]\n")

    assert engine.namespace["v"].tolist() == [[2], [3]]
    assert engine.namespace["s"].tolist() == [[1, 4]]


def test_a_part_evaluates_with_its_units(monkeypatch, capsys):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng(
        "", FRAME + "numeric(K[[1, 3], [1, 3]])\nnumeric(S_i*K*transpose(S_i))\n"
    )
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    page = block_text("".join(str(getattr(obj, "data", "")) for obj in captured))
    finals = re.findall(r"& = & \\displaystyle (10³ \[\\beginmatrix.*?\\endmatrix\] kN·m)", page)
    assert len(finals) == 2 and finals[0] == finals[1] and "517.20" in finals[0], page


# --- what must be refused -------------------------------------------------------------


@pytest.mark.parametrize(
    ("index", "message"),
    [
        ("A[0:2, 1]", "counted from 1"),
        ("A[2:1, 1]", "the range 2:1 runs backwards"),
        ("A[1:4, 1]", "the range 1:4 is out of range for 3"),
        ("A[[1, 4], 1]", "index 4 is out of range for 3"),
        ("A[4, :]", "index 4 is out of range for 3"),
        ("A[idx, 1]", "a list of indices is one row"),
        ("A[1:3:2, 1]", "step"),
    ],
)
def test_a_part_that_does_not_exist_is_refused_by_name(index, message):
    """Each by its own sentence. SymPy says `Index out of range` too, in words that name
    none of the rows, and a first version of these checks passed without them."""
    with pytest.raises(EngCalcError, match=message):
        run(f"A = [1, 2, 3; 4, 5, 6; 7, 8, 9]\nidx = [1, 2; 2, 3]\nB = {index}\n")


def test_a_list_kept_in_a_name_takes_the_same_part():
    """`dofs = [1, 3]` once, and `K[dofs, dofs]` wherever the partition is needed - the
    way a degree-of-freedom list is carried through a frame analysis."""
    engine, _ = run("A = [1, 2, 3; 4, 5, 6; 7, 8, 9]\ndofs = [1, 3]\nB = A[dofs, dofs]\n")

    assert engine.namespace["B"].tolist() == [[1, 3], [7, 9]]


# --- what must not move ---------------------------------------------------------------


def test_one_entry_is_still_a_scalar():
    engine, _ = run("A = [1, 2, 3; 4, 5, 6; 7, 8, 9]\na = A[2, 3]\nu = [5; 6]\nb = u[2]\n")

    assert engine.namespace["a"] == 6
    assert engine.namespace["b"] == 6
