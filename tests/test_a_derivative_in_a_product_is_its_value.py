r"""After the `=`, a derivative or an integral inside a product is worked out with it.

A regression of 0.42.1 (#359), seen 2026-09-27: on a line that reaches a kept name the
written reader walks `diff` and `integrate`, and what they came to was put beside the
typed factor unevaluated - `Z = 2*diff(R_A*x^2, x)` read `= 2 \cdot 2 R_A x`, `diff(...)/2`
read `2 R_A x/2`, `3*x*diff(...)` read `2 \cdot 3 R_A x x`. 0.42.0 read `2 q L x`: the kept
name expanded, the number folded. The formula before the `=` is still the one typed.
"""

import contextlib
import io

from IPython.display import Math

import engcalc_colab.magic as magic

HEAD = "L := 6[m]\nq := 10[kN/m]\nR_A = q*L/2\nV(x) = R_A - q*x\n"


def _page(source: str, monkeypatch) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    assert not console.getvalue(), console.getvalue()
    latex = " ".join(item.data for item in captured if isinstance(item, Math))
    return latex.replace(r"\displaystyle ", "")


def _row(page: str, name: str) -> str:
    start = page.index(name + r" & = &")
    ends = [i for i in (page.find(r"\\[", start), page.find(r"\end{array}", start)) if i != -1]
    return page[start:min(ends)]


def test_a_number_times_a_derivative_is_one_number(monkeypatch):
    row = _row(_page(HEAD + "Z = 2*diff(R_A*x^2, x)\n", monkeypatch), "Z")
    assert row.rstrip().endswith(r"= 4 R_{A} x"), row
    assert r"2 \frac{\partial}{\partial x} R_{A} x^{2}" in row, row


def test_a_derivative_over_a_number_is_divided(monkeypatch):
    row = _row(_page(HEAD + "Z = diff(R_A*x^2, x)/2\n", monkeypatch), "Z")
    assert row.rstrip().endswith(r"= R_{A} x"), row


def test_a_typed_decimal_is_multiplied_in(monkeypatch):
    row = _row(_page(HEAD + "Z = 0.85*diff(R_A*x^2, x)\n", monkeypatch), "Z")
    assert r"0.85 \cdot 2" not in row, row
    assert row.rstrip().endswith(r"= 1.7 R_{A} x"), row


def test_a_product_of_a_name_and_a_derivative_is_collected(monkeypatch):
    row = _row(_page(HEAD + "Z = 3*x*diff(R_A*x^2, x)\n", monkeypatch), "Z")
    assert row.rstrip().endswith(r"= 6 R_{A} x^{2}"), row


def test_a_negated_derivative_over_a_number_is_divided(monkeypatch):
    row = _row(_page(HEAD + "Z = -diff(R_A*x^2, x)/2\n", monkeypatch), "Z")
    assert row.rstrip().endswith(r"= - R_{A} x"), row


def test_a_derivative_first_in_a_longer_product_is_collected(monkeypatch):
    row = _row(_page(HEAD + "Z = diff(R_A*x^2, x)*3*x\n", monkeypatch), "Z")
    assert row.rstrip().endswith(r"= 6 R_{A} x^{2}"), row


def test_the_formula_typed_keeps_its_numbers(monkeypatch):
    row = _row(_page(HEAD + "Z = 2*0.85*diff(R_A*x^2, x)\n", monkeypatch), "Z")
    assert r"1.7 \frac{\partial}" not in row, row
    assert row.rstrip().endswith(r"= 3.4 R_{A} x"), row


def test_a_power_of_a_derivative_is_worked_out(monkeypatch):
    row = _row(_page(HEAD + "Z = diff(R_A*x^2, x)^2\n", monkeypatch), "Z")
    assert row.rstrip().endswith(r"= 4 R_{A}^{2} x^{2}"), row


def test_a_sum_with_a_derivative_is_collected(monkeypatch):
    row = _row(_page(HEAD + "Z = diff(R_A*x^2, x) + R_A*x\n", monkeypatch), "Z")
    assert row.rstrip().endswith(r"= 3 R_{A} x"), row


def test_a_number_times_a_sum_with_a_derivative_is_one_term(monkeypatch):
    row = _row(_page(HEAD + "Z = 2*(diff(R_A*x^2, x) + R_A*x)\n", monkeypatch), "Z")
    assert row.rstrip().endswith(r"= 6 R_{A} x"), row


def test_a_number_times_an_integral_is_worked_out(monkeypatch):
    row = _row(_page(HEAD + "Z = 2*integrate(V(x), x, 0, x)\n", monkeypatch), "Z")
    assert row.rstrip().endswith(r"= 2 R_{A} x - q x^{2}"), row


def test_a_matrix_cell_is_worked_out_the_same(monkeypatch):
    page = _page(HEAD + "W = [2*diff(R_A*x^2, x), 0]\n", monkeypatch)
    row = page[page.index(r"W & = &"):]
    assert r"= \left[\begin{matrix}4 R_{A} x & 0\end{matrix}\right]" in row, row


def test_a_line_with_no_kept_name_is_as_it_was(monkeypatch):
    row = _row(_page("y = 2*diff(x^2, x)\n", monkeypatch), "y")
    assert row.rstrip().endswith(r"= 4 x"), row
