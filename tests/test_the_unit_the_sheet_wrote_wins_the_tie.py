r"""A pressure times a length is not how anyone spells a force per length.

The last of the seven display findings the matrix frame analysis produced, open in
`NEXT.md` since #98 and described there as the one the term count cannot settle:

    `_unit_terms` cannot separate `GPa*mm` from `kN/m`. Both cost 2, so a force per
    length assembled from a modulus and a length is judged to be the engineer's own
    unit and kept. The same tie is what protects `kN/mm`, which *is* an engineer's
    unit and is documented as kept, so the count cannot be tightened.

Both halves of that are true, and the way out is not to count differently. It is to look
at what the factors *are*:

    kN/mm    (a force) / (a length)      an engineer's spelling
    tonf/m   (a force) / (a length)      an engineer's spelling
    kgf*cm   (a force) * (a length)      an engineer's spelling
    GPa*mm   (a PRESSURE) * (a length)   nobody's

All four are the same dimension. The three that are kept reach it through a force,
because a line load is so many newtons per metre. The one that is not reaches it through
a pressure, which is an artefact of `E*t` having been multiplied out.

So the tie is broken by the shape of the factors rather than by their number, and the
count stays exactly as it was for everything whose shape already matches.

Real values, not invented ones: `E*t` is a plate's axial stiffness per unit width and
`E*b` a beam's, and both came out in `GPa*mm`.
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


KN_PER_M = r"\frac{\mathrm{kN}}{\mathrm{m}}"


# --- the defect --------------------------------------------------------------------

def test_a_plate_stiffness_reads_as_a_stiffness(cell):
    """`210 GPa x 8 mm` is 1.68e6 kN/m, and it read `1680.00 GPa*mm` - compact, and
    meaningless."""
    final = _final(cell("E := 210*GPa\nt := 8*mm\nk = E*t\nnumeric(k)\n"))
    assert "GPa" not in final, final
    assert KN_PER_M in final, final


def test_a_beam_width_stiffness_reads_as_a_stiffness(cell):
    final = _final(cell("E := 210*GPa\nb := 300*mm\nk = E*b\nnumeric(k)\n"))
    assert "GPa" not in final, final
    assert KN_PER_M in final, final


def test_it_reaches_a_matrix_too(cell):
    final = _final(cell("E := 210*GPa\nb := 300*mm\nK = [E*b]\nnumeric(K)\n"))
    assert "GPa" not in final, final
    assert KN_PER_M in final, final


# --- the three spellings that must survive ------------------------------------------

def test_a_stiffness_in_kilonewtons_per_millimetre_is_still_kept(cell):
    """The case the tie exists to protect, and the reason the count could not simply be
    tightened. Same number of terms as `GPa*mm`, and a shape that matches."""
    final = _final(cell("k := 10*kN/mm\nx = 2*k/2\nnumeric(x)\n"))
    assert r"\frac{\mathrm{kN}}{\mathrm{mm}}" in final, final
    assert "10.00" in final, final


def test_a_line_load_in_tonnes_force_is_still_kept(cell):
    final = _final(cell("q := 2.8*tonf/m\nw = 1*q\nnumeric(w)\n"))
    assert r"\frac{\mathrm{tonf}}{\mathrm{m}}" in final, final


def test_a_moment_in_kilogram_force_centimetres_is_still_kept(cell):
    final = _final(cell("M := 5000*kgf*cm\nx = 2*M/2\nnumeric(x)\n"))
    assert r"\mathrm{kgf} \cdot \mathrm{cm}" in final, final


def test_a_matrix_of_kilonewtons_per_millimetre_is_still_kept(cell):
    final = _final(cell("k := 10*kN/mm\nA = [k, 0; 0, 2*k]\nnumeric(A)\n"))
    assert r"\frac{\mathrm{kN}}{\mathrm{mm}}" in final, final


# --- everything already right must stay right ---------------------------------------

def test_an_axial_stiffness_still_reads_in_kilonewtons_per_metre(cell):
    """Three terms, so it already lost the tie and reached the family in #94."""
    final = _final(cell("E := 210*GPa\nA := 625*mm**2\nL := 6*m\nk = E*A/L\nnumeric(k)\n"))
    assert "21875.00" in final, final
    assert KN_PER_M in final, final


def test_a_technical_sheet_is_unaffected(cell):
    final = _final(cell("P := 25000*kgf\nA := 100*cm**2\nfc = P/A\nnumeric(fc)\n"))
    assert r"\frac{\mathrm{kgf}}{\mathrm{cm}^{2}}" in final, final


def test_a_modulus_on_its_own_is_unaffected(cell):
    final = _final(cell("E := 210*GPa\nx = 2*E/2\nnumeric(x)\n"))
    assert r"\mathrm{GPa}" in final, final
    assert "210.00" in final, final


def test_an_ordinary_beam_is_unaffected(cell):
    final = _final(cell("q := 10*kN/m\nL := 6*m\nM = q*L**2/8\nnumeric(M)\n"))
    assert "45.00" in final, final
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final
