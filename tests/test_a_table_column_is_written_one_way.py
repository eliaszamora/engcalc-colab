r"""A column of numbers is written one way, the way it wears one unit.

The engineer's beam memoria on the `kgf` palette, one column of eleven rows:

    U1(x) [kgf·cm]
        0.00
    673991.63
      1.20×10⁶
      1.57×10⁶
      1.80×10⁶
      1.87×10⁶

`673991.63` and `1.20×10⁶` are the same order of magnitude written two ways, one row
apart, and a reader comparing down the column has to stop and convert. It is the defect
`_aggregate_unit` already exists to prevent - *"one unit for a whole table column or
matrix, never one per cell"* - asked about notation instead of units.

The cause is that `_magnitude_text` answers for one value: below `_FIXED_DECIMAL_CEILING`
a fixed-decimal render, above it a power of ten. That is the right rule for a value
standing alone and the wrong one for a column, where what matters is that the rows can be
read against each other. A palette makes it common rather than rare - moments in `kgf·cm`
straddle a million on any ordinary beam - but nothing about it is new: a sheet written in
`N·mm` has always been able to do this.

So the choice is made once per column, from the values the column holds, exactly where
the unit is chosen: if any row needs the exponent, every row carries it.

Per *column* and not per table, for the same reason the unit is per column. A span in
centimetres and a moment in kgf·cm are different questions, and forcing the span into
`6.00×10²` because the moment needed an exponent would fix one column by breaking another.
"""

import re

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str, *, palette: str = "") -> str:
        captured.clear()
        if palette:
            magics.eng_units(palette)
            captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    run.objects = captured
    run.magics = magics
    return run


BEAM = (
    "L := 6.00*m\n"
    "qD := 18*kN/m\n"
    "qL := 12*kN/m\n"
    "M_D(x) = qD*x*(L - x)/2\n"
    "M_L(x) = qL*x*(L - x)/2\n"
    "case D = M_D(x)\n"
    "case Lv = M_L(x)\n"
    "combo U1 = 1.2*D + 1.6*Lv\n"
)

EXPONENT = "×10"


def _columns(page: str) -> list[list[str]]:
    rows = re.findall(r"<tr>(.*?)</tr>", page, re.S)
    cells = [re.findall(r"<td[^>]*>(.*?)</td>", row) for row in rows]
    cells = [row for row in cells if row]
    assert cells, page
    return [list(column) for column in zip(*cells)]


_SUPERSCRIPTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


def _read(cell_text: str) -> float:
    """A rendered cell back to the number it stands for, exponent and all."""
    if EXPONENT not in cell_text:
        return float(cell_text)
    mantissa, _, power = cell_text.partition(EXPONENT)
    return float(mantissa) * 10.0 ** int(power.translate(_SUPERSCRIPTS))


def test_one_column_is_not_written_two_ways(cell, capsys):
    """His page. The moment column straddles a million and must not straddle notations."""
    page = cell(BEAM + "table(U1(x), x, 0, L, 11)\n", palette="kgf")
    capsys.readouterr()

    moments = _columns(page)[1]
    with_exponent = [value for value in moments if EXPONENT in value]
    assert with_exponent, moments

    plain = [
        value
        for value in moments
        if EXPONENT not in value and float(value.replace(",", "")) != 0.0
    ]
    assert not plain, moments


def test_the_values_are_the_same_numbers_they_were(cell, capsys):
    """Choosing a notation is not choosing a different number. The mid-span moment of
    this beam is 183.60 kN·m, which is what the column has to still say in kgf·cm."""
    from engcalc_colab.numeric import engineering_registry

    units = engineering_registry()
    expected = (183.6 * units.kN * units.m).to("kgf*cm").magnitude

    page = cell(BEAM + "table(U1(x), x, 0, L, 11)\n", palette="kgf")
    capsys.readouterr()

    moments = _columns(page)[1]
    # Read back through the exponent, not the mantissa. A first draft compared mantissas
    # and failed on `6.74×10⁵`, whose mantissa is larger than `1.87×10⁶`'s and whose
    # value is a third of it - the column now spans two exponents, which is exactly what
    # it is supposed to do.
    values = [_read(value) for value in moments]
    assert max(values) == pytest.approx(float(expected), rel=5e-3), moments


def test_a_zero_stays_a_zero(cell, capsys):
    """`0.00×10⁰` is not a number anybody writes, and a zero has no exponent to take."""
    page = cell(BEAM + "table(U1(x), x, 0, L, 11)\n", palette="kgf")
    capsys.readouterr()

    moments = _columns(page)[1]
    assert moments[0] == "0.00", moments
    assert moments[-1] == "0.00", moments


def test_each_column_answers_for_itself(cell, capsys):
    """The span is in centimetres and reads perfectly well in decimals; the moment needs
    an exponent. Forcing one on the other would fix a column by breaking its neighbour."""
    page = cell(BEAM + "table(U1(x), x, 0, L, 11)\n", palette="kgf")
    capsys.readouterr()

    spans, moments = _columns(page)[0], _columns(page)[1]
    assert not any(EXPONENT in value for value in spans), spans
    assert any(EXPONENT in value for value in moments), moments


def test_two_response_columns_answer_separately(cell, capsys):
    """A loaded beam and a light purlin in one table: same unit, four orders apart.

    The variable's column is computed separately from the response columns, so the test
    above cannot tell "each column decides" from "the responses all share one answer" -
    a mutant giving every response column the same verdict survived it. A table's columns
    must share a dimension, so this is what "different" looks like: both in `kgf·cm`, one
    in the millions and one under a hundred.
    """
    page = cell(
        "L := 6.00*m\nq1 := 30*kN/m\nq2 := 2*N/m\n"
        "M1(x) = q1*x*(L - x)/2\nM2(x) = q2*x*(L - x)/2\n"
        "table(M1(x), M2(x), x, 0, L, 5)\n",
        palette="kgf",
    )
    capsys.readouterr()

    heavy, light = _columns(page)[1], _columns(page)[2]
    assert any(EXPONENT in value for value in heavy), heavy
    assert not any(EXPONENT in value for value in light), light


def test_the_variable_s_column_takes_an_exponent_when_it_needs_one(cell, capsys):
    """It is a column like any other, and nothing measured that until a mutant that
    exempted it survived. Fifteen kilometres of alignment is 1.5×10⁶ cm."""
    page = cell(
        "L := 15000*m\nq := 18*kN/m\nM(x) = q*x*(L - x)/2\ntable(M(x), x, 0, L, 4)\n",
        palette="kgf",
    )
    capsys.readouterr()

    stations = _columns(page)[0]
    assert any(EXPONENT in value for value in stations), stations
    plain = [value for value in stations if EXPONENT not in value and _read(value) != 0.0]
    assert not plain, stations


# --- what must not move ---------------------------------------------------------------


def test_a_column_that_reads_well_in_decimals_keeps_them(cell, capsys):
    """The same beam with no palette. Nothing here is near a million, and a column of
    `183.60` must not acquire exponents because one exists somewhere."""
    page = cell(BEAM + "table(U1(x), x, 0, L, 11)\n")
    capsys.readouterr()

    moments = _columns(page)[1]
    assert not any(EXPONENT in value for value in moments), moments
    assert "183.60" in moments, moments


def test_a_single_value_outside_a_table_is_unchanged(cell, capsys):
    """This is a rule about reading a column. A lone value still answers for itself."""
    page = cell(BEAM + "M_u = U1(L/2)\nnumeric(M_u)\n", palette="kgf")
    capsys.readouterr()
    assert "1.87" in page, page
