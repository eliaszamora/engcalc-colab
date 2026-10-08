r"""`eigenvals(K, G)` worked out in 60 figures on the entries as written (0.47.0).

Seven audits of a method in floats each found a silently wrong λ, and every one was the
solver's round-off. The pencil is now solved exactly on the floats the sheet holds; three
runs, the entries moved by 1e-14 of themselves, tell what those floats do not settle.

- Two DOFs tied by a stiff spring P, `K = [1 + P, -P; -P, 1 + P]`: the soft λ = 1 is
  (1 + P) - P. The float method refused it from P = 1e10 (main printed it); it is the exact
  answer to the entries, and a move of 1e-14 - a hundred times their round-off - moves it
  by less than a tenth up to P = 1e13. At 1e14 it does not hold, and is refused.
- A G nearly singular, `G = [1, 1; 1, 1 + d]` with K = 2G: λ = 2 twice down to d = 1e-11;
  at d = 1e-13 the move of 1e-14 is d itself, and it is refused (main printed noise).
"""

import numpy as np
import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def written(matrix) -> str:
    return "; ".join(", ".join(f"{float(v)!r}[kN/m]" for v in row) for row in matrix)


def eigenvalues(stiffness, geometric) -> list[float]:
    engine = EngineeringEngine()
    for item in parse_cell(f"K := [{written(stiffness)}]\nG := [{written(geometric)}]\nl := eigenvals(K, G)\n"):
        engine.evaluate(item)
    return [float(q.magnitude) for q in engine.numeric_context.matrices["l"].entries]


@pytest.mark.parametrize("tie", [1e10, 1e11, 1e12, 1e13])
def test_two_dofs_tied_by_a_stiff_spring(tie):
    got = eigenvalues(np.array([[1 + tie, -tie], [-tie, 1 + tie]]), np.eye(2))
    assert got == [1.0, 1 + 2 * tie], got


def test_a_tie_no_float_settles_is_refused():
    tie = 1e14
    with pytest.raises(EngEvaluationError, match="cannot be told"):
        eigenvalues(np.array([[1 + tie, -tie], [-tie, 1 + tie]]), np.eye(2))


@pytest.mark.parametrize("d", [1e-9, 1e-11, 1e-12])
def test_a_nearly_singular_g_with_k_twice_it(d):
    g = np.array([[1, 1], [1, 1 + d]])
    assert eigenvalues(2 * g, g) == [2.0, 2.0]


def test_a_g_singular_to_round_off_beside_k_twice_it_is_refused():
    g = np.array([[1, 1], [1, 1 + 1e-13]])
    with pytest.raises(EngEvaluationError, match="cannot be told"):
        eigenvalues(2 * g, g)


def test_a_rotated_nearly_singular_g():
    q = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    got = eigenvalues(q @ np.diag([1, 3e-11]) @ q.T, q @ np.diag([1, 1e-11]) @ q.T)
    assert abs(got[0] - 1) <= 1e-12 and abs(got[1] - 3) <= 1e-4, got


def test_a_stiff_spring_beside_a_k_singular_to_round_off_keeps_its_eigenvalue():
    # The sixth audit's non-symmetric cluster, K with λ = 0 to round-off and a 1e14 spring on
    # one DOF. The first σ that inverted was 0, whose μ of 1e16 made the spring's μ look like a
    # zero: its λ, 9.6e13, was lost and the moved runs' copies were dropped as running off
    # (the battery of 0.47.0).
    import pathlib

    import mpmath

    from engcalc_colab.engine import EngineeringEngine

    source = (pathlib.Path(__file__).parent / "sheets" / "nonsym_cluster_spring_1e14.eng").read_text(encoding="utf-8")
    engine = EngineeringEngine()
    for item in parse_cell(source):
        engine.evaluate(item)
    got = [float(q) if not hasattr(q, "magnitude") else float(q.magnitude) for q in engine.numeric_context.matrices["l"].entries]
    def matrix(name):
        body = source.split(f"{name} := [", 1)[1].split("]", 1)[0]
        return np.array([[float(v) for v in row.split(",")] for row in body.split(";")])

    k, g = matrix("K"), matrix("G")
    with mpmath.workdps(80):
        mus = mpmath.eig(mpmath.inverse(mpmath.matrix(g.tolist())) * mpmath.matrix(k.tolist()), left=False, right=False)
        want = sorted(float(mpmath.re(x)) for x in mus)
    assert len(got) == len(want) == 10, (got, want)
    assert abs(got[-1] - want[-1]) <= 1e-9 * want[-1], (got[-1], want[-1])
    for a, b in zip(got[2:], want[2:]):
        assert abs(a - b) <= 1e-9 * abs(b), (got, want)


