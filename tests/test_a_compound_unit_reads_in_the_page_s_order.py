r"""`20*kgf*cm` read `20 cm·kgf` in its formula, one line above its own `20.00 kgf·cm`.

The last of the three spellings #104, #135 and `test_one_quantity_is_spelled_one_way`
removed from a quantity, standing on the symbolic side. Pint's alphabetical sort was
replaced in `engineering_registry` so a quantity keeps the order it was built in - a
moment is `kN·m`, `kgf·cm`, `kip·ft`, force before length, the way every code writes
it. The printer of a formula had no such rule. SymPy hands it a product's factors in its
own canonical order and `_engineering_factor_key` sorts them by name, so `kN*m` came out
right by the luck of the alphabet and every other moment came out backwards:

    20*kgf*cm   ->  20 cm·kgf
    20*tonf*m   ->  20 m·tonf
    20*N*mm     ->  20 mm·N
    20*kip*ft   ->  20 ft·kip

Found while correcting the separator between two units, and pinned there as it was.

The order cannot be the one the engineer typed: `20*kgf*cm` and `20*cm*kgf` are one
expression by the time the printer sees them. It can be the one the page uses, and the
page already says what that is - the unit tables name every compound it prints, and each
names it force first. So the units of one product are put in the order of the table's
spelling of that same unit, matched on the dimension of each factor rather than on its
name: `N*mm` matches the shape of `N * m`, and `kip*ft` the shape of `kip * ft`. A
product the tables have no spelling for keeps the order it had.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_result

from conftest import block_text


def rows(source: str) -> list[str]:
    engine = EngineeringEngine()
    written = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        written.append(render_result(engine.evaluate(item)))
    return written


def last(source: str) -> str:
    return rows(source)[-1]


@pytest.mark.parametrize(
    "source, written",
    [
        ("M = 20*kgf*cm", r"M = 20\,\mathrm{kgf} \cdot \mathrm{cm}"),
        ("M = 20*tonf*m", r"M = 20\,\mathrm{tonf} \cdot \mathrm{m}"),
        ("W = 20*N*mm", r"W = 20\,\mathrm{N} \cdot \mathrm{mm}"),
        ("M = 20*kip*ft", r"M = 20\,\mathrm{kip} \cdot \mathrm{ft}"),
    ],
)
def test_a_moment_is_written_force_first_in_every_system(source, written):
    """The four the alphabet put backwards: technical, technical, SI, US customary."""
    assert last(source) == written


def test_a_moment_written_the_other_way_round_reads_the_page_s_way():
    """The page's spelling wins over the sheet's, as it does for a quantity."""
    assert last("M = 20*cm*kgf") == r"M = 20\,\mathrm{kgf} \cdot \mathrm{cm}"


def test_the_formula_and_its_value_spell_the_moment_one_way():
    """The defect as the reader met it: two spellings of one unit, one line apart."""
    page = block_text(" ".join(rows("M_lim = 20000*kgf*cm\nnumeric(M_lim)\n")))
    assert "cm·kgf" not in page, page
    assert page.count("kgf·cm") == 2, page


def test_a_compound_numerator_is_ordered_above_the_line():
    assert last("p = 2*kgf*cm/rad") == (
        r"p = \frac{2\,\mathrm{kgf} \cdot \mathrm{cm}}{\mathrm{rad}}"
    )


# --- what must not move ---------------------------------------------------------------


@pytest.mark.parametrize(
    "source, written",
    [
        ("M = 20*kN*m", r"M = 20\,\mathrm{kN} \cdot \mathrm{m}"),
        ("c = 2*kN*m*s", r"c = 2\,\mathrm{kN} \cdot \mathrm{m} \cdot \mathrm{s}"),
        ("A = 3*m*m", r"A = 3\,\mathrm{m} \cdot \mathrm{m}"),
        ("k = 5*kN/m", r"k = \frac{5\,\mathrm{kN}}{\mathrm{m}}"),
        ("E = 2*kgf/cm^2", r"E = \frac{2\,\mathrm{kgf}}{\mathrm{cm}^{2}}"),
    ],
)
def test_what_already_read_the_page_s_way_or_has_no_spelling_is_left(source, written):
    """`kN*m` was already right. `kN*m*s` is a unit no table names, so it keeps the order
    it had rather than one this invents. `m*m` is one unit twice, and a fraction holds one
    unit on each side of the line."""
    assert last(source) == written
