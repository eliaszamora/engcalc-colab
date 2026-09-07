r"""Two values of the same kind get the same precision.

Found by re-running the braced-frame benchmark against 0.29.0. Its direction cosines,
one line apart:

    c_d =  0.804
    s_d = -0.59

Both are cosines of the same brace, computed the same way, and they are shown to
different precision. The only difference between them is whether the second decimal
happens to be a zero.

`_is_reduced` decides whether the page's decimals have left a value with nothing to say,
and it asks `_significant_figures`, which strips zeros from *both* ends. So `0.80386`
renders `0.80`, is counted as one figure because the trailing zero is discarded, is
judged reduced, and is rescued to `0.804`. `0.59489` renders `0.59`, counts as two, and
stays.

The two ends are not the same. A leading zero really does carry nothing - `0.002` has one
figure - but a trailing one is a digit the renderer chose to print, and `0.80` has lost
no more than `0.59` has. `_magnitude_text` already counts them that way, with a comment
saying `_significant_figures` strips both ends because it asks a different question. It
does: the band question is whether a value sits in the natural range for its unit, and
there a trailing zero genuinely carries nothing. The rescue kept the wrong one.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str) -> str:
        captured.clear()
        magic.EngMagics().eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


BRACE = "x2 := 0*m\nx4 := 5*m\ny2 := 3.70*m\ny4 := 0*m\nLd := sqrt((x4-x2)^2 + (y4-y2)^2)\n"


def test_the_two_direction_cosines_agree(cell):
    """The defect, in the values that found it."""
    c = _final(cell(BRACE + "cd = (x4 - x2)/Ld\nnumeric(cd)\n"))
    s = _final(cell(BRACE + "sd = (y4 - y2)/Ld\nnumeric(sd)\n"))
    assert "0.80" in c and "0.804" not in c, c
    assert "-0.59" in s and "-0.595" not in s, s


def test_a_second_decimal_of_zero_is_not_a_lost_digit(cell):
    """Directly: two ratios one hundredth apart, one landing on a trailing zero.

    Written first as `assert "0.80" in final`, which `0.804` satisfies - a contract that
    passes without exercising anything, section 1 of `HOW-THIS-WORK-GOES-WRONG.md`. The
    assertion has to exclude the longer form to mean anything.
    """
    wide = _final(cell("r := 0.80386\nx = 2*r/2\nnumeric(x)\n"))
    narrow = _final(cell("r := 0.79386\nx = 2*r/2\nnumeric(x)\n"))
    assert "0.804" not in wide, wide
    assert "0.80" in wide, wide
    assert "0.79" in narrow and "0.794" not in narrow, narrow


# --- the rescue must still fire where it was built to ---------------------------------

def test_a_period_is_still_rescued(cell):
    """`0.02` is one digit for real - a leading zero carries nothing."""
    final = _final(cell("T := 0.016756*s\nx = 1*T\nnumeric(x)\n"))
    assert "0.0168" in final, final


def test_a_value_with_nothing_left_is_still_rescued(cell):
    final = _final(cell("r := 0.002278125\ns = 1*r\nnumeric(s)\n"))
    assert "0.00228" in final, final


def test_the_engineers_own_floor_still_reads(cell):
    assert "0.00002" in _final(cell("t := 0.00002*s\nu = 1*t\nnumeric(u)\n"))


def test_an_exact_half_still_reads_as_it_did(cell):
    """`0.5` renders `0.50` either way - it has nothing more to give - so this is the
    case that shows the change is about inexact values, not about trailing zeros."""
    assert "0.50" in _final(cell("r := 0.5\nx = 2*r/2\nnumeric(x)\n"))


def test_an_ordinary_beam_is_unaffected(cell):
    final = _final(cell("q := 10*kN/m\nL := 6*m\nM = q*L**2/8\nnumeric(M)\n"))
    assert "45.00" in final, final
