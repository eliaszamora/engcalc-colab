r"""The same unit is the same unit, whichever order its factors came out in.

The engineer's Colab screenshot of the beam memoria, two lines apart:

    Extrema — U1(x)
    ... value = 183.60 m·kN          the extrema block
    M_u  =  183.60 kN·m              the working, and the summary

One quantity, two spellings, on one page. A reader has to stop and check whether they are
the same thing, and #104 exists precisely so a memoria does not ask that.

**The cause is a string comparison where a value comparison belongs.** `_display_quantity`
asks whether a quantity already wears one of its family's units:

    str(quantity.to(name).units) == str(quantity.units)

and Pint spells a compound unit in the order it was built, so `meter * kilonewton` and
`kilonewton * meter` are different strings. They are not different units - `a.units ==
b.units` is True - and the test says False, so the one built the other way round is not
recognised as its family's own, falls through to the factor-shape rule, and is kept
exactly as the arithmetic happened to leave it.

Nothing wrote `m·kN`. It is an accident of the order two evaluators multiply in, and
#104's rule - a compound unit keeps the order its factors were *written* in - was never
about that.

Comparing units rather than their spellings is the whole change, and its blast radius is
exactly the defect: a unit that differs from a family member by more than factor order is
still not a family member, and one that differs by nothing at all was already one.
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

    run.objects = captured
    run.magics = magics
    return run


BEAM = (
    "L := 6*m\n"
    "qD := 18*kN/m\n"
    "qL := 12*kN/m\n"
    "M_D(x) = qD*x*(L - x)/2\n"
    "M_L(x) = qL*x*(L - x)/2\n"
    "case D = M_D(x)\n"
    "case Lv = M_L(x)\n"
    "combo U1 = 1.2*D + 1.6*Lv\n"
)


def test_a_moment_built_the_other_way_round_reads_as_a_moment(cell):
    """`m·kN` is `kN·m`. Pint agrees; only the string comparison did not."""
    from engcalc_colab.numeric import engineering_registry
    from engcalc_colab.renderer import RenderSettings, _display_quantity

    units = engineering_registry()
    backwards = 183.6 * units.m * units.kN
    shown = _display_quantity(backwards, RenderSettings(), declared=False)
    assert str(shown.units) == "kilonewton * meter", str(shown.units)


def test_one_sheet_spells_it_one_way(cell):
    """The page the engineer read. The extrema block and the working must agree."""
    page = cell(BEAM + "extrema(U1(x), x, 0, L)\nM_u = U1(L/2)\nnumeric(M_u)\n")
    assert "m·kN" not in page, page
    assert r"\mathrm{m} \cdot \mathrm{kN}" not in page, page


def test_the_value_is_untouched(cell):
    page = cell(BEAM + "M_u = U1(L/2)\nnumeric(M_u)\n")
    assert "183.60" in page, page


def test_a_zero_is_spelled_the_same_way_as_the_value_beside_it(cell):
    """The two supports of the beam. `extrema` names three points and two are zero.

    The zero-tolerance return keeps a value in its stored unit so rescaling cannot lift
    an approved zero out of the band, and it was handing back the stored *spelling* with
    it. The maximum read `183.60 kN·m` and the ends read `0.00 m·kN`, six lines apart.
    """
    page = cell(BEAM + "extrema(U1(x), x, 0, L)\n")
    assert "0.00 m·kN" not in page, page
    assert "0.00 kN·m" in page, page


def test_both_ends_of_an_interval_wear_one_unit(cell):
    """A region is read by subtracting its ends, so its ends must be comparable.

    Letting a computed quantity choose the unit that says the most about itself is
    right for one value and wrong for two the reader compares: the region of a beam
    where the moment exceeds 20 kN·m came out `(763.93 mm, 5.24 m)`.
    """
    page = cell(BEAM + "solve(U1(x) > 100*kN*m, x, 0, L)\n")
    region = page[page.index("satisfies the inequality"):]
    assert "mm" not in region, region
    assert region.count(" m") >= 2, region


def test_every_coordinate_in_a_block_wears_the_domain_s_unit(cell):
    """Three roots of one beam, and the middle one is near the support.

    `Domain: 0.00 m to 6.00 m`, then `x = 0.3*m (300.00 mm)` between `0.00 m` and
    `6.00 m`. Each coordinate had chosen the unit that showed *it* best, which is the
    right rule for a value standing alone and the wrong one for three the reader is
    placing along the same beam.
    """
    page = cell(
        "L := 6*m\nq := 8*kN/m\nM(x) = q*x*(x - 0.3*m)*(L - x)\nroots(M(x), x, 0, L)\n"
    )
    block = page[page.index("Roots"):]
    assert "0.30 m" in block, block
    assert "mm" not in block, block


def test_a_governing_table_reads_in_the_unit_a_table_of_that_beam_reads_in(cell):
    """The same beam, the same variable, two blocks: they must agree.

    Two failures were measured here, in opposite directions. Choosing per row gave
    `0.00 m to 0.33 m` above `0.33 mm to 6.00 m` - one boundary, two units, one line
    apart. Choosing from every boundary at once gave `0.00 mm to 6000.00 mm`, because a
    0.33 m boundary outvotes a six-metre beam on significant figures - and `table(...)`
    of that same beam heads its column `x [m]`. The domain decides, so both blocks say
    metres.
    """
    sheet = (
        "L := 6*m\nq := 8*kN/m\nM1(x) = 40*kN*m - 100*kN*x\nM2(x) = q*x*(L-x)/2\n"
    )
    governing = cell(sheet + "governing(M1(x), M2(x), x, 0, L)\n")
    block = governing[governing.index("Governing"):]
    assert "0.33 m" in block and "6.00 m" in block, block
    assert "mm" not in block, block

    table = cell(sheet + "table(M2(x), x, 0, L, 5)\n")
    assert "x [m]" in table, table


def test_a_declared_palette_reaches_a_span(cell):
    """A sheet that says once what its units are means it for the domain too.

    The cheap way to give a span one unit is to keep the unit its first bound is stored
    in. It is also wrong: on a `kN` sheet `L := 800*mm` is 0.80 m everywhere else on the
    page, and a domain line reading `800.00 mm` would be the sheet disagreeing with its
    own declaration. The unit is chosen by the same function the tables use, which
    checks the palette before anything else.
    """
    cell.magics.eng_units("kN")
    page = cell("L := 800*mm\nq := 8*kN/m\nM(x) = q*x*(L-x)/2\nroots(M(x), x, 0, L)\n")
    block = page[page.index("Roots"):]
    assert "0.80 m" in block, block
    assert "mm" not in block, block


# --- what must not move ---------------------------------------------------------------

def test_a_unit_the_sheet_wrote_is_still_kept(cell):
    """#104 and #109 are about a unit an engineer typed, and this does not touch them:
    `tonf/m` differs from its family's member by nothing, and `GPa*mm` differs by more
    than the order of its factors."""
    page = cell("q := 2.8*tonf/m\nnumeric(q)\n")
    assert "tonf" in page, page


def test_a_pressure_times_a_length_is_still_not_a_line_load(cell):
    """#109's case. `GPa*mm` reaches force-per-length through a pressure, so it is not a
    family member however its factors are ordered, and it still reads in kN/m."""
    page = cell("E := 210*GPa\nt := 8*mm\nk = E*t\nnumeric(k)\n")
    assert "GPa" not in page.split("& = &")[-1], page
    assert r"\mathrm{kN}" in page, page


def test_a_unit_that_only_shares_a_dimension_is_not_a_family_member(cell):
    """The comparison is between units, not dimensions: a value in `N*m` is not silently
    treated as though it wore `kN*m`."""
    from engcalc_colab.numeric import engineering_registry

    units = engineering_registry()
    assert (1.0 * units.N * units.m).units != (1.0 * units.kN * units.m).units
    assert (1.0 * units.m * units.kN).units == (1.0 * units.kN * units.m).units
