r"""`solve(K, F)` writes each unknown as one fraction, not as the elimination that found it.

Two springs, `u = solve(K, F)`, and the page wrote the first displacement as

    (10 kN + k₂ (10 kN k₂/(k₁ + k₂) + 5 kN) / (−k₂²/(k₁ + k₂) + k₂)) / (k₁ + k₂)

and then substituted a number into every piece of that. The same displacement is
`15 kN/k₁`, which `inv(K)*F` already printed. `LUsolve` returns the steps of Gaussian
elimination unsimplified, and nothing tidied them: at six degrees of freedom the unknowns
ran to 6028 characters.

**The system is solved with `linsolve`**, which eliminates without nesting fractions, and
each unknown is factored: `5 kN (k₁ + 3 k₂)/(k₁ k₂)`. At six degrees of freedom that is
488 characters in 0.05 s. Measured against the alternatives before choosing: factoring the
LU answer takes 2.2 s there, Gauss-Jordan 36 s, and the adjugate 0.8 s to the same form.
The numbers are untouched, and a system with no single solution is refused as before.
"""

import time

import numpy as np
import pytest

import engcalc_colab.magic as magic
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell

from conftest import block_text


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str) -> tuple[str, str]:
        captured.clear()
        magic.EngMagics().eng("", source)
        raw = "".join(str(getattr(obj, "data", "")) for obj in captured)
        return raw, block_text(raw)

    return run


TWO_SPRINGS = (
    "k_1 := 2000*kN/m\nk_2 := 1500*kN/m\n"
    "K = [k_1 + k_2, -k_2; -k_2, k_2]\nF = [10*kN; 5*kN]\n"
)


def test_two_springs_read_as_the_inverse_reads(cell, capsys):
    raw, page = cell(TWO_SPRINGS + "u = solve(K, F)\n")
    capsys.readouterr()

    definition = raw.rsplit("\\\\[8pt]", 1)[-1]
    assert r"k_{2}^{2}" not in definition, definition
    assert r"\frac{15\,\mathrm{kN}}{k_{1}}" in definition, definition
    # Factored: the common `5 kN` outside, as it would be written by hand.
    assert r"\frac{5\,\mathrm{kN}\,\left(k_{1} + 3 k_{2}\right)}{k_{1} k_{2}}" in definition, definition


def test_the_numbers_do_not_move(cell, capsys):
    raw, page = cell(TWO_SPRINGS + "u = solve(K, F)\nnumeric(u)\n")
    capsys.readouterr()

    assert page.rstrip().endswith("[\\beginmatrix\\displaystyle 7.50\\\\\\displaystyle 10.83\\endmatrix] mm \\endarray"), page


def test_six_degrees_of_freedom_stay_readable():
    storeys = 6
    lines = [f"k_{i + 1} := {3000 - 300 * i}*kN/m" for i in range(storeys)]
    rows = []
    stiffness = np.zeros((storeys, storeys))
    k = [3000.0 - 300.0 * i for i in range(storeys)]
    for i in range(storeys):
        row = []
        for j in range(storeys):
            if i == j:
                row.append(f"k_{i + 1} + k_{i + 2}" if i < storeys - 1 else f"k_{i + 1}")
                stiffness[i, j] = k[i] + (k[i + 1] if i < storeys - 1 else 0.0)
            elif abs(i - j) == 1:
                row.append(f"-k_{max(i, j) + 1}")
                stiffness[i, j] = -k[max(i, j)]
            else:
                row.append("0")
        rows.append(", ".join(row))
    lines.append("K = [" + "; ".join(rows) + "]")
    lines.append("F = [" + "; ".join(f"{10 - i}*kN" for i in range(storeys)) + "]")
    lines.append("u = solve(K, F)")

    engine = EngineeringEngine()
    started = time.perf_counter()
    for statement in parse_cell("\n".join(lines) + "\n"):
        result = engine.evaluate(statement)
    elapsed = time.perf_counter() - started

    assert sum(len(str(entry)) for entry in result.value) < 1500, result.value
    assert elapsed < 10.0, elapsed


# --- what must not move ---------------------------------------------------------------


@pytest.mark.parametrize("rhs", ["[1; 2]", "[1; 3]"])
def test_a_system_without_one_solution_is_still_refused(rhs):
    """`[1, 2; 2, 4]` has a line of solutions for `[1; 2]` and none for `[1; 3]`."""
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError, match="solve matrix system requires a unique solution"):
        for statement in parse_cell(f"A = [1, 2; 2, 4]\nb = {rhs}\nsolve(A, b)\n"):
            engine.evaluate(statement)
