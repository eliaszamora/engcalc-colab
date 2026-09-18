r"""A figure is set in a serif, like the mathematics on the page around it.

The engineer on 0.31.2, looking at his memoria in Colab: "hay fuentes distintas, no se ve
ordenado". Most of that was the computed blocks, which set their words in the notebook's
text font until they became `Math` outputs. What was left was the figures. Every label,
tick, annotation and title on a figure was matplotlib's DejaVu Sans, a sans-serif, between
equations MathJax sets in a serif - and the figure's units already typeset through
mathtext, so the axis read `M(x)` in one face and `[kgf·cm]` in another.

So a figure is built in DejaVu Serif, with mathtext's matching `dejavuserif`. Both ship
with matplotlib itself, so there is nothing for Colab or CI to be missing - which is not
true of `cmr10`, the closer match to MathJax, whose bold is absent and which put a
`findfont` warning under the one bold label every figure has.

Two things the change must not do, and each has a contract below. It must not reach the
notebook's own matplotlib state: a library that rewrites a user's `rcParams` changes the
figures they draw themselves. And it must survive a draw: the figure is built inside a
context and Colab draws it outside, and a draw that needs another tick makes one.
"""

import matplotlib
import pytest
from matplotlib.text import Text

import engcalc_colab.magic as magic

matplotlib.use("Agg")

SERIF = "DejaVu Serif"
SERIF_MATH = "dejavuserif"

SHEET = """L := 600*cm
q := 10.20*kgf/cm
M(x) = q*x*(L - x)/2
M2(x) = 1.5*M(x)
P2 := 200*kN
Md(x) = P2*x*(L - x)/L
"""


@pytest.fixture
def figures(monkeypatch):
    def draw(source: str) -> list:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magics = magic.EngMagics()
        magics.eng_units("kgf")
        magics.eng("", SHEET + source)
        found = [item for item in captured if hasattr(item, "savefig")]
        assert found, "the cell drew no figure"
        return found

    return draw


def texts(figure) -> list[Text]:
    """Every piece of writing on the figure, after it has been drawn once."""
    figure.canvas.draw()
    return [text for text in figure.findobj(Text) if text.get_text()]


@pytest.mark.parametrize(
    "call",
    [
        "plot(M(x), x, 0, L)",
        "plot(M(x), M2(x), x, 0, L)",
        'plot(M(x), x, 0, L, title="Momento", xlabel="Posición", ylabel="Momento")',
        "plot(Md(x), x, 0, L, P2=[200*kN, 400*kN, 600*kN, 800*kN])",
    ],
)
def test_every_piece_of_writing_on_a_figure_is_serif(figures, call):
    """Title, axis labels, ticks, annotations, the offset and a legend: one face.

    And the summary panel a sweep of four curves or more draws beside the plot, whose
    texts are made after the plot is laid out, by the layout pass.
    """
    for figure in figures(call + "\n"):
        for text in texts(figure):
            assert text.get_fontfamily() == [SERIF], (text.get_text(), text.get_fontfamily())


def test_the_mathematics_on_a_figure_is_the_serif_s_own(figures):
    """A unit on an axis typesets through mathtext, which has its own font setting."""
    for figure in figures("plot(M(x), x, 0, L)\n"):
        written = [text for text in texts(figure) if "$" in text.get_text()]
        assert written, "no typeset label to check"
        for text in written:
            assert text.get_math_fontfamily() == SERIF_MATH, text.get_text()


def test_the_ticks_are_still_serif_after_the_figure_is_drawn_again(figures):
    """Matplotlib rebuilds tick labels on every draw; the face has to be on the axis."""
    (figure,) = figures("plot(M(x), x, 0, L)\n")
    figure.canvas.draw()
    figure.axes[0].set_xlim(-50, 650)
    figure.canvas.draw()
    ticks = [label for label in figure.axes[0].get_xticklabels() if label.get_text()]
    assert ticks
    for label in ticks:
        assert label.get_fontfamily() == [SERIF], label.get_text()


def test_the_notebook_s_own_matplotlib_settings_are_left_alone(figures, monkeypatch):
    """The engineer's own `plt.plot(...)` in the next cell is not EngCalc's to restyle.

    The notebook's settings are set here to values nobody would choose, so the contract
    reads its own answer back. Its first draft compared the settings before and after,
    and mutation showed why that is no test: a change that wrote the page's type into
    `rcParams` had already done so in an earlier test in the same process, so "before"
    was the page's type too, and the two were equal.
    """
    mine = {"font.family": ["cursive"], "mathtext.fontset": "stixsans"}
    for key, value in mine.items():
        monkeypatch.setitem(matplotlib.rcParams, key, value)
    figures("plot(M(x), x, 0, L)\n")
    assert {key: matplotlib.rcParams[key] for key in mine} == mine
