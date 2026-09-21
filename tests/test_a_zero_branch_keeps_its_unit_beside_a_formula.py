r"""A zero branch takes its unit even when every branch beside it holds the variable.

#216 and #217 gave a zero branch the unit its neighbours are shown in. Both reached it the
same way: the engine resolves every branch to a quantity and `_normalize_quantity_group`
hands the group one unit, which is what turns a bare `Integer(0)` into `0.00 kN/m`.

That works when the neighbouring branches are **names**. On the engineer's own beam they
are **formulas holding the interval variable**, so they never resolve to a quantity at
all - they stay symbolic, with their coefficients evaluated - and the zero is left alone
in the group with nothing to take a unit from:

    M_P(x) = piecewise(P*x/2, x <= L/2, P*(L - x)/2, x <= L, 0*kgf*cm)
    numeric(M_P(x))

    definition    0                   correct: the symbolic row has no unit to show
    substitution  (0.00)              bracketed, and dimensionless
    answer        0.00                a moment, with no unit, in the row he reads off

So #216 closed the case where the branches are names and left open the one every real
beam is written in.

**The unit is not guessed.** `_infer_piecewise_zero_unit` already answers exactly this
question - it is what makes `numeric(q(9*m))` answer `0.00 kN/m` - by evaluating the other
branches and taking the unit they agree on. It could not be used here because a branch
holding `x` does not evaluate while `x` is free. It does evaluate once `x` is given one
unit of its own dimension, and the breakpoints say what that dimension is: `x <= L/2` with
`L` in centimetres makes `x` a length, so `P*x/2` is `kgf·cm`, which is what the engineer
wrote in the default branch in the first place.

A unit is inferred only when the group settled on none. Where a neighbour already resolved
to a quantity, #216's answer stands untouched.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell

matplotlib.use("Agg")


BEAM = """L := 600*cm
P := 4000*kgf
M_P(x) = piecewise(P*x/2, x <= L/2, P*(L - x)/2, x <= L, 0*kgf*cm)
"""

LOAD = """q1 := 8*kN/m
q2 := 4*kN/m
a_q := 3*m
L := 6*m
q_v(x) = piecewise(q1, x < a_q, q2, x <= L, 0*kN/m)
"""

RATIO = """k1 := 2
a_q := 3
f_v(x) = piecewise(k1*x, x < a_q, 0)
"""

# A span carrying nothing at either end: two zero branches around one that holds the
# variable. Found by mutation - paying only the first zero left the last one bare, and
# every other sheet here has exactly one zero to pay.
TWO_ZEROS = """L := 600*cm
a_t := 200*cm
P := 4000*kgf
M_T(x) = piecewise(0*kgf*cm, x <= a_t, P*(x - a_t)/2, x <= L, 0*kgf*cm)
"""


@pytest.fixture
def page(monkeypatch):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def evaluate(sheet: str, call: str):
    engine = EngineeringEngine()
    result = None
    for line in (sheet + call).strip().splitlines():
        result = run(engine, line)
    return result


def zero_branch_of(written: str, row: int) -> str:
    """The last branch of the `row`-th `cases` body, as it is written."""
    import re

    bodies = [
        after.split(r"\end{cases}")[0]
        for after in written.split(r"\begin{cases}")[1:]
    ]
    branches = re.split(r"\\\\(?:\[[^\]]*\])?", bodies[row])
    return (
        branches[-1].strip().replace(r"\displaystyle ", "").split("&", 1)[0].strip()
    )


def test_the_substituted_row_writes_the_zero_in_the_branches_unit(page):
    written = page(BEAM + "numeric(M_P(x))\n")

    assert zero_branch_of(written, 1) == (
        r"\left(0.00\,\mathrm{kgf} \cdot \mathrm{cm}\right)"
    ), zero_branch_of(written, 1)


def test_the_answer_row_writes_the_zero_in_the_branches_unit(page):
    """The row the engineer reads off."""
    written = page(BEAM + "numeric(M_P(x))\n")

    assert zero_branch_of(written, 2) == r"0.00\,\mathrm{kgf} \cdot \mathrm{cm}", (
        zero_branch_of(written, 2)
    )


def test_every_zero_branch_is_paid_not_only_the_first(page):
    """A span carrying nothing at either end has two of them."""
    import re

    written = page(TWO_ZEROS + "numeric(M_T(x))\n")
    answer = written.split(r"\begin{cases}")[3].split(r"\end{cases}")[0]
    values = [
        branch.strip().replace(r"\displaystyle ", "").split("&", 1)[0].strip()
        for branch in re.split(r"\\\\(?:\[[^\]]*\])?", answer)
    ]

    assert values[0] == r"0.00\,\mathrm{kgf} \cdot \mathrm{cm}", values
    assert values[-1] == r"0.00\,\mathrm{kgf} \cdot \mathrm{cm}", values


def test_the_engine_carries_the_unit_not_just_the_page():
    """Read off the evaluation itself, so this cannot be satisfied by string surgery.

    Asked by conversion rather than by the unit's printed name: Pint writes the same
    moment as `kgf·cm` here and `cm * kgf` elsewhere depending on the format, and a
    contract that pins one spelling is testing the formatter.
    """
    result = evaluate(BEAM, "numeric(M_P(x))\n")
    default = result.piecewise_evaluation.branches[-1]

    assert not default.value.dimensionless, default.value
    assert float(default.value.to("kgf * cm").magnitude) == pytest.approx(0.0)


# --- what must not move ---------------------------------------------------------------


def test_the_definition_row_still_says_zero(page):
    """The symbolic row names names; a zero there has no unit to be shown in."""
    written = page(BEAM + "numeric(M_P(x))\n")

    assert zero_branch_of(written, 0) == "0", zero_branch_of(written, 0)


def test_what_216_settled_stays_settled(page):
    """Branches that are names already resolved; that answer is untouched."""
    written = page(LOAD + "numeric(q_v(x))\n").replace(r"\dfrac", r"\frac")

    assert zero_branch_of(written, 1) == (
        r"\left(0.00\,\frac{\mathrm{kN}}{\mathrm{m}}\right)"
    ), zero_branch_of(written, 1)


def test_the_fully_evaluated_beam_is_unchanged(page):
    """`numeric(M_P(100*cm))` goes down another path and already answered."""
    written = page(BEAM + "numeric(M_P(100*cm))\n")

    assert zero_branch_of(written, 2) == (
        r"\left(0.00\,\mathrm{kgf} \cdot \mathrm{cm}\right)"
    ), zero_branch_of(written, 2)


def test_a_piecewise_with_no_units_in_it_stays_bare(page):
    """A unit is inferred where there is one to infer, and invented nowhere."""
    written = page(RATIO + "numeric(f_v(x))\n")

    assert zero_branch_of(written, 2) == "0.00", zero_branch_of(written, 2)
