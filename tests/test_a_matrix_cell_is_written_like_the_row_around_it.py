r"""A matrix cell is drawn with the settings its row was given.

Found looking for why the frame page writes `A_c E / L_c` when the engineer typed
`E*A_c/L_c`. The order of two names is a separate question and is not this file's - what
is this file's is that **one sheet writes the same expression two ways**:

    M(x) = P*x/2                     ->  \frac{P x}{2}
    k    = [ P*x/2, 0; 0, P*x/2 ]    ->  \frac{x P}{2}

`P` is a load the sheet has valued and `x` a coordinate it has not, so 0.31.13's rule puts
the load first. The rule lives in the printer and the printer is built from
`RenderSettings`, which is where `valued_names` is. `_value_latex` was given those
settings and passed them on - but only in its last line. The branch one line above,

    if isinstance(value, sp.MatrixBase):
        return _matrix_latex(value, unit_literals)

dropped them, and so did `_matrix_latex` itself, which never had a settings parameter. So
did the three places that build a matrix's stage list, and `_analysis_scalar_latex`.

`_analysis_scalar_latex` had no unit literals to pass and was left without them here. That
was a second thing, not this one: no sheet in the repository drew an eigenvalue whose
closed form holds a unit alias, so there was nothing to show and nothing to pin, and it was
written down rather than fixed blind. The audit of 0.31.14 drew one - `λ = 2 kN/m` with an
italic metre - and `test_a_unit_in_an_eigenvalue_is_typeset_as_a_unit` pins the fix.

That is the same defect #228 fixed, in the branches #228 did not reach. It is not about
matrices as such: anything the sheet knows and the printer needs - which names have
values, which are units, what precision, which palette - was missing from every one of
these. The factor order is simply the one that shows.

The substitution stage was never affected, because `_matrix_substitution_latex` has taken
settings all along. That is what makes the defect visible inside a single block: the
substitution row reorders and the symbolic row above it does not.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import RenderSettings, render_result

matplotlib.use("Agg")


def rendered_rows(source: str, settings: RenderSettings) -> list[str]:
    """`render_result` on its own, which is the other way into these branches.

    The magic reaches it only for `summary()` and `governing(...)`, so no sheet sends a
    matrix through it - but it is exported, the repository's own tests call it, and it
    carries a second copy of the stage list that `_numeric_matrix_stages` builds. The
    settings were dropped in that copy too, and its two mutants survived a full suite
    until these contracts existed. Four survived in all: the other two were the eigenvalue
    and the eigenvector, which a sheet does reach and no sheet here drew.
    """
    engine = EngineeringEngine()
    written = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        written.append(render_result(engine.evaluate(item), settings=settings))
    return written


@pytest.fixture
def page(monkeypatch):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def cells_of(written: str) -> list[str]:
    inner = written.split(r"\begin{matrix}")[1:]
    return [chunk.split(r"\end{matrix}")[0] for chunk in inner]


def test_a_matrix_cell_follows_the_same_factor_rule_as_a_row(page):
    """The load goes before the coordinate inside a matrix too."""
    written = page("P := 40*kN\nk = [ P*x/2, 0; 0, P*x/2 ]\n")

    assert r"\frac{P x}{2}" in written, written
    assert r"\frac{x P}{2}" not in written, written


def test_one_sheet_does_not_write_one_expression_two_ways(page):
    """The whole complaint, in one block: the row and the cell must agree."""
    written = page("P := 40*kN\nM(x) = P*x/2\nk = [ P*x/2, 0; 0, P*x/2 ]\n")

    assert written.count(r"\frac{P x}{2}") == 3, written
    assert r"\frac{x P}{2}" not in written, written


def test_a_block_does_not_contradict_itself_one_row_to_the_next(page):
    r"""The sharpest shape of it: `numeric(k)` draws both stages, one under the other.

    `_matrix_substitution_latex` has taken settings all along and `_matrix_latex` had
    none, so the symbolic stage said `x P` and the substitution stage directly below it
    said `(40.00 kN) x` - the two halves of one block disagreeing about which factor comes
    first.
    """
    written = page("P := 40*kN\nk = [ P*x/2, 0; 0, P*x/2 ]\nnumeric(k)\n")

    assert r"\frac{P x}{2}" in written, written
    assert r"\frac{x P}{2}" not in written, written
    assert r"\frac{\left(40.00\,\mathrm{kN}\right)\,x}{2}" in written, written


def test_an_eigenvalue_that_is_a_formula_follows_it(page):
    """`_analysis_scalar_latex` draws an eigenvalue that is not a quantity."""
    written = page("P := 40\nK = [ P*x, 0; 0, 2*P*x ]\neigenvals(K)\n")

    assert r"\lambda=P x" in written, written
    assert r"\lambda=x P" not in written, written


def test_an_eigenvector_that_holds_a_formula_follows_it(page):
    """The vector is a matrix of its own, drawn by `_matrix_latex`."""
    written = page("P := 40\nK = [ 1, P*x; 0, 3 ]\neigenvects(K)\n")

    assert r"\frac{P x}{2}" in written, written
    assert r"\frac{x P}{2}" not in written, written


def test_render_result_draws_an_evaluated_matrix_at_the_page_s_precision():
    """The factor order cannot show in this branch, and the precision can.

    A matrix reaches `NumericMatrixEvaluationResult` only when every symbol in it has a
    value, so there is no coordinate left to move and `valued_names` has nothing to say -
    a first version of this contract asserted an order that could never come out wrong.
    What the dropped settings did show is the precision: the symbolic stage fell back on
    the default 2 whatever the sheet had asked for.
    """
    written = rendered_rows(
        "P := 40*kN\nL := 6*m\n"
        "k = [ 0.123456789*P*L, 0; 0, 0.123456789*P*L ]\nnumeric(k)\n",
        RenderSettings(precision=6),
    )

    assert "0.123457 L P" in written[-1], written[-1]
    assert "0.12 L P" not in written[-1], written[-1]


def test_render_result_draws_a_partly_evaluated_matrix_the_same_way():
    settings = RenderSettings(valued_names=frozenset({"P"}))
    written = rendered_rows(
        "P := 40*kN\nk = [ P*x/2, 0; 0, P*x/2 ]\nnumeric(k)\n", settings
    )

    assert r"\frac{P x}{2}" in written[-1], written[-1]
    assert r"\frac{x P}{2}" not in written[-1], written[-1]


def test_a_cell_of_a_matrix_the_sheet_knows_nothing_about_is_unchanged(page):
    """No values at all: the shape of the name still decides, as it does in a row."""
    written = page("k = [ 3*q*L/8, 0; 0, 3*q*L/8 ]\n")

    assert r"\frac{3 q L}{8}" in written, written


# --- what must not move ---------------------------------------------------------------


def test_a_unit_in_a_matrix_cell_is_still_upright(page):
    """`_matrix_latex` already carried the unit literals; it keeps carrying them."""
    written = page("k = [ 3*m, 0; 0, 3*m ]\n")

    assert r"\mathrm{m}" in written, written


def test_a_matrix_of_numbers_is_untouched(page):
    (cells,) = cells_of(page("A_1 = [ 1, 0; 0, 1 ]\n"))

    assert cells == (
        r"\displaystyle 1 & \displaystyle 0\\\displaystyle 0 & \displaystyle 1"
    ), cells


def test_the_substitution_stage_still_says_what_it_said(page):
    """It was already right, and this change must not disturb it."""
    written = page("P := 40*kN\nL := 6*m\nk = [ P*L/2, 0; 0, P*L/2 ]\nnumeric(k)\n")

    assert r"\left(40.00\,\mathrm{kN}\right)" in written, written


def test_a_matrix_still_draws_as_a_matrix(page):
    written = page("P := 40*kN\nk = [ P*x/2, 0; 0, P*x/2 ]\n")

    assert written.count(r"\begin{matrix}") == 1, written
    assert written.count(r"\end{matrix}") == 1, written
