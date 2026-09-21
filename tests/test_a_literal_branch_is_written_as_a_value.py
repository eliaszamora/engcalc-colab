r"""In a substitution row, a branch that holds a value is written as a value.

Seen in Colab on the engineer's own run of 0.31.8, and left open deliberately until now.
The substitution row of

    w(x) = piecewise(q1, x < a, 5*kN/m)

reads

    ⎧ (8.00 kN/m)   for x < (3.00 m)
    ⎩ 5 kN/m        otherwise

two shapes in one column: the branch that was a name wears the brackets every substituted
value on the page wears, and the branch that was already a number does not. The reader has
to work out that the brackets mean nothing about the arithmetic.

**One shape is not available everywhere, and that is not what this asks for.** A branch
that is a *formula* is not a single value and never becomes a bracketed whole: on the
engineer's beam the substitution row holds `(100.00 cm)(4000.00 kgf)/2`, with the brackets
around the values inside it. What this asks is narrower and is the rule the row already
follows for every other cell: **a branch that holds a value is written as a value**, in the
row's own form - two decimals, bracketed - rather than as the engineer happened to type it.

That is what `0*kN/m` was given when it became `(0.00 kN/m)`; a literal is the same case
with a number in it. The value is not invented here either: the engine resolved the branch,
exactly as it resolved the zero.

**The definition row is untouched.** `5 kN/m` is what the engineer wrote and the definition
is where what he wrote belongs. A substitution row is where the values go.
"""

import re

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")


LOAD = """q1 := 8*kN/m
a_q := 3*m
w_v(x) = piecewise(q1, x < a_q, 5*kN/m)
"""

ZERO = """q1 := 8*kN/m
q2 := 4*kN/m
a_q := 3*m
L := 6*m
q_v(x) = piecewise(q1, x < a_q, q2, x <= L, 0*kN/m)
"""

BEAM = """L := 6*m
P := 40*kN
M_W(x) = piecewise(P*x/2, x <= L/2, 7*kN*m)
"""

# A zero, a formula and a literal in one piecewise: two branches that hold a value, with a
# formula between them. Found by mutation - paying only the first left the `7` bare, and
# every other sheet here has exactly one value branch to write.
TWO_VALUES = """L := 6*m
a_t := 2*m
P := 40*kN
M_T(x) = piecewise(0*kN*m, x <= a_t, P*x/2, x <= L, 7*kN*m)
"""

# The same load written in two units. The substitution row must show what was substituted -
# `400.00 kgf/m`, as the sheet stores it - while the answer row is free to bring the
# branches to the one unit they share. Found by mutation: reading the engine's value
# instead of the row's own substitution swaps one for the other.
MIXED = """q1 := 8*kN/m
q2 := 400*kgf/m
a_q := 3*m
L := 6*m
q_m(x) = piecewise(q1, x < a_q, q2, x <= L, 0*kN/m)
"""

# A formula branch on the path that binds the variable, where every branch resolves to a
# quantity. Naming it would collapse `(1.00 m)(40.00 kN)/2` to `(20.00 kN·m)` and throw
# away the working the row exists to show.
POINT = """L := 6*m
P := 40*kN
M_P(x) = piecewise(P*x/2, x <= L/2, P*(L - x)/2, x <= L, 0*kN*m)
"""


@pytest.fixture
def page(monkeypatch):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def values_of(written: str, row: int) -> list[str]:
    """The value cells of the `row`-th `cases` body."""
    bodies = [
        after.split(r"\end{cases}")[0]
        for after in written.split(r"\begin{cases}")[1:]
    ]
    return [
        branch.strip().replace(r"\displaystyle ", "").split("&", 1)[0].strip()
        for branch in re.split(r"\\\\(?:\[[^\]]*\])?", bodies[row])
    ]


def test_a_literal_branch_is_written_as_a_value(page):
    written = page(LOAD + "numeric(w_v(x))\n").replace(r"\dfrac", r"\frac")

    assert values_of(written, 1)[-1] == (
        r"\left(5.00\,\frac{\mathrm{kN}}{\mathrm{m}}\right)"
    ), values_of(written, 1)


def test_the_column_reads_as_one_kind_of_thing(page):
    """Both branches hold a value, so both are written as one."""
    for value in values_of(page(LOAD + "numeric(w_v(x))\n"), 1):
        assert value.startswith(r"\left("), value
        assert value.endswith(r"\right)"), value


