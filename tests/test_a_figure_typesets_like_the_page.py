r"""A figure writes its mathematics the way the page around it does.

The beam memoria rendered with the engineer's own palette, figure and table one below
the other:

    figure   Comparison [kgf·cm]      1e6 in the corner      (300, 1.97×10⁶)
    table    U1(x) [kgf · cm]                                1.87 × 10⁶

Three spellings of one thing on one page. `1e6` is the worst of them: it is programmer
notation, it appears nowhere else in the memoria, and it sits two centimetres above an
annotation on the same axis that writes the same power of ten as `1.97×10⁶`. It is #152
again - *one figure is annotated one way* - one level down, between the annotation and
the axis it hangs on.

The page's spellings already exist and are used by every block that typesets:
`_latex_unit_text` writes `\mathrm{kgf} \cdot \mathrm{cm}`, `_scientific_latex` writes
`1.97 \times 10^{6}`. Matplotlib reads that same LaTeX subset through mathtext, so a
figure can be handed the page's own strings rather than a second spelling of them - the
drift #135 and #138 were about.

**The name does not typeset and the unit does**, which is not an oversight but the
decision `_table_header` already documents: a unit comes from Pint and is mathematics,
while `M(x)`, `Comparison`, `q_s(x)` is the text the engineer typed, and turning that
into LaTeX means parsing it. The axis label is now built exactly the way the table header
beside it is.

**One deliberate difference from the page: a quotient is written inline.** Pint's `~L`
puts `kgf/cm` in a `\frac`, which the page renders at body size and an axis label renders
at about six points on a rotated y label - measured, and worse than the plain text it
replaces. Products, powers and the exponent all improve; the stacked fraction was the one
that did not, so that one is flattened.

The face does not change. Matplotlib's default `mathtext.fontset` is `dejavusans`, so
`\mathrm{kgf}` is set in the same sans the ticks, the title and the legend use - measured
against `cm`, `stix`, `stixsans` and `dejavuserif`, which all put a serif unit beside a
sans word inside one label. An earlier note in this project said mathtext meant serif
labels; it does not.
"""

import re

import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib.figure  # noqa: E402
from matplotlib.mathtext import MathTextParser  # noqa: E402

import engcalc_colab.magic as magic  # noqa: E402
from engcalc_colab.numeric import engineering_registry  # noqa: E402
from engcalc_colab.plotting import _unit_mathtext  # noqa: E402
from engcalc_colab.renderer import PALETTES  # noqa: E402
from engcalc_colab.unit_text import unit_text  # noqa: E402

from conftest import figure_text  # noqa: E402


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str, *, palette: str = "") -> matplotlib.figure.Figure:
        # A fresh magic per sheet. One test below renders the same sheet with a palette
        # and without, and a shared `EngMagics` carries the declaration into the second
        # run - it read `kgf·cm` where the sheet declares nothing at all.
        magics = magic.EngMagics()
        captured.clear()
        if palette:
            magics.eng_units(palette)
            captured.clear()
        magics.eng("", source)
        figures = [
            obj for obj in captured if isinstance(obj, matplotlib.figure.Figure)
        ]
        assert figures, [type(obj).__name__ for obj in captured]
        run.page = "".join(getattr(obj, "data", "") for obj in captured)
        figures[-1].canvas.draw()
        return figures[-1]

    run.page = ""
    return run


# 200 kN and not 40 on purpose: a mid-span moment of 611 829 kgf·cm draws no axis offset
# at all, so the defect this file is about is not on the figure to be seen.
MOMENT = (
    "L := 6*m\n"
    "P := 200*kN\n"
    "M(x) = P*x*(L - x)/L\n"
    "plot(M(x), x, 0, L)\n"
)

DISTRIBUTED = (
    "L := 6*m\n"
    "q := 30*kgf/cm\n"
    "f(x) = q*x/L\n"
    "plot(f(x), x, 0, L)\n"
)


