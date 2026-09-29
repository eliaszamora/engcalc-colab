r"""What chapter 2 of his book found wrong on the page and in `solve` (2026-09-28).

He asked (2026-09-28) to solve every exercise of *Matrix Structural Analysis* (McGuire,
Gallagher, Ziemian) in EngCalc. Chapter 2's numbers all agreed with an independent
oracle; four things did not, and he chose them first:

- a coefficient the algebra computes, `-0.006999999999999999`, was rounded to the page's
  two decimals and printed `-0.01`: problem 2.3's reaction read `R_d = -0.01 E A` for
  `-0.007 E A`. A coefficient keeps as many significant figures as the page has
  decimals: `-0.007`; `0.588...` still reads `0.59`;
- with a kept `k`, `u = P/(5*k/4)` read `P/(5 1/4 k)`: `5` beside `1/4` is a mixed number,
  5.25 k, where the value is 1.25 k. A denominator holding a fraction is written as one,
  `\frac{P}{\frac{5 k}{4}}`, the numbers as typed;
- a bare `solve(eq(2*T, q*L), T)` wrote `T = q L/2` and defined nothing, though the README
  said the one-unknown form is the n = 1 case of a system, which defines its unknowns.
  Defining it was built and its audit refused it: the unknown is often the variable of
  the sheet's functions, and `solve(eq(V(x), 0), x)` made `M(x)` a constant - a plot flat
  at 45 kN·m, `M(L/4)` wrong. It still defines nothing; the README says so, and a later
  line that asks for its number is told to write `T = solve(...)`;
- `x_2 := solve(eq(...), x)` stopped at `unsupported numeric function`.
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


def test_a_computed_coefficient_keeps_its_figures(monkeypatch):
    page, console = _run("k = 2.8*E*A/L\nu = 0.0025*L\nR = -k*u\n", monkeypatch)
    assert not console, console
    assert r"R & = & - 0.007 E A" in page, page
    assert "0.01 E A" not in page, page


@pytest.mark.parametrize(
    ("line", "shown"),
    [
        # 1/(2*0.85) is an artefact of the algebra, and two figures are all the page has.
        ("a = As*fy/(0.85*fc*b)\nd_2 = a/2", r"0.59"),
    ],
)
def test_a_coefficient_of_two_figures_reads_as_before(line, shown, monkeypatch):
    page, _console = _run(line + "\n", monkeypatch)
    assert shown in page, page


def test_a_number_beside_a_reciprocal_is_one_fraction(monkeypatch):
    page, console = _run("keep k = A*E/L\nu = P/(5*k/4)\nkeep R = 2*P/3\nw = -R/(5*k/4)\n", monkeypatch)
    assert not console, console
    assert r"5 \frac{1}{4}" not in page, page
    assert r"u & = & \frac{P}{\frac{5 k}{4}}" in page, page


@pytest.mark.parametrize(
    ("line", "shown"),
    [
        # The audit: a point or a power beside `1/4` read as a mixed number too, and a
        # fold into one number rewrote what was typed (`4*k/4` read `k`).
        ("u = P/(1.5*k/4)", r"\frac{P}{\frac{1.5 k}{4}}"),
        ("u = P/(2^2*L/4)", r"\frac{P}{\frac{2^{2} L}{4}}"),
        ("u = P/(4*k/4)", r"\frac{P}{\frac{4 k}{4}}"),
    ],
)
def test_a_denominator_keeps_the_numbers_typed(line, shown, monkeypatch):
    page, _console = _run("keep k = A*E/L\n" + line + "\n", monkeypatch)
    assert r"\frac{1}{4}" not in page, page
    assert shown in page, page


def test_the_fraction_has_the_value_it_reads(monkeypatch):
    source = (
        "A := 2000[mm^2]\nE := 200000[MPa]\nL := 3[m]\nP := 100[kN]\n"
        "keep k = A*E/L\nu = P/(5*k/4)\nnumeric(u, mm)\n"
    )
    page, console = _run(source, monkeypatch)
    assert not console, console
    # 100 kN / (1.25 * 133333.33 kN/m) = 0.60 mm.
    assert page.rstrip().endswith(r"0.60\,\mathrm{mm} \end{array}"), page


def test_a_bare_solve_says_how_to_keep_its_answer(monkeypatch):
    source = "q := 10[kN/m]\nL := 6[m]\nsolve(eq(2*T, q*L), T)\nZ = 2*T\nnumeric(Z)\n"
    _page, console = _run(source, monkeypatch)
    assert "engcalc: line 5: numeric evaluation requires values for: T" in console, console
    assert "T was solved on line 3 on a line of its own" in console, console
    assert "write T = solve(...) to use it" in console, console


def test_a_named_solve_is_used(monkeypatch):
    source = "q := 10[kN/m]\nL := 6[m]\nT = solve(eq(2*T, q*L), T)\nZ = 2*T\nnumeric(Z)\n"
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert page.rstrip().endswith(r"60.00\,\mathrm{kN} \end{array}"), page


BEAM = (
    "L := 6[m]\nq := 10[kN/m]\nR_A = q*L/2\nM(x) = R_A*x - q*x^2/2\nV(x) = diff(M(x), x)\n"
    "solve(eq(V(x), 0), x)\n"
)


def test_a_bare_solve_for_the_maximum_leaves_the_function_a_function(monkeypatch):
    # The audit of 0.43.3: defining `x` here made `M(L/4)` read 45 kN·m, not 33.75.
    page, console = _run(BEAM + "numeric(subs(M(x), x, L/4))\n", monkeypatch)
    assert not console, console
    assert page.rstrip().endswith(r"33.75\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), page


def test_a_bare_solve_of_several_answers_defines_nothing(monkeypatch):
    # README: when the equation has more than one solution the statement defines nothing.
    source = "solve(x^2 - 4, x)\ny = 2*x\n"
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"y & = & 2 x" in page, page


def test_a_colon_equals_solve_is_worked_out(monkeypatch):
    source = "a := 2[m]\nb := 3[kN/m]\nx_2 := solve(eq(b*x, a*b - x*b), x)\nnumeric(x_2)\n"
    page, console = _run(source, monkeypatch)
    assert "unsupported numeric function" not in console, console
    assert not console, console
    assert r"1.00\,\mathrm{m}" in page, page


def test_a_colon_equals_solve_of_several_answers_says_so(monkeypatch):
    _page, console = _run("x_3 := solve(x^2 - 4, x)\n", monkeypatch)
    assert "unsupported numeric function" not in console, console
    assert "single numeric value" in console or "solutions" in console, console
