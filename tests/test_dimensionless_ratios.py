r"""A ratio that is physically a number must print as a number.

The external reinforced-concrete trial wrote the obvious thing:

    phiMn = phi*As*fy*z
    DC = Mu/phiMn
    numeric(DC)

and the memoria said

    9.63 x 10^-7  kN*m / (MPa*mm^3)

which is not wrong - that unit is dimensionless and its scale factor is exactly 1e6 -
but no engineer reads a demand/capacity ratio by converting kN*m to MPa*mm^3 in their
head. The answer is 0.96.

Pint keeps the compound because the two units are different symbols of the same
dimension, so nothing cancels syntactically. `Mu/phiMn` with both sides already in kN*m
cancels on its own and always printed 0.96; the defect needs the mixed units that come
from computing a capacity out of a stress and a volume, which is how anyone actually
writes it.

The rule chosen here is "dimensionless and not an angle", not "more than two unit
symbols". The second was measured against the same case in a different disguise - a
demand in N*m over a capacity in kN*m, which reduces to `newton/kilonewton`, two
symbols - and left the defect standing. Angles have to be named explicitly because Pint
calls degrees and radians dimensionless, and reducing them would turn 30 deg into 0.52.

It applies only where a unit was not declared, which is the rule the renderer already
follows for physical quantities: what the engineer typed on a `:=` line is kept, and a
computed value gets the form that reads. So `slope := 2*mm/m` keeps `mm/m` on its own
row, and a computed dimensionless value becomes a number.
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
    """The last value the reader sees in the block."""
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


SECTION = (
    "fy := 413.6854*MPa\n"
    "As := 1935.48*mm**2\n"
    "z := 394.53*mm\n"
    "phi := 0.9\n"
    "Mu := 273.7057*kN*m\n"
    "phiMn = phi*As*fy*z\n"
    "DC = Mu/phiMn\n"
)


def test_a_demand_capacity_ratio_prints_as_a_number(cell):
    """The reported defect. 273.7057 / 284.30 = 0.9627, and that is what belongs there."""
    final = _final(cell(SECTION + "numeric(DC)\n"))
    assert "0.96" in final, final
    assert "MPa" not in final and "kN" not in final, final
    assert "10^{-7}" not in final, final


def test_the_same_ratio_in_the_disguise_that_two_unit_symbols_would_have_missed(cell):
    """A demand in N*m over a capacity in kN*m reduces to `newton/kilonewton`.

    Two unit symbols, so a rule that collapsed only compounds of three or more would
    print `1000.00 N/kN` and call the defect fixed. It is the same defect.
    """
    final = _final(cell(
        "Mu := 1000*N*m\nMn := 1*kN*m\nratio = Mu/Mn\nnumeric(ratio)\n"
    ))
    assert "1.00" in final, final
    assert "N" not in final.replace(r"\displaystyle", ""), final


def test_degrees_survive(cell):
    """Pint calls a degree dimensionless. Reducing it would turn 30 deg into 0.52."""
    final = _final(cell("theta := 30*deg\nnumeric(theta)\n"))
    assert "30.00" in final and "deg" in final, final


def test_radians_survive(cell):
    final = _final(cell("alpha := 0.5*rad\nnumeric(alpha)\n"))
    assert "0.50" in final and "rad" in final, final


def test_an_angle_reached_through_arithmetic_survives(cell):
    """`declared` is about the row, not the value: this one is computed and still an angle."""
    final = _final(cell("theta := 60*deg\nhalf = theta/2\nnumeric(half)\n"))
    assert "30.00" in final and "deg" in final, final


def test_a_plain_number_is_unchanged(cell):
    """Nothing to collapse, and the existing path already handled it."""
    final = _final(cell("phi := 0.9\nnumeric(phi)\n"))
    assert "0.90" in final, final


def test_a_trig_result_is_still_a_bare_number(cell):
    """sin of an angle was already bare; the new rule must not reach it and change it."""
    final = _final(cell("theta := 30*deg\nnumeric(sin(theta))\n"))
    assert "0.50" in final, final
    assert "deg" not in final and "rad" not in final, final


def test_a_ratio_of_exactly_zero_does_not_keep_the_artefact_unit(cell):
    """Where the leftover unit is least defensible, it was surviving.

    The collapse sat below the zero-tolerance return at first, which looked like the
    careful choice: a zero is decided in its stored unit so that rescaling metres to
    millimetres cannot lift an approved zero out of the band. Measured, it printed
    `0.00 kN*m/(MPa*mm^3)` - the artefact unit, on a zero.

    That rule is about choosing between units a value could reasonably wear. A
    dimensionless value has one, its own number.
    """
    final = _final(cell(
        "c := 0*kN*m\nb := 1e13*MPa*mm**3\nexact = c/b\nnumeric(exact)\n"
    ))
    assert "0.00" in final, final
    assert "MPa" not in final and "kN" not in final, final


def test_a_ratio_below_the_tolerance_in_artefact_units_is_still_read_honestly(cell):
    """1e-13 in `kN*m/(MPa*mm^3)` is 1e-7, and 1e-7 is not zero.

    Deciding zero-ness before the collapse decides it on a scale the algebra picked by
    accident: the same value would be a zero or not depending on which units the
    capacity happened to come out in. `_magnitude_text` still applies the tolerance,
    now to the magnitude that means something.
    """
    final = _final(cell(
        "a := 1*kN*m\nb := 1e13*MPa*mm**3\ntiny = a/b\nnumeric(tiny)\n"
    ))
    assert "10^{-7}" in final, final
    assert "MPa" not in final and "kN" not in final, final


def test_a_physical_quantity_is_not_dragged_into_base_units(cell):
    """The rule must reach dimensionless values and nothing else.

    Without its dimensionality check the collapse fires on every undeclared quantity,
    and the P-3 deflection - the case the family selection exists for - prints
    `0.01 m` instead of `10.55 mm`. Nothing in the suite caught that: not the
    presentation contracts, not the matrix renderer, not the eighteen exercise answers.
    A guard being load-bearing and a guard being tested are different things, and this
    one was only the first.
    """
    final = _final(cell(
        "L := 6*m\nq := 10*kN/m\nE := 200*GPa\nI := 80e6*mm**4\n"
        "d = 5*q*L^4/(384*E*I)\nnumeric(d)\n"
    ))
    assert "10.55" in final and r"\mathrm{mm}" in final, final


def test_a_declared_ratio_keeps_the_unit_the_engineer_wrote(cell):
    """`slope := 2*mm/m` is a notation, not an accident of the algebra.

    This is what scopes the rule to undeclared values. Without it the row where the
    engineer states their own input would be rewritten under them.
    """
    latex = cell("slope := 2*mm/m\n")
    assert "2.00" in latex and r"\mathrm{mm}" in latex, latex


def test_computing_with_that_ratio_does_give_the_number(cell):
    """The visible cost of scoping by `declared`, pinned rather than left in a comment.

    `slope := 2*mm/m` shows `2.00 mm/m` on its own row and `2.00e-3` where it is
    computed. That is the same split the renderer already makes for physical
    quantities - a declared unit is kept, a computed one is made readable - so it is
    the existing model rather than a new wart, but it is a change a reader will notice
    and it should fail loudly if anyone alters it by accident.
    """
    final = _final(cell("slope := 2*mm/m\nnumeric(slope)\n"))
    assert "10^{-3}" in final, final
