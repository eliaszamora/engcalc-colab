r"""The extremes of a value read from a table are found at the table's points.

    f(x) = interp(x, [0, 1, 2], [0, 1, 0])
    extrema(f(x), x, 0, 2)        characteristic numerical fallback could not validate a solution set

`interp` draws straight lines between the table's points, so its extremes sit at those
points, where the slope jumps, and a search for where the slope is zero finds nothing to
validate. The analysis already reads a function whose slope jumps: a `piecewise`, whose
extremes at its breakpoints it finds exactly. So `extrema` reads an `interp` as the
piecewise it is - one straight segment per pair of points - and the table's points become
breakpoints.

A domain that reaches outside the table is refused, as `interp` refuses a point outside
it: the piecewise would carry its end segments on in silence, and that is extrapolation.
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


def run(magics, source: str) -> str:
    magics.captured.clear()
    magics.eng("", source)
    return "".join(getattr(obj, "data", "") for obj in magics.captured)


def rows(page: str) -> list[str]:
    return [row for row in page.split(r"\\[") if r"\cdot" in row]


def test_the_peak_of_a_table_is_its_global_maximum(magics, capsys):
    page = run(magics, "f(x) = interp(x, [0, 1, 2], [0, 1, 0])\nextrema(f(x), x, 0, 2)\n")
    assert "engcalc:" not in capsys.readouterr().out
    found = rows(page)
    peak = [row for row in found if r"x = 1\," in row]
    assert peak and "global max" in peak[0] and r"\text{value} = 1\," in peak[0], found
    assert sum("global min" in row for row in found) == 2, found  # both ends, value 0


def test_a_domain_inside_the_table_ends_where_it_ends(magics, capsys):
    page = run(magics, "f(x) = interp(x, [0, 1, 2], [0, 1, 0])\nextrema(f(x), x, 0.5, 1.5)\n")
    assert "engcalc:" not in capsys.readouterr().out
    found = rows(page)
    assert any(r"x = 1\," in row and "global max" in row for row in found), found
    assert sum("global min" in row and "0.50" in row for row in found) == 2, found


def test_a_table_with_units(magics, capsys):
    page = run(
        magics,
        "L := 2*m\nk(x) = interp(x, [0*m, 1*m, 2*m], [1*kN, 5*kN, 2*kN])\nextrema(k(x), x, 0, L)\n",
    )
    assert "engcalc:" not in capsys.readouterr().out
    found = rows(page)
    assert any("1.00" in row and r"5.00\,\mathrm{kN}" in row and "global max" in row for row in found), found
    assert any(r"1.00\,\mathrm{kN}" in row and "global min" in row for row in found), found


def test_a_table_read_at_a_scaled_coordinate(magics, capsys):
    """`interp(x/2, ...)`: the table's points sit at x = 0, 2, 4. A first version rewrote only
    `interp(x, ...)` and left this one to the zero-slope search, which could not validate it;
    measured with and without that restriction, it bought nothing and cost this case."""
    page = run(magics, "f(x) = interp(x/2, [0, 1, 2], [0, 1, 0])\nextrema(f(x), x, 0, 4)\n")
    assert "engcalc:" not in capsys.readouterr().out
    found = rows(page)
    assert any(r"x = 2\," in row and "global max" in row for row in found), found


def test_a_scaled_coordinate_past_the_table_is_refused(magics, capsys):
    run(magics, "f(x) = interp(x/2, [0, 1, 2], [0, 1, 0])\nextrema(f(x), x, 0, 5)\n")
    printed = capsys.readouterr().out
    assert "engcalc: line 2: interp does not extrapolate: 2.5 lies outside its table, 0 to 2" in printed, printed


def test_a_domain_outside_the_table_is_refused(magics, capsys):
    run(magics, "f(x) = interp(x, [0, 1, 2], [0, 1, 0])\nextrema(f(x), x, 0, 3)\n")
    printed = capsys.readouterr().out
    assert "engcalc: line 2: interp does not extrapolate: 3 lies outside its table, 0 to 2" in printed, printed
