r"""A zero reads in the unit of the values beside it, never in the one the algebra left.

A beam 700 mm long under 8 kN/m, on a sheet with no palette:

    Extrema — M(x)
      x = 0   (0.00 mm)   · value = 0      (0.00 kN·mm²/m)
      x = L/2 (350.00 mm) · value = qL²/8  (490.00 N·m)
      x = L   (700.00 mm) · value = 0      (0.00 kN·mm²/m)

`kN·mm²/m` is what `q*x*(L - x)` carries when `q` was typed per metre and `L` in
millimetres, and nobody writes it. The midspan value leaves it for `N·m` because it has a
magnitude to choose with; the two supports have none, and kept it.

**Why a zero kept it.** `_best_in_family` stops at a floor: when no member of the family
shows a single significant figure, moving the value "only obscures it", so `1e-6 m` stays
`1.00×10⁻⁶ m` where the engineer put it. A zero shows no figure in any unit, so it always
stopped there - and for a unit nobody wrote, *where the engineer put it* is the algebra.
The floor's own reason does not reach that case.

It is not a short-beam defect. Any sheet that types a load per metre and a length in
millimetres reaches it, in `numeric`, `report`, `summary` and every extrema block with a
zero in it; and a deflection's supports printed `0.00 kN/(m·GPa)` beside `0.0156 mm`.

**Which unit, then.** A zero has no scale, so it cannot choose for itself - and any rule
that makes it try is wrong somewhere measured here. The family's first member gives `0.00
N·m` beside `81.00 kN·m` on a six-metre beam typed in millimetres; its last gives `0.00 m`
beside `0.0156 mm`. So:

* **in a block, a zero takes the unit its neighbours are shown in** - the largest value in
  the block, which is the one the reader is comparing the zero against;
* **standing alone, the answer a table column of zeros already gets** from
  `_aggregate_unit`: the family's first member. Not a new rule, the existing one.
"""

import re

import pytest

import engcalc_colab.magic as magic

from conftest import block_text


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
        return block_text("".join(str(getattr(obj, "data", "")) for obj in captured))

    return run


# `value = <symbolic> (<number> <unit>)`, as `block_text` reads an extrema row back.
_VALUE = re.compile(r"value = [^·]*?\((-?[\d.]+) ([^)]*)\) ·")


def values(page: str) -> list[tuple[str, str]]:
    found = _VALUE.findall(page)
    assert found, page
    return found


def test_a_short_beam_writes_its_supports_in_the_moment_s_unit(cell, capsys):
    """The page this came from."""
    page = cell("L := 700*mm\nq := 8*kN/m\nM(x) = q*x*(L - x)/2\nextrema(M(x), x, 0, L)\n")
    capsys.readouterr()

    assert values(page) == [("0.00", "N·m"), ("490.00", "N·m"), ("0.00", "N·m")], page


def test_a_long_beam_in_millimetres_writes_them_in_kilonewton_metres(cell, capsys):
    """What makes it the neighbours' unit and not a fixed one. Six metres typed as
    6000 mm: the midspan reads `81.00 kN·m`, and a zero that went to the family's first
    member would read `0.00 N·m` on either side of it."""
    page = cell("L := 6000*mm\nq := 18*kN/m\nM(x) = q*x*(L - x)/2\nextrema(M(x), x, 0, L)\n")
    capsys.readouterr()

    assert values(page) == [("0.00", "kN·m"), ("81.00", "kN·m"), ("0.00", "kN·m")], page


def test_a_cantilever_writes_its_free_end_in_the_root_s_unit(cell, capsys):
    """One zero, and the value beside it is negative: the largest *magnitude* decides."""
    page = cell("L := 2500*mm\nq := 10*kN/m\nM(x) = -q*(L - x)^2/2\nextrema(M(x), x, 0, L)\n")
    capsys.readouterr()

    assert values(page) == [("-31.25", "kN·m"), ("0.00", "kN·m")], page


OVERHANG = (
    "a := 700*mm\nc := 150*mm\nq := 40*kN/m\n"
    "R_A := q*(a^2 - c^2)/(2*a)\n"
    "M(x) = piecewise(R_A*x - q*x^2/2, x <= a, -q*(a + c - x)^2/2)\n"
    "extrema(M(x), x, 0, a + c)\n"
)


def test_the_largest_value_decides_when_the_block_holds_two_units(cell, capsys):
    """An overhanging beam: `2.23 kN·m` in the span and `-450.00 N·m` over the support,
    each chosen for itself as before. The supports are read against the span, so they take
    the span's unit - and the size is compared as a moment, not as a printed number,
    since 450 is larger than 2.23 only on paper."""
    page = cell(OVERHANG)
    capsys.readouterr()

    shown = values(page)
    assert ("-450.00", "N·m") in shown, shown
    assert ("2.23", "kN·m") in shown, shown
    zeros = [unit for number, unit in shown if number == "0.00"]
    assert zeros and set(zeros) == {"kN·m"}, shown


