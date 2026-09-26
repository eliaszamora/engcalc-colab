r"""`% if`: a sheet decides which lines run, and the memoria says why.

    % if Vu > phi_v*V_c:
    V_s = Vu/phi_v - V_c
    % else:
    V_s := 0*kgf
    % end

Approved on 2026-09-25 (*"Apruebo tus recomendaciones en los 4 puntos, empieza por el
if"*): a line that starts with `%` is control, written as Python - `if`, `elif`, `else` -
and a block closes with `% end`. The condition reads the sheet's values with their units.
Only the branch that holds runs, and it is opened by a sentence with the numbers, `Como
Vu = 7920.00 kgf > φ_v V_c = 7603.63 kgf:`, which is what a reviewer needs to see. He
could not find it the first time: it was Colab's text, smaller and in another letter than
the rows. It is now typeset as the rows are, "Como" in bold, with room above and below. The
branch that does not hold is neither computed nor written. A cell without `%` lines runs
exactly as before.
"""

import contextlib
import io

import pytest
from IPython.display import Markdown, Math

import engcalc_colab.magic as magic

NOTE = r"\textbf{Como}"

SHEAR = (
    "fc := 210*kgf/cm^2\nb := 30*cm\nd := 44*cm\nphi_v := 0.75\n"
    "V_c := 0.53*sqrt(fc*kgf/cm^2)*b*d\n"
)


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str):
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        # The sentence is typeset as the rows are, in their letter and size (his choice,
        # option 1b, 2026-09-25): a Math output that opens with a bold "Como".
        assert not [item for item in captured if isinstance(item, Markdown) and "Como" in item.data], captured
        shown = [item.data for item in captured if isinstance(item, Math)]
        notes = [data for data in shown if NOTE in data]
        math = " ".join(data for data in shown if NOTE not in data)
        return math, notes, console.getvalue()

    return run


IF_ELSE = (
    "% if Vu > phi_v*V_c:\n"
    "V_s = Vu/phi_v - V_c\n"
    "numeric(V_s)\n"
    "% else:\n"
    "V_s := 0*kgf\n"
    "% end\n"
    "V_t = V_c + V_s\n"
    "numeric(V_t)\n"
)


def test_the_branch_that_holds_runs_and_says_why(sheet):
    math, notes, console = sheet(SHEAR + "Vu := 7920*kgf\n" + IF_ELSE)
    assert not console, console
    (note,) = notes
    assert NOTE in note and note.endswith(r"\,\text{:}"), note
    # No room of its own: it stands apart from the rows around it by the one rule every
    # block has, the magic's spacer (test_one_spacing_rule).
    assert note.startswith(r"\textbf{Como}"), note
    assert r"7920.00\,\mathrm{kgf} > \phi_{v} V_{c} = 7603.63\,\mathrm{kgf}" in note, note
    assert r"421.83\,\mathrm{kgf}" in math, math
    assert r"V_{s} & = & \displaystyle 0.00" not in math, math
    # The line after the block runs on the branch's value, as a page without `%` writes it.
    assert r"10.56\,\mathrm{tonf}" in math, math


def test_the_other_branch_when_it_does_not_hold(sheet):
    math, notes, console = sheet(SHEAR + "Vu := 5000*kgf\n" + IF_ELSE)
    assert not console, console
    (note,) = notes
    assert r"5000.00\,\mathrm{kgf} \leq \phi_{v} V_{c} = 7603.63\,\mathrm{kgf}" in note, note
    assert "421.83" not in math and r"\frac{\mathit{Vu}}{\phi_{v}}" not in math, math
    assert r"10138.17\,\mathrm{kgf}" in math, math


def test_elif_takes_the_first_that_holds(sheet):
    source = SHEAR + "Vu := 4000*kgf\n" + (
        "% if Vu <= phi_v*V_c/2:\n"
        "s := 60*cm\n"
        "% elif Vu <= phi_v*V_c:\n"
        "s := d/2\n"
        "% else:\n"
        "s := d/4\n"
        "% end\n"
    )
    math, notes, console = sheet(source)
    assert not console, console
    (note,) = notes
    assert r"\leq" in note and "3801.81" in note, note
    assert r"s & = & \displaystyle 22.00\,\mathrm{cm}" in math, math
    assert r"60.00\,\mathrm{cm}" not in math, math


