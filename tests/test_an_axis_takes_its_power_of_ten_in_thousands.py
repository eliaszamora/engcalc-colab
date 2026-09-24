r"""An axis of large values takes a power of ten in thousands, as a matrix does.

The portal frame's two moment diagrams, one unit, two spellings:

    beam      M_b(x) [kgf·cm]    ×10⁶ in the corner, ticks 0.25 ... 1.00
    columns   M(y)   [kgf·cm]    no factor, ticks 200000 ... 800000

Matplotlib decided both: it takes an offset out only once the axis reaches a million,
and it takes whatever power that is. The beam's 687 277 kgf·cm drew an axis to 1 000 000
and read in fractions of a million; the columns' 519 596 stayed under it and read in six
digits. He liked neither (*"no me gusta que sea con marcas de 0 a 1 ... tampoco sería lo
ideal que fueran tan grandes como 200000"*).

The rule is the matrix's, which he chose to keep: a power of ten that is a multiple of
three, sized on the largest value drawn, so the ticks read between 1 and 1000. It is taken
only when a value would otherwise run to five digits - a shear of 6948 kgf reads well as
it is. Where it is taken, it is written where matplotlib writes it, in the corner, `×10³`
(his option A, chosen on 2026-09-24 over putting it into the unit of the label).
Annotations keep the numbers the page writes.
"""

import re

import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib.figure  # noqa: E402

import engcalc_colab.magic as magic  # noqa: E402

from conftest import figure_text  # noqa: E402


@pytest.fixture
def figures(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str, *, palette: str = "kgf") -> list[matplotlib.figure.Figure]:
        magics = magic.EngMagics()
        if palette:
            magics.eng_units(palette)
        captured.clear()
        magics.eng("", source)
        drawn = [obj for obj in captured if isinstance(obj, matplotlib.figure.Figure)]
        assert drawn, [type(obj).__name__ for obj in captured]
        for figure in drawn:
            figure.canvas.draw()
        return drawn

    return run


BEAM = (
    "L := 6*m\nw := 2000*kgf/m\nV_2 := 5051.98*kgf\nM_2 := -49214.04*kgf*cm\n"
    "M_b(x) = -M_2 + V_2*x - w*x^2/2\nV_b(x) = V_2 - w*x\n"
    "plot(M_b(x), x, 0, L)\nplot(V_b(x), x, 0, L)\n"
)

COLUMNS = (
    "h := 4*m\nV_1 := 619.54*kgf\nM_1 := 198601.90*kgf*cm\n"
    "V_4 := 2380.46*kgf\nM_4 := 432587.86*kgf*cm\n"
    "M_c1(y) = -M_1 + V_1*y\nM_c4(y) = -M_4 + V_4*y\n"
    "plot(M_c1(y), M_c4(y), y, 0, h)\n"
)


def offset_of(figure) -> str:
    return figure_text(figure.axes[0].yaxis.get_offset_text().get_text())


def ticks_of(figure) -> list[float]:
    axis = figure.axes[0]
    low, high = sorted(axis.get_ylim())
    values = []
    for label in axis.get_yticklabels():
        text = figure_text(label.get_text()).replace("−", "-")
        if text and low <= label.get_position()[1] <= high:
            values.append(float(text))
    assert values, [label.get_text() for label in axis.get_yticklabels()]
    return values


def test_the_beam_moment_reads_in_thousands(figures):
    moment, _shear = figures(BEAM)
    assert offset_of(moment) == "×10³", offset_of(moment)
    ticks = ticks_of(moment)
    assert max(abs(t) for t in ticks) >= 100, ticks
    assert all(abs(t) <= 1000 for t in ticks), ticks


def test_the_column_moments_read_in_thousands_too(figures):
    (moment,) = figures(COLUMNS)
    assert offset_of(moment) == "×10³", offset_of(moment)
    ticks = ticks_of(moment)
    assert max(abs(t) for t in ticks) >= 100, ticks
    assert all(abs(t) <= 1000 for t in ticks), ticks


def test_a_shear_of_four_digits_takes_no_factor(figures):
    _moment, shear = figures(BEAM)
    assert offset_of(shear) == "", offset_of(shear)
    assert max(abs(t) for t in ticks_of(shear)) >= 1000, ticks_of(shear)


def test_the_annotations_keep_the_page_s_numbers(figures):
    moment, _shear = figures(BEAM)
    texts = [figure_text(t.get_text()) for t in moment.axes[0].texts]
    # The full number, as the page writes it, not the tick's thousands.
    assert any(re.fullmatch(r"\(252\.6, 6872\d\d\.\d\d\)", text) for text in texts), texts


def test_a_moment_in_the_millions_still_reads_in_millions(figures):
    (moment,) = figures("L := 6*m\nP := 200*kN\nM(x) = P*x*(L - x)/L\nplot(M(x), x, 0, L)\n")
    assert offset_of(moment) == "×10⁶", offset_of(moment)
    assert all(abs(t) < 1000 for t in ticks_of(moment)), ticks_of(moment)
