r"""The branches of a `cases` body are set apart, now that they are full height.

Seen in Colab, on the engineer's own run of 0.31.8. A `cases` body gives its branches no
separation at all: measured on the rendered page, every body has **0 px** between its
rows while the rows of the block around it are given 10.2 px by `\\[8pt]`. With branches
18 px tall that read as a tight list and nobody noticed. 0.31.7 set them in display style
with full-size fractions, which took them to 36-44 px, and at that height the fraction
rule of one branch sits directly against the numerator of the next:

    ⎧ 8.00 kN
    ⎪      m
    ⎨ 4.00 kN      <- the `m` above and this `kN` are touching
    ⎪      m
    ⎩ 0.00 kN
           m

So this is 0.31.7's own doing, in the half of the question it did not ask: it made the
branches the right size without giving them the room that size needs.

**Measured, not guessed.** In a MathJax page loading the same 3.2.2 build the notebook
loads, the three-branch body above is 106.2 px tall joined with `\\`, 119.2 px with
`\\[4pt]` and 125.6 px with `\\[6pt]`. The separation MathJax adds goes *inside* the row
box rather than between boxes, which is why the gap between rows reads 0 either way - the
gap was the wrong instrument, and a first attempt at this measured nothing because of it.

A strut was tried first, the way `_computed_block` makes its room: `\rule[-0.4em]{0pt}
{1.4em}` in front of each branch changed the body's height by **nothing at all**. It is
not the tool here.

`4pt`, half of the `8pt` the block gives its own rows: the branches of one definition are
a tighter grouping than two stages of a calculation, and should not be spaced as if they
were separate.

The estimator must not be charged for any of this. `_cases_span` splits a body on `\\`,
so an unhandled `\\[4pt]` would put five characters in front of every branch and re-inflate
the measurement `test_a_piecewise_is_measured_as_its_widest_branch` corrected - which is
what put `M_P(x) =` on a row with nothing after it in the first place.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic
from engcalc_colab.renderer import _COMPLETE_ROW_VISUAL_BUDGET, _latex_visual_width

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
numeric(q_v(x))
"""

# The middle branch is the widest, on purpose. A separator pattern that is too greedy
# swallows everything between the first `\\[` and the last `]`, which eats the branches
# in between; with the beam's own two value branches the estimator scores both at 31.0,
# so losing one of them changes nothing a contract can see. Found by mutation, which is
# the same trap `test_a_display_fraction_is_measured_as_a_fraction` recorded when a
# numerator of 20 over a denominator of 6 measured 26 whether it was summed or maxed.
# `qD` comes from the engineer's own beam, where `M_D(x)` is written exactly this way.
BRANCHES = (
    r"\displaystyle \dfrac{x P}{2} & \text{for}\: x \leq \dfrac{L}{2}",
    r"\displaystyle \dfrac{\mathrm{qD}\,x \left(L - x\right)}{2} & \text{for}\: x \leq L",
    r"\displaystyle 0 & \text{otherwise}",
)
FLUSH = r"\begin{cases} " + r" \\ ".join(BRANCHES) + r" \end{cases}"
SPACED = r"\begin{cases} " + r" \\[4pt] ".join(BRANCHES) + r" \end{cases}"


@pytest.fixture
def page(monkeypatch):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def bodies_of(written: str) -> list[str]:
    return [
        after.split(r"\end{cases}")[0]
        for after in written.split(r"\begin{cases}")[1:]
    ]


def test_the_branches_of_a_definition_are_set_apart(page):
    (body,) = bodies_of(page(BEAM))

    assert body.count(r"\\[4pt]") == 2, body
    assert r"\\ " not in body, body


def test_every_body_of_a_partly_evaluated_block_is_set_apart(page):
    """Three rows, two producers: SymPy's printer and `_piecewise_partial_latex`."""
    bodies = bodies_of(page(LOAD))

    assert len(bodies) == 3, bodies
    for body in bodies:
        assert body.count(r"\\[4pt]") == 2, body


# --- the measurement this must not disturb --------------------------------------------


def test_the_room_between_branches_costs_the_page_no_width():
    """`\\[4pt]` is not drawn, so it is not charged."""
    assert _latex_visual_width(SPACED) == pytest.approx(
        _latex_visual_width(FLUSH), abs=0.01
    )


def test_the_widest_branch_is_the_middle_one():
    """The property the two contracts below lean on, stated so it cannot drift away."""
    widths = [_latex_visual_width(branch) for branch in BRANCHES]

    assert widths.index(max(widths)) == 1, widths
    assert widths[1] > widths[0], widths


def test_a_branch_is_still_measured_across_and_not_end_to_end():
    widest = max(_latex_visual_width(branch) for branch in BRANCHES)
    added_up = sum(_latex_visual_width(branch) for branch in BRANCHES)

    assert _latex_visual_width(SPACED) < added_up
    assert _latex_visual_width(SPACED) == pytest.approx(widest + 2.0, abs=0.01)


def test_the_definition_still_sits_beside_its_name(page):
    """What `test_a_piecewise_is_measured_as_its_widest_branch` won, kept."""
    written = page(BEAM)
    (body,) = bodies_of(written)

    assert _latex_visual_width(body) < _COMPLETE_ROW_VISUAL_BUDGET
    assert r"M_{P}\left(x\right) & = & \displaystyle \begin{cases}" in written, written
    assert r"M_{P}\left(x\right) & = & \\" not in written, written


# --- what must not move ---------------------------------------------------------------


def test_the_branches_still_say_what_they_said(page):
    (body,) = bodies_of(page(BEAM))
    said = [branch.strip() for branch in body.split(r"\\[4pt]")]

    assert said == [
        r"\displaystyle \dfrac{x P}{2} & \text{for}\: x \leq \dfrac{L}{2}",
        r"\displaystyle \dfrac{P \left(L - x\right)}{2} & \text{for}\: x \leq L",
        r"\displaystyle 0 & \text{otherwise}",
    ], said


def test_the_rows_of_the_block_keep_their_own_spacing(page):
    """`8pt` between stages is a separate decision and is not touched."""
    written = page(LOAD)

    assert r"\\[8pt]" in written, written


def test_a_block_with_no_cases_in_it_is_untouched(page):
    written = page("b := 30*cm\nh := 60*cm\nA = b*h\nnumeric(A)\n")

    assert r"\\[4pt]" not in written, written
    assert r"1800.00\,\mathrm{cm}^{2}" in written, written
