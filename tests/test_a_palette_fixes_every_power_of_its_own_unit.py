r"""A declared palette fixes a length, and every power of that length follows it.

Found on the engineer's own frame memoria, in the static condensation. Three lines, one
after the other, on a sheet that had declared `%eng_units kgf`:

    C  =  -3 s_c / (2 L_c)
       =  -3 (1.00) / (2 (370.00 cm))        the working, in centimetres
       =  [-0.41  -0.41]  1/m                the answer, in reciprocal metres

`-3 / (2 x 370 cm)` is `-0.00405`, not `-0.41`. The number is right - `-0.41 1/m` *is*
`-0.00405 1/cm` - and the page is still unreadable, because a reviewer redoing the
arithmetic as written gets a different figure and nothing on the page says why.

Every unit that memoria prints was swept: 93 occurrences of `cm`, `kgf/cm`, `cm⁴`, `cm²`,
`kgf`, `1/s`, `kg` and `s` - all of them the palette's - and one `1/m`, that one.

**The table enumerates powers by hand.** `_PALETTES` names `[length]^1`, `^2` and `^4`,
which are the ones somebody needed: a length, an area, an inertia. `[length]^-1` is a
curvature - `1/r = M/EI` - and a condensation matrix; `[length]^3` is a section modulus,
`W = I/c`, as ordinary as reinforced concrete gets. Neither is in the table, so both keep
whatever system the arithmetic happened to leave them in:

    %eng_units kgf    kappa = -3/(2 L)   370.00 cm            ->  -0.41 1/m
    %eng_units kN     W = I/c            0.0054 m⁴ / 0.30 m   ->  18000.00 cm³

The second is the same defect from the other side, on the palette an SI-minded reader is
likelier to pick.

So a power of a dimension the palette names is derived rather than enumerated. The table
stays as it is: it is also the list `%eng_units` announces, and it holds the compound
units - stress, moment, line load - which are not powers of anything.
"""

import re

import matplotlib
import pytest

matplotlib.use("Agg")

import engcalc_colab.magic as magic  # noqa: E402

from conftest import block_text  # noqa: E402

# A length spelling in a unit position: the token right after a number, with the `1/` a
# reciprocal carries and whatever exponent follows. `370.00 cm`, `-0.41 1/m`,
# `18000.00 cm³`, `0.0054 m⁴`.
LENGTH_AFTER_A_NUMBER = re.compile(r"\d\s+(?:1/)?(mm|cm|m)(?![A-Za-z])")


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str, *, palette: str = "") -> str:
        magics = magic.EngMagics()
        captured.clear()
        if palette:
            magics.eng_units(palette)
            captured.clear()
        magics.eng("", source)
        page = " ".join(block_text(str(getattr(obj, "data", ""))) for obj in captured)
        assert page.strip(), [type(obj).__name__ for obj in captured]
        return page

    return run


CURVATURE = "L := 3.70*m\nkeep kappa = -3/(2*L)\nreport(kappa)\n"
MODULUS = "I := 540000*cm**4\nc := 30*cm\nkeep W = I/c\nreport(W)\n"


def test_a_curvature_reads_in_the_length_the_page_declared(cell, capsys):
    """The defect, on the block he read: `1/m` on a page whose every length is `cm`."""
    page = cell(CURVATURE, palette="kgf")
    capsys.readouterr()

    assert "1/cm" in page, page
    assert "1/m " not in page and not page.endswith("1/m"), page


def test_a_section_modulus_reads_in_the_length_the_page_declared(cell, capsys):
    """The same defect from the other side. `I/c` with both in metres came out `cm³`."""
    page = cell(MODULUS, palette="kN")
    capsys.readouterr()

    assert "m³" in page, page
    assert "cm³" not in page, page


