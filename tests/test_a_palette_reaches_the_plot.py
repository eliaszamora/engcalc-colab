r"""A sheet that declares its units declares them for the figure too.

The engineer's screenshot of the beam memoria on the `kgf` palette: the working reads
`kgf·cm`, the table heads its columns `[cm]` and `[kgf·cm]`, the extrema block says
`1.87×10⁶ kgf·cm` - and the one figure on the page is labelled

    Comparison [kN·m]        x [m]        (4.47, 216.9)

Measured rather than read off the picture: the figure comes out **byte-identical with and
without** `%eng_units kgf`. The plotting path never sees a `RenderSettings` at all, so the
palette does not reach it, and `magic.py` has `self._settings()` on the very line that
renders the plot without passing it.

A memoria that says `cm` in its text and `m` on its axis makes the reader convert before
they can read their own drawing, and it is the same defect as `183.60 m·kN` two lines from
`183.60 kN·m` - one page, one quantity, two answers. #135 closed that for the text.

Four places carry a quantity into a figure and all four have to agree: the x values, each
series' y values, the characteristic points annotated on the curves, and the legend of a
swept parameter. Converting only the axis label would put `[kgf·cm]` above numbers still
drawn in kN·m, which is worse than not converting at all.

The palette only, not the whole display rule. `%eng_units` shipped as opt-in - "a sheet
that declares no palette renders as it did in 0.29.3" - and that promise covers the figure
exactly as it covers the text.
"""

import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib.figure  # noqa: E402

import engcalc_colab.magic as magic  # noqa: E402

BEAM = (
    "L := 6*m\n"
    "qD := 18*kN/m\n"
    "qL := 12*kN/m\n"
    "M_D(x) = qD*x*(L - x)/2\n"
    "M_L(x) = qL*x*(L - x)/2\n"
)


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str, *, palette: str = "") -> str:
        captured.clear()
        if palette:
            magics.eng_units(palette)
            captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    run.objects = captured
    run.magics = magics
    return run


def _figure(cell) -> matplotlib.figure.Figure:
    figures = [
        obj for obj in cell.objects if isinstance(obj, matplotlib.figure.Figure)
    ]
    assert figures, [type(obj).__name__ for obj in cell.objects]
    return figures[-1]


def test_a_declared_palette_labels_the_axes(cell, capsys):
    cell(BEAM + "M(x) = M_D(x) + M_L(x)\nplot(M(x), x, 0, L)\n", palette="kgf")
    capsys.readouterr()
    axis = _figure(cell).axes[0]

    assert "[kgf·cm]" in axis.get_ylabel(), axis.get_ylabel()
    assert "[cm]" in axis.get_xlabel(), axis.get_xlabel()


def test_the_curve_is_drawn_in_the_unit_its_axis_names(cell, capsys):
    """The half that matters more than the label. A span of six metres is six hundred on
    a `cm` axis, and a moment of 183.6 kN·m is 1.87e6 kgf·cm - if the numbers stay in the
    old unit under a relabelled axis the figure is simply wrong."""
    cell(BEAM + "M(x) = M_D(x) + M_L(x)\nplot(M(x), x, 0, L)\n", palette="kgf")
    capsys.readouterr()
    axis = _figure(cell).axes[0]

    # Derived from the sheet, not pasted from what the code printed: the span is 6 m and
    # the load is 18 + 12 = 30 kN/m, so the mid-span moment is qL²/8 and the only question
    # this test asks is whether the figure is drawn in the palette's units.
    from engcalc_colab.numeric import engineering_registry

    units = engineering_registry()
    span = 6 * units.m
    moment = (30 * units.kN / units.m) * span**2 / 8

    x_data, y_data = axis.lines[0].get_xdata(), axis.lines[0].get_ydata()
    assert max(x_data) == pytest.approx(
        float(span.to("cm").magnitude), rel=1e-9
    ), max(x_data)
    assert max(abs(y_data)) == pytest.approx(
        float(moment.to("kgf*cm").magnitude), rel=1e-9
    ), max(abs(y_data))