@pytest.mark.parametrize("angle", [31.0, 37.0])
@pytest.mark.parametrize("stiff", [1e11, 1e12, 1e14])
def test_a_round_off_eigenvalue_does_not_take_a_settled_ones_place(angle, stiff):
    # A decoupled DOF with K = stiff and G = 1, beside a G block 100 [c², cs; cs, s²] singular
    # only to round-off, whose λ (round-off over round-off) is below the decoupled one. Paired
    # smallest first, the round-off λ took the moved runs' copy of the decoupled one, which was
    # then dropped as running off, in silence (the first audit of 0.47.0).
    import math

    import mpmath

    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    block = 100.0 * np.array([[c * c, c * s], [c * s, s * s]])
    with mpmath.workdps(50):
        small = float(min(mpmath.eigsy(mpmath.matrix(block.tolist()), eigvals_only=True), key=abs))
    k_block = abs(0.3 * stiff * small)
    k = np.diag([1.0, stiff, k_block, k_block])
    g = np.zeros((4, 4))
    g[0, 0] = g[1, 1] = 1.0
    g[2:, 2:] = block
    got = eigenvalues(k, g)
    assert 1.0 in got and stiff in got, got


def test_two_round_off_eigenvalues_that_meet_by_chance_are_not_one_lost():
    # G = b bᵀ of rank 2: its two round-off directions read 5.18e14 and 5.75e14 in the moved
    # runs, within a tenth of each other, and were taken for a λ the first run lost.
    rng = np.random.default_rng(7)
    for _ in range(4):
        a = rng.normal(size=(4, 4))
        k = a @ a.T + np.eye(4)
        b = rng.normal(size=(4, 2))
        g = b @ b.T
    mu = np.linalg.eigvals(np.linalg.solve(k, g))
    want = sorted(1 / m.real for m in mu if abs(m) > 1e-9 * np.abs(mu).max())
    got = eigenvalues(k, g)
    assert len(got) == 2 and all(abs(x - y) <= 1e-6 * abs(y) for x, y in zip(got, want)), (got, want)


@pytest.mark.parametrize("spring", [1e12, 1e16, 1e22])
def test_a_complex_pair_beside_a_stiff_spring_is_refused(spring):
    # det = (2 - λ)² + 1: λ = 2 ± i. Beside a spring the best conditioned σ was huge, the μ of
    # the pair differed by 1e-30 of themselves and 2 ± i printed 2 twice (the second audit of
    # 0.47.0; main did so from 1e16).
    k = np.array([[1.0, 2, 0], [2, -1, 0], [0, 0, spring]])
    g = np.array([[0.0, 1, 0], [1, 0, 0], [0, 0, 1]])
    with pytest.raises(EngEvaluationError, match="not real"):
        eigenvalues(k, g)
    with pytest.raises(EngEvaluationError, match="not real"):
        eigenvalues(np.array([[3.0, 0.5, 0], [-0.5, 3, 0], [0, 0, spring]]), np.eye(3))


def test_a_settled_eigenvalue_45_decades_above_the_rest():
    # μ = 1e-20 / 1e25 = 1e-45 was taken for 0 and its λ for infinite (the second audit).
    got = eigenvalues(np.diag([1.0, 1, 1e25]), np.diag([1.0, -1, 1e-20]))
    assert got[:2] == [-1.0, 1.0] and len(got) == 3 and abs(got[2] - 1e45) <= 1e-12 * 1e45, got


@pytest.mark.parametrize("tiny", [1e-9, 1e-14, 1e-20])
@pytest.mark.parametrize("g_sign", [1.0, -1.0])
def test_a_mechanism_beside_a_tiny_eigenvalue_that_holds(tiny, g_sign):
    # His eigenvals(-K_g, K) has zeros beside λ of 1e-18 that hold; the moved runs' 0 read
    # 1e-16, above 1e-8 of the tiny one, and the pencil was refused (the second audit; main
    # printed 0, t, 2).
    k = np.array([[1.0, -1, 0], [-1, 1, 0], [0, 0, tiny]])
    got = eigenvalues(k, np.diag([1.0, 1, g_sign]))
    want = sorted([0.0, 2.0, tiny * g_sign])
    assert len(got) == 3 and all(abs(a - b) <= 1e-9 * abs(b) + 1e-15 * (b == 0) for a, b in zip(got, want)), got
