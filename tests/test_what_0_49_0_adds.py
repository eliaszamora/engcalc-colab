r"""What 0.49.0 adds and corrects, from the inventory of open findings.

- C2l: `piecewise` reads "si ... en otro caso", the page's language.
- C3i: a `table` whose columns are of different kinds - a shear beside its moment - shows each
  in its own unit; it was refused "incompatible units".
- C10f: a loop table keeps the family member its values carry: ft stays ft.
- C2e, C3o, C2f, B1: kept names stand in part assignments, `zeros(n, n) + K`, a `piecewise`
  body, a `solve` inside a product, and definitions written before their values.
- C7a: `assume(beta < pi/2)` is stated as given data; a bound that implies a sign gives it.
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


def test_a_piecewise_reads_in_spanish(sheet):
    page, printed = sheet("q(x) = piecewise(1, x < 2, 0)\n")
    assert not printed, printed
    assert r"\text{si}\: x < 2" in page and r"\text{en otro caso}" in page, page
    assert "for" not in page and "otherwise" not in page, page


def test_a_table_of_a_shear_and_its_moment(sheet):
    page, printed = sheet(
        "L := 6[m]\nq := 10[kN/m]\nV(x) = q*(L/2 - x)\nM(x) = q*x*(L - x)/2\ntable(V(x), M(x), x, 0[m], L, 4)\n"
    )
    assert not printed, printed
    assert r"V\left(x\right)\,[\mathrm{kN}] & M\left(x\right)\,[\mathrm{kN} \cdot \mathrm{m}]" in page, page
    assert r"2.00 & 10.00 & 40.00" in page, page


def test_a_loop_table_keeps_feet(sheet):
    page, printed = sheet("% for i in [1, 2]:\nL_{i} := {i}*10[ft]\nw_{i} := L_{i}*2[kip/ft]\n% end\n")
    assert not printed, printed
    assert r"L_{i}\,[\mathrm{ft}]" in page and "1 & 10.00 & 20.00" in page, page


_KEPT = "E := 200[GPa]\nA := 10[cm^2]\nL := 2[m]\nc := 0.6\nkeep k = E*A/L\n"


def test_an_assembly_into_parts_keeps_the_kept_name(sheet):
    page, printed = sheet(
        _KEPT + "K = zeros(2,2)\nK[1,1] = K[1,1] + k*c^2\nK[[1,2],[1,2]] = K[[1,2],[1,2]] + k*[1, -1; -1, 1]\nnumeric(K)\n"
    )
    assert not printed, printed
    assert r"\displaystyle k c^{2} + k & \displaystyle - k" in page, page
    assert r"136.00 & \displaystyle -100.00" in page, page
    assert "+ 0" not in page, page


def test_zeros_plus_a_matrix_and_a_piecewise_keep_the_kept_name(sheet):
    page, printed = sheet(_KEPT + "K = [k*c^2, 0; 0, k]\nG = zeros(2,2) + K\nf(x) = piecewise(k*x, x < L, 0)\n")
    assert not printed, printed
    assert r"G & = & \displaystyle \left[\begin{matrix}\displaystyle k c^{2}" in page, page
    assert r"\displaystyle k x & \text{si}\: x < L" in page, page


def test_a_solve_inside_a_product_reads_in_kept_names(sheet):
    page, printed = sheet("keep k_b = E*A_b/L\nkeep k_c = E*A_c/L\ndP_b = solve(eq(k_b*u + k_c*u, T), u)*k_b\n")
    assert not printed, printed
    assert r"\mathit{dP}_{b} & = & \displaystyle \frac{k_{b} T}{k_{b} + k_{c}} \end{array}" in page, page


def test_definitions_written_before_their_values_stay_names(sheet):
    page, printed = sheet(
        "d = h - cover\na = As*fy/(0.85*fc*b)\nphiMn = phi*As*fy*(d - a/2)\nphi := 0.9\n"
        "As := 1500[mm^2]\nfy := 420[MPa]\nfc := 28[MPa]\nb := 300[mm]\nh := 500[mm]\ncover := 40[mm]\nnumeric(phiMn)\n"
    )
    assert not printed, printed
    # The definition's own row, written before any value, reads as it always has; the
    # `numeric` row, once the values are there, reads in `d` and `a`.
    shown = page.split(r"\mathit{cover} & = &", 1)[1]
    assert r"\mathit{phiMn} & = & \displaystyle \phi\,\mathit{As}\,\mathit{fy}\,\left(d - \frac{a}{2}\right)" in shown, page
    assert "235.81" in shown and r"0.59\," not in shown, page


def test_a_bound_is_stated_and_the_cell_goes_on(sheet):
    page, printed = sheet("assume(beta < pi/2, L > 0)\ny = sin(beta)\nassume(x > 3)\nz = sqrt(x^2)\n")
    assert not printed, printed
    assert r"\beta < \frac{\pi}{2},\; L > 0" in page and "x > 3" in page, page
    assert r"z & = & \displaystyle x" in page, page


# The audit of 0.49.0.

_LOOP = (
    "E := 200[GPa]\nA := 10[cm^2]\nkeep k = E*A/L\nK {op} zeros(4,4)\n"
    "% for p, q, LL in [(1, 2, 2), (2, 3, 4), (3, 4, 1)]:\nL := {{LL}}[m]\n"
    "K[[{{p}},{{q}}],[{{p}},{{q}}]] {op} K[[{{p}},{{q}}],[{{p}},{{q}}]] + k*[1, -1; -1, 1]\n% end\n"
)


def test_an_equals_assembly_reading_a_redefined_name_says_so(sheet):
    _, printed = sheet(_LOOP.format(op="="))
    assert "K was assembled with = and is a formula that reads L" in printed, printed
    assert printed.count("assembled with =") == 1, printed


def test_a_colon_equals_assembly_adds_numbers_pass_by_pass(sheet):
    page, printed = sheet(_LOOP.format(op=":="))
    assert not printed, printed
    assert r"10^{3}\,\left[\begin{matrix}\displaystyle 100.00 & \displaystyle -100.00" in page, page
    assert r"\displaystyle -50.00 & \displaystyle 250.00 & \displaystyle -200.00" in page, page


def test_a_large_assembly_in_a_loop_is_not_slow(sheet):
    """His Example 4.15: a 42x42 assembled in a loop took 84 s while every entry was
    verified on every pass; only the entries a line changes are."""
    import time

    start = time.perf_counter()
    page, printed = sheet(
        "k := 2[kN/m]\nh := 3[m]\nk_s = k*h\nK = zeros(42,42)\n% for i in range(2,21):\n"
        "K[{2*i-1},{2*i-1}] = K[{2*i-1},{2*i-1}] + k_s\n% end\n"
    )
    assert not printed, printed
    assert time.perf_counter() - start < 20, "the assembly took too long"
