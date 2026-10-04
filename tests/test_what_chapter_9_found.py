r"""What chapter 9 of his book found refused, wrong or hanging (2026-10-02).

- `eigenvals` and `det` of a `:=` matrix were refused, so a frame's critical load could only
  be found by an inverse iteration written by hand in a `% while`;
- a rotation a `solve` found to be exactly 0 took the vector's metre, `θ = 0.00 m`, and the
  moment it made read `kN·m²`;
- `{a}` in the condition of a `% while` inside a `% for` read as a set, `{2}`;
- a placeholder holding an operation after `)` or an operand, `(2*a){q}`, was refused as
  invalid syntax before the loop ran;
- a `% for` holding a `% while` tabulated `r = 1.00`, its value before the while, beside the
  converged `s = 1.41`;
- `extrema` of the load of Example 9.1 - sines under a root - never came back;
- `solve` in a range said "no root" when its equation added quantities of different units.
"""

import contextlib
import io
import time

import numpy as np
import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


def _run(source: str, monkeypatch) -> tuple[str, str]:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    latex = " ".join(item.data for item in captured if isinstance(item, Math))
    return latex.replace(r"\displaystyle ", ""), console.getvalue()


# A cantilever column of one element, in (w, θ) at its free end: Equation 4.34 and the
# geometric stiffness of Equation 9.14 per unit of compression. EI/l² is 1000 kN.
_COLUMN = (
    "E := 200000[MPa]\nI := 8e7[mm^4]\nl := 4[m]\n"
    "K := E*I/l^3*[12, -6*l; -6*l, 4*l^2]\n"
    "G := -1/(30*l)*[36, -3*l; -3*l, 4*l^2]\n"
)


def _column_in_si():
    stiffness = 200e9 * 8e-5 / 4.0**3 * np.array([[12, -6 * 4.0], [-6 * 4.0, 4 * 4.0**2]])
    geometric = -1 / (30 * 4.0) * np.array([[36, -3 * 4.0], [-3 * 4.0, 4 * 4.0**2]])
    return stiffness, geometric


def test_the_critical_load_of_a_numeric_pencil(monkeypatch):
    page, console = _run(_COLUMN + "lam := eigenvals(K, -G)\nP_cr := lam[1]\n", monkeypatch)
    assert not console, console

    stiffness, geometric = _column_in_si()
    loads = np.sort(np.linalg.eigvals(np.linalg.inv(-geometric) @ stiffness).real) / 1000
    assert f"P_{{cr}} & = & \\mathit{{lam}}_{{1}} = {loads[0]:.2f}\\,\\mathrm{{kN}}" in page, page
    assert f"{loads[0]:.2f}" == "2485.96"
    assert r"\operatorname{eigenvals}\left(K, -G\right)" in page, page


def test_the_determinant_of_a_numeric_matrix_has_its_units(monkeypatch):
    page, console = _run(_COLUMN + "D := det(K)\n", monkeypatch)
    assert not console, console

    stiffness, _ = _column_in_si()
    assert np.linalg.det(stiffness) / 1e6 == pytest.approx(1.2e7)
    assert r"\operatorname{det}\left(K\right) = 1.20 \times 10^{7}\,\mathrm{kN}^{2}" in page, page


def test_eigenvals_of_one_numeric_matrix_and_of_one_that_has_no_real_ones(monkeypatch):
    page, console = _run("A := [2, 1; 1, 2]\nv := eigenvals(A)\n", monkeypatch)
    assert not console, console
    assert r"\left[\begin{matrix}1.00\\[3pt]3.00\end{matrix}\right]" in page, page

    _, console = _run("B := [0, -1; 1, 0]\nw := eigenvals(B)\n", monkeypatch)
    assert "not real" in console and "symmetric" in console, console


def test_an_exact_zero_a_solve_found_is_a_number(monkeypatch):
    page, console = _run(
        "k := 1000[kN/m]\nK := [k, 0[kN]; 0[kN], 2*k*1[m^2]]\nF := [10[kN]; 0[kN*m]]\n"
        "d := solve(K, F)\ntheta := d[2]\nM := 2*k*1[m^2]*theta\n",
        monkeypatch,
    )
    assert not console, console
    assert r"\theta & = & d_{2} = 0.00 \\" in page, page
    assert r"M & = & 0.00\,\mathrm{kN} \cdot \mathrm{m} \\" in page or page.rstrip().endswith(
        r"M & = & 0.00\,\mathrm{kN} \cdot \mathrm{m} \end{array}"
    ), page