def annotations(figure) -> list[str]:
    texts = [
        text.get_text().strip()
        for text in figure.axes[0].texts
        if text.get_text().strip().startswith("(")
    ]
    assert texts, [text.get_text() for text in figure.axes[0].texts]
    return texts


def offset_of(figure) -> str:
    return figure.axes[0].yaxis.get_offset_text().get_text()


def test_the_axis_does_not_say_1e6(cell, capsys):
    """The defect, on the page he reads. `1e6` is not how this memoria writes a million
    anywhere else on it."""
    figure = cell(MOMENT, palette="kgf")
    capsys.readouterr()

    offset = offset_of(figure)
    assert offset, "this sheet is supposed to draw an axis offset"
    assert "e6" not in offset, offset
    assert figure_text(offset) == "×10⁶", (offset, figure_text(offset))


def test_the_offset_and_the_annotation_are_one_notation(cell, capsys):
    """The property joining them, rather than two separate spellings that happen to agree
    today. They sit on the same axis, two centimetres apart."""
    figure = cell(MOMENT, palette="kgf")
    capsys.readouterr()

    written = [figure_text(text) for text in annotations(figure)]
    powers = [text for text in written if "10" in text.split(",")[-1]]
    assert powers, written
    assert all("×10" in text for text in powers), written
    assert "×10" in figure_text(offset_of(figure)), offset_of(figure)


def test_a_compound_unit_on_an_axis_is_typeset(cell, capsys):
    """`kgf·cm` becomes `$\\mathrm{kgf} \\cdot \\mathrm{cm}$`, and still reads `kgf·cm`."""
    figure = cell(MOMENT, palette="kgf")
    capsys.readouterr()

    label = figure.axes[0].get_ylabel()
    assert "$" in label, label
    assert r"\mathrm{kgf}" in label and r"\cdot" in label, label
    assert figure_text(label) == "M(x) [kgf·cm]", figure_text(label)


def test_the_figure_spells_the_unit_the_way_the_table_beside_it_does(cell, capsys):
    """The strong form: not "both read kgf·cm" - they did before this change too - but
    that the axis label and the table header on the same page carry the *same LaTeX*,
    because both are built from `_latex_unit_text`."""
    figure = cell(MOMENT + "table(M(x), x, 0, L, 5)\n", palette="kgf")
    capsys.readouterr()

    axis_maths = re.findall(r"\$(.*?)\$", figure.axes[0].get_ylabel())
    assert axis_maths, figure.axes[0].get_ylabel()

    headers = re.findall(r"<th[^>]*>(.*?)</th>", cell.page, re.S)
    header_maths = [
        maths for header in headers for maths in re.findall(r"\$(.*?)\$", header)
    ]
    assert header_maths, headers

    assert axis_maths[0] in header_maths, (axis_maths, header_maths)


def test_an_annotated_power_of_ten_is_typeset(cell, capsys):
    """The annotation's exponent, in the page's `\\times 10^{6}` rather than the Unicode
    superscript an HTML block needs. Measured side by side: the Unicode `⁶` sits low and
    small against a mathtext superscript, and the axis offset next to it is mathtext."""
    figure = cell(MOMENT, palette="kgf")
    capsys.readouterr()

    written = [text for text in annotations(figure) if "10" in text]
    assert written, annotations(figure)
    assert all(r"\times" in text for text in written), written
    assert not any("×" in text for text in written), written


def test_a_quotient_is_written_inline_on_a_figure(cell, capsys):
    """The one deliberate difference from the page. `\\frac{\\mathrm{kgf}}{\\mathrm{cm}}`
    on a rotated y label renders its two halves at about six points."""
    figure = cell(DISTRIBUTED, palette="kgf")
    capsys.readouterr()

    label = figure.axes[0].get_ylabel()
    assert "$" in label, label
    assert r"\frac" not in label, label
    assert figure_text(label) == "f(x) [kgf/cm]", figure_text(label)


