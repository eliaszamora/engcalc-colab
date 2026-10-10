r"""What the follow-up audit of the chapter 10 fixes found (2026-10-06).

- `eigenvals(K, G)` of an inclined bar mechanism printed `0.00` alone, in silence: K is
  singular only to round-off, so no shift was taken, and λ = 5 was thrown away as a μ
  small beside the round-off's 1e13. Which eigenvalues are infinite is now judged against
  ‖(K + σG)⁻¹‖·‖G‖, on the best conditioned K + σG.
- The same pencil written with plain `0` entries was refused as "singular for every λ":
  the unit of λ was looked for only where both matrices have one.
- A range bound read from an entry was said in base units, `222411.08 m·kg/s²`; said now in
  the other bound's unit, or as the page would show it.
- An exact zero eigenvalue of a shifted pencil printed as `-232.83 × 10^{-12}`.
"""

import contextlib
import io

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


def eigenvalues_shown(page: str, name: str = "l") -> list[float]:
    import re

    shown = page.split(f"{name} & = &", 1)[1].split(r"\end{array}", 1)[0]
    shown = shown.split(r"\operatorname{eigenvals}", 1)[1]
    shown = shown.replace(r"\rule{0pt}{0.7em}", "")
    numbers = re.findall(r"-?\d+\.\d+(?: \\times 10\^\{-?\d+\})?", shown)
    values = []
    for number in numbers:
        if r"\times" in number:
            mantissa, exponent = number.split(r" \times 10^{")
            values.append(float(mantissa) * 10 ** int(exponent.rstrip("}")))
        else:
            values.append(float(number))
    return values


def zeros(n):
    return "0[kN/m]"


@pytest.mark.parametrize("angle", [30, 37, 45])
def test_an_inclined_bar_mechanism_keeps_both_eigenvalues(sheet, angle):
    page, printed = sheet(
        f"c := cos({angle}[deg])\ns := sin({angle}[deg])\nk := 1000[kN/m]\n"
        "K := [k*c^2, k*c*s, 0[kN/m]; k*c*s, k*s^2, 0[kN/m]; 0[kN/m], 0[kN/m], 5[kN/m]]\n"
        "G := [1[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 1[kN/m]]\n"
        "l := eigenvals(K, G)\n"
    )
    assert "engcalc:" not in printed, printed
    # det(K - λG) = -λ k s² (5 - λ)
    assert eigenvalues_shown(page) == [0.0, 5.0], page


def test_a_spectrum_wider_than_ten_decades(sheet):
    page, printed = sheet(
        "K := [1[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 1e-12[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 3[kN/m]]\n"
        "G := [1[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 1[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 0[kN/m]]\n"
        "l := eigenvals(K, G)\n"
    )
    assert "engcalc:" not in printed, printed
    shown = eigenvalues_shown(page)
    # 1e-12 is kept, and printed 0.00 at the page's precision.
    assert shown == [0.0, 1.0], (shown, page)


def test_a_shift_near_an_eigenvalue(sheet):
    page, printed = sheet(
        "K := [2.999999999999[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 3[kN/m]]\n"
        "G := [-1[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 1[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 0[kN/m]]\n"
        "l := eigenvals(K, G)\n"
    )
    assert "engcalc:" not in printed, printed
    assert eigenvalues_shown(page) == [-3.0, 0.0], page


def test_plain_zeros_in_a_regular_pencil(sheet):
    page, printed = sheet("K := [1[kN/m], 0; 0, 0]\nG := [0, 0; 0, 1[kN/m]]\nl := eigenvals(K, G)\n")
    assert "engcalc:" not in printed, printed
    assert eigenvalues_shown(page) == [0.0], page


def test_an_exact_zero_is_zero(sheet):
    page, printed = sheet(
        "K := [2e6[kN/m], -2e6[kN/m], 0[kN/m]; -2e6[kN/m], 2e6[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 0[kN/m]]\n"
        "G := [1[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 1[kN/m]]\n"
        "l := eigenvals(K, G)\n"
    )
    assert "engcalc:" not in printed, printed
    assert eigenvalues_shown(page) == [0.0, 0.0], page


def test_random_pencils_match_numpy(sheet):
    rng = np.random.default_rng(7)
    for _ in range(8):
        a = rng.normal(size=(4, 4))
        stiffness = a @ a.T + np.eye(4)
        b = rng.normal(size=(4, 2))
        geometric = b @ b.T  # rank 2: two finite eigenvalues
        rows = lambda m: "; ".join(", ".join(f"{float(v)!r}[kN/m]" for v in row) for row in m)
        page, printed = sheet(f"K := [{rows(stiffness)}]\nG := [{rows(geometric)}]\nl := eigenvals(K, G)\n")
        assert "engcalc:" not in printed, printed
        mu = np.linalg.eigvals(np.linalg.solve(stiffness, geometric))
        expected = sorted(1 / m.real for m in mu if abs(m) > 1e-9 * np.abs(mu).max())
        shown = eigenvalues_shown(page)
        assert len(shown) == 2, (shown, expected)
        for got, want in zip(shown, expected):
            assert abs(got - want) <= 0.006 * max(1.0, abs(want)), (shown, expected)


def test_a_lower_bound_from_an_entry_is_said_in_its_unit(sheet):
    _, printed = sheet("f := [100[kip]; 50[kip]]\nx := solve(eq(x, 300[kip]), x, f[2], 200[kip])\n")
    assert "50.00 kip" in printed and "200.00 kip" in printed and "kg" not in printed, printed


def test_an_upper_bound_from_an_entry_beside_a_plain_zero(sheet):
    _, printed = sheet("f := [100[kip]; 50[kip]]\nx := solve(eq(x, 300[kip]), x, 0, f[1])\n")
    # The matrix holds its entries in base units; a kip sheet shows them in kip since 0.50.0,
    # and the bound reads as the page does (it read 444.82 kN).
    assert "100.00 kip" in printed and "kg" not in printed, printed


def test_a_bound_typed_in_metres_stays_in_metres(sheet):
    _, printed = sheet("x := solve(eq(x, 3[m]), x, 0.2[m], 1.5[m])\n")
    assert "0.20 m" in printed and "1.50 m" in printed, printed
    _, printed = sheet("x := solve(eq(x, 3[m]), x, 200[mm], 1.5[m])\n")
    assert "200.00 mm" in printed and "1.50 m" in printed, printed
