r"""What chapter 7 of his book found read wrong or refused (2026-10-01).

Numbers that read wrong:
- a flexibility `L/(E*I)` in MPa and mm^4 printed `0.00 m/(MPa·mm^4)`, the zero tolerance
  applied to 4.0e-13 (problem 7.22); a bimoment read `m³·kg/s²` (problem 7.13);
- a table column of a ratio `x/a` with `x` in inches and `a` in feet was headed `[in/ft]`
  and read 6.00 for 0.5 (Example 7.4);
- the written `0` of `[0; 2[1/m]]`, taken out, carried the metre of what multiplied it.

Refused or silent:
- `solve` of the constants of `C_1*integrate(1/(3 - x), x) + C_2`: "no solution", SymPy's
  antiderivative being `-log(x - 3)` (problem 7.10);
- `numeric` of `log(5*L/2) - log(3*L/2)`: "log requires a dimensionless argument";
- `integrate` of a matrix, `zeros`, `diag` and a part `K[[1, 2], [1, 2]]` on a `:=` line
  (problems 7.23 and 7.29);
- `psi` read as pounds per square inch after `assume(psi > 0)` (problem 7.23);
- `subs(f, [a, b], [1, 2])` replaced nothing and said nothing (problem 7.17);
- `atanh` unknown (problem 7.10).
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


def _run(source: str, monkeypatch, palette: str | None = None) -> tuple[str, str]:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    magics = magic.EngMagics()
    with contextlib.redirect_stdout(console):
        if palette:
            magics.eng_units(palette)
        magics.eng("", source)
    latex = " ".join(item.data for item in captured if isinstance(item, Math))
    return latex.replace(r"\displaystyle ", ""), console.getvalue()


@pytest.mark.parametrize("palette", [None, "kN"])
def test_a_flexibility_reads_in_a_force_and_a_length(monkeypatch, palette):
    page, console = _run(
        "E := 200000[MPa]\nI := 150e6[mm^4]\nL := 12[m]\nf := L/(E*I)\nd := [L; 1[m]]/(E*I)\n",
        monkeypatch,
        palette,
    )
    assert r"f & = & 0.0004\,\frac{1}{\left(\mathrm{kN} \cdot \mathrm{m}\right)}" in page, page
    assert r"\frac{1}{\left(\mathrm{kN} \cdot \mathrm{m}\right)} \end{array}" in page, page
    assert "MPa} \\cdot" not in page and r"\mathrm{kg}" not in page, page


def test_a_typed_unit_is_still_kept(monkeypatch):
    page, console = _run("c := 3[m/kN]\n", monkeypatch)
    assert r"3.00\,\frac{\mathrm{m}}{\mathrm{kN}}" in page, page


def test_a_column_of_ratios_is_a_number(monkeypatch):
    page, console = _run(
        "a := 2[ft]\nf(x) = x/a\ntable(f(x), x, 0[in], 24[in], 3)\n", monkeypatch
    )
    assert not console, console
    assert r"\frac{\mathrm{in}}{\mathrm{ft}}" not in page, page
    assert "12.00 & 0.50" in page and "24.00 & 1.00" in page, page


def test_a_written_zero_takes_the_unit_of_its_vector(monkeypatch):
    page, console = _run(
        "GJ := 10[kN*m^2]\nT := 5[kN*m]\nD := [0; 2[1/m]]\ns := GJ*D[1]/T\n", monkeypatch
    )
    assert not console, console
    assert r"= 0.00 \end{array}" in page, page


def test_a_stiffness_keeps_its_plain_zero(monkeypatch):
    page, console = _run("K := [0, 2[kN]; 3[kN*m], 0]\nk := K[1, 1]\n", monkeypatch)
    assert not console, console
    assert r"k & = & K_{1,1} = 0" in page, page


def test_the_constants_of_a_log_are_solved(monkeypatch):
    page, console = _run(
        "u(x) = C_1*integrate(1/(3 - x), x) + C_2\nsolve(eq(u(0), 0), eq(u(1), 1), C_1, C_2)\n"
        "w(x) = integrate(1/(3 - t), t, 0, x)\n",
        monkeypatch,
    )
    assert not console, console
    assert r"\log{\left(3 - x \right)}" in page, page
    assert "i" not in page.split("w\\left(x\\right)")[1].replace("\\int", "").replace(
        "\\limits", ""
    ).replace("\\right", "").replace("\\left", "").replace("\\displaystyle", ""), page


def test_a_log_of_a_ratio_of_lengths_has_a_number(monkeypatch):
    page, console = _run(
        "g = log(5*L/2) - log(3*L/2)\nL := 3[m]\nnumeric(g)\nh := log(L) - log(2*L)\n",
        monkeypatch,
    )
    assert not console, console
    assert page.count("= & 0.51") >= 1 and r"h & = &" in page, page
    assert "-0.69" in page, page


def test_a_log_of_a_length_is_still_refused(monkeypatch):
    page, console = _run("L := 3[m]\nh := log(L)\n", monkeypatch)
    assert "log requires a dimensionless argument" in console, console


def test_matrices_built_on_a_numeric_line(monkeypatch):
    page, console = _run(
        "R := 2[m]\nd := integrate([R*cos(phi); 1]*[R*cos(phi), 1], phi, 0, pi/2)\n"
        "t := integrate(R*cos(phi), phi, 0, pi/2)\nk := 5[kN/m]\nS := diag(k, 2*k)\n",
        monkeypatch,
    )
    assert not console, console
    assert r"3.14\,\mathrm{m}^{2} & 2.00\,\mathrm{m}" in page, page
    assert r"\int\limits_{0}^{\frac{\pi}{2}}" in page and r"\cos{\left(\phi\right)}" in page, page
    assert r"\operatorname{integrate}" not in page and r"\operatorname{cos}" not in page, page
    assert r"= 2.00\,\mathrm{m}" in page, page
    assert r"5.00 & 0.00\\[3pt]0.00 & 10.00" in page, page


def test_a_stiffness_assembled_in_numbers(monkeypatch):
    page, console = _run(
        "k_1 := 2[kN/m]\nk_2 := 3[kN/m]\nK := zeros(3, 3)\n"
        "% for p, q, k in [(1, 2, k_1), (2, 3, k_2)]:\n"
        "K[[{p}, {q}], [{p}, {q}]] := K[[{p}, {q}], [{p}, {q}]] + {k}*[1, -1; -1, 1]\n% end\n"
        "F := [0[kN]; 6[kN]]\nd := solve(K[[2, 3], [2, 3]], F)\nK[1, 3] := 7[kN/m]\n",
        monkeypatch,
    )
    assert not console, console
    assert r"2.00 & -2.00 & 0.00\\[3pt]-2.00 & 5.00 & -3.00\\[3pt]0.00 & -3.00 & 3.00" in page, page
    assert r"3.00\\[3pt]5.00\end{matrix}\right]\,\mathrm{m}" in page, page
    assert r"2.00 & -2.00 & 7.00" in page, page
    assert r"K_{1,3} & = &" in page, page


def test_a_part_of_a_matrix_with_nothing_to_assign_into(monkeypatch):
    page, console = _run("K[1, 1] := 2[kN/m]\n", monkeypatch)
    assert "K has no matrix of numbers to assign into" in console, console


def test_an_assumed_psi_is_the_angle(monkeypatch):
    page, console = _run("assume(psi > 0)\nd = integrate(sin(phi), phi, 0, psi)\n", monkeypatch)
    assert not console, console
    assert r"\int\limits_{0}^{\psi}" in page and r"\mathrm{psi}" not in page, page


def test_subs_with_two_lists(monkeypatch):
    page, console = _run(
        "f = a*b + a\ng = subs(f, [a, b], [1, 2])\nM = [a*b; a]\nG = subs(M, [a, b], [1, 2])\n",
        monkeypatch,
    )
    assert not console, console
    assert r"g & = & 3" in page and r"2\\[3pt]1\end{matrix}" in page, page
    page, console = _run("f = a*b\ng = subs(f, [a, b], [1])\n", monkeypatch)
    assert "subs has 2 variables and 1 values" in console, console


def test_atanh(monkeypatch):
    page, console = _run("y := atanh(0.5)\nf(x) = atanh(x/2)\n", monkeypatch)
    assert not console, console
    assert r"y & = & 0.55" in page, page


def test_the_chapter_s_pages_are_typeset_by_colab_s_katex(monkeypatch):
    from test_colab_can_typeset_every_formula import _formulas, _katex_available, _typeset

    if not _katex_available():
        pytest.skip("KaTeX is not installed; run `npm ci --prefix tools/katex`")
    source = (
        "R := 2[m]\nd := integrate([R*cos(phi); 1]*[R*cos(phi), 1], phi, 0, pi/2)\n"
        "K := zeros(3, 3)\nK[[1, 2], [1, 2]] := K[[1, 2], [1, 2]] + 2[kN/m]*[1, -1; -1, 1]\n"
        "E := 200000[MPa]\nI := 150e6[mm^4]\nf := R/(E*I)\n"
    )
    formulas = _formulas(source, "", monkeypatch)
    results = _typeset(formulas)["results"]
    failed = [result["error"] for result in results if result["error"]]
    assert not failed, failed


def test_a_bracket_unit_in_a_matrix_is_a_measurement(monkeypatch):
    page, console = _run(
        "F := [10[kN]; 0[kip*in^2]]\nD := [1; 0.002[1/in]]\nG := [3[kip*in], 2[kip*in^2]]\n",
        monkeypatch,
    )
    assert not console, console
    assert r"0\,\mathrm{kip} \cdot \mathrm{in}^{2}" in page, page
    assert r"\frac{0.002}{\mathrm{in}}" in page, page
    assert r"3\,\mathrm{kip} \cdot \mathrm{in} & 2\,\mathrm{kip} \cdot \mathrm{in}^{2}" in page, page
    assert r"1\,\mathrm{in}" not in page and r"\cdot 1}" not in page, page


# What the audit of 0.45.3 found in the first draft of these fixes.


def test_a_column_of_angles_keeps_its_degrees(monkeypatch):
    page, console = _run(
        "f(t) = 2*t\ntable(f(t), t, 0[deg], 90[deg], 3)\n"
        "% for i, a in [(1, 30), (2, 45)]:\nt_{i} := {a}[deg]\nc_{i} := cos(t_{i})\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"t\,[{}^{\circ}] & f\left(t\right)\,[{}^{\circ}]" in page, page
    assert r"t_{i}\,[{}^{\circ}]" in page, page


def test_an_assumed_psi_has_no_value_on_a_numeric_line(monkeypatch):
    page, console = _run("assume(psi > 0)\nr := 3*psi\n", monkeypatch)
    assert "unknown numeric name 'psi'" in console, console


def test_a_log_of_a_product_of_negative_numbers(monkeypatch):
    page, console = _run("a := -2\nb := -3\nw = log(a*b) + 1\nnumeric(w)\n", monkeypatch)
    assert not console, console
    assert r"= & 2.79" in page, page


def test_a_log_of_a_ratio_of_two_lengths(monkeypatch):
    page, console = _run("L_1 := 3[m]\nL_2 := 6[m]\ny := log(L_1) - log(L_2)\n", monkeypatch)
    assert not console, console
    assert r"y & = & -0.69" in page, page


def test_an_indefinite_integral_keeps_a_symbol_s_sign(monkeypatch):
    page, console = _run(
        "assume(a > 0)\nF = integrate(1/(t - a), t)\nG = subs(F, t, 2*a)\n"
        "assume(L > 0)\nw(x) = integrate(1/(3*L - 2*t), t, 0, x)\n",
        monkeypatch,
    )
    assert not console, console
    assert r"\log{\left(t - a \right)}" in page and r"G & = & \log{\left(a \right)}" in page, page
    assert r"\frac{\log{\left(3 L \right)}}{2} - \frac{\log{\left(3 L - 2 x \right)}}{2}" in page, page


def test_a_part_index_counted_in_a_loop(monkeypatch):
    page, console = _run(
        "k := 2[kN/m]\nK := zeros(3, 3)\n% for e in [1, 2]:\n"
        "K[[{e}, {e}+1], [{e}, {e}+1]] := K[[{e}, {e}+1], [{e}, {e}+1]] + k*[1, -1; -1, 1]\n% end\n",
        monkeypatch,
    )
    assert not console, console
    assert r"-2.00 & 4.00 & -2.00" in page, page
    assert r"\textbf{Ensamble en 2 pasos}" in page, page
    # The matrix it built, not the last pass's row read as the only one added.
    assert r"K_{\left[2,3\right],\left[2,3\right]} & = &" not in page, page
    page, console = _run("J := zeros(2, 2)\nJ[[1, 3], [1, 3]] := zeros(2, 2)\n", monkeypatch)
    assert "'J[[1, 3], [1, 3]]' is outside the 2x2 matrix" in console, console
