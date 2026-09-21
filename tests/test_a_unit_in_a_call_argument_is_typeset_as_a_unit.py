r"""A unit in a call's argument is set upright, whatever its name is worth in letters.

Seen on 0.31.8's own new reference block, where the heading of a piecewise asked at a
point reads

    q_v(9 m)        the metre in italic, with a plain space

while two blocks above, and on the engineer's own beam,

    M_P(100 cm)     upright, with the thin space a unit gets

Measured across the alias table, the split is not between units and names. It is between
**one letter and two**:

    m  s  N  g          italic      - `9 m`, `9 s`, `9 N`, `9 g`
    cm mm kN kg         upright     - `900\,\mathrm{cm}`, `9\,\mathrm{kN}`

`_render_function_call_lhs` calls `_latex(argument)` with no `unit_literals`, so the
printer has nothing to go on and falls back on its own rule that a name of several
letters is upright. A unit of one letter is indistinguishable from a variable there.

This is #96 in the one place that was never handed the answer, the same shape as the three
renderers 0.31.6 fixed: "those three renderers were never told which names are units,
which is the whole of #96 in the paths it did not reach."

The heading is part of the row, so the row's own `unit_literals` is what it is told - and
that set already yields to a stored value before consulting the alias table, so
`m := 500*kg` keeps the engineer's name in italic where it belongs.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")


def heading_of(written: str) -> str:
    """The left-hand side of the row whose call carries a number.

    The definition row above it names parameters and has no digit in it, which is what
    separates the two - not the letter `x`, because a function is free to call its
    parameters anything.
    """
    body = written.split("{lcl} ", 1)[-1]
    for row in body.split("\\\\[8pt]"):
        lhs = row.split(" & = & ")[0].strip().replace(r"\displaystyle ", "")
        if r"\left(" in lhs and any(character.isdigit() for character in lhs):
            return lhs
    raise AssertionError(written)


@pytest.fixture
def page(monkeypatch):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def called_with(argument: str) -> str:
    return f"f(x) = 2*x\nnumeric(f({argument}))\n"


@pytest.mark.parametrize("unit", ["m", "s", "N"])
def test_a_unit_of_one_letter_is_upright_in_a_heading(page, unit):
    """Every one the alias table has - it holds exactly these three of one letter."""
    heading = heading_of(page(called_with(f"9*{unit}")))

    assert heading == rf"f\left(9\,\mathrm{{{unit}}}\right)", heading


def test_the_three_are_every_single_letter_unit_there_is():
    """So the parametrisation above cannot quietly stop covering the whole of it."""
    from engcalc_colab.numeric import _UNIT_ALIASES

    assert sorted(name for name in _UNIT_ALIASES if len(name) == 1) == ["N", "m", "s"]


def test_a_unit_raised_to_a_power_is_upright_too(page):
    heading = heading_of(page(called_with("9*m*m")))

    assert heading == r"f\left(9\,\mathrm{m}^{2}\right)", heading


def test_a_partly_evaluated_row_tells_its_heading_too(page):
    """A row can be partial and still carry a bound argument in its heading.

    `numeric(g(9*m, v))` leaves `v` free and writes the metre beside it. Found by
    mutation: leaving the arguments out at the partial construction site changed nothing
    any contract here could see, because every other one asks a row that resolves.
    """
    heading = heading_of(page("g(u, v) = u + v\nnumeric(g(9*m, v))\n"))

    assert heading == r"g\left(9\,\mathrm{m}, v\right)", heading


def test_the_engineers_own_beam_is_unchanged(page):
    """`cm` was already upright; the fix must not be a second way of saying so."""
    heading = heading_of(page(called_with("900*cm")))

    assert heading == r"f\left(900\,\mathrm{cm}\right)", heading


# --- what must not move ---------------------------------------------------------------


@pytest.mark.parametrize(
    "argument,expected",
    [
        ("9000*mm", r"f\left(9000\,\mathrm{mm}\right)"),
        ("9*kN", r"f\left(9\,\mathrm{kN}\right)"),
        ("9*kg", r"f\left(9\,\mathrm{kg}\right)"),
    ],
)
def test_a_unit_of_several_letters_reads_as_it_did(page, argument, expected):
    assert heading_of(page(called_with(argument))) == expected


def test_a_name_that_is_not_a_unit_stays_in_italic(page):
    r"""`g` is not in the alias table, so in a heading it is a variable and reads as one.

    The boundary, not an afterthought: a first draft of this file asserted `9\,\mathrm{g}`
    beside the metre, and it was the contract that was wrong, not the page.
    """
    assert heading_of(page(called_with("9*g"))) == r"f\left(9 g\right)"


def test_a_number_with_no_unit_is_left_alone(page):
    assert heading_of(page(called_with("9"))) == r"f\left(9\right)", page(called_with("9"))


def test_a_stored_value_keeps_the_engineers_name_in_italic(page):
    """`m := 500*kg` makes `m` a mass. The precedence that governs the arithmetic
    governs the typesetting, or the page relabels the reader's own quantity."""
    written = page("m := 500*kg\nf(x) = 2*x\nnumeric(f(9*m))\n")

    assert heading_of(written) == r"f\left(9 m\right)", heading_of(written)


def test_the_definition_row_still_names_its_parameter(page):
    written = page(called_with("9*m"))

    assert r"\displaystyle f\left(x\right) & = & \displaystyle 2 x" in written, written
