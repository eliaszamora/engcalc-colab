r"""A swept legend writes the number the page writes for the same quantity.

From his own notebook, one figure and the rows above it:

    the page     P_2  =  20394.32 kgf
    the legend   P2   =  20394.3 kgf

Same load, same page, two spellings - which is #135 for the fourth time, now between a
figure's legend and the text beside it.

It is not only the converted case. With no palette at all the page writes `200.00 kN` and
the legend writes `200 kN`; the palette only made the disagreement wide enough to notice.

**Where the `%g` came from.** #151 moved the legend into the renderer so a declared
palette could reach it, and chose `%g` deliberately: *"a swept parameter is a value the
engineer typed - `P=[40*kN, 80*kN]` - and `40` is what he wrote."* True of the sheet, and
not true of the page, which writes `200.00 kN` for that same typed value in the row above
the figure. And once a palette converts it, `20394.3` is not what anybody wrote.

So the legend takes the page's precision, from the same `RenderSettings` every other
number on the page takes it from - `%eng_config precision=3` moves them together.

The subscript stays as the sheet typed it: `P2`, not `P_2`. That is not an oversight but
the rule `_table_header` documents and #154 applied to the axis - the unit is mathematics
and the name is the engineer's text - so the legend agrees with the axis label beside it,
which is the comparison a reader of the figure actually makes.
"""

import re

import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib.figure  # noqa: E402

import engcalc_colab.magic as magic  # noqa: E402


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str, *, palette: str = "", config: str = ""):
        magics = magic.EngMagics()
        captured.clear()
        if config:
            magics.eng_config(config)
            captured.clear()
        if palette:
            magics.eng_units(palette)
            captured.clear()
        magics.eng("", source)
        figures = [
            obj for obj in captured if isinstance(obj, matplotlib.figure.Figure)
        ]
        page = "".join(str(getattr(obj, "data", "")) for obj in captured)
        return page, figures

    return run


SWEEP = (
    "L := 6*m\n"
    "P2 := 200*kN\n"
    "Md(x) = P2*x*(L - x)/L\n"
    "report(P2)\n"
    "plot(Md(x), x, 0, L, P2=[200*kN, 400*kN])\n"
)


def legend_of(figures) -> list[str]:
    assert figures, "the sweep drew no figure"
    legend = figures[-1].axes[0].get_legend()
    labels = [text.get_text() for text in legend.get_texts()] if legend else []
    assert labels, "the sweep drew no legend"
    return labels


def on_the_page(page: str) -> str:
    written = re.findall(r"P_\{2\} & = & \\displaystyle ([\d.]+)", page)
    assert written, page[:400]
    return written[0]


def test_the_legend_and_the_page_write_one_number(cell, capsys):
    """The defect, on his own figure and the row above it."""
    page, figures = cell(SWEEP, palette="kgf")
    capsys.readouterr()

    assert any(on_the_page(page) in label for label in legend_of(figures)), (
        on_the_page(page),
        legend_of(figures),
    )


def test_they_agree_with_no_palette_too(cell):
    """The palette made it wide enough to notice; it was never only the converted case.
    The page writes `200.00 kN` and the legend wrote `200 kN`."""
    page, figures = cell(SWEEP)

    assert on_the_page(page) == "200.00", on_the_page(page)
    assert any("200.00" in label for label in legend_of(figures)), legend_of(figures)


def test_the_precision_the_sheet_asked_for_reaches_the_legend(cell, capsys):
    """The strong form. A contract naming `200.00` would pass on a legend that had
    hard-coded two decimals; this asks whether the legend takes its precision from the
    same place every other number on the page takes it from."""
    page, figures = cell(SWEEP, config="precision=3")
    capsys.readouterr()

    assert on_the_page(page) == "200.000", on_the_page(page)
    assert any("200.000" in label for label in legend_of(figures)), legend_of(figures)


def test_the_value_is_the_same_load_it_was(cell, capsys):
    """Spelling a number is not changing a load. 200 kN is 20394.32 kgf."""
    from engcalc_colab.numeric import engineering_registry

    units = engineering_registry()
    expected = float((200 * units.kN).to("kgf").magnitude)

    _, figures = cell(SWEEP, palette="kgf")
    capsys.readouterr()

    first = legend_of(figures)[0].split("=")[-1].strip().split()[0]
    assert float(first) == pytest.approx(expected, rel=1e-4), legend_of(figures)


# --- what must not move ---------------------------------------------------------------


def test_the_legend_is_still_in_the_declared_units(cell, capsys):
    """#151's subject, untouched: the unit still follows the palette."""
    _, figures = cell(SWEEP, palette="kgf")
    capsys.readouterr()

    labels = legend_of(figures)
    assert all("kgf" in label for label in labels), labels
    assert not any("kN" in label for label in labels), labels


def test_the_name_is_the_one_the_sheet_typed(cell, capsys):
    """`P2`, not `P_2`. The unit is mathematics and the name is the engineer's text -
    `_table_header`'s rule, which #154 applied to the axis label the legend sits beside."""
    _, figures = cell(SWEEP, palette="kgf")
    capsys.readouterr()

    assert all(label.startswith("P2 = ") for label in legend_of(figures)), legend_of(
        figures
    )


def test_a_dimension_the_palette_does_not_name_is_left_alone(cell, capsys):
    """A velocity has no entry in either palette, and the number still follows the
    page."""
    _, figures = cell(
        "L := 6*m\nv0 := 2*m/s\nf(x) = v0*x/L\n"
        "plot(f(x), x, 0, L, v0=[2*m/s, 4*m/s])\n",
        palette="kgf",
    )
    capsys.readouterr()

    labels = legend_of(figures)
    assert all("m/s" in label for label in labels), labels
    assert labels[0].startswith("v0 = 2.00 "), labels


def test_a_dimensionless_sweep_keeps_its_number_and_drops_the_unit(cell):
    """A dimensionless value has no unit to write, and a legend that printed an empty one
    would read `k = 2.00 `."""
    _, figures = cell(
        "L := 6*m\nk := 2\nf(x) = k*x/L\nplot(f(x), x, 0, L, k=[2, 4])\n"
    )

    labels = legend_of(figures)
    assert labels == ["k = 2.00", "k = 4.00"], labels


def test_a_plot_with_no_sweep_has_no_legend_entry_to_write(cell, capsys):
    """The series that are not swept carry no value, and nothing tries to rebuild their
    labels."""
    _, figures = cell("L := 6*m\nP := 40*kN\nM(x) = P*x\nplot(M(x), x, 0, L)\n", palette="kgf")
    capsys.readouterr()

    from conftest import figure_text

    label = figure_text(figures[-1].axes[0].get_ylabel())
    assert "[kgf·cm]" in label, label
