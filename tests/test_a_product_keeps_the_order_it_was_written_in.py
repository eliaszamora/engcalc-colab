r"""A product is written in the order the sheet wrote it.

    N_b = E*A*(u_2 - u_1)/L        read    A E (u_2 - u_1) / L

SymPy keeps no order for a product: `E*A` is stored as `A*E` the moment it is read, and
the page ordered the factors again by a rule of its own - numbers, lowercase names,
capitals, and among the capitals what carries mass first, else the alphabet. With `E` and
`A` still symbols the alphabet decided, and the engineer's `EA` read `AE`. He asked on
2026-09-23, reading his matrix derivation, for the order he wrote to be kept.

The engine now records, for every product the sheet writes, which name was written before
which, and the printer puts names in that order. A product the sheet never wrote as such -
the entries of `transpose(T)*k*T`, a value that came out of a substitution - takes the
order its names were first written in together, so `f_1 = -N_b` reads `E A` like the line
that defined `N_b`. Two names never written together keep the rule they had. Numbers stay
first, units keep the page's order, and the first writing is the one the sheet keeps: a
page that writes `E*A` and later `A*E` reads `E A` in both, rather than a row that
changes with what was typed after it.
"""

import pytest

from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def page(monkeypatch, capsys):
    engine = magic.EngMagics()

    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        engine.eng("", source)
        assert "engcalc:" not in capsys.readouterr().out
        return " ".join(item.data for item in captured if isinstance(item, Math))

    render.engine = engine
    return render


@pytest.mark.parametrize(
    ("source", "written", "sorted_"),
    [
        # The row he asked about.
        ("N_b = E*A*(u_2 - u_1)/L\n", r"\frac{E A \left(u_{2} - u_{1}\right)}{L}", r"A E"),
        # The alphabet and the written order disagree the other way.
        ("k = I*E/L\n", r"\frac{I E}{L}", r"\frac{E I}{L}"),
        # A lowercase name written after a capital.
        ("M = L^2*q/8\n", r"\frac{L^{2} q}{8}", r"\frac{q L^{2}}{8}"),
        # ACI's order, which the shape rule turned round.
        ("T = A_s*f_y\n", r"A_{s} f_{y}", r"f_{y} A_{s}"),
    ],
)
def test_a_written_product_keeps_its_order(page, source, written, sorted_):
    shown = page(source)
    assert written in shown, shown
    assert sorted_ not in shown, shown


def test_a_number_stays_in_front(page):
    shown = page("y = E*A*2\n")
    assert r"2 E A" in shown, shown


def test_a_denominator_keeps_its_order_too(page):
    shown = page("d = 5*q*L^4/(384*I*E)\n")
    assert r"\frac{5 q L^{4}}{384 I E}" in shown, shown


def test_a_value_derived_from_it_reads_the_same(page):
    """`f_1 = -N_b` never wrote `E*A`; it reads the order `N_b` was written in."""
    shown = page("N_b = E*A*(u_2 - u_1)/L\nf_1 = -N_b\n")
    assert r"- \frac{E A \left(u_{2} - u_{1}\right)}{L}" in shown, shown
    assert r"A E" not in shown, shown


def test_a_matrix_built_from_it_reads_the_same(page):
    """The stiffness of an inclined bar: no entry was written, every one reads `E A`."""
    shown = page(
        "k = [E*A/L, -E*A/L; -E*A/L, E*A/L]\n"
        "T = [c, s; -s, c]\n"
        "K = transpose(T)*k*T\n"
    )
    assert r"A E" not in shown, shown
    assert r"E A" in shown, shown


def test_the_first_writing_is_the_one_the_page_keeps(page):
    shown = page("a = E*A\nb = A*E\n")
    assert r"A E" not in shown, shown


def test_the_order_carries_into_the_next_cell(page):
    page("N_b = E*A*(u_2 - u_1)/L\n")
    shown = page("f = 2*N_b\n")
    assert r"E A" in shown and r"A E" not in shown, shown


def test_a_reset_forgets_it(page):
    page("a = I*E\n")
    page.engine.engine.reset()
    shown = page("b = E*I\nc = I*E/L\n")
    assert r"\frac{E I}{L}" in shown, shown


def test_the_substituted_row_follows_the_written_one(page):
    """Both rows of one block, in one order."""
    shown = page("A := 500*mm^2\nE := 200*GPa\nL := 4*m\nk = A*E/L\nnumeric(k)\n")
    assert r"\frac{A E}{L}" in shown, shown
    first_a = shown.index(r"\left(500")
    first_e = shown.index(r"\left(200")
    assert first_a < first_e, shown


def test_a_product_split_across_rows_keeps_its_order():
    """Too wide for one row, a product is split at its factors - in the written order,
    the numerator and the denominator each in their own."""
    import ast
    import re

    import sympy as sp

    from engcalc_colab.engine import record_written_order
    from engcalc_colab.renderer import WRITTEN_ORDER, _bounded_expression_rows

    top = [f"n_{index:02d}" for index in range(16, 0, -1)]
    bottom = [f"d_{index:02d}" for index in range(16, 0, -1)]
    written: dict = {}
    record_written_order(
        ast.parse(f"{'*'.join(top)}/({'*'.join(bottom)})", mode="eval"), written
    )
    expression = sp.Mul(*map(sp.Symbol, top)) / sp.Mul(*map(sp.Symbol, bottom))

    token = WRITTEN_ORDER.set(written)
    try:
        rows = " ".join(_bounded_expression_rows(expression))
    finally:
        WRITTEN_ORDER.reset(token)

    assert re.findall(r"n_\{(\d+)\}", rows) == [name[2:] for name in top], rows
    assert re.findall(r"d_\{(\d+)\}", rows) == [name[2:] for name in bottom], rows


def test_a_product_never_written_together_keeps_its_rule(page):
    """Nothing the sheet wrote says where `E` goes against `A`; the old rule answers."""
    shown = page("a = E*x\nc = a*A\n")
    assert r"A E x" in shown, shown