def test_a_literal_beside_a_formula_is_written_as_a_value_too(page):
    written = page(BEAM + "numeric(M_W(x))\n")

    assert values_of(written, 1)[-1] == (
        r"\left(7.00\,\mathrm{kN} \cdot \mathrm{m}\right)"
    ), values_of(written, 1)


def test_every_value_branch_is_written_as_a_value_not_only_the_first(page):
    """A zero and a literal in one piecewise, with a formula between them."""
    written = page(TWO_VALUES + "numeric(M_T(x))\n")
    first, formula, last = values_of(written, 1)

    assert first == r"\left(0.00\,\mathrm{kN} \cdot \mathrm{m}\right)", first
    assert last == r"\left(7.00\,\mathrm{kN} \cdot \mathrm{m}\right)", last
    assert formula == r"\dfrac{x\,\left(40.00\,\mathrm{kN}\right)}{2}", formula


# --- what must not move ---------------------------------------------------------------


def test_a_branch_shows_the_value_that_was_substituted_into_it(page):
    r"""The substitution row is what the row substituted, not what the group agreed on.

    `q2 := 400*kgf/m` beside `q1 := 8*kN/m`: the engine brings the branches to one unit to
    answer, and the substitution row must still say `400.00 kgf/m`, because that is the
    value the sheet put there. Reading the engine's normalised value here instead would
    have the row claim a substitution that never happened.
    """
    written = page(MIXED + "numeric(q_m(x))\n").replace(r"\dfrac", r"\frac")

    assert values_of(written, 1)[1] == (
        r"\left(400.00\,\frac{\mathrm{kgf}}{\mathrm{m}}\right)"
    ), values_of(written, 1)
    assert values_of(written, 2)[1] == r"3.92\,\frac{\mathrm{kN}}{\mathrm{m}}", (
        values_of(written, 2)
    )


def test_a_formula_branch_is_not_collapsed_to_its_value(page):
    """On the path that binds the variable every branch resolves, and a formula still
    shows its working: the row exists to show it."""
    written = page(POINT + "numeric(M_P(1*m))\n")
    formula = values_of(written, 2)[0]

    assert formula == (
        r"\dfrac{\left(1.00\,\mathrm{m}\right)\,\left(40.00\,\mathrm{kN}\right)}{2}"
    ), formula


def test_the_definition_row_still_says_what_the_engineer_wrote(page):
    """`5 kN/m` is his writing, and the definition is where his writing belongs."""
    written = page(LOAD + "numeric(w_v(x))\n")

    assert values_of(written, 0) == [
        r"q_{1}",
        r"\dfrac{5\,\mathrm{kN}}{\mathrm{m}}",
    ], values_of(written, 0)


def test_a_formula_branch_keeps_its_shape(page):
    """A formula is not a single value and does not become a bracketed whole."""
    written = page(BEAM + "numeric(M_W(x))\n")
    formula = values_of(written, 1)[0]

    assert formula == r"\dfrac{x\,\left(40.00\,\mathrm{kN}\right)}{2}", formula


def test_a_name_branch_reads_as_it_did(page):
    written = page(LOAD + "numeric(w_v(x))\n").replace(r"\dfrac", r"\frac")

    assert values_of(written, 1)[0] == (
        r"\left(8.00\,\frac{\mathrm{kN}}{\mathrm{m}}\right)"
    ), values_of(written, 1)


def test_a_zero_branch_reads_as_it_did(page):
    """What #216 settled stays settled; a literal is the same case with a number in it."""
    written = page(ZERO + "numeric(q_v(x))\n").replace(r"\dfrac", r"\frac")

    assert values_of(written, 1)[-1] == (
        r"\left(0.00\,\frac{\mathrm{kN}}{\mathrm{m}}\right)"
    ), values_of(written, 1)


def test_the_answer_row_reads_as_it_did(page):
    written = page(LOAD + "numeric(w_v(x))\n").replace(r"\dfrac", r"\frac")

    assert values_of(written, 2) == [
        r"8.00\,\frac{\mathrm{kN}}{\mathrm{m}}",
        r"5.00\,\frac{\mathrm{kN}}{\mathrm{m}}",
    ], values_of(written, 2)
