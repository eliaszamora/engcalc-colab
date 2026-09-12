r"""One figure annotates its points one way.

A two-curve sweep on a `kgf` sheet, both labels on the same axis:

    (300, 611829.73)
    (300, 1.22×10⁶)

The same quantity, on the same axis, one written in full and one as a power of ten.
`_compact_number` answers for one value - fixed decimals below `_FIXED_DECIMAL_CEILING`,
an exponent above it - which is the right rule for a value standing alone and the wrong
one for a figure, where the whole point of an annotation is that the reader compares it
with the curve beside it and with the axis behind it.

It is #141 asked about a figure instead of a table: *"the choice is made once per column,
from the values the column holds"*. Here the column is an axis.

**Per axis, not per figure.** A beam's abscissa runs 0 to 600 cm and reads perfectly well
in decimals while its ordinate is in the millions; one answer for the whole figure would
print `3.00×10²` for the mid-span station in order to tidy the moment. That is the same
mistake #141 measured and rejected for a table's variable column.

The decision comes from the values the figure *draws*, not from the annotated points
alone: those points lie on the curves, and matplotlib computes its own axis offset from
the same data, so the annotation and the axis it sits against cannot disagree.
"""

import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib.figure  # noqa: E402

import engcalc_colab.magic as magic  # noqa: E402

from conftest import figure_text  # noqa: E402

EXPONENT = "×10"


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str, *, palette: str = "") -> matplotlib.figure.Figure:
        captured.clear()
        if palette:
            magics.eng_units(palette)
            captured.clear()
        magics.eng("", source)
        figures = [
            obj for obj in captured if isinstance(obj, matplotlib.figure.Figure)
        ]
        assert figures, [type(obj).__name__ for obj in captured]
        return figures[-1]

    return run


def coordinates(figure) -> list[tuple[str, str]]:
    """Every `(x, y)` annotation on the axes, as the two strings the reader sees.

    An annotation typesets its power of ten now - `$1.22 \times 10^{6}$`, the page's
    own spelling - so `figure_text` reads it back. This file asks whether one axis is
    written two ways, which is the same question in either spelling.
    """
    pairs = []
    for text in figure.axes[0].texts:
        body = figure_text(text.get_text()).strip()
        if not (body.startswith("(") and body.endswith(")")):
            continue
        parts = body[1:-1].split(",")
        if len(parts) == 2:
            pairs.append((parts[0].strip(), parts[1].strip()))
    assert pairs, [t.get_text() for t in figure.axes[0].texts]
    return pairs


SWEEP = (
    "L := 6*m\n"
    "P := 40*kN\n"
    "M(x) = P*x*(L - x)/L\n"
    "plot(M(x), x, 0, L, P=[40*kN, 80*kN])\n"
)


def test_one_figure_does_not_annotate_two_ways(cell, capsys):
    """The defect: two curves, two notations, one axis."""
    pairs = coordinates(cell(SWEEP, palette="kgf"))
    capsys.readouterr()

    ordinates = [y for _, y in pairs if float(y.split(EXPONENT)[0]) != 0.0]
    assert ordinates, pairs
    with_exponent = [y for y in ordinates if EXPONENT in y]
    assert with_exponent, pairs
    assert len(with_exponent) == len(ordinates), pairs


def test_each_axis_answers_for_itself(cell, capsys):
    """The span reads well in decimals; the moment needs an exponent. One answer for the
    whole figure would print `3.00×10²` for a station in order to tidy a moment."""
    pairs = coordinates(cell(SWEEP, palette="kgf"))
    capsys.readouterr()

    assert not any(EXPONENT in x for x, _ in pairs), pairs
    assert any(EXPONENT in y for _, y in pairs), pairs


def test_a_zero_stays_a_zero(cell, capsys):
    """`0×10⁶` is not a number anybody writes."""
    pairs = coordinates(cell(SWEEP, palette="kgf"))
    capsys.readouterr()

    zeros = [y for _, y in pairs if y in {"0", "0.00"}]
    assert zeros, pairs


def test_an_envelope_answers_once_for_both_of_its_curves(cell, capsys):
    """An envelope draws a max and a min and annotates both.

    The load is 200 kN and not 40 on purpose. A first draft used 40, whose mid-span
    moment is 611 829 kgf·cm - under the ceiling, so there was no exponent anywhere and
    the test failed on a figure that was perfectly consistent. A contract about two
    notations needs values that straddle the boundary.
    """
    figure = cell(
        "L := 6*m\nP := 200*kN\nA(x) = P*x*(L - x)/L\nB(x) = 0.2*P*x*(L - x)/L\n"
        "envelope(A(x), B(x), x, 0, L)\n",
        palette="kgf",
    )
    capsys.readouterr()
    pairs = coordinates(figure)

    ordinates = [y for _, y in pairs if y not in {"0", "0.00"}]
    assert ordinates, pairs
    assert all(EXPONENT in y for y in ordinates), pairs


def test_the_dense_summary_panel_answers_the_same_way(cell, capsys):
    """Four curves or more move the annotations into a summary panel, and it is the same
    column of values under a different roof.

    Straddling on purpose: `[40, 80, 150, 200] kN` gives `611829.73` beside `1.22×10⁶`,
    while a sweep whose loads are all large is consistent by accident and proves nothing.
    """
    figure = cell(
        "L := 6*m\nP := 40*kN\nM(x) = P*x*(L - x)/L\n"
        "plot(M(x), x, 0, L, P=[40*kN, 80*kN, 150*kN, 200*kN])\n",
        palette="kgf",
    )
    capsys.readouterr()

    panels = [
        axes
        for axes in figure.axes
        if axes.get_gid() == "engcalc-characteristic-summary"
    ]
    assert panels, [axes.get_gid() for axes in figure.axes]

    values = [
        figure_text(text.get_text())
        for text in panels[0].texts
        if text.get_text() and text.get_text().lstrip('$')[0].isdigit()
    ]
    written = [value for value in values if value not in {"0", "0.00"}]
    assert written, values
    assert all(EXPONENT in value for value in written), values


# --- what must not move ---------------------------------------------------------------


def test_a_figure_that_reads_well_in_decimals_keeps_them(cell):
    """The same sweep with no palette. Nothing is near a million, and the annotations
    must not acquire exponents because a rule exists."""
    pairs = coordinates(cell(SWEEP))

    assert not any(EXPONENT in y for _, y in pairs), pairs
    assert not any(EXPONENT in x for x, _ in pairs), pairs


def test_the_value_is_the_same_number_it_was(cell, capsys):
    """Choosing a notation is not choosing a different moment. `P·L/4` at mid-span, for
    the larger of the two swept loads."""
    from engcalc_colab.numeric import engineering_registry

    units = engineering_registry()
    expected = float(((80 * units.kN) * (6 * units.m) / 4).to("kgf*cm").magnitude)

    pairs = coordinates(cell(SWEEP, palette="kgf"))
    capsys.readouterr()

    values = []
    for _, y in pairs:
        if EXPONENT in y:
            mantissa, _, power = y.partition(EXPONENT)
            values.append(
                float(mantissa)
                * 10.0 ** int(power.translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")))
            )
        else:
            values.append(float(y))

    assert max(values) == pytest.approx(expected, rel=5e-3), pairs
