r"""The low findings of the independent audit of 0.46.1, left for 0.46.2 (2026-10-07).

- A range `solve` whose bounds are in inches failed "symbolic evaluation failed: invalid
  syntax": the root came back as `2.00 in` and `in` was read as Python's keyword. mm, ft and
  kip bounds worked; his kip/inch sheets need the inch.
- `max(2[mm/m], 0.001)` drew `0.002` (main before 0.46.1, `2.00 mm/m`): a ratio whose
  scale is a power of ten, a strain in mm/m, keeps its unit when every argument is that
  ratio or a plain number. `1 kN/kip` is not such a ratio and stays a number,
  `max(1[kN]/1[kip], 0.5) = 0.50` (0.46.1).
- Two refusals quoted internals: `% if f[1] > 0.5[m]` over kip entries said
  `0.5 * __u_m: m·kg/s² against m`, and `% if P > 3[{u}]` was refused before it ran,
  quoting the stand-in `3[1]` - a placeholder inside a unit's brackets is a unit.
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


def last_value(page: str, name: str) -> str:
    row = page.split(name + r" & = & \displaystyle ", 1)[1].split(r"\end{array}", 1)[0]
    return row.split(r"\\")[-2 if row.rstrip().endswith(r"\\") else -1].split(r"\displaystyle ")[-1].strip()


# -- a range solve in inches -------------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    [
        "x := solve(eq(x, 2[inch]), x, 0[inch], 10[inch])\n",
        "lo := 0[inch]\nhi := 10[inch]\nx := solve(eq(x, 2[inch]), x, lo, hi)\n",
        "x = solve(eq(x, 2[inch]), x, 0[inch], 10[inch])\n",
    ],
)
def test_a_range_solve_in_inches(sheet, source):
    page, printed = sheet(source)
    assert "engcalc:" not in printed, printed
    assert last_value(page, "x") == r"2.00\,\mathrm{in}", page


def test_a_range_solve_in_inches_over_a_kip_inch_equation(sheet):
    page, printed = sheet(
        "k := 50[kip/inch]\nP := 120[kip]\nd := solve(eq(k*d, P), d, 0[inch], 10[inch])\n"
    )
    assert "engcalc:" not in printed, printed
    assert last_value(page, "d") == r"2.40\,\mathrm{in}", page


def test_a_range_solve_in_feet_is_as_it_was(sheet):
    page, printed = sheet("x := solve(eq(x, 2[ft]), x, 0[ft], 10[ft])\n")
    assert "engcalc:" not in printed, printed
    assert last_value(page, "x") == r"2.00\,\mathrm{ft}", page


# -- a strain in mm/m through max and min ------------------------------------------------


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("r := max(2[mm/m], 0.001)\n", "2.00"),
        ("r = max(2[mm/m], 0.001)\n", "2.00"),
        ("r := max(0.5[mm/m], 0.001)\n", "1.00"),  # 0.001 is 1 mm/m; main read 0.5 as larger
        ("r := min(2[mm/m], 0.001)\n", "1.00"),
        ("r := max(0.001, 2[mm/m])\n", "2.00"),
        ("r := max(2[mm/m], 3[mm/m])\n", "3.00"),
    ],
)
def test_a_strain_keeps_its_unit(sheet, source, expected):
    page, printed = sheet(source)
    assert not printed, printed
    value = last_value(page, "r")
    assert value.startswith(expected) and r"\mathrm{mm}" in value and r"\mathrm{m}" in value, page


def test_a_strain_beside_another_scale_is_read_in_the_first(sheet):
    # 1 cm/m is 10 mm/m.
    page, printed = sheet("r := max(2[mm/m], 1[cm/m])\n")
    assert not printed, printed
    value = last_value(page, "r")
    assert value.startswith("10.00") and r"\mathrm{mm}" in value, page


def test_a_force_ratio_stays_a_number(sheet):
    page, _ = sheet("r := max(1[kN]/1[kip], 0.5)\n")
    assert last_value(page, "r") == "0.50", page


# -- refusals said as the sheet writes them -----------------------------------------------


def test_a_condition_of_two_kinds_is_quoted_as_typed(sheet):
    _, printed = sheet("f := [100[kip]; 50[kip]]\n% if f[1] > 0.5[m]:\ny := 1\n% end\n")
    assert "line 2" in printed and "f[1] > 0.5[m]" in printed, printed
    assert "__u_" not in printed and "kg" not in printed, printed


def test_a_condition_of_two_kinds_over_scalars(sheet):
    _, printed = sheet("P := 10[kN]\n% if P > 0.5[m] and P > 1[kN]:\ny := 1\n% end\n")
    assert "P > 0.5[m]" in printed, printed
    assert "__u_" not in printed and "kg" not in printed, printed


def test_a_placeholder_names_the_unit_of_a_condition(sheet):
    page, printed = sheet("P := 5[kN]\n% u = 'kN'\n% if P > 3[{u}]:\ny := 1\n% end\n")
    assert "engcalc:" not in printed, printed
    assert last_value(page, "y") == "1.00", page


def test_a_placeholder_names_the_unit_of_a_line(sheet):
    page, printed = sheet("% u = 'kN'\nP := 3[{u}]\n")
    assert "engcalc:" not in printed, printed
    assert last_value(page, "P") == r"3.00\,\mathrm{kN}", page


def test_a_placeholder_unit_that_is_none_is_said_as_typed(sheet):
    _, printed = sheet("P := 5[kN]\n% u = 'zz'\n% if P > 3[{u}]:\ny := 1\n% end\n")
    assert "engcalc:" in printed and "zz" in printed, printed
    assert "3[1]" not in printed, printed
