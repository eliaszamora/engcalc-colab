r"""A piecewise condition keeps the interval variable on the side it was written.

The engineer's beam memoria, on the page, four lines apart:

    M_P(x) = { x P / 2        for x ≤ L/2
               P (L − x) / 2  for x ≤ L
               0              otherwise }

    Mo(x)  = { x P / 2        for x ≤ L/2
               P (L − x) / 2  for L ≥ x        <- the same condition, reversed
               0              otherwise }

And it is worse inside one block than between two: the first branch keeps `x` on the
left and the second moves it to the right, so a reader following the branches down sees
the variable change sides between adjacent lines.

**The builder already prevents this and substitution undoes it.** `build_relation` and
`build_piecewise` both pass `evaluate=False`, deliberately, so the stored expression says
what the sheet said. `Relational` has a canonical form that reorders a comparison when
*both* sides are bare symbols - `Le(x, L)` becomes `Ge(L, x)`, while `Le(x, L/2)` is left
alone because `L/2` is not a symbol - and `subs` rebuilds the Piecewise with evaluation
on, which applies it.

So a sheet that never reuses the function is fine and one that writes `case Mo = M_P(x)`
is not, and neither is a plain `N(x) = M_P(x)`. Measured: `subs(x, t)` flips it,
`subs(x, x)` does not, because SymPy skips the rebuild when nothing changes.

Which side is right is not a matter of taste here. `inspect_piecewise_variable` exists
because the language requires *"one direct comparison between the Piecewise interval
variable and a breakpoint expression"*, so there is always a variable and always a
breakpoint, and `for x ≤ L` is the direction every engineer writes and every branch of
this same piecewise already used.
"""

import io
from contextlib import redirect_stdout

import pytest
import sympy as sp

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> str:
        captured.clear()
        with redirect_stdout(io.StringIO()):
            magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


BEAM = (
    "L := 6.00*m\n"
    "P := 40*kN\n"
    "M_P(x) = piecewise(P*x/2, x <= L/2, P*(L - x)/2, x <= L, 0*kN*m)\n"
)


def conditions(page: str) -> list[list[str]]:
    """The `for ...` of every branch, one list per `cases` block."""
    blocks = []
    for chunk in page.split(r"\begin{cases}")[1:]:
        body = chunk.split(r"\end{cases}")[0]
        blocks.append(
            [
                piece.split(r"\\")[0].strip()
                for piece in body.split(r"\text{for}\:")[1:]
            ]
        )
    return blocks


def test_one_block_does_not_move_the_variable_between_its_branches(cell):
    """The sharpest form: adjacent lines of one piecewise."""
    page = cell(BEAM + "case Mo = M_P(x)\n")

    for block in conditions(page):
        assert block, page
        for condition in block:
            assert condition.startswith("x "), (condition, block)


def test_a_reused_function_states_its_conditions_as_the_first_one_did(cell):
    """`M_P` and `Mo` are the same function and must read the same."""
    page = cell(BEAM + "case Mo = M_P(x)\n")
    blocks = conditions(page)

    assert len(blocks) == 2, blocks
    assert blocks[0] == blocks[1], blocks


def test_a_plain_redefinition_is_no_different(cell):
    """It is not the `case` path: any substitution rebuilds the Piecewise."""
    page = cell(BEAM + "N(x) = M_P(x)\n")
    blocks = conditions(page)

    assert len(blocks) == 2, blocks
    assert blocks[0] == blocks[1], blocks


def test_the_substitution_still_happens(cell):
    """The branch-by-branch path must substitute, not merely reassemble.

    A mutant that returned the branches untouched - the piecewise put back together with
    its original symbols and nothing replaced - survived every contract here and in the
    suite. Reassembling correctly and substituting nothing is a perfect way to keep the
    conditions tidy and the answer wrong, and the cheapest case that separates them is a
    parameter with a different name.
    """
    page = cell(
        "L := 6.00*m\nP := 40*kN\n"
        "M_P(x) = piecewise(P*x/2, x <= L/2, P*(L - x)/2, x <= L, 0*kN*m)\n"
        "N(y) = M_P(y)\n"
    )
    blocks = conditions(page)

    assert len(blocks) == 2, blocks
    for condition in blocks[1]:
        assert condition.startswith("y "), (condition, blocks)


def test_a_combination_built_on_it_agrees_too(cell):
    """`combo` reaches the same expression by a third road."""
    page = cell(BEAM + "case Mo = M_P(x)\ncombo U = 1.2*Mo\n")

    for block in conditions(page):
        for condition in block:
            assert condition.startswith("x "), (condition, block)


# --- what must not move ---------------------------------------------------------------


def test_the_value_the_piecewise_computes_is_untouched(cell):
    """Reversing `L ≥ x` to `x ≤ L` is the same condition. If any number moved, the
    change is not about how a comparison is written."""
    page = cell(
        BEAM
        + "case Mo = M_P(x)\n"
        + "numeric(Mo(0*m))\nnumeric(Mo(3*m))\nnumeric(Mo(6*m))\n"
    )
    assert "60.00" in page, page
    assert page.count("0.00") >= 2, page


def test_a_condition_the_engineer_wrote_the_other_way_is_kept(cell):
    """The rule is *the side it was written on*, not "always `≤`". A sheet that writes
    the breakpoint first keeps it - what must not happen is one branch disagreeing with
    the next."""
    page = cell(
        "L := 6.00*m\nP := 40*kN\n"
        "M(x) = piecewise(P*x/2, L/2 >= x, P*(L - x)/2, L >= x, 0*kN*m)\n"
        "N(x) = M(x)\n"
    )
    blocks = conditions(page)
    assert len(blocks) == 2, blocks
    assert blocks[0] == blocks[1], blocks


def test_a_relation_outside_a_piecewise_is_not_touched():
    """`solve(M(x) > 20*kN*m, ...)` is a different feature with its own contracts."""
    x, L = sp.symbols("x L")
    assert str(sp.Le(x, L)) == "x <= L"
