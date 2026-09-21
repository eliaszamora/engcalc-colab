r"""A polynomial coefficient writes its units in the page's order, having lost its own.

Seen in Colab on the engineer's own run of 0.31.11, two lines apart in one block:

    120.00 m·kN − 20.00 kN x     for x ≤ 6.00 m
      0.00 kN·m                  otherwise

**This does not overrule the written order.**
`test_a_compound_unit_reads_in_the_order_it_was_written` settled that a value keeps the
order its factors were written in - "not 'force first' - *written* first. An engineer who
writes `mm*N` gets `mm*N`" - and `_units_in_the_page_s_order` makes a *formula's* unit
literals follow the value rather than the other way round. Both still hold, and a contract
below checks the `mm*N` case from here.

A polynomial coefficient is the one place where there is no written order left to keep.
The engineer wrote `P*(L - x)/2`, **force first**. Expanding it hands the constant term
over as `L*P/2`, because SymPy canonicalises alphabetically and `L` sorts before `P`. So
the order that reached the page was the alphabet's, not his - which is the same complaint
`_page_unit_order` was written for, in the one path it had not reached. Asking the page's
tables restores what the expansion discarded rather than inventing a second convention.

Older than 0.31.7 - it reads `m·kN` on 0.31.6 too. What changed is that 0.31.10 gave the
zero branch below it a unit, so for the first time there was a `kN·m` beside it to
disagree with. Measured across the four reference pages before the fix: 23 products of two
units written force first, and exactly one the other way - this one.
"""

import re

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")


BEAM = """L := 6*m
P := 40*kN
M_P(x) = piecewise(P*x/2, x <= L/2, P*(L - x)/2, x <= L, 0*kN*m)
numeric(M_P(x))
"""

# The same beam in technical units, so the reordering is not one table answering for all.
BEAM_KGF = """L := 600*cm
P := 4000*kgf
M_K(x) = piecewise(P*x/2, x <= L/2, P*(L - x)/2, x <= L, 0*kgf*cm)
numeric(M_K(x))
"""


@pytest.fixture
def page(monkeypatch):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def test_a_coefficient_reached_by_expanding_is_written_force_first(page):
    """The row the engineer read, and what he read it against."""
    written = page(BEAM)

    assert r"120.00\,\mathrm{kN} \cdot \mathrm{m}" in written, written
    assert r"\mathrm{m} \cdot \mathrm{kN}" not in written, written


def test_a_technical_coefficient_is_reordered_too(page):
    """`kgf·cm` comes from another table, so one table is not answering for all."""
    written = page(BEAM_KGF)

    assert r"\mathrm{kgf} \cdot \mathrm{cm}" in written, written
    assert r"\mathrm{cm} \cdot \mathrm{kgf}" not in written, written


@pytest.mark.parametrize("sheet", [BEAM, BEAM_KGF])
def test_one_page_writes_a_product_of_two_units_one_way(sheet, page):
    """Stated as the property: no page may carry both spellings of one product."""
    written = page(sheet)
    pairs = set(re.findall(r"\\mathrm\{(\w+)\} \\cdot \\mathrm\{(\w+)\}", written))

    assert not (pairs & {(right, left) for left, right in pairs}), sorted(pairs)


def test_the_whole_row_reads_as_one_thing(page):
    """The coefficient does not stand alone: the row it is in has to read right."""
    written = page(BEAM)

    assert r"120.00\,\mathrm{kN} \cdot \mathrm{m} - 20.00\,\mathrm{kN}\,x" in written, written
    assert r"0.00\,\mathrm{kN} \cdot \mathrm{m}" in written, written


# --- what must not move ---------------------------------------------------------------


def test_a_unit_the_engineer_wrote_keeps_his_order(page):
    """The rule this joins rather than competes with, checked from this side too.

    `M := 5000*mm*N` reads `mm·N`, because he wrote it that way and nothing here is
    entitled to a second opinion. See
    `test_a_compound_unit_reads_in_the_order_it_was_written`.
    """
    written = page("M := 5000*mm*N\nX = 1*M\nnumeric(X)\n")

    assert r"\mathrm{mm} \cdot \mathrm{N}" in written, written


def test_a_coefficient_with_one_unit_is_untouched(page):
    """`20.00 kN x` has a single unit, and the rule has nothing to say about it."""
    written = page(BEAM)

    assert r"20.00\,\mathrm{kN}\,x" in written, written


def test_a_line_load_coefficient_still_reads_as_a_ratio(page):
    """A fraction of units is not a product, and no table names its order."""
    written = page(
        "q1 := 8*kN/m\na_q := 3*m\nL := 6*m\n"
        "w(x) = piecewise(q1, x < a_q, 5*kN/m)\nnumeric(w(x))\n"
    )

    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in written, written
