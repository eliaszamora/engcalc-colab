r"""An ACI example reads in the units it is written in.

RC-1 from the external reinforced-concrete trial. The engine got a US code example's
engineering right once the numbers were transcribed into SI, which is work the engineer
should not have to do and a step where a transcription error would be invisible. Written
in its own units the sheet died on its first line:

    L := 20*ft      ->  unknown numeric name 'ft'

Pint already knows every one of these names, so this is an alias table, not a unit
definition. `kip`, `ksi`, `psi` and `inch` are Pint's own spellings; `ft` is Pint's
`foot`. What is *not* borrowed is `kilopound`, which Pint defines as a mass of 453 kg -
a name one letter away from the force a structural engineer means.

The aliases alone do not finish the job, and measuring is what showed it. With them in
place every declared value keeps its unit, and so does every computed one whose unit is
no more complex than its family's canonical member - `kip`, `foot * kip`, `inch`. The
exception is the same shape that RC-2B was in SI:

    phiMn = 0.9*As*fy*(d - a/2)      ->  inch^3 * kip_per_square_inch

Four unit terms against the moment family's two, so `_unit_is_the_engineers` correctly
refuses it and hands it to the family - which had only `kN * m` in it. An all-imperial
page then printed its flexural capacity in kilonewton-metres. The family table is now
chosen by the system the quantity is already in, so the same rejection lands in
`kip * ft`.

The dispatch is deliberately one-directional in the mixed case: any US customary unit in
a value's own units picks the US customary table. A sheet that mixes systems has already
made a choice the renderer should not quietly undo, and the alternative silently converts
the imperial half of a page somebody wrote in imperial on purpose.

Finally, `in` is a Python keyword, so `b := 12*in` can never parse - and `in` is the
first thing a US engineer writes. It said `invalid syntax` and nothing else.
"""

import ast

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.numeric import NumericContext
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import _unit_family


def expr(text: str) -> ast.Expression:
    return ast.parse(text.replace("^", "**"), mode="eval")


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


# --- the names resolve ------------------------------------------------------------

@pytest.mark.parametrize(
    "source, unit, magnitude",
    [
        ("20*ft", "foot", 20.0),
        ("12*inch", "inch", 12.0),
        ("60*ksi", "ksi", 60.0),
        ("4000*psi", "psi", 4000.0),
        ("70*kip", "kip", 70.0),
    ],
)
def test_each_imperial_name_resolves(source, unit, magnitude):
    value = NumericContext().evaluate_expression(expr(source))
    assert value.to(unit).magnitude == pytest.approx(magnitude)


def test_kip_is_a_force_and_not_a_mass():
    """Pint's `kilopound` is 453 kg. A force table that reaches it prints a beam's
    shear as a mass, and every dimensional check downstream agrees with it."""
    value = NumericContext().evaluate_expression(expr("70*kip"))
    assert dict(value.dimensionality) == {"[length]": 1, "[mass]": 1, "[time]": -2}


def test_an_aci_sheet_runs_start_to_finish_in_its_own_units(cell):
    latex = cell(
        "L := 20*ft\n"
        "b := 12*inch\n"
        "d := 21.5*inch\n"
        "fc := 4*ksi\n"
        "fy := 60*ksi\n"
        "As := 3.16*inch**2\n"
        "wu := 3.5*kip/ft\n"
    )
    assert "unknown numeric name" not in latex, latex
    assert r"\mathrm{ft}" in latex, latex
    assert r"\mathrm{ksi}" in latex, latex
    assert r"\mathrm{in}^{2}" in latex, latex


# --- the page stays in one system -------------------------------------------------

# The route the external trial used, and the one the SI fix for this shape targeted:
# a symbolic definition evaluated with `numeric(...)`. A numeric `:=` assignment does
# not reach the family while its own unit still shows figures - see the closing note.
CAPACITY = (
    "b := 12*inch\n"
    "d := 21.5*inch\n"
    "fc := 4*ksi\n"
    "fy := 60*ksi\n"
    "As := 3.16*inch**2\n"
    "a := As*fy/(0.85*fc*b)\n"
    "phi := 0.9\n"
    "z = d - a/2\n"
    "phiMn = phi*As*fy*z\n"
    "numeric(phiMn)\n"
)


def test_an_imperial_capacity_reads_as_a_moment_in_imperial(cell):
    """The defect. `inch^3 * ksi` is rightly rejected as the algebra's unit; what it
    was replaced with was the SI family's `kN * m`, on a page with no SI on it.

    272.69 kip-ft, checked by hand: T = 3.16 in^2 x 60 ksi = 189.6 kip,
    a = 189.6/(0.85 x 4 x 12) = 4.65 in, z = 21.5 - 2.32 = 19.18 in,
    0.9 x 189.6 x 19.18 = 3272 kip-in = 272.7 kip-ft.

    The two symbols are asserted separately rather than as `kip \\cdot ft` because the
    factor order is Pint's, and Pint orders a product alphabetically: `foot` before
    `kip`. US practice writes kip-ft. It happens to agree with practice in SI, where
    `kilonewton` sorts before `meter`. Ordering a moment force-first is a change to
    `format(units, "~L")`, the single call that typesets every unit in the system, so
    it is recorded as a limitation here and not smuggled in with the alias table.
    """
    final = _final(cell(CAPACITY))
    assert "272.69" in final, final
    assert r"\mathrm{kip}" in final, final
    assert r"\mathrm{ft}" in final, final
    assert "kN" not in final, final


