r"""A sum the sheet wrote reads in the order it was written, as a product does since 0.33.0.

Seen in his exercise 2.1 on 2026-09-25: `sin(theta + phi)` read `sin(φ + θ)`, and
`L = sqrt(6^2 + 4^2)*m` read `√(4² + 6²)`. SymPy keeps no order for a sum - it sorts the
terms the moment it reads them - so the order the engineer wrote is taken from the line,
before it is lost, and the printer puts the terms back in it.

Only a sum that reaches the page with the terms it was written with: each term is known by
the names it holds (by its value when it holds none), and a sum is put back in order only
when its terms are exactly those of a sum the sheet wrote. A sum the algebra made - an
integral, an expansion, two terms SymPy merged - keeps the order the page gave it before.
The first writing is kept, as for products: `b + a` and then `a + b` read `b + a` both
times. And a sum still does not open with a minus when it can open with a plus (0.31.17):
`-cover + h` reads `h - cover`.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def page(monkeypatch):
    def run(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        assert "engcalc:" not in console.getvalue(), console.getvalue()
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return run


def test_a_sum_inside_a_function_reads_as_written(page):
    shown = page("a := 0.5\nb := 0.9\nkeep y = sin(b + a)\nnumeric(y)\n")
    assert r"\sin{\left(b + a \right)}" in shown, shown
    # The values stand in a sum, so each keeps its brackets.
    assert r"\sin{\left(\left(0.90\right) + \left(0.50\right) \right)}" in shown, shown


def test_his_angles_read_theta_then_phi(page):
    shown = page(
        "theta := atan(4/6)\nphi := atan(4/3)\nd := 2*mm\nkeep u = d/sin(theta + phi)\nnumeric(u)\n"
    )
    assert r"\sin{\left(\theta + \phi \right)}" in shown, shown


def test_a_line_of_values_reads_its_squares_as_written(page):
    shown = page("L = sqrt(6^2 + 4^2)*m\n")
    assert r"6^{2} + 4^{2}" in shown, shown


def test_an_effective_depth_reads_as_typed(page):
    shown = page(
        "h := 500*mm\ncover := 40*mm\ndb_st := 10*mm\ndb := 20*mm\n"
        "d = h - cover - db_st - db/2\nnumeric(d)\n"
    )
    assert r"h - \mathit{cover} - \mathit{db}_{st} - \frac{\mathit{db}}{2}" in shown, shown


def test_a_sum_still_opens_with_a_plus(page):
    shown = page("h := 500*mm\ncover := 40*mm\nd = -cover + h\nnumeric(d)\n")
    assert r"d & = & \displaystyle h - \mathit{cover}" in shown, shown


def test_the_first_writing_is_kept(page):
    shown = page("a := 1*m\nb := 2*m\ny = b + a\nz = a + b\n")
    assert r"y & = & \displaystyle b + a" in shown, shown
    assert r"z & = & \displaystyle b + a" in shown, shown


def test_a_sum_the_algebra_changed_keeps_the_page_s_order(page):
    # Written `b + a + a`: two terms known by the same name, so which is which cannot be
    # told, and the sum keeps the order the page gave it before.
    shown = page("a := 1*m\nb := 2*m\ny = b + a + a\n")
    assert r"y & = & \displaystyle a + a + b" in shown, shown
