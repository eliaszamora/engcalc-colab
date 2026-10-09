r"""`eigenvals(K, G)` worked out exactly on the entries as written (0.47.0).

Seven audits of a method in floats each found a silently wrong λ, and every one was the
solver's round-off. The pencil is now solved in 80 figures on the floats the sheet holds, and
each λ's sensitivity to a change of 1e-15 in every entry - from its left and right vectors -
tells what those floats do not settle. (A first way of telling it, the same λ asked again on
entries moved by 1e-14, was misjudged by four audits; several contracts below come from them.)

- Two DOFs tied by a stiff spring P, `K = [1 + P, -P; -P, 1 + P]`: the soft λ = 1 is
  (1 + P) - P. The float method refused it from P = 1e10 (main printed it); it is the exact
  answer to the entries, and a move of 1e-14 - a hundred times their round-off - moves it
  by 2% up to P = 1e13, and at 1e14 by 20% - negligible beside the tie's 2e14, printed as main.
- A G nearly singular, `G = [1, 1; 1, 1 + d]` with K = 2G: λ = 2 twice down to d = 1e-12;
  at d = 1e-13 the pair moves by more than 3% and is refused (main printed noise).
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


def test_a_tie_of_1e14_prints_its_soft_eigenvalue_as_main():
    # λ = 1 moves by 20% under a change of 1e-15 in the entries - more than a printed λ may -
    # but beside the tie's 2e14 it is negligible, and one figure of it holds: as main printed it.
    # Written in kN/m and stored in N/m, the entries round: the exact answer to them is 0.992.
    tie = 1e14
    got = eigenvalues(np.array([[1 + tie, -tie], [-tie, 1 + tie]]), np.eye(2))
    assert abs(got[0] - 1.0) <= 0.2 and got[1] == 1 + 2 * tie, got


@pytest.mark.parametrize("d", [1e-9, 1e-11, 1e-12])
def test_a_nearly_singular_g_with_k_twice_it(d):
    g = np.array([[1, 1], [1, 1 + d]])
    assert eigenvalues(2 * g, g) == [2.0, 2.0]


def test_a_g_singular_to_round_off_beside_k_twice_it_is_refused():
    # K = 2G exactly in the floats, λ = 2 twice; the second hangs on G's 1e-13, and the pair,
    # worked out again on entries moved by 1e-15, moves by more than the 3% a printed λ may.
    g = np.array([[1, 1], [1, 1 + 1e-13]])
    with pytest.raises(EngEvaluationError, match="cannot be told"):
        eigenvalues(2 * g, g)


def test_a_rotated_nearly_singular_g():
    q = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    got = eigenvalues(q @ np.diag([1, 3e-11]) @ q.T, q @ np.diag([1, 1e-11]) @ q.T)
    assert abs(got[0] - 1) <= 1e-12 and abs(got[1] - 3) <= 1e-4, got


def test_a_pencil_that_is_not_symmetric_is_worked_out_as_main():
    # Follower loads, not a frame's stiffness: the exact way is for symmetric pencils (a last-bit
    # difference from tᵀkt being round-off). A non-symmetric one is G⁻¹K as main works it, and a
    # singular G is refused as main refuses it (the fifth audit of 0.47.0 found the first-order
    # sensitivity of a nearly defective non-symmetric λ to be no measure at all).
    k = np.array([[3.0, 1.0], [0.0, 2.0]])
    assert eigenvalues(k, np.eye(2)) == [2.0, 3.0]
    with pytest.raises(EngEvaluationError, match="second matrix is singular"):
        eigenvalues(k, np.diag([1.0, 0.0]))


def test_a_last_bit_asymmetry_is_symmetric():
    # tᵀkt leaves K[3,2] one bit off K[2,3]: a ring's double of 66668.09 lost in silence (the
    # fifth audit of 0.47.0); symmetric to its round-off, it is worked out as symmetric.
    k = 202671.0 * np.eye(4)
    for i in range(4):
        k[i, (i + 1) % 4] = k[(i + 1) % 4, i] = -96510.0
    k[3, 2] = -96509.99999999999
    got = eigenvalues(k, 3.04 * np.eye(4))
    with __import__("mpmath").workdps(60):
        import mpmath

        symmetric = (k + k.T) / 2
        want = sorted(float(v) for v in mpmath.eigsy(mpmath.matrix((symmetric / 3.04).tolist()), eigvals_only=True))
    assert len(got) == 4 and all(abs(a - b) <= 1e-9 * abs(b) for a, b in zip(got, want)), (got, want)


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


def test_a_soft_mode_the_floats_do_not_settle_is_not_a_zero():
    # A portal whose beam is a link of EA = 1e17: ω² = 3.79 reads about ±4 when the entries move
    # by 1e-14 - no mechanism, a λ the floats do not hold. Counted as a 0 within 1e-12 of the
    # largest, it was printed 0 (the battery of 0.47.0); it is refused.
    import pathlib

    from engcalc_colab.engine import EngineeringEngine

    source = (pathlib.Path(__file__).parent / "sheets" / "portal_link_1e17_soft_mode.eng").read_text(encoding="utf-8")
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError, match="cannot be told"):
        for item in parse_cell(source):
            engine.evaluate(item)


def _sheet_eigenvalues(name: str) -> list[float]:
    import pathlib

    from engcalc_colab.engine import EngineeringEngine

    source = (pathlib.Path(__file__).parent / "sheets" / name).read_text(encoding="utf-8")
    engine = EngineeringEngine()
    for item in parse_cell(source):
        engine.evaluate(item)
    return [float(q.magnitude) if hasattr(q, "magnitude") else float(q) for q in engine.numeric_context.matrices["l"].entries]


def _exact(name: str) -> list[float]:
    import pathlib

    import mpmath

    source = (pathlib.Path(__file__).parent / "sheets" / name).read_text(encoding="utf-8")

    def matrix(label):
        body = source.split(f"{label} := [", 1)[1].split("]", 1)[0]
        return [[float(v) for v in row.split(",")] for row in body.split(";")]

    with mpmath.workdps(90):
        values = mpmath.eig(mpmath.inverse(mpmath.matrix(matrix("G"))) * mpmath.matrix(matrix("K")), left=False, right=False)
        return sorted(float(mpmath.re(v)) for v in values)


@pytest.mark.parametrize(
    "name",
    ["frame_minus_kg_k_tiny_and_zero.eng", "frame_minus_kg_k_nonsymmetric.eng", "free_frame_k_m_nonsymmetric.eng"],
)
def test_his_frames_print_as_main(name):
    # Frames assembled with tᵀkt - inclined columns, beam forces of 1e-11, non-symmetric by an
    # ulp - in his eigenvals(-K_g, K), and a free frame's eigenvals(K, M): the runs on moved
    # entries refused them, where main printed them right (the fourth audit of 0.47.0).
    got = _sheet_eigenvalues(name)
    want = _exact(name)
    scale = max(abs(v) for v in want)
    assert len(got) == len(want), (got, want)
    for a, b in zip(got, want):
        assert abs(a - b) <= 1e-6 * abs(b) + 1e-12 * scale, (got, want)


def test_a_spectrum_of_55_decades_keeps_every_eigenvalue():
    # μ of 1e15 below a floor of 1e-52 against ‖L⁻¹‖² of 1e40: lost (the fourth audit).
    got = eigenvalues(np.diag([1e-40, 1e15, 1.0]), np.diag([1.0, 1, -1]))
    assert got == [-1.0, 1e-40, 1e15], got


def test_a_follower_load_beside_a_support_spring_is_not_symmetrized():
    # Beck's column under a follower load of 1.5e5, its base a 1e18 spring: against K's largest
    # entry the asymmetry passed for round-off, the pencil was symmetrized and a negative ω²
    # was printed (the sixth audit of 0.47.0). Each pair against its own scale: G⁻¹K, exactly.
    got = _sheet_eigenvalues("beck_follower_on_springs_1e18.eng")
    want = _exact("beck_follower_on_springs_1e18.eng")
    assert all(value > 0 for value in got), got
    for a, b in zip(got[:8], want[:8]):
        assert abs(a - b) <= 1e-9 * abs(b), (got, want)
    assert eigenvalues(np.array([[1e16, 0, 0], [0, 2.0, 1.5], [0, 0.1, 3.0]]), np.eye(3))[:2] == pytest.approx(
        [1.867544468, 3.132455532], rel=1e-9
    )


def test_storeys_on_springs_keep_their_critical_loads():
    # eigenvals(K, K_g) of a frame on 1e20 springs: G's two round-off directions gave a pair of
    # λ of 7e28; measured as a pair at 93% they were refused, where they are infinite (the
    # battery of 0.47.0). The ten critical load factors print.
    got = _sheet_eigenvalues("storeys_on_springs_1e20_k_kg.eng")
    assert len(got) == 10 and abs(got[0] - 63.5274) <= 1e-4, got


def test_a_round_off_direction_of_g_below_zero_is_counted():
    # The block 100 [c², cs; cs, s²] at 29°: its round-off eigenvalue is negative. Scaled by its
    # diagonal in floats the round-off was lost, the direction was not counted, and a pencil
    # whose λ the floats settle was refused (the battery of 0.47.0).
    import math

    import mpmath

    c, s = math.cos(math.radians(29.0)), math.sin(math.radians(29.0))
    block = 100.0 * np.array([[c * c, c * s], [c * s, s * s]])
    with mpmath.workdps(50):
        small = float(min(mpmath.eigsy(mpmath.matrix(block.tolist()), eigvals_only=True), key=abs))
    k_block = abs(0.3 * 1e11 * small)
    k = np.diag([1.0, 1e11, k_block, k_block])
    g = np.zeros((4, 4))
    g[0, 0] = g[1, 1] = 1.0
    g[2:, 2:] = block
    got = eigenvalues(k, g)
    assert 1.0 in got and 1e11 in got and len(got) == 3, got


@pytest.mark.parametrize("name", ["tied_twins_antisymmetric_coupling.eng", "complex_pair_beside_3e37.eng"])
def test_a_complex_pair_hidden_by_symmetry_or_scale_is_refused(name):
    # Two tied systems coupled by an antisymmetric 0.45e-12 of their scale: symmetric pair by
    # pair, symmetrized, their double printed 1 twice for 1 ± 0.00225i; and 2 ± 0.001i beside
    # a λ of 3e37 passed as real at 1e-40 of the largest (the seventh audit of 0.47.0). What
    # symmetrizing drops is weighed against each λ's round-off, and beyond it the pencil is
    # worked out as one that is not symmetric.
    with pytest.raises(EngEvaluationError, match="not real"):
        _sheet_eigenvalues(name)


def test_a_joint_where_kg_cancels_is_symmetric():
    # Five members at a joint whose axial forces cancel: K_g's entries there are round-off,
    # their last bits O(1) of themselves. Against their own diagonal - round-off too - the pair
    # failed the symmetry test and his eigenvals(-K_g, K) was refused (the seventh audit).
    got = _sheet_eigenvalues("joint_where_kg_cancels_minus_kg_k.eng")
    want = _exact("joint_where_kg_cancels_minus_kg_k.eng")
    scale = max(abs(v) for v in want)
    assert len(got) == len(want) and all(abs(a - b) <= 1e-12 * scale for a, b in zip(got, want)), (got, want)


def test_an_antisymmetric_coupling_between_two_apart_eigenvalues_is_seen():
    # Two tied systems whose soft λ are 1e-3 apart, coupled by an antisymmetric 2.25e-4 - each
    # λ alone blind to it - were symmetrized and printed 1 and 1.001; the exact λ are 1.000282
    # and 1.000718 (the eighth audit of 0.47.0). Every pair of λ is weighed now, and this
    # pencil is worked out as the non-symmetric one it is.
    e = 0.00022500000045
    k = np.array([
        [500000001.0, -500000000.0, e, e],
        [-500000000.0, 500000001.0, e, e],
        [-e, -e, 750000001.001, -750000000.0],
        [-e, -e, -750000000.0, 750000001.001],
    ])
    got = eigenvalues(k, np.eye(4))
    assert got[:2] == pytest.approx([1.00028202482, 1.00071802191], rel=1e-6), got


def test_an_imaginary_part_below_a_millionth_prints_the_real_part():
    # 2 ± 1e-6i beside 1e8, out of symmetry: main printed 2 twice, within its figures; refused
    # at 1e-9 of itself (the eighth audit of 0.47.0).
    got = eigenvalues(np.array([[2.0, 1e-6, 0], [-1e-6, 2.0, 0], [0, 0, 1e8]]), np.eye(3))
    assert got == pytest.approx([2.0, 2.0, 1e8], rel=1e-9), got


def test_couplings_each_under_the_gate_are_summed():
    # Six tied systems, one coupled to the other five by an antisymmetric 2: each pair moved the
    # soft λ by 0.18, under ten times its round-off, so the largest of them let the pencil be
    # symmetrized and 1 was printed for 2.149 (the ninth audit of 0.47.0). Summed, it is
    # worked out as the non-symmetric pencil it is.
    got = _sheet_eigenvalues("six_ties_summed_coupling.eng")
    want = _exact("six_ties_summed_coupling.eng")
    assert got[:2] == pytest.approx(want[:2], rel=1e-9), (got[:3], want[:3])


def test_a_non_symmetric_pencil_whose_iteration_needs_more_figures():
    # Ten such systems: 3.75 ± 1.2i. In 80 figures mpmath's QR did not settle and its own
    # error reached the page; in 120 it does, and the pair is refused as not real.
    with pytest.raises(EngEvaluationError, match="not real"):
        _sheet_eigenvalues("ten_ties_summed_coupling.eng")


def test_a_coupling_to_a_direction_g_lacks_is_seen():
    # An antisymmetric 14.2 between a tied mode (λ = 1) and a soft direction where G is 0 - whose
    # λ is infinite and was no row of the check - moved λ to 6.06, and 1 was printed (the tenth
    # audit of 0.47.0). Weighed through those directions too, the pencil is not symmetric, and
    # with G singular it is refused as main refuses it.
    q, ks = 1e14, 40.0
    e = 0.9 * 5e-13 * ((1e13 + 1) * (q + ks)) ** 0.5
    k = np.array([
        [1e13 + 1, -1e13, e, 0], [-1e13, 1e13 + 1, 0, e], [-e, 0, q + ks, -q], [0, -e, -q, q + ks],
    ])
    with pytest.raises(EngEvaluationError, match="second matrix is singular"):
        eigenvalues(k, np.diag([1.0, 1.0, 0.0, 0.0]))
