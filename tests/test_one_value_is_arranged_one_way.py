r"""One value, one arrangement, wherever the page writes it.

From his own 0.30.9 run, four lines apart:

    Extrema — U1(x)
      x = L/2 (300.00 cm) · value = L² (0.15 qD + 0.2 qL)   (1.87×10⁶ kgf·cm)

    M_u  =  0.15 qD L² + 0.2 qL L²
         =  0.15 (18.35 kgf/cm) (600.00 cm)² + 0.2 (12.24 kgf/cm) (600.00 cm)²
         =  1.87×10⁶ kgf·cm

`U1(L/2)` both times. Neither form is wrong, which is what makes it different from
`m·kN` beside `kN·m` or `1e6` beside `×10⁶` - and a reader still has to do the algebra to
see that the block naming the design moment and the block computing it are the same
thing.

**One path simplifies and the other does not.** `_resolve_decidable_abs` - named
`_simplify_decidable_abs` until this change - exists to resolve an `|...|` whose sign the
sheet can decide, and it did that between two calls to `sp.simplify`. The second one is
what collects `0.15 L² qD + 0.2 L² qL` into `L² (0.15 qD + 0.2 qL)`; the ordinary
evaluation path runs no `simplify` at all, so `keep M_u = U1(L/2)` shows the substitution
as SymPy builds it. Neither call is left, which is why the name changed.

Measured over nine shapes an engineer writes - a udl moment at midspan, a cantilever at
the root, a point load, a deflection, a ratio, an absolute value, a shear through zero -
`simplify` changes the arrangement of exactly one: the one with two different symbols
against the same power, which is his. Everywhere else SymPy's own automatic evaluation
already produces the same expression. So resolving the absolute value is kept and the
rearrangement is dropped, and the majority form wins: the one every other block uses.
"""

import re

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import _latex

from conftest import block_text


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str, *, palette: str = "") -> str:
        magics = magic.EngMagics()
        captured.clear()
        if palette:
            magics.eng_units(palette)
            captured.clear()
        magics.eng("", source)
        return "".join(str(getattr(obj, "data", "")) for obj in captured)

    return run


BEAM = (
    "L := 6.00*m\n"
    "qD := 18*kN/m\n"
    "qL := 12*kN/m\n"
    "M_D(x) = qD*x*(L - x)/2\n"
    "M_L(x) = qL*x*(L - x)/2\n"
    "case D = M_D(x)\n"
    "case Lv = M_L(x)\n"
    "combo U1 = 1.2*D + 1.6*Lv\n"
)

HIS_SHEET = BEAM + "extrema(U1(x), x, 0, L)\nkeep M_u = U1(L/2)\nreport(M_u)\n"


def test_the_extrema_and_the_report_write_the_same_value(cell, capsys):
    """The defect, on the two blocks he read."""
    page = block_text(cell(HIS_SHEET, palette="kgf"))
    capsys.readouterr()

    assert "0.15 qD L² + 0.2 qL L²" in page, page
    assert "L² (0.15 qD + 0.2 qL)" not in page, page


def test_the_value_is_whatever_the_sheet_would_have_written(cell, capsys):
    """The property rather than the string: the extrema's symbolic value is the same
    expression the sheet's own evaluation of that point builds, so the two blocks cannot
    drift apart again for some other shape."""
    page = cell(HIS_SHEET, palette="kgf")
    capsys.readouterr()

    engine = EngineeringEngine()
    for statement in parse_cell(BEAM + "keep M_u = U1(L/2)\n"):
        engine.evaluate(statement)
    evaluated = engine.evaluate(parse_cell("report(M_u)\n")[0])
    # The renderer's own printer, not `sp.latex`: a multi-letter name is upright on this
    # page since #96, so comparing against SymPy's default would be comparing the page
    # with a spelling the page never uses.
    written = _latex(evaluated.symbolic_expression)

    assert written in page, (written, page[:400])


# --- what must not move ---------------------------------------------------------------


def test_an_absolute_value_is_still_resolved(cell, capsys):
    """The reason that function exists. A magnitude envelope's value must not reach the
    page with an `|...|` the sheet could have decided the sign of."""
    page = block_text(
        cell(
            "R_constr := 6*kN\nq_constr := 4*kN/m\nR_uso := -9*kN\nq_uso := 1*kN/m\n"
            "L := 2*m\n"
            "V_constr(x) = R_constr - q_constr*x\n"
            "V_uso(x) = R_uso + q_uso*x\n"
            "extrema(abs(V_uso(x)), x, 0, L)\n"
        )
    )
    capsys.readouterr()

    # The title keeps the `|...|` the sheet typed - `Extrema — |V_uso(x)|` - and that is
    # the name of the response, not a value. Only the values are asked about.
    values = re.findall(r"value = ([^(]+)\(", page)
    assert values, page
    assert not any("|" in value for value in values), values


