r"""What the independent audit of the chapter 10 fixes found (2026-10-06).

- `max(10[deg], 45)` printed 45.00 before and 2578.31° after the first fix: a plain number
  beside an angle is left as it was, and `max` of angles alone is read in the first one.
- `eigenvals(K, G)` with K and G both singular said "any λ satisfies K x = λ G x" of a
  pencil whose only eigenvalue is 0: refused only when K + σG is singular for every σ.
- A condition refused before it ran quoted the stand-ins, `x  + 1 3`, not `x {op} 3`.
- `c := a*b/1e300` over `1e200` values, true value 1e100, was "too large": a step passed
  the float range, and the message says that. `0*(1e300*1e300)` is not a number.
- A range bound taken from an entry was said in base units, `444822.16 m·kg/s²`.
- `solve` over a whole matrix suggested `d[1,1]`, a matrix the sheet did not have; a
  1 x 1 product, `g'*f`, is one number.
- An entry written `f_{1}` beside a scalar `f_1` of the sheet read as that scalar.
- `9.999e600` was written `10.00 × 10^{600}`.
"""

import contextlib
import io

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


def value_of(page: str, name: str) -> str:
    return page.split(name + r" & = & \displaystyle ", 1)[1].split(r"\\", 1)[0].split(r"\end", 1)[0].strip()


def test_a_plain_number_beside_an_angle_is_as_it_was(sheet):
    page, printed = sheet("a := max(10[deg], 45)\nb := max(10[deg], 0.5)\n")
    assert not printed, printed
    assert value_of(page, "a") == "45.00", page
    assert "10.00" in value_of(page, "b"), page


def test_angles_alone_are_read_in_the_first(sheet):
    page, _ = sheet("t := max(30[deg], 0.5[rad])\n")
    assert "30.00" in value_of(page, "t"), page


def test_a_regular_pencil_with_both_singular(sheet):
    # det(K - λG) = -λ: one finite eigenvalue, 0.
    page, printed = sheet(
        "K := [1[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m]]\nG := [0[kN/m], 0[kN/m]; 0[kN/m], 1[kN/m]]\n"
        "l := eigenvals(K, G)\n"
    )
    assert "engcalc:" not in printed, printed
    assert r"& = & \displaystyle 0.00" in page.split("l & = &", 1)[1], page


def test_a_shifted_pencil_matches_numpy(sheet):
    import numpy as np

    page, printed = sheet(
        "K := [4[kN/m], -2[kN/m], 0[kN/m]; -2[kN/m], 2[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 0[kN/m]]\n"
        "G := [1[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], 3[kN/m]]\n"
        "l := eigenvals(K, G)\n"
    )
    assert "engcalc:" not in printed, printed
    stiffness = np.array([[4, -2, 0], [-2, 2, 0], [0, 0, 0.0]])
    geometric = np.diag([1, 0, 3.0])
    shift = 1.0
    inverses = np.linalg.eigvals(np.linalg.solve(stiffness + shift * geometric, geometric))
    expected = sorted(1 / value.real - shift for value in inverses if abs(value) > 1e-12)
    shown = page.split("l & = &", 1)[1]
    for value in expected:
        assert f"{value:.2f}" in shown, (expected, shown)


def test_a_singular_pencil_is_refused(sheet):
    _, printed = sheet(
        "K := [1[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m]]\nG := [1[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m]]\n"
        "l := eigenvals(K, G)\n"
    )
    assert "engcalc:" in printed and "any λ" in printed, printed


def test_a_refused_condition_is_quoted_as_typed(sheet):
    _, printed = sheet("x := 2\n% op = '<'\n% if x {op} 3:\ny := 1\n% end\n")
    assert "x {op} 3" in printed, printed


def test_a_step_past_the_float_range_says_so(sheet):
    _, printed = sheet("a := 1e200\nb := 1e200\nc := a*b/1e300\n")
    assert "a step of it" in printed, printed


def test_not_a_number_is_said(sheet):
    _, printed = sheet("x := 0*(1e300*1e300)\n")
    assert "not a number" in printed, printed


def test_a_bound_from_an_entry_is_said_in_its_unit(sheet):
    _, printed = sheet("f := [100[kip]; 50[kip]]\nx := solve(eq(x, 300[kip]), x, 0[kip], f[1])\n")
    assert "100.00 kip" in printed and "kg" not in printed, printed


def test_a_whole_matrix_in_a_solve_names_it(sheet):
    _, printed = sheet("f := [1[kip]; 2[kip]]\nx := solve(eq(f + x*1[kip], 300[kip]), x, 0, 1000)\n")
    assert "f[1]" in printed and "d[1,1]" not in printed, printed


def test_a_one_by_one_product_is_a_number(sheet):
    page, printed = sheet(
        "g := [1; 2]\nf := [1[kip]; 2[kip]]\n% if g'*f > 2[kip]:\ny := 1\n% else:\ny := 2\n% end\n"
        "w := solve(eq(g'*f*w, 10[kip]), w, 0, 10)\n"
    )
    assert "engcalc:" not in printed, printed
    assert value_of(page, "y") == "1.00", page
    # `g'*f` is no single entry, so the line is written as typed, then its value.
    assert value_of(page, "w").endswith("= 2.00"), page


def test_an_entry_is_not_named_as_a_scalar_of_the_sheet(sheet):
    page, printed = sheet("f := [1[kip]; 2[kip]]\nf_1 := 7[kip]\n% if f[1] > 0.5[kip]:\ny := 1\n% end\n")
    assert "engcalc:" not in printed, printed
    assert r"\textbf{Como}\;\; f_{1}" not in page, page


def test_a_mantissa_that_rounds_to_ten(sheet):
    # A literal past the float range is read as infinity before any of this; a product
    # is held exactly.
    page, _ = sheet("x = 9.999e300*1e300\ny = 9.999e300*1\n")
    assert r"1.00 \times 10^{601}" in page and r"10.00 \times" not in page, page
