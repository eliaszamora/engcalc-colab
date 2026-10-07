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
