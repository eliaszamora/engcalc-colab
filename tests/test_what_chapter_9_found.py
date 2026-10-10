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
import sympy as sp
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
    assert f"P_{{cr}} & = & \\lambda_{{1}} = {loads[0]:.2f}\\,\\mathrm{{kN}}" in page, page
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


def test_eigenvals_of_a_matrix_with_nothing_on_its_diagonal(monkeypatch):
    """The audit of 0.45.6: the eigenvalues' unit was read off the diagonal, and a diagonal
    of written zeros gave none, so `[0, 1; 1, 0]` answered `[0.00; 0.00]`. The unit is the
    root of a cycle of entries, λ² = a₁₂ a₂₁; and it is taken from a nonzero entry, not
    from [1,1]."""
    page, console = _run(
        "A := [0, 1; 1, 0]\nv := eigenvals(A)\na_1 := v[1]\na_2 := v[2]\n"
        "B := [0, 2[kN]; 2[kN], 0]\nw := eigenvals(B)\nb_1 := w[1]\nb_2 := w[2]\n"
        "C := [0, 2[kN]; 2[kN], 3[kN]]\nz := eigenvals(C)\nc_1 := z[1]\nc_2 := z[2]\n",
        monkeypatch,
    )
    assert not console, console
    for row in (
        r"a_{1} & = & v_{1} = -1.00 \\",
        r"a_{2} & = & v_{2} = 1.00 \\",
        r"b_{1} & = & w_{1} = -2.00\,\mathrm{kN} \\",
        r"b_{2} & = & w_{2} = 2.00\,\mathrm{kN} \\",
        r"c_{1} & = & z_{1} = -1.00\,\mathrm{kN} \\",
        r"c_{2} & = & z_{2} = 4.00\,\mathrm{kN} \end{array}",
    ):
        assert row in page, (row, page)


def test_eigenvals_of_a_pencil_whose_second_matrix_has_no_diagonal(monkeypatch):
    page, console = _run(
        "k := 1000[kN/m]\nK := [k, 0; 0, k]\nG := [0, 1; 1, 0]\nlam := eigenvals(K, G)\n"
        "l_1 := lam[1]\nl_2 := lam[2]\n",
        monkeypatch,
    )
    assert not console, console
    assert r"l_{1} & = & \lambda_{1} = -1000.00\,\frac{\mathrm{kN}}{\mathrm{m}}" in page, page
    assert r"l_{2} & = & \lambda_{2} = 1000.00\,\frac{\mathrm{kN}}{\mathrm{m}}" in page, page


def test_eigenvals_are_in_order_of_value_not_of_size(monkeypatch):
    page, console = _run("S := [2, 0; 0, -5]\ns := eigenvals(S)\n", monkeypatch)
    assert not console, console
    assert r"\left[\begin{matrix}-5.00\\[3pt]2.00\end{matrix}\right]" in page, page


def test_eigenvals_and_det_refuse_units_that_do_not_fit(monkeypatch):
    _, console = _run("M := [1[kN], 0; 0, 1[m]]\nm := eigenvals(M)\n", monkeypatch)
    assert "eigenvalues" in console and "inverse" not in console, console

    _, console = _run("N := [1[kN], 1[m]; 1[m], 1[kN]]\nn := det(N)\n", monkeypatch)
    assert "determinant" in console and "inverse" not in console, console


def test_the_determinant_keeps_its_sign_and_the_unit_of_a_term(monkeypatch):
    """`det([0, 2 kN; 2 kN, 0])` is -4 kN²: the unit of the one term that is not zero, the
    off-diagonal one, and its sign."""
    page, console = _run("B := [0, 2[kN]; 2[kN], 0]\nD := det(B)\n", monkeypatch)
    assert not console, console
    assert r"\operatorname{det}\left(B\right) = -4.00\,\mathrm{kN}^{2}" in page, page


