r"""A unit literal left in a displayed expression must read as a unit.

`subs(M(x), x, 3*m)` substitutes symbolically, so the metre stays in the expression as
an ordinary free symbol. The numeric layer resolves it for the arithmetic - that rule
predates this file - but the printer had no way to tell it from a variable, so a memoria
showed

    3 m q L / 2 - 9 m^2 q / 2   ->   45.00 kN*m

with the metre in italic, sitting between `3` and `q` exactly as a variable would. The
number was right and the typesetting said something false.

Multi-letter units were never affected: `kN` is already uprighted by the multi-letter
rule in `_EngineeringLatexPrinter`. Only `m`, `N` and `s` - the single-letter aliases -
rendered as variables, which is why this survived so long.

The uprighting is scoped to the names the evaluation actually resolved as units. A name
the user has defined is a value and keeps its italic, whatever it is called. That
scoping is the whole risk of the change: in structural work `N` is an axial force and
`s` is a spacing far more often than they are newtons and seconds.
"""

import re

import pytest

import engcalc_colab.magic as magic


def _italic_metre(latex: str) -> bool:
    """True when a bare `m` survives outside any \\mathrm{...} group."""
    without_units = re.sub(r"\\mathrm\{[^}]*\}", "", latex)
    return bool(re.search(r"(?<![A-Za-z\\])m(?![A-Za-z])", without_units))


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> str:
        captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def test_a_substituted_metre_is_upright(cell):
    """The reported defect: the metre read as a variable between two variables."""
    latex = cell(
        "L := 6*m\n"
        "q := 10*kN/m\n"
        "M(x) = q*x*L/2 - q*x**2/2\n"
        "numeric(subs(M(x), x, 3*m))\n"
    )
    assert r"3 \mathrm{m} q L" in latex, latex
    assert r"9 \mathrm{m}^{2} q" in latex, latex


def test_the_substitution_stage_keeps_the_metre_upright(cell):
    """The unit stays a unit in the row where the values arrive, not just the formula."""
    latex = cell(
        "L := 6*m\n"
        "q := 10*kN/m\n"
        "M(x) = q*x*L/2 - q*x**2/2\n"
        "numeric(subs(M(x), x, 3*m))\n"
    )
    stage = latex.split(r"& = &")[-2]
    assert "10.00" in stage, "not the substitution stage"
    # Asserting `\mathrm{m}` is present proves nothing here: q is 10 kN/m, so the stage
    # carries an upright metre in that denominator whatever the substituted one does.
    # What has to be true is that no italic metre is left, so strip every unit and look
    # for a bare `m` standing where a variable would stand.
    assert not _italic_metre(stage), stage


def test_a_defined_name_that_looks_like_a_unit_stays_a_variable(cell):
    """`m := 500*kg` is a mass. Uprighting it would relabel the user's own quantity.

    This is what scopes the rule. A printer that uprighted on the alias table alone
    would fix the metre above and corrupt every notebook that calls something `m`, `N`
    or `s`, which in structural work is most of them.
    """
    cell("m := 500*kg\nW = m*2\n")
    latex = cell("numeric(W)\n")
    assert r"\mathrm{m}" not in latex, latex
    assert "500.00" in latex, latex


def test_the_formula_row_also_leaves_a_defined_name_alone(cell):
    """The formula row carries no substitutions, so it needs the same scoping told to it.

    Checking the substitution row alone would not see this: there the name is replaced
    by its quantity and never reaches the symbol printer. The row above it, printed with
    no substitutions at all, is where a naive rule shows.
    """
    cell("m := 500*kg\nW = m*2\n")
    latex = cell("numeric(W)\n")
    formula = latex.split(r"& = &")[1]
    assert "500.00" not in formula, f"not the formula row: {formula}"
    assert r"\mathrm{m}" not in formula, formula
    assert _italic_metre(formula), formula
