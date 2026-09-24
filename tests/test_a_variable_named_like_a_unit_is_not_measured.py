r"""A variable that shares its name with a unit is not given a one.

    T = [c, s; -s, c]        0.32.2 printed   [c, 1 s; -1 s, c]
    N_u = N + P              0.32.2 printed   1 N + P

0.32.2 wrote a unit standing alone with its one, so that `1*m` in a table or an argument
read `1 m` and not `m`. It decided by the name, and a name does not say which it is: `s` is
the second and the sine of a direction, `N` the newton and an axial force, `m` the metre and
a mass. A transformation matrix read `[c, 1 s; -1 s, c]`. Found on 2026-09-23 checking the
very derivation he had asked for, before it was handed to him.

What does say it is how the sheet writes the name. `1*m`, `2*kN/m`, `-1*kN/m`, `0*m` are
measurements - a number and units and nothing else - and a name written that way is a unit
of this sheet. `c^2 + s^2` and `N + P` never write it so. The one goes only to units the sheet
has measured; `%eng_reset` forgets them with everything else.
"""

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.renderer import _MATRIX_ROW_SEPARATOR as ROW


@pytest.fixture
def magics(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    engine = magic.EngMagics()
    engine.captured = captured
    return engine


def run(magics, source: str) -> str:
    magics.captured.clear()
    magics.eng("", source)
    return "".join(getattr(obj, "data", "") for obj in magics.captured)


@pytest.mark.parametrize(
    ("source", "shown"),
    [
        (
            "T = [c, s; -s, c]\n",
            r"c & \displaystyle \mathrm{s}" + ROW + r"\displaystyle - \mathrm{s} & \displaystyle c",
        ),
        ("x = c^2 + s^2\n", r"c^{2} + \mathrm{s}^{2}"),
        ("N_u = N + P\n", r"N_{u} & = & \displaystyle \mathrm{N} + P"),
        ("p = m*g + s\n", r"g\,\mathrm{m} + \mathrm{s}"),
    ],
)
def test_a_name_never_measured_keeps_no_one(magics, capsys, source, shown):
    page = run(magics, source)
    assert "engcalc:" not in capsys.readouterr().out
    assert shown in page, page
    assert r"1\,\mathrm{" not in page, page


@pytest.mark.parametrize(
    ("source", "shown"),
    [
        ("L := 8*m\nb = max(1*m, L/4)\n", r"\max\left(1\,\mathrm{m}, \frac{L}{4}\right)"),
        ("K = [2*kN/m, -1*kN/m; -1*kN/m, 2*kN/m]\n", r"- \frac{1\,\mathrm{kN}}{\mathrm{m}}"),
        ("k(x) = 1*kN + 4*kN*x/m\nx0 := 1*m\nnumeric(k(x0))\n", r"1\,\mathrm{kN} + \frac{4\,\mathrm{kN}\,x}{\mathrm{m}}"),
    ],
)
def test_a_measured_unit_still_has_its_one(magics, capsys, source, shown):
    page = run(magics, source)
    assert "engcalc:" not in capsys.readouterr().out
    assert shown in page, page


@pytest.mark.parametrize(
    "source",
    [
        # A unit asked for is not a unit measured: there is no number in `kN/m`, and the
        # sheet measured millimetres, not metres.
        "k := 2000*kN/mm\nnumeric(k, kN/m)\np = m + a\n",
        # A number times a variable is not a measurement of it: `2*m*a` keeps `m` a mass.
        "F = 2*m*a\np = m + a\n",
    ],
)
def test_what_is_not_a_measurement_measures_nothing(magics, capsys, source):
    page = run(magics, source)
    assert "engcalc:" not in capsys.readouterr().out
    assert r"a + \mathrm{m}" in page, page
    assert r"1\,\mathrm{m}" not in page, page


def test_a_reset_forgets_what_was_measured(magics, capsys):
    """A metre measured in one sheet is not a metre in the next one."""
    run(magics, "b = max(1*m, 2*a)\n")
    with pytest.MonkeyPatch.context():
        magics.eng_reset("")
    page = run(magics, "x = m + a\n")
    assert "engcalc:" not in capsys.readouterr().out.replace("engcalc state cleared", "")
    assert r"1\,\mathrm{m}" not in page, page
