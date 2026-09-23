r"""A sum does not open with a minus when it can open with a plus.

    L_c = sqrt((- x_1 + x_2)^2 + (- y_1 + y_2)^2)      what the frame page wrote
    d   = - cover - db/2 - db_st + h                   an effective depth, backwards
    M(x) = - P <- a + x>^1 + P x (L - a)/L             a Macaulay bracket, inside out

A sum reached the page in SymPy's canonical order, which sorts its terms by name and so
opens with whichever term is alphabetically first, sign and all. The engineer writes
`x_2 - x_1`, `h - cover - ...`, `<x - a>`. Asked, he said it bothers him (2026-09-22).

Four rules were measured on the thirteen reference sheets and the eighteen gap-map
exercises before this one was chosen. On those they agree - 44 rows move, 42 on the frame
pages and two in the exercises, every one for the better - and they part on the shapes
below:

- *the first positive term leads* breaks an expanded polynomial: `- qL³x/24 + qLx³/12 -
  qx⁴/24` became `qLx³/12 - qL³x/24 - qx⁴/24`, powers 3, 1, 4;
- *positive terms first* does the same, and moves four more rows for no gain;
- *read it backwards when that opens with a plus* never breaks a polynomial, but writes the
  effective depth `h - db_st - db/2 - cover` and leaves `- a + b - c` alone.

So the rule has two halves. A sum ordered by the powers of a name - some name appears in
two of its terms with different exponents - is read the other way round when that makes
it open with a plus; reversing keeps its powers in order, only in the other direction. Any
other sum lets its first positive term lead, and the rest keep the order they had. A sum
that already opens with a plus, and one with no positive term at all, are left alone.

The order is decided once, in `_ordered_sum_terms`, and used by the printer and by both
paths that lay a sum out term by term - the definition and its substitution row used to
come from different places, and a rule in one would have made them disagree.

What it does not do: keep the order the engineer typed. The terms after the first keep
SymPy's order, so `h - cover - db_st - db/2` reads `h - cover - db/2 - db_st`. The written
order does not survive the algebra that builds most rows, and a rule that pretended it did
would be right only for the rows that were never combined.
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


FRAME = "x_1 := 0*cm\nx_2 := 500*cm\ny_1 := 0*cm\ny_2 := 370*cm\n"
DEPTH = "h := 500*mm\ncover := 40*mm\ndb_st := 10*mm\ndb := 20*mm\n"


# --- what bothered him -------------------------------------------------------------

def test_a_difference_of_coordinates_reads_the_way_it_is_written(cell, capsys):
    page = cell(FRAME + "L_c = sqrt((x_2 - x_1)**2 + (y_2 - y_1)**2)\nnumeric(L_c)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\left(x_{2} - x_{1}\right)^{2} + \left(y_{2} - y_{1}\right)^{2}" in page, page
    assert (
        r"\left(\left(500.00\,\mathrm{cm}\right) - \left(0.00\,\mathrm{cm}\right)\right)^{2}"
        in page
    ), page


def test_an_effective_depth_and_its_substitution_open_with_the_height(cell, capsys):
    """Two paths drew this row pair, so the rule had to live where both could reach it."""
    page = cell(DEPTH + "d = h - cover - db_st - db/2\nnumeric(d)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"d & = & \displaystyle h - \mathrm{cover} - " in page, page
    assert (
        r"& = & \displaystyle \left(500.00\,\mathrm{mm}\right) - \left(40.00\,\mathrm{mm}\right) - "
        in page
    ), page


def test_a_macaulay_bracket_reads_x_minus_a(cell, capsys):
    page = cell("L := 8*m\nP := 40*kN\na := 3*m\nR_A = P*(L-a)/L\nM(x) = R_A*x - P*<x-a>^1\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"x - a \right\rangle" in page, page
    assert r"- a + x" not in page, page


def test_a_bracket_in_a_product_opens_with_its_plus(cell, capsys):
    page = cell(
        DEPTH + "fc := 25*MPa\nfy := 420*MPa\nAs := 1935*mm**2\nb := 300*mm\nphi := 0.9\n"
        "keep d = h - cover - db_st - db/2\nkeep a = As*fy/(0.85*fc*b)\n"
        "phiMn = phi*As*fy*(d - a/2)\nnumeric(phiMn)\n"
    )
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\left(d - \frac{a}{2}\right)" in page, page


# --- the two halves of the rule ----------------------------------------------------

def test_a_polynomial_keeps_its_powers_in_order(cell, capsys):
    """The counterexample that ruled out the simplest rule: powers 1, 3, 4 stay in order,
    and since reading it backwards would still open with a minus, it is left as it is."""
    page = cell("q := 10*kN/m\nL := 6*m\ny(x) = -q*x**4/24 + q*L*x**3/12 - q*L**3*x/24\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert (
        r"- \frac{q L^{3} x}{24} + \frac{q L x^{3}}{12} - \frac{q x^{4}}{24}" in page
    ), page


def test_a_polynomial_read_backwards_when_that_opens_with_a_plus(cell, capsys):
    page = cell("L := 6*m\nf(x) = x**3 - L**2*x\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"x^{3} - L^{2} x" in page, page


def test_a_sum_that_is_no_polynomial_lets_its_first_plus_lead(cell, capsys):
    """Reading it backwards would leave this one opening with a minus."""
    page = cell("s = -a + b - c\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"s & = & \displaystyle b - a - c" in page, page


# --- what is left alone ------------------------------------------------------------

def test_a_sum_with_no_plus_is_left_alone(cell, capsys):
    page = cell("s = -a - b\n")
    assert r"s & = & \displaystyle - a - b" in page, page


def test_a_sum_that_already_opens_with_a_plus_is_left_alone(cell, capsys):
    page = cell("q := 10*kN/m\nR_A := 30*kN\nV(x) = R_A - q*x\nM(x) = R_A*x - q*x**2/2\n")
    assert r"R_{A} - q x" in page, page
    assert r"R_{A} x - \frac{q x^{2}}{2}" in page, page
