r"""A plot reads a unit written in its function.

    q := 10*kN/m
    L := 3*m
    V(x) = 30*kN - q*x
    plot(V(x), x, 0, L)        symbolic evaluation failed: 'kN'

To decide where a piecewise changes branch, `plot` evaluates every name in the function at
each of its points, and it looked each one up among the sheet's values. `kN` is not a value:
it is a unit written in the function, which every other evaluation resolves as a unit
(`unit_literal_overrides`). So a shear law with a constant written in kilonewtons could be
evaluated, tabulated and solved, and not drawn - the whole figure lost to a KeyError. Found
on 2026-09-23 on `main`, beside the unit-alone-in-a-sum defect it resembles and is not.
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


def run(magics, source: str) -> list:
    magics.captured.clear()
    magics.eng("", source)
    return list(magics.captured)


SHEET = "q := 10*kN/m\nL := 3*m\nV(x) = 30*kN - q*x\n"


@pytest.mark.parametrize(
    "call",
    [
        "plot(V(x), x, 0, L)",
        "envelope(V(x), -V(x), x, 0, L)",
        "plot(V(x), x, 0, L, q=[5*kN/m, 10*kN/m])",
    ],
)
def test_a_function_with_a_unit_written_in_it_is_drawn(magics, capsys, call):
    shown = run(magics, SHEET + call + "\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert any(type(obj).__name__ not in {"Math", "HTML", "Latex"} for obj in shown), shown


def test_a_piecewise_with_a_unit_in_its_breakpoint_is_still_drawn(magics, capsys):
    """The same lookup also reads the conditions: `x <= 1*m` needs the metre."""
    run(magics, "k(x) = piecewise(5*kN, x <= 1*m, 2*kN)\nplot(k(x), x, 0, 2*m)\n")
    assert "engcalc:" not in capsys.readouterr().out
