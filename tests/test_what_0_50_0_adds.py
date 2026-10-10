r"""What 0.50.0 adds, from the inventory of open findings.

- C9i: two `% for`, one directly inside the other, make one table over their pairs.
- L44: a loop's `:=` line written with its formula (`y_{i} := x[{i}] - 1[m]`) is a column of the
  table, its rule written once above it.
- C5h: a sheet that writes one system - kips and inches - reads its matrices of numbers in it.
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


def test_nested_loops_make_one_table(sheet):
    page, printed = sheet(
        "% for i in range(1, 3):\n% for j in range(1, 3):\na_{i}{j} := {i}*{j}\nb_{i}{j} := {i}+{j}\n% end\n% end\n"
        "c := a_21 + b_12\n"
    )
    assert not printed, printed
    assert r"i, j & a_{ij} & b_{ij}" in page, page
    assert r"2, 1 & 2.00 & 3.00" in page and r"c & = & \displaystyle 5.00" in page, page


def test_an_inner_loop_with_a_break_still_runs_pass_by_pass(sheet):
    page, printed = sheet(
        "% for i in range(1, 3):\n% for j in range(1, 4):\n% if j > 1:\n% break\n% end\n"
        "c_{i} := {i}*{j}\nd_{i} := 2*c_{i}\n% end\n% end\n"
    )
    assert not printed, printed
    assert page.count(r"\text{: el ciclo se detiene.}") == 2, page


def test_a_loop_line_read_from_a_matrix_is_a_column(sheet):
    page, printed = sheet("x := [1[m]; 3[m]; 6[m]]\n% for i in range(1, 4):\ny_{i} := x[{i}] - 1[m]\nz_{i} := 2*y_{i}\n% end\n")
    assert not printed, printed
    assert r"\quad \displaystyle y_{i} = x_{i} - 1\,\mathrm{m}" in page, page
    assert r"i & y_{i}\,[\mathrm{m}] & z_{i}\,[\mathrm{m}]" in page and "3 & 5.00 & 10.00" in page, page


def test_a_kip_sheet_reads_its_matrices_in_kips(sheet):
    page, printed = sheet(
        "E := 29000[ksi]\nA := 1[in^2]\nk = E*A/L\nL := 10[ft]\nK := [k*1, k; k, 2*k]\n"
        "F := [1[kip]; 2[kip]]\nd := solve(K, F)\n"
    )
    assert not printed, printed
    assert r"2.90 & \displaystyle 2.90\\[3pt]\displaystyle 2.90 & \displaystyle 5.80\end{matrix}\right]\,\frac{\mathrm{kip}}{\mathrm{ft}}" in page, page
    assert r"\displaystyle 0.00414\end{matrix}\right]\,\mathrm{in}" in page, page


def test_an_si_sheet_still_reads_its_matrices_in_si(sheet):
    page, printed = sheet("k := 100[kN/m]\nK := [k, -k; -k, k]\nF := [1[kN]; 2[kN]]\nd := solve(K + [1, 0; 0, 0]*1[kN/m], F)\n")
    assert not printed, printed
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in page and r"\mathrm{kip}" not in page, page


# The audit of 0.50.0.


def test_nested_loops_name_their_columns_in_the_order_written(sheet):
    page, printed = sheet(
        '% for e, L in [(1, "2[m]"), (2, "3[m]")]:\n% for j in [1, 2]:\n'
        "a_{e}{j} := {j}*{L}\nb_{e}{j} := 2*a_{e}{j}\n% end\n% end\n"
    )
    assert not printed, printed
    assert r"e, L, j & a_{ej}" in page, page
    assert r"2, 3\,\mathrm{m}, 2 & 6.00 & 12.00" in page, page


def test_the_outer_name_ends_at_its_last_value(sheet):
    page, printed = sheet(
        "% for i in [1, 2, 3]:\n% for j in range(i, 3):\nc_{i}{j} := {i}*{j}\nd_{i}{j} := {i}+{j}\n% end\n% end\np := {i}\n"
    )
    assert not printed, printed
    assert r"p & = & \displaystyle 3.00" in page, page


def test_a_kgf_sheet_reads_its_matrices_in_its_system(sheet):
    page, printed = sheet("k := 2000[kgf/cm]\nK := [k, -k; -k, k]\nL_0 := 5[m]\n")
    assert not printed, printed
    assert r"200.00 & \displaystyle -200.00" in page and r"\frac{\mathrm{tonf}}{\mathrm{m}}" in page, page
