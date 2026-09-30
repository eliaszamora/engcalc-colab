r"""A `% for` that assembles or tables its values shows what every pass ran, and only that.

The first version of the loop's page (`test_a_for_loop_shows_its_assembly_once`) was
audited before it was released (2026-09-29), and the audit and chapter 4 of his book found
where it read wrong: a unit or a matrix written in the rule printed as the parser keeps it,
a column that mixed metres and seconds, notices that never reached the console, two lines
into one matrix counted as one, a nested loop that repeated its "once", a failing pass that
took the passes before it off the page, and a summary decided by a width that was not the
page's. Each test here is one of them, with the page it should have been.
"""

import contextlib
import io

import pytest
import sympy as sp
from IPython.display import Math

import engcalc_colab.magic as magic
from engcalc_colab import renderer


def _run(source: str, monkeypatch) -> tuple[str, str]:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    latex = " ".join(item.data for item in captured if isinstance(item, Math))
    return latex.replace(r"\displaystyle ", ""), console.getvalue()


def _band(n: int, value: str) -> str:
    return (
        f"K = zeros({n}, {n})\n"
        f"% for p in range(1, {n}):\n"
        f"K[[{{p}}, {{p}}+1], [{{p}}, {{p}}+1]] = K[[{{p}}, {{p}}+1], [{{p}}, {{p}}+1]] + {value}*[1, -1; -1, 1]\n"
        "% end\n"
    )


LOADS = "F = zeros(3, 1)\n% for p in [1, 2, 3]:\nF[{p}] = F[{p}] + 10[kN]\n% end\n"


def test_a_unit_in_the_rule_is_written_as_a_unit(monkeypatch):
    page, console = _run(LOADS, monkeypatch)
    assert not console, console
    assert "__u" not in page, page
    assert r"F_{p} + 10\,\mathrm{kN}" in page, page


def test_a_column_holds_one_kind_of_quantity(monkeypatch):
    # 4 s is not 4 m: a line whose passes are not one quantity keeps its rows.
    page, console = _run(
        '% for i, q in [(1, "3[m]"), (2, "4[s]")]:\na := {q}\nb := 2*a\n% end\n', monkeypatch
    )
    assert not console, console
    assert r"4.00\,\mathrm{s}" in page, page
    assert r"a\,[\mathrm{m}]" not in page, page


def test_what_a_tabled_line_says_reaches_the_console(monkeypatch):
    page, console = _run("% for i in [1, 2]:\na_{i} := {i}[m]\nb_{i} := a_{i}*s\n% end\n", monkeypatch)
    assert r"\hline" in page, page
    assert "'s' is read as a unit (second)" in console, console
    assert console.count("'s' is read as a unit") == 1, console


def test_what_a_summarised_assembly_says_reaches_the_console(monkeypatch):
    page, console = _run(_band(30, "s*k"), monkeypatch)
    assert r"30 \times 30" in page, page
    assert "'s' is read as a unit (second)" in console, console


