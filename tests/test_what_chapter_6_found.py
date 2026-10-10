r"""What chapter 6 of his book found breaking the page or leaving an unknown in (2026-10-01).

- the definite integral of a formula with bracket units, `W = integrate((270[kN*m] -
  30[kN]*x)*(L - x), x, 6[m], L)`, stopped the cell: "renderer semantic spacing metadata
  does not match rendered row count" (problem 6.15);
- the equation row of `N_b := solve(eq(dW, 0), N_b)` whose formula holds a bracket unit
  printed `\mathit{__u}_{kN}`, red in Colab (problem 6.1b);
- a `piecewise` inside a `piecewise` - the way to write three pieces - printed a literal
  `[4pt]` before its last case and nested one `cases` block in another;
- `q = solve(eq(2*q, P), q)` did not reach `g(x) = q*x` written before it, where a solve of
  a system does: `g(2)` read `2 q`.
"""

import contextlib
import io

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


def test_the_integral_of_a_formula_with_bracket_units_is_drawn(monkeypatch):
    page, console = _run(
        "L := 9[m]\nW = integrate((270[kN*m] - 30[kN]*x)*(L - x), x, 6[m], L)\nZ = 1\n",
        monkeypatch,
    )
    assert not console, console
    assert r"\int\limits_{6\,\mathrm{m}}^{L}" in page, page
    assert r"- 5\,\mathrm{kN}\,L^{3}" in page, page
    assert r"Z & = & 1" in page, page


def test_a_sum_of_integrals_over_a_stiffness_is_drawn(monkeypatch):
    page, console = _run(
        "L := 9[m]\nEI := 50000[kN*m^2]\n"
        "D = (integrate((270[kN*m] - 30[kN]*x)*(L - x), x, 0[m], 3[m]) "
        "+ integrate(20[kN]*x*(L - x), x, 3[m], L))/EI\n",
        monkeypatch,
    )
    assert not console, console
    assert r"\int\limits_{3\,\mathrm{m}}^{L}" in page, page


def test_a_solve_s_equation_row_shows_its_units(monkeypatch):
    page, console = _run(
        "x_6 := 5[m]\ndW = N_b*t - 50[kN]*x_6*t\nN_b := solve(eq(dW, 0), N_b)\n", monkeypatch
    )
    assert not console, console
    assert "__u" not in page, page
    assert r"\mathrm{kN}" in page, page


def test_a_piecewise_in_a_piecewise_is_one_list_of_cases(monkeypatch):
    page, console = _run("f(x) = piecewise(1, x < 1, piecewise(2, x < 2, 3))\n", monkeypatch)
    assert not console, console
    assert "[4pt] [4pt]" not in page and r"\\[4pt] [4pt]" not in page, page
    assert page.count(r"\begin{cases}") == 1, page
    assert r"2 & \text{si}\: x < 2" in page and r"3 & \text{en otro caso}" in page, page


def test_a_piecewise_in_a_branch_keeps_both_conditions(monkeypatch):
    page, console = _run(
        "f(x) = piecewise(piecewise(1, x > 0, 2), x < 3, 4)\nv := f(-1)\nw := f(1)\n",
        monkeypatch,
    )
    assert not console, console
    assert page.count(r"\begin{cases}") == 1, page
    assert r"v & = & 2.00" in page and r"w & = & 1.00" in page, page


def test_a_name_solved_for_itself_reaches_a_function_written_before(monkeypatch):
    page, console = _run(
        "g(x) = q*x\nq = solve(eq(2*q, P), q)\nz = g(2)\nP := 10[kN]\nnumeric(z)\n", monkeypatch
    )
    assert not console, console
    assert r"z & = & g\left(2\right) \\[8pt]  & = & P" in page, page
    assert r"= & 10.00\,\mathrm{kN}" in page, page


def test_a_solve_for_another_name_defines_only_that_name(monkeypatch):
    page, console = _run("g(x) = q*x\nk = solve(eq(2*q, P), q)\nz = g(2)\n", monkeypatch)
    assert not console, console
    assert r"& = & 2 q" in page, page


def test_the_variable_of_a_function_solved_for_a_point_stays_a_variable(monkeypatch):
    page, console = _run(
        "V(x) = 10 - 2*x\nM(x) = 10*x - x^2\nx = solve(eq(V(x), 0), x)\nm = M(1)\n", monkeypatch
    )
    assert not console, console
    assert r"m & = & M\left(1\right) \\[8pt]  & = & 9" in page, page


def test_the_chapter_s_pages_are_typeset_by_colab_s_katex(monkeypatch):
    from test_colab_can_typeset_every_formula import _formulas, _katex_available, _typeset

    if not _katex_available():
        pytest.skip("KaTeX is not installed; run `npm ci --prefix tools/katex`")
    source = (
        "L := 9[m]\nW = integrate((270[kN*m] - 30[kN]*x)*(L - x), x, 6[m], L)\n"
        "x_6 := 5[m]\ndW = N_b*t - 50[kN]*x_6*t\nN_b := solve(eq(dW, 0), N_b)\n"
        "f(x) = piecewise(1, x < 1, piecewise(2, x < 2, 3))\n"
    )
    formulas = _formulas(source, "", monkeypatch)
    results = _typeset(formulas)["results"]
    failed = [result["error"] for result in results if result["error"]]
    assert not failed, failed
