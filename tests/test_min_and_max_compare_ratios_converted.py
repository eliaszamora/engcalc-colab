r"""`min` and `max` compare a ratio of units by its value, not by the number typed.

    r = max(1[kN]/1[kip], 0.5)

drew `r = 0.22`: 1 kN/kip is 0.2248, so the maximum is 0.5. A ratio of two units of one
kind is dimensionless, and when every argument was dimensionless the group was handed back
unconverted - `1 kN/kip` compared as 1 against 0.5 and won, then printed converted. Found
by three of the four solvers of chapter 10 of his book (an adaptive step became 15276 kip).

Angles are dimensionless too and keep their unit: `min(30 deg, 0.5 rad)` is read in
degrees, the first angle written.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        with contextlib.redirect_stdout(io.StringIO()):
            magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return run


def last_value(page: str, name: str) -> str:
    row = page.split(name + r" & = & \displaystyle ", 1)[1].split(r"\end{array}", 1)[0]
    return row.split(r"\\")[-2 if row.rstrip().endswith(r"\\") else -1].split(r"\displaystyle ")[-1].strip()


def test_max_of_a_force_ratio_and_a_number(sheet):
    page = sheet("r = max(1[kN]/1[kip], 0.5)\n")
    assert last_value(page, "r") == "0.50", page


def test_max_of_a_length_ratio_and_a_number(sheet):
    # 1 m/ft is 3.28; the old comparison picked 2.
    page = sheet("r = max(1[m]/1[ft], 2)\n")
    assert "3.28" in last_value(page, "r"), page


def test_min_of_a_force_ratio_and_a_number(sheet):
    page = sheet("r = min(1[kN]/1[kip], 0.5)\n")
    assert "0.22" in last_value(page, "r"), page


def test_a_value_line_compares_converted(sheet):
    page = sheet("a := max(1[kN]/1[kip], 0.5)\n")
    assert last_value(page, "a") == "0.50", page


def test_a_ratio_read_from_names(sheet):
    page = sheet("P := 1[kN]\nQ := 1[kip]\nr := max(P/Q, 0.5)\n")
    assert last_value(page, "r") == "0.50", page


def test_angles_keep_their_unit(sheet):
    # 30 deg is 0.524 rad, more than 0.5 rad.
    page = sheet("t = max(30[deg], 0.5[rad])\n")
    value = last_value(page, "t")
    assert "30" in value and "circ" in value, page


def test_two_values_in_one_ratio_unit_are_unchanged(sheet):
    page = sheet("r = max(2[kN]/1[kip], 1[kN]/1[kip])\n")
    assert "0.45" in last_value(page, "r") or "2.00" in last_value(page, "r"), page
