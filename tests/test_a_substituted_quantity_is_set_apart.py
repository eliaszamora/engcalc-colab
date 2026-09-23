r"""A substituted value is set apart from what it multiplies, whatever name it replaced.

Found by reading the rendered beam of 0.31.4. Two substitution rows of one page, fifteen
lines apart:

    M_u  =  0.15 (18.35 kgf/cm) (600.00 cm)^2      set apart
    d    =  5(30.59 kgf/cm)(600.00 cm)^4           not

0.31.4 gave an upright name of several letters the thin space an upright unit already
had, so `qD*x` would stop reading `qDx`. The substitution row inherited that rule, and
there it answers the wrong question: `M_u`'s factors were `qD` and `L`, `d`'s were `q_s`,
`E` and `I_z`, and by the time the row is drawn **none of those names is on it**. The
reader is shown two spacings and the thing that decides between them is invisible.

What is on the row is what should decide it, and it is the same in both: a value in
brackets. `(30.59 kgf/cm)` is an upright block exactly as `qD` and `kgf` are, so it is
set apart for the same reason - and then a page spaces its substitution rows one way.

Before 0.31.4 both rows read the tight way, so this is a consistency 0.31.4 broke and
not one it inherited.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")


SHEET = """b := 30*cm
h := 60*cm
q_s := 30*kgf/cm
L := 600*cm
E := 240000*kgf/cm^2
I_z := 540000*cm^4
qD := 18*kgf/cm
"""


@pytest.fixture
def rows(monkeypatch):
    def read(source: str) -> list[str]:
        """The rows of the equation group the cell displays, as the notebook gets them."""
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", SHEET + source)
        maths = [item.data for item in captured if isinstance(item, Math)]
        assert maths, "the cell displayed no mathematics"
        body = maths[-1]
        body = body[body.index(r"{lcl}") + len(r"{lcl}") :].replace(r"\end{array}", "")
        return [row.strip() for row in body.split(r"\\[8pt]")]

    return read


@pytest.fixture
def substitution(rows):
    def read(source: str) -> str:
        """The row that carries the values: the last one before the result."""
        return rows(source)[-2]

    return read


def test_two_values_multiplied_are_set_apart(substitution):
    assert substitution("A = b*h\nnumeric(A)") == (
        r"& = & \displaystyle \left(30.00\,\mathrm{cm}\right)"
        r"\,\left(60.00\,\mathrm{cm}\right)"
    )


def test_the_deflection_row_is_spaced_like_the_moment_row(substitution):
    """The two rows of the engineer's beam that disagreed."""
    assert substitution("d = 5*q_s*L^4/(384*E*I_z)\nnumeric(d)") == (
        r"& = & \displaystyle \frac{5\,\left(30.00\,\frac{\mathrm{kgf}}{\mathrm{cm}}\right)"
        r"\,\left(600.00\,\mathrm{cm}\right)^{4}}"
        r"{384\,\left(240000.00\,\frac{\mathrm{kgf}}{\mathrm{cm}^{2}}\right)"
        r"\,\left(540000.00\,\mathrm{cm}^{4}\right)}"
    )


def test_the_moment_row_still_reads_as_it_did(substitution):
    """The row that was already right, in the release this corrects. It must not move."""
    assert substitution("M_u = 0.15*qD*L^2\nnumeric(M_u)") == (
        r"& = & \displaystyle 0.15\,\left(18.00\,\frac{\mathrm{kgf}}{\mathrm{cm}}\right)"
        r"\,\left(600.00\,\mathrm{cm}\right)^{2}"
    )


@pytest.mark.parametrize(
    "source",
    [
        "A = b*h\nnumeric(A)",
        "d = 5*q_s*L^4/(384*E*I_z)\nnumeric(d)",
        "M_u = 0.15*qD*L^2\nnumeric(M_u)",
    ],
)
def test_no_substitution_row_butts_two_values_together(substitution, source):
    """Asked of all three at once, because the defect is that they disagreed."""
    assert r"\right) \left(" not in substitution(source)
    assert r"\right)\left(" not in substitution(source)


def test_a_mode_s_value_is_set_apart_like_any_other(monkeypatch):
    """`lam[1]` is substituted by its own printer, and is the same bracketed value.

    Found by mutation: the reference pages have modal analysis but never multiply a mode
    by anything, so dropping this branch changed nothing they could see.
    """
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng(
        "",
        "k_1 := 2000*kN/m\nk_2 := 1500*kN/m\nm_1 := 600*kg\nm_2 := 500*kg\n"
        "K = [k_1 + k_2, -k_2; -k_2, k_2]\nM = [m_1, 0; 0, m_2]\n"
        "lam = eigenvals(inv(M)*K)\nnumeric(lam)\nE = 2*lam[1]\nnumeric(E)\n",
    )
    page = " ".join(item.data for item in captured if isinstance(item, Math))
    assert r"2\,\left(1333.33\,\frac{1}{\mathrm{s}^{2}}\right)" in page, page


# --- what must not move ---------------------------------------------------------------


def test_the_formula_row_is_not_touched(rows):
    """The names are still there on that row, and single letters are juxtaposed."""
    assert rows("A = b*h\nnumeric(A)")[-3].endswith(r"\displaystyle b h")
    assert rows("d = 5*q_s*L^4/(384*E*I_z)\nnumeric(d)")[-3].endswith(
        r"\displaystyle \frac{5 q_{s} L^{4}}{384 E I_{z}}"
    )


def test_a_difference_of_two_values_is_unchanged(substitution):
    """A sum is not a product; nothing here should reach it. (It read `- (4.00 cm) +
    (60.00 cm)` until a sum stopped opening with a minus - see
    test_a_sum_does_not_open_with_a_minus - and the spacing this file is about is the
    same either way.)"""
    assert substitution("cover := 4*cm\nd = h - cover\nnumeric(d)") == (
        r"& = & \displaystyle \left(60.00\,\mathrm{cm}\right) - "
        r"\left(4.00\,\mathrm{cm}\right)"
    )


def test_the_value_row_is_unchanged(rows):
    assert rows("A = b*h\nnumeric(A)")[-1].endswith(r"1800.00\,\mathrm{cm}^{2}")