DENSE = (
    "L := 6*m\n"
    "P := 200*kN\n"
    "M(x) = P*x*(L - x)/L\n"
    "plot(M(x), x, 0, L, P=[200*kN, 400*kN, 600*kN, 800*kN])\n"
)


def group_headers(figure):
    panels = [
        axes for axes in figure.axes if axes.get_gid() == "engcalc-characteristic-summary"
    ]
    assert panels, [axes.get_gid() for axes in figure.axes]
    headers = [
        text
        for text in panels[0].texts
        if text.get_gid() == "engcalc-summary-group-header"
    ]
    assert headers, [text.get_gid() for text in panels[0].texts]
    return headers


def test_a_bold_label_is_bold_all_the_way_across(cell, capsys):
    """The one label on a figure whose mathematics sits inside bold text: the dense
    summary panel's `x = 300 cm`.

    Mathtext sets a formula in its own font and ignores the weight of the text around it,
    so the first draft of this change put a light `cm` beside a semibold `300` - one
    phrase in two weights, visible at the panel's own 8.2 pt.
    """
    figure = cell(DENSE, palette="kgf")
    capsys.readouterr()

    headers = group_headers(figure)
    for header in headers:
        assert header.get_fontweight() in {"semibold", 600}, header.get_fontweight()
        assert r"\mathbf" in header.get_text(), header.get_text()
        assert r"\mathrm" not in header.get_text(), header.get_text()

    assert figure_text(headers[0].get_text()) == "x = 0 cm", headers[0].get_text()


def test_the_number_in_a_bold_label_is_bold_too(cell, capsys):
    """A twenty-kilometre span in centimetres, which is the shortest sheet that puts a
    power of ten in that header - and the case that showed a per-unit `bold` flag was the
    wrong shape: the value is typeset by a different function and arrived light beside a
    bold unit, the same defect one word to the left."""
    figure = cell(DENSE.replace("L := 6*m", "L := 20000*m"), palette="kgf")
    capsys.readouterr()

    written = [text.get_text() for text in group_headers(figure)]
    powers = [text for text in written if r"\times" in text]
    assert powers, written
    for header in powers:
        assert r"\mathbf{" in header.split(r"\times")[0], header
        assert figure_text(header).startswith("x = 1"), figure_text(header)


def test_a_label_that_is_not_bold_asks_for_no_bold_unit(cell, capsys):
    """The other side of it. An axis label is regular, and `\\mathbf` there would be the
    same mismatch pointing the other way."""
    figure = cell(MOMENT, palette="kgf")
    capsys.readouterr()

    label = figure.axes[0].get_ylabel()
    assert r"\mathrm" in label, label
    assert r"\mathbf" not in label, label


def test_every_unit_a_palette_declares_can_be_drawn(cell):
    """Mathtext is a LaTeX subset, and a unit it cannot parse raises at draw time and
    kills the cell where today there is a label. Every unit either palette names, plus
    the ones a sheet reaches without declaring."""
    units = engineering_registry()
    names = {
        spelling for palette in PALETTES.values() for spelling in palette.values()
    } | {"kN * m", "N * mm", "tonf * m", "mm ** 4", "m / s ** 2", "kg / m ** 3", "deg"}

    parser = MathTextParser("agg")
    for name in sorted(names):
        unit = (1 * units(name)).units
        maths = _unit_mathtext(unit)
        if not maths:
            continue
        parser.parse(maths)


def test_a_unit_mathtext_cannot_draw_falls_back_to_plain_text():
    """The guard for the unit nobody enumerated. Thirty-eight were measured and every one
    parses, which is the reason to expect this never fires and no reason to let a figure
    die if it does."""

    class Unparseable:
        def __format__(self, spec):
            return "\\frac{" if "L" in spec else "weird"

        def __str__(self):
            return "weird"

    assert _unit_mathtext(Unparseable()) == "weird"


