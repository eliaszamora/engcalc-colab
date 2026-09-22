r"""A squared frequency reads in `1/s²`.

The eigenvalue problem of a shear building is `K φ = ω² M φ`, and `eigenvals(inv(M)*K)`
answers with the `ω²` of each mode. With no palette a two-storey model printed

    λ = 1.65 kN/(kg·m), m = 1 ; λ = 9.10 kN/(kg·m), m = 1

`kN/(kg·m)` is a thousand `1/s²`, so both numbers are right and neither can be read
against `ω = 40.6 rad/s` without doing the conversion by hand. A single degree of freedom
had it too: `w2 = k/m` printed `4.00 kN/(m·kg)` for 4000 per second squared.

**Why.** `[time]⁻²` had no family, so - as a curvature's did until #168 - the unit the
algebra built was treated as one the engineer wrote. `[time]⁻¹` has had one since a period
and a frequency first reached a page; the square was never added. With `%eng_units kgf`
the palette already derived `1/s²`, which is why his pages never showed it.

**Fix.** `1/s²` in all three tables, the same one member `1/s` has, for the same reason:
a second is a second in every system.
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


TWO_STOREYS = (
    "k_1 := 2000*kN/m\nk_2 := 1500*kN/m\nm_1 := 500*kg\nm_2 := 400*kg\n"
    "K = [k_1 + k_2, -k_2; -k_2, k_2]\nM = diag(m_1, m_2)\n"
)


def last_row(page: str) -> str:
    return page.rsplit("\\\\[8pt]", 1)[-1]


def test_the_eigenvalues_of_a_shear_building_read_per_second_squared(cell, capsys):
    page = cell(TWO_STOREYS + "lam = eigenvals(inv(M)*K)\nnumeric(lam)\n")
    capsys.readouterr()

    numeric = last_row(page)
    assert re.findall(r"\\lambda=([\d.]+) ([^,\\]+)", numeric) == [
        ("1647.99", "1/s²"),
        ("9102.01", "1/s²"),
    ], numeric


def test_the_eigenvalues_beside_the_mode_shapes_read_per_second_squared(cell, capsys):
    """`eigenvects` writes the same eigenvalues through the same printer."""
    page = cell(TWO_STOREYS + "phi = eigenvects(inv(M)*K)\nnumeric(phi)\n")
    capsys.readouterr()

    numeric = last_row(page)
    assert re.findall(r"\\lambda=([\d.]+) ([^,\\]+)", numeric) == [
        ("1647.99", "1/s²"),
        ("9102.01", "1/s²"),
    ], numeric


def test_a_single_degree_of_freedom_reads_per_second_squared(cell, capsys):
    page = cell("k := 2000*kN/m\nm := 500*kg\nw2 = k/m\nnumeric(w2)\n")
    capsys.readouterr()

    assert last_row(page).strip().endswith("4000.00 1/s² \\endarray"), page


def test_a_sheet_in_kilogram_force_reads_per_second_squared(cell, capsys):
    """Metric-technical: `kgf/(cm·kg)` keeps its force, so the technical table is asked."""
    page = cell("k := 20000*kgf/cm\nm := 500*kg\nw2 = k/m\nnumeric(w2)\n")
    capsys.readouterr()

    # 20000 kgf/cm is 1.96e7 N/m
    assert last_row(page).strip().endswith("39226.60 1/s² \\endarray"), page


def test_a_sheet_in_us_customary_units_reads_per_second_squared(cell, capsys):
    """A US mass is written `W/g`, in `kip·s²` over a length, so the kip cancels - and
    with a stiffness per inch over a mass per foot the lengths do not, which leaves
    `ft/(in·s²)` and sends the value to the US table."""
    page = cell("k := 100*kip/inch\nm := 0.5*kip*s^2/ft\nw2 = k/m\nnumeric(w2)\n")
    capsys.readouterr()

    assert last_row(page).strip().endswith("2400.00 1/s² \\endarray"), page


# --- what must not move ---------------------------------------------------------------


def test_a_palette_still_decides(cell, capsys):
    page = cell(TWO_STOREYS + "lam = eigenvals(inv(M)*K)\nnumeric(lam)\n", palette="kgf")
    capsys.readouterr()

    assert "1647.99 1/s²" in page, page


def test_a_unit_the_engineer_asks_for_is_kept(cell, capsys):
    """`numeric(lam, unit)` names the unit. The page used to keep every eigenvalue's unit,
    asked for or not; now it keeps the one that was asked for."""
    page = cell(TWO_STOREYS + "lam = eigenvals(inv(M)*K)\nnumeric(lam, kN/(kg*m))\n")
    capsys.readouterr()

    numeric = last_row(page)
    assert re.findall(r"\\lambda=([\d.]+) ([^,\\]+)", numeric) == [
        ("1.65", "kN/(kg·m)"),
        ("9.10", "kN/(kg·m)"),
    ], numeric


def test_a_unit_asked_for_beside_the_mode_shapes_is_kept(cell, capsys):
    """The same promise through `eigenvects`, which carries its own copy of the flag."""
    page = cell(TWO_STOREYS + "phi = eigenvects(inv(M)*K)\nnumeric(phi, kN/(kg*m))\n")
    capsys.readouterr()

    numeric = last_row(page)
    assert re.findall(r"\\lambda=([\d.]+) ([^,\\]+)", numeric) == [
        ("1.65", "kN/(kg·m)"),
        ("9.10", "kN/(kg·m)"),
    ], numeric


def test_an_acceleration_is_not_a_squared_frequency(cell, capsys):
    """`m/s²` is another dimension, and the unit the engineer's own inputs build."""
    page = cell("v := 3*m/s\nt := 2*s\na = v/t\nnumeric(a)\n")
    capsys.readouterr()

    assert last_row(page).strip().endswith("1.50 m/s² \\endarray"), page


def test_a_squared_frequency_somebody_typed_is_kept(cell, capsys):
    page = cell("w2 := 1600/s^2\nnumeric(w2)\n")
    capsys.readouterr()

    assert last_row(page).strip().endswith("1600.00 1/s² \\endarray"), page
