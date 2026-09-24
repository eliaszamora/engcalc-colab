r"""A name kept with `keep` stays itself through `subs`, `expand`, `simplify` and `factor`.

    keep a = E*A/L
    K0 = subs(K, c, 1)          read   [EA/L, 0; 0, EA/L]     where K was [a c, 0; 0, a]
    y  = simplify(a*c + a*c)    read   2 c E A / L

`keep` makes a name stand for itself on the page - the formula an engineer checks against
a code or a textbook reads in the names he chose. The formula as written is rebuilt with
those names standing, and shown only when it verifies against the value computed beside
it. That rebuild was allowed only for plain arithmetic and a few calls with no effects,
and these four were not among them, so a derivation that passed through one of them lost
every kept name at once: in his matrix derivation `K_b0 = subs(K_b, c_theta, 1, s_theta,
0)` and the column `K_c` read in `E A / L` and `12 E I / L^3` where every matrix around
them read in `a` and `b_1 ... b_4`. He chose to have them keep the names on 2026-09-24.

None of the four has an effect a second reading would repeat, and the verification is
what keeps the short form honest: `subs(K_b, ..., L, L_1)` replaces the `L` inside `a`,
so `a` is no longer what the entry is, the check fails, and the entry reads `E A / L_1`.
"""

import contextlib
import io

import pytest

from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def page(monkeypatch):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        assert "engcalc:" not in console.getvalue(), console.getvalue()
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def last_row(shown: str) -> str:
    return shown[shown.rindex(r"& = &"):]


KEEP = "keep a = E*A/L\n"


@pytest.mark.parametrize(
    ("source", "kept", "expanded"),
    [
        ("K = [a*c, 0; 0, a]\nK0 = subs(K, c, 1)\n", r"\displaystyle a & \displaystyle 0", r"\frac{E A}{L}"),
        ("z = a*c\nz0 = subs(z, c, 2)\n", r"2 a", r"\frac{2 E A}{L}"),
        ("x = expand(a*(c + 1))\n", r"a c + a", r"\frac{c E A}{L}"),
        ("y = simplify(a*c + a*c)\n", r"2 a c", r"\frac{2 c E A}{L}"),
        ("w = factor(a*c + a)\n", r"a \left(c + 1\right)", r"\frac{E A \left(c + 1\right)}{L}"),
    ],
)
def test_a_kept_name_stays_itself(page, source, kept, expanded):
    shown = last_row(page(KEEP + source))
    assert kept in shown, shown
    assert expanded not in shown, shown


def test_a_substitution_inside_the_kept_name_does_not_show_it(page):
    """`a` is `EA/L`; after `L` becomes `L_1` the entry is `EA/L_1`, and `a` would be false."""
    shown = last_row(page(KEEP + "K = [a*c, 0; 0, a]\nK1 = subs(K, c, 1, L, L_1)\n"))
    assert r"\frac{E A}{L_{1}}" in shown, shown
    assert r"\displaystyle a & \displaystyle 0" not in shown, shown


def test_the_value_is_the_same_either_way(page):
    """The page changes; what the sheet computes with does not."""
    shown = page(
        KEEP + "E := 200*GPa\nA := 500*mm^2\nL := 4*m\n"
        "y = simplify(a*c + a*c)\nc := 2\nnumeric(y)\n"
    )
    assert shown.rstrip().endswith(r"100000.00\,\frac{\mathrm{kN}}{\mathrm{m}} \end{array}"), shown


def test_the_columns_of_the_derivation_keep_a_and_b(page):
    """The case he saw: `K_c` in `a` and `b_1 ... b_4`, as the matrices above it."""
    shown = page(
        KEEP
        + "keep b_1 = 12*E*I/L^3\nkeep b_2 = 6*E*I/L^2\nkeep b_3 = 4*E*I/L\nkeep b_4 = 2*E*I/L\n"
        "k_f = [a, 0, 0; 0, b_1, b_2; 0, b_2, b_3]\n"
        "T = [c, s, 0; -s, c, 0; 0, 0, 1]\n"
        "K = transpose(T)*k_f*T\n"
        "K_c = subs(K, c, 0, s, 1)\n"
    )
    row = last_row(shown)
    assert r"b_{1}" in row and r"\frac{12 E I}{L^{3}}" not in row, row
