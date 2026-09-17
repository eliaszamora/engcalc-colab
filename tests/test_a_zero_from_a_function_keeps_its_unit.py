r"""A moment that is zero at a support is still a moment: `M_B = M(L)` reads `0.00 kN·m`.

A beam, and the moment where it is known to vanish:

    M(x) = q x (L - x)/2
    M_B  = M(L)
    numeric(M_B)      ->  M_B = 0 = 0.00

and the same with `keep M_0 = M(0*mm)`, in `report` and in the summary. A zero with no
unit on a page where every other moment has one reads as a number that is not a moment.
`numeric(M(L))`, written in place, has always read `0.00 kN·m`.

**Why.** Calling a function substitutes into its expression, and SymPy simplifies as it
substitutes: `q L (L - L)/2` is `0` before anything numeric sees it, and a SymPy zero has
no dimension to carry. `numeric(M(L))` never meets that zero, because it substitutes
*quantities* into the function - `(10 kN/m)(6 m)((6 m) - (6 m))/2` - and Pint keeps the
unit through the cancellation.

**So a definition whose value is an exact zero asks that same evaluation for its unit**,
once, when it is defined, and a numeric row of that name answers in it. A zero the sheet
wrote with no unit stays a plain zero, and a value that is not zero is not touched.
"""

import re

import engcalc_colab.magic as magic

from conftest import block_text


def page(monkeypatch, source: str) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", source)
    return block_text("".join(str(getattr(obj, "data", "")) for obj in captured))


BEAM = "L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L - x)/2\nV(x) = q*(L/2 - x)\n"


def test_the_moment_at_a_support(monkeypatch, capsys):
    text = page(monkeypatch, BEAM + "M_B = M(L)\nnumeric(M_B)\n")
    capsys.readouterr()

    assert text.rstrip().endswith("0.00 kN·m \\endarray"), text


def test_the_shear_at_midspan(monkeypatch, capsys):
    text = page(monkeypatch, BEAM + "V_c = V(L/2)\nnumeric(V_c)\n")
    capsys.readouterr()

    assert text.rstrip().endswith("0.00 kN \\endarray"), text


def test_a_kept_zero_in_report_and_summary(monkeypatch, capsys):
    """`keep` stores a number of its own, so it is the second place the zero was lost.

    The short beam in millimetres this was found on: the support reads in the unit the
    midspan does, by the rule `test_a_zero_reads_in_the_unit_beside_it` gives a zero."""
    text = page(
        monkeypatch,
        "L := 700*mm\nq := 8*kN/m\nM(x) = q*x*(L - x)/2\n"
        "keep M_c = M(L/2)\nreport(M_c)\nkeep M_0 = M(0*mm)\nreport(M_0)\nsummary()\n",
    )
    capsys.readouterr()

    assert text.count("490.00 N·m") == 2, text
    assert len(re.findall(r"(?<![\d.])0\.00 N·m", text)) == 2, text
    # A summary row reads `name = value` since test_a_computed_block_is_written_like_the_working.
    assert text.rstrip().endswith("M_0 = 0.00 N·m"), text


def test_a_kept_zero_substitutes_with_its_unit(monkeypatch, capsys):
    """A kept name substitutes as its stored number, so that number carries the unit too."""
    text = page(
        monkeypatch,
        "L := 700*mm\nq := 8*kN/m\nM(x) = q*x*(L - x)/2\n"
        "keep M_c = M(L/2)\nkeep M_0 = M(0*mm)\nkeep R = M_0 + M_c\nnumeric(R)\n",
    )
    capsys.readouterr()

    assert "(0.00 N·m) + (490.00 N·m)" in text, text


# --- what must not move ---------------------------------------------------------------


def test_a_zero_the_sheet_wrote_bare_stays_bare(monkeypatch, capsys):
    text = page(monkeypatch, "n = 0\nnumeric(n)\n")
    capsys.readouterr()

    assert text.rstrip().endswith(r"\displaystyle 0.00 \endarray"), text


def test_a_zero_of_a_dimensionless_function_stays_bare(monkeypatch, capsys):
    text = page(monkeypatch, "L := 6*m\nf(x) = x/L - 1\nf_L = f(L)\nnumeric(f_L)\n")
    capsys.readouterr()

    assert text.rstrip().endswith(r"\displaystyle 0.00 \endarray"), text


def test_a_zero_whose_unit_cannot_be_found_is_still_defined(monkeypatch, capsys):
    """`q*x - x` adds a force per metre times a length to a length. The definition was
    accepted as a zero before, and asking for its unit must not be what rejects it."""
    text = page(monkeypatch, "q := 10*kN/m\nG(x) = q*x - x\ng_0 = G(0*m)\n")
    capsys.readouterr()

    assert text.rstrip().endswith(r"g_0 & = & \displaystyle 0 \endarray"), text


def test_a_value_that_is_not_zero_is_untouched(monkeypatch, capsys):
    text = page(monkeypatch, BEAM + "M_c = M(L/2)\nnumeric(M_c)\n")
    capsys.readouterr()

    assert text.rstrip().endswith("45.00 kN·m \\endarray"), text


def test_a_redefined_name_forgets_the_zero(monkeypatch, capsys):
    """The unit belongs to one definition. `M_B = 0` afterwards is a bare zero."""
    text = page(monkeypatch, BEAM + "M_B = M(L)\nM_B = 0\nnumeric(M_B)\n")
    capsys.readouterr()

    assert text.rstrip().endswith(r"\displaystyle 0.00 \endarray"), text

    text = page(monkeypatch, BEAM + "M_B = M(L)\nM_B := 0\nnumeric(M_B)\n")
    capsys.readouterr()

    assert text.rstrip().endswith(r"\displaystyle 0.00 \endarray"), text

    # Not a zero any more, and without a unit of its own: nothing may stand in for it.
    text = page(monkeypatch, BEAM + "M_B = M(L)\nM_B = 2\nnumeric(M_B)\n")
    capsys.readouterr()

    assert text.rstrip().endswith(r"\displaystyle 2.00 \endarray"), text