# --- what must not move ---------------------------------------------------------------


def test_the_reader_reads_the_same_unit_he_read_before(cell, capsys):
    """Typesetting a unit is not changing it. Every axis, read back, says exactly what
    the plain-text side of the project spells."""
    units = engineering_registry()
    for sheet, palette, expected in (
        (MOMENT, "kgf", (1 * units("kgf * cm")).units),
        (MOMENT, "", (1 * units("kN * m")).units),
        (DISTRIBUTED, "kgf", (1 * units("kgf / cm")).units),
    ):
        figure = cell(sheet, palette=palette)
        capsys.readouterr()
        label = figure_text(figure.axes[0].get_ylabel())
        assert label.endswith(f"[{unit_text(expected)}]"), (label, unit_text(expected))


def test_the_title_is_the_name_the_sheet_typed(cell, capsys):
    """The unit typesets and the name does not - `_table_header`'s decision, applied to
    the figure so the two agree. A title is not mathematics to be parsed."""
    figure = cell(MOMENT, palette="kgf")
    capsys.readouterr()

    assert figure.axes[0].get_title() == "M(x)", figure.axes[0].get_title()


def test_a_dimensionless_axis_carries_no_brackets(cell, capsys):
    """`""` for a dimensionless unit is what every caller wants, and wrapping it would
    put an empty `$[]$` on the axis."""
    figure = cell(
        "L := 6*m\nk := 2\nf(x) = k*x/L\nplot(f(x), x, 0, L)\n", palette="kgf"
    )
    capsys.readouterr()

    assert "[" not in figure.axes[0].get_ylabel(), figure.axes[0].get_ylabel()


def test_the_abscissa_still_reads_in_decimals(cell, capsys):
    """#152's rule is per axis and this change does not reach it: the span reads 0 to 600
    and must not acquire an exponent because the ordinate has one."""
    figure = cell(MOMENT, palette="kgf")
    capsys.readouterr()

    abscissae = [figure_text(text).split(",")[0].lstrip("(") for text in annotations(figure)]
    assert abscissae, annotations(figure)
    assert not any("10" in value for value in abscissae), abscissae


def test_the_abscissa_takes_no_offset_it_never_had(cell, capsys):
    """This change spells an offset; it does not decide when one appears. That stays
    matplotlib's call from the data, and forcing scientific notation on every axis in
    order to reach the spelling would put a `×10²` under a beam six metres long."""
    figure = cell(MOMENT, palette="kgf")
    capsys.readouterr()

    assert figure.axes[0].xaxis.get_offset_text().get_text() == "", (
        figure.axes[0].xaxis.get_offset_text().get_text()
    )


def test_a_zero_stays_a_zero(cell, capsys):
    """`$0 \\times 10^{0}$` is not a number anybody writes, and neither was `0×10⁶`."""
    figure = cell(MOMENT, palette="kgf")
    capsys.readouterr()

    ordinates = [figure_text(text).rstrip(")").split(",")[-1].strip() for text in annotations(figure)]
    assert "0" in ordinates, ordinates


def test_the_value_is_the_same_moment_it_was(cell, capsys):
    """Typesetting a number is not changing it. `P·L/4` at mid-span."""
    units = engineering_registry()
    expected = float(((200 * units.kN) * (6 * units.m) / 4).to("kgf*cm").magnitude)

    figure = cell(MOMENT, palette="kgf")
    capsys.readouterr()

    values = []
    for text in annotations(figure):
        written = figure_text(text).rstrip(")").split(",")[-1].strip()
        if "×10" in written:
            mantissa, _, power = written.partition("×10")
            values.append(
                float(mantissa)
                * 10.0 ** int(power.translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")))
            )
        else:
            values.append(float(written))

    assert max(values) == pytest.approx(expected, rel=5e-3), annotations(figure)
