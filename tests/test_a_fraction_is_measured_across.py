r"""A fraction is as wide as its wider half, and a substituted fraction stays a fraction.

On the engineer's beam memoria, four lines apart:

    delta  =  5 q_s L⁴ / (384 E I)                        one clean fraction
           =  5 (30.59 kgf/cm) (600.00 cm)⁴
              . 1/(384 (239633.31 kgf/cm²) (540000.00 cm⁴))   the numerator, then a dot,
                                                              then one over the rest
           =  0.40 cm

Nobody writes that. The symbolic line is a fraction and the line under it - the same
expression with numbers in - is a product with a reciprocal in it.

**The splitter was never supposed to be reached.** `_latex_visual_width` gates it, and it
charged a fraction its numerator *plus* its denominator plus six for the rule. MathJax
stacks a fraction, so what the reader sees is the wider half:

    5 q_s L⁴ / (384 E I)     estimated 83 against a budget of 64
                             what he sees is 44

Judged over budget, it went to `_bounded_product_rows`, which splits a product at factor
boundaries - and SymPy's `A/B` is `Mul(A, Pow(B, -1))`, so the split fell right between
numerator and denominator. The splitter was doing exactly what it says.

**It also closes a remainder that was recorded as a trade.** `NEXT.md` says a formula too
wide to sit beside its own value is not promoted into the identity column, because
`5 k q L^4 / (384 E I)` "measures 124 against a budget of 104" and "an identity column
that wide pushes every other row's `=` across the page". Measured on the rendered page at
Colab's 900 px, promoting it makes the block **4 px narrower and 135 px shorter**: the
identity is a stacked fraction about 150 px wide, and the loose row it replaces ran the
full width. The trade was taken against a number that was wrong.
"""

import matplotlib
import pytest

matplotlib.use("Agg")

import engcalc_colab.magic as magic  # noqa: E402
from engcalc_colab.renderer import (  # noqa: E402
    _NUMERIC_ROW_VISUAL_BUDGET,
    _latex_visual_width,
)


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str, *, palette: str = "") -> str:
        magics = magic.EngMagics()
        captured.clear()
        if palette:
            magics.eng_units(palette)
            captured.clear()
        magics.eng("", source)
        page = "".join(str(getattr(obj, "data", "")) for obj in captured)
        assert page.strip(), [type(obj).__name__ for obj in captured]
        return page

    return run


DEFLECTION = (
    "q := 10*kN/m\n"
    "L := 6*m\n"
    "E := 200*GPa\n"
    "I_z := 80e6*mm**4\n"
    "d = 5*q*L**4/(384*E*I_z)\n"
    "numeric(d)\n"
)

# The engineer's own sheet, in the units he reads it in.
HIS_DEFLECTION = (
    "L := 6.00*m\nb := 300*mm\nh := 600*mm\nE := 23500*MPa\n"
    "qD := 18*kN/m\nqL := 12*kN/m\n"
    "keep I = b*h^3/12\n"
    "keep q_s = qD + qL\n"
    "keep delta = 5*q_s*L^4/(384*E*I)\n"
    "report(delta)\n"
)


def test_a_substituted_fraction_is_still_one_fraction(cell, capsys):
    """The defect, on his page: the numerator on one row and `\\cdot \\frac{1}{...}` on
    the next."""
    page = cell(HIS_DEFLECTION, palette="kgf")
    capsys.readouterr()

    assert r"\quad \cdot \frac{1}" not in page, page


def test_the_substituted_line_has_the_shape_of_the_line_above_it(cell, capsys):
    """Stated as the property rather than as the absence of one marker: a fraction
    substituted is a fraction, so the two lines have the same number of `\\frac` at the
    top level and the reader can follow one into the other."""
    page = cell(DEFLECTION)
    capsys.readouterr()

    symbolic = r"\frac{5 q L^{4}}{384 E I_{z}}"
    assert symbolic in page, page
    substituted = page.split(symbolic, 1)[1]
    substituted = substituted.split(r"10.55", 1)[0]
    assert substituted.count(r"\frac{5 ") == 1, substituted
    assert r"\frac{1}" not in substituted, substituted


