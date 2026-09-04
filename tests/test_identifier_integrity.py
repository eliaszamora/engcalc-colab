r"""The memoria must print every letter the engineer typed.

An external trial of a reinforced-concrete beam - someone handed the repository link,
installing the package and working an ACI example - found that `Mu` printed as `M`. The
arithmetic was right and the page said a different variable. In a memoria that is worse
than an ugly unit, because a reviewer has no way to notice it.

Two separate causes, found by tracing rather than assuming:

`Mu` never reached EngCalc's own rule at all. SymPy's `translate` maps the capital Greek
names with no distinct glyph - Mu, Nu, Rho, Tau, Chi, Eta, Beta, Zeta - onto the Latin
letter they look like, and returns `\mathrm{M}`. EngCalc's guard trusted any rendering
that began with a backslash, reading it as "SymPy recognised this name", so it stood
aside. It had recognised it, and thrown three characters away.

`As_prov` is EngCalc's own. The uprighting rule handed SymPy a name containing braces,
and `LatexPrinter._split_super_sub` returns early on those: `if '{' in name: return
(name, [], [])`. So the subscript was never split or braced, and `\mathrm{As}_prov`
subscripts only the `p`, leaving `rov` beside it.

The rule these contracts pin is deliberately narrow: the printer may not drop or
reinterpret characters of the written identifier. It is not "make `Mu` into `M_u`".
Inferring structural notation from a name is a feature with its own design, and putting
it inside a bug fix for information loss would make both harder to judge.
"""

import re

import pytest
import sympy as sp

import engcalc_colab.magic as magic
from engcalc_colab.renderer import _latex

# What a structural engineer actually types, and what it means. The Greek-capital
# collisions are first: those are the ones that were silently losing letters.
ENGINEERING_NAMES = [
    "Mu", "Nu", "Tu", "Vu", "Pu", "Rho", "Tau", "Chi", "Eta", "Beta", "Zeta",
    "Mn", "Vn", "Mr", "As", "Av", "Ag", "Ec", "Es", "fc", "fy", "fyt", "wu",
    "As_prov", "As_trial", "db_long", "db_st", "Vs_req", "phiMn", "eqFy",
    "A_s", "M_u", "V_s", "d_max", "I_z", "rebar",
]


def _letters(latex: str) -> str:
    """The letters a reader sees, with LaTeX scaffolding removed."""
    text = re.sub(r"\\mathrm|\\left|\\right|\\displaystyle", "", latex)
    return re.sub(r"[\\{}^_,. ]", "", text)


@pytest.mark.parametrize("name", ENGINEERING_NAMES)
def test_no_letter_of_a_written_name_disappears(name):
    """The one rule. Everything below is a case of it worth naming on its own."""
    printed = _latex(sp.Symbol(name))
    assert _letters(printed) == name.replace("_", ""), f"{name} printed as {printed}"


@pytest.mark.parametrize(
    "name,collapsed",
    # Every entry SymPy renders as an upright Latin letter, not just the ones an
    # engineer is likely to type. The table is fourteen long and none of them spells
    # itself back, so leaving six out would only mean six untested ways to lose a name.
    [("Mu", "M"), ("Nu", "N"), ("Rho", "P"), ("Tau", "T"), ("Chi", "X"),
     ("Eta", "H"), ("Beta", "B"), ("Zeta", "Z"), ("Alpha", "A"), ("Epsilon", "E"),
     ("Iota", "I"), ("Kappa", "K"), ("Omicron", "O"), ("Khi", "X")],
)
def test_a_capital_greek_name_is_not_collapsed_to_its_latin_lookalike(name, collapsed):
    """`Mu` is a factored moment far more often than it is the twelfth Greek letter.

    SymPy is not wrong to map it - there is no separate glyph for capital mu - but the
    result is that the identifier loses characters, and a memoria cannot afford that.
    """
    printed = _latex(sp.Symbol(name))
    assert printed != rf"\mathrm{{{collapsed}}}", f"{name} collapsed to {collapsed}"
    assert name in printed, printed


@pytest.mark.parametrize(
    "name,expected",
    [("mu", r"\mu"), ("nu", r"\nu"), ("rho", r"\rho"), ("tau", r"\tau"),
     ("theta", r"\theta"), ("phi", r"\phi"), ("Sigma", r"\Sigma"),
     ("Delta", r"\Delta"), ("Pi", r"\Pi"), ("Xi", r"\Xi"), ("Phi", r"\Phi")],
)
def test_a_genuine_greek_letter_still_prints_as_that_letter(name, expected):
    """The fix must not cost the Greek that works.

    These spell themselves back, which is exactly what separates them from the eight
    above: `\\Sigma` reads "Sigma", `\\mathrm{M}` does not read "Mu".
    """
    assert _latex(sp.Symbol(name)) == expected


def test_a_multi_letter_base_keeps_its_whole_subscript():
    r"""`\mathrm{As}_prov` subscripts the `p` and leaves `rov` standing beside it.

    LaTeX takes one token after `_`. SymPy would have braced this itself, but only for
    a name it was allowed to split, and a name carrying `\mathrm{...}` is not one.
    """
    assert _latex(sp.Symbol("As_prov")) == r"\mathrm{As}_{prov}"
    assert _latex(sp.Symbol("db_st")) == r"\mathrm{db}_{st}"


def test_a_multi_letter_base_keeps_its_whole_superscript():
    """`__` is SymPy's superscript, and EngCalc's grammar lets a name carry one.

    Same defect as the subscript, same cause, and reachable from a cell: `As__1 :=
    500*mm**2` prints through this branch.
    """
    assert _latex(sp.Symbol("As__1")) == r"\mathrm{As}^{1}"
    assert _latex(sp.Symbol("As__1_prov")) == r"\mathrm{As}^{1}_{prov}"


def test_the_multi_letter_uprighting_still_holds():
    """The rule this fix sits inside is unchanged: a label is upright, a quantity italic."""
    assert _latex(sp.Symbol("eqFy")) == r"\mathrm{eqFy}"
    assert _latex(sp.Symbol("phiMn")) == r"\mathrm{phiMn}"


def test_single_letter_names_are_untouched():
    """Italic for a quantity, and SymPy's own bracing where it already worked."""
    assert _latex(sp.Symbol("A_s")) == "A_{s}"
    assert _latex(sp.Symbol("d_max")) == "d_{max}"
    assert _latex(sp.Symbol("x")) == "x"


def test_a_name_ending_in_a_sympy_modifier_is_not_reinterpreted():
    """`rebar` ends in `bar`, and SymPy's modifier table turns that into an overbar.

    No letter is lost, so a rule counting letters would allow it, and the page would
    show `re` with a bar over it for a variable the engineer called `rebar`.
    """
    printed = _latex(sp.Symbol("rebar"))
    assert printed == r"\mathrm{rebar}", printed


def test_the_memoria_prints_Mu_as_Mu(monkeypatch):
    """End to end, through the magic, the way the trial hit it."""
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng(
        "",
        "DL := 11.967*kN/m\nLL := 14.5939*kN/m\nL := 7.62*m\n"
        "wu = 1.2*DL + 1.6*LL\nMu = wu*L^2/8\nnumeric(Mu, kN*m)\n",
    )
    latex = "".join(getattr(obj, "data", "") for obj in captured)
    assert r"\mathrm{Mu}" in latex, latex
    assert "273.71" in latex, latex
