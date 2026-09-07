r"""A deflection of 3.95 mm printed `0.00`, because of the unit it happened to be in.

The sheet is the one every civil engineer writes:

    E := 200000*MPa
    I = b*h**3/12
    delta = P*L**3/(3*E*I)
    numeric(delta)

and the page said

    0.00 kN*m^3/(MPa*mm^4)        where the deflection is 3.95 mm

Two things are wrong and only the second is dangerous. The unit is one nobody types -
that is the `phiMn` defect of `test_derived_unit_choice.py` in another disguise, and it
is visible. The number is not: `0.00` is a plausible-looking answer to a deflection
check, and a deflection check is a comparison against a limit, so a wrong zero passes it.

**The cause.** `_display_quantity` returns early on `abs(magnitude) < zero_tolerance`,
deciding zero-ness in the unit the value is *stored* in. That rule is right and it exists
for a reason: rescaling metres to millimetres must not lift a value the engineer has
already accepted as zero back out of the band.

But `kN*m^3/(MPa*mm^4)` is not a unit anyone accepted. It is an artefact of the algebra,
and it is 10^9 times the metre, so the magnitude is 3.95e-12 and *every* deflection
smaller than about 100 mm falls under a tolerance of 1e-10. The tolerance was being
applied on a scale the arithmetic picked by accident.

**The fix has a precedent inside the same function.** The dimensionless-ratio branch sits
deliberately *above* the zero-tolerance return, and its comment says why: a ratio of
exactly zero printed `0.00 kN*m/(MPa*mm^3)`, "carrying the artefact unit in the one place
it is least defensible", and a value whose only honest scale is its own number cannot
have its zero-ness decided on any other. The same argument had never been extended to a
value that *has* a dimension, so a deflection kept being judged on a scale of 10^-9.

Zero-ness is decided in a unit the engineer would recognise: one they declared, or one
their own system uses. Anything else is converted first and judged afterwards.
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


@pytest.fixture
def loose_cell(monkeypatch):
    """A sheet whose author has said that below a millimetre is zero.

    `%eng_config zero_tolerance=0.001`. The default 1e-10 is too small for the early
    return to decide anything, so it is the only setting under which the rule that return
    exists for can be tested at all.
    """
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()
    magics.eng_config("zero_tolerance=0.001")

    def run(source: str) -> str:
        captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


DEFLECTION = (
    "E := 200000*MPa\n"
    "b := 300*mm\n"
    "h := 450*mm\n"
    "I = b*h**3/12\n"
    "L := 6*m\n"
    "P := 25*kN\n"
    "delta = P*L**3/(3*E*I)\n"
)


def test_a_deflection_reads_in_millimetres(cell):
    """P L^3 / (3 E I) = 25 kN x 216 m^3 / (3 x 200 GPa x 2.278e9 mm^4) = 3.95 mm."""
    final = _final(cell(DEFLECTION + "numeric(delta)\n"))
    assert "3.95" in final, final
    assert r"\mathrm{mm}" in final, final


def test_the_deflection_does_not_print_as_zero(cell):
    """The half that matters. A deflection check compares against a limit, and `0.00`
    passes every limit there is."""
    final = _final(cell(DEFLECTION + "numeric(delta)\n"))
    assert "0.00" not in final, final


def test_the_deflection_does_not_wear_the_unit_the_algebra_invented(cell):
    final = _final(cell(DEFLECTION + "numeric(delta)\n"))
    assert "MPa" not in final, final
    assert "kN" not in final, final


def test_a_value_the_engineer_called_zero_is_not_rescaled_until_it_shows(loose_cell):
    r"""The rule the early return exists for, which must not move.

    A tolerance of 1e-3 says: below a millimetre, this sheet calls it zero. `0.0001 m` is
    then a zero its author accepted, and `0.10 mm` is that same zero rescaled until the
    rounding shows. The unit is a family member, so the family would otherwise move it.

    **The default tolerance cannot test this, and the first draft of this file tried.**
    At 1e-10 the early return decides nothing at all: no family member is 1e10 smaller
    than another, so `_best_in_family`'s own floor - move only if the move gains a figure
    - already keeps a tiny value where it is. Both guard contracts passed with the whole
    return deleted, which is how three mutants survived and how the condition above came
    to be written with an arm that never fires.
    """
    final = _final(loose_cell("gap := 0.0001*m\nnumeric(gap)\n"))
    assert "0.00" in final, final
    assert r"\mathrm{m}" in final, final
    assert "0.10" not in final, final


def test_a_derived_zero_in_a_unit_the_reader_sees_stays_zero(loose_cell):
    """Not declared - `numeric` of a difference reaches the renderer with `declared`
    False - but metres are still what the reader sees, so the tolerance applies."""
    final = _final(loose_cell("a := 1.0001*m\nb2 := 1*m\nd = a - b2\nnumeric(d)\n"))
    assert "0.00" in final, final
    assert "0.10" not in final, final


def test_a_declared_unit_holds_its_own_zero_even_when_the_renderer_dislikes_it(
    loose_cell,
):
    """The third arm, and the only case it decides.

    `GPa*mm` is the documented artefact shape - it is what `E*t` leaves behind, and #109
    exists to send it to `kN/m`. But an engineer who *writes* `GPa*mm` has written it, and
    the rule stated at the top of `_display_quantity` is that a declared unit is kept. So
    a declared `GPa*mm` below the tolerance stays `0.00 GPa*mm` rather than becoming
    `100.00 N/m`, which is the same value shown in a unit its author did not choose.

    Found because a mutant dropping this arm survived the whole suite: neither of the
    other two arms covers a declared unit that is neither a family member nor shaped
    like one.
    """
    final = _final(loose_cell("k := 0.0001*GPa*mm\n"))
    assert r"\mathrm{GPa} \cdot \mathrm{mm}" in final, final
    assert "N" not in final.replace(r"\mathrm", ""), final


def test_the_deflection_survives_a_raised_tolerance(loose_cell):
    """The two halves together: 3.95 mm is not a zero at any tolerance this sheet would
    set, and the artefact unit must not be allowed to decide otherwise."""
    final = _final(loose_cell(DEFLECTION + "numeric(delta)\n"))
    assert "3.95" in final, final
    assert r"\mathrm{mm}" in final, final