def test_blocks_nest(sheet):
    source = SHEAR + "Vu := 7920*kgf\n" + (
        "% if Vu > phi_v*V_c:\n"
        "% if Vu > 2*phi_v*V_c:\n"
        "s := d/4\n"
        "% else:\n"
        "s := d/2\n"
        "% end\n"
        "% end\n"
    )
    math, notes, console = sheet(source)
    assert not console, console
    assert len(notes) == 2, notes
    assert r"s & = & \displaystyle 22.00\,\mathrm{cm}" in math, math


def test_an_if_that_does_not_hold_and_has_no_else_writes_nothing(sheet):
    math, notes, console = sheet(SHEAR + "Vu := 5000*kgf\n% if Vu > phi_v*V_c:\nV_s = Vu/phi_v - V_c\n% end\ny := 2*m\n")
    assert not console, console
    assert notes == [] and "V_{s}" not in math, (notes, math)
    assert r"y & = & \displaystyle 2.00\,\mathrm{m}" in math, math


def test_a_condition_joins_with_and(sheet):
    math, notes, console = sheet(SHEAR + "Vu := 7920*kgf\n% if Vu > phi_v*V_c and d < 50*cm:\ny := 1*m\n% end\n")
    assert not console, console
    (note,) = notes
    assert r"\;\text{y}\;" in note, note


@pytest.mark.parametrize(
    "source, words",
    [
        ("% if 1 > 0:\ny := 1*m\n", ("line 1", "% end")),
        ("y := 1*m\n% else:\n", ("line 2", "% else")),
        ("y := 1*m\n% end\n", ("line 2", "% end")),
        ("% switch x:\n% end\n", ("line 1", "% if")),
        ("% if 2*m > 3*kgf:\ny := 1*m\n% end\n", ("line 1", "compare")),
        ("% if Q > 0:\ny := 1*m\n% end\n", ("line 1", "Q")),
    ],
)
def test_a_block_written_wrong_says_where(sheet, source, words):
    _math, _notes, console = sheet(source)
    for word in words:
        assert word in console, (word, console)


def test_a_percent_inside_a_text_block_is_text(sheet):
    source = '"""\nLa cuantía mínima es\n% 0.18 del área bruta.\n"""\ny := 1*m\n'
    math, notes, console = sheet(source)
    assert not console, console
    assert r"y & = & \displaystyle 1.00\,\mathrm{m}" in math, math


def test_a_line_written_wrong_in_a_branch_that_does_not_run_still_refuses_the_cell(sheet):
    # As a cell without `%` does: nothing is written until every line reads.
    math, _notes, console = sheet("y := 1*m\n% if 1 > 2:\nz = w +\n% end\n")
    assert "line 3" in console, console
    assert "y" not in math, math


def test_a_line_inside_a_branch_is_counted_in_the_cell(sheet):
    _math, _notes, console = sheet("% if 1 > 0:\ny := 1*m\nz = w +\n% end\n")
    assert "line 3" in console, console


@pytest.mark.parametrize("zero", ["0", "0*kN"])
def test_a_value_compares_with_zero_whatever_its_unit(sheet, zero):
    # `0*kN` reaches the condition as a plain 0: a zero has no unit left to disagree with.
    math, notes, console = sheet(f"V := 5*kN\n% if V > {zero}:\ny := 1*m\n% end\n")
    assert not console, console
    (note,) = notes
    assert r"y & = & \displaystyle 1.00\,\mathrm{m}" in math, math


def test_a_number_other_than_zero_still_needs_its_unit(sheet):
    _math, _notes, console = sheet("V := 5*kN\n% if V > 3:\ny := 1*m\n% end\n")
    assert "compare" in console, console
