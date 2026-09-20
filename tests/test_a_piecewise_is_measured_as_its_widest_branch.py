r"""A `cases` body is as wide as its widest branch, because MathJax stacks them.

Found by a visual pass over 0.31.6, on the engineer's own beam. His point load reads

    M_P(x)  =
                  ⎧ xP/2       for x ≤ L/2
                  ⎨ P(L−x)/2   for x ≤ L
                  ⎩ 0          otherwise

with the `=` pointing at nothing and the body dropped to its own row, where every other
definition on the page sits beside its name. Measured: the estimate charges that body
**94** against a budget of 104, and the name in front of it takes the row over. What the
reader sees is **30** - a `cases` environment stacks its branches, exactly as a fraction
stacks its halves.

This is the defect `test_a_fraction_is_measured_across` removed for fractions, in the
environment it did not reach. That file's own words: it "charged a fraction its numerator
*plus* its denominator", and "MathJax stacks a fraction, so what the reader sees is the
wider half".

The branch with the widest *value* need not be the branch with the widest *condition*, so
what is measured is the whole branch, value and condition together.
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

CASES = (
    r"\begin{cases} \frac{x P}{2} & \text{for}\: x \leq \frac{L}{2} \\"
    r"\frac{P \left(L - x\right)}{2} & \text{for}\: x \leq L \\"
    r"0 & \text{otherwise} \end{cases}"
)


@pytest.fixture
def page(monkeypatch):
    def run(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return run


def test_a_cases_body_is_measured_across_its_branches():
    """Stated as the property: the whole body costs about what one branch costs."""
    branches = [
        r"\frac{x P}{2} & \text{for}\: x \leq \frac{L}{2}",
        r"\frac{P \left(L - x\right)}{2} & \text{for}\: x \leq L",
        r"0 & \text{otherwise}",
    ]
    widest = max(_latex_visual_width(branch) for branch in branches)
    added_up = sum(_latex_visual_width(branch) for branch in branches)

    assert _latex_visual_width(CASES) < added_up, _latex_visual_width(CASES)
    assert _latex_visual_width(CASES) == pytest.approx(widest + 2.0, abs=0.01)


def test_the_widest_branch_decides_even_when_it_is_the_last():
    """The order of the branches cannot change what the body costs."""
    short = r"0 & \text{otherwise}"
    long = r"\frac{" + "a" * 30 + r"}{2} & \text{for}\: x \leq L"
    first = rf"\begin{{cases}} {long} \\ {short} \end{{cases}}"
    last = rf"\begin{{cases}} {short} \\ {long} \end{{cases}}"

    assert _latex_visual_width(first) == _latex_visual_width(last)


def test_a_condition_counts_toward_its_branch():
    """A branch is its value and its condition, side by side on one line."""
    bare = r"\begin{cases} 0 \\ 1 \end{cases}"
    with_condition = r"\begin{cases} 0 & \text{for}\: x \leq L \\ 1 \end{cases}"

    assert _latex_visual_width(with_condition) > _latex_visual_width(bare)


@pytest.mark.parametrize(
    "written",
    [
        "abcdefghij + " + CASES,
        CASES + " + abcdefghij",
    ],
)
def test_what_sits_beside_a_cases_body_is_counted_too(written):
    """A piecewise is not always the whole right-hand side.

    `Q(x) = M_P(x) + P*L` puts `L P +` in front of the body and `N(x) = 2*M_P(x)` puts a
    bracket after it. Found by mutation: dropping either side changed nothing the
    reference pages could see, because on them the body is the whole row.
    """
    assert _latex_visual_width(written) > _latex_visual_width(CASES)


def test_the_definition_sits_beside_its_name(page):
    """The page, which is where this was seen."""
    written = page(BEAM)
    body = written[written.index(r"\begin{cases}") : written.index(r"\end{cases}")]

    assert _latex_visual_width(body) < _COMPLETE_ROW_VISUAL_BUDGET
    assert r"M_{P}\left(x\right) & = & \displaystyle \begin{cases}" in written, written
    assert r"M_{P}\left(x\right) & = & \\" not in written, written


# --- what must not move ---------------------------------------------------------------


def test_a_row_with_no_cases_in_it_is_measured_as_before():
    left = r"384 \left(200.00\,\mathrm{GPa}\right)"
    right = r"\left(8.00 \times 10^{7}\,\mathrm{mm}^{4}\right)"

    assert _latex_visual_width(left + right) == pytest.approx(
        _latex_visual_width(left) + _latex_visual_width(right), abs=0.01
    )


def test_a_fraction_is_still_measured_across():
    assert _latex_visual_width(r"\frac{x P}{2}") == pytest.approx(9.0, abs=0.01)


def test_the_branches_still_say_what_they_said(page):
    """Read past the fraction's size, which is a separate question from its width."""
    written = page(BEAM).replace(r"\dfrac", r"\frac")
    assert r"\text{for}\: x \leq \frac{L}{2}" in written, written
    assert r"\text{otherwise}" in written, written
