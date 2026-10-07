r"""The low findings of the independent audit of 0.46.1, left for 0.46.2 (2026-10-07).

- A range `solve` whose bounds are in inches failed "symbolic evaluation failed: invalid
  syntax": the root came back as `2.00 in` and `in` was read as Python's keyword. mm, ft and
  kip bounds worked; his kip/inch sheets need the inch.
- The audit of these fixes: the root's unit was read back from its symbol, so the tonne's
  `t` was the sheet's `t` - `2 ton` read `20.00 mm` beside `t := 10[mm]`, in silence - a
  sheet's `m` mass made a root in metres kilograms, and `Δ°C` was refused. It is read by
  Pint's name now, under its bracketed spelling.
- `max(2[mm/m], 0.001)` draws `0.002` and stays so: keeping mm/m there carried
  `mm·MPa/m` into `max(eps, 0.002)*E` (the audit of these fixes), which a page does not
  simplify - a strain times a modulus without `max` reads the same today.
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


def row_of(page: str, name: str) -> str:
    """The value on the row a name opens, without the rows after it."""
    return page.split(name + r" & = & \displaystyle ", 1)[1].split(r"\\", 1)[0].split(r"\end", 1)[0].strip()


def last_value(page: str, name: str) -> str:
    row = page.split(name + r" & = & \displaystyle ", 1)[1].split(r"\end{array}", 1)[0]
    return row.split(r"\\")[-2 if row.rstrip().endswith(r"\\") else -1].split(r"\displaystyle ")[-1].strip()


# -- a range solve in inches -------------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    [
        "x := solve(eq(x, 2[inch]), x, 0[inch], 10[inch])\n",
        "lo := 0[inch]\nhi := 10[inch]\nx := solve(eq(x, 2[inch]), x, lo, hi)\n",
    ],
)
def test_a_range_solve_in_inches(sheet, source):
    page, printed = sheet(source)
    assert "engcalc:" not in printed, printed
    assert last_value(page, "x") == r"2.00\,\mathrm{in}", page


def test_a_range_solve_in_inches_on_an_equals_line(sheet):
    # A root that falls exactly, 2.0, is written `2.0` on a `=` line in any unit and none -
    # a short Float reads as typed; known, not this release's.
    page, printed = sheet("x = solve(eq(x, 2[inch]), x, 0[inch], 10[inch])\n")
    assert "engcalc:" not in printed, printed
    assert last_value(page, "x").endswith(r"\,\mathrm{in}"), page


def test_a_range_solve_in_metres_says_nothing(sheet):
    # The root's unit was read back as a bare `m`, and the sheet was told it never wrote
    # the metre as a unit - beside `2[m]`.
    page, printed = sheet("x = solve(eq(x, 2[m]), x, 0[m], 10[m])\n")
    assert not printed, printed
    assert last_value(page, "x").endswith(r"\,\mathrm{m}"), page


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


# -- a root read back in its unit by name -----------------------------------------------


def test_a_root_in_tonnes_is_not_the_sheet_s_t(sheet):
    page, printed = sheet("t := 10[mm]\nx := solve(eq(x, 2[ton]), x, 0[ton], 10[ton])\ny := 2*x\n")
    assert "engcalc:" not in printed, printed
    assert row_of(page, "x") == r"2.00\,\mathrm{t}", page
    assert row_of(page, "y") == r"4.00\,\mathrm{t}", page


def test_a_root_in_tonnes_needs_no_t(sheet):
    page, printed = sheet("x := solve(eq(x, 2[ton]), x, 0[ton], 10[ton])\n")
    assert "engcalc:" not in printed, printed
    assert last_value(page, "x").startswith("2.00"), page


@pytest.mark.parametrize("name", ["m := 5[kg]", "s := 3[mm]", "N := 7[kN]"])
def test_a_root_is_not_a_name_spelled_like_its_unit(sheet, name):
    page, printed = sheet(name + "\nx := solve(eq(x, 2[m]), x, 0[m], 10[m])\n")
    assert "engcalc:" not in printed, printed
    assert last_value(page, "x") == r"2.00\,\mathrm{m}", page


def test_a_root_in_degrees_celsius(sheet):
    page, printed = sheet("x := solve(eq(x, 20[degC]), x, 0[degC], 100[degC])\n")
    assert "engcalc:" not in printed, printed
    assert last_value(page, "x").startswith("20.00"), page


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("k := 50[kip/inch]\nd := solve(eq(k*d, 100[kip]), d, 0[inch], 10[inch])\nF := k*d\n", "100.00"),
        ("x := solve(eq(x^2, 4[inch^2]), x, 0[inch], 10[inch])\nA := x^2\n", "4.00"),
        ("x := solve(eq(x, 5[kN*m]), x, 0[kN*m], 10[kN*m])\nM := 2*x\n", "10.00"),
    ],
)
def test_a_root_in_a_compound_unit_carries_on(sheet, source, expected):
    page, printed = sheet(source)
    assert "engcalc:" not in printed, printed
    name = source.rsplit("\n", 2)[-2].split(" :=")[0]
    assert last_value(page, name).startswith(expected), page


# -- max and min of ratios, as 0.46.1 left them -------------------------------------------


def test_a_strain_through_max_is_a_number_and_its_product_a_stress(sheet):
    page, printed = sheet("r := max(2[mm/m], 0.001)\nf := max(2[mm/m], 0.001)*200000[MPa]\n")
    assert not printed, printed
    assert row_of(page, "r") == "0.002", page
    assert row_of(page, "f") == r"400.00\,\mathrm{MPa}", page


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
    assert "line 3" in printed and "zz" in printed, printed
    assert "3[1]" not in printed, printed


def test_a_side_that_has_no_value_is_quoted_as_typed(sheet):
    _, printed = sheet("P := 10[kN]\n% if P > 2 + 0.5[m]:\ny := 1\n% end\n")
    assert "line 2" in printed and "2 + 0.5[m]" in printed and "__u_" not in printed, printed


def test_a_typed_compound_is_said_as_typed(sheet):
    _, printed = sheet("f := [100[kip]; 50[kip]]\n% if f[1] > 0.5[kN/m]:\ny := 1\n% end\n")
    assert "against kN/m" in printed and "kg" not in printed, printed
    _, printed = sheet("P := 5[kN]\n% if P > 10[kN/m^2]:\ny := 1\n% end\n")
    assert "against kN/m²" in printed, printed


def test_a_plain_number_is_said_as_a_number(sheet):
    _, printed = sheet("P := 5[kN]\n% if 1 < P < 3[m]:\ny := 1\n% end\n")
    assert "a number against kN" in printed, printed


def test_a_placeholder_number_with_a_placeholder_unit(sheet):
    page, printed = sheet("% u = 'kN'\n% for i in range(1, 3):\nP_{i} := {i}[{u}]\n% end\n")
    assert "engcalc:" not in printed, printed
    assert last_value(page, "P_{2}") == r"2.00\,\mathrm{kN}", page


def test_an_index_placeholder_is_still_an_index(sheet):
    page, printed = sheet("x2 := [1[kN]; 2[kN]]\n% for i in range(1, 3):\ny_{i} := x2[{i}]\n% end\n")
    assert "engcalc:" not in printed, printed
    assert row_of(page, "y_{2}").endswith(r"= 2.00\,\mathrm{kN}"), page
