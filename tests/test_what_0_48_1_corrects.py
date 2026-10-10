r"""Presentation 0.48.1 corrects, from the inventory of open findings.

- C2j: an angle in a formula read `\cos(45 deg)`; it reads `\cos(45°)`, as its value does.
- An angle vector read in radians with no unit: `[30[deg], 45[deg]]` = `[0.52 0.79]`.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str, units: str = "") -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            magics = magic.EngMagics()
            if units:
                magics.eng_units(units)
            magics.eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), out.getvalue()

    return run


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("P := 10[kN]\nF = P*cos(45*deg)\nnumeric(F)\n", r"\cos{\left(45^{\circ} \right)}"),
        ("y = sin(30[deg])\n", r"\sin{\left(30^{\circ} \right)}"),
        ("a := [30[deg], 45[deg]]\n", r"\displaystyle 30^{\circ} & \displaystyle 45^{\circ}"),
        ("e := [2[deg]*3]\n", r"6.00^{\circ}"),
    ],
)
def test_an_angle_in_degrees_reads_with_its_mark(sheet, source, expected):
    page, printed = sheet(source)
    assert not printed, printed
    assert expected in page and r"\mathrm{deg}" not in page, page


def test_a_difference_of_degrees_celsius_keeps_its_space(sheet):
    page, printed = sheet("T := 20[degC]\nu = T*2\nnumeric(u)\n")
    assert not printed, printed
    assert r"40.00\,{}^{\circ}\mathrm{C}" in page, page


def test_a_vector_of_angles_reads_in_degrees(sheet):
    page, printed = sheet("a := [30[deg], 45[deg]]\n")
    assert not printed, printed
    assert r"\displaystyle 30.00 & \displaystyle 45.00\end{matrix}\right]\,{}^{\circ}" in page, page


def test_a_vector_of_angles_typed_in_radians_keeps_them(sheet):
    page, printed = sheet("t := [0.5[rad]; 1[rad]]\n")
    assert not printed, printed
    assert r"\displaystyle 0.50\\[3pt]\displaystyle 1.00\end{matrix}\right]\,\mathrm{rad}" in page, page


def test_an_angle_over_a_length_keeps_its_length(sheet):
    page, printed = sheet("d := [1[deg/m]]\n")
    assert not printed, printed
    assert r"\frac{1^{\circ}}{\mathrm{m}}" in page, page


def test_a_round_off_entry_does_not_move_a_vector_to_newtons(sheet):
    """His chapter 10: `[1 kN; 1e-7 kN]` read `[1000.00; 0.0001] N`."""
    page, printed = sheet("F := [1[kN]; 1e-7[kN]]\n")
    assert not printed, printed
    assert r"\displaystyle 1.00\\[3pt]\displaystyle 1.00 \times 10^{-7}\end{matrix}\right]\,\mathrm{kN}" in page, page


def test_a_small_force_beside_a_large_one_still_chooses_by_both(sheet):
    page, printed = sheet("G := [1[kN]; 0.5[N]]\n")
    assert not printed, printed
    assert r"\displaystyle 1000.00\\[3pt]\displaystyle 0.50\end{matrix}\right]\,\mathrm{N}" in page, page


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("K := [1e12, 0; 0, 1]\n", r"\displaystyle 10^{12} & \displaystyle 0"),
        ("F := [1[kN]; 1e-7[kN]]\n", r"\displaystyle 10^{-7}\,\mathrm{kN}"),
        ("f(I) = 2*I\ny = f(1e8[mm^4])\nnumeric(y)\n", r"f\left(1.00 \times 10^{8}\,\mathrm{mm}^{4}\right)"),
    ],
)
def test_a_power_of_ten_is_written_as_one(sheet, source, expected):
    page, printed = sheet(source)
    assert not printed, printed
    assert expected in page and "100000000" not in page and "1e-07" not in page, page
