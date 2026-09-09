r"""`%eng_units kN` and the whole sheet reads in kN, m, MPa — whatever was typed.

The engineer asked for this three times, and the argument that settles it is his:

    "¿cómo sabrás tú qué es secciones o deflexiones?"

It cannot be known. A span, a section depth and a deflection are the same dimension, and
every rule this renderer has for telling them apart is a guess dressed as a convention.
So: one unit per dimension, chosen up front, and where the answer is wrong for a
particular line he writes `numeric(delta, mm)` — which already shows the unit it is asked
for, and is the one thing the palette must not override.

    %eng_units kN        m, kN, MPa, kN·m, kN/m, m², m⁴, kg, s
    %eng_units kgf      cm, kgf, kgf/cm², kgf·cm, kgf/cm, cm², cm⁴, kg, s
    %eng_units           clears it; the sheet reads as it always has

What this is *not*: a system detected from what the sheet wrote. That already exists and
works - three sheets measured, kgf in and kgf out, MPa in and MPa out, both in and kgf
wins. It answers "which family", which was never the hard part. This answers "which
unit", which is where every accumulated rule lives, and answers it by decree.

The price, stated plainly because it is real and was measured before this was built: a
section written `b := 300*mm` prints `0.30 m` under the kN palette, and a deflection
prints `0.00395 m`. Neither is how anyone writes it. That is what `numeric(b, mm)` is
for, and the engineer chose this knowing it - twice, after seeing both pages.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str, units: str | None = None) -> str:
        captured.clear()
        if units is not None:
            magics.eng_units(units)
            captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def _last(latex: str) -> str:
    return latex.split(r"\\[8pt]")[-1].replace(r"\end{array}", "").strip()


# --- the palette decides, whatever was written ----------------------------------------

def test_a_section_written_in_millimetres_reads_in_metres_under_kn(cell):
    """The case the engineer named: `b = 500*mm` with kN chosen becomes metres."""
    final = _last(cell("b := 500*mm\nnumeric(b)\n", units="kN"))
    assert "0.50" in final, final
    assert r"\mathrm{m}" in final, final
    assert "mm" not in final, final


def test_a_stress_written_in_kilogram_force_reads_in_megapascals_under_kn(cell):
    final = _last(cell("fc := 250*kgf/cm**2\nnumeric(fc)\n", units="kN"))
    assert "24.52" in final, final
    assert r"\mathrm{MPa}" in final, final
    assert "kgf" not in final, final


def test_a_stress_written_in_megapascals_reads_in_kgf_per_cm2_under_kgf(cell):
    final = _last(cell("fc := 25*MPa\nnumeric(fc)\n", units="kgf"))
    assert "254.93" in final or "254.92" in final, final
    assert r"\mathrm{kgf}" in final, final
    assert "MPa" not in final, final


def test_a_length_reads_in_centimetres_under_kgf(cell):
    final = _last(cell("b := 500*mm\nnumeric(b)\n", units="kgf"))
    assert "50.00" in final, final
    assert r"\mathrm{cm}" in final, final


def test_a_force_written_in_tonf_reads_in_kilonewtons_under_kn(cell):
    final = _last(cell("P := 25*tonf\nnumeric(P)\n", units="kN"))
    assert "245.17" in final, final
    assert r"\mathrm{kN}" in final, final


def test_a_derived_quantity_follows_the_palette_too(cell):
    """Not only what was declared. `A = b*h` in mm² reads in m²."""
    final = _last(cell("b := 300*mm\nh := 450*mm\nA = b*h\nnumeric(A)\n", units="kN"))
    assert r"\mathrm{m}^{2}" in final, final
    assert "mm" not in final, final


def test_a_matrix_follows_the_palette(cell):
    """A matrix picks one unit for every cell, and the palette decides it too. This is
    the second of the two places a display unit is chosen; a palette that reached only
    scalars would leave a frame analysis half converted."""
    final = _last(cell("a := 300*mm\nb := 1200*mm\nM = [a, b; b, a]\nnumeric(M)\n", units="kN"))
    assert r"\mathrm{m}" in final, final
    assert "mm" not in final, final


# --- the escape, which the palette must not override ------------------------------------

def test_a_requested_unit_still_wins(cell):
    """`numeric(delta, mm)` is the whole answer to "I cannot know it is a deflection".
    A palette that overruled it would take away the only escape and make itself
    unusable."""
    final = _last(cell("delta := 0.00395*m\nnumeric(delta, mm)\n", units="kN"))
    assert "3.95" in final, final
    assert r"\mathrm{mm}" in final, final


# --- what must not move ---------------------------------------------------------------

def test_without_a_palette_the_sheet_reads_as_it_always_has(cell):
    """Opt-in, like `keep` and `combo` before it. Every memoria written until today has
    to render unchanged, which is the only reason this can ship at all."""
    final = _last(cell("b := 300*mm\nnumeric(b)\n"))
    assert "300.00" in final, final
    assert r"\mathrm{mm}" in final, final


def test_clearing_the_palette_restores_that(cell, monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()
    magics.eng_units("kN")
    magics.eng_units("")
    captured.clear()
    magics.eng("", "b := 300*mm\nnumeric(b)\n")
    final = _last("".join(getattr(obj, "data", "") for obj in captured))
    assert "300.00" in final, final
    assert r"\mathrm{mm}" in final, final


def test_an_unknown_palette_says_so_and_changes_nothing(cell, monkeypatch):
    printed = []
    monkeypatch.setattr("builtins.print", lambda *args: printed.append(" ".join(map(str, args))))
    magics = magic.EngMagics()
    magics.eng_units("kgf/cm2")
    assert any("kgf/cm2" in line for line in printed), printed
    assert magics.units == "", magics.units


def test_a_dimension_outside_the_palette_is_left_alone(cell):
    """An angle has no entry, and inventing one for every dimension anybody might reach
    is how a palette turns back into the rules it replaced."""
    final = _last(cell("theta := 30*deg\nnumeric(theta)\n", units="kN"))
    assert "30.00" in final, final
    assert "deg" in final, final
