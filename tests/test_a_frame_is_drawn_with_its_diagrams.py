r"""The diagrams of a frame, drawn on the frame: `member` and `frame_plot`.

    member("C1", start=[0*m, 0*m], end=[0*m, h], forces=f_1, displacements=T_c*D_1, EI=E*I_c)
    member("V",  start=[0*m, h],   end=[L, h],   forces=f_v, displacements=d,       EI=E*I_v, load=w)
    member("C2", start=[L, 0*m],   end=[L, h],   forces=f_4, displacements=T_c*D_4, EI=E*I_c)

    frame_plot(M, "Momento flector")
    frame_plot(V, "Fuerza cortante")
    frame_plot(N, "Fuerza axial")
    frame_plot(deformed, "Deformada", scale=150)

Approved on 2026-09-24 over a mock-up of `tools/portico_matricial.eng`: *"Sí, opción (b),
apruebo la sintaxis y déjalo como Figura"*. `member` declares what the sheet already
worked out - the geometry, the end forces in local axes, the local displacements - and
EngCalc does not solve the frame again. Asked for with it: the moment drawn on the tension
side, values with their sign in boxes, loads in red, and a distributed load that *"siempre
se debe empezar y terminar con una flecha"*.

Option (b) is the sign: a moment is positive when it pulls the fibre on the inside of the
frame, so the knee reads the same number from the beam and from the column. Each member is
read as a beam seen from inside the frame, which makes the shear follow the same reading.

A `frame_plot` is a figure, numbered with the figures of `image`.
"""

import base64
import contextlib
import io
import pathlib

import matplotlib
import pytest
from IPython.display import Markdown
from matplotlib.figure import Figure

import engcalc_colab.magic as magic

matplotlib.use("Agg")

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRAME = (ROOT / "tools" / "portico_matricial.eng").read_text(encoding="utf-8")
MEMBERS = """
member("C1", start=[0*m, 0*m], end=[0*m, h], forces=f_1, displacements=T_c*D_1, EI=E*I_c)
member("V", start=[0*m, h], end=[L, h], forces=f_v, displacements=d, EI=E*I_v, load=w)
member("C2", start=[L, 0*m], end=[L, h], forces=f_4, displacements=T_c*D_4, EI=E*I_c)
"""
PLOTS = """
frame_plot(M, "Momento flector")
frame_plot(V, "Fuerza cortante")
frame_plot(N, "Fuerza axial")
frame_plot(deformed, "Deformada", scale=150)
"""


def _run(magics, source: str):
    captured = []
    console = io.StringIO()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(magic, "display", captured.append)
        with contextlib.redirect_stdout(console):
            magics.eng("", source)
    return captured, console.getvalue()


@pytest.fixture(scope="module")
def frame():
    """The frame, its members and its four diagrams, run once: the sheet takes seconds."""
    magics = magic.EngMagics()
    with contextlib.redirect_stdout(io.StringIO()):
        magics.eng_units("kgf")
    _run(magics, FRAME)
    members, members_console = _run(magics, MEMBERS)
    outputs, console = _run(magics, PLOTS)
    assert not console, console
    figures = [item for item in outputs if isinstance(item, Figure)]
    captions = [item.data for item in outputs if isinstance(item, Markdown)]
    return {
        "members": (members, members_console),
        "figures": dict(zip(("M", "V", "N", "deformed"), figures)),
        "captions": captions,
        "magics": magics,
    }


def texts(figure) -> list[str]:
    return [text.get_text() for axis in figure.axes for text in axis.texts if text.get_text()]


def title(figure) -> str:
    return figure.axes[0].get_title()


def test_a_member_puts_nothing_on_the_page(frame):
    outputs, console = frame["members"]
    assert outputs == [] and not console, (outputs, console)


def test_each_diagram_is_a_numbered_figure(frame):
    assert len(frame["figures"]) == 4
    assert frame["captions"] == [
        "**Figura 1.** Momento flector",
        "**Figura 2.** Fuerza cortante",
        "**Figura 3.** Fuerza axial",
        "**Figura 4.** Deformada",
    ]


