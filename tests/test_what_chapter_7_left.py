r"""What chapter 7 of his book left after 0.45.3 (his "aborda lo pendiente", 2026-10-01).

- `inv` of a 3 x 3 flexibility of sines and cosines took 100 s (problem 7.29);
- an integral of `(x/L)^k (1 - (x/L)^n)` never returned (problem 7.17);
- no integer assumption: `sin(n*pi)` stayed (problem 7.17);
- `simplify` put joint displacements in an exponent, `log(2^(16 v_A + 48 v_B))`, and a
  derivative then carried `2^(-16 v_A) 2^(16 v_A)` (problems 7.4, 7.20);
- a definite integral came as `6a/L + (3c - 9a)/L + (4a - 4c)/L` (Example 7.8);
- the natural log printed `log`.
"""

import contextlib
import io
import time

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


def test_the_inverse_of_an_arch_s_flexibility_is_quick(monkeypatch):
    started = time.perf_counter()
    page, console = _run(
        "a_0 := 0.985\nQ(phi) = [sin(a_0) - sin(phi), cos(phi) - cos(a_0), -1]\n"
        "d = integrate(transpose(Q(phi))*Q(phi), phi, 0, a_0)\nf = inv(d)\nnumeric(f)\n",
        monkeypatch,
    )
    assert time.perf_counter() - started < 30
    assert not console, console
    assert r"189.97 & -329.45 & -24.50\\[3pt]-329.45 & 627.14 & 58.84" in page, page


def test_an_integral_with_symbolic_exponents_returns(monkeypatch):
    started = time.perf_counter()
    page, console = _run(
        "assume(L > 0)\nassume(n > 0)\nassume(k > 0)\n"
        "F = integrate(x*(1 - x/L)^2*(1 - (x/L)^n)*(x/L)^k, x, 0, L)\n",
        monkeypatch,
    )
    assert time.perf_counter() - started < 60
    assert not console, console
    assert r"\frac{L^{2}}{k + 2}" in page, page


def test_a_whole_number(monkeypatch):
    page, console = _run(
        "assume(L > 0)\nassume(n > 0, integer(n))\ns = sin(n*pi)\n"
        "F = integrate(q*sin(n*pi*x/L)^2, x, 0, L)\n",
        monkeypatch,
    )
    assert not console, console
    assert r"n \in \mathbb{Z}" in page, page
    assert r"s & = & 0" in page and r"= \frac{q L}{2}" in page, page


def test_integer_takes_a_name(monkeypatch):
    page, console = _run("assume(integer(2))\n", monkeypatch)
    assert "assume takes comparisons" in console, console


def test_simplify_keeps_the_displacements_out_of_exponents(monkeypatch):
    page, console = _run(
        "F = (11*v_A + 33*v_B - 16*log(2)*v_A - 48*log(2)*v_B)/L^2\nG = simplify(F)\n"
        "c = diff(G, v_A)\nh = simplify(log(65536)*x)\n",
        monkeypatch,
    )
    assert not console, console
    assert "2^{" not in page, page
    assert r"\frac{11 - 16 \ln{\left(2 \right)}}{L^{2}}" in page, page
    assert r"h & = & 16 x \ln{\left(2 \right)}" in page or r"16 \ln{\left(2 \right)} x" in page, page


def test_a_log_of_ten_stays(monkeypatch):
    page, console = _run("h = simplify(log(10)*x)\n", monkeypatch)
    assert r"\ln{\left(10 \right)}" in page, page


def test_a_definite_integral_is_collected(monkeypatch):
    page, console = _run(
        "assume(L > 0)\nf(x) = (6/L^2 - 12*x/L^3)*((1 - x/L)*a + x/L*c)\n"
        "s = integrate(f(x), x, 0, L)\nM = integrate(q*x*(L - x)/2, x, 0, L)\n",
        monkeypatch,
    )
    assert not console, console
    assert r"= & \frac{a - c}{L}" in page, page
    assert r"\frac{q L^{3}}{12}" in page, page


def test_the_natural_log_is_ln(monkeypatch):
    page, console = _run("h = log(x) + ln(2*x)\ny := ln(2)\nM := [log(2); 1]\n", monkeypatch)
    assert not console, console
    assert r"\log" not in page and r"\ln{\left(x \right)}" in page, page
    assert r"y & = & 0.69" in page and r"\ln{\left(2\right)}" in page, page


def test_the_pages_are_typeset_by_colab_s_katex(monkeypatch):
    from test_colab_can_typeset_every_formula import _formulas, _katex_available, _typeset

    if not _katex_available():
        pytest.skip("KaTeX is not installed; run `npm ci --prefix tools/katex`")
    source = (
        "assume(n > 0, integer(n))\nh = ln(x)\n"
        "F = (11*v_A - 16*log(2)*v_A)/L^2\nG = simplify(F)\n"
    )
    formulas = _formulas(source, "", monkeypatch)
    results = _typeset(formulas)["results"]
    failed = [result["error"] for result in results if result["error"]]
    assert not failed, failed


# What the audit of these fixes found in their first draft.


def test_a_mechanism_of_sines_and_cosines_is_still_singular(monkeypatch):
    page, console = _run(
        "T = [cos(t), sin(t), 0, 0; -sin(t), cos(t), 0, 0; 0, 0, cos(t), sin(t); 0, 0, -sin(t), cos(t)]\n"
        "k_l = k*[1, 0, -1, 0; 0, 0, 0, 0; -1, 0, 1, 0; 0, 0, 0, 0]\n"
        "K = transpose(T)*k_l*T + [1, 0, 0, 0; 0, 1, 0, 0; 0, 0, 0, 0; 0, 0, 0, 0]\nf = inv(K)\n",
        monkeypatch,
    )
    assert "inv requires a nonsingular matrix" in console, console
    page, console = _run("M = [sin(t)^2 + cos(t)^2, 1; 1, 1]\nN = inv(M)\n", monkeypatch)
    assert "inv requires a nonsingular matrix" in console, console


def test_the_inverse_of_a_rotation_reads_as_one(monkeypatch):
    page, console = _run("Q = inv([cos(t), sin(t); -sin(t), cos(t)])\n", monkeypatch)
    assert not console, console
    assert (
        r"\cos{\left(t \right)} & - \sin{\left(t \right)}\\[3pt]\sin{\left(t \right)} & \cos{\left(t \right)}"
        in page
    ), page


def test_a_loop_s_labels_write_ln(monkeypatch):
    page, console = _run(
        'x := 2\n% for i, c in [(1, "ln(2)"), (2, "log(3)")]:\ny_{i} := x*{c}\nz_{i} := 2*y_{i}\n% end\n',
        monkeypatch,
    )
    assert not console, console
    assert r"\log" not in page, page


def test_the_powers_of_an_expanded_integral_are_combined(monkeypatch):
    page, console = _run(
        "assume(L > 0)\nassume(n > 0)\nF = integrate((x/L)^n*(1 - x/L), x, 0, L)\n", monkeypatch
    )
    assert not console, console
    assert r"\frac{L}{n + 1} - \frac{L}{n + 2}" in page, page
