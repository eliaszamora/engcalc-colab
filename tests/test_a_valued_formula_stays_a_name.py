r"""A formula of the sheet's names that already has a number stays a name, as `keep` does.

`phiMn = phi*As*fy*(d - a/2)` over plain `d = h - cover` and `a = As*fy/(0.85*fc*b)` read
`φ As fy (h - 0.59 As fy/(fc b) - cover)`: the two definitions expanded into it, the 0.85
and the 1/2 folded into 0.59, the substitution over two rows. A memoria written by hand
reads `φ As fy (d - a/2)` and substitutes `d` and `a` by their numbers. `keep` did that, and
only where the sheet wrote it (RC-3 made it opt-in on purpose, measured then).

His decision, 2026-09-26, after both rules were measured (*"Sí, adopta la regla 2 por
defecto. Lo dejo a tu criterio"*): keeping *every* definition made the frames worse
(`R_2 = R_1` for a matrix); keeping a scalar formula whose names all have values moved no
reference page. So the mark is given where both hold:

- the definition is a formula of the sheet's own names (`d = h - cover`), not a value
  written out (`L = 6*m` still folds into `M = 45 kN·m`);
- it is a scalar that can be worked out in numbers now, so a formula over names without a
  value - a derivation's `a = E*A/L` - still expands, as the algebra needs.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def run(monkeypatch):
    def run(source: str) -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), console.getvalue()

    return run


BEAM = (
    "phi := 0.9\nAs := 1500*mm^2\nfy := 420*MPa\nh := 500*mm\ncover := 40*mm\n"
    "b := 300*mm\nfc := 28*MPa\n"
    "d = h - cover\na = As*fy/(0.85*fc*b)\nphiMn = phi*As*fy*(d - a/2)\nnumeric(phiMn)\n"
)


def test_a_capacity_reads_in_the_names_it_was_written_with(run):
    page, console = run(BEAM)
    assert not console, console
    assert r"\mathit{phiMn} & = & \displaystyle \phi\,\mathit{As}\,\mathit{fy}\,\left(d - \frac{a}{2}\right)" in page, page
    assert "0.59" not in page, page


def test_the_substitution_puts_in_each_name_s_number(run):
    page, _console = run(BEAM)
    assert r"\left(460.00\,\mathrm{mm}\right) - \frac{\left(88.24\,\mathrm{mm}\right)}{2}" in page, page
    assert r"235.81\,\mathrm{kN} \cdot \mathrm{m}" in page, page


def test_a_value_written_out_still_folds(run):
    """`L = 6*m` is a value, not a formula of names: `M` reads its number as before."""
    page, _console = run("L = 6*m\nq = 10*kN/m\nM = q*L^2/8\n")
    assert r"M & = & \displaystyle 45\,\mathrm{kN} \cdot \mathrm{m}" in page, page


def test_a_formula_that_reads_a_value_written_out_reads_it_as_a_name(run):
    """`M` read `9 m^2 q/2` here, and was left out of this rule: kept, it drew `L`'s
    written form, `10 kN (6 m)^2/(8 m)`. Since his decision of 2026-09-27 a value written
    out stands beside a name that stands, `M` reads `q L^2/8`, and with every name it reads
    holding a number it stays a name. See `test_a_value_written_out_stands_beside_a_name`."""
    page, _console = run("q := 10*kN/m\nL = 6*m\nM = q*L^2/8\ny = 2*M\n")
    assert r"M & = & \displaystyle \frac{q L^{2}}{8}" in page, page
    assert r"y & = & \displaystyle 2 M" in page, page


def test_a_formula_over_names_without_a_value_still_expands(run):
    """A derivation: `a` has no number, so `k` is written in what it stands for."""
    page, _console = run("a = E*A/L\nk = 2*a\n")
    k_row = page[page.index(r"k & = &"):]
    assert r"2 a" not in k_row and "L" in k_row, k_row


def test_a_formula_of_a_free_variable_still_expands(run):
    """`L` and `q` have values, `x` has none: `M` is a law along the span, not a number."""
    page, _console = run("L := 6*m\nq := 10*kN/m\nM = q*x*(L - x)/2\ny = 2*M\n")
    y_row = page[page.index(r"y & = &"):]
    assert "2 M" not in y_row and "x" in y_row, y_row


def test_a_matrix_of_valued_names_is_left_as_it_was(run):
    """Only a scalar is a number to substitute; a matrix keeps its own rules (`:=`)."""
    page, _console = run("a := 2*m\nK = [a, 0; 0, a]\nJ = 2*K\n")
    j_row = page[page.index(r"J & = &"):]
    assert "2 K" not in j_row, j_row


def test_the_number_follows_a_later_value(run):
    page, _console = run("h := 60*cm\nd = h - 4*cm\ny = 2*d\nh := 50*cm\nnumeric(y)\n")
    assert r"y & = & \displaystyle 2 d" in page, page
    assert page.rstrip().endswith(r"92.00\,\mathrm{cm} \end{array}"), page[-200:]


def test_a_colon_equals_line_reads_it(run):
    page, _console = run("h := 60*cm\ncover := 4*cm\nd = h - cover\nx := 2*d\ny = 3*d\n")
    assert r"x & = & \displaystyle 112.00\,\mathrm{cm}" in page, page
    assert r"y & = & \displaystyle 3 d" in page, page
