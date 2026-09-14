r"""Assigning into a part of a matrix: `K[[1,2],[1,2]] = K[[1,2],[1,2]] + k_1`.

The direct stiffness method assembles a structure by adding each element's stiffness into
the rows and columns of its degrees of freedom. The engineer's frame memoria cannot do
that, so it reaches the same matrix another way - a 12x6 localisation matrix per element,
typed in full, and `transpose(A_e)*k_e*A_e` - which is correct, and on a frame of thirty
degrees of freedom is thirty-column matrices by hand. `K[1, 1] = k` was refused:
`invalid assignment target 'K[1, 1]'`.

**A part of a matrix can now be assigned**, with the same indices that read one
(`test_a_part_of_a_matrix`): a single entry, a list of rows and columns, a range. The
right-hand side is worked out with the matrix as it stands, the part is replaced, and the
page shows the matrix after it. The part and the value must be the same shape.
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


ASSEMBLY = (
    "k_e = [1, -1; -1, 1]\n"
    "K = zeros(3, 3)\n"
    "K[[1, 2], [1, 2]] = K[[1, 2], [1, 2]] + k_1*k_e\n"
    "K[[2, 3], [2, 3]] = K[[2, 3], [2, 3]] + k_2*k_e\n"
)


def test_two_springs_assemble_by_their_degrees_of_freedom():
    engine = run(ASSEMBLY + "H = [k_1, -k_1, 0; -k_1, k_1 + k_2, -k_2; 0, -k_2, k_2]\n")

    assert engine.namespace["K"] == engine.namespace["H"]


def test_one_entry_and_one_range():
    engine = run("A = zeros(3, 3)\nA[2, 3] = 7\nA[1:2, 1] = [4; 5]\nu = zeros(3, 1)\nu[2] = 9\n")

    assert engine.namespace["A"].tolist() == [[4, 0, 0], [5, 0, 7], [0, 0, 0]]
    assert engine.namespace["u"].tolist() == [[0], [9], [0]]


def test_the_page_shows_the_matrix_after_the_assignment(monkeypatch, capsys):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", "k_1 := 2000*kN/m\nk_2 := 1500*kN/m\n" + ASSEMBLY + "numeric(K)\n")
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    page = block_text("".join(str(getattr(obj, "data", "")) for obj in captured))
    rows = page.split("\\\\[8pt]")
    assert any(
        row.strip().startswith("\\displaystyle K & = &") and "k_1 + k_2" in row for row in rows
    ), page
    assert "3.50" in page.rsplit("& = & \\displaystyle", 1)[-1], page


def test_the_matrix_before_is_what_the_right_hand_side_reads():
    """`K[1, 1] = K[1, 1] + 1` twice is 2, not 1: each line reads the matrix the line
    above left."""
    engine = run("K = zeros(2, 2)\nK[1, 1] = K[1, 1] + 1\nK[1, 1] = K[1, 1] + 1\n")

    assert engine.namespace["K"][0, 0] == 2


def test_a_matrix_written_with_kept_names_is_evaluated_as_it_is_now(monkeypatch, capsys):
    """A matrix whose definition kept a name - `EA/L` - carries that formula for the page.
    After `K[1, 1] = 0` the formula is no longer the matrix: kept, it made `numeric(K)`
    open with the old matrix and print `133.33` where the entry is zero. Measured with the
    line that drops it taken out."""
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng(
        "",
        "E := 200*GPa\nA := 20*cm^2\nL := 3*m\nkeep EA = E*A\n"
        "K = EA/L*[1, -1; -1, 1]\nK[1, 1] = 0\nnumeric(K)\n",
    )
    capsys.readouterr()

    page = block_text("".join(str(getattr(obj, "data", "")) for obj in captured))
    final = page.rsplit("& = & \\displaystyle", 1)[-1]
    assert "\\displaystyle 0.00 & \\displaystyle -133.33" in final, final


# --- what must be refused -------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("K[1, 1] = 5\n", "K has no matrix to assign into"),
        ("x = 3\nx[1] = 5\n", "x has no matrix to assign into"),
        ("K = zeros(3, 3)\nK[[1, 2], [1, 2]] = 5\n", "K\\[\\.\\.\\.\\] is 2x2 and the value is a scalar"),
        ("K = zeros(3, 3)\nK[1, 1] = [1, 2]\n", "K\\[\\.\\.\\.\\] is 1x1 and the value is 1x2"),
        ("K = zeros(3, 3)\nK[[1, 2], 1] = [1, 2, 3]\n", "K\\[\\.\\.\\.\\] is 2x1 and the value is 1x3"),
        ("K = zeros(3, 3)\nK[4, 1] = 5\n", "out of range"),
        ("K = zeros(3, 3)\nK[4, [1, 2]] = [1, 2]\n", "index 4 is out of range for 3"),
    ],
)
def test_an_assignment_that_does_not_fit_is_refused_by_name(source, message):
    with pytest.raises(EngCalcError, match=message):
        run(source)


# --- what must not move ---------------------------------------------------------------


def test_a_plain_assignment_is_untouched():
    engine = run("K = [1, 2; 3, 4]\nK = K + K\n")

    assert engine.namespace["K"].tolist() == [[2, 4], [6, 8]]
