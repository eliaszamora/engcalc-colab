r"""What the fourth audit of the chapter 10 fixes found (2026-10-06), and the method since.

A mechanism beside masses - a chain of springs, K singular - read 10³·[0; 2.85; 6.62]
for [0; 2.32; 7.66], or crashed with "Singular matrix"; a non-symmetric pencil read 0 for
1; a repeated λ of an indefinite G read 0; a G of condition 1e11 lost an eigenvalue. Each
had been right on main. Four audits found a silent wrong λ in each heuristic tried, so
`eigenvals(K, G)` is now worked one way and checked:

- a G that inverts well, as main: G⁻¹K; a singular G taken apart exactly - with G = U S Vᵀ
  the directions where S is 0 are condensed out of K;
- each λ of a symmetric pencil polished by inverse iteration and taken only when it
  settles as an eigenvalue of K and G;
- the whole asked again with the entries moved by 1e-14, and refused when the answer moves.

The references are mpmath at 60 digits on the same matrices.
"""

import contextlib
import io
import re

import numpy as np
import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str) -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), out.getvalue()

    return run


def eigenvalues(source: str) -> list[float]:
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.parser import parse_cell

    engine = EngineeringEngine()
    for item in parse_cell(source):
        engine.evaluate(item)
    return [float(q.to_base_units().magnitude) if hasattr(q, "to_base_units") else float(q)
            for q in engine.numeric_context.matrices["l"].entries]


def written(matrix, unit="kN/m") -> str:
    return "; ".join(", ".join(f"{float(value)!r}[{unit}]" for value in row) for row in matrix)


def close(got, want, tolerance=1e-9):
    assert len(got) == len(want), (got, want)
    scale = max(abs(value) for value in want) or 1.0
    for a, b in zip(got, want):
        assert abs(a - b) <= tolerance * abs(b) + 1e-12 * scale, (got, want)


def test_a_mechanism_beside_masses(sheet):
    page, printed = sheet(
        "K := [7.3[kN/m], -7.3[kN/m], 0[kN/m]; -7.3[kN/m], 14.6[kN/m], -7.3[kN/m]; 0[kN/m], -7.3[kN/m], 7.3[kN/m]]\n"
        "M := [2[kg], 0[kg], 0[kg]; 0[kg], 3[kg], 0[kg]; 0[kg], 0[kg], 5[kg]]\nl := eigenvals(K, M)\n"
    )
    assert "engcalc:" not in printed, printed
    stiffness = 7300 * np.array([[1, -1, 0], [-1, 2, -1], [0, -1, 1.0]])
    mass = np.diag([2.0, 3, 5])
    want = sorted(np.linalg.eigvals(np.linalg.solve(mass, stiffness)).real)
    got = eigenvalues(
        "K := [7.3[kN/m], -7.3[kN/m], 0[kN/m]; -7.3[kN/m], 14.6[kN/m], -7.3[kN/m]; 0[kN/m], -7.3[kN/m], 7.3[kN/m]]\n"
        "M := [2[kg], 0[kg], 0[kg]; 0[kg], 3[kg], 0[kg]; 0[kg], 0[kg], 5[kg]]\nl := eigenvals(K, M)\n"
    )
    assert abs(got[0]) < 1e-6 and abs(got[1] - want[1]) < 1e-6 * want[1] and abs(got[2] - want[2]) < 1e-6 * want[2], (got, want)


@pytest.mark.parametrize("n", [3, 4, 5, 8])
def test_a_chain_with_a_unit_mass(n):
    stiffness = 7300.0 * (np.diag([1] + [2] * (n - 2) + [1]) - np.eye(n, k=1) - np.eye(n, k=-1))
    got = eigenvalues(f"K := [{written(stiffness / 1000)}]\nG := [{written(np.eye(n), 'kg')}]\nl := eigenvals(K, G)\n")
    want = sorted(np.linalg.eigvalsh(stiffness))
    assert abs(got[0]) < 1e-6
    close(got[1:], want[1:], 1e-9)


