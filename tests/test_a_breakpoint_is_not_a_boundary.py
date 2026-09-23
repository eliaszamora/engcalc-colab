r"""A breakpoint is called a breakpoint, not a boundary.

    f(x) = interp(x, [0, 1, 2], [0, 1, 0])
    extrema(f(x), x, 0, 2)

    x = 1 (1.00) · value = 1 (1.00) · boundary, local max, global max

x = 1 is inside the domain, 0 to 2: it is where the table's straight line turns. Every
point the piecewise analysis found at a place where the law changes was labelled
`boundary`, the word the page uses for the ends of the domain, so a reviewer reading the
block was told the peak sat at an end. Seen by him on his own Colab page on 2026-09-23,
the day `extrema` learned to read tables; it was already so for every `piecewise`.

A point where the law changes is a `breakpoint`, the word the README uses for a
piecewise's; the ends of the domain stay `boundary`.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def magics(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    engine = magic.EngMagics()
    engine.captured = captured
    return engine


def run(magics, source: str) -> list[str]:
    magics.captured.clear()
    magics.eng("", source)
    page = "".join(getattr(obj, "data", "") for obj in magics.captured)
    return [row for row in page.split(r"\\[") if r"\cdot" in row]


def at(rows: list[str], x: str) -> list[str]:
    return [row for row in rows if rf"x = {x}\," in row]


def test_the_peak_of_a_table_is_at_a_breakpoint(magics, capsys):
    rows = run(magics, "f(x) = interp(x, [0, 1, 2], [0, 1, 0])\nextrema(f(x), x, 0, 2)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert at(rows, "1") and r"\text{breakpoint, local max, global max}" in at(rows, "1")[0], rows
    assert "boundary" not in at(rows, "1")[0], rows


def test_the_ends_of_the_domain_are_still_its_boundary(magics, capsys):
    rows = run(magics, "f(x) = interp(x, [0, 1, 2], [0, 1, 0])\nextrema(f(x), x, 0, 2)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\text{boundary, global min}" in at(rows, "0")[0], rows
    assert r"\text{boundary, global min}" in at(rows, "2")[0], rows


def test_a_jump_is_read_at_its_breakpoint_from_both_sides(magics, capsys):
    """A discontinuous law: the two one-sided limits and the value at the point are all
    at the breakpoint, and none of them is at an end of the domain."""
    rows = run(magics, "f(x) = piecewise(x, x < 2, 10 - x)\nextrema(f(x), x, 0, 4)\n")
    assert "engcalc:" not in capsys.readouterr().out
    found = at(rows, "2")
    assert len(found) >= 2 and all("breakpoint" in row and "boundary" not in row for row in found), found


def test_a_piecewise_in_units_has_its_breakpoint_where_its_law_changes(magics, capsys):
    rows = run(
        magics,
        "L := 2*m\nb := 1*m\n"
        "k(x) = piecewise(1*kN + 4*kN*x/m, x <= b, 5*kN - 3*kN*(x - b)/m)\n"
        "extrema(k(x), x, 0, L)\n",
    )
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\text{breakpoint, local max, global max}" in at(rows, "b")[0], rows
    assert r"\text{boundary, global min}" in at(rows, "0")[0], rows


def test_a_law_that_changes_where_the_domain_begins_is_at_its_boundary(magics, capsys):
    """`piecewise(5, x <= 0, x)` on [0, 2]: the law changes at x = 0, which is also where the
    domain begins. The limit from the right is read there, and for the reader it is the
    start of the domain - so a point on a domain end stays `boundary` even when the law
    changes on it."""
    rows = run(magics, "f(x) = piecewise(5, x <= 0, x)\nextrema(f(x), x, 0, 2)\n")
    assert "engcalc:" not in capsys.readouterr().out
    right = [row for row in at(rows, "0") if r"\text{right}" in row]
    assert right and r"\text{boundary}" in right[0] and "breakpoint" not in right[0], rows
