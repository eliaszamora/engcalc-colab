r"""A unit nobody typed is the algebra's, however it is shaped.

The engineer, told that a section written in millimetres on a kilogram-force sheet prints
`kgf/mm^2`:

    "yo nunca he ocupado kgf/mm2. debería ser kgf/cm2 no? es lo más común?"

It is: f'c is 250 kgf/cm^2, fy 4200, the steel modulus 2.1e6. `kgf/mm^2` is not written in
structural work at all. And the note that left this open was wrong about why it was safe -
it said sections are written in centimetres, when a structural section is written in
millimetres, as the braced-frame benchmark's own `b := 300*mm` is.

What it costs is not a unit, it is a number nobody recognises:

    P := 25000*kgf, b := 300*mm, d := 450*mm     ->  0.19 kgf/mm^2
                                                     18.52 kgf/cm^2 is the stress

#109 settled `GPa*mm` against `kN/m` by comparing what the factors *are* - a pressure
against a force - and that cannot separate these two: `kgf/mm^2` and `kgf/cm^2` are both a
force over a length, and so are `kN/mm` and `kN/m`.

**There is no rule here, and three were tried before admitting it.** "The sheet never
wrote this composite" sends `mm^2`, built from two declared `mm`, to `cm^2`. "The family
member has several factors" and "a one-member family is authoritative" each break one of
`N*mm`, `kN/mm` and an inertia in `mm^4`. What is actually true is narrower and is not
about units at all: **in the metric-technical system a stress is written `kgf/cm^2`**,
the way it is written `MPa` in SI - and SI gets there on its own only because `MPa` is a
*named* unit whose factor shape differs, which `kgf/cm^2` is not.

So it is recorded as a convention, in `_AUTHORITATIVE_TECHNICAL_DIMENSIONS`, holding one
dimension in one system and saying that it is a convention. And it yields to anything the
sheet actually wrote, because the first version of it rewrote a soil pressure the engineer
had typed as `tonf/m^2`.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str) -> str:
        captured.clear()
        magic.EngMagics().eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


KGF_CM2 = r"\frac{\mathrm{kgf}}{\mathrm{cm}^{2}}"


# --- the defect ---------------------------------------------------------------------

def test_a_stress_from_millimetre_sections_reads_in_kgf_per_cm2(cell):
    final = _final(cell("P := 25000*kgf\nb := 300*mm\nd := 450*mm\ns = P/(b*d)\nnumeric(s)\n"))
    assert "18.52" in final, final
    assert KGF_CM2 in final, final
    assert "mm" not in final, final


def test_a_bending_stress_from_millimetre_sections_reads_the_same_way(cell):
    """`500 kgf*m` over a section modulus of `30 x 45^2 / 6 = 10125 cm^3` is
    `4.94 kgf/cm^2`. This asserted `494` when it was written, which was my arithmetic
    and not the engine's: the value was right the moment the unit was."""
    final = _final(cell(
        "M := 500*kgf*m\nb := 300*mm\nd := 450*mm\ns = M/(b*d**2/6)\nnumeric(s)\n"
    ))
    assert KGF_CM2 in final, final
    assert "4.94" in final, final


# --- the units the sheet did write must survive --------------------------------------

def test_a_stiffness_the_sheet_wrote_in_kn_per_mm_is_kept(cell):
    final = _final(cell("k := 10*kN/mm\nx = 2*k/2\nnumeric(x)\n"))
    assert r"\frac{\mathrm{kN}}{\mathrm{mm}}" in final, final
    assert "10.00" in final, final


def test_a_matrix_of_a_written_stiffness_is_kept(cell):
    final = _final(cell("k := 10*kN/mm\nA = [k, 0; 0, 2*k]\nnumeric(A)\n"))
    assert r"\frac{\mathrm{kN}}{\mathrm{mm}}" in final, final


def test_a_line_load_the_sheet_wrote_in_tonf_per_m_is_kept(cell):
    final = _final(cell("q := 2.8*tonf/m\nw = 1*q\nnumeric(w)\n"))
    assert r"\frac{\mathrm{tonf}}{\mathrm{m}}" in final, final


def test_a_moment_the_sheet_wrote_in_kgf_cm_is_kept(cell):
    final = _final(cell("M := 5000*kgf*cm\nx = 2*M/2\nnumeric(x)\n"))
    assert r"\mathrm{kgf} \cdot \mathrm{cm}" in final, final


def test_an_inertia_the_sheet_wrote_in_mm4_is_kept(cell):
    final = _final(cell("I := 80e6*mm**4\nJ = 2*I/2\nnumeric(J)\n"))
    assert r"\mathrm{mm}^{4}" in final, final


# --- what #109 settled must stay settled ----------------------------------------------

def test_a_plate_stiffness_still_leaves_gigapascal_millimetres(cell):
    final = _final(cell("E := 210*GPa\nt := 8*mm\nk = E*t\nnumeric(k)\n"))
    assert "GPa" not in final, final
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in final, final


# --- ordinary sheets are untouched ------------------------------------------------------

def test_an_si_sheet_is_untouched(cell):
    final = _final(cell("q := 10*kN/m\nL := 6*m\nM = q*L**2/8\nnumeric(M)\n"))
    assert "45.00" in final, final
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final


def test_a_technical_sheet_in_centimetres_is_untouched(cell):
    final = _final(cell("P := 25000*kgf\nA := 100*cm**2\nfc = P/A\nnumeric(fc)\n"))
    assert "250.00" in final, final
    assert KGF_CM2 in final, final


def test_a_deflection_still_reaches_millimetres(cell):
    final = _final(cell(
        "L := 6*m\nq := 10*kN/m\nE := 200*GPa\nI_z := 80e6*mm**4\n"
        "d = 5*q*L^4/(384*E*I_z)\nnumeric(d)\n"
    ))
    assert "10.55" in final, final
    assert r"\mathrm{mm}" in final, final


# --- the convention yields to what the sheet wrote ------------------------------------

def test_a_soil_pressure_written_in_tonnes_per_square_metre_is_kept(cell):
    """The half that nearly went. A bearing pressure is written `tonf/m^2` across Latin
    American geotechnics, and the convention above would otherwise rewrite it as
    `0.28 kgf/cm^2` - the same value, and not what the engineer typed. It yields to any
    unit the sheet actually wrote, which is the whole reason the engine keeps them."""
    final = _final(cell("q := 2.8*tonf/m**2\nx = 1*q\nnumeric(x)\n"))
    assert "2.80" in final, final
    assert r"\frac{\mathrm{tonf}}{\mathrm{m}^{2}}" in final, final


def test_two_forces_of_the_same_dimension_have_the_same_shape():
    """A latent defect in #109's shape rule, found by chasing the pressure above.

    `_factor_shape` compared the *spelling* of a dimensionality, and Pint renders one in
    whatever order it holds it: `kgf` gives `[length] * [mass] / [time] ** 2` and `tonf`
    gives `[mass] * [length] / [time] ** 2` for the same dimension. `kN` and `N` fall on
    one side, `kip` and `lbf` on the other, so the rule was wrong in every system at once
    and only showed where a value and its family member used different spellings.
    """
    import engcalc_colab.renderer as renderer
    from engcalc_colab.numeric import engineering_registry

    registry = engineering_registry()
    shapes = {
        name: renderer._factor_shape(registry.Quantity(1.0, f"{name}/m**2"))
        for name in ("kgf", "tonf", "kN", "N", "kip", "lbf")
    }
    assert len(set(shapes.values())) == 1, shapes
