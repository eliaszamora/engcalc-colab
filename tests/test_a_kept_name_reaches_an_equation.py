r"""A kept name reaches an equation: the one `solve` shows, and a line written with `eq`.

Measured on 0.42.1 (2026-09-27): over `R_A = q*L/2` (kept) and `V(x) = R_A - q*x`,
`x_0 = solve(eq(V(x), 0), x)` showed the equation it solved as `qL/2 - q x = 0`, one row
under `V(x) = R_A - q x`; and in the elastic curve of gap-map E4 the boundary condition
`bc2 = eq(subs(v(x), x, L), 0)` read `L C_1 + C_2 + qL^4/(24 E I) = 0` under a `v(x)` that
reads `R_A`. The next step of #359, his ask (*"aborda el punto 1"*). The equation is read
with the kept names standing and shown only once it agrees with the one computed.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic

BEAM = "L := 6*m\nq := 10*kN/m\nR_A = q*L/2\nV(x) = R_A - q*x\n"
CURVE = (
    "L := 6*m\nq := 10*kN/m\nE := 200*GPa\nI := 80e6*mm**4\nR_A = q*L/2\nV(x) = R_A - q*x\n"
    "M(x) = integrate(V(x), x, 0, x)\ntheta(x) = integrate(M(x)/(E*I), x) + C1\n"
    "v(x) = integrate(theta(x), x) + C2\nbc1 = eq(subs(v(x), x, 0), 0)\n"
    "bc2 = eq(subs(v(x), x, L), 0)\nsolve(bc1, bc2, C1, C2)\n"
)


@pytest.fixture
def run(monkeypatch):
    def run(source: str) -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        latex = " ".join(item.data for item in captured if isinstance(item, Math))
        return latex.replace(r"\displaystyle ", ""), console.getvalue()

    return run


def test_the_equation_solve_solved_keeps_the_name(run):
    page, console = run(BEAM + "x_0 = solve(eq(V(x), 0), x)\n")
    assert not console, console
    assert r"R_{A} - q x = 0" in page, page
    assert r"\frac{q L}{2} - q x = 0" not in page, page
    assert r"x_{0} & = & \frac{L}{2}" in page, page


def test_a_boundary_condition_keeps_the_name(run):
    page, console = run(CURVE)
    assert not console, console
    row = page[page.index(r"\mathit{bc}_{2} & = &"):]
    row = row[: row.index(r"\\[")]
    assert "R_{A}" in row and "= 0" in row, row


def test_what_solve_answers_is_what_it_was(run):
    page, _console = run(CURVE)
    assert r"C_{1} & = & - \frac{q L^{3}}{24 E I}" in page, page
    assert r"C_{2} & = & 0" in page, page


def test_an_equation_whose_kept_form_would_be_false_is_not_shown(run):
    """`subs(V(x), L, 2*L)` changes the `L` inside `R_A` too."""
    page, console = run(BEAM + "x_0 = solve(eq(subs(V(x), L, 2*L), 0), x)\n")
    assert not console, console
    assert "R_{A} - q x = 0" not in page, page
    assert r"x_{0} & = & L" in page, page


def test_a_boundary_condition_whose_kept_form_would_be_false_is_not_shown(run):
    page, console = run(BEAM + "bc = eq(subs(V(x), L, 2*L), 0)\n")
    assert not console, console
    row = page[page.index(r"\mathit{bc} & = &"):]
    assert "R_{A}" not in row, row


def test_a_solve_of_an_expression_shows_it_equal_to_zero(run):
    """`solve(V(x), x)` is `V(x) = 0`, as the evaluator reads it."""
    page, _console = run(BEAM + "x_0 = solve(V(x), x)\n")
    assert r"R_{A} - q x = 0" in page, page


def test_an_equation_with_nothing_kept_is_as_it_was(run):
    page, _console = run("V(x) = q*L/2 - q*x\nx_0 = solve(eq(V(x), 0), x)\n")
    assert r"= 0" in page and "R_{A}" not in page, page
