r"""A moment's axis reads `kN·m`, and one rule for it is enough.

`plotting._force_length_unit_order` read a formatted unit string back and swapped its
factors when a moment had come out length-first: `m·kN` became `kN·m`, `cm·kgf` became
`kgf·cm`. It is gone, and this file is what replaces it.

**Nothing on a page reached it.** Measured twice, before and after the plotting path was
given a palette in #140: nine sheets across `kN·m`, `kgf·cm`, `N·mm` and `tonf·m`,
written force-first and length-first, with each palette and without, through `plot`,
`envelope` and a parameter sweep. Every one arrives at the axis already force-first,
because the registry's `_keep_written_unit_order` and the display path settle the order
long before a label is built. A mutant that broke its comparison survived the whole suite
on both Pint versions, which is what put it on the list.

It was not harmless furniture, either. It worked by splitting the formatted string on the
dot - so when Pint 0.26 changed which dot that is, the rule stopped applying and the plot
went on drawing, silently. #138 fixed the character and left the rule; this removes the
second thing that could go wrong with it.

What the page needs is the property, not the mechanism: a moment is labelled force
first. That is asserted here directly, over the units an engineer actually writes, so
removing the code cannot quietly remove the guarantee.
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


@pytest.mark.parametrize(
    "sheet, expected",
    [
        ("L := 6*m\nP := 40*kN\nM(x) = P*x\nplot(M(x), x, 0, L)\n", "kN·m"),
        ("L := 6*m\nP := 40*kN\nM(x) = x*P\nplot(M(x), x, 0, L)\n", "kN·m"),
        ("L := 600*cm\nP := 4000*kgf\nM(x) = x*P\nplot(M(x), x, 0, L)\n", "kgf·cm"),
        ("L := 6000*mm\nP := 40000*N\nM(x) = x*P\nplot(M(x), x, 0, L)\n", "N·mm"),
        ("L := 6*m\nP := 4*tonf\nM(x) = x*P\nplot(M(x), x, 0, L)\n", "tonf·m"),
    ],
)
def test_a_moment_axis_names_the_force_first(cell, sheet, expected):
    """Written either way round, in four unit systems."""
    label = cell(sheet).axes[0].get_ylabel()
    assert f"[{expected}]" in label, label


def test_a_palette_does_not_change_the_order(cell, capsys):
    figure = cell("L := 6*m\nP := 40*kN\nM(x) = x*P\nplot(M(x), x, 0, L)\n", palette="kgf")
    capsys.readouterr()
    assert "[kgf·cm]" in figure.axes[0].get_ylabel(), figure.axes[0].get_ylabel()


def test_an_envelope_names_it_the_same_way(cell):
    figure = cell(
        "L := 6*m\nP := 40*kN\nA(x) = x*P\nB(x) = x*P*0.8\n"
        "envelope(A(x), B(x), x, 0, L)\n"
    )
    assert "[kN·m]" in figure.axes[0].get_ylabel(), figure.axes[0].get_ylabel()


def test_the_rule_that_was_removed_is_gone(cell):
    """Stated so nobody puts it back without measuring again. It reached nothing, and
    the way it worked - reading a formatted string back and splitting it on a character -
    is what let Pint 0.26 disable it in silence."""
    import engcalc_colab.plotting as plotting

    assert not hasattr(plotting, "_force_length_unit_order")
