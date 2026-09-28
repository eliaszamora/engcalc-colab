r"""`numeric(...)` is a line of its own: inside a formula it stops the cell and says so.

`numeric` shows a formula worked out to its value - the formula, its numbers put in, the
result. The approved 0.9.0 design keeps it there: "`numeric(A) * numeric(B)` is not part
of the public contract"; a formula is written first and `numeric` asks for its number.
Written inside a formula it took the line over (found 2026-09-28): `M = q*numeric(L^2)/2`
defined `M` as `9 m^2`, `q/2` gone, and `y = sqrt(numeric(L_2^2))` showed `y = 9.00 m^2`.
On a `:=` line it stopped at `unsupported numeric function 'numeric'`, and a plot of
`numeric(M(x))` drew the moment upward under a Python title. The line now stops and writes
itself without it: `M = q*L^2/2`, then `numeric(M)`.

A condition of `% if` or `% while` is worked out in numbers already, and there `numeric(X)`
reads as `X`: it did before, and its audit (2026-09-28) found it refused.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic

BASE = "L_2 := 3[m]\nq_2 := 10[kN/m]\nM_2 = q_2*L_2^2/2\nM(x) = q_2*x^2/2\n"


def _run(source: str, monkeypatch) -> tuple[str, str]:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    latex = " ".join(item.data for item in captured if isinstance(item, Math))
    return latex.replace(r"\displaystyle ", ""), console.getvalue()


def test_a_product_with_numeric_in_it_stops_and_writes_the_formula(monkeypatch):
    page, console = _run("L = 3*m\nM = q*numeric(L^2)/2\nN = 2*M\n", monkeypatch)
    assert "engcalc: line 2: numeric must be a standalone statement" in console, console
    assert "M = q*L^2/2, then numeric(M)" in console, console
    # Nothing was defined: the line that read `M` was never reached.
    assert "M & = &" not in page and "N & = &" not in page, page


def test_a_colon_equals_value_is_told_what_colon_equals_already_does(monkeypatch):
    page, console = _run(BASE + "M_3 := q_2*numeric(L_2^2)/2\n", monkeypatch)
    assert "unsupported numeric function" not in console, console
    assert "engcalc: line 5:" in console, console
    assert "':=' works its right side out to a number already" in console, console
    assert "M_3 := q_2*L_2^2/2" in console, console
    assert "M_{3}" not in page, page


def test_a_colon_equals_of_numeric_alone_is_told_too(monkeypatch):
    _page, console = _run(BASE + "x_1 := numeric(L_2)\n", monkeypatch)
    assert "unsupported numeric function" not in console, console
    assert "x_1 := L_2" in console, console


@pytest.mark.parametrize(
    ("line", "written"),
    [
        ("M_4 = q_2*numeric(L_2^2)/2", "M_4 = q_2*L_2^2/2, then numeric(M_4)"),
        ("y = sqrt(numeric(L_2^2))", "y = sqrt(L_2^2), then numeric(y)"),
        ("keep w = 2*numeric(L_2)", "keep w = 2*L_2, then numeric(w)"),
        ("u = 2*numeric(L_2 + L_2)", "u = 2*(L_2 + L_2), then numeric(u)"),
        ("v = numeric(L_2^2)^2", "v = (L_2^2)^2, then numeric(v)"),
        ("u = numeric(L_2, cm) + 0*m", "u = L_2 + 0*m, then numeric(u)"),
        ("numeric(M_2) + 1*kN*m", "numeric(M_2 + 1*kN*m)"),
        ("numeric(2*numeric(L_2))", "numeric(2*L_2)"),
        ("numeric(2*numeric(L_2), cm)", "numeric(2*L_2, cm)"),
        ("numeric(M(numeric(L_2)))", "numeric(M(L_2))"),
        # A function is asked for its number at an argument; the line says only its body.
        ("f(x) = 2*numeric(L_2)", "Write f(x) = 2*L_2."),
        ("f(x) = numeric(x)", "Write f(x) = x."),
        ("plot(numeric(M(x)), x, 0, L_2)", "Write plot(M(x), x, 0, L_2)."),
        ("roots(numeric(M(x)), x, 0, L_2)", "Write roots(M(x), x, 0, L_2)."),
        # A call of mathematics or of the sheet on a line of its own shows no number.
        ("sqrt(numeric(L_2^2))", "Write numeric(sqrt(L_2^2))."),
        ("M(numeric(L_2))", "Write numeric(M(L_2))."),
        ("max(numeric(L_2), 1*m)", "Write numeric(max(L_2, 1*m))."),
        # An equation is not a value, and has none to ask for.
        ("e = eq(numeric(L_2), x)", "Write e = eq(L_2, x)."),
        ("x_0 = solve(eq(2*x, numeric(L_2)), x)", "Write x_0 = solve(eq(2*x, L_2), x), then numeric(x_0)."),
        ("solve(eq(2*x, numeric(L_2)), x)", "Write solve(eq(2*x, L_2), x)."),
        # A comment is not written back; nor is a matrix of several lines.
        ("y = 2*numeric(L_2 + L_2)  # numeric(L_2)", "Write y = 2*(L_2 + L_2), then numeric(y)."),
        ("K = [numeric(L_2), 0*m;\n     0*m, L_2]", "Write K = [L_2, 0*m; 0*m, L_2], then numeric(K)."),
        ("case D = 2*numeric(M(x))", "Write case D = 2*M(x)."),
        # Whole, it was no named numeric either: `D(x)` was `M(x)`, `L_2/2` gone.
        ("case D = numeric(M(L_2/2))", "Write case D = M(L_2/2)."),
    ],
)
def test_the_line_is_written_without_it(line, written, monkeypatch):
    _page, console = _run(BASE + line + "\n", monkeypatch)
    assert "engcalc: line 5: numeric must be a standalone statement" in console, console
    assert written in console, console


def test_a_combination_is_written_back_without_a_numeric(monkeypatch):
    source = BASE + "case D = M(x)\ncombo U = 1.2*numeric(D)\n"
    _page, console = _run(source, monkeypatch)
    assert "engcalc: line 6: numeric must be a standalone statement" in console, console
    assert "Write combo U = 1.2*D." in console, console


@pytest.mark.parametrize("line", ["y = 2*numeric()", "y = 2*numeric(L_2, cm, m)", "numeric(numeric())"])
def test_a_numeric_with_the_wrong_arguments_says_so(line, monkeypatch):
    _page, console = _run(BASE + line + "\n", monkeypatch)
    assert "numeric expects 1 or 2 arguments" in console, console
    assert "Write" not in console, console


def test_a_report_with_the_wrong_arguments_says_so(monkeypatch):
    _page, console = _run(BASE + "z = 2*report(M_2, L_2)\n", monkeypatch)
    assert "report expects one defined name" in console, console


def test_a_string_is_not_written_back():
    from engcalc_colab.engine import _written_without_numeric

    assert _written_without_numeric('f("numeric(a)", numeric(b))', False) == ('f("numeric(a)", b)', ["numeric"])
    assert _written_without_numeric("f('x', numeric(b))", False) == ("f('x', b)", ["numeric"])


def test_a_matrix_written_with_numeric_in_a_cell_stops(monkeypatch):
    page, console = _run(BASE + "K = [numeric(L_2), 0; 0, 1]\n", monkeypatch)
    assert "engcalc: line 5: numeric must be a standalone statement" in console, console
    assert "numeric(K)" in console, console
    # The row it showed was `L_2 = 3.00 m`, a second time, in place of the matrix.
    assert page.count(r"L_{2} & = &") == 1, page


def test_result_inside_a_formula_is_told_by_its_own_name(monkeypatch):
    # `result` is `numeric` without the substitution row: the parser hands it on as
    # `numeric`, and the line written back must not keep it.
    _page, console = _run(BASE + "M_4 = q_2*result(L_2^2)/2\n", monkeypatch)
    assert "engcalc: line 5: result must be a standalone statement" in console, console
    assert "Write M_4 = q_2*L_2^2/2, then result(M_4)." in console, console
    _page, console = _run(BASE + "M_5 := q_2*result(L_2^2)/2\n", monkeypatch)
    assert "and result shows" in console, console
    assert "Write M_5 := q_2*L_2^2/2." in console, console


def test_report_inside_a_formula_is_told_by_its_own_name(monkeypatch):
    _page, console = _run(BASE + "z = 2*report(M_2)\n", monkeypatch)
    assert "report must be a standalone statement" in console, console
    assert "Write z = 2*M_2, then report(z)." in console, console
    _page, console = _run(BASE + "numeric(2*report(M_2))\n", monkeypatch)
    assert "report must be a standalone statement" in console, console
    assert "Write numeric(2*M_2)." in console, console
    # Named, it says what it said before.
    _page, console = _run(BASE + "z = report(M_2)\n", monkeypatch)
    assert "report must be a standalone statement; its value is shown where it is written" in console


@pytest.mark.parametrize(
    ("line", "shown"),
    [
        ("numeric(M_2)", r"45.00\,\mathrm{kN} \cdot \mathrm{m}"),
        ("numeric(M_2, kN*cm)", r"4500.00\,\mathrm{kN} \cdot \mathrm{cm}"),
        ("w = numeric(M_2)", r"45.00\,\mathrm{kN} \cdot \mathrm{m}"),
        ("keep w = numeric(M_2)", r"45.00\,\mathrm{kN} \cdot \mathrm{m}"),
        ("report(M_2)", r"45.00\,\mathrm{kN} \cdot \mathrm{m}"),
        ("result(M_2)", r"45.00\,\mathrm{kN} \cdot \mathrm{m}"),
        ("w = result(M_2)", r"45.00\,\mathrm{kN} \cdot \mathrm{m}"),
        ("numeric(M(L_2/2))", r"11.25\,\mathrm{kN} \cdot \mathrm{m}"),
        ("numeric(2*M(L_2))", r"90.00\,\mathrm{kN} \cdot \mathrm{m}"),
    ],
)
def test_numeric_as_the_line_is_as_it_was(line, shown, monkeypatch):
    page, console = _run(BASE + line + "\n", monkeypatch)
    assert not console, console
    assert page.rstrip().endswith(shown + r" \end{array}"), page


def test_a_word_that_ends_in_numeric_is_not_numeric(monkeypatch):
    page, console = _run(BASE + "nonnumeric(x) = 2*x\nnumeric(nonnumeric(L_2))\n", monkeypatch)
    assert not console, console
    assert page.rstrip().endswith(r"6.00\,\mathrm{m} \end{array}"), page
    # And the line written back does not take it for one.
    _page, console = _run(BASE + "nonnumeric(x) = 2*x\nu = 2*numeric(nonnumeric(L_2))\n", monkeypatch)
    assert "Write u = 2*nonnumeric(L_2), then numeric(u)." in console, console


CONDITION_BASE = BASE + "M_u := 50[kN*m]\n"


def _page_of(source: str, monkeypatch) -> tuple[str, str]:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    return " ".join(str(getattr(item, "data", "")) for item in captured), console.getvalue()


@pytest.mark.parametrize(
    ("condition", "as_written"),
    [
        ("% if numeric(M_2) > 40*kN*m:", "% if M_2 > 40*kN*m:"),
        ("% if result(M_2) > 40*kN*m:", "% if M_2 > 40*kN*m:"),
        ("% if numeric(M_2, kN*m) > 40*kN*m:", "% if M_2 > 40*kN*m:"),
        ("% if 2*numeric(M_2) > 40*kN*m:", "% if 2*M_2 > 40*kN*m:"),
        ("% if numeric(M_2) < numeric(M_u):", "% if M_2 < M_u:"),
        ("% if 4*M(numeric(L_2)) > 40*kN*m:", "% if 4*M(L_2) > 40*kN*m:"),
        (
            "% if L_2 > 5*m:\nnumeric(L_2)\n% elif numeric(M_2) > 40*kN*m:",
            "% if L_2 > 5*m:\nnumeric(L_2)\n% elif M_2 > 40*kN*m:",
        ),
    ],
)
def test_a_condition_reads_numeric_as_its_value(condition, as_written, monkeypatch):
    ending = "\nnumeric(M_2)\n% else:\nnumeric(L_2)\n% end\n"
    page, console = _page_of(CONDITION_BASE + condition + ending, monkeypatch)
    expected, _console = _page_of(CONDITION_BASE + as_written + ending, monkeypatch)
    assert not console, console
    assert page == expected, (page, expected)
    assert r"45.00\,\mathrm{kN} \cdot \mathrm{m}" in page, page


def test_a_while_condition_reads_numeric_as_its_value(monkeypatch):
    loop = "x := 1[m]\n% while {}:\nx := x + 1[m]\n% end\n"
    page, console = _page_of(BASE + loop.format("numeric(x) < 4*m"), monkeypatch)
    expected, _console = _page_of(BASE + loop.format("x < 4*m"), monkeypatch)
    assert not console, console
    assert page == expected, (page, expected)
    assert "En 3 iteraciones" in page, page


def test_a_report_in_a_condition_says_the_condition_reads_the_value(monkeypatch):
    source = CONDITION_BASE + "% if report(M_2) > 40*kN*m:\nnumeric(M_2)\n% end\n"
    _page, console = _page_of(source, monkeypatch)
    assert "engcalc: line 6: report must be a standalone statement" in console, console
    assert "M_2 > 40*kN*m" in console, console
    assert "line 1" not in console, console
