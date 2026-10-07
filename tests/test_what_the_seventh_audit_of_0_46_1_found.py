r"""What the seventh audit of the chapter 10 fixes found (2026-10-07).

A soft mode beside a stiff link - a rigid diaphragm written as EA = 1e15 kN, two masses
tied by 1e14 kN/m - was printed as exactly 0: its λ sits below the round-off of the link's
entries, 1e-13 |y|ᵀ|K||x| / |yᵀGx|, as a mechanism's noise does, and that one bound
decided. A portal so built read a stable frame as a mechanism, ω² = 0 for 3.736 1/s², in
silence (main refused its singular mass; for the two masses main read 1, right).

What tells the two apart is the three runs with entries moved by 1e-14: the soft mode
holds its value, a mechanism's noise changes size and sign. Reference: mpmath, 50 digits.
"""

import pytest


def eigenvalues(source: str, unit: str) -> list[float]:
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.parser import parse_cell

    engine = EngineeringEngine()
    for item in parse_cell(source):
        engine.evaluate(item)
    return [float(q.to(unit).magnitude) for q in engine.numeric_context.matrices["l"].entries]


@pytest.mark.parametrize(
    "link, soft, expected",
    [
        ("100000000000000", "5", 1.0),
        ("1e16", "100", 20.0),
    ],
)
def test_a_soft_mode_beside_a_stiff_link(link, soft, expected):
    k = float(link)
    source = (
        f"K := [{k + float(soft)!r}[kN/m], {-k!r}[kN/m]; {-k!r}[kN/m], {k!r}[kN/m]]\n"
        "M := [2000[kg], 0[kg]; 0[kg], 3000[kg]]\nl := eigenvals(K, M)\n"
    )
    try:
        got = eigenvalues(source, "1/s**2")
    except Exception as exc:  # noqa: BLE001 - refused is not wrong; 0 is
        assert "cannot be told" in str(exc), exc
        return
    assert got[0] != 0.0, got
    assert abs(got[0] - expected) <= 0.02 * expected, (got, expected)


def test_a_mechanism_is_still_a_zero():
    # Two masses and nothing to the ground: a rigid-body mode, λ = 0, and k(1/m1 + 1/m2).
    got = eigenvalues(
        "K := [5[kN/m], -5[kN/m]; -5[kN/m], 5[kN/m]]\nM := [2000[kg], 0[kg]; 0[kg], 3000[kg]]\nl := eigenvals(K, M)\n",
        "1/s**2",
    )
    assert got[0] == 0.0 and abs(got[1] - 5000 * (1 / 2000 + 1 / 3000)) < 1e-9, got
