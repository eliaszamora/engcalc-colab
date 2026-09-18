r"""`20*kN*m` on a working line read `20 kN m`, where its own result reads `20.00 kN·m`.

Found by rendering the reference pages on 0.31.3 and reading them, while looking at why
an inequality's limit came out that way in its heading.

The symbolic printer sets a unit apart from what it multiplies with a thin space, which
is right for a number meeting a unit - `10\,\mathrm{kN}`, without which the engineer's
load vector read `10kN`. It applied the same space between two *units*, and there the
page already has a spelling: every quantity Pint prints goes through `format(unit, "~L")`
and comes out `\mathrm{kN} \cdot \mathrm{m}`. So one unit was spelled two ways on one
page, which is the defect #135 and #104 exist to keep out.

`m*m` is the sharp end of it. It rendered `3\,\mathrm{m}\,\mathrm{m}`: two metres and a
thin space between them, a hair from `3 mm` on the page. A reader has no way to tell
which was meant, and the two differ by a factor of a thousand.
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


def test_two_units_multiplied_are_joined_the_way_the_page_joins_them():
    assert last("M_lim = 20*kN*m") == r"M_{lim} = 20\,\mathrm{kN} \cdot \mathrm{m}"


def test_the_formula_and_its_value_spell_one_unit_one_way():
    """The whole point. Two lines of one sheet may not disagree about a unit."""
    page = " ".join(rows("M_lim = 20*kN*m\nnumeric(M_lim)\n"))
    assert block_text(page).count("kN·m") == 2, block_text(page)


def test_a_unit_written_twice_cannot_be_read_as_the_prefixed_one():
    """`3 m m` and `3 mm` differ by a thousand and looked the same."""
    written = last("A_lim = 3*m*m")
    assert written == r"A_{lim} = 3\,\mathrm{m} \cdot \mathrm{m}"
    assert r"\mathrm{m}\,\mathrm{m}" not in written


def test_a_number_is_still_only_spaced_from_its_unit():
    """The space between a number and a unit is what stops `10kN`, and it stays a space.

    A centred dot there would read as a multiplication the engineer did not write.
    """
    assert last("F = 10*kN") == r"F = 10\,\mathrm{kN}"


def test_three_units_are_joined_at_every_step():
    """Asserted because joining only the last pair passes a two-unit contract."""
    assert last("c = 2*kN*m*s") == r"c = 2\,\mathrm{kN} \cdot \mathrm{m} \cdot \mathrm{s}"


def test_a_unit_under_the_line_is_untouched():
    """`kN/m` is a fraction, and its numerator and denominator each hold one unit."""
    assert last("q = 5*kN/m") == r"q = \frac{5\,\mathrm{kN}}{\mathrm{m}}"


def test_a_compound_numerator_over_a_unit_joins_above_the_line():
    assert last("p = 2*kN*m/rad") == (
        r"p = \frac{2\,\mathrm{kN} \cdot \mathrm{m}}{\mathrm{rad}}"
    )


def test_a_power_of_one_unit_is_left_as_a_power():
    """`m^2` is one factor, not two, and nothing here should make it two."""
    assert last("A = 3*m^2") == r"A = 3\,\mathrm{m}^{2}"
    assert last("I = 4*cm^4") == r"I = 4\,\mathrm{cm}^{4}"


def test_two_names_that_are_not_units_keep_the_ordinary_product():
    """The change is about units meeting units, and must not reach anything else.

    `b h` is a product of two lengths the engineer named; setting a dot between them
    would be this file overreaching into how the working writes algebra.
    """
    written = last("b := 30*cm\nh := 60*cm\nS = b*h*kgf")
    assert written == r"S = b h\,\mathrm{kgf}"


@pytest.mark.parametrize(
    "source, unit",
    [
        ("M = 20*kgf*cm", r"\mathrm{kgf} \cdot \mathrm{cm}"),
        ("M = 20*tonf*m", r"\mathrm{tonf} \cdot \mathrm{m}"),
        ("W = 20*N*mm", r"\mathrm{N} \cdot \mathrm{mm}"),
    ],
)
def test_every_palette_spells_its_moment_the_same_way(source, unit):
    """The three the engineer switches between, so no palette is left on the old spelling.

    These came back `cm · kgf`, `m · tonf` and `mm · N` when this file was written - the
    order was SymPy's, alphabetical, and `kN*m` read the right way round by the luck of
    the alphabet - and were pinned that way so the correction would have to come back
    and say so. It did: see `test_a_compound_unit_reads_in_the_page_s_order.py`.
    """
    assert last(source).endswith(unit)
