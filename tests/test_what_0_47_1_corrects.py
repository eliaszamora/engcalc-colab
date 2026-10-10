r"""Presentation left open by 0.46.2 and 0.47.0 (his "aborda todo lo que falte", 2026-10-09).

- A compound unit typed in brackets on a `=` line read in the alphabet's order:
  `2.5[kip*ft]` printed `2.5 ft·kip`, `2.5[kip*inch]` `2.5 in·kip`. The page's unit order
  (`_page_unit_order`) asked Pint for `__u_ft`, the name a bracketed unit is read under,
  failed, and left SymPy's order; `kN·m` was right by the alphabet alone.
- A range `solve` on a `=` line whose root falls exactly wrote `2.0`: a short float reads
  as typed, and a root is no typed number.
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
