r"""A value substituted into a formula reads in the unit its own result would use.

The last of the display complaints the matrix frame analysis produced, and the one left
open by #94, #97, #99 and #100. A period is derived from a circular frequency, and the
page shows:

    w_n = sqrt(A E / (ms L))
        = ...
    T   = 2 pi / w_n
        = 2 pi / (6.61 GPa^0.5*mm/(kg^0.5*m^0.5))     <- the substitution
        = 0.0300 s                                    <- the result

Same quantity, two lines apart, in two units - and the one an engineer cannot read is the
one in the middle of the derivation they are being asked to follow. It is also where the
fractional unit exponents come from, which is the defect reported as "¿por qué las
unidades están elevadas a 0.5?".

The cause is one missing argument. `_quantity_latex` takes `declared`, which decides
whether a unit is kept as stored or handed to the family that makes it readable, and it
defaults to True; `_NumericSubstitutionLatexPrinter._print_Symbol` never passes it. So
every substituted value is treated as a unit the engineer wrote down, including the ones
the algebra invented.

What the answer needs is per name, not per page, and the engine already computes it:
`written_unit_names` separates `q := 2.8*tonf/m`, where a unit was written, from
`phiMn := 0.9*As*fy*z`, where the units arrived from three stored values. It was computed
per assignment and thrown away; the engine keeps the set now.

The half that must not move is `d := 0.0105*m`. Handed to the family it becomes
`10.50 mm`, which is a better number and the wrong one: the engineer wrote metres.
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


OSCILLATOR = (
    "E := 210*GPa\n"
    "A := 625*mm**2\n"
    "L := 6*m\n"
    "ms_ := 500*kg\n"
    "keep k = E*A/L\n"
    "w = sqrt(k/ms_)\n"
    "keep w_n = w\n"
)


# --- the defect -------------------------------------------------------------------

def test_a_computed_value_substitutes_in_the_unit_its_result_uses(cell):
    """`w_n` is 209.17 1/s wherever it appears, including inside the next formula."""
    latex = cell(OSCILLATOR + "T = 2*pi/w_n\nnumeric(T)\n")
    assert "209.17" in latex, latex
    assert "GPa" not in latex.split("T")[-1], latex


def test_no_fractional_unit_exponent_reaches_the_page(cell):
    """The reported symptom: `GPa^{0.5}` and `kg^{0.5}` in the middle of a derivation.
    They exist only because a substituted value kept the unit the square root left."""
    latex = cell(OSCILLATOR + "T = 2*pi/w_n\nnumeric(T)\n")
    assert "^{0.5}" not in latex, latex


def test_the_result_row_is_unchanged(cell):
    """The final row was always right, and this must not disturb it."""
    latex = cell(OSCILLATOR + "T = 2*pi/w_n\nnumeric(T)\n")
    assert "0.0300" in latex, latex
    assert r"\mathrm{s}" in latex, latex


# --- the half that must not move ---------------------------------------------------

def test_a_declared_unit_survives_into_the_substitution(cell):
    """`d := 0.0105*m` is metres because the engineer wrote metres. The family would
    make it `10.50 mm`, which is the better number and the wrong one - this is the
    single case in the whole sheet where `declared` changes the answer, so it is the
    reason the engine has to keep the set at all rather than passing False everywhere.
    """
    latex = cell("d := 0.0105*m\nF := 10*kN\nM = F*d\nnumeric(M)\n")
    assert "0.0105" in latex, latex
    assert "10.50" not in latex, latex


def test_the_engineers_own_unit_survives_into_the_substitution(cell):
    """`tonf/m` is not in any family and is kept by the term weighting rather than by
    `declared`, so it should read the same either way. Asserted because "should" is not
    a measurement."""
    latex = cell("q := 2.8*tonf/m\nL := 6*m\nW = q*L\nnumeric(W)\n")
    assert r"\mathrm{tonf}" in latex, latex
    assert "2.80" in latex, latex


def test_an_ordinary_sheet_is_untouched(cell):
    """Every value here is already in the unit its family would choose, so nothing in
    the substitution row may move."""
    latex = cell(
        "q := 10*kN/m\nL := 6*m\nM = q*L**2/8\nnumeric(M)\n"
    )
    assert "10.00" in latex and "6.00" in latex, latex
    assert "45.00" in latex, latex


def test_a_redefinition_without_a_unit_stops_protecting_the_name(cell):
    """Both of the set's edges were left uncontracted until mutation said so.

    `d := 0.0105*m` protects `d`. `d := 2*d` writes no unit - the metres came from a
    stored value - so the protection has to go with it, or a name stays declared on the
    strength of a line the engineer has since replaced. `0.021 m` then reads `21.00 mm`,
    which is the family answering as it should.
    """
    latex = cell("d := 0.0105*m\nd := 2*d\nF := 10*kN\nM = F*d\nnumeric(M)\n")
    assert "21.00" in latex, latex
    assert r"\mathrm{mm}" in latex, latex
    assert "0.021" not in latex, latex


def test_a_reset_clears_the_declared_names(monkeypatch):
    """The other edge. `%eng_reset` clears the namespace, and a set of names that
    outlived it would protect units belonging to a sheet that no longer exists."""
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    magics.eng("", "d := 0.0105*m\n")
    assert "d" in magics.engine.declared_unit_names

    magics.eng_reset("")
    assert magics.engine.declared_unit_names == set()


def test_a_declared_unit_that_was_never_written_is_still_made_readable(cell):
    """The distinction the engine draws. `phiMn := 0.9*As*fy*z` declares a name and no
    unit - the units came from three stored values - so there is nothing to keep and
    the family answers, in the substitution exactly as in the result."""
    latex = cell(
        "As := 1935*mm**2\nfy := 420*MPa\nz := 400*mm\n"
        "phiMn := 0.9*As*fy*z\nn = 2*phiMn\nnumeric(n)\n"
    )
    assert r"\mathrm{kN} \cdot \mathrm{m}" in latex, latex
    assert "MPa" not in latex.split("n")[-1] or "292" in latex, latex