def test_eigenvals_of_a_pencil_with_a_singular_second_matrix_says_which(monkeypatch):
    """A lumped geometric stiffness or mass is often singular; the message blamed the
    supports, which belong to K. Since chapter 10 a singular G alone gives the finite
    eigenvalues (`test_lines_chapter_10_found_refused`); refused when K is singular too."""
    page, console = _run(
        "K := [2[kN/m], 0; 0, 3[kN/m]]\nG := [1, 0; 0, 0]\nlam := eigenvals(K, G)\n",
        monkeypatch,
    )
    assert not console, console
    assert r"& = & 2.00\,\frac{\mathrm{kN}}{\mathrm{m}}" in page, page
    _, console = _run(
        "K := [2[kN/m], 0; 0, 0[kN/m]]\nG := [1, 0; 0, 0]\nlam := eigenvals(K, G)\n",
        monkeypatch,
    )
    assert "any λ satisfies" in console, console
    assert "supports" not in console, console


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
    """Example 7.4's curvature, a `0` written in the literal."""
    page, console = _run("z := [0; 2[mm]]\nw := z[1]\n", monkeypatch)
    assert not console, console
    assert r"w & = & z_{1} = 0.00\,\mathrm{m} " in page, page


def test_a_written_zero_keeps_its_unit_through_an_operation(monkeypatch):
    """The audit of 0.45.6: only `numbers_of` knew which zeros were written, so after a
    `transpose` or a factor on the same line Example 7.4's curvature lost its 1/m and
    `GJ D_1 / T` read `0.00 m` again."""
    page, console = _run(
        "GJ := 10[kN*m^2]\nT := 5[kN*m]\nD := [0; 2[1/m]]\n"
        "s := GJ*transpose(D)[1]/T\nq := GJ*(2*D)[1]/T\n",
        monkeypatch,
    )
    assert not console, console
    assert r"\left(D^{T}\right)_{1}}{T} = 0.00 \\" in page, page
    assert page.rstrip().endswith(r"= 0.00 \end{array}"), page
    assert r"0.00\,\mathrm{m}" not in page, page


@pytest.mark.parametrize("load", ["0[kN*m]", "0"])
def test_a_zero_a_solve_found_stays_a_number_when_it_is_read_again(load, monkeypatch):
    """A rotation a solve found to be 0, read on a later line: with the moment written as a
    plain `0` the solve cannot know its unit, and either way it is not the metre of the
    displacement beside it (the audit of 0.45.6 found `0.00 m` with `F := [10[kN]; 0]`)."""
    page, console = _run(
        "k := 1000[kN/m]\nK := [k, 0; 0, 2*k*1[m^2]]\n"
        f"F := [10[kN]; {load}]\nd := solve(K, F)\ntheta := d[2]\n"
        "M := 2*k*1[m^2]*theta\nu := d[1]\n"
        "t_1 := transpose(d)[2]\nt_2 := (2*d)[2]\n",
        monkeypatch,
    )
    assert not console, console
    assert r"\theta & = & d_{2} = 0.00 \\" in page, page
    assert r"M & = & 0.00\,\mathrm{kN} \cdot \mathrm{m} \\" in page, page
    assert r"u & = & d_{1} = 10.00\,\mathrm{mm}" in page, page
    # Through an operation that only moves or scales the entries, it is still a number.
    assert r"\left(d^{T}\right)_{2} = 0.00 \\" in page, page
    assert page.rstrip().endswith(r"\left(2\,d\right)_{2} = 0.00 \end{array}"), page


def test_a_computed_rotation_of_a_frame_keeps_no_unit_once_stored(monkeypatch):
    """A connected stiffness gives every entry of the solution its unit, a rotation none;
    stored and read back, a rotation that came out exactly 0 was taken for a written 0 and
    lent the metre beside it."""
    page, console = _run(
        "K := [2000[kN/m], 1000[kN]; 1000[kN], 4000[kN*m]]\nF := [0[kN]; 0[kN*m]]\n"
        "G := [1000[kN/m], 0[kN]; 0[kN], 1000[kN*m]]\nH := [10[kN]; 0]\n"
        "d := solve(G, H)\nt := d[2]\nr := 1000[kN*m]*t\n",
        monkeypatch,
    )
    assert not console, console
    assert r"t & = & d_{2} = 0.00 \\" in page, page
    assert r"r & = & 0.00\,\mathrm{kN} \cdot \mathrm{m}" in page, page


