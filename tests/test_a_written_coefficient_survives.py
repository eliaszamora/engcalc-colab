r"""The page shows the numbers the engineer wrote.

    a = As*fy/(0.85*fc*b)        rendered as    a = 1.18 fy As / (b fc)

0.85 is what ACI 318 §22.2.2.4.1 requires, and a reviewer checking the sheet against the
code cannot find it, because the page no longer contains it. SymPy inverts a Float in a
denominator when it builds the expression: `1/0.85` becomes `1.176470588…`, and #79's
precision rule then prints it as 1.18.

This is `## v0.25.0`'s finding in a second place. A load combination written as an
ordinary definition rendered `0.6*qD*x*(L - x) + 0.8*qL*x*(L - x)` - "the number is right
and the load combination is gone" - and `case`/`combo` fixed it by keeping the terms as
written beside the expanded expression. The same answer works here: keep the expression
as it was typed, for the page, and go on computing with the evaluated one.

Three things were measured before this was written, and two of them changed the design.

Building the written form without flattening is worse than the defect. Nested
unevaluated `Add`s and `Mul`s print with grouping SymPy would never produce: `5qL⁴/(384EI)`
came out `L⁴ · 5 q` and `h - cover - db_st - db/2` came out `-(cover + db_st - h)`. Flat
`Add(*args)` and `Mul(*args)` render identically to the evaluated form everywhere except
where the coefficient was being destroyed.

And the obvious way to check a written form against its evaluated twin does not work.
`written - value == 0` is False even when they agree, because subtracting does not force
an unevaluated expression to flatten; `simplify` does force it, costs 33 ms a definition
and still failed to verify three of seven real formulas. A `srepr` round-trip verifies
all seven at 1.9 ms. A written form that does not survive that check is discarded and
the evaluated one is shown, because a wrong formula on the page is worse than an ugly
one.
"""

import pytest

import engcalc_colab.magic as magic


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


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


INPUTS = "fc := 25*MPa\nfy := 420*MPa\nAs := 1935*mm**2\nb := 300*mm\n"


def test_a_coefficient_written_in_a_denominator_is_on_the_page(cell):
    """The defect. 0.85 is the number the code requires and the number to check."""
    latex = cell(INPUTS + "a = As*fy/(0.85*fc*b)\n")
    assert "0.85" in latex, latex
    assert "1.18" not in latex, latex


def test_the_value_behind_it_is_unchanged(cell):
    """Presentation only, and the check that says so.

    As fy / (0.85 fc b) = 1935 x 420 / (0.85 x 25 x 300) = 812700 / 6375 = 127.48 mm.
    """
    final = _final(cell(INPUTS + "a = As*fy/(0.85*fc*b)\nnumeric(a)\n"))
    assert "127.48" in final, final
    assert r"\mathrm{mm}" in final, final


@pytest.mark.parametrize(
    "source, expected",
    [
        ("M = q*L**2/8", r"\frac{q L^{2}}{8}"),
        ("M = R_A*x - q*x**2/2", r"x R_{A} - \frac{q x^{2}}{2}"),
        ("d = h - cover - db_st - db/2",
         r"- \mathrm{cover} - \frac{\mathrm{db}}{2} - \mathrm{db}_{st} + h"),
        ("w = 1.2*D + 1.6*L", "1.2 D + 1.6 L"),
        ("Vc = 0.17*fc*b", r"0.17 b \mathrm{fc}"),
    ],
)
def test_a_formula_that_already_read_correctly_does_not_move(cell, source, expected):
    """Every one of these renders identically with the written form or without it. They
    are the reason showing a written form is safe at all, and the reason the flattening
    matters: built with nested unevaluated Adds and Muls, three of them change.

    Each expectation is the engine's own output, not SymPy's default printer - this
    module's first draft used `sp.latex`, which orders `q L^2` the other way round and
    does not know the upright rule for a multi-letter name.
    """
    latex = cell(source + "\n")
    assert expected in latex, latex


def test_an_integer_denominator_was_never_the_problem(cell):
    """`q*L^2/8` keeps its 8 because SymPy holds an integer division as a Rational. Only
    a decimal is inverted, which is why this went unnoticed: the beam formulas in this
    repository all divide by integers."""
    latex = cell("M = q*L**2/8\n")
    assert r"\frac{q L^{2}}{8}" in latex, latex