def test_the_moment_reads_the_same_at_a_knee(frame):
    """Option (b): tension inside is positive, so beam and column agree at each knee."""
    labels = texts(frame["figures"]["M"])
    assert labels.count("-519 596") == 1, labels
    assert labels.count("49 214") == 1, labels
    for value in ("-198 602", "687 277", "432 588"):
        assert value in labels, (value, labels)
    assert "519 596" not in labels, labels
    assert title(frame["figures"]["M"]).startswith("M"), title(frame["figures"]["M"])


def test_the_shear_is_read_from_inside_the_frame(frame):
    labels = texts(frame["figures"]["V"])
    for value in ("5 052", "-6 948", "620", "-2 380"):
        assert value in labels, (value, labels)
    assert "2 380" not in labels, labels


def test_the_axial_force_is_positive_in_tension(frame):
    labels = texts(frame["figures"]["N"])
    for value in ("-2 380", "-5 052", "-6 948"):
        assert value in labels, (value, labels)


def test_the_deformed_shape_gives_the_displacements(frame):
    figure = frame["figures"]["deformed"]
    labels = texts(figure)
    assert "Δx = 0.63 cm" in labels and "Δx = 0.62 cm" in labels, labels
    assert "δ = -0.35 cm" in labels, labels
    assert "150" in title(figure), title(figure)


def _arrows(figure, gid):
    return [text for axis in figure.axes for text in axis.texts if text.get_gid() == gid]


def test_a_distributed_load_starts_and_ends_with_an_arrow(frame):
    arrows = _arrows(frame["figures"]["M"], "distributed-load")
    tips = sorted(arrow.xy[0] for arrow in arrows)
    assert len(tips) >= 5, tips
    assert tips[0] == pytest.approx(0.0) and tips[-1] == pytest.approx(600.0), tips


def test_the_load_on_a_joint_is_drawn_in_red(frame):
    (label,) = [text for text in _arrows(frame["figures"]["M"], "joint-load") if text.get_text()]
    assert label.get_text() == "3 000 kgf", label.get_text()
    assert matplotlib.colors.to_hex(label.get_color()) == "#b03a2e"


def test_the_supports_are_drawn_where_nothing_moves(frame):
    figure = frame["figures"]["M"]
    supports = [line for axis in figure.axes for line in axis.lines if line.get_gid() == "support"]
    assert supports, "no support drawn"


def test_the_deformed_scale_is_chosen_when_not_given(frame):
    outputs, console = _run(frame["magics"], "frame_plot(deformed)\n")
    assert not console, console
    (figure,) = [item for item in outputs if isinstance(item, Figure)]
    assert "×" in title(figure), title(figure)


# One pixel, for a figure placed with `image` before a diagram.
PIXEL = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)

BEAM = """
L := 6*m
w := 2000*kgf/m
f := [0*kgf; w*L/2; w*L^2/12; 0*kgf; w*L/2; -w*L^2/12]
member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, load=w)
"""


def _fresh(source: str):
    return _run(magic.EngMagics(), source)


def test_an_image_and_a_diagram_share_the_numbering(tmp_path, monkeypatch):
    (tmp_path / "viga.png").write_bytes(PIXEL)
    monkeypatch.chdir(tmp_path)
    outputs, console = _fresh(BEAM + 'image("viga.png", "La viga")\nframe_plot(M, "Momento")\n')
    assert not console, console
    captions = [item.data for item in outputs if isinstance(item, Markdown)]
    assert captions == ["**Figura 1.** La viga", "**Figura 2.** Momento"], captions


def test_a_beam_alone_is_drawn(tmp_path):
    outputs, console = _fresh(BEAM + "frame_plot(M)\n")
    assert not console, console
    (figure,) = [item for item in outputs if isinstance(item, Figure)]
    labels = texts(figure)
    # w L^2/24 at the middle of a fixed-ended beam, -w L^2/12 at its ends: in kN·m, as the
    # page writes f without a palette - not in the base units a matrix of numbers keeps.
    assert "29.42" in labels and "-58.84" in labels, labels
    assert "kN" in title(figure), title(figure)


