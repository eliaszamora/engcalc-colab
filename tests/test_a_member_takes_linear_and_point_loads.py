r"""A member carries a linear load and point loads, and the diagrams draw them.

    member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, load=[w_1, w_2])
    member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, point=[P, a])
    member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, point=[P_1, a_1; P_2, a_2])

Approved on 2026-09-24 (*"apruebo ... la sintaxis de cargas"*): `load=[w_1, w_2]` runs
linearly from `w_1` at `start` to `w_2` at `end`; `point=[P, a]` is a load `P` at `a` from
`start`, one row per load. Both act towards -y', as `load=w` does. As before nothing is
solved again: the end forces are the sheet's, and the loads say what happens in between.

Every number below is a textbook one, worked by hand:
- simply supported, triangular 0 -> w: R = wL/6, wL/3; M_max = wL^2/(9 sqrt 3) at L/sqrt 3;
- simply supported, P at a: M = P a b / L under the load;
- fixed-fixed, P at the middle: δ = P L^3 / (192 EI);
- fixed-fixed, triangular 0 -> w: end moments wL^2/30, wL^2/20, reactions 3wL/20, 7wL/20,
  δ_max = wL^4 / (764 EI).
"""

import contextlib
import io

import matplotlib
import pytest
from matplotlib.figure import Figure

import engcalc_colab.magic as magic

matplotlib.use("Agg")


def _figure(source: str):
    captured = []
    console = io.StringIO()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(magic, "display", captured.append)
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
    figures = [item for item in captured if isinstance(item, Figure)]
    return (figures[0] if figures else None), console.getvalue()


def texts(figure, gid=None) -> list[str]:
    return [
        text.get_text()
        for axis in figure.axes
        for text in axis.texts
        if text.get_text() and (gid is None or text.get_gid() == gid)
    ]


TRIANGLE = """
L := 6*m
w := 12*kN/m
f := [0*kN; 12*kN; 0*kN*m; 0*kN; 24*kN; 0*kN*m]
member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, load=[0*kN/m, w])
"""

POINT = """
L := 6*m
P := 30*kN
f := [0*kN; 20*kN; 0*kN*m; 0*kN; 10*kN; 0*kN*m]
member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, point=[P, 2*m])
"""


def test_a_linear_load_moment_peaks_where_the_shear_is_zero():
    figure, console = _figure(TRIANGLE + "frame_plot(M)\n")
    assert not console, console
    assert "27.71" in texts(figure), texts(figure)


def test_a_linear_load_shear():
    figure, console = _figure(TRIANGLE + "frame_plot(V)\n")
    assert not console, console
    assert "12.00" in texts(figure) and "-24.00" in texts(figure), texts(figure)


def test_a_linear_load_is_drawn_growing_to_the_end():
    figure, console = _figure(TRIANGLE + "frame_plot(M)\n")
    assert not console, console
    arrows = [text for axis in figure.axes for text in axis.texts if text.get_gid() == "distributed-load"]
    tips = sorted(arrow.xy[0] for arrow in arrows)
    assert len(tips) >= 4 and tips[-1] == pytest.approx(6.0), tips
    lengths = sorted(abs(arrow.xyann[1] - arrow.xy[1]) for arrow in arrows)
    assert lengths[0] < lengths[-1], lengths
    assert any(label.startswith("12.00") for label in texts(figure)), texts(figure)


def test_a_point_load_moment_and_shear():
    figure, console = _figure(POINT + "frame_plot(M)\n")
    assert not console, console
    assert "40.00" in texts(figure), texts(figure)
    assert texts(figure, "point-load") == ["30.00 kN"], texts(figure, "point-load")
    figure, console = _figure(POINT + "frame_plot(V)\n")
    assert not console, console
    # The reaction's shear before the load, and after it the shear less P.
    placed = sorted(
        (text.xy[0], text.get_text()) for axis in figure.axes for text in axis.texts if text.get_text()
    )
    assert placed[0][1] == "20.00" and placed[-1][1] == "-10.00", placed


def test_two_point_loads_written_as_rows():
    figure, console = _figure(
        "L := 6*m\nP := 10*kN\nf := [0*kN; 10*kN; 0*kN*m; 0*kN; 10*kN; 0*kN*m]\n"
        'member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, point=[P, 2*m; P, 4*m])\n'
        "frame_plot(M)\n"
    )
    assert not console, console
    assert texts(figure).count("20.00") == 2, texts(figure)
    assert len(texts(figure, "point-load")) == 2


def test_a_point_load_bends_a_fixed_beam():
    figure, console = _figure(
        "L := 4*m\nP := 48*kN\nEI_v := 1000*kN*m^2\n"
        "f := [0*kN; 24*kN; 24*kN*m; 0*kN; 24*kN; -24*kN*m]\n"
        "u := [0*m; 0*m; 0; 0*m; 0*m; 0]\n"
        'member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, displacements=u, EI=EI_v, point=[P, 2*m])\n'
        "frame_plot(deformed)\n"
    )
    assert not console, console
    assert "δ = -16.00 mm" in texts(figure), texts(figure)


def test_a_linear_load_bends_a_fixed_beam():
    figure, console = _figure(
        "L := 4*m\nw := 10*kN/m\nEI_v := 1000*kN*m^2\n"
        "f := [0*kN; 6*kN; w*L^2/30; 0*kN; 14*kN; -w*L^2/20]\n"
        "u := [0*m; 0*m; 0; 0*m; 0*m; 0]\n"
        'member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, displacements=u, EI=EI_v, load=[0*kN/m, w])\n'
        "frame_plot(deformed)\n"
    )
    assert not console, console
    # w L^4 / (764 EI) = 3.35 mm.
    assert "δ = -3.35 mm" in texts(figure), texts(figure)


@pytest.mark.parametrize(
    "line, words",
    [
        ('member("V", start=[0*m, 0*m], end=[6*m, 0*m], load=[1*kN/m, 2*kN/m, 3*kN/m])\n', ("load", "[w_1, w_2]")),
        ('member("V", start=[0*m, 0*m], end=[6*m, 0*m], point=[10*kN, 7*m])\n', ("point", "7")),
        ('member("V", start=[0*m, 0*m], end=[6*m, 0*m], point=[10*kN, 2*kN])\n', ("point", "length")),
        ('member("V", start=[0*m, 0*m], end=[6*m, 0*m], point=[10*kN])\n', ("point", "[P, a]")),
    ],
)
def test_a_load_written_wrong_says_how(line, words):
    _figure_, console = _figure(line)
    for word in words:
        assert word in console, (word, console)
