r"""`MN` is a unit an engineer writes, so it is one this language accepts.

`_UNIT_ALIASES` is a deliberate whitelist - "a table of the spellings an engineer writes,
not a set of definitions" - and it gives pressure four steps and force two:

    pressure   Pa, kPa, MPa, GPa
    force      N, kN

A bridge reaction is written in meganewtons, and both ways of saying so failed:

    P := 12*MN            unknown numeric name 'MN'. Define the numeric value first...
    numeric(M, MN*m)      unknown target unit 'MN'

The first message is the worse one: it reads the unit as a variable the engineer forgot
to define, and tells them to define it.

**This is not a reversal of #99.** That release took mega out of `_UNIT_FAMILIES`, which
is the table of units the system *chooses*, because the engineer asked for a sheet that
stays in kilonewtons rather than mixing kilo and mega. `_UNIT_ALIASES` is the table of
units the engineer may *write*. Those are different questions, and only the second is
answered here - the guards below pin the first, unchanged.

Found while testing #106: making `numeric(expr, unit)` honour a requested unit turned
this from an unreachable corner into a visible edge.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> str:
        captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


BEAM = "q := 10*kN/m\nL := 6*m\n"


# --- what the engineer may write ----------------------------------------------------

def test_a_force_can_be_declared_in_meganewtons(cell):
    latex = cell("P := 12*MN\n")
    assert "12.00" in latex, latex
    assert r"\mathrm{MN}" in latex, latex


def test_a_moment_can_be_requested_in_meganewton_metres(cell):
    final = _final(cell(BEAM + "M = q*L**2/8\nnumeric(M, MN*m)\n"))
    assert r"\mathrm{MN} \cdot \mathrm{m}" in final, final
    assert "0.045" in final or "0.05" in final, final


def test_a_declared_meganewton_survives_into_arithmetic(cell):
    """It was written, so it is kept - the same rule that keeps `tonf`."""
    final = _final(cell("P := 12*MN\nR = 2*P\nnumeric(R)\n"))
    assert "24.00" in final, final
    assert r"\mathrm{MN}" in final, final


# --- what the system still never chooses --------------------------------------------

def test_a_large_computed_force_still_stays_in_kilonewtons(cell):
    """#99's rule, and the reason for it in the engineer's own words: *"no me gusta que
    hayan algunos en kilo y otros en mega"*. Nothing here puts mega back in the family."""
    final = _final(cell("F := 209670*kN\nG = 1*F\nnumeric(G)\n"))
    assert "209670.00" in final, final
    assert r"\mathrm{kN}" in final, final
    assert "MN" not in final, final


def test_a_stiffness_assembled_from_kilonewtons_stays_there(cell):
    final = _final(cell(
        "E := 210*GPa\nA := 625*mm**2\nL := 6*m\nk = E*A/L\nnumeric(k)\n"
    ))
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in final, final
    assert "MN" not in final, final


def test_a_matrix_still_takes_its_scale_outside_rather_than_going_to_mega(cell):
    final = _final(cell(
        "E := 210*GPa\nb := 300*mm\nd := 450*mm\nh := 3.70*m\nkeep I_c = b*d**3/12\n"
        "K = [4*E*I_c/h, 6*E*I_c/h**2; 6*E*I_c/h**2, 12*E*I_c/h**3]\nnumeric(K)\n"
    ))
    assert "10^{3}" in final, final
    assert "MN" not in final, final


def test_the_ordinary_force_units_are_unchanged(cell):
    assert "10.00" in _final(cell("F := 10*N\nG = 1*F\nnumeric(G)\n"))
    assert "45.00" in _final(cell(BEAM + "M = q*L**2/8\nnumeric(M)\n"))
