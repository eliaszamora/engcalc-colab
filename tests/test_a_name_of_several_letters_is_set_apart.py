r"""`qD*x` read `qDx`, one token, where the sheet multiplies two things.

The engineer's beam, on 0.31.3, three lines of one memoria:

    M_D(x) = qDx(L − x)/2
    M_u    = 0.15qDL² + 0.2qLL²
    d      = 5qDL⁴/(384EI_z)

`qD` is set upright, and that is #96's correction and the right one: a name of several
letters in italic is spaced by MathJax as a product, and the reactions block showed
`eqFy` as four sliding letters. What #96 did not do is set the finished upright block
apart from what follows it. LaTeX collapses the plain space between two factors - that
is what makes `bh` read as `b` times `h`, correctly, for single italic letters - and an
upright `qD` butted against an italic `x` gives the reader one word to take apart by
font alone.

The page already has the rule and the reason. `10\,\mathrm{kN}` is a thin space put
there because `10kN` ran together, and an upright multi-letter name is the same object
as an upright unit: a label, not a quantity. So it is set apart the same way.

Single letters are untouched, and that is the point of the second half of this file: `b
h`, `a m`, `384 E I_z` are italic quantities, and the convention for those is exactly
the juxtaposition LaTeX gives them.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_result


SHEET = """L := 6*m
qD := 18*kN/m
qL := 10*kN/m
E := 25*GPa
I_z := 4e-4*m^4
b := 30*cm
h := 60*cm
f_y := 420*MPa
As_prov := 20*cm^2
alpha := 0.85
beta := 0.80
"""


def last(source: str) -> str:
    engine = EngineeringEngine()
    written = ""
    for item in parse_cell(SHEET + source):
        if isinstance(item, ParsedHeading):
            continue
        written = render_result(engine.evaluate(item))
    return written


def test_a_name_of_several_letters_is_set_apart_from_what_follows_it():
    assert last("M_D(x) = qD*x*(L - x)/2") == (
        r"M_{D}\left(x\right) = \frac{\mathit{qD}\,x \left(L - x\right)}{2}"
    )


def test_a_coefficient_does_not_run_into_the_name_after_it():
    assert last("W = 0.15*qD*L^2 + 0.2*qL*L^2") == (
        r"W = 0.15\,\mathit{qD}\,L^{2} + 0.2\,\mathit{qL}\,L^{2}"
    )


def test_two_names_of_several_letters_are_set_apart_from_each_other():
    assert last("z = qD*qL") == r"z = \mathit{qD}\,\mathit{qL}"


def test_a_name_with_a_subscript_is_set_apart_by_its_base():
    """`As_prov` is `As` under a subscript, and `As` is what butts against `f_y`.

    The factors come out in SymPy's order, not the sheet's, which is why `f_y` is first
    here; that is the ordering defect `test_two_units_multiplied_read_as_one_unit`
    describes and neither file corrects.
    """
    assert last("T = As_prov*f_y") == r"T = f_{y}\,\mathit{As}_{prov}"


def test_a_power_of_such_a_name_is_set_apart_by_its_base():
    """`qD^2` is `qD` with an exponent, and `qD` is still what butts against `x`.

    Found by mutation: asking a `Pow` whether it is a name answers no, and nothing here
    noticed.
    """
    assert last("z = qD^2*x") == r"z = \mathit{qD}^{2}\,x"


# --- what must not move ---------------------------------------------------------------


def test_a_name_of_several_letters_beside_a_unit_already_had_its_space():
    """A unit asks to be set apart on its own, and a thin space is a thin space.

    Green before this correction and after it: nothing here may turn one space into two.
    """
    assert last("p = qD*m") == r"p = \mathrm{m}\,\mathit{qD}"


@pytest.mark.parametrize(
    "source, written",
    [
        ("A = b*h", r"A = b h"),
        ("Q = 0.5*1.2*b*h", r"Q = 0.5 \cdot 1.2 b h"),
        ("d = 5*L^4/(384*E*I_z)", r"d = \frac{5 L^{4}}{384 E I_{z}}"),
    ],
)
def test_single_letters_keep_the_juxtaposition_they_are_read_with(source, written):
    """Italic quantities of one letter. `bh` is how every textbook writes b times h, and
    a thin space between them would be this correction overreaching into algebra it was
    never about. `I_z` is a single letter under a subscript and counts as one."""
    assert last(source) == written


def test_a_greek_letter_spelled_out_is_one_letter_and_keeps_its_juxtaposition():
    r"""`alpha` is three letters in the sheet and one glyph on the page.

    The printer leaves a name SymPy spells back to SymPy - `\alpha`, `\phi`, `\Sigma` -
    precisely so it is set as the letter it is, and a letter is a quantity, so `\alpha
    \beta` is juxtaposed like `b h`. Found by mutation: dropping that guard here spaced
    every Greek pair and nothing noticed.
    """
    assert last("w = alpha*beta") == r"w = \alpha \beta"
    assert last("u = alpha*qD") == r"u = \alpha\,\mathit{qD}"


def test_a_number_and_its_unit_still_take_one_thin_space():
    assert last("F = 10*kN") == r"F = 10\,\mathrm{kN}"


def test_two_units_still_take_the_centred_dot():
    """From test_two_units_multiplied_read_as_one_unit, which this must not undo."""
    assert last("M_lim = 20*kN*m") == r"M_{lim} = 20\,\mathrm{kN} \cdot \mathrm{m}"
