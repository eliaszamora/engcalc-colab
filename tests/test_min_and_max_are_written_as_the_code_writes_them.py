r"""`min` and `max`, written in the order the code writes them.

    b_eff = min(L/4, b_w + 16*h_f, s)       the flange a T-beam may count on
    numeric(b_eff)                           min(2.00 m, 2.22 m, 3.00 m) = 2.00 m

A design code is full of them - the effective flange, the minimum steel, the smaller of
two spacings - and EngCalc had neither: `min(...)` was an unsupported function. Asked for
on 2026-09-23 after comparing EngCalc with Calcpad, which has both.

SymPy has `Min` and `Max`, and they reorder their arguments: `min(L/4, b_w + 16*h_f, s)`
prints `min(L/4, s, b_w + 16 h_f)`. Right, and not the formula in the code - a reviewer
reading the page against ACI finds the three limits in another order. `max` and `min` are
SymPy's own, with every argument where it was typed; nothing else about them changes, so a
derivative, a substitution or an integral treats them as SymPy does.
"""

import pytest
import sympy as sp

import engcalc_colab.magic as magic
from engcalc_colab.min_max import WrittenMax, WrittenMin


@pytest.fixture
def magics(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    engine = magic.EngMagics()
    engine.captured = captured
    return engine


def run(magics, source: str) -> str:
    magics.captured.clear()
    magics.eng("", source)
    return "".join(getattr(obj, "data", "") for obj in magics.captured)


FLANGE = "L := 8*m\nb_w := 300*mm\nh_f := 120*mm\ns := 3*m\nb_eff = min(L/4, b_w + 16*h_f, s)\n"


def test_the_limits_stay_in_the_order_the_code_gives_them(magics, capsys):
    page = run(magics, FLANGE)
    assert "engcalc:" not in capsys.readouterr().out
    assert r"b_{eff} & = & \displaystyle \min\left(\frac{L}{4}, b_{w} + 16 h_{f}, s\right)" in page, page


def test_the_substitution_keeps_that_order_and_the_smallest_wins(magics, capsys):
    page = run(magics, FLANGE + "numeric(b_eff)\n")
    assert "engcalc:" not in capsys.readouterr().out
    row = page.split(r"\min\left(")[2]  # the formula is [1], the substitution [2]
    # 8 m / 4, then 300 mm + 16 * 120 mm, then 3 m: the order written, each value where
    # its formula was.
    assert row.index("8.00") < row.index("300.00") < row.index("3.00"), page
    assert r"\displaystyle 2.00\,\mathrm{m}" in page, page


def test_each_limit_is_worked_out_before_the_smallest_is_taken(magics, capsys):
    """The row a reviewer checks: every limit as a value, in the order written, so the one
    that governs can be read off the page rather than recomputed from the substitution."""
    page = run(magics, FLANGE + "numeric(b_eff)\n")
    assert "engcalc:" not in capsys.readouterr().out
    compared = (
        # Inside the parentheses of `min` a value takes no brackets of its own; see
        # test_a_value_in_a_function_is_bracketed_once.
        r"\min\left(2.00\,\mathrm{m}, 2.22\,\mathrm{m}, 3.00\,\mathrm{m}\right)"
    )
    assert compared in page, page
    rows = page.split(r"\\[")
    stages = [row for row in rows if r"\min\left(" in row]
    assert len(stages) == 3, stages  # formula, substitution, the limits worked out
    assert rows.index(stages[-1]) < max(i for i, row in enumerate(rows) if r"2.00\,\mathrm{m} \end" in row or row.rstrip().endswith(r"2.00\,\mathrm{m}"))


def test_a_limit_already_a_value_is_not_worked_out_twice(magics, capsys):
    """`max(V_B, V_A)` substitutes into two values; a row of the same two values again would
    be the substitution printed twice."""
    page = run(magics, "V_A := 30*kN\nV_B := 45*kN\nV_max = max(V_B, V_A)\nnumeric(V_max)\n")
    assert page.count(r"\max\left(45.00\,\mathrm{kN}, 30.00\,\mathrm{kN}\right)") == 1, page


def test_the_compact_form_shows_no_working(magics, capsys):
    """`result` is formula and value, nothing between: the limits are working."""
    page = run(magics, FLANGE + "result(b_eff)\n")
    assert r"\left(2.22\,\mathrm{m}\right)" not in page, page


def test_max_takes_the_largest_in_the_order_written(magics, capsys):
    page = run(magics, "V_A := 30*kN\nV_B := 45*kN\nV_max = max(V_B, V_A)\nnumeric(V_max)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\max\left(V_{B}, V_{A}\right)" in page, page
    assert r"\displaystyle 45.00\,\mathrm{kN}" in page, page


def test_a_value_can_be_the_larger_of_two_directly(magics, capsys):
    """`:=` takes them too: `s_max := min(3*h, 450*mm)` is how a spacing limit is set."""
    page = run(magics, "h := 200*mm\ns_max := min(3*h, 450*mm)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"s_{max} & = & \displaystyle 450.00\,\mathrm{mm}" in page, page


def test_the_larger_of_two_near_values_is_the_larger(magics, capsys):
    """A thin margin, so the contract is decided by the comparison and not by the example:
    2.000 m against 1999 mm, one millimetre apart and written in two units."""
    page = run(magics, "a := 2*m\nb := 1999*mm\nc = max(b, a)\nnumeric(c)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\displaystyle 2.00\,\mathrm{m}" in page or r"\displaystyle 2000.00\,\mathrm{mm}" in page, page


@pytest.mark.parametrize(
    ("source", "said"),
    [
        ("L := 8*m\nV := 3*kN\nc = max(L, V)\nnumeric(c)\n", "line 4: max compares values of one kind; its arguments have incompatible units"),
        ("L := 8*m\nV := 3*kN\nc := min(L, V)\n", "line 3: min compares values of one kind; its arguments have incompatible units"),
        ("a = max(3)\n", "line 1: max expects at least 2 arguments: the values to compare"),
        ("A = [1, 2; 3, 4]\nc = min(A, 1)\n", "line 2: min compares scalar values, not a matrix"),
    ],
)
def test_what_cannot_be_compared_says_why(magics, capsys, source, said):
    run(magics, source)
    printed = capsys.readouterr().out
    assert f"engcalc: {said}" in printed, printed


def test_a_function_of_the_coordinate_can_be_plotted(magics, capsys):
    run(magics, "L := 6*m\nq := 10*kN/m\nM(x) = max(q*x*(L - x)/2, q*L^2/16)\nplot(M(x), x, 0, L)\n")
    assert "engcalc:" not in capsys.readouterr().out


def test_they_are_still_sympys_min_and_max():
    """Everything SymPy does with them it still does; only the order of the arguments is
    the reader's. A subclass built naively gets `max(3, 5) = 3`, because `Max` asks
    `cls is Max` internally - pinned here with every combination of order and sign."""
    b, a, x = sp.symbols("b a x")
    p = sp.Symbol("p", positive=True)
    assert WrittenMax(3, 5) == 5 and WrittenMax(5, 3) == 5
    assert WrittenMin(3, 5) == 3 and WrittenMin(5, 3) == 3
    assert WrittenMax(p, 0) == p and WrittenMin(p, 0) == 0
    assert WrittenMax(b, a).args == (b, a) and WrittenMin(b, a).args == (b, a)
    assert WrittenMax(b, a).subs({a: 1, b: 2}) == 2
    assert WrittenMax(b, a, x).subs(b, 2).args == (2, a, x)
    assert sp.integrate(WrittenMin(x, 1 - x), (x, 0, 1)) == sp.Rational(1, 4)
    assert WrittenMax(b, a).diff(b) == sp.Max(a, b).diff(b)
    assert isinstance(WrittenMax(b, a), sp.Max) and isinstance(WrittenMin(b, a), sp.Min)
