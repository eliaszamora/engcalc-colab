r"""A zero branch keeps its unit when the piecewise is evaluated at a point too.

#216 gave the zero branch its unit in the substitution row of a *partially* evaluated
piecewise. The same row, with the variable bound, still read a bare zero - and the
sharpest form of it is two lines apart on one block:

    q_v(9*m)  =  ⎧ (8.00 kN/m)   for (9.00 m) < (3.00 m)
                 ⎨ (4.00 kN/m)   for (9.00 m) ≤ (6.00 m)
                 ⎩ 0             otherwise

              =  0.00 kN/m

the same branch, written once without its unit and once with it.

On the engineer's own beam the other branches are not single quantities but expressions -
`(100.00 cm) (4000.00 kgf) / 2` - so the unit cannot be read off a neighbour's printed
form. It has to be evaluated, which is the engine's work, not the renderer's.

`build_partial_piecewise_evaluation` already does exactly that for the partial path, and
the step that gives a bare `Integer(0)` its unit is `_normalize_quantity_group(values,
"piecewise branches")` - the same call that raises "piecewise branches has incompatible
units" when they do not agree. This file asks the fully numeric path to carry the same
group, so the renderer reads a value rather than deriving one.

Older than 0.31.7; the row has read a bare zero for as long as it has been drawn.
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
q_v(x) = piecewise(q1, x < a_q, q2, x <= L, 0*kN/m)
"""

BEAM = """L := 600*cm
P := 4000*kgf
M_P(x) = piecewise(P*x/2, x <= L/2, P*(L - x)/2, x <= L, 0*kgf*cm)
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
    """The last `cases` row: the one the values were substituted into."""
    return bodies_of(written)[-1]


def test_a_zero_branch_is_shown_in_the_unit_beside_it_at_a_point(page):
    written = page(LOAD + "numeric(q_v(1*m))\n").replace(r"\dfrac", r"\frac")
    values = values_of(substitution_body(written))

    assert values[-1] == r"\left(0.00\,\frac{\mathrm{kN}}{\mathrm{m}}\right)", values


def test_the_zero_does_not_differ_from_the_answer_two_lines_below_it(page):
    """The sharpest form: the branch that answers is the branch written as a zero."""
    written = page(LOAD + "numeric(q_v(9*m))\n").replace(r"\dfrac", r"\frac")
    zero = values_of(substitution_body(written))[-1]

    assert zero == r"\left(0.00\,\frac{\mathrm{kN}}{\mathrm{m}}\right)", zero
    assert r"& = & \displaystyle 0.00\,\frac{\mathrm{kN}}{\mathrm{m}}" in written, written


def test_a_branch_that_is_an_expression_still_decides_the_unit(page):
    """The engineer's own beam: no neighbour is a single quantity to read a unit off."""
    written = page(BEAM + "numeric(M_P(100*cm))\n")
    values = values_of(substitution_body(written))

    assert values[-1] == r"\left(0.00\,\mathrm{kgf} \cdot \mathrm{cm}\right)", values


# --- what must not move ---------------------------------------------------------------


def test_the_definition_row_still_says_zero(page):
    """The symbolic row names names; a zero there has no unit to be shown in."""
    written = page(LOAD + "numeric(q_v(1*m))\n")

    assert values_of(bodies_of(written)[0]) == ["q_{1}", "q_{2}", "0"], written


def test_the_answer_still_answers(page):
    written = page(LOAD + "numeric(q_v(1*m))\n").replace(r"\dfrac", r"\frac")

    assert r"& = & \displaystyle 8.00\,\frac{\mathrm{kN}}{\mathrm{m}}" in written, written


def test_the_partial_path_is_unchanged(page):
    """What #216 settled stays settled."""
    written = page(LOAD + "numeric(q_v(x))\n").replace(r"\dfrac", r"\frac")
    definition, substituted, answer = bodies_of(written)

    assert values_of(substituted)[-1] == (
        r"\left(0.00\,\frac{\mathrm{kN}}{\mathrm{m}}\right)"
    ), substituted
    assert values_of(answer)[-1] == r"0.00\,\frac{\mathrm{kN}}{\mathrm{m}}", answer


def test_a_row_with_no_piecewise_in_it_is_untouched(page):
    written = page("b := 30*cm\nh := 60*cm\nA = b*h\nnumeric(A)\n")

    product = r"\left(30.00\,\mathrm{cm}\right)\,\left(60.00\,\mathrm{cm}\right)"

    assert product in written, written
    assert r"1800.00\,\mathrm{cm}^{2}" in written, written
