r"""A mass reads in kilograms, and in tonnes once it runs to five figures.

`m = P/g`, the mass of a storey from its weight, printed the units the division left:

    (12000.00 kgf)/(9.81 m/s²)   = 1223.24 kgf·s²/m
    (120.00 kN)/(9.81 m/s²)      = 12.23 kN·s²/m

**Why.** No family table held a mass, so the unit was kept as if the engineer had written
it - the cause #168 found for a curvature and #182 for a section modulus.

**Which unit, in his words.** Asked whether a mass should read in kg, t or kgf·s²/m:

    "si es un numero razonable por ejemplo 1000kg o 2500kg usar kg, pero si ya se
     extiende a 15000kg mejor pasarlo a ton 15ton"

So the family is `kg` then `t`, and the step between them is not the band every other
family uses. That band changes unit at 1000 and would print `2.50 t` for the 2500 kg he
named as kilograms. A kilogram reads up to 9999; from 10 000 the value is a tonne,
`15.00 t`. Metric-technical sheets get the same family: a weight in kgf gives a mass in kg.
A mass matrix follows the same band, and its scale is not taken outside the brackets while
the kilograms are inside it - `[2497.45, 1997.96] kg`, not `10³ [2.50, 2.00] kg` beside a
scalar `2497.45 kg`.

A palette still decides first - `%eng_units kgf` and `kN` both fix a mass in kg - and a US
customary sheet keeps its `kip·s²/ft`, which is how that system writes a mass.
"""

import pytest

import engcalc_colab.magic as magic

from conftest import block_text


def last(monkeypatch, source: str, palette: str = "") -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()
    if palette:
        magics.eng_units(palette)
        captured.clear()
    magics.eng("", source)
    text = block_text("".join(str(getattr(obj, "data", "")) for obj in captured))
    # The last row, after its `=`: a value, or a whole matrix with its unit.
    row = text.rstrip().removesuffix(r"\endarray").rsplit("& = &", 1)[-1].strip()
    return row.removeprefix(r"\displaystyle").strip()


@pytest.mark.parametrize(
    ("weight", "expected"),
    [
        ("24.5*kN", "2497.45 kg"),
        ("150*kN", "15.29 t"),
        ("1000*kgf", "999.66 kg"),
        ("15*tonf", "14.99 t"),
    ],
    ids=["si-kilograms", "si-tonnes", "technical-kilograms", "technical-tonnes"],
)
def test_the_mass_of_a_weight(monkeypatch, capsys, weight, expected):
    assert last(monkeypatch, f"P := {weight}\ng := 9.81*m/s^2\nm_1 = P/g\nnumeric(m_1)\n") == expected
    capsys.readouterr()


@pytest.mark.parametrize(
    ("each", "expected"),
    [("4999*kg", "9998.00 kg"), ("5000*kg", "10.00 t")],
    ids=["just-below", "at-the-step"],
)
def test_the_step_is_ten_thousand_kilograms(monkeypatch, capsys, each, expected):
    assert last(monkeypatch, f"m_a := {each}\nm_b = 2*m_a\nnumeric(m_b)\n") == expected
    capsys.readouterr()


def test_a_mass_matrix_of_heavy_storeys(monkeypatch, capsys):
    """The same choice for a matrix, which picks one unit for all its entries."""
    text = last(
        monkeypatch,
        "P_1 := 150*kN\nP_2 := 120*kN\ng := 9.81*m/s^2\nM = [P_1/g, 0; 0, P_2/g]\nnumeric(M)\n",
    )
    capsys.readouterr()

    assert "15.29" in text and "12.23" in text and text.endswith("t"), text


def test_a_mass_matrix_of_his_reasonable_masses_stays_in_kilograms(monkeypatch, capsys):
    """2500 kg and 2000 kg: in the kilogram band he named, where the common band says t."""
    text = last(
        monkeypatch,
        "P_1 := 24.5*kN\nP_2 := 19.6*kN\ng := 9.81*m/s^2\nM = [P_1/g, 0; 0, P_2/g]\nnumeric(M)\n",
    )
    capsys.readouterr()

    assert "2497.45" in text and text.endswith("kg"), text


# --- what must not move ---------------------------------------------------------------


def test_a_light_mass_matrix_stays_in_kilograms(monkeypatch, capsys):
    text = last(monkeypatch, "m_1 := 500*kg\nm_2 := 400*kg\nM = [m_1, 0; 0, m_2]\nnumeric(M)\n")
    capsys.readouterr()

    assert "500.00" in text and text.endswith("kg"), text


def test_a_palette_still_decides(monkeypatch, capsys):
    assert last(monkeypatch, "P := 150*kN\ng := 9.81*m/s^2\nm_1 = P/g\nnumeric(m_1)\n", palette="kgf") == "15290.52 kg"
    capsys.readouterr()


def test_a_us_customary_mass_keeps_its_system(monkeypatch, capsys):
    text = last(monkeypatch, "P := 10*kip\ng := 32.2*ft/s^2\nm_1 = P/g\nnumeric(m_1)\n")
    capsys.readouterr()

    assert "kip" in text and "kg" not in text, text


def test_a_frequency_from_a_mass_is_unchanged(monkeypatch, capsys):
    assert last(monkeypatch, "k := 2000*kN/m\nm := 500*kg\nw_n = sqrt(k/m)\nnumeric(w_n)\n") == "63.25 1/s"
    capsys.readouterr()
