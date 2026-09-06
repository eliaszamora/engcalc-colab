r"""A sheet written in kilogram-force is shown in kilogram-force.

The engineer, asked which units he works in:

    "el f'c creo que lo trabajo en kgf cm2 normalmente y también en MPa ... el E del
     acero nunca lo he trabajado en GPa ... Quizás podrías elegir las unidades
     dependiendo de qué forma te doy los inputs? si te los doy en kgf, entonces que sea
     kgf, si te los doy en MPa entonces que sea MPa, si te los doy en ambos, elige
     kgf cm2."

That is not a preference to be configured. It is the rule this renderer already follows
for US customary units, applied to the system half the Spanish-speaking world writes in.
A page in `psi`, `ksi`, `kip` and `ft` is detected and kept, because RC-1 gave imperial
its own family table. The metric-technical system never got one, so a sheet written
entirely in it was converted to SI under the engineer:

    fc := 250*kgf/cm**2          ->  24.52 MPa      the *declared* unit, overruled
    P/A from 25000 kgf, 100 cm2  ->  24.52 MPa
    E := 2100000*kgf/cm**2       ->  205.94 GPa     the one unit he says he never uses

The declared case fails for the reason that has been failing all session:
`_unit_terms` counts `kgf/cm**2` as two and `MPa` as one, so the term heuristic decides
the engineer's own unit is not his.

The tie-break is his, and it matches `_is_us_customary`'s: a value carrying any
technical factor is technical. Mixing systems is something an engineer does on purpose,
and the alternative silently rewrites the half they meant.
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


# --- a technical sheet stays technical ----------------------------------------------

def test_a_declared_strength_in_kgf_per_cm2_is_kept(cell):
    """He wrote it. That should have been enough before any family was consulted."""
    final = _final(cell("fc := 250*kgf/cm**2\nx = 1*fc\nnumeric(x)\n"))
    assert "250.00" in final, final
    assert KGF_CM2 in final, final
    assert "MPa" not in final, final


def test_a_strength_computed_from_technical_inputs_is_technical(cell):
    final = _final(cell("P := 25000*kgf\nA := 100*cm**2\nfc = P/A\nnumeric(fc)\n"))
    assert "250.00" in final, final
    assert KGF_CM2 in final, final


def test_a_steel_modulus_in_technical_units_never_becomes_gigapascals(cell):
    """`2100000 kgf/cm^2` is how Peru and Mexico write the steel modulus. `205.94 GPa`
    is not a number anybody on that page would recognise."""
    final = _final(cell("E := 2100000*kgf/cm**2\nx = 2*E/2\nnumeric(x)\n"))
    assert "GPa" not in final, final
    assert KGF_CM2 in final, final


def test_a_moment_from_tonnes_force_reads_in_tonnes_force(cell):
    final = _final(cell("P := 5*tonf\nL := 4*m\nM = P*L/4\nnumeric(M)\n"))
    assert r"\mathrm{tonf} \cdot \mathrm{m}" in final, final
    assert "5.00" in final, final


def test_a_line_load_in_kilogram_force_reaches_tonnes_force(cell):
    """This test asserted `3000.00 kgf` when it was written, and the code was right and
    the assertion wrong: 500 kgf stays kgf, 3000 kgf reads `3.00 tonf`, 25000 kgf reads
    `25.00 tonf`. That is the same step `N` takes to `kN`, and it is how a memoria in
    this system is written - small loads in kilogram-force, reactions in tonnes."""
    assert "500.00" in _final(cell("P := 500*kgf\nQ = 1*P\nnumeric(Q)\n"))
    final = _final(cell("w := 500*kgf/m\nL := 6*m\nR = w*L\nnumeric(R)\n"))
    assert "3.00" in final, final
    assert r"\mathrm{tonf}" in final, final


def test_mixing_the_two_chooses_the_technical_one(cell):
    """His tie-break, in his words: "si te los doy en ambos, elige kgf cm2". Sections
    in centimetres, which is what he writes them in."""
    final = _final(cell("P := 25000*kgf\nb := 10*cm\nd := 10*cm\nfc = P/(b*d)\nnumeric(fc)\n"))
    assert "250.00" in final, final
    assert KGF_CM2 in final, final
    assert "MPa" not in final, final


def test_a_section_in_millimetres_does_not_reach_kgf_per_cm2_yet(cell):
    """The one this does *not* fix, pinned rather than left in a comment.

    `25000 kgf / (100 mm x 100 mm)` reads `2.50 kgf/mm^2` where it should read
    `250.00 kgf/cm^2`. The system is detected correctly - the value is technical - but
    `_unit_is_the_engineers` never hands it to the family: `kgf/mm^2` and `kgf/cm^2`
    both cost two unit terms, so the tie keeps whatever the algebra produced.

    That is the last of the seven display findings still open in `NEXT.md`, and it is
    the same tie that keeps `GPa*mm` out of `kN/m`. Sections written in centimetres -
    which is what this engineer writes - are unaffected, so this is a remainder rather
    than a hole in what was asked for.
    """
    final = _final(cell("P := 25000*kgf\nb := 100*mm\nd := 100*mm\nfc = P/(b*d)\nnumeric(fc)\n"))
    assert "2.50" in final, final
    assert r"\mathrm{mm}" in final, final


# --- the other two systems must not move --------------------------------------------

def test_an_si_sheet_is_untouched(cell):
    assert "45.00" in _final(cell("q := 10*kN/m\nL := 6*m\nM = q*L**2/8\nnumeric(M)\n"))
    assert r"\mathrm{kN} \cdot \mathrm{m}" in _final(
        cell("q := 10*kN/m\nL := 6*m\nM = q*L**2/8\nnumeric(M)\n")
    )


def test_an_si_stress_is_untouched(cell):
    final = _final(cell("F := 250*kN\nA := 0.01*m**2\ns = F/A\nnumeric(s)\n"))
    assert r"\mathrm{MPa}" in final, final
    assert "25.00" in final, final


def test_an_imperial_sheet_is_untouched(cell):
    final = _final(cell("P := 12*kip\nd := 8*ft\nM = P*d\nnumeric(M)\n"))
    assert r"\mathrm{kip} \cdot \mathrm{ft}" in final, final


def test_a_deflection_still_reaches_millimetres(cell):
    """Lengths are not what changes. "para deflexiones generalmente es mm", and the
    magnitude rule already does that in every system."""
    final = _final(cell(
        "L := 6*m\nq := 10*kN/m\nE := 200*GPa\nI_z := 80e6*mm**4\n"
        "d = 5*q*L^4/(384*E*I_z)\nnumeric(d)\n"
    ))
    assert "10.55" in final, final
    assert r"\mathrm{mm}" in final, final
