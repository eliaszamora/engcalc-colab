r"""A kept name reaches an integral, a derivative and a function built on a function.

Measured on 0.42.0 (2026-09-27), the same with `keep`: over `R_A = q*L/2` (kept since
0.42.0, its names have values) and `V(x) = R_A - q*x`, which reads `R_A - q x`,

    M(x) = integrate(V(x), x, 0, x)   read  ∫_0^x (qL/2 - qx) dx = qLx/2 - qx²/2
    W(x) = 2*V(x)                     read  q L - 2 q x

- the reaction a memoria names, gone one line after it was written, and the integral
written in what `V` expands to under a row that says `R_A - q x`. His ask (*"Sí, aborda
el nombre guardado en integrales y funciones"*). Three places: a call of a function whose
body keeps a name did not count as reaching one; `integrate` and `diff` were not calls a
written form may walk through; and the integral a row shows was read in the expanded
names. Each is checked against the evaluated expression before it is shown.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic

BEAM = "L := 6*m\nq := 10*kN/m\nR_A = q*L/2\nV(x) = R_A - q*x\n"


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


def _row(page: str, name: str) -> str:
    """From the row that defines `name` to the next row that defines something."""
    start = page.index(name + r" & = &")
    rest = page[start + len(name):]
    following = [rest.find(r"\left(x\right) & = &", 1), rest.find(r"\end{array}")]
    return page[start:start + len(name) + min(i for i in following if i > 0)]


def test_a_function_built_on_a_function_keeps_the_name(run):
    page, console = run(BEAM + "W(x) = 2*V(x)\n")
    assert not console, console
    row = _row(page, r"W\left(x\right)")
    assert "R_{A}" in row and r"q L" not in row, row


def test_an_integral_is_written_in_the_names_of_what_it_integrates(run):
    page, console = run(BEAM + "M(x) = integrate(V(x), x, 0, x)\n")
    assert not console, console
    row = _row(page, r"M\left(x\right)")
    assert r"\int\limits_{0}^{x} \left(R_{A} - q x\right)\, dx" in row, row
    assert r"R_{A} x - \frac{q x^{2}}{2}" in row, row
    assert r"\frac{q L}{2}" not in row, row


def test_an_integral_written_out_keeps_the_name_too(run):
    page, _console = run(BEAM + "M(x) = integrate(R_A - q*x, x, 0, x)\n")
    row = _row(page, r"M\left(x\right)")
    assert r"\left(R_{A} - q x\right)" in row and r"\frac{q L}{2}" not in row, row


def test_a_derivative_keeps_the_name(run):
    page, _console = run(BEAM + "M(x) = integrate(V(x), x, 0, x)\nS(x) = diff(M(x), x)\n")
    row = _row(page, r"S\left(x\right)")
    assert "R_{A}" in row and r"q L" not in row, row


def test_an_integral_whose_kept_form_would_be_false_is_not_shown(run):
    """`subs(V(x), L, 2*L)` changes the `L` inside `R_A` too: read with `R_A` standing the
    integral would be of the wrong beam, so it is shown in what it expands to."""
    page, console = run(BEAM + "M(x) = integrate(subs(V(x), L, 2*L), x, 0, x)\n")
    assert not console, console
    row = _row(page, r"M\left(x\right)")
    assert "R_{A}" not in row, row


@pytest.mark.parametrize(
    "line, keeps",
    [
        # The equation `solve` solved stays the row above the answer.
        ("x_0 = solve(eq(V(x), 0), x)\n", r"- q x = 0"),
        # A sum is written once, not once in each spelling.
        ("S = sum(V(k*m), k, 0, 2)\n", r"\sum_{k=0}^{2}"),
    ],
)
def test_a_call_a_second_walk_would_repeat_shows_as_it_did(run, line, keeps):
    """Only integrals and derivatives are read again with the kept names standing: read
    so, `solve` lost the equation it solved and `sum` was written twice on one row."""
    page, console = run(BEAM + line)
    assert not console, console
    assert keeps in page, page
    assert page.count(r"\sum") <= 1, page


def test_the_numbers_are_the_ones_they_were(run):
    """`M(L/2)` with `R_A = 30 kN`: 90 - 45 = 45 kN·m, as before."""
    page, console = run(BEAM + "M(x) = integrate(V(x), x, 0, x)\nnumeric(M(L/2))\n")
    assert not console, console
    assert page.rstrip().endswith(r"45.00\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), page[-300:]


def test_a_derivation_with_no_values_is_as_it_was(run):
    """Nothing kept - `q` and `L` have no value - so nothing moves."""
    page, _console = run("R_A = q*L/2\nV(x) = R_A - q*x\nM(x) = integrate(V(x), x, 0, x)\n")
    row = _row(page, r"M\left(x\right)")
    assert r"\int\limits_{0}^{x} \left(\frac{L q}{2} - q x\right)\, dx" in row or (
        "R_{A}" not in row
    ), row
