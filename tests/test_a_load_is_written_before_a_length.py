r"""A name the sheet has no value for is written after the ones it has.

The engineer wrote `piecewise(P*x/2, ...)` and read `xP/2` on his own beam, two lines
above `P(L - x)/2` - the same `P` before its companion in one branch and after it in the
next. He said it bothers him and chose this rule with every row it moves in front of him.

`_engineering_factor_key` ordered a commutative product by the *shape of the name*:
numbers, then names beginning with a lowercase letter, then names beginning with an
uppercase one. That gets `q L / 2`, `q L^{2} / 8` and `5 q L^{4} / (384 E I)` right by
correlation - loads are usually written lowercase and geometry uppercase - and `P` is the
load that breaks the correlation.

**Three rules were tried and measured before this one. Each had a counterexample, and two
of them were found by contracts already in this repository.**

- *The function's parameter goes last.* Fixes `P*x/2` and ruins `R_B(q) = 3 q L / 8`,
  where the parameter is the load. `test_symbolic_mathjax_wrapping` caught it.
- *What carries mass goes first.* Fixes both and splits `E I`, because a dimensionless
  direction cosine sat between them and the modulus jumped it.
- *Coefficients, then what carries mass.* Keeps `E I` together and writes `fy As` where
  ACI writes `As fy`. `test_a_written_coefficient_survives` caught it. There is no
  dimensional rule that gets `E A` and `As fy` both right, because those are idiom and
  they disagree with each other.

So this rule does not touch a product between two names the sheet has settled. `As fy`,
`E A`, `E I`, `q L` are left exactly as they are. What moves is the one name the sheet
knows nothing about - on these pages, the coordinate:

    numbers, the names with values, the names without, then everything else

Two names without values keep the shape order between them, or `3 q L / 8` comes out
`3 L q / 8` again. And a unit literal is not a coordinate: `m` has no value either, and
sending it to the end tore the metre off its number, `3 q L m / 2` where the engineer had
substituted `3 m`.

Measured across the reference pages: nine rows move on the five the repository pins -
eight `x P` to `P x`, two of those being substitution rows, and one `q x L` to `q L x` -
and a tenth in the wider thirteen-sheet diff a release is read against, where `2 x² L`
becomes `2 L x²` in a deflection. That last one restores the order the sheet wrote.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")


@pytest.fixture
def page(monkeypatch):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def last_body(written: str) -> str:
    rows = written.split("\\\\[8pt]")
    return rows[-1].split("& = &")[-1].replace(r"\end{array}", "").strip()


def test_a_load_goes_before_the_coordinate_it_multiplies(page):
    """The row he read: `P*x/2` is written `P x`, not `x P`."""
    written = page("P := 40*kN\nM(x) = P*x/2\n")

    assert last_body(written) == r"\displaystyle \frac{P x}{2}", last_body(written)


def test_a_piecewise_branch_follows_the_same_rule(page):
    """His own beam, where the complaint started."""
    written = page(
        "L := 6*m\nP := 40*kN\n"
        "M_P(x) = piecewise(P*x/2, x <= L/2, P*(L - x)/2, x <= L, 0*kN*m)\n"
    )

    assert r"\dfrac{P x}{2}" in written, written
    assert r"\dfrac{x P}{2}" not in written, written


def test_the_substituted_row_follows_it_too(page):
    """Both rows of one block, or the block contradicts itself again."""
    written = page(
        "L := 6*m\nP := 40*kN\n"
        "M_P(x) = piecewise(P*x/2, x <= L/2, P*(L - x)/2, x <= L, 0*kN*m)\n"
        "numeric(M_P(x))\n"
    )

    assert r"\dfrac{\left(40.00\,\mathrm{kN}\right)\,x}{2}" in written, written


def test_the_coordinate_goes_after_every_name_with_a_value(page):
    """A product the sheet did not write reads `q L x`: the quantities together, the
    coordinate last.

    Until 0.33.0 this was `M(x) = q*x*L/2` read `q L x / 2`. A product the sheet writes is
    now written in its order, so that line reads `q x L`; the rule here still answers for
    what the sheet never wrote side by side - here `L` and `x`. See
    `test_a_product_keeps_the_order_it_was_written_in`.
    """
    written = page("q := 10*kN/m\nL := 6*m\nw(x) = q*x\nM(x) = w(x)*L/2\n")

    assert last_body(written) == r"\displaystyle \frac{q L x}{2}", last_body(written)


def test_a_written_coordinate_stays_where_it_was_written(page):
    written = page("q := 10*kN/m\nL := 6*m\nM(x) = q*x*L/2\n")

    assert last_body(written) == r"\displaystyle \frac{q x L}{2}", last_body(written)


# --- what must not move ---------------------------------------------------------------


def test_a_product_of_two_settled_names_is_untouched(page):
    r"""Whatever the shape rule makes of it, this rule leaves it alone.

    The renderer wrote `fy As`, because `fy` begins lowercase and `As` uppercase, where
    ACI writes `As fy`. That was left as a separate decision, and 0.33.0 made it: a product
    is written in the order the sheet wrote it, so `As*fy` reads `As fy`. See
    `test_a_product_keeps_the_order_it_was_written_in`.
    """
    written = page("As := 1935*mm**2\nfy := 420*MPa\nT = As*fy\n")

    assert last_body(written) == (
        r"\displaystyle \mathrm{As}\,\mathrm{fy}"
    ), last_body(written)


def test_a_flexural_rigidity_is_not_split(page):
    """`E I` stays together. Sorting by dimension put the cosine between them."""
    written = page(
        "s := 0.5\nI := 2280*cm**4\nE := 210*GPa\nL := 4*m\nk = 12*s**2*E*I/L**3\n"
    )

    assert r"\frac{12 s^{2} E I}{L^{3}}" in last_body(written), last_body(written)


def test_a_reaction_is_unchanged(page):
    written = page("q := 10*kN/m\nL := 6*m\nR = q*L/2\n")

    assert last_body(written) == r"\displaystyle \frac{q L}{2}", last_body(written)


def test_a_span_moment_is_unchanged(page):
    written = page("q := 10*kN/m\nL := 6*m\nM = q*L**2/8\n")

    assert last_body(written) == r"\displaystyle \frac{q L^{2}}{8}", last_body(written)


def test_a_deflection_is_unchanged(page):
    written = page(
        "q := 10*kN/m\nL := 6*m\nE := 200*GPa\nI := 8e6*mm**4\n"
        "d = 5*q*L**4/(384*E*I)\n"
    )

    assert last_body(written) == (
        r"\displaystyle \frac{5 q L^{4}}{384 E I}"
    ), last_body(written)


def test_a_distributed_moment_is_unchanged(page):
    written = page("qD := 18*kN/m\nL := 6*m\nM_D(x) = qD*x*(L - x)/2\n")

    assert last_body(written) == (
        r"\displaystyle \frac{\mathrm{qD}\,x \left(L - x\right)}{2}"
    ), last_body(written)


@pytest.mark.parametrize(
    "sheet",
    [
        "R(q) = 3*q*L/8\n",
        # With a value on the sheet as well, so the coordinate group is actually entered
        # rather than skipped by the "told us nothing" shortcut. Found by mutation:
        # ordering two coordinates alphabetically changed nothing the first sheet could
        # see, because on it no name reaches that group at all.
        "P := 40*kN\nR(q) = 3*q*L/8\n",
    ],
)
def test_names_the_sheet_never_valued_keep_their_order(sheet, page):
    """`3 q L / 8` was the counterexample that killed the first rule tried here."""
    written = page(sheet)

    assert r"\frac{3 q L}{8}" in last_body(written), last_body(written)


def test_a_unit_stays_beside_the_number_it_belongs_to(page):
    """A unit has no value either, and is not a coordinate.

    `subs(M(x), x, 3*m)` substitutes `3 m`, and sending every valueless name to the end
    read `3 q L m / 2`. See `test_a_substituted_metre_is_upright`.
    """
    written = page(
        "L := 6*m\nq := 10*kN/m\nM(x) = q*x*L/2\nnumeric(subs(M(x), x, 3*m))\n"
    )

    assert r"3\,\mathrm{m}\,q L" in written, written