def test_a_small_deflection_is_not_taken_for_a_zero(cell, capsys):
    """`P L³/(3 E I)` with `E` in MPa and `I` in mm⁴ carries `kN·m³/(MPa·mm⁴)`, which is
    10⁹ m, so a 1.33 mm tip deflection arrives with a magnitude of 1.33e-12 - under the
    tolerance. It is a zero only in a unit nobody reads, and giving it the block's zero
    unit would print `0.00 mm` at the tip of a cantilever."""
    page = cell(
        "L := 2*m\nP := 10*kN\nE := 25000*MPa\nI := 8e8*mm^4\n"
        "y(x) = P*x^2*(3*L - x)/(6*E*I)\n"
        "extrema(y(x), x, 0, L)\n"
    )
    capsys.readouterr()

    assert values(page) == [("0.00", "mm"), ("1.33", "mm")], page


def test_a_zero_found_numerically_is_written_the_same_way(cell, capsys):
    """A minimum no formula reaches - the `cos` puts the stationary points out of
    `solve`'s range - so the block writes `x ≈ ...` and `value ≈ ...` for it. That row is
    a separate branch, and a mutant leaving it out of this survived every other contract
    here, because every other zero on them sits at a boundary and has a formula."""
    page = cell(
        "L := 700*mm\nq := 8*kN/m\n"
        "M(x) = q*L*(x - L/3)^2*(2 + cos(3*x/L))/L\n"
        "extrema(M(x), x, 0, L)\n"
    )
    capsys.readouterr()

    assert "value ≈ 0.00 kN·m" in page, page
    assert "(1.76 kN·m)" in page, page


def test_a_deflection_writes_its_supports_in_millimetres(cell, capsys):
    """The other dimension, and the artefact that was furthest from anything written:
    `kN/(m·GPa)` beside `0.0156 mm`."""
    page = cell(
        "L := 700*mm\nq := 8*kN/m\nE := 200*GPa\nI := 8e6*mm^4\n"
        "y(x) = q*x*(L^3 - 2*L*x^2 + x^3)/(24*E*I)\n"
        "extrema(y(x), x, 0, L)\n"
    )
    capsys.readouterr()

    assert values(page) == [("0.00", "mm"), ("0.0156", "mm"), ("0.00", "mm")], page


def test_a_sheet_in_tonnes_force_writes_them_in_its_own_system(cell, capsys):
    """Metric-technical: `0.00 tonf·mm²/m` beside `122.50 kgf·m`."""
    page = cell("L := 700*mm\nq := 2*tonf/m\nM(x) = q*x*(L - x)/2\nextrema(M(x), x, 0, L)\n")
    capsys.readouterr()

    assert values(page) == [("0.00", "kgf·m"), ("122.50", "kgf·m"), ("0.00", "kgf·m")], page


def test_a_zero_standing_alone_reads_in_its_family(cell, capsys):
    """No neighbours: the family's first member, which is what `_aggregate_unit` gives a
    column of zeros. Through `numeric` and through the summary, the two places a lone
    value is written."""
    page = cell(
        "L := 700*mm\nq := 8*kN/m\n"
        "keep M_a = q*L*(L - L)/2\nnumeric(M_a)\nreport(M_a)\nsummary()\n"
    )
    capsys.readouterr()

    # `numeric`, `report`, and the summary row.
    assert page.count("0.00 N·m") == 3, page
    # A summary row reads `name = value` since test_a_computed_block_is_written_like_the_working.
    assert page.rstrip().endswith("M_a = 0.00 N·m"), page


# --- what must not move ---------------------------------------------------------------


def test_a_zero_in_the_sheet_s_own_unit_is_untouched(cell, capsys):
    """A beam typed in metres. Its supports were never wrong, and they are the case
    every sheet he has written is: the zero already wears the family's unit."""
    page = cell("L := 6*m\nqD := 18*kN/m\nM(x) = 1.2*qD*x*(L - x)/2\nextrema(M(x), x, 0, L)\n")
    capsys.readouterr()

    assert values(page) == [("0.00", "kN·m"), ("97.20", "kN·m"), ("0.00", "kN·m")], page


def test_a_zero_the_engineer_wrote_keeps_the_unit_they_wrote(cell, capsys):
    """`0*tonf*m` is a declaration: the unit is his, and a zero is no reason to take it."""
    page = cell("M_0 := 0*tonf*m\nnumeric(M_0)\n")
    capsys.readouterr()

    assert "0.00 tonf·m" in page, page


def test_a_palette_still_decides(cell, capsys):
    """`%eng_units kgf` converts before any of this is asked."""
    page = cell(
        "L := 700*mm\nq := 8*kN/m\nM(x) = q*x*(L - x)/2\nextrema(M(x), x, 0, L)\n",
        palette="kgf",
    )
    capsys.readouterr()

    assert values(page) == [("0.00", "kgf·cm"), ("4996.61", "kgf·cm"), ("0.00", "kgf·cm")], page
