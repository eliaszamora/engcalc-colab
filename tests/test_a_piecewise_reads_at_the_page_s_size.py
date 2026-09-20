r"""A piecewise branch is set at the size the rows around it are set at.

Found by a visual pass over 0.31.6, on the engineer's own beam. His point load gives

    M_P(x)  =
                  ⎧ xP/2       for x ≤ L/2
                  ⎨ P(L−x)/2   for x ≤ L
                  ⎩ 0          otherwise

and the fractions inside the branches are visibly smaller than the fractions in the rows
above them. Measured on the rendered page at Colab's width: **20.7 px and 23.6 px against
36.4 px** for the fractions of the same block, two rows up.

A `cases` environment sets its cells in text style, where a fraction is drawn small.
0.31.2 answered the same question for the computed blocks - "a characteristic block sets
its formulas in display style with full-size fractions ... so a frame's frequencies read
at the page's size" - and `cases` is where that did not reach. `\dfrac` as well as
`\displaystyle`, for the reason recorded there: `\displaystyle` sizes only the outermost
fraction, and a branch can hold one inside another.

A partially evaluated piecewise writes **three** `cases` rows, and they come from two
places. The definition and the row with the values substituted into it are printed by
SymPy's `Piecewise` printer, through this package's subclass of it. The answer row - the
one the engineer reads off - is built here, by `_piecewise_partial_latex`, and it holds
its own fractions: a load in `kN/m` is drawn as one.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")


BEAM = """L := 600*cm
P := 4000*kgf
M_P(x) = piecewise(P*x/2, x <= L/2, P*(L - x)/2, x <= L, 0*kgf*cm)
"""

LOAD = """q1 := 8*kN/m
q2 := 4*kN/m
a := 3*m
L := 6*m
q(x) = piecewise(q1, x < a, q2, x <= L, 0*kN/m)
numeric(q(x))
"""


@pytest.fixture
def page(monkeypatch):
    def run(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return run


def bodies_of(written: str) -> list[list[str]]:
    r"""Every `cases` body on the page, each as its list of branches."""
    bodies = []
    for after in written.split(r"\begin{cases}")[1:]:
        inner = after.split(r"\end{cases}")[0]
        bodies.append([branch.strip() for branch in inner.split(r"\\")])
    return bodies


def answer_body(written: str) -> list[str]:
    r"""The body `_piecewise_partial_latex` built: the last row, the one that answers.

    Above it sit the definition and the row with the values substituted into it, both
    printed by SymPy. This one is the only one whose numbers are not in brackets.
    """
    bodies = bodies_of(written)

    assert len(bodies) == 3, written
    assert not any(r"\left(8.00" in branch for branch in bodies[-1]), bodies[-1]
    return bodies[-1]


def test_every_branch_of_a_definition_is_in_display_style(page):
    (body,) = bodies_of(page(BEAM))

    for branch in body:
        assert branch.startswith(r"\displaystyle "), branch


def test_a_fraction_in_a_branch_is_drawn_at_full_size(page):
    r"""`\dfrac`, not `\frac`: `\displaystyle` sizes only the outermost one."""
    (body,) = bodies_of(page(BEAM))
    branches = " ".join(body)

    assert r"\dfrac{x P}{2}" in branches, branches
    assert r"\frac{x P}{2}" not in branches.replace(r"\dfrac", r"\d?frac"), branches


def test_every_branch_of_an_answer_row_is_in_display_style(page):
    """The other producer, which does not go through SymPy's printer at all."""
    for branch in answer_body(page(LOAD)):
        assert branch.startswith(r"\displaystyle "), branch


def test_a_fraction_in_an_answer_branch_is_drawn_at_full_size(page):
    """A load in `kN/m` is a fraction, in the row the engineer reads off."""
    branches = " ".join(answer_body(page(LOAD)))

    assert r"\dfrac{\mathrm{kN}}{\mathrm{m}}" in branches, branches
    assert r"\frac{\mathrm{kN}}" not in branches.replace(r"\dfrac", r"\d?frac"), branches


# --- what must not move ---------------------------------------------------------------


def test_the_branches_still_say_what_they_said(page):
    """Read past the fraction's size, so that changing it cannot satisfy this."""
    (body,) = bodies_of(page(BEAM))
    conditions = [branch.split("&", 1)[1].strip() for branch in body]
    plain = [condition.replace(r"\dfrac", r"\frac") for condition in conditions]

    assert plain == [
        r"\text{for}\: x \leq \frac{L}{2}",
        r"\text{for}\: x \leq L",
        r"\text{otherwise}",
    ], conditions


def test_the_answer_row_still_answers(page):
    """Read past the fraction's size as well: the values and their breakpoints."""
    said = [
        branch.replace(r"\dfrac", r"\frac").replace(r"\displaystyle ", "")
        for branch in answer_body(page(LOAD))
    ]
    kn_per_m = r"\frac{\mathrm{kN}}{\mathrm{m}}"

    assert said == [
        rf"8.00\,{kn_per_m} & \text{{for}}\: x < 3.00\,\mathrm{{m}}",
        rf"4.00\,{kn_per_m} & \text{{for}}\: x \leq 6.00\,\mathrm{{m}}",
        rf"0.00\,{kn_per_m} & \text{{otherwise}}",
    ], said


def test_a_row_with_no_piecewise_in_it_is_untouched(page):
    written = page("b := 30*cm\nh := 60*cm\nA = b*h\n")

    assert r"\displaystyle A & = & \displaystyle b h" in written, written
    assert r"\dfrac" not in written, written
