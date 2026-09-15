r"""A section modulus reads in cm³, not in the units its division happened to leave.

The reference page with no palette, `W = I/c` with `I` in mm⁴ and `c` in cm:

    W = 1.80×10⁸ mm⁴/cm

and the section modulus a design asks for, `W = M/f`, in each system:

    (180.00 kN·m)/(250.00 MPa)          = 0.72 kN·m/MPa
    (12.00 tonf·m)/(1400.00 kgf/cm²)    = 0.00857 tonf·m·cm²/kgf
    (50.00 kip·ft)/(24.00 ksi)          = 2.08 kip·ft/ksi

**Why.** No family table held a length cubed. With no family `_unit_is_the_engineers` has
no factor shape to compare against and keeps whatever unit arrived - the rule
`test_a_curvature_is_not_a_zero` recorded for `[length]⁻¹`. `[length]²` and `[length]⁴`
have had families since the first tables; the power between them was never written down.

**So `[length]³` gets the family the square has, `cm³` then `m³`**, and the band chooses
between them as it does for an area: a section modulus of 0.00072 m³ reads `720.00 cm³`, a
concrete volume of 3 m³ stays `3.00 m³`. `in³` in US customary units. The metric-technical
table gets `cm³` alone, and it is reached: a moment in `tonf·m` over a stress in `kgf/cm²`
keeps both forces in its unit until the family converts it. Cubic metres there would need a
modulus of several of them, and a mutant removing that step survived for that reason.

A modulus the sheet built from its own lengths - `b*h²/6` in millimetres - is the engineer's
and stays `mm³`, and a palette still decides first.
"""

import pytest

import engcalc_colab.magic as magic

from conftest import block_text


def page(monkeypatch, source: str, palette: str = "") -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()
    if palette:
        magics.eng_units(palette)
        captured.clear()
    magics.eng("", source)
    return block_text("".join(str(getattr(obj, "data", "")) for obj in captured))


def last_value(text: str) -> str:
    return text.rstrip().removesuffix(r"\endarray").rsplit("\\displaystyle", 1)[-1].strip()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("I := 5.4e9*mm^4\nc := 30*cm\nW = I/c\nnumeric(W)\n", "18000.00 cm³"),
        ("M_u := 180*kN*m\nf_y := 250*MPa\nW = M_u/f_y\nnumeric(W)\n", "720.00 cm³"),
        # Arrives in cubic metres, a member of the family, so the band chooses.
        ("I := 2.278e-3*m^4\nc := 0.3*m\nW = I/c\nnumeric(W)\n", "7593.33 cm³"),
        ("M := 12*tonf*m\nf_b := 1400*kgf/cm^2\nW = M/f_b\nnumeric(W)\n", "857.14 cm³"),
        ("M := 50*kip*ft\nF_b := 24*ksi\nW = M/F_b\nnumeric(W)\n", "25.00 in³"),
    ],
    ids=["reference-page", "si", "si-in-metres", "metric-technical", "us-customary"],
)
def test_a_section_modulus_reads_in_its_system_s_cubic_unit(monkeypatch, capsys, source, expected):
    text = page(monkeypatch, source)
    capsys.readouterr()

    assert last_value(text) == expected, text


# --- what must not move ---------------------------------------------------------------


def test_a_volume_stays_in_cubic_metres(monkeypatch, capsys):
    text = page(monkeypatch, "L := 3*m\nB := 4*m\ne := 0.25*m\nV = L*B*e\nnumeric(V)\n")
    capsys.readouterr()

    assert last_value(text) == "3.00 m³", text


def test_a_modulus_built_from_millimetres_keeps_them(monkeypatch, capsys):
    text = page(monkeypatch, "b := 300*mm\nh := 600*mm\nW = b*h^2/6\nnumeric(W)\n")
    capsys.readouterr()

    assert last_value(text) == "1.80×10⁷ mm³", text


def test_a_palette_still_decides(monkeypatch, capsys):
    text = page(
        monkeypatch, "M_u := 180*kN*m\nf_y := 250*MPa\nW = M_u/f_y\nnumeric(W)\n", palette="kN"
    )
    capsys.readouterr()

    assert last_value(text) == "0.00072 m³", text