def test_an_si_capacity_still_reads_kn_m(cell):
    """The mirror. Nothing about an SI sheet may move."""
    final = _final(cell(
        "fy := 413.6854*MPa\n"
        "As := 1935.48*mm**2\n"
        "z := 394.53*mm\n"
        "phi := 0.9\n"
        "phiMn = phi*As*fy*z\n"
        "numeric(phiMn)\n"
    ))
    assert "284.30" in final, final
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final
    assert "kip" not in final, final


def test_a_quantity_carrying_no_unit_information_is_read_as_si():
    """`_unit_family` is called in one place with a stand-in that has a dimensionality
    and no units at all. It must not become a US customary lookup by accident."""
    class _Quantity:
        def __init__(self, dimensionality):
            self.dimensionality = dimensionality

    moment = dict([("[time]", -2), ("[mass]", 1), ("[length]", 2)])
    assert _unit_family(_Quantity(moment)) == ("kN * m",)


def test_a_value_that_mixes_systems_is_shown_in_us_customary(cell):
    """Documented, not accidental: any US customary unit present picks the US table.
    Converting the imperial half of a deliberately imperial sheet is the worse error."""
    final = _final(cell(
        "fy := 60*ksi\n"
        "As := 2000*mm**2\n"
        "z := 400*mm\n"
        "phi := 0.9\n"
        "phiMn = phi*As*fy*z\n"
        "numeric(phiMn)\n"
    ))
    assert "219.69" in final, final
    assert r"\mathrm{kip}" in final, final
    assert r"\mathrm{ft}" in final, final
    assert "mm" not in final, final


# --- the keyword a US engineer writes first ---------------------------------------

def test_in_is_a_keyword_and_says_what_to_write_instead():
    with pytest.raises(EngSyntaxError) as excinfo:
        parse_cell("b := 12*in\n")
    message = str(excinfo.value)
    assert "inch" in message, message
    assert "keyword" in message, message


def test_an_ordinary_syntax_error_does_not_gain_the_inch_hint():
    """`12*(` reads well as a negative case and is worthless as one: it dies on the
    unbalanced-parenthesis guard and never reaches the hint at all. `12*` does reach
    it, which is the only reason this test is evidence of anything."""
    with pytest.raises(EngSyntaxError) as excinfo:
        parse_cell("b := 12*\n")
    message = str(excinfo.value)
    assert message.endswith("invalid syntax"), message


def test_a_name_that_merely_contains_in_is_not_read_as_the_keyword():
    """The word boundary, and the one mutation that survived the first draft of this
    module. `12*sin*` fails to parse, keeps its parentheses balanced so it reaches the
    hint, and contains the letters `in` inside a name. Without `\\b` the hint fires on
    it and answers a trigonometric typo with `write inch`, which is worse than the
    message it replaced."""
    with pytest.raises(EngSyntaxError) as excinfo:
        parse_cell("b := 12*sin*\n")
    assert "inch" not in str(excinfo.value), str(excinfo.value)


def test_a_capacity_assigned_as_a_number_also_reads_as_a_moment(cell):
    """This module first shipped with a note saying the `:=` route was a limitation it
    deliberately did not contract - `phiMn := 0.9*As*fy*(d - a/2)` kept `in^3 * ksi`,
    because a declared unit was left alone while it still showed figures. That was an
    SI question wearing imperial clothes, and it was answered separately: `declared`
    now asks whether the right-hand side names a unit, and a line built out of stored
    values names none.

    The contract is here because the imperial families are what this lands in.
    """
    final = _final(cell(
        "b := 12*inch\n"
        "d := 21.5*inch\n"
        "fc := 4*ksi\n"
        "fy := 60*ksi\n"
        "As := 3.16*inch**2\n"
        "a := As*fy/(0.85*fc*b)\n"
        "phiMn := 0.9*As*fy*(d - a/2)\n"
    ))
    assert "272.69" in final, final
    assert r"\mathrm{kip}" in final, final
    assert r"\mathrm{ft}" in final, final
    assert "ksi" not in final, final


def test_a_length_built_from_imperial_inputs_stays_in_inches(cell):
    """The guard beside it. `a` names no unit either, so it is no longer declared - and
    `in` costs no more than the family's own member, so it is kept where it was."""
    final = _final(cell(
        "b := 12*inch\n"
        "fc := 4*ksi\n"
        "fy := 60*ksi\n"
        "As := 3.16*inch**2\n"
        "a := As*fy/(0.85*fc*b)\n"
    ))
    assert "4.65" in final, final
    assert r"\mathrm{in}" in final, final
