r"""`%eng_units kgf` announces its units the way the page writes them.

The engineer's Colab screenshot, the first cell of a fresh notebook on 0.30.3:

    engcalc units: kgf — 1 / s, cm, cm ** 2, cm ** 4, kg, kgf, kgf * cm, kgf / cm, kgf …

`cm ** 2`. `kgf * cm`. `1 / s`. That is Python's spelling of a unit, printed to a reader
whose whole page says `cm²`, `kgf·cm` and `1/s` - and it is the *declaration* of the
sheet's units, so it is the one line where the two spellings are guaranteed to be read
against each other.

The cause is that `_PALETTES` stores each unit as a string Pint can parse, because
`quantity.to("cm ** 2")` is what the table exists for, and `_palette_summary` printed
those strings verbatim. Pint will format a unit for a reader - `format(unit, "~P")` is
the same call the rest of the renderer makes - and it was never asked to.

It also runs off the edge of the cell. Colab gave that line a horizontal scrollbar and
cut it at `kgf …`, so the reader cannot see the palette they just declared. `kgf/cm²` is
nine characters where `kgf / cm ** 2` is thirteen, and the whole line fits.

And the order: `sorted` put `1 / s` first and `kgf/cm²` between `kgf/cm` and `s`, which
is alphabetical and means nothing to anyone. `_PALETTES` is already written in the order
an engineer would list them - length, area, second moment, force, moment, stress, line
load, mass, time, frequency - so the table's own order is the answer, and it is one less
thing written down twice.
"""

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.renderer import PALETTE_NAMES


@pytest.fixture
def printed(monkeypatch):
    lines = []
    monkeypatch.setattr(
        "builtins.print", lambda *args: lines.append(" ".join(map(str, args)))
    )
    return lines


def test_a_declared_palette_reads_the_way_the_page_reads(printed):
    magic.EngMagics().eng_units("kgf")
    line = printed[-1]
    assert "cm²" in line and "cm⁴" in line, line
    assert "kgf·cm" in line and "kgf/cm²" in line, line
    assert "1/s" in line, line


def test_no_palette_announces_python_s_spelling_of_a_unit(printed):
    """The defect stated as what must not appear, for every palette there is."""
    magics = magic.EngMagics()
    for name in PALETTE_NAMES:
        printed.clear()
        magics.eng_units(name)
        line = printed[-1]
        assert " ** " not in line, (name, line)
        assert " * " not in line, (name, line)
        assert " / " not in line, (name, line)


def test_the_line_fits_in_a_notebook_cell(printed):
    """It was cut off at `kgf …` on his screen, which is the whole line failing at the
    one job it has. Eighty characters is the width every terminal and every notebook
    output agrees on."""
    magics = magic.EngMagics()
    for name in PALETTE_NAMES:
        printed.clear()
        magics.eng_units(name)
        assert len(printed[-1]) <= 80, (len(printed[-1]), printed[-1])


def test_the_units_are_listed_in_the_table_s_own_order(printed):
    """Not alphabetical, and the difference is where a reader starts.

    `_PALETTES` is written the way an engineer lists them: the length first, then what is
    built from it, then force, moment, stress, line load, and the mass-time units last.
    Sorting the stored strings opens the line with `1 / s` and drops the length in the
    middle of it.

    The first draft of this test asserted `cm` before `cm²` and `kgf` before `kgf·cm`,
    which are true in *both* orders - alphabetical happens to agree on those three - and
    a mutant that restored `sorted` survived it. What separates the two orders is where
    the frequency goes, and whether the stress unit precedes the line load.
    """
    from engcalc_colab.renderer import palette_unit_names

    listed = list(palette_unit_names("kgf"))
    assert listed[0] == "cm", listed
    assert listed[-1] == "1/s", listed
    assert listed.index("kgf/cm²") < listed.index("kgf/cm"), listed

    assert list(palette_unit_names("kN"))[0] == "m", palette_unit_names("kN")


# --- what must not move ---------------------------------------------------------------


def test_every_unit_the_palette_fixes_is_still_named(printed):
    """The summary is read off the table so the two cannot drift, and shortening the
    spelling must not quietly shorten the list."""
    from engcalc_colab.renderer import PALETTES

    for name in PALETTE_NAMES:
        printed.clear()
        magic.EngMagics().eng_units(name)
        listed = [part.strip() for part in printed[-1].split("—", 1)[1].split(",")]
        assert len(listed) == len(set(PALETTES[name].values())), (name, listed)


def test_it_is_still_a_report_and_not_an_error(printed):
    """#127's contract, restated here because this file rewrites the line it guards."""
    magic.EngMagics().eng_units("kgf")
    assert printed[-1].startswith("engcalc units: kgf"), printed[-1]
    assert not printed[-1].startswith("engcalc: "), printed[-1]


def test_the_announcement_agrees_with_a_table_header_on_the_same_sheet(printed):
    """The property that matters, checked down two independent paths.

    A draft of this file guarded the *stored* strings instead, on the assumption that a
    pretty spelling would not parse. It parses: Pint reads `cm²`, `kgf·cm` and `kgf/cm²`
    as readily as `cm ** 2`, so a mutant that stored the pretty form survived - the
    contract was vacuous, and the thing it thought it was defending was not a property.

    What is a property: the sheet declares `kgf·cm` in its first line and a table column
    on that same sheet heads itself `[kgf·cm]`. The two are reached by different code and
    the reader reads them against each other.
    """
    import re

    from engcalc_colab.renderer import palette_unit_names

    magics = magic.EngMagics()
    magics.eng_units("kgf")
    announced = set(palette_unit_names("kgf"))

    captured = []
    magic.display = captured.append
    magics.eng(
        "",
        "L := 6*m\nq := 18*kN/m\nM(x) = q*x*(L - x)/2\ntable(M(x), x, 0, L, 3)\n",
    )
    page = "".join(getattr(obj, "data", "") for obj in captured)
    # Through the reader's view. A header carries its unit as `[$\mathrm{cm}$]` now,
    # because the table is a `Markdown` output and its units typeset - and the property
    # being checked is that the reader sees the same spelling in both places.
    from conftest import block_text

    headers = [
        unit
        for header in re.findall(r"<th[^>]*>(.*?)</th>", page)
        for unit in re.findall(r"\[(.*?)\]", block_text(header))
    ]

    assert headers, page
    for header_unit in headers:
        assert header_unit in announced, (header_unit, sorted(announced))