def test_a_matrix_in_the_rule_is_written_as_the_page_writes_one(monkeypatch):
    source = (
        "K = zeros(2, 2)\n"
        "% for p in [1, 2]:\n"
        "K[[1, 2], [1, 2]] = K[[1, 2], [1, 2]] + E*I/L^3*[12, 6*L; 6*L, 4*L^2]\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    rule = page[page.index("Ensamble"):]
    assert "*" not in rule.split(r"\end{matrix}")[0], rule
    assert "6 L" in rule and "4 L^{2}" in rule, rule


def test_two_lines_into_one_matrix_are_two_rules(monkeypatch):
    source = (
        "K = zeros(3, 3)\n"
        "% for p in [1, 2]:\n"
        "K[{p}, {p}] = K[{p}, {p}] + a\n"
        "K[{p}+1, {p}+1] = K[{p}+1, {p}+1] + b\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert page.count(r"\textbf{Ensamble en 2 pasos") == 2, page
    assert r"K_{p,p} + a" in page and r"K_{p + 1,p + 1} + b" in page, page
    # The matrix once, after both of its rules.
    assert page.count(r"K & = &") == 2, page
    assert r"a & 0 & 0\\[3pt]0 & a + b & 0" in page, page


@pytest.mark.parametrize(
    ("n", "value", "drawn"),
    [
        # Measured with KaTeX 0.16.28 at Colab's 900 px.
        (6, "k", True),                   # 243 px
        (8, "(k_1 + k_2)", True),         # 717 px
        (10, "1234.567", False),          # 938 px
        (14, "1500", False),              # 973 px
    ],
)
def test_a_matrix_is_drawn_when_it_fits_the_page(monkeypatch, n, value, drawn):
    page, console = _run(_band(n, value), monkeypatch)
    assert not console, console
    summarised = r"\text{términos no nulos}" in page
    assert summarised is not drawn, page


def test_an_assembly_inside_a_loop_is_shown_once(monkeypatch):
    source = (
        "K = zeros(3, 3)\n"
        "% for i in [1, 2]:\n"
        "% for p in [1, 2]:\n"
        "K[{p}, {p}] = K[{p}, {p}] + a\n"
        "% end\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert page.count("Ensamble") == 1, page
    assert r"\textbf{Ensamble en 4 pasos" in page, page
    assert page.count(r"K & = &") == 2, page


def test_a_table_comes_before_the_rows_built_from_it(monkeypatch):
    source = (
        "% for i, (dx, dy) in enumerate([(3, 4), (6, 8)], start=1):\n"
        "L_{i} := sqrt(({dx}[m])^2 + ({dy}[m])^2)\n"
        "c_{i} := {dx}[m]/L_{i}\n"
        "g_{i} = c_{i}*[1; -1]\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert page.count(r"\hline") == 1, page
    # The formula every pass wrote with other subscripts, once, after the table it reads.
    assert page.index(r"\hline") < page.index(r"\quad g_{i} = "), page
    # The table's own formulas, above it: `{dx}[m]` is the loop's value times a metre.
    assert r"\quad L_{i} = \sqrt{\left(\mathit{dx}\,\mathrm{m}\right)^{2}" in page, page
    assert r"\quad g_{i} = c_{i}" in page, page
    assert r"g_{1}" not in page and r"g_{2}" not in page, page


def test_a_formula_that_works_out_to_a_number_keeps_its_rows(monkeypatch):
    source = (
        "% for i in [1, 2]:\n"
        "L_{i} := {i}[m]\n"
        "c_{i} := 2*L_{i}\n"
        "n_{i} = 3*{i}\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\quad n_{" not in page, page
    assert r"n_{1} & = &" in page and r"n_{2} & = &" in page, page


def test_the_formulas_of_problem_3_6_are_said_once(monkeypatch):
    source = (
        "x_A := 0[m]\nx_B := 3[m]\nx_C := 3[m]\ny_A := 0[m]\ny_B := 4[m]\ny_C := 0[m]\n"
        '% for i, j in [("A", "B"), ("B", "C"), ("A", "C")]:\n'
        "L_{i}{j} := sqrt((x_{j} - x_{i})^2 + (y_{j} - y_{i})^2)\n"
        "c_{i}{j} := (x_{j} - x_{i})/L_{i}{j}\n"
        "s_{i}{j} := (y_{j} - y_{i})/L_{i}{j}\n"
        "g_{i}{j} = [-c_{i}{j}; -s_{i}{j}; c_{i}{j}; s_{i}{j}]\n"
        "% end\n"
        "numeric(g_BC)\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert page.count(r"\quad g_{ij} = ") == 1, page
    assert r"\quad g_{ij} = \left[\begin{matrix}-c_{ij}" in page, page
    # What each pass defined is still there to read.
    assert r"0.00\\[3pt]1.00\\[3pt]0.00\\[3pt]-1.00" in page, page


def test_a_matrix_value_is_not_an_empty_column(monkeypatch):
    source = (
        "% for i in [1, 2]:\n"
        "L_{i} := {i}[m]\n"
        "k_{i} := 3[kN]/L_{i}\n"
        "M_{i} := k_{i}*[1, -1; -1, 1]\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\text{---}" not in page, page
    assert r"M_{1}" in page and r"M_{2}" in page, page
    assert page.index(r"\hline") < page.index(r"M_{1}"), page


def test_a_failing_pass_leaves_the_passes_before_it_on_the_page(monkeypatch):
    page, console = _run("% for i in [1, 0]:\na_{i} := {i}[m]\nb_{i} := 1[m]/{i}\n% end\n", monkeypatch)
    assert "division by zero" in console, console
    assert r"a_{1} & = & 1.00\,\mathrm{m}" in page, page
    assert r"b_{1} & = & 1.00\,\mathrm{m}" in page, page
    assert r"a_{0} & = & 0.00\,\mathrm{m}" in page, page


def test_a_negative_factor_in_the_rule_keeps_its_parentheses(monkeypatch):
    source = (
        "K = zeros(2, 2)\n"
        "% for p in [1, 2]:\n"
        "K[{p}, {p}] = K[{p}, {p}] + k*(-1) + (-a)^2\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"k \left(-1\right)" in page, page
    assert r"\left(-a\right)^{2}" in page, page


def test_a_subscripted_matrix_in_the_rule_is_one_subscript(monkeypatch):
    source = (
        "k_e = [a, -a; -a, a]\n"
        "K_T = zeros(3, 3)\n"
        "% for p in [1, 2]:\n"
        "K_T[[{p}, {p}+1], [{p}, {p}+1]] = K_T[[{p}, {p}+1], [{p}, {p}+1]] + k_e[[1, 2], [1, 2]]\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\left(K_{T}\right)_{" in page and r"\left(k_{e}\right)_{" in page, page
    assert r"K_{T}_" not in page and r"k_{e}_" not in page, page


def test_a_recurrence_is_not_an_assembly(monkeypatch):
    source = (
        "v = zeros(3, 1)\n"
        "v[1] = 1\n"
        "% for p in [2, 3]:\n"
        "v[{p}] = 2*v[{p}-1]\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert "Ensamble" not in page, page


def test_a_line_written_twice_keeps_every_value(monkeypatch):
    source = "x := 0[m]\n% for i in [1, 2]:\nx := x + 1[m]\nx := x + 1[m]\n% end\n"
    page, console = _run(source, monkeypatch)
    assert not console, console
    for value in ("1.00", "2.00", "3.00", "4.00"):
        assert rf"x & = & {value}\,\mathrm{{m}}" in page or rf"= {value}\,\mathrm{{m}}" in page, (value, page)


def test_the_rule_writes_functions_as_the_page_does(monkeypatch):
    source = (
        "T(a) = [a, -a; -a, a]\n"
        "K = zeros(2, 2)\n"
        "% for p in [1, 2]:\n"
        "K[[1, 2], [1, 2]] = K[[1, 2], [1, 2]] + sqrt(k)*2*T(b)\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    rule = page[page.index("Ensamble"):]
    assert r"\sqrt{k} \cdot 2" in rule, rule
    assert r"\operatorname{T}" not in rule and r"T\left(b\right)" in rule, rule


def test_the_rule_says_what_its_loop_names_are(monkeypatch):
    page, console = _run(
        "K = zeros(3, 3)\n% for p in [1, 2]:\nK[{p}, {p}] = K[{p}, {p}] + a\n% end\n", monkeypatch
    )
    assert not console, console
    assert r"\textbf{Ensamble en 2 pasos},\ \text{para}\ p = 1,\ 2\textbf{:}" in page, page


def test_degrees_of_freedom_written_as_text_read_as_numbers(monkeypatch):
    source = (
        "K = zeros(3, 3)\n"
        '% for m, n in [("1", "[1, 2]"), ("2", "[2, 3]")]:\n'
        "K[{n}, {n}] = K[{n}, {n}] + a*[1, -1; -1, 1]\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    # Only the names the rule stands on: m is the loop's, and the rule never reads it.
    assert r"\text{para}\ n = \left[1, 2\right],\ \left[2, 3\right]\textbf{:}" in page, page


def test_the_values_of_a_frame_s_loop_wrap_onto_rows_of_the_page(monkeypatch):
    # Chapter 4: six degrees of freedom to a value, and the row ran to 1083 px.
    values = ", ".join(f'("e", "[{", ".join(str(n + k) for k in range(6))}]")' for n in range(1, 6))
    source = (
        "k_e = identity(6)\nK = zeros(10, 10)\n"
        f"% for m, p in [{values}]:\n"
        "K[{p}, {p}] = K[{p}, {p}] + k_{m}\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    note = page[page.index(r"\textbf{Ensamble"):]
    note = note[: note.index(r"\end{array}")]
    rows = note.split(r" \\[4pt] ")
    assert len(rows) >= 3, rows
    assert all(renderer._katex_em(row) * renderer._EM_PX <= 860 for row in rows), rows


def test_a_loop_value_written_as_an_expression_reads_as_one(monkeypatch):
    source = (
        "L_1 := 3[m]\nL_2 := 5[m]\n"
        '% for m, c in [("a", "L_1/L_2"), ("b", "-cos(60[deg])")]:\n'
        "r_{m} := {c}\n"
        "t_{m} := 2*r_{m}*L_1\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\text{-cos" not in page and r"\text{L" not in page, page
    assert r"\frac{L_{1}}{L_{2}}" in page and r"\cos\left(60\,\mathrm{deg}\right)" in page, page
    # The formula of the column the table works out, once, above the table.
    assert r"\quad t_{m} = 2 r_{m} L_{1}" in page, page
    assert page.index(r"\quad t_{m} = ") < page.index(r"\hline"), page
    # A column that only writes the loop's value has no formula to say.
    assert r"\quad r_{m} = " not in page, page


def test_the_rule_says_what_the_percent_helpers_made(monkeypatch):
    source = (
        "K = zeros(4, 4)\n"
        "% for m in [1, 2]:\n"
        "% p, q = 2*m - 1, 2*m\n"
        "K[[{p}, {q}], [{p}, {q}]] = K[[{p}, {q}], [{p}, {q}]] + a*[1, -1; -1, 1]\n"
        "% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\text{con}\ \left(p, q\right) = \left(2 m - 1, 2 m\right)\textbf{:}" in page, page
    # The rule on a row of its own, where the page's width cannot cut its arrow off.
    assert r"\textbf{:} \\[4pt] \quad K_{" in page, page


def test_a_zero_that_sympy_leaves_written_is_not_counted():
    a, b = sp.symbols("a b")
    matrix = sp.Matrix([[(a + b) ** 2 - a**2 - 2 * a * b - b**2, 1], [1, 0]])
    assert r"2\ \text{términos no nulos}" in renderer.matrix_summary_latex("K", matrix)


@pytest.mark.parametrize(
    ("rows", "columns", "shown"),
    [(36, 36, r"\mathbf{0}_{36 \times 36}"), (6, 1, r"\mathbf{0}_{6 \times 1}")],
)
def test_a_large_matrix_of_zeros_is_written_as_one(monkeypatch, rows, columns, shown):
    page, console = _run(f"K = zeros({rows}, {columns})\n", monkeypatch)
    assert not console, console
    assert rf"K & = & {shown}" in page, page


def test_a_small_matrix_of_zeros_is_drawn(monkeypatch):
    page, console = _run("K = zeros(3, 3)\n", monkeypatch)
    assert not console, console
    assert r"0 & 0 & 0" in page, page


# -- the second audit (of c7a16f1) ------------------------------------------------------


def test_a_line_that_adds_into_its_own_name_keeps_its_rows(monkeypatch):
    source = (
        "W = 0\n% for i in [1, 2, 3]:\nL_{i} := {i}[m]\nw_{i} := 2[kN/m]*L_{i}\nW = W + w_{i}\n% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"W & = & w_{1} + w_{2} + w_{3}" in page, page
    assert r"\quad W = W" not in page, page


def test_a_loop_that_writes_its_own_headings_keeps_each_pass_under_its_heading(monkeypatch):
    source = "% for i in [1, 2]:\n### Barra {i}\na_{i} := {i}[m]\nb_{i} := 2*a_{i}\n% end\n"
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\hline" not in page, page
    assert r"a_{2} & = & 2.00\,\mathrm{m}" in page, page


def test_a_percent_if_that_assembles_keeps_its_rows_under_its_condition(monkeypatch):
    source = (
        "K = zeros(3, 3)\n% for p in [1, 2]:\n% if p == 1:\nK[{p}, {p}] = K[{p}, {p}] + 1\n"
        "% else:\nK[{p}, {p}] = K[{p}, {p}] + 2\n% end\n% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert "Ensamble" not in page, page
    assert page.count(r"K & = &") == 3, page


def test_what_every_pass_of_a_rule_said_reaches_the_console(monkeypatch):
    source = (
        "w = 5\nz = 6\n"
        '% for i, n in [(1, "w"), (2, "z")]:\n'
        "L_{i} := {i}[m]\nd_{i} := 2*L_{i}\nM_{i} = {n}*L_{i}\nnumeric(L_{i})\n% end\n"
    )
    _page, console = _run(source, monkeypatch)
    assert "'w'" in console and "'z'" in console, console


def test_a_helper_the_formulas_of_a_table_read_is_said(monkeypatch):
    source = "% for i in [1, 2]:\n% t = 30*i\nc_{i} := cos({t}[deg])\ns_{i} := sin({t}[deg])\n% end\n"
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\text{con}\ t = 30 i\textbf{:}" in page, page


def test_a_percent_name_the_same_in_every_pass_is_said_once(monkeypatch):
    source = (
        "K = zeros(4, 4)\n% s = 2\n% for m in [1, 2]:\n% p = s*m - 1\n"
        "K[{p}, {p}] = K[{p}, {p}] + a\n% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\text{para}\ m = 1,\ 2" in page, page
    assert r"p = s m - 1,\ s = 2\textbf{:}" in page, page


def test_a_name_joined_to_a_loop_value_is_subscripted(monkeypatch):
    source = "k1 = 2\nk2 = 3\nK = zeros(2, 2)\n% for p in [1, 2]:\nK[{p}, {p}] = K[{p}, {p}] + k{p}\n% end\n"
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"K_{p,p} + k_{p}" in page, page


def test_a_loop_inside_a_loop_that_does_not_gather_keeps_its_rows(monkeypatch):
    source = (
        "% for i in [1, 2]:\na_{i} := {i}[m]\n% for j in [1, 2]:\n"
        "c_{i}{j} := a_{i}*{j}\nd_{i}{j} := 2*c_{i}{j}\n% end\n% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\hline" not in page, page
    assert r"d_{22} & = &" in page, page


def test_the_values_of_an_inner_loop_are_said_by_its_names(monkeypatch):
    source = (
        "K = zeros(4, 4)\n% for e in [1, 2]:\n% for a in [0, 1]:\n"
        "K[{e}+{a}, {e}+{a}] = K[{e}+{a}, {e}+{a}] + b\n% end\n% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\text{para}\ \left(e, a\right) = \left(1, 0\right),\ \left(1, 1\right),\ \left(2, 0\right),\ \left(2, 1\right)" in page, page


def test_a_label_with_a_hyphen_is_a_name_not_a_subtraction():
    assert renderer._loop_value_latex("1-2") == r"\text{1-2}"
    assert renderer._loop_value_latex("Viga (A-B)") == r"\text{Viga (A-B)}"


def test_a_unit_in_a_rule_reads_as_the_page_writes_one():
    assert renderer._rule_latex("F[{p}] = F[{p}] + 10[kN/m]*L").endswith(r"F_{p} + \frac{10\,\mathrm{kN}}{\mathrm{m}} L")
    assert renderer._rule_latex("F[{p}] = F[{p}] + 5[1/m]").endswith(r"F_{p} + \frac{5}{\mathrm{m}}")
    assert r"\texttt" not in renderer._helper_latex("s = -1 if p == 1 else 1")


# -- the third audit (of 6623195) --------------------------------------------------------


def test_an_expression_in_a_subscript_keeps_its_group(monkeypatch):
    source = "x_0 := 0[m]\n% for i in [1, 2, 3]:\nx_{i} := 2*{i}[m]\nL_{i} := x_{i} - x_{i-1}\n% end\n"
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\quad L_{i} = x_{i} - x_{i - 1}" in page, page
    assert renderer._rule_latex("K[{i}, {i}] = K[{i}, {i}] + k_{i+1}").endswith(r"K_{i,i} + k_{i + 1}")
    assert renderer._formula_rule_latex("y_{i} = a^{i-1}*b") == r"y_{i} = a^{i - 1} b"


def test_a_recurrence_through_subscripts_keeps_its_rows(monkeypatch):
    source = "M_0 = 0\n% for i in [1, 2, 3]:\nx_{i} := {i}[m]\nV_{i} := 2[kN]*x_{i}\nM_{i} = M_{i-1} + V_{i}\n% end\n"
    page, _console = _run(source, monkeypatch)  # main's notice on M_0 = 0, as before
    assert r"M_{3} & = & V_{1} + V_{2} + V_{3}" in page, page
    assert r"\quad M_{i} = " not in page, page


def test_helpers_made_from_helpers_are_followed_back_to_the_loop(monkeypatch):
    source = "K = zeros(4, 4)\n% for m in [1, 2]:\n% q = 2*m\n% p = q - 1\nK[{p}, {p}] = K[{p}, {p}] + 1\n% end\n"
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\text{para}\ m = 1,\ 2" in page, page
    assert r"\text{con}\ q = 2 m,\ p = q - 1\textbf{:}" in page, page


def test_the_names_of_a_note_follow_the_header(monkeypatch):
    source = (
        "k_a = 1\nk_b = 2\nK = zeros(3, 3)\n"
        '% for m, p in [("a", "[1, 2]"), ("b", "[2, 3]")]:\n'
        "K[{p}, {p}] = K[{p}, {p}] + k_{m}*[1, -1; -1, 1]\n% end\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"\text{para}\ \left(m, p\right) = " in page, page


SOURCES = [
    LOADS,
    "% for i, n in [(1, \"A&B\"), (2, \"50%\"), (3, \"x#y\")]:\na_{i} := {i}[m]\nb_{i} := 2*a_{i}\n% end\n",
    "K = zeros(2, 2)\n% for p in [1, 2]:\nK[[1, 2], [1, 2]] = K[[1, 2], [1, 2]] + E*I/L^3*[12, 6*L; 6*L, 4*L^2]\n% end\n",
    "k_e = [a, -a; -a, a]\nK_T = zeros(3, 3)\n% for p in [1, 2]:\n"
    "K_T[[{p}, {p}+1], [{p}, {p}+1]] = K_T[[{p}, {p}+1], [{p}, {p}+1]] + k_e[[1, 2], [1, 2]]\n% end\n",
    "K = zeros(3, 3)\n% for p in [1, 2]:\nK[{p}, {p}] = K[{p}, {p}] + a\n% end\n",
    "K = zeros(36, 36)\n",
]


def test_what_these_loops_put_on_the_page_is_typeset_by_colab_s_katex(monkeypatch):
    from test_colab_can_typeset_every_formula import _formulas, _katex_available, _typeset

    if not _katex_available():
        pytest.skip("KaTeX is not installed; run `npm ci --prefix tools/katex`")
    for source in SOURCES:
        formulas = _formulas(source, "", monkeypatch)
        results = _typeset(formulas)["results"]
        failed = [formula["tex"][:200] for formula, result in zip(formulas, results) if result["error"]]
        assert not failed, failed