def test_a_coefficient_in_a_numerator_was_never_the_problem(cell):
    latex = cell(INPUTS + "Vc = 0.17*fc*b\n")
    assert "0.17" in latex, latex


def test_a_definition_built_on_other_definitions_is_left_alone(cell):
    """The boundary, and the reason it is drawn where it is.

    `phiMn = phi*As*fy*(d - a/2)` substitutes `d` and `a`, and what arrives is an
    expression SymPy has already evaluated. The written form of that is *wider* than the
    evaluated one, because it keeps `1.18 fy As / (2 b fc)` where evaluation folds the
    halving into `0.59 fy As / (b fc)`. Width is not cosmetic: it tips the row past the
    wrapping budget, and the wrapping path splits a product into additive terms. The
    definition stops being `fy phi As (...)` and becomes two rows in which `As` is
    squared.

    So the written form is declined here, and `As^2` appearing on the page is the sign
    that it was not. This is the boundary RC-3 moves - until a definition can be shown
    without expanding the names inside it, there is nothing to preserve - and the
    contract exists so that removing the restriction is caught rather than shipped.

    The first draft of this test asserted against `(-1)` and `\frac{1}{b}`, which is what
    `sp.latex` produces and not what the renderer does. It passed with the restriction
    removed, which is no test at all.
    """
    latex = cell(
        "b := 300*mm\nh := 500*mm\ncover := 40*mm\ndb_st := 10*mm\ndb := 20*mm\n"
        "fc := 25*MPa\nfy := 420*MPa\nAs := 1935*mm**2\nphi := 0.9\n"
        "d = h - cover - db_st - db/2\n"
        "a = As*fy/(0.85*fc*b)\n"
        "phiMn = phi*As*fy*(d - a/2)\n"
    )
    assert r"\mathrm{As}^{2}" not in latex, latex
    assert r"\mathrm{fy} \phi \mathrm{As} \left(" in latex, latex
    # `a`'s own row is still fixed - the restriction is per definition, not per sheet.
    assert "0.85" in latex, latex


def test_a_negated_sum_is_not_typeset_as_a_difference(cell):
    """The one place the written form was wrong on the page, and `_agrees_with` could
    not see it, because what was wrong was the typesetting and not the mathematics.

    `Mul(-1, Add(a, b), evaluate=False)` is the right expression and prints `- a + b`:
    the parentheses are dropped and the page states something false. The same trap as
    #76, where a rendering that was accepted quietly lost a letter. Only the unary minus
    is affected, and only for a sum, so that is where the written form declines.
    """
    latex = cell("y = -(a + b)\n")
    assert "- a - b" in latex, latex
    assert "- a + b" not in latex, latex


def test_a_negated_quotient_still_keeps_its_coefficient(cell):
    """The other side of that restriction: declining for sums must not decline for
    everything. `-x/(0.85*b)` is a unary minus over a quotient, and the 0.85 is exactly
    what this change exists to keep."""
    latex = cell("y = -x/(0.85*b)\n")
    assert "0.85" in latex, latex
    assert "1.18" not in latex, latex


def test_a_difference_of_a_sum_keeps_the_brackets_that_were_typed(cell):
    """Better than it was, and free. `a - (b + c)` builds its negation inside an `Add`,
    where the parentheses survive, so the written form keeps the grouping the engineer
    typed instead of flattening it to `a - b - c`."""
    latex = cell("y = a - (b + c)\n")
    assert r"a - \left(b + c\right)" in latex, latex


def test_the_written_form_is_verified_before_it_is_shown():
    """A written form that does not evaluate back to the expression it was built beside
    is discarded rather than shown. The check is a `srepr` round-trip, chosen because
    `simplify` failed on three of seven real formulas at seventeen times the cost."""
    import sympy as sp

    from engcalc_colab.engine import _agrees_with

    x, y = sp.symbols("x y")
    honest = sp.Mul(x, sp.Pow(sp.Mul(sp.Float("0.85"), y, evaluate=False), -1, evaluate=False), evaluate=False)
    assert _agrees_with(honest, x / (sp.Float("0.85") * y))
    assert not _agrees_with(honest, x / (sp.Float("0.85") * y) + 1)