@pytest.mark.parametrize(
    "source, words",
    [
        ("frame_plot(M)\n", ("member",)),
        (BEAM + "frame_plot(deformed)\n", ("displacements", "V")),
        ('member("X", start=[0*m, 0*m], end=[1*m, 0*m], forces=[1*kgf; 2*kgf])\nframe_plot(M)\n', ("forces", "6")),
        ('member("X", start=[0*kgf, 0*m], end=[1*m, 0*m])\n', ("start", "length")),
        ('member("X", start=[0*m, 0*m], end=[0*m, 0*m])\n', ("X", "length")),
        (BEAM + 'member("Y", start=[0*m, 0*m], end=[1*m, 0*m])\nframe_plot(V)\n', ("forces", "Y")),
    ],
)
def test_what_is_missing_is_said(source, words):
    _outputs, console = _fresh(source)
    for word in words:
        assert word in console, (word, console)


@pytest.mark.parametrize(
    "line, words",
    [
        ("frame_plot(Q)\n", ("frame_plot", "M, V, N or deformed")),
        ('frame_plot(M, "Momento", scale=10)\n', ("scale", "deformed")),
        ('member("X", start=[0*m, 0*m], end=[1*m, 0*m], colour=1)\n', ("member", "colour")),
        ("member(X, start=[0*m, 0*m], end=[1*m, 0*m])\n", ("member", "name in quotes")),
        ('member("X", end=[1*m, 0*m])\n', ("start",)),
        ('member("X", start=[0*m], end=[1*m, 0*m])\n', ("start", "two")),
    ],
)
def test_a_line_written_wrong_says_how_to_write_it(line, words):
    _outputs, console = _fresh(line)
    for word in words:
        assert word in console, (word, console)


def test_a_reset_forgets_the_members():
    magics = magic.EngMagics()
    _run(magics, BEAM)
    with contextlib.redirect_stdout(io.StringIO()):
        magics.eng_reset("")
    _outputs, console = _run(magics, "frame_plot(M)\n")
    assert "member" in console, console


# A cantilever, fixed at the left, with a moment of 10 kN·m applied at its free end:
# the member's end moments are -10 and +10 kN·m, the tip turns M L / EI and rises
# M L^2 / (2 EI). Nothing but the moment loads it.
CANTILEVER = """
L := 3*m
M_0 := 10*kN*m
EI_c := 5000*kN*m^2
f := [0*kN; 0*kN; -M_0; 0*kN; 0*kN; M_0]
u := [0*m; 0*m; 0; 0*m; M_0*L^2/(2*EI_c); M_0*L/EI_c]
member("B", start=[0*m, 0*m], end=[L, 0*m], forces=f, displacements=u, EI=EI_c)
"""


def test_a_moment_on_a_joint_is_read_back_and_drawn():
    """Asked for with the rest of the pending points: a moment applied at a joint was
    not drawn. It needs no syntax - the end moments meeting at a free joint add up to
    it, as the end forces add up to the force there."""
    outputs, console = _fresh(CANTILEVER + "frame_plot(M)\n")
    assert not console, console
    (figure,) = [item for item in outputs if isinstance(item, Figure)]
    moments = _arrows(figure, "joint-moment")
    labels = [text.get_text() for text in moments if text.get_text()]
    assert len(labels) == 1 and labels[0].startswith("10.00"), labels
    assert matplotlib.colors.to_hex(moments[0].get_color()) == "#b03a2e"
    assert not [text for text in _arrows(figure, "joint-load") if text.get_text()]


def test_the_frame_has_no_moment_on_its_joints(frame):
    assert not _arrows(frame["figures"]["M"], "joint-moment")


def test_a_fixed_end_is_a_wall_across_its_member():
    """A cantilever's fixed end stood on the ground under the beam; it is a wall."""
    outputs, console = _fresh(CANTILEVER + "frame_plot(M)\n")
    assert not console, console
    (figure,) = [item for item in outputs if isinstance(item, Figure)]
    lines = [line for axis in figure.axes for line in axis.lines if line.get_gid() == "support"]
    wall = [line for line in lines if len(set(line.get_xdata())) == 1]
    assert wall and all(line.get_xdata()[0] == pytest.approx(0.0) for line in wall), [
        (list(line.get_xdata()), list(line.get_ydata())) for line in lines
    ]
    assert all(max(line.get_xdata()) <= 1e-9 for line in lines), "the hatching is not behind the wall"
