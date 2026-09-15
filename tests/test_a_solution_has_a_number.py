r"""Each of several solutions carries its number.

`solve(k - w^2*m = 0, w)` has two answers, and the page printed

    w = -√(k/m)
    w =  √(k/m)

with no number beside either. A single answer can be named and passed to `numeric(...)`,
and a system defines its unknowns, which `numeric(...)` then reads; several answers can do
neither - assigning them is refused, rightly, because there is no one value to assign - so
the frequency a sheet solved for could not be seen as a frequency at all. For a two-storey
building's `det(K - ω² M) = 0` that is four formulas and no frequency.

**Each one now carries its number**, the way a characteristic point already does:
`x = L/2 (300.00 cm)`. An answer that cannot be evaluated - a name with no value, or a
complex root - is written without one, as before.
"""

import math
import re

import numpy as np
import pytest

import engcalc_colab.magic as magic

from conftest import block_text


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str) -> str:
        captured.clear()
        magic.EngMagics().eng("", source)
        return block_text("".join(str(getattr(obj, "data", "")) for obj in captured))

    return run


def numbers(page: str, unit: str) -> list[float]:
    return [float(value) for value in re.findall(r"\((-?[\d.]+) " + re.escape(unit) + r"\)", page)]


def test_a_single_degree_of_freedom_has_its_two_frequencies(cell, capsys):
    page = cell("k := 2000*kN/m\nm := 500*kg\nsolve(k - w^2*m = 0, w)\n")
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    expected = math.sqrt(2000e3 / 500)
    assert numbers(page, "1/s") == pytest.approx([-expected, expected], abs=6e-3), page


def test_a_two_storey_frequency_equation_has_its_four_roots(cell, capsys):
    page = cell(
        "k_1 := 3000*kN/m\nk_2 := 2500*kN/m\nm_1 := 600*kg\nm_2 := 550*kg\n"
        "K = [k_1 + k_2, -k_2; -k_2, k_2]\nM = diag(m_1, m_2)\n"
        "solve(det(K - w^2*M) = 0, w)\n"
    )
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    stiffness = np.array([[5500e3, -2500e3], [-2500e3, 2500e3]])
    mass = np.diag([600.0, 550.0])
    frequencies = np.sqrt(np.sort(np.linalg.eigvals(np.linalg.inv(mass) @ stiffness).real))
    assert sorted(numbers(page, "1/s")) == pytest.approx(
        sorted([-frequencies[0], frequencies[0], -frequencies[1], frequencies[1]]), abs=6e-3
    ), page


# --- what must not move ---------------------------------------------------------------


def test_a_complex_root_is_written_without_a_number(cell, capsys):
    page = cell("a := 4\nsolve(x^2 + a = 0, x)\n")
    printed = capsys.readouterr().out

    assert "engcalc:" not in printed, printed
    assert page.count("x & = &") == 2, page
    assert "(" not in page.split("x² = 0")[-1].replace("\\sqrt", ""), page


def test_a_name_with_no_value_is_written_without_a_number(cell, capsys):
    page = cell("solve(x^2 - b = 0, x)\n")
    printed = capsys.readouterr().out

    assert "engcalc:" not in printed, printed
    assert page.count("x & = &") == 2, page
    assert numbers(page, "") == [], page


def test_a_system_is_still_read_through_numeric(cell, capsys):
    """Its unknowns are defined and `numeric(R_A)` shows the working; a number beside the
    definition would say it twice."""
    page = cell(
        "L := 6*m\nq := 10*kN/m\neqFy = eq(R_A + R_B, q*L)\neqMA = eq(R_B*L, q*L*L/2)\n"
        "solve(eqFy, eqMA, R_A, R_B)\n"
    )
    capsys.readouterr()

    assert "R_B & = & \\displaystyle q L/2 \\endarray" in page, page