def test_the_resolution_lands_on_the_expression_as_written(cell, capsys):
    """An `|...|` *and* something to collect, in one value.

    A mutant that applied the replacement to the simplified copy instead survived the
    whole suite: every sheet here either had an absolute value or had something to
    collect, and none had both, so the two answers were the same expression. This one
    has both - `1.2|qD| x (L-x)/2 + 1.6|qL| x (L-x)/2` reads `L²(0.6 qD + 0.8 qL)/4` as
    written and `L²(0.15 qD + 0.2 qL)` simplified.
    """
    page = cell(
        "L := 6*m\nqD := 18*kN/m\nqL := 12*kN/m\n"
        "M(x) = 1.2*abs(qD)*x*(L - x)/2 + 1.6*abs(qL)*x*(L - x)/2\n"
        "extrema(M(x), x, 0, L)\n"
    )
    capsys.readouterr()

    assert r"0.15\,\mathrm{qD}\,L^{2} + 0.2\,\mathrm{qL}\,L^{2}" in page, page
    assert r"\left(0.15" not in page and r"\left(0.6" not in page, page
    assert "183.60" in page, page


def test_a_boundary_value_is_arranged_the_same_way(cell, capsys):
    """A cantilever's root, which is a boundary point with a value worth arranging.

    His beam's two boundaries are both zero, so nothing there could tell the expression
    as written from the simplified one, and a mutant that stopped handing the written
    form to the boundary path survived the whole suite. A cantilever is as ordinary as
    his beam and its root is not zero.
    """
    page = cell(
        "L := 6*m\nqD := 18*kN/m\nqL := 12*kN/m\n"
        "M_D(x) = qD*x^2/2\nM_L(x) = qL*x^2/2\n"
        "case D = M_D(x)\ncase Lv = M_L(x)\n"
        "combo U1 = 1.2*D + 1.6*Lv\n"
        "extrema(U1(x), x, 0, L)\n"
        "keep M_emp = U1(L)\nreport(M_emp)\n",
        palette="kgf",
    )
    capsys.readouterr()

    written = r"0.6\,\mathrm{qD}\,L^{2} + 0.8\,\mathrm{qL}\,L^{2}"
    assert page.count(written) >= 2, page
    assert r"L^{2} \left(0.6" not in page, page


def test_the_coordinate_is_still_written_as_a_fraction(cell, capsys):
    """`x = L/2`, not `x = 0.5 L`.

    The contract this file did not have, and the regression it let through: a draft that
    stopped simplifying the response for *both* jobs fixed the value and broke the
    coordinate, because the derivative of the form as written solves to a float where the
    derivative of the simplified form solves to the rational. He found it on his own page
    after the release. The analysis keeps its simplified copy; only the value shown comes
    from the expression the sheet wrote.
    """
    page = cell(HIS_SHEET, palette="kgf")
    capsys.readouterr()

    assert r"\dfrac{L}{2}" in page, page  # `\dfrac` since the block reads at the page's size (test_a_characteristic_block_reads_at_the_page_s_size).
    assert "0.5 L" not in page, page


def test_a_zero_is_still_a_zero(cell, capsys):
    """A boundary value that is exactly zero prints `0`, not `0.0 L² qD`."""
    page = block_text(cell(HIS_SHEET, palette="kgf"))
    capsys.readouterr()

    body = page.split("Extrema", 1)[-1].split("M_u", 1)[0]
    assert "value = 0 (" in body, body


def test_the_number_beside_it_is_unchanged(cell, capsys):
    """Rearranging nothing is not recomputing anything. `1.2 qD L²/8 + 1.6 qL L²/8` with
    his loads and span."""
    page = block_text(cell(HIS_SHEET, palette="kgf"))
    capsys.readouterr()

    assert "1.87×10⁶ kgf·cm" in page, page


def test_the_ordinary_shapes_are_untouched(cell, capsys):
    """A udl moment at midspan: SymPy's own evaluation already gives one form, and
    `simplify` never had anything to say about it. Read from the LaTeX rather than
    through `block_text`, which flattens the braces this one is about."""
    page = cell("L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L - x)/2\nextrema(M(x), x, 0, L)\n")
    capsys.readouterr()

    assert r"\dfrac{q L^{2}}{8}" in page, page  # `\dfrac` since the block reads at the page's size (test_a_characteristic_block_reads_at_the_page_s_size).
    assert "45.00" in page, page


def test_a_name_is_spelled_the_way_the_page_spells_it(cell, capsys):
    """The second cause, and a defect on its own.

    This block printed through `sp.latex` while every other block prints through the
    renderer's `_latex`, and the two disagree about a multi-letter name: SymPy sets `qD`
    in italic, which MathJax spaces as a product of `q` and `D`, and #96 made this page
    write `\\mathrm{qD}`. So the design moment was italic in the extrema block and upright
    four lines below.
    """
    page = cell(HIS_SHEET, palette="kgf")
    capsys.readouterr()

    body = page.split("Extrema", 1)[-1].split("M_{u}", 1)[0]
    assert r"\mathrm{qD}" in body, body
    assert re.search(r"[^{]qD", body) is None, body