def test_a_fraction_costs_the_wider_half_and_not_both(cell):
    """The estimator itself, over the shape that started it."""
    numerator = r"5 \left(10.00\,\frac{\mathrm{kN}}{\mathrm{m}}\right)"
    denominator = r"384 \left(200.00\,\mathrm{GPa}\right) \left(8.00 \times 10^{7}\right)"
    whole = rf"\frac{{{numerator}}}{{{denominator}}}"

    halves = max(_latex_visual_width(numerator), _latex_visual_width(denominator))
    both = _latex_visual_width(numerator) + _latex_visual_width(denominator)

    assert _latex_visual_width(whole) < both, (_latex_visual_width(whole), both)
    assert _latex_visual_width(whole) == pytest.approx(halves + 6.0, abs=0.01), (
        _latex_visual_width(whole),
        halves,
    )


# --- what must not move ---------------------------------------------------------------


# Ten factors and no denominator. Nine is where the row budget starts to bite, measured;
# ten leaves a margin. The contracts elsewhere that needed a wrapped block used the
# deflection until now, and the deflection's wrapping was the defect.
LONG_PRODUCT = (
    "a := 1.11*m\nb := 2.22*m\nc := 3.33*m\nd := 4.44*m\ne := 5.55*m\n"
    "f := 6.66*m\ng := 7.77*m\nh := 8.88*m\ni := 9.99*m\nj := 11.10*m\n"
    "numeric(a*b*c*d*e*f*g*h*i*j)\n"
)


def test_a_product_with_no_denominator_still_wraps(cell):
    """The splitter is not being removed, and a long product genuinely needs it: there is
    no fraction to stack, so the row budget is the only thing holding the line."""
    page = cell(LONG_PRODUCT)

    assert r"\quad \cdot " in page, page


def test_a_fraction_inside_a_fraction_is_measured_across_too(cell):
    """The recursion, pinned on the function.

    A mutant that measured a numerator flat instead of following the fractions inside it
    survived the whole suite: his deflection's numerator holds `kgf/cm`, so the recursion
    runs on every page, but the two answers are a couple of characters apart and no
    layout decision turns on them. Here the inner fraction is wide enough that they are
    not: measured flat, a numerator holding one costs its two halves added up.
    """
    top, bottom = "a" * 24, "b" * 24
    inner = rf"\frac{{{top}}}{{{bottom}}}"
    whole = rf"\frac{{{inner}}}{{c}}"

    inner_stacked = _latex_visual_width(inner)
    assert _latex_visual_width(whole) == pytest.approx(
        inner_stacked + 6.0, abs=0.01
    ), _latex_visual_width(whole)

    # Both halves are substantial, so following the nesting is cheaper than adding them
    # up - which is the difference the mutant erased.
    assert inner_stacked < len(top) + len(bottom), (inner_stacked, len(top) + len(bottom))


def test_a_row_with_no_fraction_is_still_counted_straight_across(cell):
    """The estimator's other half is untouched. Stated as the property rather than as a
    number, so it says what it means: with no fraction in them, two stretches laid end to
    end measure what they measure apart."""
    left = r"384 \left(200.00\,\mathrm{GPa}\right)"
    right = r"\left(8.00 \times 10^{7}\,\mathrm{mm}^{4}\right)"

    assert _latex_visual_width(left + right) == pytest.approx(
        _latex_visual_width(left) + _latex_visual_width(right), abs=0.01
    )
    assert _NUMERIC_ROW_VISUAL_BUDGET == 64.0


def test_the_reference_beam_still_reads_the_way_it_read(cell, capsys):
    """His memoria, end to end, with the numbers unchanged."""
    page = cell(HIS_DEFLECTION, palette="kgf")
    capsys.readouterr()

    assert "0.40" in page, page
    assert r"\frac{5 q_{s} L^{4}}{384 E I}" in page, page
