r"""What `solve` answers is written as `w = ...`, however many answers it found.

Found by a visual pass over 0.31.5. The same call, twice, on one page:

    solve(eq(w^2, 25/s^2), w)             w = −5/s  (−5.00 1/s)
                                          w =  5/s  ( 5.00 1/s)

    assume(v > 0)
    solve(eq(v^2, 25/s^2), v)             v² = 25/s²
                                          5/s                     <- answer of what?

Two answers are written with their unknown and a number beside each; one answer is
written as a bare value in the column where an unnamed thing goes. Nothing on the page
says the `5/s` is `v`. A memoria's reader is handed a number with no subject, and the
product already knows the right shape - it uses it one block above.

The unknown is never in doubt: `solve(equation, v)` names it, and the engine resolves it
to a symbol before it solves anything. It just was not carried to the page.

`z = solve(...)` is unaffected: the sheet named the row, and that name wins.

The examples here are in metres or in nothing at all, deliberately. A `solve` with two
answers writes its units in italic until `test_a_solved_answer_wears_its_units` corrects
it, and this file is about which rows have a subject, not about how they spell a second.
"""

import re

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")

_ROW = re.compile(r"\\\\\[-?\d+pt\]")


@pytest.fixture
def rows(monkeypatch):
    def read(source: str) -> list[str]:
        """Every row of the cell's equation group, however far apart they are set."""
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        maths = [item.data for item in captured if isinstance(item, Math)]
        assert maths, "the cell displayed no mathematics"
        body = maths[-1]
        body = body[body.index(r"{lcl}") + len(r"{lcl}") :].replace(r"\end{array}", "")
        return [row.strip() for row in _ROW.split(body)]

    return read


def test_one_answer_after_an_assumption_says_what_it_answers(rows):
    """The row the reader met as a bare number."""
    written = rows("assume(v > 0)\nsolve(eq(v^2, 25), v)\n")
    assert written[-1] == r"\displaystyle v & = & \displaystyle 5", written


def test_one_answer_after_a_discard_says_what_it_answers(rows):
    """With units the second root is found and then ruled out, so a discard row follows
    the answer; the answer is the row above it and still has its unknown."""
    written = rows("assume(v > 0)\nsolve(eq(v^2, 25/s^2), v)\n")
    assert written[-2].startswith(r"\displaystyle v & = & \displaystyle \frac{5}"), written
    assert written[-1].startswith(r"& & \displaystyle \text{discarded by }"), written


def test_one_answer_with_nothing_discarded_says_what_it_answers(rows):
    """No assumption in sight: one root, and it still has an unknown."""
    written = rows("solve(eq(2*y, 10*m), y)\n")
    assert written[-1] == r"\displaystyle y & = & \displaystyle 5\,\mathrm{m}", written


def test_the_equation_is_still_written_above_it(rows):
    """The answer gains a name; the equation it came from does not move."""
    written = rows("solve(eq(2*y, 10*m), y)\n")
    assert written[0] == r"& & \displaystyle 2 y = 10\,\mathrm{m}", written


def test_a_solve_with_two_answers_is_unchanged(rows):
    """The shape this copies. It must read exactly as it did."""
    written = rows("solve(eq(y^2, 25), y)\n")
    expected = r"\displaystyle y & = & \displaystyle {0}\;\;\left({1}\right)"
    assert written[1] == expected.format("-5", "-5.00"), written
    assert written[2] == expected.format("5", "5.00"), written


# --- what must not move ---------------------------------------------------------------


def test_a_named_row_keeps_the_name_the_sheet_gave_it(rows):
    written = rows("z = solve(eq(2*z, 10*m), z)\n")
    assert written[-1] == r"\displaystyle z & = & \displaystyle 5\,\mathrm{m}", written


def test_a_row_that_is_only_an_expression_keeps_no_name(rows):
    """`2*b` on a line of its own is not an answer to anything, and gets no unknown.

    Found by mutation: an unknown left over from a previous statement would be written
    on this row, a name the sheet never typed. It is why the unknown is cleared with the
    rest of the evaluator's state rather than left to be overwritten.
    """
    written = rows("b := 30*cm\n2*b\n")
    assert written[-1] == r"& & \displaystyle 2 b", written


def test_an_ordinary_definition_is_untouched(rows):
    written = rows("b := 30*cm\nh := 60*cm\nA = b*h\n")
    assert written[-1] == r"\displaystyle A & = & \displaystyle b h", written


def test_a_system_still_names_each_unknown(rows):
    written = rows(
        "L := 6*m\nq := 10*kN/m\n"
        "eqFy = eq(R_A + R_B, q*L)\neqMA = eq(R_B*L, q*L*L/2)\n"
        "solve(eqFy, eqMA, R_A, R_B)\n"
    )
    assert any(row.startswith(r"\displaystyle R_{A} & = &") for row in written), written
    assert any(row.startswith(r"\displaystyle R_{B} & = &") for row in written), written
