r"""What the follow-up audit of the chapter 10 fixes found (2026-10-06).

A range bound read from an entry of a matrix of numbers was said in base units,
`solve found no root for x between 222411.08 m·kg/s² and 889644.32 m·kg/s²`: said now in the
other bound's unit, or as the page would show it.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str) -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), out.getvalue()

    return run


def test_a_lower_bound_from_an_entry_is_said_in_its_unit(sheet):
    _, printed = sheet("f := [100[kip]; 50[kip]]\nx := solve(eq(x, 300[kip]), x, f[2], 200[kip])\n")
    assert "50.00 kip" in printed and "200.00 kip" in printed and "kg" not in printed, printed


def test_an_upper_bound_from_an_entry_beside_a_plain_zero(sheet):
    _, printed = sheet("f := [100[kip]; 50[kip]]\nx := solve(eq(x, 300[kip]), x, 0, f[1])\n")
    # The matrix holds its entries in base units and the page shows f in kN: so is the bound.
    assert "444.82 kN" in printed and "kg" not in printed, printed


def test_a_bound_typed_in_metres_stays_in_metres(sheet):
    _, printed = sheet("x := solve(eq(x, 3[m]), x, 0.2[m], 1.5[m])\n")
    assert "0.20 m" in printed and "1.50 m" in printed, printed
    _, printed = sheet("x := solve(eq(x, 3[m]), x, 200[mm], 1.5[m])\n")
    assert "200.00 mm" in printed and "1.50 m" in printed, printed
