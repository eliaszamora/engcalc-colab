r"""A value read from a table, by linear interpolation between the two points around it.

    C = interp(r, [0.5, 1.0, 2.0], [0.8, 1.0, 1.3])
    numeric(C)        interp((0.70), ...) = (0.80) + (0.70 - 0.50)/(1.00 - 0.50) (1.00 - 0.80)
                                          = 0.88

Codes are full of tables read this way - a coefficient against a ratio, the strength
reduction factor between two strains - and EngCalc had no way to read one. Asked for on
2026-09-23 after comparing EngCalc with Calcpad, whose `line(...)` interpolates.

`interp(x, xs, ys)`: the point, then the table as two rows written like any other matrix,
the abscissas in increasing order and the values beside them. The page shows the segment
used, worked out, because that is what a reviewer checks against the code's table: which
two rows were read, and the straight line between them. Outside the table it refuses -
a code's table is not a law to extend, and extrapolating in silence is how a sheet ends up
using a coefficient nobody tabulated.
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


TABLE = "C = interp(r, [0.5, 1.0, 2.0], [0.8, 1.0, 1.3])\n"


def test_the_table_is_written_as_it_was_given(magics, capsys):
    page = run(magics, "r := 0.7\n" + TABLE)
    assert "engcalc:" not in capsys.readouterr().out
    assert r"C & = & \displaystyle \operatorname{interp}\left(r, " in page, page
    assert r"0.5 & \displaystyle 1.0 & \displaystyle 2.0" in page, page
    assert r"0.8 & \displaystyle 1.0 & \displaystyle 1.3" in page, page


def test_the_segment_used_is_worked_out_before_the_value(magics, capsys):
    page = run(magics, "r := 0.7\n" + TABLE + "numeric(C)\n")
    assert "engcalc:" not in capsys.readouterr().out
    worked = (
        r"\left(0.80\right) + \frac{\left(0.70\right) - \left(0.50\right)}"
        r"{\left(1.00\right) - \left(0.50\right)} \left(\left(1.00\right) - \left(0.80\right)\right)"
    )
    assert worked in page, page
    assert page.rstrip().endswith(r"\displaystyle 0.88 \end{array}"), page


@pytest.mark.parametrize(
    ("r", "value"),
    [("0.5", "0.80"), ("1.0", "1.00"), ("2.0", "1.30"), ("1.5", "1.15"), ("0.51", "0.80")],
)
def test_it_reads_the_table_at_its_points_and_between_them(magics, capsys, r, value):
    """At each point the tabulated value exactly, the last one included; between two points
    the straight line. `0.51` sits one hundredth past the first point, a thin margin: the
    segment is chosen by the value and not by its neighbourhood."""
    page = run(magics, f"r := {r}\n" + TABLE + "numeric(C)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert page.rstrip().endswith(rf"\displaystyle {value} \end{{array}}"), page


def test_the_strength_reduction_factor_between_two_strains(magics, capsys):
    """ACI 318 §21.2.2: φ from 0.65 at εt = 0.002 to 0.90 at 0.005, linearly."""
    page = run(
        magics,
        "e_t := 0.003\nphi = interp(e_t, [0.002, 0.005], [0.65, 0.90])\nnumeric(phi)\n",
    )
    assert "engcalc:" not in capsys.readouterr().out
    assert page.rstrip().endswith(r"\displaystyle 0.73 \end{array}"), page


def test_a_table_with_units_reads_a_point_in_another_unit(magics, capsys):
    page = run(
        magics,
        "h := 1500*mm\nk = interp(h, [1*m, 2*m, 3*m], [10*kN, 16*kN, 20*kN])\nnumeric(k)\n",
    )
    assert "engcalc:" not in capsys.readouterr().out
    assert page.rstrip().endswith(r"\displaystyle 13.00\,\mathrm{kN} \end{array}"), page
    # Worked out in the table's unit, metres, not the point's millimetres.
    assert r"\left(1.50\,\mathrm{m}\right) - \left(1.00\,\mathrm{m}\right)" in page, page


def test_the_compact_form_shows_no_working(magics, capsys):
    page = run(magics, "r := 0.7\n" + TABLE + "result(C)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\left(0.80\right) +" not in page, page
    assert page.rstrip().endswith(r"\displaystyle 0.88 \end{array}"), page


@pytest.mark.parametrize(
    ("source", "said"),
    [
        (
            "r := 2.5\n" + TABLE + "numeric(C)\n",
            "line 3: interp does not extrapolate: 2.5 lies outside its table, 0.5 to 2",
        ),
        (
            "r := 0.4\n" + TABLE + "numeric(C)\n",
            "line 3: interp does not extrapolate: 0.4 lies outside its table, 0.5 to 2",
        ),
        (
            "C = interp(r, [0.5, 1.0], [0.8, 1.0, 1.3])\n",
            "line 1: interp needs one value for each point: 2 points, 3 values",
        ),
        ("C = interp(r, [0.5], [0.8])\n", "line 1: interp needs a table of at least 2 points"),
        (
            "r := 0.7\nC = interp(r, [1.0, 0.5, 2.0], [0.8, 1.0, 1.3])\nnumeric(C)\n",
            "line 3: interp needs its points in increasing order",
        ),
        (
            "h := 2*m\nk = interp(h, [1*kN, 3*kN], [10*kN, 20*kN])\nnumeric(k)\n",
            "line 3: interp reads its point against the table in one kind of unit",
        ),
        ("C = interp([1, 2], [0.5, 1.0], [0.8, 1.0])\n", "line 1: interp reads one point, not a matrix"),
        ("C = interp(r, 0.5, 0.8)\n", "line 1: interp reads its table as two rows, the points and the values"),
        (
            "C := interp(0.7, [0.5, 1.0], [0.8, 1.0])\n",
            "line 1: interp reads a table, which := cannot hold; define it with = and ask "
            "numeric(...) for its value",
        ),
    ],
)
def test_what_cannot_be_read_says_why(magics, capsys, source, said):
    run(magics, source)
    printed = capsys.readouterr().out
    assert f"engcalc: {said}" in printed, printed


def test_a_function_of_the_coordinate_can_be_plotted(magics, capsys):
    run(magics, "f(x) = interp(x, [0, 1, 2], [0, 1, 0])\nplot(f(x), x, 0, 2)\n")
    assert "engcalc:" not in capsys.readouterr().out


def test_the_derivative_of_a_table_stays_unevaluated(magics, capsys):
    """SymPy's chain rule differentiated the table's matrices too and recursed until Python
    stopped it, which `plot` reached first, because it differentiates to mark extrema. The
    derivative of an `interp` stays unevaluated.

    This contract first pinned that `extrema` over an `interp` answered in one line that it
    could not validate the kink of a broken line. It answers now, at the table's points
    (test_the_extremes_of_a_table_are_found), so what is left to pin is the derivative."""
    run(magics, "f(x) = interp(x, [0, 1, 2], [0, 1, 0])\ng(x) = diff(f(x), x)\n")
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed
