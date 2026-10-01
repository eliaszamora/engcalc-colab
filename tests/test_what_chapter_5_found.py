r"""What chapter 5 of his book found refused, silent or wrong on the page (2026-09-30).

- `numeric` of a matrix whose `E*I` cancels stopped after its substitution row, silently;
  the scalar form said "requires values for: E, I" (problem 5.5);
- `A := solve(eq(...), eq(...), x, y)` on a `:=` line failed with "'NoneType' object has
  no attribute 'free_symbols'" (example 5.12);
- a loop line `{r}_a = {r} + 1` was refused before it ran, "invalid assignment target
  '1_a'" (problem 5.9);
- an undefined `psi` was read as pounds per square inch with no word (problem 5.17);
- `10.6[in^2]` was "not a unit" (problem 5.10);
- a function's parameter `s` or `m` was set as the second or the metre (every `(c, s)`
  rotation of the chapter);
- a 12 x 12 matrix whose entries carry typed units ran past KaTeX's 1000 expansions, and
  Colab drew it as red source (problem 5.10d).
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


def test_a_matrix_whose_unknowns_cancel_has_a_number(monkeypatch):
    source = (
        "L_1 := 2[m]\nL_2 := 4[m]\nP := 10[kN]\ntheta = P*L_1^2/(E*I)\n"
        "R = [E*I/L_1^2 + E*I/L_2^2; E*I/L_2^2]*theta\nnumeric(R)\n"
        "r = (E*I/L_1^2 + E*I/L_2^2)*theta\nnumeric(r)\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"12.50\\[3pt]2.50\end{matrix}\right]\,\mathrm{kN}" in page, page
    assert r"= & 12.50\,\mathrm{kN}" in page, page


def test_names_that_do_not_cancel_are_still_asked_for(monkeypatch):
    page, console = _run("P := 10[kN]\nt = P/(E*I)\nnumeric(t)\n", monkeypatch)
    assert "requires values for: E, I" in console, console


def test_a_system_solve_on_a_numeric_line_says_what_to_write(monkeypatch):
    page, console = _run(
        "c := 0.5\nB := 6000\nA := solve(eq(x*c + y*c, 0), eq(x*c - y*c + B, 0), x, y)\n", monkeypatch
    )
    assert "solve of a system must be a standalone statement" in console, console
    assert "NoneType" not in console, console


def test_a_loop_line_whose_name_starts_with_a_value(monkeypatch):
    page, console = _run("x = a + b\nw = a - b\n% for r in [\"x\", \"w\"]:\n{r}_a = {r} + 1\n% end\n", monkeypatch)
    assert not console, console
    assert r"x_{a} & = & a + b + 1" in page and r"w_{a} & = & a - b + 1" in page, page


def test_psi_read_as_a_unit_is_said(monkeypatch):
    page, console = _run("y = 2*psi + 3*phi\n", monkeypatch)
    assert "'psi' is read as the unit psi" in console, console
    page, console = _run("f := 60[psi]\n", monkeypatch)
    assert not console, console


def test_the_inch_in_brackets(monkeypatch):
    page, console = _run("A := 10.6[in^2]\nk = E*3[inch^2]/(2[ft])\n", monkeypatch)
    assert not console, console
    assert r"10.60\,\mathrm{in}^{2}" in page, page
    assert r"\mathrm{inch}" not in page, page


def test_a_function_s_parameters_are_its_variables(monkeypatch):
    page, console = _run("f(c, s) = c + 2*s\ng(c, s) = [c, s; -s, c]\nq(m) = 2*m\n", monkeypatch)
    assert not console, console
    assert r"\mathrm{s}" not in page and r"\mathrm{m}" not in page, page


def test_a_large_matrix_with_typed_units_is_typeset_by_colab_s_katex(monkeypatch):
    from test_colab_can_typeset_every_formula import _formulas, _katex_available, _typeset

    if not _katex_available():
        pytest.skip("KaTeX is not installed; run `npm ci --prefix tools/katex`")
    row = ", ".join(["E*3[inch^2]/(2[ft])"] * 12)
    source = "K = [" + "; ".join([row] * 12) + "]\n"
    formulas = _formulas(source, "", monkeypatch)
    results = _typeset(formulas)["results"]
    failed = [result["error"] for result in results if result["error"]]
    assert not failed, failed
