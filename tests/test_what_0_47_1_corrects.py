r"""Presentation left open by 0.46.2 and 0.47.0 (his "aborda todo lo que falte", 2026-10-09).

- A compound unit typed in brackets on a `=` line read in the alphabet's order:
  `2.5[kip*ft]` printed `2.5 ft·kip`, `2.5[kip*inch]` `2.5 in·kip`. The page's unit order
  (`_page_unit_order`) asked Pint for `__u_ft`, the name a bracketed unit is read under,
  failed, and left SymPy's order; `kN·m` was right by the alphabet alone.
- A range `solve` on a `=` line whose root falls exactly wrote `2.0`: a short float reads
  as typed, and a root is no typed number.
- `2[mm/m]*200000[MPa]` read `400000.00 mm·MPa/m`: units of one kind that cancel out are
  cancelled before the unit is chosen.
- From the inventory of open findings (2026-10-09): `(x[1]/y)^2` lost its parentheses,
  `solve(K, -2*F)` read as a subtraction, `A^2` of an area was bracketed twice, `x/0.85` in
  a function read `1.18 x`, a `table` of an expression and a matrix refusal showed `__u_`.
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


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("2.5[kip*ft]", r"\mathrm{kip} \cdot \mathrm{ft}"),
        ("2.5[kip*inch]", r"\mathrm{kip} \cdot \mathrm{in}"),
        ("2.5[N*m]", r"\mathrm{N} \cdot \mathrm{m}"),
        ("2.5[kN*m]", r"\mathrm{kN} \cdot \mathrm{m}"),
        ("2.5[kgf*cm]", r"\mathrm{kgf} \cdot \mathrm{cm}"),
    ],
)
def test_a_bracketed_moment_reads_force_first(sheet, typed, expected):
    page, printed = sheet(f"M = {typed}\n")
    assert not printed, printed
    assert expected in page, page


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("x = solve(eq(x, 2[ft]), x, 0[ft], 10[ft])\n", r"2.00\,\mathrm{ft}"),
        ("x = solve(eq(x, 2), x, 0, 10)\n", "2.00"),
        ("x = solve(eq(x, 2.5[m]), x, 0[m], 10[m])\n", r"2.50\,\mathrm{m}"),
    ],
)
def test_an_exact_root_reads_at_the_page_s_precision(sheet, source, expected):
    page, printed = sheet(source)
    assert not printed, printed
    assert last_value(page, "x") == expected, page


def test_a_typed_short_number_still_reads_as_typed(sheet):
    page, _ = sheet("b := 30[cm]\na = 0.9*b\n")
    assert r"0.9 b" in page.replace("\\,", " ") or "0.9 b" in page, page


# -- refusals said as the sheet writes them (the third audit of 0.46.2) -------------------


def test_a_name_read_from_kip_entries_is_said_in_the_page_s_unit(sheet):
    _, printed = sheet("f := [100[kip]; 50[kip]]\nF := f[1]\n% if F > 0.5[m]:\ny := 1\n% end\n")
    assert "F > 0.5[m]: kN against m" in printed and "kg" not in printed, printed


def test_a_name_with_a_written_unit_is_said_as_written(sheet):
    _, printed = sheet("rho := 2400[kg/m^3]\n% if rho > 5[kN]:\na := 1\n% end\n")
    assert "kg/m³ against kN" in printed, printed


def test_a_fractional_power_is_quoted_whole(sheet):
    _, printed = sheet("x := 1[kN]\n% if x > 3[m^0.5]:\ny := 1\n% end\n")
    assert "x > 3[m^0.5]" in printed, printed


def test_a_product_with_a_bracketed_number_is_quoted_as_typed(sheet):
    _, printed = sheet("x := 1[kN]\n% if x > 2*3[m]:\ny := 1\n% end\n")
    assert "x > 2 * 3[m]" in printed, printed


@pytest.mark.parametrize(
    ("source", "name", "expected"),
    [
        ("r := 2[mm/m]*200000[MPa]\n", "r", r"400.00\,\mathrm{MPa}"),
        ("fs := min(3[mm/m]*200000[MPa], 420[MPa])\n", r"\mathit{fs}", r"420.00\,\mathrm{MPa}"),
        ("V = 3[kN/m]*2[cm]\n", "V", r"\mathrm{N}"),
    ],
)
def test_a_strain_times_a_modulus_reads_as_a_stress(sheet, source, name, expected):
    page, printed = sheet(source)
    assert not printed, printed
    value = last_value(page, name)
    assert expected in value and r"\mathrm{m}}" not in value and "000.00" not in value, page


def test_a_typed_strain_keeps_its_mm_per_m(sheet):
    page, printed = sheet("eps := 2[mm/m]\n")
    assert not printed, printed
    assert r"\mathrm{mm}" in page, page


def test_a_power_of_a_fraction_keeps_its_parentheses(sheet):
    page, printed = sheet("x := [3[kN]; 4[kN]]\ny := 2[kN]\np := (x[1]/y)^2\n")
    assert not printed, printed
    assert r"\left(\frac{x_{1}}{y}\right)^{2}" in page, page


def test_a_solve_of_a_negative_load_is_not_a_subtraction(sheet):
    page, printed = sheet("K := [2, 0; 0, 4]\nF := [1; 2]\nd := solve(K, -2*F)\n")
    assert not printed, printed
    assert r"K^{-1}\,\left(-2" in page, page


def test_a_refusal_never_quotes_the_parser_s_unit_names(sheet):
    _, printed = sheet("k := [2[kN/m]; 3[kN/m]]\ny := 5[kN/m] - k\n")
    assert "'5[kN/m] - k' adds a number to a matrix" in printed, printed
    assert "__u_" not in printed, printed


def test_a_table_of_an_expression_heads_its_column_in_mathematics(sheet):
    page, printed = sheet("r = 3[kN]/(1[kN/m])\nx := 1[m]\ntable(r*y/x, y, 0[m], 1[m], 3)\ntable(y^2/2, y, 0, 1, 3)\n")
    assert not printed, printed
    assert "__u_" not in page and r"\text{" not in page, page
    assert r"\frac{y^{2}}{2}" in page, page


def test_a_squared_area_is_bracketed_once(sheet):
    page, printed = sheet("A := 8000[mm^2]\nx = A^2\nnumeric(x)\n")
    assert not printed, printed
    assert r"\left(\left(" not in page, page
    assert r"\left(8000.00\,\mathrm{mm}^{2}\right)^{2}" in page, page


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("f(x) = x/0.85\n", r"\frac{x}{0.85}"),
        ("g(x) = 2*x/0.9 + 1\n", r"\frac{2 x}{0.9} + 1"),
    ],
)
def test_a_function_dividing_by_a_decimal_is_written_as_typed(sheet, source, expected):
    page, printed = sheet(source)
    assert not printed, printed
    assert expected in page, page


# The audit of 0.47.1.


def test_a_table_over_one_bracketed_unit_heads_its_column_as_a_measurement(sheet):
    page, printed = sheet("table(x/1[m], x, 0[m], 1[m], 3)\n")
    assert not printed, printed
    assert r"\frac{x}{1\,\mathrm{m}}" in page and "__u" not in page, page


@pytest.mark.parametrize("unit", ["kN*m", "kip*ft"])
def test_a_root_in_a_compound_unit_keeps_its_thin_space(sheet, unit):
    page, printed = sheet(f"x = solve(eq(x, 4[{unit}]), x, 0[{unit}], 10[{unit}])\n")
    assert not printed, printed
    assert r"4.00\,\mathrm{" in last_value(page, "x"), page


@pytest.mark.parametrize(
    ("source", "kept"),
    [
        ("m := 2500[kgf*cm/m]\n", r"2500.00\,\frac{\mathrm{kgf} \cdot \mathrm{cm}}{\mathrm{m}}"),
        ("M := 4[kip*in/ft]\n", r"4.00\,\frac{\mathrm{kip} \cdot \mathrm{in}}{\mathrm{ft}}"),
    ],
)
def test_a_moment_per_width_typed_in_one_bracket_keeps_its_unit(sheet, source, kept):
    page, printed = sheet(source)
    assert not printed, printed
    assert kept in page, page


@pytest.mark.parametrize(
    ("source", "expected"),
    [("g(x) = 1/0.85*x\n", "1.18 x"), ("h(x) = sqrt(x/1.5)*2[m]\n", r"1.63\,\mathrm{m}\,\sqrt{x}")],
)
def test_a_decimal_under_a_number_or_inside_a_call_folds_as_before(sheet, source, expected):
    page, printed = sheet(source)
    assert not printed, printed
    assert expected in page, page
