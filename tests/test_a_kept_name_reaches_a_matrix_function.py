r"""A kept name inside a function whose value is a matrix stands for itself in its row.

Found while fixing `numeric(M(L/2))` (#362, 2026-09-27): over `k = E*A/L`, kept because its
names have values, `K_2 = [k, -k; -k, k]` read `k`, and `K(x) = [k*x, 0; 0, k]` read
`[E A x/L, 0; 0, E A/L]`. A function keeps its written body only when the line reaches a
kept name, and a matrix written on the line reaches the evaluator as one placeholder name:
the names in its cells were never looked at. The numbers are the same.
"""

import contextlib
import io

from IPython.display import Math

import engcalc_colab.magic as magic

SHEET = (
    "E := 200[GPa]\nA := 10[cm^2]\nL := 3[m]\nk = E*A/L\n"
    "K(x) = [k*x, 0; 0, k]\nnumeric(K(2))\n"
)


def _page(source: str, monkeypatch) -> tuple[str, str]:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    latex = " ".join(item.data for item in captured if isinstance(item, Math))
    return latex.replace(r"\displaystyle ", ""), console.getvalue()


def _row(page: str, name: str) -> str:
    start = page.index(name + r" & = &")
    end = page.find(r"\rule{0pt}", start)
    return page[start:end if end != -1 else None]


def test_the_function_row_reads_the_kept_name(monkeypatch):
    page, console = _page(SHEET, monkeypatch)
    assert not console, console
    row = _row(page, r"K\left(x\right)")
    assert r"k x & 0\\" in row, row
    assert r"\frac{E A x}{L}" not in row, row


def test_the_call_opens_with_the_written_body_and_its_number_is_the_same(monkeypatch):
    page, _console = _page(SHEET, monkeypatch)
    rows = page[page.index(r"K\left(2\right) & = &"):]
    # The call writes its argument where `x` was (2026-09-27): `k \cdot 2`, the kept `k`
    # standing. See `test_numeric_of_a_call_writes_its_argument`.
    assert r"k \cdot 2 & 0\\" in rows, rows
    assert r"\frac{E A x}{L}" not in rows, rows
    assert rows.rstrip().endswith(
        r"10^{3}\,\left[\begin{matrix}133.33 & 0.00\\[3pt]0.00 & 66.67\end{matrix}\right]"
        r"\,\frac{\mathrm{kN}}{\mathrm{m}} \end{array}"
    ), rows


def test_a_matrix_function_with_nothing_kept_is_as_it_was(monkeypatch):
    page, console = _page("k = E*A/L\nK(x) = [k*x, 0; 0, k]\n", monkeypatch)
    assert not console, console
    row = _row(page, r"K\left(x\right)")
    assert r"\frac{x E A}{L}" in row, row


def test_a_later_line_that_calls_it_reads_the_kept_name(monkeypatch):
    page, console = _page(SHEET + "D = K(2)\nnumeric(D)\n", monkeypatch)
    assert not console, console
    row = _row(page, "D")
    assert r"2 k" in row, row
    assert r"\frac{2 E A}{L}" not in row, row
    assert page.rstrip().endswith(
        r"10^{3}\,\left[\begin{matrix}133.33 & 0.00\\[3pt]0.00 & 66.67\end{matrix}\right]"
        r"\,\frac{\mathrm{kN}}{\mathrm{m}} \end{array}"
    ), page