def test_a_placeholder_in_the_condition_of_a_while(monkeypatch):
    page, console = _run(
        "% for a in [2, 3]:\nr := 1\n% while abs(r^2 - {a}) > 1e-9:\n"
        "r := (r + {a}/r)/2\n% end\ns := r\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"\left|{r^{2} - 2}\right|" in page and r"\left|{r^{2} - 3}\right|" in page, page
    assert r"s & = & 1.41" in page and r"s & = & 1.73" in page, page


def test_a_placeholder_in_a_while_condition_is_read_at_every_pass(monkeypatch):
    """The audit of 0.45.6: `{k}` was written in once, before the loop, so a counter the
    body moves never reached the condition - 1000 passes, "does not converge" - where the
    bare `k`, read at every pass, stops at three."""
    page, console = _run(
        "% k = 0\nr := 0\n% while {k} < 3:\nr := r + 1\n% k += 1\n% end\n", monkeypatch
    )
    assert not console, console
    assert r"\textbf{En 3 iteraciones:}" in page and r"r & = & 3.00" in page, page


def test_a_placeholder_in_an_if_condition_is_read_as_in_a_while(monkeypatch):
    page, console = _run(
        "% for a in [1, 2]:\n% if {a} > 1:\nb_{a} := 10\n% else:\nb_{a} := 20\n% end\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"b_{1} & = & 20.00" in page and r"b_{2} & = & 10.00" in page, page


def test_a_for_holding_a_while_does_not_tabulate_the_value_before_it(monkeypatch):
    page, console = _run(
        "c := 2\n% for a in [1, 2]:\nr := 1\n% while abs(r^2 - c) > 1e-9:\n"
        "r := (r + c/r)/2\n% end\ns := r*{a}\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"1 & 1.00 & 1.41" not in page, page
    assert r"s & = & 1.41" in page and r"s & = & 2.83" in page, page


def test_a_name_set_again_in_a_later_pass_keeps_its_column(monkeypatch):
    """The audit of 0.45.6: a `% if` of the second pass sets `r` before that pass's own
    `r := {a}`. The first pass's `r` was taken for one set again after its line - the
    block's rows carried no pass - and the whole table went."""
    page, console = _run(
        "% for a in [1, 2]:\n% if a > 1:\nr := 7\n% end\nr := {a}\ns := r*2\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"1 & 1.00 & 2.00" in page and r"2 & 2.00 & 4.00" in page, page


def test_a_placeholder_after_a_bracket_or_an_operand_holds_an_operation(monkeypatch):
    page, console = _run(
        "a := 2\n% for i, q in enumerate([\"+ 1\", \"* 2\"], start=1):\n"
        "b_{i} := (2*a){q}\nc_{i} := a {q}\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"& 5.00 & 3.00" in page and r"& 8.00 & 4.00" in page, page

    page, console = _run(
        "v := [1; 2]\n% for i, q in enumerate([\"+ 1\", \"* 3\"], start=1):\n"
        "w_{i} := v[1]{q}\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"w_{1} & = & v_{1} + 1 = 2.00" in page, page
    assert r"w_{2} & = & v_{1} \cdot 3 = 3.00" in page, page


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


_EXAMPLE_9_1 = (
    "E := 200000[MPa]\nA_ab := 2[mm^2]\nL := 4[m]\nalpha := 0.05\n"
    "L_a(phi) = L*sqrt((1 + sin(phi))^2 + (1 - cos(phi))^2)\n"
    "N_a(phi) = E*A_ab*(L_a(phi) - L)/L\n"
    "P_e(phi) = L*N_a(phi)*(sin(phi) + cos(phi))/(L_a(phi)*(sin(phi) + alpha*cos(phi)))\n"
)


@pytest.mark.parametrize(
    "sheet",
    [
        "P := 10[kN]\nF(t) = P/sin(t)\nextrema(F(t), t, 0[deg], 180[deg])\n",
        "extrema(1/sin(x), x, 3, 4)\n",
        "extrema(1/sin(x) + x, x, 6, 6.5)\n",
        "extrema(1/sin(x), x, 6, 6.5)\n",
        "extrema(1/sin(x), x, -3.5, -3)\n",
    ],
)
def test_extrema_with_a_pole_in_its_range_is_refused_not_invented(sheet, monkeypatch):
    """The audit of 0.45.6: once a periodic family of singularities was let through, a pole
    inside the range left the slope's numeric search to call hundreds of points of a curve
    that runs to infinity its minima (`P/sin t` on 0°-180°: 815 rows of "global min"). A
    family proves only that the range holds none of its members; one inside, at n = 0 or
    n = 1 or n = 2, is refused as before."""
    page, console = _run(sheet, monkeypatch)
    assert "could not resolve" in console or "could not validate" in console, console
    assert "global min" not in page and "local max" not in page, page[:2000]


def test_a_short_trigonometric_root_keeps_its_exact_answers(monkeypatch):
    """The audit of 0.45.6: every sine under a root was taken from SymPy, and answers it
    gives at once in closed form - `x = π`, `asin(1/4)`, `-π/4` - came back as numbers.
    Only a long one, where `solveset` does not return, is left to the numeric search."""
    page, console = _run(
        "roots(sqrt(1+sin(x))-1, x, 0, 4)\nroots(sqrt(sin(x))-1/2, x, 0, 3)\n"
        "extrema(1/sqrt(3+2*sin(x)-2*cos(x)), x, -1, -0.5)\n",
        monkeypatch,
    )
    assert not console, console
    assert r"x = \pi\,\left(3.14\right)" in page, page
    assert r"x = \operatorname{asin}{\left(\dfrac{1}{4} \right)}\,\left(0.25\right)" in page, page
    assert r"x = - \dfrac{\pi}{4}\,\left(-0.79\right)" in page, page


def test_a_longer_trigonometric_root_is_found_in_numbers(monkeypatch):
    """Twenty-two operations in the slope: SymPy took 30 s on it and then gave the search
    nothing it could validate. In numbers, at once."""
    started = time.perf_counter()
    page, console = _run(
        "extrema((sin(x) + cos(x))/sqrt(3 + 2*sin(x) - 2*cos(x)), x, -0.5, 0.5)\n", monkeypatch
    )
    elapsed = time.perf_counter() - started
    assert not console, console
    assert r"\approx" in page and "global max" in page, page
    assert elapsed < 20.0, elapsed


def test_extrema_beside_a_pole_just_outside_its_range(monkeypatch):
    """`1/sin x` on 0.5-3.1: π lies 0.04 past the end, and the minimum is 1 at π/2."""
    page, console = _run("extrema(1/sin(x), x, 0.5, 3.1)\n", monkeypatch)
    assert not console, console
    assert r"\text{value} = 1" in page and "global min" in page, page


def test_one_over_the_length_of_example_9_1_still_answers(monkeypatch):
    """A guard: `1/L_a` on 5-6 answered on main, where the sheet's expression reaches no
    family of singularities, and still does. (The family itself, 2nπ - π/4 ± i·0.35 with
    its real part at 5.50, is exercised by `test_example_9_1_past_a_complex_family_of_its_bar`;
    a mutant that keeps complex families inside the range survived this one.)"""
    page, console = _run(_EXAMPLE_9_1 + "extrema(1/L_a(phi), phi, 5, 6)\n", monkeypatch)
    assert not console, console
    assert "global max" in page and "global min" in page, page


def test_example_9_1_past_a_complex_family_of_its_bar(monkeypatch):
    """On 5-6 the load has a stationary point at 5.22, and the zeros of its bar's length,
    2π - π/4 ± i·0.35, have their real part at 5.50, inside: a family that is not real is
    no singularity there. The real pole, where `sin φ + α cos φ` vanishes, is at 6.23."""
    page, console = _run(_EXAMPLE_9_1 + "extrema(P_e(phi), phi, 5, 6)\n", monkeypatch)
    assert not console, console
    assert r"\phi \approx 5.22" in page and r"-162.48\,\mathrm{kN}" in page, page


def test_the_limit_point_of_example_9_1_in_degrees(monkeypatch):
    """The family `nπ - 0.05` read in the range's own unit: in radians its members 15.65
    and 18.80 would fall between 17.2 and 34.4 and refuse a range that holds none."""
    page, console = _run(
        _EXAMPLE_9_1 + "extrema(P_e(phi), phi, 17.2[deg], 34.4[deg])\n", monkeypatch
    )
    assert not console, console
    assert r"339.21\,\mathrm{kN}" in page and "local max, global max" in page, page


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


def test_a_range_solve_whose_range_has_no_unit_says_so(monkeypatch):
    _, console = _run("k := 3[kN/m]\nx_1 := solve(eq(k*x, 6[kN]), x, 0, 5)\n", monkeypatch)
    assert "the range has no unit" in console and "0[m]" in console, console


@pytest.mark.parametrize(
    "equation",
    ["eq(k/x + 1[kN], 6)", "eq(k*sqrt(x - 1), 6[kN])", "eq(k/(x - 2.5) + 1[kN], 6)"],
)
def test_a_pole_in_the_range_does_not_hide_units_that_do_not_fit(equation, monkeypatch):
    """The audit of 0.45.6: one sample with no value - a pole at 0, a root of a negative
    number - and every other one refused for its units brought back "no root"."""
    _, console = _run(f"k := 3[kN/m]\nx_1 := solve({equation}, x, 0, 5)\n", monkeypatch)
    assert "incompatible units" in console and "no root" not in console, console


def test_a_range_in_degrees_is_not_said_to_have_no_unit(monkeypatch):
    """A degree is a number to Pint; the range was written with a unit all the same."""
    _, console = _run(
        "k := 3[kN/m]\nx_1 := solve(eq(k*x, 6[kN]), x, 0[deg], 90[deg])\n", monkeypatch
    )
    assert "incompatible units" in console, console
    assert "has no unit" not in console, console


def test_a_range_solve_with_fitting_units_still_answers(monkeypatch):
    page, console = _run("k := 3[kN/m]\nx_1 := solve(eq(k*x, 6[kN]), x, 0[m], 5[m])\n", monkeypatch)
    assert not console, console
    assert r"2.00\,\mathrm{m}" in page, page

    _, console = _run("x_1 := solve(eq(x^2 + 1, 0), x, 0, 5)\n", monkeypatch)
    assert "no root" in console, console


def test_a_family_whose_members_are_not_real_holds_no_singularity():
    """`_no_singularity_in_domain` on families written directly: 2nπ - π/4 + 0.35 i has its
    real part 5.50 inside 5-6 and no member on the real line; 2nπ - π/4 is real there."""
    from engcalc_colab.characteristics import normalize_analysis_domain
    from engcalc_colab.characteristics.extrema import _no_singularity_in_domain
    from engcalc_colab.numeric import NumericContext

    context = NumericContext()
    n = sp.Symbol("n", integer=True)
    domain = normalize_analysis_domain(context, sp.Integer(5), sp.Integer(6))
    complex_family = sp.ImageSet(sp.Lambda(n, 2 * n * sp.pi - sp.pi / 4 + sp.I * sp.Rational(35, 100)), sp.S.Integers)
    real_family = sp.ImageSet(sp.Lambda(n, 2 * n * sp.pi - sp.pi / 4), sp.S.Integers)
    assert _no_singularity_in_domain(complex_family, domain, context, None) is True
    assert _no_singularity_in_domain(real_family, domain, context, None) is False
    outside = normalize_analysis_domain(context, sp.Integer(1), sp.Integer(5))
    assert _no_singularity_in_domain(real_family, outside, context, None) is True


def test_a_zero_of_springs_borrows_the_unit_beside_it(monkeypatch):
    """The second audit of 0.45.6: marking every worked-out zero a plain number moved the
    error from a frame's rotation to a spring's displacement - `u_2 = 0.00` and the force
    `k u_2 = 0.00 kN/m`. Operands of one kind give a zero of that kind, as on main."""
    page, console = _run(
        "k := 1000[kN/m]\nK := [k, 0; 0, k]\nF := [10[kN]; 0]\nd := solve(K, F)\n"
        "u_2 := d[2]\nN_2 := k*u_2\nT := [1, 0; 0, 1]\ne := T*d\nN_3 := k*e[2]\n",
        monkeypatch,
    )
    assert not console, console
    assert r"u_{2} & = & d_{2} = 0.00\,\mathrm{m}" in page, page
    assert r"N_{2} & = & 0.00\,\mathrm{kN} \\" in page, page
    assert r"N_{3} & = & k e_{2} = 0.00\,\mathrm{kN}" in page, page


_FRAME_ZERO = (
    "k := 1000[kN/m]\nK := [k, 0; 0, 2*k*1[m^2]]\nF := [10[kN]; 0]\nd := solve(K, F)\n"
)


@pytest.mark.parametrize(
    "line, written",
    [
        ("t := d[[1, 2], [1]][2]", "t"),
        ("t := [d; d][4]", "t"),
        ("T := [1, 0; 0, 1]\nt := (T*d)[2]", "t"),
        ("t := (d + [1[mm]; 0])[2]", "t"),
        ("D := zeros(2, 1)\nD[[1, 2], [1]] := d\nt := D[2]", "t"),
    ],
)
def test_a_frame_s_worked_zero_stays_a_number_through_every_operation(line, written, monkeypatch):
    """A part, blocks, a product, a sum and an assignment into a part keep what the solve
    knew of its zero: a number, not the metre of the displacement beside it."""
    page, console = _run(_FRAME_ZERO + line + "\n", monkeypatch)
    assert not console, console
    assert page.rstrip().endswith(r"= 0.00 \end{array}"), page[-400:]


def test_a_zero_written_over_a_worked_one_is_a_written_zero(monkeypatch):
    page, console = _run(
        _FRAME_ZERO + "D := d\nD[[2], [1]] := 0\nt := D[2]\n", monkeypatch
    )
    assert not console, console
    assert page.rstrip().endswith(r"= 0.00\,\mathrm{m} \end{array}"), page[-400:]


def test_two_placeholders_in_one_condition(monkeypatch):
    page, console = _run(
        "% k = 0\n% n = 2\nr := 0\n% while {k} < {n}:\nr := r + 1\n% k += 1\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"\textbf{En 2 iteraciones:}" in page and r"r & = & 2.00" in page, page


def test_each_zero_of_a_frame_takes_the_unit_its_stiffness_gives(monkeypatch):
    """The third audit of 0.45.6: a frame loaded only along its axis has its transverse
    displacement and its rotation exactly 0, and the solve cannot read their units off the
    load. Marking both plain numbers gave the shear `12EI/L³ v` in kN/m. Each takes its
    unit from its own stiffness by work: K_ii c_i² is the work F x of the loaded entries -
    a metre against kN/m, nothing against kN·m."""
    page, console = _run(
        "EA := 2000[kN]\nEI := 500[kN*m^2]\nL := 2[m]\n"
        "K := [EA/L, 0, 0; 0, 12*EI/L^3, -6*EI/L^2; 0, -6*EI/L^2, 4*EI/L]\n"
        "F := [10[kN]; 0; 0]\nd := solve(K, F)\nv := d[2]\ntheta := d[3]\n"
        "V := 12*EI/L^3*v\nM := 4*EI/L*theta\nS := 12*EI/L^3*v - 6*EI/L^2*theta\n",
        monkeypatch,
    )
    assert not console, console
    assert r"v & = & d_{2} = 0.00\,\mathrm{m}" in page, page
    assert r"\theta & = & d_{3} = 0.00 \\" in page, page
    assert r"V & = & 0.00\,\mathrm{kN} \\" in page, page
    assert r"M & = & 0.00\,\mathrm{kN} \cdot \mathrm{m} \\" in page, page
    assert r"S & = & 0.00\,\mathrm{kN}" in page, page[-300:]


@pytest.mark.parametrize(
    "line, ending",
    [
        # A zero of unknown kind solved against: still unknown.
        ("I := [1, 0; 0, 1]\nt := solve(I, d)[2]", r"= 0.00 \end{array}"),
        ("I := [1, 0; 0, 1]\nt := (transpose(d)*I)[1, 2]", r"= 0.00 \end{array}"),
        # The inverse of springs is of one kind: its zero borrows m/kN, as on main.
        ("t := inv([k, 0; 0, k])[1, 2]", r"= 0.00\,\frac{\mathrm{m}}{\mathrm{kN}} \end{array}"),
    ],
)
def test_what_a_worked_zero_becomes_through_a_solve_a_product_and_an_inverse(line, ending, monkeypatch):
    page, console = _run(_FRAME_ZERO + line + "\n", monkeypatch)
    assert not console, console
    assert page.rstrip().endswith(ending), page[-300:]


@pytest.mark.parametrize(
    "sheet, line, ending",
    [
        # Equilibrium written as a system [M; H; V]: V is a force, not the moment loaded first.
        ("H_0 := 10[kN]\nh := 3[m]\nA := [1, 0, 0; 0, 1, 0; 0, 0, 1]\nb := [H_0*h; -H_0; 0]\n"
         "x := solve(A, b)\n", "V := x[3]", r"= 0.00 \end{array}"),
        # A rotation solved through a transformation keeps no length.
        ("c := 0.8\ns := 0.6\nG := [c, s, 0, 0, 0, 0; -s, c, 0, 0, 0, 0; 0, 0, 1, 0, 0, 0; "
         "0, 0, 0, c, s, 0; 0, 0, 0, -s, c, 0; 0, 0, 0, 0, 0, 1]\n"
         "u := [1[mm]; 2[mm]; 0; 3[mm]; 1[mm]; 0.01]\nD := solve(G, u)\n",
         "a := D[3]", r"= 0.00 \end{array}"),
        # A diagonal whose work has no whole root: no unit is made up.
        ("K := [1000[kN/m], 0; 0, 1000[kN/m^2]]\nF := [10[kN]; 0]\nd := solve(K, F)\n",
         "t := d[2]", r"= 0.00 \end{array}"),
        # Only the second load column carries a unit: the first is still read by its work.
        ("k := 1000[kN/m]\nK := [k, 0; 0, k]\nF := [0, 10[kN]; 0, 0]\nd := solve(K, F)\n",
         "t := d[2, 2]", r"= 0.00\,\mathrm{m} \end{array}"),
    ],
)
def test_the_work_rule_is_for_stiffnesses(sheet, line, ending, monkeypatch):
    """The fourth audit of 0.45.6: by work, a solve that is no stiffness - equilibrium, a
    transformation - took the unit of its first load for an unknown of another kind. A
    stiffness's diagonal has a dimension; where it has none the rule does not apply."""
    page, console = _run(sheet + line + "\n", monkeypatch)
    assert not console, console
    assert page.rstrip().endswith(ending), page[-300:]


_AXIAL_FRAME = (
    "EA := 2000[kN]\nEI := 500[kN*m^2]\nL := 2[m]\n"
    "K := [EA/L, 0, 0; 0, 12*EI/L^3, -6*EI/L^2; 0, -6*EI/L^2, 4*EI/L]\n"
)


def test_the_work_rule_reads_a_load_in_any_column(monkeypatch):
    """The fourth audit's follow-up: a load only in the second column, on a frame (springs
    borrow their unit without the rule)."""
    page, console = _run(
        _AXIAL_FRAME + "F := [0, 10[kN]; 0, 0; 0, 0]\nd := solve(K, F)\nt := d[2, 2]\nr := d[3, 2]\n",
        monkeypatch,
    )
    assert not console, console
    assert r"t & = & d_{2,2} = 0.00\,\mathrm{m}" in page, page[-500:]
    assert page.rstrip().endswith(r"r & = & d_{3,2} = 0.00 \end{array}"), page[-300:]


def test_a_zero_on_the_diagonal_gets_no_unit_by_work(monkeypatch):
    k = "k := 1000[kN/m]\n"
    page, console = _run(
        k + "K := [k, 0, 0; 0, 0, k; 0, k, 0]\nF := [10[kN]; 0; 0]\nd := solve(K, F)\nt := d[2]\n",
        monkeypatch,
    )
    assert not console, console
    assert "t & = & d_{2} = 0.00" in page, page[-300:]


def test_a_complex_pair_beside_a_large_eigenvalue_is_refused(monkeypatch):
    """The Codex review of #395: the tolerance on the imaginary part was the largest
    eigenvalue's, so ±i beside 1e12 passed as two real zeros. Each is judged by its own size,
    above a floor of round-off on the whole spectrum."""
    _, console = _run("A := [0, -1, 0; 1, 0, 0; 0, 0, 1e12]\nv := eigenvals(A)\n", monkeypatch)
    assert "not real" in console, console

    page, console = _run("C := [2, 1, 0; 1, 2, 0; 0, 0, 1e12]\nw := eigenvals(C)\n", monkeypatch)
    assert not console, console
    assert r"1.00" in page and r"3.00" in page, page
