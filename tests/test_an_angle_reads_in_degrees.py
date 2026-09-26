r"""An angle the sheet worked out reads in degrees, written with the degree sign.

Seen in his exercise 2.1 on 2026-09-26: `theta := atan(4/6)` read `0.59 rad`, and asking
for degrees, `numeric(theta, deg)`, wrote four rows - `θ = θ = (0.59 rad) = 33.69 deg` -
with `deg` where a drawing writes `°`. He left it to me (*"lo dejo a tu criterio"*).

A memoria reads angles in degrees. An angle the sheet computed - an `atan`, an `asin` -
has no unit anyone wrote, so it is shown in degrees: `θ = 33.69°`, and `sin(33.69°)`
where it is substituted. An angle written in radians keeps them (`t := 0.5*rad`), as
every declared unit is kept, and a frequency in `rad/s` is not an angle. A degree is
written `°`, against the number: `30.00°`, not `30.00 deg`.

And `numeric` of a name that already holds a value writes one row, `w = 374.98 1/s`,
not the name, its value in brackets and the value again.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def page(monkeypatch):
    def run(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        assert "engcalc:" not in console.getvalue(), console.getvalue()
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return run


def test_a_computed_angle_reads_in_degrees(page):
    shown = page("theta := atan(4/6)\n")
    assert r"\theta & = & \displaystyle 33.69^{\circ}" in shown, shown
    assert "rad" not in shown, shown


def test_a_computed_angle_is_substituted_in_degrees(page):
    shown = page("phi := atan(4/3)\nd := 2*mm\nkeep u = d*sin(phi)\nnumeric(u)\n")
    assert r"\sin{\left(53.13^{\circ} \right)}" in shown, shown


def test_an_angle_written_in_degrees_takes_the_sign(page):
    shown = page("alpha := 30*deg\n")
    assert r"\alpha & = & \displaystyle 30.00^{\circ}" in shown, shown
    assert r"\mathrm{deg}" not in shown, shown


def test_an_angle_written_in_radians_keeps_them(page):
    shown = page("t := 0.5*rad\n")
    assert r"t & = & \displaystyle 0.50\,\mathrm{rad}" in shown, shown


def test_a_frequency_is_not_an_angle(page):
    shown = page("w := 12*rad/s\n")
    assert r"\mathrm{rad}" in shown and r"^{\circ}" not in shown, shown


def test_the_same_number_goes_on(page):
    # Shown in degrees, computed as the same angle: sin(33.69°) is sin(0.588 rad).
    shown = page("theta := atan(4/6)\ny = 10*sin(theta)\nnumeric(y)\n")
    assert r"5.55" in shown, shown


@pytest.mark.parametrize(
    "source, row",
    [
        ("w := 374.98/s\nnumeric(w)\n", r"w & = & \displaystyle 374.98\,\frac{1}{\mathrm{s}}"),
        ("d := 0.00241*m\nnumeric(d, mm)\n", r"d & = & \displaystyle 2.41\,\mathrm{mm}"),
        ("t := 0.5*rad\nnumeric(t, deg)\n", r"t & = & \displaystyle 28.65^{\circ}"),
    ],
)
def test_numeric_of_a_value_is_one_row(page, source, row):
    shown = page(source)
    name = row.split(" & = & ")[0]
    # Its `:=` row and this one, and nothing between: no `w = w`, no `(374.98 1/s)`.
    assert rf"{name} & = & \displaystyle {name} " not in shown, shown
    assert r" & = & \displaystyle \left(" not in shown, shown
    assert shown.rstrip().endswith(row + r" \end{array}"), shown


def test_a_column_of_angles_reads_in_degrees(page):
    shown = page("L := 4*m\nh(x) = atan(x/L)\ntable(h(x), x, 0*m, 4*m, 3)\n")
    assert r"[{}^{\circ}]" in shown and "26.57" in shown and "45.00" in shown, shown
    assert "rad" not in shown, shown


def test_a_degree_as_text_is_its_sign():
    import pint

    from engcalc_colab.unit_text import quantity_text, unit_text

    units = pint.get_application_registry()
    assert unit_text(units.degree) == "°"
    assert quantity_text(units.Quantity(30, "degree"), decimals=2) == "30.00°"
