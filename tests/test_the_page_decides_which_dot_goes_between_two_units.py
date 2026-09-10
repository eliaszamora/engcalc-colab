r"""`kN·m`, with the dot this project chose, whichever Pint is installed.

Pint 0.26 was released while EngCalc 0.30.3 was being cut, and it changed the separator
`~P` puts between two unit factors from U+00B7 MIDDLE DOT to U+22C5 DOT OPERATOR:

    0.25.3   format(kN*m, "~P")  ->  'kN·m'
    0.26     format(kN*m, "~P")  ->  'kN⋅m'

Nothing in EngCalc changed. Ten contracts went red on the same commit that had been
green an hour earlier - table headers, plot axis labels, characteristic values, the
summary - because every plain-text unit on every page reads through that one call. The
install line an engineer actually runs is

    %pip install -q --upgrade --no-cache-dir git+https://github.com/.../engcalc-colab.git

so the next `--upgrade` in a notebook would have changed the character under a memoria
that was already written.

**The point is not which dot is prettier.** It is that the page's spelling of a unit is
a decision this project makes - #104, #109 and #135 are all about it - and it was being
made by whichever version of a dependency happened to resolve. `product_fmt="⋅"` is
hard-coded in Pint 0.26's `PrettyFormatter` with no knob on the formatter object, so the
only place to decide it is here.

The middle dot is the one to keep: ISO 80000 writes a product of units with U+00B7, the
LaTeX path emits `\cdot` which typesets as that same glyph, and every page this project
has ever rendered uses it. A dependency's default is not a reason to change any of that.

The first two contracts below are red on *both* Pint versions, because they hand the
formatter's own output through the code path rather than relying on the installed
version to produce the wrong character. The third is red only on 0.26, which is the
version that matters and the reason this file exists.
"""

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.renderer import _table_unit_text

DOT_OPERATOR = "⋅"
MIDDLE_DOT = "·"


class _UnitSpelledPintsWay:
    """What `format(unit, "~P")` returns on Pint 0.26, without needing Pint 0.26."""

    def __init__(self, text: str):
        self._text = text

    def __format__(self, spec: str) -> str:
        return self._text

    def __str__(self) -> str:
        return self._text


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> str:
        captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    run.magics = magics
    run.objects = captured
    return run


BEAM = (
    "L := 6*m\n"
    "q := 18*kN/m\n"
    "M(x) = q*x*(L - x)/2\n"
)


def test_a_dot_operator_from_the_formatter_becomes_the_page_s_dot():
    assert _table_unit_text(_UnitSpelledPintsWay(f"kN{DOT_OPERATOR}m")) == f"kN{MIDDLE_DOT}m"


def test_every_factor_of_a_long_unit_is_converted_not_only_the_first():
    """`kN⋅m³/MPa⋅mm⁴` has two. A `replace` without a count does all of them and a
    `partition` would have done one, which is the kind of thing that shows up on the one
    page with a three-factor unit and nowhere else."""
    spelled = f"kN{DOT_OPERATOR}m³/MPa{DOT_OPERATOR}mm⁴"
    assert _table_unit_text(_UnitSpelledPintsWay(spelled)) == "kN·m³/MPa·mm⁴"
    assert DOT_OPERATOR not in _table_unit_text(_UnitSpelledPintsWay(spelled))


def test_no_page_carries_a_dot_operator(cell):
    """The end-to-end statement, across every block that prints a unit as text.

    Green on Pint 0.25.3 whatever this file does, and red on 0.26 without the fix - so
    it is the contract that speaks for the version an engineer will actually install,
    and it is why the two above exist to be red on both.
    """
    page = cell(
        BEAM
        + "table(M(x), x, 0, L, 3)\n"
        + "extrema(M(x), x, 0, L)\n"
        + "M_u = M(L/2)\n"
        + "report(M_u)\n"
        + "summary()\n"
    )
    assert DOT_OPERATOR not in page, page
    assert f"kN{MIDDLE_DOT}m" in page, page


def test_a_plot_axis_carries_the_page_s_dot_too(cell):
    """The axis label is built from the same call and is the one unit on the page that
    is drawn rather than written, so it is the one a text search over the HTML misses."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.figure

    cell(BEAM + "plot(M(x), x, 0, L)\n")
    figures = [
        obj for obj in cell.objects if isinstance(obj, matplotlib.figure.Figure)
    ]
    assert figures, [type(obj).__name__ for obj in cell.objects]

    label = figures[-1].axes[0].get_ylabel()
    assert DOT_OPERATOR not in label, label
    assert MIDDLE_DOT in label, label


def test_a_swept_parameter_s_legend_carries_the_page_s_dot(cell):
    """`plot(..., M0=[...])` labels each curve with the value swept, and that label is
    built by its own call to the formatter rather than through the table's. A sweep over
    a moment is the case that reaches it with a compound unit."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.figure

    cell(
        "L := 6*m\nM0 := 40*kN*m\n"
        "M(x) = M0*x/L\n"
        "plot(M(x), x, 0, L, M0=[40*kN*m, 80*kN*m])\n"
    )
    figures = [
        obj for obj in cell.objects if isinstance(obj, matplotlib.figure.Figure)
    ]
    assert figures, [type(obj).__name__ for obj in cell.objects]

    legend = figures[-1].axes[0].get_legend()
    labels = [text.get_text() for text in legend.get_texts()] if legend else []
    assert labels, "the sweep drew no legend"
    assert any("kN·m" in label for label in labels), labels
    assert not any(DOT_OPERATOR in label for label in labels), labels


def test_a_breakpoint_diagnostic_names_its_unit_the_page_s_way(cell, capsys):
    """The one diagnostic that prints a unit. An error message is still the page.

    Two things had to be measured rather than assumed. It is *printed*, not raised, so a
    first draft of this test read the returned HTML and passed on a page that never
    contained the message - vacuous, like the palette contract two changes ago. And the
    usual breakpoint is a span, whose unit has no product in it at all; a moment-curvature
    law is what reaches this with `40 kN·m`.
    """
    cell(
        "Mcr := 40*kN*m\nk1 := 2*1/m\nk2 := 1*1/m\n"
        "phi(M) = piecewise(k1*M/Mcr, M < Mcr, k2, M <= 80*kN*m, 0)\n"
        "d(M) = diff(phi(M), M)\nnumeric(d(Mcr))\n"
    )
    printed = capsys.readouterr().out

    assert "breakpoint" in printed, printed
    assert f"kN{MIDDLE_DOT}m" in printed, printed
    assert DOT_OPERATOR not in printed, printed


# --- what must not move ---------------------------------------------------------------


def test_a_unit_with_no_product_is_untouched():
    for text in ("m", "kN/m", "MPa", "cm²", "1/s", ""):
        assert _table_unit_text(_UnitSpelledPintsWay(text)) == text


def test_a_dimensionless_unit_still_prints_nothing():
    class _Dimensionless(_UnitSpelledPintsWay):
        def __str__(self) -> str:
            return "dimensionless"

    assert _table_unit_text(_Dimensionless("dimensionless")) == ""


def test_the_latex_path_still_writes_cdot(cell):
    r"""`~L` is a different format spec and Pint 0.26 did not change it. The Math rows
    must keep `\cdot`, which typesets as the same glyph the text rows now print."""
    page = cell(BEAM + "M_u = M(L/2)\nnumeric(M_u)\n")
    assert r"\cdot" in page, page
    assert DOT_OPERATOR not in page, page
