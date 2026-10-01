r"""What his book needed and EngCalc could not write (chapters 2-4, 2026-09-30):

- a temperature: Example 2.4 and Problem 2.12 heat a bar, and `[1/degC]`, `[1/K]` were
  "not a unit" - α and ΔT went in as bare numbers, and the page showed them without one;
- `sinh`, `cosh`, `tanh`: a beam on an elastic foundation (Example 4.15) is written with
  them, and they were "unsupported function";
- a row on a `:=` line: `v := [c, s]` was "unsupported numeric syntax 'List'", though the
  book writes a bar's force as `[cos φ, sin φ]` times its stiffness times its displacements.

A temperature in a structural sheet is a change of temperature - ΔT, α ΔT - so `[degC]` is
a difference of degrees, and reads `°C`.
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


def test_a_bar_heated_by_a_change_of_temperature(monkeypatch):
    source = (
        "alpha := 1.17e-5[1/degC]\n"
        "dT := 40[degC]\n"
        "L := 5[m]\n"
        "E := 200000[MPa]\n"
        "A := 1000[mm^2]\n"
        "d := alpha*dT*L\n"
        "F := E*A*alpha*dT\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"40.00\,{}^{\circ}\mathrm{C}" in page or r"40.00\,^{\circ}\mathrm{C}" in page or r"40.00\,\mathrm{{}^\circ C}" in page, page
    assert r"d & = & " in page and r"2.34\,\mathrm{mm}" in page, page
    assert r"93.60\,\mathrm{kN}" in page, page
    assert "delta" not in page and "Delta" not in page, page


def test_a_temperature_in_kelvin_is_the_same_difference(monkeypatch):
    page, console = _run("alpha := 1.2e-5[1/K]\ndT := 30[K]\ne := alpha*dT\n", monkeypatch)
    assert not console, console
    assert "0.00036" in page or r"3.60 \times 10^{-4}" in page, page


def test_the_letter_K_is_still_a_name(monkeypatch):
    page, console = _run("K = [k, -k; -k, k]\nk := 2[kN/mm]\nK_n := K\n", monkeypatch)
    assert not console, console
    assert r"K & = &" in page, page


@pytest.mark.parametrize("name", ["sinh", "cosh", "tanh"])
def test_hyperbolic_functions_are_written_and_worked_out(monkeypatch, name):
    import math

    page, console = _run(f"x := 0.5\ny := {name}(x)\nf = {name}(b*L)\n", monkeypatch)
    assert not console, console
    value = getattr(math, name)(0.5)
    assert f"{value:.2f}" in page, page
    assert rf"\{name}" in page, page


def test_a_row_on_a_numeric_line(monkeypatch):
    source = (
        "phi := 30[deg]\n"
        "v := [cos(phi), sin(phi)]\n"
        "k := 2[kN/mm]\n"
        "u := [3[mm]; 1[mm]]\n"
        "F := k*v*u\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"0.87 & 0.50" in page or r"0.87 & \displaystyle 0.50" in page, page
    assert r"F & = &" in page and r"6.20\,\mathrm{kN}" in page, page


def test_what_these_lines_put_on_the_page_is_typeset_by_colab_s_katex(monkeypatch):
    from test_colab_can_typeset_every_formula import _formulas, _katex_available, _typeset

    if not _katex_available():
        pytest.skip("KaTeX is not installed; run `npm ci --prefix tools/katex`")
    for source in (
        "alpha := 1.17e-5[1/degC]\ndT := 40[degC]\nq := 3[degF]\nt := 30[K]\ne := alpha*dT\n",
        "x := 0.5\ny := sinh(x) + cosh(x) + tanh(x)\nf = sinh(b*L)/cosh(b*L)\n",
        "c := 0.6\ns := 0.8\nv := [c, s]\nw := 2*[c, s]\n",
    ):
        formulas = _formulas(source, "", monkeypatch)
        results = _typeset(formulas)["results"]
        failed = [formula["tex"][:200] for formula, result in zip(formulas, results) if result["error"]]
        assert not failed, failed


def test_a_temperature_is_not_converted_to_another_scale(monkeypatch):
    # A change of 20 °C is a change of 36 °F, and `T_1 = 36.00 °F` read as the thermometer's
    # 20 °C = 36 °F - false (the audit of 0.45.0).
    page, console = _run("T_1 := 20[degC]\nnumeric(T_1, degF)\n", monkeypatch)
    assert "a change in one scale is not the reading in another" in console, console
    assert "36.00" not in page, page
    page, console = _run("T_3 := 300[K]\nnumeric(T_3, K)\n", monkeypatch)
    assert not console, console


def test_temperatures_held_in_numbers_read_in_degrees(monkeypatch):
    page, console = _run("T := [20[degC], 30[degC]]\ndT := T*[1; -1]\n", monkeypatch)
    assert not console, console
    assert r"\mathrm{K}" not in page and "Δ" not in page, page
    assert r"-10.00\,{}^{\circ}\mathrm{C}" in page, page


def test_a_formula_writes_its_degrees(monkeypatch):
    page, console = _run("e = 1.2e-5[1/degC]*(T_b - T_a)\n", monkeypatch)
    assert r"\mathrm{degC}" not in page and r"{}^{\circ}\mathrm{C}" in page, page