def test_a_written_zero_still_takes_the_unit_beside_it(monkeypatch):
    """What `written_zeros` keeps: Example 7.4's curvature, a `0` written in the literal."""
    page, console = _run("z := [0; 2[mm]]\nw := z[1]\n", monkeypatch)
    assert not console, console
    assert r"w & = & z_{1} = 0.00\,\mathrm{m} " in page, page


def test_a_placeholder_in_the_condition_of_a_while(monkeypatch):
    page, console = _run(
        "% for a in [2, 3]:\nr := 1\n% while abs(r^2 - {a}) > 1e-9:\n"
        "r := (r + {a}/r)/2\n% end\ns := r\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"\left|{r^{2} - 2}\right|" in page and r"\left|{r^{2} - 3}\right|" in page, page
    assert r"s & = & 1.41" in page and r"s & = & 1.73" in page, page


def test_a_for_holding_a_while_does_not_tabulate_the_value_before_it(monkeypatch):
    page, console = _run(
        "c := 2\n% for a in [1, 2]:\nr := 1\n% while abs(r^2 - c) > 1e-9:\n"
        "r := (r + c/r)/2\n% end\ns := r*{a}\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"1 & 1.00 & 1.41" not in page, page
    assert r"s & = & 1.41" in page and r"s & = & 2.83" in page, page


def test_a_placeholder_after_a_bracket_or_an_operand_holds_an_operation(monkeypatch):
    page, console = _run(
        "a := 2\n% for i, q in enumerate([\"+ 1\", \"* 2\"], start=1):\n"
        "b_{i} := (2*a){q}\nc_{i} := a {q}\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"& 5.00 & 3.00" in page and r"& 8.00 & 4.00" in page, page


def test_the_limit_point_of_example_9_1(monkeypatch):
    started = time.perf_counter()
    page, console = _run(
        "E := 200000[MPa]\nA_ab := 2[mm^2]\nL := 4[m]\nalpha := 0.05\n"
        "L_a(phi) = L*sqrt((1 + sin(phi))^2 + (1 - cos(phi))^2)\n"
        "N_a(phi) = E*A_ab*(L_a(phi) - L)/L\n"
        "P_e(phi) = L*N_a(phi)*(sin(phi) + cos(phi))/(L_a(phi)*(sin(phi) + alpha*cos(phi)))\n"
        "extrema(P_e(phi), phi, 0.3, 0.6)\n",
        monkeypatch,
    )
    elapsed = time.perf_counter() - started
    assert not console, console
    assert (
        r"\phi \approx 0.44 \quad\cdot\quad \text{value} \approx 339.21\,\mathrm{kN}"
        r" \quad\cdot\quad \text{local max, global max}"
    ) in page, page
    assert elapsed < 90.0, elapsed


@pytest.mark.parametrize(
    "sheet",
    [
        "k := 3[kN/m]\nx_1 := solve(eq(k*x, 6[kN]), x, 0, 5)\n",
        "x_1 := solve(eq(x + 1[m], 3[m]), x, 0, 5)\n",
        "k := 3[kN/m]\nx_1 := solve(eq(k*x + 1[kN], 6), x, 0[m], 5[m])\n",
    ],
)
def test_a_range_solve_says_its_units_do_not_fit(sheet, monkeypatch):
    _, console = _run(sheet, monkeypatch)
    assert "incompatible units" in console, console
    assert "no root" not in console, console


def test_a_range_solve_with_fitting_units_still_answers(monkeypatch):
    page, console = _run("k := 3[kN/m]\nx_1 := solve(eq(k*x, 6[kN]), x, 0[m], 5[m])\n", monkeypatch)
    assert not console, console
    assert r"2.00\,\mathrm{m}" in page, page

    _, console = _run("x_1 := solve(eq(x^2 + 1, 0), x, 0, 5)\n", monkeypatch)
    assert "no root" in console, console
