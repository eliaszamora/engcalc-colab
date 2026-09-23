r"""A unit written alone as a term of a sum is a quantity of one of it.

    k(x) = 1*kN + 4*kN*x/m
    numeric(k(x0))            numeric evaluation failed: 'Unit' object has no attribute
                              '_get_non_multiplicative_units'

`1*kN` reaches the numeric layer as the unit `kN` on its own - the `1` folds away - and a
unit is not a quantity: Pint multiplies one by a quantity and refuses to add one to it. So
a sum whose first term was a bare unit failed in `numeric`, `table` and `plot` with Pint's
own words, while `1*kN + 4*kN`, which folds to `5 kN` before anything is evaluated, never
did. Found on 2026-09-23 tracing why `extrema` over a piecewise in kilonewtons dropped the
end of its domain: the end was evaluated through this sum.
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


LAW = "k(x) = 1*kN + 4*kN*x/m\n"


@pytest.mark.parametrize(("x0", "value"), [("0*m", "1.00"), ("1*m", "5.00"), ("500*mm", "3.00")])
def test_a_law_with_a_unit_alone_is_evaluated(magics, capsys, x0, value):
    page = run(magics, f"x0 := {x0}\n" + LAW + "numeric(k(x0))\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert page.rstrip().endswith(rf"\displaystyle {value}\,\mathrm{{kN}} \end{{array}}"), page


def test_the_unit_alone_can_be_the_second_term_too(magics, capsys):
    page = run(magics, "x0 := 1*m\nk(x) = 4*kN*x/m - 1*kN\nnumeric(k(x0))\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert page.rstrip().endswith(r"\displaystyle 3.00\,\mathrm{kN} \end{array}"), page


def test_a_table_of_it(magics, capsys):
    """`plot` fails on the same law for a reason of its own - see
    test_a_plot_reads_a_unit_written_in_its_function."""
    page = run(magics, "L := 2*m\n" + LAW + "table(k(x), x, 0, L, 3)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert "9.00" in page, page  # k(2 m) = 1 + 8 kN


def test_two_units_alone_that_do_not_add_are_still_refused(magics, capsys):
    """A metre and a kilonewton, each alone: the coercion must not make them addable."""
    run(magics, "x0 := 1*m\nk(x) = 1*kN + 1*m*x/m\nnumeric(k(x0))\n")
    printed = capsys.readouterr().out
    assert "engcalc: line 3: incompatible units" in printed, printed
