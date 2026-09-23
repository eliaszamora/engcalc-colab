r"""Among the capitals, what carries mass is written first: `E A`, not `A E`.

The engineer types `E*A_c/L_c` in `tools/portico.eng` and the page draws `A_c E / L_c`.
He asked for `EA`, which is how it is written everywhere: *"quiero que sea EA ya que
convencionalmente así se usa"*.

`_engineering_factor_key` sorts a commutative product into numbers, then names beginning
with a lowercase letter, then names beginning with a capital, then the names the sheet has
no value for. **Inside each of those groups the order was alphabetical**, which is SymPy's
canonical order leaking onto the page: `A` before `E` for no reason a reader could name.
Among the capitals that order carries no information at all, so this replaces it with one
that does.

    among the capitals, a name whose value carries mass goes before one that does not

`E` is a pressure and `A_c` an area, so `E A_c`. `E I`, already right by the alphabet,
stays right for a reason now.

**Why "among the capitals" and not everywhere.** The same rule applied to a whole product
was tried in 0.31.13 and rejected twice over, and the counterexamples are pinned in
`test_a_load_is_written_before_a_length`:

- it splits `E I`, because a dimensionless direction cosine `s_c` sits between them and the
  modulus jumps it - `12 s^{2} E I` becomes `12 E I s^{2}`;
- it writes `fy As` as `As fy`... in the wrong direction: `fy` is a stress and `As` an
  area, so a global rule moves `fy` first, and ACI writes `As fy`.

Both of those pair a *lowercase* name with a capital, and the shape groups already keep
them apart. Confining the rule to the capitals is what leaves them alone: this file's rule
never compares a lowercase name with anything.

`As fy` and `E A` are the same two dimensions in opposite orders. No dimensional rule gets
both right, and none is attempted: what settles `As fy` is the shape of the names, which
is where the engineer's own habit already lives.

Measured across the thirteen sheets: **39 rows move, all three of them on the frame pages,
and every one is a permutation of the same line** - checked character by character - with
the modulus or the area it jumped as the only thing that moved. Nothing else on any page
moves at all.

This rule needs the settings to reach the printer, which for a matrix cell they did not
until the commit before this one. Without it the frame page would correct three rows and
leave ten contradicting them.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")

FRAME = "E := 210*GPa\nA_c := 1350*cm^2\nL_c := 3.7*m\n"


@pytest.fixture
def page(monkeypatch):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def last_body(written: str) -> str:
    rows = written.split(r"\\[8pt]")
    return rows[-1].split("& = &")[-1].replace(r"\end{array}", "").strip()


def test_an_axial_rigidity_is_written_modulus_first(page):
    """The row he typed: `E*A_c/L_c`."""
    written = page(FRAME + "k = E*A_c/L_c\n")

    assert last_body(written) == (
        r"\displaystyle \frac{E A_{c}}{L_{c}}"
    ), last_body(written)


def test_it_reaches_a_matrix_cell(page):
    """Where he actually writes it: `tools/portico.eng` builds `k_c` as a matrix."""
    written = page(FRAME + "k_c = [ E*A_c/L_c, 0; 0, E*A_c/L_c ]\n")

    assert r"\frac{E A_{c}}{L_{c}}" in written, written
    assert r"\frac{A_{c} E}{L_{c}}" not in written, written


def test_the_substituted_row_follows_it_too(page):
    """Or the block contradicts itself, one row to the next."""
    written = page(FRAME + "k = E*A_c/L_c\nnumeric(k)\n")

    assert (
        r"\left(210.00\,\mathrm{GPa}\right)\,\left(1350.00\,\mathrm{cm}^{2}\right)"
        in written
    ), written


def test_a_load_goes_before_a_length(page):
    """The same rule, on the other pair of capitals it reaches: `P L`, not `L P`."""
    written = page("P := 40*kN\nL := 6*m\nM = P*L\n")

    assert last_body(written) == r"\displaystyle P L", last_body(written)


# --- what must not move ---------------------------------------------------------------


def test_a_flexural_rigidity_is_still_not_split(page):
    """`12 s^{2} E I`: the cosine is lowercase, so this rule never looks at it."""
    written = page(
        "s := 0.5\nI := 2280*cm**4\nE := 210*GPa\nL := 4*m\nk = 12*s**2*E*I/L**3\n"
    )

    assert r"\frac{12 s^{2} E I}{L^{3}}" in last_body(written), last_body(written)


def test_a_tension_capacity_is_untouched(page):
    r"""`As fy` - the idiom a dimensional rule gets backwards - is not reordered by it.

    `fy` is a stress and `As` an area, the same two dimensions as `E A_c` in the opposite
    order. This rule cannot reach it: `fy` begins with a lowercase letter and is in a
    group of its own. It read `fy As` by the shape rule until 0.33.0, which writes a
    product in the order the sheet wrote it; see
    `test_a_product_keeps_the_order_it_was_written_in`.
    """
    written = page("As := 1935*mm**2\nfy := 420*MPa\nT = As*fy\n")

    assert last_body(written) == (
        r"\displaystyle \mathrm{As}\,\mathrm{fy}"
    ), last_body(written)


def test_two_capitals_that_carry_no_mass_keep_the_alphabet(page):
    """Neither is a modulus, so there is nothing to say and the old order stands."""
    written = page("A_c := 1350*cm**2\nI_c := 2280*cm**4\nr = A_c*I_c\n")

    assert last_body(written) == (
        r"\displaystyle A_{c} I_{c}"
    ), last_body(written)


def test_a_capital_unit_literal_is_not_a_modulus(page):
    """`N` has no value on the sheet, so it carries no mass and does not lead."""
    written = page("A_c := 1350*cm**2\nF = 3*N*A_c\n")

    assert last_body(written) == (
        r"\displaystyle 3 A_{c}\,\mathrm{N}"
    ), last_body(written)


def test_the_coordinate_still_goes_last(page):
    """0.31.13's rule, which this one sits inside and must not disturb."""
    written = page("P := 40*kN\nM(x) = P*x/2\n")

    assert last_body(written) == r"\displaystyle \frac{P x}{2}", last_body(written)


def test_a_sheet_with_no_values_is_unchanged(page):
    written = page("R(q) = 3*q*L/8\n")

    assert r"\frac{3 q L}{8}" in last_body(written), last_body(written)


def test_a_deflection_is_unchanged(page):
    written = page(
        "q := 10*kN/m\nL := 6*m\nE := 200*GPa\nI := 8e6*mm**4\n"
        "d = 5*q*L**4/(384*E*I)\n"
    )

    assert last_body(written) == (
        r"\displaystyle \frac{5 q L^{4}}{384 E I}"
    ), last_body(written)


def test_a_reaction_is_unchanged(page):
    written = page("q := 10*kN/m\nL := 6*m\nR = q*L/2\n")

    assert last_body(written) == r"\displaystyle \frac{q L}{2}", last_body(written)
