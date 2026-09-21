r"""A zero branch is shown in the unit its neighbours are shown in.

The substitution row of a partially evaluated piecewise read

    ⎧ (8.00 kN/m)   for x < (3.00 m)
    ⎨ (4.00 kN/m)   for x ≤ (6.00 m)
    ⎩ 0             otherwise

with two branches carrying a unit and the third a bare zero - and the row directly below
it, the one the engineer reads off, writes `0.00 kN/m` for that same branch.

`0*kN/m` folds to `Integer(0)` on the way into the symbolic layer, so by the time the
substitution row is printed there is no unit left on it and no name to replace. The
engine, though, has already decided what that branch is worth: `build_partial_piecewise_
evaluation` resolves it to a quantity in the branches' shared unit, and does so even when
the engineer writes a bare `0` with no unit at all.

This is `test_a_zero_reads_in_the_unit_beside_it` in the row it did not reach. That file's
rule: "in a block, a zero takes the unit its neighbours are shown in - the largest value
in the block, which is the one the reader is comparing the zero against."

**A zero only, at the time.** A literal branch kept the form the engineer typed it in,
because nothing was substituted into it, and a zero had no form left to keep. Seeing that
rendered showed the cost of the distinction - `(8.00 kN/m)` beside a bare `5 kN/m`, two
shapes in one column - and `test_a_literal_branch_is_written_as_a_value` settled it the
other way for every branch that holds a value. What is written here about the *zero* is
unchanged; it is now one case of a wider rule rather than an exception to a narrower one.

Older than 0.31.7; measured on 0.31.6 with the tree asserted.
"""

import re

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")


LOAD = """q1 := 8*kN/m
q2 := 4*kN/m
a_q := 3*m
L := 6*m
q_v(x) = piecewise(q1, x < a_q, q2, x <= L, {default})
numeric(q_v(x))
"""

RATIO = """k1 := 2
a_q := 3*m
f_v(x) = piecewise(k1, x < a_q, 3)
numeric(f_v(x))
"""


@pytest.fixture
def page(monkeypatch):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def bodies_of(written: str) -> list[list[str]]:
    r"""The separator carries a row space - `\\[4pt]`, from
    `test_a_cases_body_gives_its_branches_room` - so the split takes it with its optional
    argument, or every branch but the first arrives wearing a `[4pt]`."""
    bodies = []
    for after in written.split(r"\begin{cases}")[1:]:
        inner = after.split(r"\end{cases}")[0]
        bodies.append(
            [
                branch.strip().replace(r"\displaystyle ", "")
                for branch in re.split(r"\\\\(?:\[[^\]]*\])?", inner)
            ]
        )
    return bodies


def values_of(body: list[str]) -> list[str]:
    return [branch.split("&", 1)[0].strip() for branch in body]


def substitution_body(written: str) -> list[str]:
    """The middle row: the one with the brackets in it."""
    definition, substituted, answer = bodies_of(written)
    return substituted


@pytest.mark.parametrize("default", ["0*kN/m", "0"])
def test_a_zero_branch_is_shown_in_the_unit_beside_it(page, default):
    """Written with its unit or without it: the engine resolved the same branch."""
    written = page(LOAD.format(default=default)).replace(r"\dfrac", r"\frac")
    values = values_of(substitution_body(written))

    assert values[-1] == r"\left(0.00\,\frac{\mathrm{kN}}{\mathrm{m}}\right)", values


def test_the_zero_is_bracketed_like_its_neighbours(page):
    """One shape down the column, not two."""
    written = page(LOAD.format(default="0*kN/m"))

    for value in values_of(substitution_body(written)):
        assert value.startswith(r"\left("), value
        assert value.endswith(r"\right)"), value


def test_a_literal_branch_is_written_as_a_value_beside_it(page):
    """A branch that holds a value is written as one, whether or not it is a zero.

    This asserted `3` left as the engineer typed it, until the rendered page showed what
    that costs: two shapes in one column. `test_a_literal_branch_is_written_as_a_value`
    holds the wider rule; this keeps the dimensionless case honest beside it.
    """
    written = page(RATIO)
    values = values_of(substitution_body(written))

    assert values[0] == r"\left(2.00\right)", values
    assert values[-1] == r"\left(3.00\right)", values


# --- what must not move ---------------------------------------------------------------


def test_the_definition_row_still_says_zero(page):
    """The symbolic row names names; a zero there has no unit to be shown in."""
    written = page(LOAD.format(default="0*kN/m"))
    definition = bodies_of(written)[0]

    assert values_of(definition) == ["q_{1}", "q_{2}", "0"], definition


def test_the_answer_row_still_answers(page):
    """The row this rule was taken from."""
    written = page(LOAD.format(default="0*kN/m")).replace(r"\dfrac", r"\frac")
    answer = bodies_of(written)[-1]

    assert values_of(answer) == [
        r"8.00\,\frac{\mathrm{kN}}{\mathrm{m}}",
        r"4.00\,\frac{\mathrm{kN}}{\mathrm{m}}",
        r"0.00\,\frac{\mathrm{kN}}{\mathrm{m}}",
    ], answer


def test_the_conditions_are_untouched(page):
    """Only the value cell of a zero branch moves."""
    written = page(LOAD.format(default="0*kN/m")).replace(r"\dfrac", r"\frac")
    conditions = [
        branch.split("&", 1)[1].strip() for branch in substitution_body(written)
    ]

    assert conditions == [
        r"\text{for}\: x < \left(3.00\,\mathrm{m}\right)",
        r"\text{for}\: x \leq \left(6.00\,\mathrm{m}\right)",
        r"\text{otherwise}",
    ], conditions