def test_one_block_spells_its_lengths_one_way(cell, capsys):
    """The property under both, rather than two contracts naming two units: whatever
    length a block is written in, the working and the answer are written in it."""
    for sheet, palette in ((CURVATURE, "kgf"), (MODULUS, "kN"), (MODULUS, "kgf")):
        page = cell(sheet, palette=palette)
        capsys.readouterr()
        spellings = set(LENGTH_AFTER_A_NUMBER.findall(page))
        assert len(spellings) == 1, (palette, spellings, page)


def test_the_value_is_the_same_number_it_was(cell, capsys):
    """Fixing a spelling is not changing a curvature: `-3/(2 x 3.70 m)`, either way."""
    page = cell(CURVATURE, palette="kgf")
    capsys.readouterr()

    written = [float(value) for value in re.findall(r"(-\d+\.\d+)\s+1/cm", page)]
    assert written, page
    assert written[-1] == pytest.approx(-3.0 / (2 * 370.0), rel=1e-2), page


# --- what must not move ---------------------------------------------------------------


def test_the_units_the_table_names_are_untouched(cell, capsys):
    """A length, an area and an inertia are in the table by hand and must read exactly as
    they did. The derivation is a fallback, not a replacement."""
    page = cell(
        "L := 6*m\nA := 1800*cm**2\nI := 540000*cm**4\n"
        "report(L)\nreport(A)\nreport(I)\n",
        palette="kgf",
    )
    capsys.readouterr()

    assert "600.00 cm" in page, page
    assert "1800.00 cm²" in page, page
    assert "540000.00 cm⁴" in page, page


def test_a_compound_unit_is_not_a_power_of_anything(cell, capsys):
    """Stress, moment and line load are compound keys the table names outright; a
    velocity is a compound key it does not name. None of them is one dimension raised to
    a power, and the derivation must reach none of them."""
    page = cell(
        "fc := 250*kgf/cm**2\nP := 40*kN\nL := 6*m\nv0 := 2*m/s\n"
        "keep M = P*L\nreport(M)\nreport(fc)\nreport(v0)\n",
        palette="kgf",
    )
    capsys.readouterr()

    assert "kgf/cm²" in page, page
    assert "kgf·cm" in page, page
    assert "m/s" in page, page


def test_a_reciprocal_time_still_reads_as_the_table_says(cell, capsys):
    """`1/s` is in the table by hand, keyed `[time]^-1`. The derivation reaches the same
    answer, which is why an explicit entry has to keep winning: the table is also what
    `%eng_units` announces."""
    page = cell("T := 0.5*s\nkeep f = 1/T\nreport(f)\n", palette="kgf")
    capsys.readouterr()

    assert "1/s" in page, page


def test_a_fractional_power_still_renders(cell, capsys):
    """`sqrt(L)` is `[length]^0.5`, and no palette named a unit for that.

    Found by probing the edges of the derivation rather than by a report: the first draft
    rounded the exponent to zero, handed Pint `(cm) ** 0` and killed the cell with a
    `KeyError` - which the caller catches `DimensionalityError` for, so it escaped. It
    rendered perfectly well before the change and has to keep doing so.
    """
    for palette in ("kgf", "kN", ""):
        page = cell("L := 4*m\nkeep s = sqrt(L)\nreport(s)\n", palette=palette)
        capsys.readouterr()
        assert "2.00" in page or "20.00" in page, (palette, page)


def test_a_sheet_with_no_palette_is_left_alone(cell):
    """`%eng_units` is opt-in and this changes nothing about that promise."""
    page = cell(MODULUS)
    assert "cm³" in page, page


def test_the_announcement_still_lists_what_the_table_holds(cell, capsys):
    """The table is the palette's advertisement as well as its lookup, and a derived unit
    is not announced: a page may print `cm³` without `cm³` being a unit the sheet
    declared."""
    cell("L := 6*m\nreport(L)\n", palette="kgf")
    line = capsys.readouterr().out
    assert "cm, cm², cm⁴, kgf, kgf·cm, kgf/cm², kgf/cm, kg, s, 1/s" in line, line
