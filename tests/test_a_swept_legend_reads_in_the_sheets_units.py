r"""A swept parameter's legend reads in the units the sheet declared.

`plot(M(x), x, 0, L, P=[40*kN, 80*kN])` draws one curve per value and names each in the
legend. On a sheet that declared `%eng_units kgf`, the figure comes out

    y axis   M(x) [kgf·cm]
    x axis   x [cm]
    legend   P = 40 kN            <- the one thing on the figure still in kN

#140 made a declared palette reach every quantity the figure *draws* - the x values, the
series, the curves an envelope puts underneath - and could not reach this one, because it
is not a quantity by the time the renderer sees it. The engine builds the legend entry as
**text**:

    case_label = f"{parameter_name} = {self._format_plot_quantity(sweep_value)}"

before any `RenderSettings` exists. Nothing downstream can convert a string back into
40 kN.

So the series carries the swept value itself, and the label is built where the units are
known. The formatting is one function in `unit_text` rather than two: a quantity spelled
as plain text is that module's subject, and the alternative is the engine and the renderer
each holding their own idea of it, which is the drift #138 was about.
"""

import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib.figure  # noqa: E402

import engcalc_colab.magic as magic  # noqa: E402


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


SWEEP = (
    "L := 6*m\n"
    "P := 40*kN\n"
    "M(x) = P*x*(L - x)/L\n"
    "plot(M(x), x, 0, L, P=[40*kN, 80*kN])\n"
)


def legend_of(figure) -> list[str]:
    legend = figure.axes[0].get_legend()
    labels = [text.get_text() for text in legend.get_texts()] if legend else []
    assert labels, "the sweep drew no legend"
    return labels


def test_the_legend_is_in_the_declared_units(cell, capsys):
    """The defect, on the page he would read."""
    labels = legend_of(cell(SWEEP, palette="kgf"))
    capsys.readouterr()

    assert all("kgf" in label for label in labels), labels
    assert not any("kN" in label for label in labels), labels


def test_the_legend_agrees_with_the_axis_beside_it(cell, capsys):
    """Stated as the property rather than the unit: whatever the figure says its forces
    are, the legend says the same. A contract naming `kgf` alone would pass on a figure
    whose axis had quietly moved somewhere else."""
    figure = cell(SWEEP, palette="kgf")
    capsys.readouterr()

    axis_unit = figure.axes[0].get_ylabel().split("[")[-1].rstrip("]")
    force_unit = axis_unit.split("·")[0]
    for label in legend_of(figure):
        assert force_unit in label, (force_unit, label)


def test_the_value_is_the_same_force_it_always_was(cell, capsys):
    """Converting a label is not changing a load. 40 kN is 4078.86 kgf."""
    from engcalc_colab.numeric import engineering_registry

    units = engineering_registry()
    expected = (40 * units.kN).to("kgf").magnitude

    labels = legend_of(cell(SWEEP, palette="kgf"))
    capsys.readouterr()

    first = labels[0].split("=")[-1].strip().split()[0]
    assert float(first) == pytest.approx(float(expected), rel=1e-3), labels


# --- what must not move ---------------------------------------------------------------


def test_a_sheet_with_no_palette_reads_as_it_always_did(cell):
    """`%eng_units` is opt-in, and that promise covers the legend like everything else."""
    labels = legend_of(cell(SWEEP))
    assert labels == ["P = 40 kN", "P = 80 kN"], labels


def test_a_dimension_the_palette_does_not_name_is_left_alone(cell, capsys):
    """A velocity has no entry in either palette.

    A velocity and not the angle the other palette contracts use: `deg` is dimensionless,
    and a legend entry drops the unit of a dimensionless value altogether - `t0 = 30` -
    so the angle cannot tell "left alone" from "unit lost", which is the whole question.
    """
    labels = legend_of(
        cell(
            "L := 6*m\nv0 := 2*m/s\nf(x) = v0*x/L\n"
            "plot(f(x), x, 0, L, v0=[2*m/s, 4*m/s])\n",
            palette="kgf",
        )
    )
    capsys.readouterr()
    assert all("m/s" in label for label in labels), labels


def test_a_plot_with_no_sweep_still_has_no_legend_entry_to_convert(cell, capsys):
    """The series that are not swept carry no value, and nothing tries to rebuild their
    labels."""
    figure = cell("L := 6*m\nP := 40*kN\nM(x) = P*x\nplot(M(x), x, 0, L)\n", palette="kgf")
    capsys.readouterr()
    assert "[kgf·cm]" in figure.axes[0].get_ylabel(), figure.axes[0].get_ylabel()
