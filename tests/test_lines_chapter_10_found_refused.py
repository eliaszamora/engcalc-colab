r"""Valid lines that chapter 10 of his book found refused.

Material nonlinear analysis is event to event: which hinge forms next is a condition on a
matrix of numbers, and how far the load goes is a `solve` in a range over its entries.
Four solvers wrote these and found each refused:

- `% if h_{e} < 0.5` - a placeholder inside a name in a condition was read before the
  loop ran, as `h_` beside a set (all four solvers);
- `% if f[1] > 0.5[kip]` on `f := [...]` - "Use it on a := line";
- `x := solve(eq(f[1] + x*df[1], 300[kip]), x, 0, 1000)` - "unknown numeric name 'x'";
- `{n} := 1` - "invalid numeric assignment target '1'";
- `% if y > 1*kip*in` - refused without the hint a `:=` line gives, "write inch".
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


def ran(result: tuple[str, str]) -> str:
    page, printed = result
    assert "engcalc:" not in printed, printed
    return page


def value_of(page: str, name: str) -> str:
    return page.split(name + r" & = & \displaystyle ", 1)[1].split(r"\\", 1)[0].split(r"\end", 1)[0].strip()


# -- a placeholder inside a name, in a condition -------------------------------------------


def test_a_placeholder_in_a_name_in_an_if(sheet):
    page = ran(sheet("h_1 := 0\n% for e in [1]:\n% if h_{e} < 0.5:\ny_{e} := 1\n% end\n% end\n"))
    assert r"y_{1}" in page, page


def test_the_largest_of_several_names(sheet):
    page = ran(sheet(
        "phi_1 := 0.2\nphi_2 := 0.7\nm := 0\n% for j in range(1, 3):\n"
        "% if phi_{j} > m:\nm := phi_{j}\n% end\n% end\nreport(m)\n"
    ))
    assert "0.70" in page.rsplit(r"m & = &", 1)[1], page


def test_a_placeholder_in_a_name_in_a_while(sheet):
    page = ran(sheet(
        "x_1 := 0[kip]\n% k = 1\n% while x_{k} < 3[kip]:\nx_1 := x_1 + 1[kip]\n% end\nreport(x_1)\n"
    ))
    assert "3.00" in page.rsplit(r"x_{1} & = &", 1)[1], page


# -- an entry of a matrix of numbers, in a condition ---------------------------------------


def test_a_condition_reads_an_entry(sheet):
    page = ran(sheet("f := [1[kip]; 2[kip]]\n% if f[1] > 0.5[kip]:\ny := 1\n% else:\ny := 2\n% end\n"))
    assert value_of(page, "y") == "1.00", page


def test_the_entry_is_named_in_the_note(sheet):
    page = ran(sheet("f := [1[kip]; 2[kip]]\n% if f[2]/f[1] > 1.5:\ny := 1\n% end\n"))
    assert r"\frac{f_{2}}{f_{1}} = 2.00 > 1.50" in page, page


def test_a_condition_that_fails_on_an_entry(sheet):
    page = ran(sheet("f := [1[kip]; 2[kip]]\n% if f[2] < f[1]:\ny := 1\n% else:\ny := 2\n% end\n"))
    assert value_of(page, "y") == "2.00", page


def test_a_whole_matrix_in_a_condition_is_told(sheet):
    _, printed = sheet("f := [1[kip]; 2[kip]]\n% if f > 0.5[kip]:\ny := 1\n% end\n")
    assert "engcalc:" in printed and "matrix" in printed, printed


def test_nothing_is_left_behind_by_a_condition(sheet):
    # The side is worked out as a `:=` line would be, and assigned to nothing.
    _, printed = sheet("f := [1[kip]; 2[kip]]\n% if f[1] > 0.5[kip]:\ny := 1\n% end\nz := eng_condition\n")
    assert "unknown numeric name 'eng_condition'" in printed, printed


# -- a range solve that reads entries ------------------------------------------------------


def test_a_range_solve_reads_entries(sheet):
    page = ran(sheet(
        "f := [200[kip]; 900[kip*in]]\ndf := [1[kip]; 2[kip*in]]\n"
        "x := solve(eq(f[1] + x*df[1], 300[kip]), x, 0, 1000)\n"
    ))
    assert value_of(page, "x") == "100.00", page
    # The equation it solved is written above the value, each entry by its name.
    assert r"f_{1}" in page and r"\mathit{df}_{1}" in page and r"\mathit{solve}" not in page, page


def test_an_entry_inside_a_product(sheet):
    page = ran(sheet(
        "f := [200[kip]; 900[kip*in]]\nK := [1[kip], 2[kip]; 3[kip], 4[kip]]\n"
        "y := solve(eq(K[1,2]*y, 2*f[1]), y, 0, 1000)\n"
    ))
    assert value_of(page, "y") == "200.00", page
    assert r"K_{1,2}" in page and r"2 f_{1}" in page, page


def test_the_unknown_need_not_be_x(sheet):
    page = ran(sheet("f := [1[kip]; 2[kip]]\nb := solve(eq(f[1]*a, 2[kip]), a, 0, 10)\n"))
    assert value_of(page, "b") == "2.00", page


def test_a_matrix_in_the_equation_is_told(sheet):
    _, printed = sheet("g := [1; 2]\ns := 3[kip]\nw := solve(eq(g[1]*w + g, s), w, 0, 10)\n")
    assert "engcalc:" in printed and "take one of its entries" in printed, printed


# -- a placeholder as the whole target -----------------------------------------------------


def test_a_placeholder_is_the_whole_target(sheet):
    page = ran(sheet("% n = 'h_1'\n{n} := 1\n"))
    assert value_of(page, r"h_{1}") == "1.00", page


def test_a_placeholder_target_in_a_loop(sheet):
    page = ran(sheet("% for n in ['a_1', 'b_2']:\n{n} := 2[m]\n% end\n"))
    assert r"a_{1}" in page and r"b_{2}" in page, page


# -- the inch in a condition ---------------------------------------------------------------


def test_the_inch_in_a_condition_is_told(sheet):
    _, printed = sheet("y := 2[kip*inch]\n% if y > 1*kip*in:\nz := 1\n% end\n")
    assert "write inch" in printed, printed