def test_an_annotated_point_agrees_with_the_axes_it_sits_on(cell, capsys):
    """`(4.47, 216.9)` beside a `cm` axis is not a coordinate, it is a riddle."""
    cell(
        BEAM
        + "case D = M_D(x)\ncase Lv = M_L(x)\n"
        + "combo U1 = 1.2*D + 1.6*Lv\ncombo U2 = 1.2*D + 1.2*Lv\n"
        + "envelope(U1(x), U2(x), x, 0, L)\n",
        palette="kgf",
    )
    capsys.readouterr()
    axis = _figure(cell).axes[0]

    annotations = [text.get_text() for text in axis.texts]
    assert annotations, "the envelope annotated nothing"

    # A first draft asserted only that each x sat inside `[0, 600]`, which `4.47` also
    # does - vacuous, and it passed before the fix. The discriminating facts are of
    # scale: on this palette the span is six hundred centimetres and the moment is of
    # order 10^6 kgf·cm, where in metres and kN·m every annotation is single digits and
    # hundreds.
    abscissas = []
    for text in annotations:
        first = text.strip("()").split(",")[0]
        try:
            abscissas.append(float(first))
        except ValueError:
            continue
    assert abscissas, annotations
    assert max(abscissas) > 6.0, annotations

    # The ordinate is written as a power of ten once it passes a million, which is the
    # page's own rule and the reason this parses the text rather than a float.
    assert any("×10⁶" in text for text in annotations), annotations


# A swept parameter's legend still reads `P = 40 kN` on a kgf sheet, and it is left for
# its own change. Its cause is a different one: that label is built as *text* in the
# engine - `f"{parameter_name} = {self._format_plot_quantity(sweep_value)}"` - before any
# `RenderSettings` exists, and the same string is then stamped onto the characteristics
# as their `source_label`. Nothing here can convert it, because by the time a figure is
# rendered the quantity is gone. Fixing it means carrying the swept value to the renderer
# rather than its rendering, which is a model change and a separate argument.


# --- what must not move ---------------------------------------------------------------


def test_a_sheet_with_no_palette_draws_exactly_what_it_always_did(cell, capsys):
    """`%eng_units` shipped opt-in, and that promise covers the figure. Byte-for-byte on
    the numbers, not just the labels."""
    sheet = BEAM + "M(x) = M_D(x) + M_L(x)\nplot(M(x), x, 0, L)\n"

    cell(sheet)
    capsys.readouterr()
    axis = _figure(cell).axes[0]

    assert "[kN·m]" in axis.get_ylabel(), axis.get_ylabel()
    assert "[m]" in axis.get_xlabel(), axis.get_xlabel()
    assert max(axis.lines[0].get_xdata()) == pytest.approx(6.0), max(
        axis.lines[0].get_xdata()
    )


def test_a_dimension_the_palette_does_not_cover_is_left_alone(cell, capsys):
    """A velocity has no entry in either palette, and inventing one for every dimension
    anybody might reach is how a palette turns back into the rules it replaced.

    An angle, and one whose base form differs, which is the difference between a contract
    and a decoration. A first draft used `m/s`, and a mutant converting an unnamed
    dimension to *base* units survived it - because the base units of `m/s` are `m/s`.
    The sheet has to be written in a unit that is not already its own base for "left
    alone" to mean anything: `30 deg` is `0.5236 rad` in base units, and no palette names
    that dimension.

    Written as `theta0 := 30*deg` and then used by name, because `deg` is a numeric name
    and not one the symbolic side knows - `t(x) = 30*deg*x/L` cannot be defined at all.
    """
    cell(
        "L := 6*m\ntheta0 := 30*deg\nt(x) = theta0*x/L\nplot(t(x), x, 0, L)\n",
        palette="kgf",
    )
    capsys.readouterr()
    axis = _figure(cell).axes[0]

    assert "deg" in axis.get_ylabel(), axis.get_ylabel()
    assert max(axis.lines[0].get_ydata()) == pytest.approx(30.0), max(
        axis.lines[0].get_ydata()
    )


def test_the_curves_under_an_envelope_move_with_the_ones_above_them(cell, capsys):
    """An envelope draws the two source responses faintly beneath the max/min pair.

    Leaving them in the old unit puts four curves on one axis at ten-thousand-to-one
    scale: two peaking at 184 and 217, two at 2.2 million. They do not look wrong, they
    look absent - flat against the axis - which is why a mutant that dropped them
    survived everything until this.
    """
    cell(
        BEAM
        + "P := 40*kN\nM_P(x) = P*x/2\n"
        + "case D = M_D(x)\ncase Lv = M_L(x)\ncase Mo = M_P(x)\n"
        + "combo U1 = 1.2*D + 1.6*Lv\ncombo U2 = 1.2*D + 1.6*Mo\n"
        + "envelope(U1(x), U2(x), x, 0, L)\n",
        palette="kgf",
    )
    capsys.readouterr()
    axis = _figure(cell).axes[0]

    peaks = [
        max(abs(value) for value in line.get_ydata())
        for line in axis.lines
        if len(line.get_ydata())
    ]
    drawn = [peak for peak in peaks if peak > 0]
    assert len(drawn) >= 4, peaks
    # Every curve on one axis is in one unit, so the largest and smallest peaks are
    # within an order of magnitude of each other rather than four.
    assert max(drawn) / min(drawn) < 10.0, sorted(drawn)
