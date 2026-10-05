r"""His asks of 2026-10-04 for 0.46.0.

- An expression or call split over lines inside parentheses or brackets: a long `solve` or a
  formula with many terms was refused "unbalanced parentheses", though the parentheses were
  balanced - only a matrix literal could continue on the next line.
- `T'` for the transpose of `T`, as the book writes it.
- `U^-1` (and `U^2`) on a `:=` line, as `=` lines already read it.
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


# --- multiline ---------------------------------------------------------------------------


def test_a_formula_split_inside_parentheses_reads_as_one_line(monkeypatch):
    one, console_one = _run("a := 2\nb := 3\ny = (a +\n     b)*2\nz := (a +\n      b)*2\n", monkeypatch)
    two, console_two = _run("a := 2\nb := 3\ny = (a + b)*2\nz := (a + b)*2\n", monkeypatch)
    assert not console_one and not console_two, (console_one, console_two)
    assert one == two, (one, two)
    assert r"z & = & 10.00" in one, one


def test_a_call_split_over_lines(monkeypatch):
    page, console = _run(
        "x_1 := solve(eq(x^2, 2),\n             x, 0, 3)\nF := max(2[kN],\n         3[kN])\n",
        monkeypatch,
    )
    assert not console, console
    assert r"x_{1} & = & 1.41" in page, page
    assert r"3.00\,\mathrm{kN}" in page, page


def test_a_matrix_inside_a_split_product(monkeypatch):
    page, console = _run(
        "k := 2[kN/m]\nK := k*(\n  [1, -1;\n   -1, 1])\n", monkeypatch
    )
    assert not console, console
    assert r"-2.00" in page and r"\frac{\mathrm{kN}}{\mathrm{m}}" in page, page


def test_a_split_line_in_a_loop_takes_its_placeholders(monkeypatch):
    page, console = _run(
        "% for i in [1, 2]:\nc_{i} := max({i},\n            1.5)\n% end\n", monkeypatch
    )
    assert not console, console
    assert "1.50" in page and "2.00" in page, page


def test_lines_after_a_split_line_keep_their_numbers(monkeypatch):
    _, console = _run("a := (1 +\n      2)\nb := a +\n", monkeypatch)
    assert "line 3" in console, console


def test_a_parenthesis_never_closed_says_where_it_opened(monkeypatch):
    _, console = _run("a := 1\nb := max(a,\n         2\n", monkeypatch)
    assert "line 2" in console and "never closed" in console, console


def test_a_blank_line_ends_a_split_line(monkeypatch):
    """A parenthesis left open by mistake does not swallow the rest of the sheet."""
    _, console = _run("b := max(1,\n\nc := 2\n", monkeypatch)
    assert "line 1" in console and "never closed" in console, console


# --- T' ----------------------------------------------------------------------------------


def test_a_prime_is_the_transpose_on_a_formula_line(monkeypatch):
    matrices = "T = [a, b; -b, a]\nK = [k, 0; 0, 2*k]\n"
    prime, console_prime = _run(matrices + "A = T'*K*T\n", monkeypatch)
    written, console_written = _run(matrices + "A = transpose(T)*K*T\n", monkeypatch)
    assert r"a^{2} k + 2 b^{2} k" in prime, prime
    assert not console_prime and not console_written, (console_prime, console_written)
    assert prime == written, (prime, written)


def test_a_prime_is_the_transpose_on_a_numeric_line(monkeypatch):
    page, console = _run(
        "U := [1, 2; 3, 4]\nV := U'\nd := [1[mm]; 2[mm]]\nW := (U*d)'\n", monkeypatch
    )
    assert not console, console
    assert r"\left[\begin{matrix}1.00 & 3.00\\[3pt]2.00 & 4.00\end{matrix}\right]" in page, page
    assert r"\left[\begin{matrix}5.00 & 11.00\end{matrix}\right]\,\mathrm{mm}" in page, page


def test_quotes_of_the_percent_lines_are_still_text(monkeypatch):
    page, console = _run(
        "% for q in ['+ 1', '* 2']:\nb := 2 {q}\n% end\n", monkeypatch
    )
    assert not console, console
    assert "3.00" in page and "4.00" in page, page


# --- U^-1 on := lines --------------------------------------------------------------------


def test_a_power_of_a_numeric_matrix(monkeypatch):
    page, console = _run(
        "U := [2, 0; 0, 4[kN/m]]\nX := U^-1\nF := [2; 8[kN]]\nd := U^-1*F\nY := U^2\n",
        monkeypatch,
    )
    assert not console, console
    assert r"X & = & U^{-1}" in page, page
    assert r"0.50" in page and r"0.25" in page, page
    assert r"\left[\begin{matrix}1.00\\[3pt]2.00\,\mathrm{m}\end{matrix}\right]" in page, page
    assert r"16.00" in page, page


def test_a_fractional_power_of_a_matrix_is_refused(monkeypatch):
    _, console = _run("U := [2, 0; 0, 4]\nX := U^(1/2)\n", monkeypatch)
    assert "whole" in console, console


def test_his_example_2_1_solve_over_four_lines(monkeypatch):
    """His cell in Untitled9 as he wrote it: main said "line 20: unbalanced parentheses"."""
    page, console = _run(
        "E := 200000*MPa\nA_ba := 6000*mm^2\nA_ac := 8000*mm^2\nF_ba := 400.6*kN\n"
        "F_ac := 277.8*kN\nL_ba := sqrt(6^2 + 4^2)*m\nL_ac := 5*m\ntheta := atan(4/6)\n"
        "phi := atan(4/3)\ndelta_ba := (F_ba*L_ba/(E*A_ba))\ndelta_ac := (-F_ac*L_ac/(E*A_ac))\n"
        '"""Luego resolvemos el siguiente sistema de ecuaciones """\n'
        "solve(\n    eq(delta_ba , a_x*cos(theta) + a_y*sin(theta)),\n"
        "    eq(delta_ac , a_x*cos(phi) - a_y*sin(phi)),\n    a_x,a_y)\n",
        monkeypatch,
    )
    assert not console, console
    assert "a_{x} & = &" in page and "a_{y} & = &" in page, page[-600:]


# --- what the audit of 0.46.0 found ------------------------------------------------------


def test_a_gathering_loop_writes_a_split_rule_whole(monkeypatch):
    """The rule of a split line in a loop that makes a table was its first physical line,
    `f_{i} := (k_{i}*`, cut off; it is the line as one line writes it."""
    head = "E := 200[GPa]\nA := 10[cm^2]\nL_1 := 2[m]\nL_2 := 3[m]\n% for i in [1, 2]:\nk_{i} := E*A/L_{i}\n"
    split, console_split = _run(head + "f_{i} := (k_{i}*\n   1[mm])\n% end\n", monkeypatch)
    whole, console_whole = _run(head + "f_{i} := (k_{i}*1[mm])\n% end\n", monkeypatch)
    assert not console_split and not console_whole, (console_split, console_whole)
    assert r"\texttt" not in split, split
    assert split == whole, (split, whole)


def test_a_placeholder_at_the_start_of_a_continued_line(monkeypatch):
    page, console = _run("% for q in ['+ 1', '* 2']:\nb := (2\n  {q})\n% end\n", monkeypatch)
    assert not console, console
    assert "3.00" in page and "4.00" in page, page


def test_a_comment_after_a_continued_line(monkeypatch):
    page, console = _run("x := 2\ny := (x +  # primer termino\n      1)\n", monkeypatch)
    assert not console, console
    assert r"y & = & 3.00" in page, page


@pytest.mark.parametrize("stop", ["", "# nota", '"""texto"""'])
def test_each_stop_ends_a_split_line(stop, monkeypatch):
    """Without the stop the lines would join into a valid `max(1, 2)`."""
    _, console = _run(f"b := max(1,\n{stop}\n2)\n", monkeypatch)
    assert "line 1" in console and "never closed" in console, console


def test_a_quote_inside_a_split_line_is_text(monkeypatch):
    page, console = _run("% for q in ['(', ')']:\nb_1 := max(1,\n  2)\n% end\n", monkeypatch)
    assert not console, console


@pytest.mark.parametrize(
    "line, entry",
    [
        ("V := T_1'", r"1.00 & 3.00"),
        ("V := d[[1, 2], [1]]'", r"\left[\begin{matrix}5.00 & 6.00\end{matrix}\right]"),
        ("V := T_1''", r"1.00 & 2.00"),
    ],
)
def test_primes_after_digits_brackets_and_primes(line, entry, monkeypatch):
    page, console = _run("T_1 := [1, 2; 3, 4]\nd := [5; 6]\n" + line + "\n", monkeypatch)
    assert not console, console
    assert entry in page.split("V & =")[-1], page[-500:]


def test_a_power_on_a_power_is_grouped_for_katex(monkeypatch):
    page, console = _run("U := [1, 2; 3, 4]\nA := U'^-1\nB := inv(U)^2\n", monkeypatch)
    assert not console, console
    assert r"\left(U^{T}\right)^{-1}" in page and r"\left(U^{-1}\right)^{2}" in page, page
    assert "}^{" not in page.replace(r"\right)^{", ""), page


@pytest.mark.parametrize(
    "power, said",
    [("U^0", "whole power"), ("U^(2[m])", "whole power"), ("U^1001", "at most 1000"),
     ("W^1000", "too large")],
)
def test_powers_a_matrix_is_not_raised_to(power, said, monkeypatch):
    _, console = _run(f"U := [1, 0; 0, 1]\nW := [2, 1; 1, 2]\nX := {power}\n", monkeypatch)
    assert said in console, console


# --- what the re-audit of 0.46.0 found unguarded -----------------------------------------


@pytest.mark.parametrize(
    "line, written",
    [
        ("A := U''", r"\left(U^{T}\right)^{T}"),
        ("B := solve(U', F)", r"\left(U^{T}\right)^{-1}\,F"),
    ],
)
def test_a_superscript_on_a_transpose_is_grouped(line, written, monkeypatch):
    page, console = _run("U := [1, 2; 3, 4]\nF := [1; 1]\n" + line + "\n", monkeypatch)
    assert not console, console
    assert written in page, page


def test_comments_on_continued_lines_in_a_loop_and_in_the_middle(monkeypatch):
    page, console = _run(
        "% for i in [1, 2]:\nc_{i} := (1 +  # uno\n  {i} +  # dos\n  1)\n% end\n", monkeypatch
    )
    assert not console, console
    assert "3.00" in page and "4.00" in page, page


def test_quotes_on_a_split_line_hold_their_hash_and_parenthesis(monkeypatch):
    page, console = _run('plot(x^2, x, 0, 1,\n     title="Momento # 1 (kN m")\n', monkeypatch)
    assert "never closed" not in console and "invalid syntax" not in console, console


def test_a_comment_on_a_middle_continued_line(monkeypatch):
    page, console = _run("y := (1 +  # uno\n      2 +  # dos\n      1)\n", monkeypatch)
    assert not console, console
    assert r"y & = & 4.00" in page, page
