r"""What chapter 8 of his book found read wrong or refused (2026-10-02).

- `solve(eq(...), t, 0[deg], 15[deg])` returned a number in degrees read as radians:
  `sin(t_1)` was 0.0231 for 0.1098 (Example 8.2);
- a ratio holding `atan(1)^2` read `0.62 rad²` (Example 8.7);
- `subs` and `sum` on a `:=` line: "unsupported numeric function";
- a definite integral SymPy writes with `i` and `Min(...)`, or not at all, had no number,
  and `elliptic_k` neither (Example 8.5, problem 8.3);
- `plot` of an `interp` function refused at its table's own last point (problem 8.8).
"""

import contextlib
import io

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


def test_a_root_found_in_degrees_is_an_angle(monkeypatch):
    page, console = _run(
        "a := 15[deg]\nt_1 := solve(eq(cos(a - t)^3, cos(a)), t, 0[deg], 15[deg])\ny := sin(t_1)\n",
        monkeypatch,
    )
    assert not console, console
    assert r"t_{1} & = & 6.31^{\circ}" in page, page
    assert r"y & = & 0.11" in page, page


def test_a_root_without_a_unit_is_a_number(monkeypatch):
    page, console = _run("x_0 := solve(eq(x^2, 2), x, 0, 3)\n", monkeypatch)
    assert r"x_{0} & = & 1.41" in page, page


def test_a_power_of_an_angle_is_a_number(monkeypatch):
    page, console = _run("b := atan(1)\nP := 10[kN]*b^2\nr := P/(10[kN])\n", monkeypatch)
    assert not console, console
    assert r"r & = & 0.62 \end{array}" in page, page
    assert r"b & = & 45.00^{\circ}" in page, page


def test_subs_and_sum_on_a_numeric_line(monkeypatch):
    page, console = _run(
        "f = 2*sin(t)\nt_0 := 30[deg]\nx_1 := subs(f, t, t_0)\nk := 0.17\nN := 40\n"
        "K := pi/(2*N)*sum(1/sqrt(1 - k^2*sin((j - 1/2)*pi/(2*N))^2), j, 1, N)\n"
        "g(x) = x^2\ny := subs(g(x), x, 3[m])\n",
        monkeypatch,
    )
    assert not console, console
    assert r"x_{1} & = & \left. f \right|_{t=t_{0}} = 1.00" in page, page
    assert r"\sum_{j=1}^{N}" in page and "= 1.58" in page, page
    assert r"\left. g\left(x\right) \right|_{x=3\,\mathrm{m}} = 9.00\,\mathrm{m}^{2}" in page, page


def test_an_integral_with_no_closed_form_has_a_number(monkeypatch):
    page, console = _run(
        "assume(a > 0, L > 0, x > 0)\nJ = integrate(x^2/(1 - x/(2*a))^(3/2), x, a, L)\n"
        "a := 1[m]\nL := 1.5[m]\nnumeric(J)\nb := 1[m]\nc := 1.5[m]\n"
        "H := integrate(x^2/(1 - x/(2*b))^(3/2), x, b, c)\n",
        monkeypatch,
    )
    assert not console, console
    assert page.count(r"3.96\,\mathrm{m}^{3}") == 2, page
    assert r"\int\limits_{a}^{L}" in page and r"\mathrm{Min}" not in page and " i " not in page, page


def test_an_elliptic_integral_has_a_number(monkeypatch):
    page, console = _run(
        "k := 0.2\nF(q) = integrate(1/sqrt(1 - q^2*sin(phi)^2), phi, 0, pi/2)\nG := F(k)\n",
        monkeypatch,
    )
    assert not console, console
    assert r"G & = & 1.59" in page, page


def test_an_interp_is_drawn_to_its_last_point(monkeypatch):
    page, console = _run(
        "E := 29000[ksi]\nI := 1170[in^4]\nM_p := 36[ksi]*146[in^3]\n"
        "k_v(L) = E*I/L^3*[12, 6*L, -12, 6*L; 6*L, 4*L^2, -6*L, 2*L^2; -12, -6*L, 12, -6*L; 6*L, 2*L^2, -6*L, 4*L^2]\n"
        "k_ab = k_v(96[in])\nd_1 := solve(k_ab[[3, 4], [3, 4]], [-1[kip]; 0[kip*in]])\n"
        "D_1 := [0[in]; 0; d_1[1]; d_1[2]]\nf_1 := k_ab*D_1\nP_1 := M_p/abs(f_1[2]/1[kip])\n"
        "delta_1 := -P_1*d_1[1]/1[kip]\n"
        "Pd(x) = interp(x, [0[in], delta_1, 2*delta_1], [0[kip], P_1, P_1])\n"
        "plot(Pd(x), x, 0[in], 2*delta_1)\n",
        monkeypatch,
    )
    assert "does not extrapolate" not in console, console


def test_interp_still_refuses_to_extrapolate(monkeypatch):
    page, console = _run(
        "P(x) = interp(x, [0[m], 2[m]], [0[kN], 10[kN]])\ny := P(3[m])\n", monkeypatch
    )
    assert "interp does not extrapolate: 3 m lies outside its table, 0 m to 2 m" in console, console


# What the audit of these fixes found in their first draft.


def test_a_ratio_root_is_a_number_not_an_angle(monkeypatch):
    page, console = _run(
        "x := solve(eq(x, 3[mm/m]), x, 0[mm/m], 10[mm/m])\nz := x*1000\n", monkeypatch
    )
    assert not console, console
    assert r"x & = & 0.003" in page and r"z & = & 3.00" in page, page
    assert r"^{\circ}" not in page, page


def test_a_divergent_integral_is_said(monkeypatch):
    page, console = _run("K = integrate(sqrt(x)/(x - 1)^2, x, 0, 2)\nnumeric(K)\n", monkeypatch)
    assert "the value is not finite" in console, console
