r"""A `% for` that assembles a matrix shows the assembly once; its `:=` values, as one table.

Chapter 3 of his book (2026-09-29): the trusses were right and the page was not. Problem
3.6's memoria was 54 000 px, 63% of it the stiffness matrix printed after every one of
33 bars, 36 x 36 and thirteen page widths wide, and 18% the five rows each bar's L, c, s
took. His decision (2026-09-29, "haz primero 1 + 3 con el resumen cuando la matriz no
quepa"):

1. a `% for` whose line adds into a part of a matrix, `K[...] = K[...] + ...`, works every
   pass out as before and shows it once: how many passes, the rule as the sheet writes it,
   and the matrix it built - or, when that is wider than the page, what it is: its size,
   whether it is symmetric, how many entries are not zero;
2. a `% for` with two or more `:=` values in its body shows them as one table, a row per
   pass. A loop of one `:=` line keeps its rows, as written by hand (approved 2026-09-25).

The numbers are the ones every pass worked out: a name defined in the loop reads as before.
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


SPRINGS = (
    "k := 100[kN/mm]\n"
    "K = zeros(3, 3)\n"
    "% for p, q in [(1, 2), (2, 3)]:\n"
    "K[[{p}, {q}], [{p}, {q}]] = K[[{p}, {q}], [{p}, {q}]] + k*[1, -1; -1, 1]\n"
    "% end\n"
)


def test_an_assembly_is_shown_once(monkeypatch):
    page, console = _run(SPRINGS, monkeypatch)
    assert not console, console
    assert r"\textbf{Ensamble en 2 pasos}" in page, page
    # The rule as the sheet writes it, the loop's names standing.
    assert r"K_{p q, p q} \;\leftarrow\; K_{p q, p q} + k" in page or r"\leftarrow" in page, page
    # The matrix it built, once: `zeros` and the one assembled K, not one per pass.
    assert page.count(r"K & = &") == 2, page
    assert r"- k & 2 k & - k" in page, page


def test_what_the_assembly_built_is_what_later_lines_read(monkeypatch):
    page, console = _run(SPRINGS + "numeric(K[2, 2])\n", monkeypatch)
    assert not console, console
    assert page.rstrip().endswith(r"200.00\,\frac{\mathrm{kN}}{\mathrm{mm}} \end{array}"), page


WIDE = (
    "k := 100[kN/mm]\n"
    "K = zeros(30, 30)\n"
    "% for p in range(1, 30):\n"
    "K[[{p}, {p}+1], [{p}, {p}+1]] = K[[{p}, {p}+1], [{p}, {p}+1]] + k*[1, -1; -1, 1]\n"
    "% end\n"
)


def test_a_matrix_wider_than_the_page_is_said_by_what_it_is(monkeypatch):
    page, console = _run(WIDE, monkeypatch)
    assert not console, console
    assert r"\textbf{Ensamble en 29 pasos}" in page, page
    assert r"30 \times 30" in page and "simétrica" in page, page
    # 30 diagonal entries and 29 above it and below it.
    assert r"88\ \text{términos no nulos}" in page, page
    assert r"2 k & - k" not in page, page


BARS = (
    "E := 200000[MPa]\nA := 1000[mm^2]\n"
    "% for i, (dx, dy) in enumerate([(3, 4), (6, 8)], start=1):\n"
    "L_{i} := sqrt(({dx}[m])^2 + ({dy}[m])^2)\n"
    "c_{i} := {dx}[m]/L_{i}\n"
    "k_{i} := E*A/L_{i}\n"
    "% end\n"
)


def test_the_values_of_a_loop_are_one_table(monkeypatch):
    page, console = _run(BARS, monkeypatch)
    assert not console, console
    # One array, a row per pass, a column per value; no row of its own for each.
    assert page.count(r"\hline") == 1, page
    assert r"L_{1} & = &" not in page and r"k_{2} & = &" not in page, page
    assert r"5.00" in page and r"10.00" in page and r"0.60" in page, page
    assert r"40000.00" in page and r"20000.00" in page, page


def test_the_names_of_the_table_are_defined(monkeypatch):
    page, console = _run(BARS + "numeric(k_2)\n", monkeypatch)
    assert not console, console
    assert page.rstrip().endswith(r"20000.00\,\frac{\mathrm{kN}}{\mathrm{m}} \end{array}"), page


def test_a_loop_of_one_value_keeps_its_rows(monkeypatch):
    page, console = _run("% for x in [2, 3]:\ny_{x} := {x}[m]\n% end\n", monkeypatch)
    assert not console, console
    assert r"y_{2} & = & 2.00\,\mathrm{m}" in page and r"y_{3} & = & 3.00\,\mathrm{m}" in page, page
    assert r"\hline" not in page, page


NAMED = (
    "A_c := 40000[mm^2]\nA_w := 25000[mm^2]\n"
    "% for m, n, A in [(1, 2, A_c), (2, 3, A_w)]:\n"
    "x_{m} := {n}[m]\n"
    "a_{m} := 2*{A}\n"
    "% end\n"
)


def test_what_a_loop_puts_on_the_page_is_typeset_by_colab_s_katex(monkeypatch):
    # The first render of problem 3.6: `\text{x_n}` and `\text{e, f, A_w}` in the table
    # are no LaTeX KaTeX accepts, and the table read as red source.
    import pytest

    from test_colab_can_typeset_every_formula import _formulas, _katex_available, _typeset

    if not _katex_available():
        pytest.skip("KaTeX is not installed; run `npm ci --prefix tools/katex`")
    for source in (SPRINGS, WIDE, BARS, NAMED):
        formulas = _formulas(source, "", monkeypatch)
        results = _typeset(formulas)["results"]
        failed = [formula["tex"][:200] for formula, result in zip(formulas, results) if result["error"]]
        assert not failed, failed
