r"""A root at midspan is written `L/2`, as the extrema block writes the same point.

A beam's shear, from its load cases with their factors:

    V(x) = 1.2 qD (L/2 − x) + 1.6 qL (L/2 − x)
    roots(V(x), x, 0, L)          x = 0.5L (3.00 m) · root
    extrema(M(x), x, 0, L)        x = L/2  (3.00 m) · local max

One point of one beam, written two ways a block apart. Found while checking 0.31.2.

**Why.** `roots` hands the response to `solveset` as written, and a factor of `1.2` makes
SymPy solve in floating point: `0.5 L`. 0.30.11 met the same thing in `extrema`, whose
analysis works on a simplified copy where the common factor stands apart, so its midspan
has read `L/2` since then. `roots` and `intersections` solve the response as written.

**So the solver takes the common factors out first** - `factor_terms`, which turns the sum
into `(L/2 − x)(1.2 qD + 1.6 qL)` - and `solveset` meets `L/2 − x` on its own. It is the
cheap half of a simplification: a thousandth of a second on a four-storey frequency
equation where `simplify` takes a seventh. A root the response does not share across its
terms is found as before.
"""

import engcalc_colab.magic as magic

from conftest import block_text


def page(monkeypatch, source: str) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", source)
    return block_text("".join(str(getattr(obj, "data", "")) for obj in captured))


BEAM = "L := 6*m\nqD := 18*kN/m\nqL := 10*kN/m\n"


def test_the_shear_of_a_factored_combination(monkeypatch, capsys):
    text = page(
        monkeypatch,
        BEAM + "V(x) = 1.2*qD*(L/2 - x) + 1.6*qL*(L/2 - x)\nroots(V(x), x, 0, L)\n",
    )
    capsys.readouterr()

    assert "x = L/2 (3.00 m)" in text, text
    assert "0.5 L" not in text and "0.5L" not in text, text


def test_a_combination_of_load_cases(monkeypatch, capsys):
    text = page(
        monkeypatch,
        BEAM
        + "V_D(x) = qD*(L/2 - x)\nV_L(x) = qL*(L/2 - x)\n"
        + "case D = V_D(x)\ncase Lv = V_L(x)\ncombo U = 1.2*D + 1.6*Lv\n"
        + "roots(U(x), x, 0, L)\n",
    )
    capsys.readouterr()

    assert "x = L/2 (3.00 m)" in text, text


# --- what must not move ---------------------------------------------------------------


def test_where_two_factored_responses_cross(monkeypatch, capsys):
    """Already `L/2`: their difference simplifies on its own before it is solved."""
    text = page(
        monkeypatch,
        BEAM
        + "V_1(x) = 1.2*qD*(L/2 - x)\nV_2(x) = 0.8*qD*(L/2 - x)\n"
        + "intersections(V_1(x), V_2(x), x, 0, L)\n",
    )
    capsys.readouterr()

    assert "x = L/2 (3.00 m)" in text, text


def test_a_root_with_no_common_factor(monkeypatch, capsys):
    text = page(monkeypatch, "f(x) = 1.2*x - 3.6\nroots(f(x), x, 0, 10)\n")
    capsys.readouterr()

    assert "3.00" in text and "root" in text, text


def test_a_cubic_keeps_its_closed_form(monkeypatch, capsys):
    text = page(monkeypatch, "f(x) = x^3 - 2*x - 5\nroots(f(x), x, 0, 3)\n")
    capsys.readouterr()

    assert "sqrt" in text or "√" in text or "1929" in text, text
    assert "2.09" in text, text
