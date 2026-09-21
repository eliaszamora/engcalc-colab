r"""`\dfrac` is a fraction, and the width estimate has to know that.

Found while correcting how a piecewise branch is set. `_stacked_width` looks for the
literal `\frac`, and `\dfrac` does not contain it - the backslash is followed by `d` - so
a display fraction never reaches the rule that measures a fraction across. It falls
through to `_flat_width`, which turns any unknown command into one character:

    \frac{x P}{2}     measured 9.0     max(numerator, denominator) + the rule
    \dfrac{x P}{2}    measured 5.0     a command, and its characters

Less than the fraction it is, and less than the same fraction written the other way. The
two are the same width on the page: display style changes the *size* of what is inside a
fraction, never whether MathJax stacks it.

It has been wrong since 0.31.2, which introduced `\dfrac` so a computed block would read
at the page's size. Any row measured with one in it has been measured too narrow since.
"""

import pytest

from engcalc_colab.renderer import _latex_visual_width


PAIRS = [
    (r"\frac{x P}{2}", r"\dfrac{x P}{2}"),
    (r"\frac{P \left(L - x\right)}{2}", r"\dfrac{P \left(L - x\right)}{2}"),
    (r"\frac{L}{2}", r"\dfrac{L}{2}"),
    (r"5 \frac{q L^{4}}{384 E I}", r"5 \dfrac{q L^{4}}{384 E I}"),
]


@pytest.mark.parametrize("flat, display", PAIRS)
def test_a_display_fraction_measures_what_the_same_fraction_measures(flat, display):
    assert _latex_visual_width(display) == _latex_visual_width(flat)


def test_a_display_fraction_is_measured_across_and_not_end_to_end():
    """The rule itself, on a display fraction: the wider half, plus the rule.

    The halves are 20 and 10, so end to end is 30 and across is 26 - far enough apart
    that the two answers cannot be confused. A first draft used 20 and 6, where they are
    both 26 and the test could not fail.
    """
    numerator, denominator = "a" * 20, "b" * 10
    whole = rf"\dfrac{{{numerator}}}{{{denominator}}}"

    assert _latex_visual_width(whole) < len(numerator) + len(denominator)
    assert _latex_visual_width(whole) == pytest.approx(len(numerator) + 6.0, abs=0.01)


def test_a_display_fraction_inside_another_is_followed():
    """The recursion reaches it too, which is the shape a frame's frequency has."""
    inner = r"\dfrac{" + "a" * 24 + "}{" + "b" * 24 + "}"
    whole = rf"\dfrac{{{inner}}}{{c}}"

    assert _latex_visual_width(whole) == pytest.approx(
        _latex_visual_width(inner) + 6.0, abs=0.01
    )


# --- what must not move ---------------------------------------------------------------


def test_an_ordinary_fraction_measures_what_it_measured():
    assert _latex_visual_width(r"\frac{x P}{2}") == pytest.approx(9.0, abs=0.01)


def test_a_stretch_with_no_fraction_is_counted_straight_across():
    left = r"384 \left(200.00\,\mathrm{GPa}\right)"
    right = r"\left(8.00 \times 10^{7}\,\mathrm{mm}^{4}\right)"

    assert _latex_visual_width(left + right) == pytest.approx(
        _latex_visual_width(left) + _latex_visual_width(right), abs=0.01
    )
