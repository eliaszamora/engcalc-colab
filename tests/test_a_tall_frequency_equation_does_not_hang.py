r"""The frequency equation of a building of three storeys does not hang the cell.

`det(K - ω² M) = 0` is how a textbook finds the frequencies of a small building by hand.
For two storeys it works in EngCalc: `roots(det(K - w^2*M), w, 0/s, 200/s)` finds
`43.92 1/s` and `108.55 1/s`. For three storeys the equation is of degree six in `ω`, a
cubic in `ω²`, and both ways of asking for its roots never came back:

    roots(det(K - w^2*M), w, 0/s, 300/s)     no answer after ten minutes
    solve(det(K - w^2*M) = 0, w)             no answer after ninety seconds

**Why.** Both hand the polynomial to SymPy's exact solver, which decomposes a cubic in
`ω²` whose coefficients are six names and expands Cardano's formula - the one that writes
three real roots through complex numbers - until the notebook is killed. It was sampled
there: `solveset` → `roots` → `_try_decompose` → `expand`.

**So a polynomial of degree five or more in the unknown, with other names in its
coefficients, is not solved in closed form.** Abel and Ruffini say there is none in
general, and where one exists it is not a formula anyone reads. `roots` goes straight to
the numeric search it already falls back to, and `solve` says why it will not and what to
write instead. A quartic keeps its closed form - the two-storey page does not move - and a
polynomial with plain numbers for coefficients is left to SymPy as before.
"""

import re
import time

import numpy as np
import pytest

import engcalc_colab.magic as magic

from conftest import block_text


def building(storeys: int):
    """A shear building's sheet, and its stiffness and mass matrices in SI for numpy."""
    k = [3000.0 - 500.0 * i for i in range(storeys)]
    m = [600.0 - 50.0 * i for i in range(storeys)]
    lines = [f"k_{i + 1} := {k[i]:g}*kN/m" for i in range(storeys)]
    lines += [f"m_{i + 1} := {m[i]:g}*kg" for i in range(storeys)]
    rows = []
    stiffness = np.zeros((storeys, storeys))
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
    lines.append("M = diag(" + ", ".join(f"m_{i + 1}" for i in range(storeys)) + ")")
    return "\n".join(lines) + "\n", stiffness * 1000.0, np.diag(m)


def reference(stiffness, mass):
    values = np.linalg.eigvals(np.linalg.inv(mass) @ stiffness)
    return np.sort(values.real), None


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str) -> str:
        captured.clear()
        magic.EngMagics().eng("", source)
        return block_text("".join(str(getattr(obj, "data", "")) for obj in captured))

    return run


def test_three_storeys_have_three_frequencies(cell, capsys):
    sheet, stiffness, mass = building(3)
    started = time.perf_counter()
    page = cell(sheet + "roots(det(K - w^2*M), w, 0/s, 300/s)\n")
    elapsed = time.perf_counter() - started
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    expected, _ = reference(stiffness, mass)
    found = [float(value) for value in re.findall(r"w ≈ ([\d.]+) 1/s · root", page)]
    assert found == pytest.approx(np.sqrt(expected), abs=6e-3), page
    assert elapsed < 20.0, elapsed


def test_solve_says_why_and_what_to_write(cell, capsys):
    sheet, _, _ = building(3)
    started = time.perf_counter()
    cell(sheet + "solve(det(K - w^2*M) = 0, w)\n")
    elapsed = time.perf_counter() - started
    printed = capsys.readouterr().out

    assert "degree 6" in printed, printed
    assert "roots(" in printed and "eigenvals(" in printed, printed
    assert elapsed < 10.0, elapsed


# --- what must not move ---------------------------------------------------------------


def test_two_storeys_keep_their_closed_form(cell, capsys):
    sheet, stiffness, mass = building(2)
    page = cell(sheet + "roots(det(K - w^2*M), w, 0/s, 200/s)\n")
    capsys.readouterr()

    expected, _ = reference(stiffness, mass)
    assert r"w = \dfrac\sqrt2" in page, page  # `\dfrac` since the block reads at the page's size (test_a_characteristic_block_reads_at_the_page_s_size).
    for value in np.sqrt(expected):
        assert f"({value:.2f} 1/s) · root" in page, page


def test_solve_still_answers_the_factor_it_can(cell, capsys):
    """`solve` refuses only when nothing in the polynomial has a closed form. Here `a` is a
    root anyone can read, and the page answered it before; it still does."""
    page = cell("a := 0\nb := -1\nsolve((x - a)*(x^5 + b*x + 1) = 0, x)\n")
    printed = capsys.readouterr().out

    assert "engcalc:" not in printed, printed
    assert page.rstrip().endswith("& & \\displaystyle a \\endarray"), page


def test_a_quintic_factor_of_plain_numbers_keeps_its_exact_root():
    """Setting aside is decided factor by factor. `x⁵ - x - 1` has no names in it, and
    SymPy answers it exactly with `CRootOf`, beside the names-bearing factor `x - a`."""
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.parser import parse_cell

    engine = EngineeringEngine()
    for statement in parse_cell("a := 0\nf(x) = (x - a)*(x^5 - x - 1)\nroots(f(x), x, -2, 2)\n"):
        result = engine.evaluate(statement)

    assert [point.provenance for point in result.points] == ["exact", "exact"]
    assert "CRootOf" in str(result.points[1].x_symbolic)


def test_a_polynomial_of_plain_numbers_is_left_to_sympy(cell, capsys):
    page = cell("roots(x^6 - 2*x^2 + 0.5, x, 0, 2)\nsolve(x^5 - 1 = 0, x)\n")
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    assert "x = 0.51 (0.51) · root" in page, page