def test_a_non_symmetric_pencil_with_a_zero_work_vector():
    got = eigenvalues(
        "K := [0[kN/m], 1[kN/m]; 2[kN/m], 3[kN/m]]\nG := [0[kN/m], 1[kN/m]; 1[kN/m], 1[kN/m]]\nl := eigenvals(K, G)\n"
    )
    close(got, [1.0, 2.0])


def test_a_repeated_eigenvalue_of_an_indefinite_g():
    got = eigenvalues("K := [1[kN/m], 3[kN/m]; 3[kN/m], 0[kN/m]]\nG := [0[kN/m], 1[kN/m]; 1[kN/m], 0[kN/m]]\nl := eigenvals(K, G)\n")
    close(got, [3.0, 3.0])


def test_a_nearly_singular_g_keeps_both(sheet):
    g = np.array([[1, 1], [1, 1.00000001]])
    got = eigenvalues(f"K := [{written(2 * g)}]\nG := [{written(g)}]\nl := eigenvals(K, G)\n")
    close(got, [2.0, 2.0], 1e-6)
    # Nearer singular, λ = 2 moves by 1e-3 when the entries move by 1e-14: both, or refused
    # - never one of the two in silence, as the audit found.
    g = np.array([[1, 1], [1, 1.0000000001]])
    page, printed = sheet(f"K := [{written(2 * g)}]\nG := [{written(g)}]\nl := eigenvals(K, G)\n")
    if "engcalc:" not in printed:
        close(eigenvalues(f"K := [{written(2 * g)}]\nG := [{written(g)}]\nl := eigenvals(K, G)\n"), [2.0, 2.0], 1e-6)
    else:
        assert "cannot be told" in printed, printed


def test_a_g_singular_to_one_e_twelve_in_exact_arithmetic():
    # mpmath: 4.9999987e-07, 2.0000005 and 7.1e27, the last from what G holds at round-off.
    g = np.array([[2e-12, 1e-6, 0], [1e-6, 1, 1e3], [0, 1e3, 2e6]])
    got = eigenvalues(f"K := [{written(np.eye(3))}]\nG := [{written(g)}]\nl := eigenvals(K, G)\n")
    close(got, [4.9999987e-07, 2.0000005], 1e-7)


def test_a_pencil_whose_k_is_twice_its_g_is_two(sheet):
    # G = Q diag(1, 1e-13) Qᵀ with K = 2G. In floats the second λ hung on the 1e-13 and was
    # refused; K is 2G exactly in the floats too, so λ = 2 twice whatever G holds - 80
    # figures say 2.000...0001 (0.47.0, worked out in 60 figures).
    q = np.array([[np.cos(0.3), -np.sin(0.3)], [np.sin(0.3), np.cos(0.3)]])
    g = q @ np.diag([1, 1e-13]) @ q.T
    got = eigenvalues(f"K := [{written(2 * g)}]\nG := [{written(g)}]\nl := eigenvals(K, G)\n")
    close(got, [2.0, 2.0])


def test_a_free_frame_with_a_full_mass_keeps_its_rigid_zeros():
    # Two free bars in a line: two rigid-body modes, two zeros.
    k = np.array([[1, -1, 0, 0], [-1, 1, 0, 0], [0, 0, 1, -1], [0, 0, -1, 1.0]]) * 5000
    m = np.array([[2, 1, 0, 0], [1, 2, 0, 0], [0, 0, 2, 1], [0, 0, 1, 2.0]])
    got = eigenvalues(f"K := [{written(k / 1000)}]\nG := [{written(m, 'kg')}]\nl := eigenvals(K, G)\n")
    want = sorted(np.linalg.eigvals(np.linalg.solve(m, k)).real)
    assert abs(got[0]) < 1e-6 and abs(got[1]) < 1e-6, got
    close(got[2:], want[2:])
