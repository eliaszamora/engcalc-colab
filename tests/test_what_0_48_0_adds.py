r"""What 0.48.0 adds, from the inventory of open findings (`docs/project-context/OPEN-FINDINGS.md`).

- B10: `km`, `lbf`, `lb` (a force, as `kip` is) and `percent` are units.
- C9k: `%eng_units kip`, kips and inches, the units of his chapter-9 sheets.
- C3e, C3e2: on a `:=` line a part of a matrix is taken by a named list of indices
  (`K[libres, libres]`), by a range (`K[1:2, 1:2]`, both ends included, as on a `=` line) or
  by a name holding a whole number.
- C3f: a 1x1 matrix plus or minus a number is that number - a bar's axial force.
- C2b: a sheet function whose body is a matrix is worked out on a `:=` line.
- C10b: `% break` stops the `% for` or `% while` it stands in.
- C3k: `{th}` in a line of text inside a loop writes what the loop holds.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str, units: str = "") -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            magics = magic.EngMagics()
            if units:
                magics.eng_units(units)
            magics.eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), out.getvalue()

    return run


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("L := 2*km\n", r"2.00\,\mathrm{km}"),
        ("L := 2[km]\n", r"2.00\,\mathrm{km}"),
        ("y := 1[lbf]\n", r"1.00\,\mathrm{lbf}"),
        ("w := 3[lb/ft]\n", r"3.00\,\frac{\mathrm{lbf}}{\mathrm{ft}}"),
        ("z := 500[lb] + 1[kip]\n", r"1500.00\,\mathrm{lbf}"),
        ("r := 5[percent]\nP := 100[kN]\nQ := r*P\n", r"Q & = & \displaystyle 5.00\,\mathrm{kN}"),
    ],
)
def test_the_units_a_sheet_writes_are_units(sheet, source, expected):
    page, printed = sheet(source)
    assert not printed, printed
    assert expected in page, page


def test_a_pound_is_a_force_and_adds_to_a_kip(sheet):
    page, printed = sheet("P := 1[kip] + 1000[lb]\nnumeric(P, kip)\n")
    assert not printed, printed
    assert r"2.00\,\mathrm{kip}" in page, page


def test_the_kip_palette_reads_kips_and_inches(sheet):
    page, printed = sheet(
        "L := 12[ft]\nP := 10[kip]\nM := P*L\nE := 29000[ksi]\nI := 500[in^4]\nk := 3*E*I/L^3\n",
        units="kip",
    )
    assert not printed.replace("engcalc units: kip", "").strip().startswith("engcalc: line"), printed
    for expected in (
        r"144.00\,\mathrm{in}",
        r"1440.00\,\mathrm{kip} \cdot \mathrm{in}",
        r"29000.00\,\mathrm{ksi}",
        r"14.57\,\frac{\mathrm{kip}}{\mathrm{in}}",
    ):
        assert expected in page, (expected, page)


_K = "K := [2,-1,0;-1,2,-1;0,-1,1]*1000[kN/m]\n"
_K_FREE = r"\left[\begin{matrix}\displaystyle 2.00 & \displaystyle -1.00\\[3pt]\displaystyle -1.00 & \displaystyle 2.00\end{matrix}\right]"


@pytest.mark.parametrize(
    "line",
    ["libres := [1, 2]\nK_f := K[libres, libres]\n", "K_f := K[1:2, 1:2]\n", "K_f := K[:2, :2]\n"],
)
def test_a_part_of_a_matrix_is_taken_by_a_named_list_or_a_range(sheet, line):
    page, printed = sheet(_K + line)
    assert not printed, printed
    assert _K_FREE in page.split(r"K_{f}", 1)[1], page


def test_an_index_held_by_a_name_reads_its_number(sheet):
    page, printed = sheet(_K + "i := 3\nk := K[i, i]\n")
    assert not printed, printed
    assert r"1000.00\,\frac{\mathrm{kN}}{\mathrm{m}}" in page.split(r"\displaystyle k & = &", 1)[1], page


def test_a_backwards_range_is_refused(sheet):
    _, printed = sheet(_K + "K_f := K[2:1, 1]\n")
    assert "runs backwards" in printed, printed


def test_a_one_by_one_matrix_plus_a_number_is_a_number(sheet):
    page, printed = sheet("k := 100[kN/m]\ng := [1; -1]\nD := [2[mm]; 1[mm]]\nN := k*transpose(g)*D + 1[kN]\n")
    assert not printed, printed
    assert r"= 1.10\,\mathrm{kN}" in page, page


def test_a_matrix_plus_a_number_is_still_refused(sheet):
    _, printed = sheet("a := [1[kN], 2[kN]]\nb := a + 1[kN]\n")
    assert "adds a number to a matrix" in printed, printed


def test_a_function_that_makes_a_matrix_is_worked_out_on_a_colon_equals_line(sheet):
    page, printed = sheet(
        "k_e(E, A, L) = E*A/L*[1, -1; -1, 1]\nK_1 := k_e(200[GPa], 10[cm^2], 2[m])\n"
        "u := [1[mm]; 2[mm]]\nf := k_e(200[GPa], 10[cm^2], 2[m])*u\n"
    )
    assert not printed, printed
    assert r"10^{3}\,\left[\begin{matrix}\displaystyle 100.00 & \displaystyle -100.00" in page, page
    assert r"\left[\begin{matrix}\displaystyle -100.00\\[3pt]\displaystyle 100.00\end{matrix}\right]\,\mathrm{kN}" in page, page


_FOR_BREAK = """% for i in range(1, 6):
P_{i} := {i}*10[kN]
% if P_{i} > 25[kN]:
% break
% end
% end
"""


def test_a_break_stops_a_for_loop(sheet):
    page, printed = sheet(_FOR_BREAK)
    assert not printed, printed
    assert r"P_{3}" in page and r"P_{4}" not in page, page
    assert r"\text{: el ciclo se detiene.}" in page, page


def test_a_break_stops_a_while_loop(sheet):
    page, printed = sheet("x := 1\n% while x < 100:\nx := 2*x\n% if x > 10:\n% break\n% end\n% end\n")
    assert not printed, printed
    assert r"\textbf{En 4 iteraciones}\text{ (\% break):}" in page, page
    assert r"x & = & \displaystyle 16.00" in page, page


def test_a_break_in_an_inner_loop_stops_only_that_loop(sheet):
    page, printed = sheet(
        "% for i in range(1, 3):\n% for j in range(1, 4):\n% if j > 1:\n% break\n% end\n"
        "c_{i} := {i}*{j}\n% end\n% end\n"
    )
    assert not printed, printed
    assert r"c_{1} & = & \displaystyle 1.00" in page and r"c_{2} & = & \displaystyle 2.00" in page, page
    assert page.count(r"\text{: el ciclo se detiene.}") == 2, page


def test_a_break_outside_a_loop_is_refused(sheet):
    _, printed = sheet("% break\n")
    assert "% break stops a % for or a % while" in printed, printed


def test_a_loop_name_in_text_is_written(sheet):
    page, printed = sheet('% for th in [30, 60]:\n"""ángulo {th} grados y {nada}"""\n% end\n')
    assert not printed, printed
    assert r"\text{30 }" in page and r"\text{60 }" in page, page
    assert r"\{nada\}" in page, page


def test_a_brace_in_text_outside_a_loop_stays_as_written(sheet):
    page, printed = sheet('"""fuera {th}"""\n')
    assert not printed, printed
    assert r"\{th\}" in page, page


# C10a, C3d, C4a, C5l.


@pytest.mark.parametrize(
    ("source", "name", "expected"),
    [
        ("a := 3[kN]\nb := 5[kN]\nc := 5[kN]\ni := argmax(a, b, c)\n", "i", "2.00"),
        ("a := 3[kN]\nb := 5[kN]\nc := 1[kN]\ni := argmin(a, b, c)\n", "i", "3.00"),
        ("f := [3[kN]; 7[kN]; 2[kN]]\ni := argmax(f[1], f[2], f[3])\n", "i", r"\operatorname{argmax}\left(f_{1}, f_{2}, f_{3}\right) = 2.00"),
        ("f := [3[kN]; 7[kN]; 2[kN]]\nj := argmin(f)\n", "j", r"\operatorname{argmin}\left(f\right) = 3.00"),
    ],
)
def test_argmin_and_argmax_give_the_governing_position(sheet, source, name, expected):
    page, printed = sheet(source)
    assert not printed, printed
    assert expected in page.split(rf"\displaystyle {name} & = &", 1)[1], page


def test_argmin_of_values_of_different_kinds_is_refused(sheet):
    _, printed = sheet("g := [1[kN]; 2[m]]\nh := argmin(g)\n")
    assert "incompatible units" in printed, printed


@pytest.mark.parametrize(
    ("matrix", "expected"),
    [("[2,-1,0;-1,2,-1;0,-1,1]*1000[kN/m]", "3.00"), ("[1,-1;-1,1]*5[kN/m]", "1.00")],
)
def test_rank_on_a_colon_equals_line(sheet, matrix, expected):
    page, printed = sheet(f"K := {matrix}\nr := rank(K)\n")
    assert not printed, printed
    assert rf"\operatorname{{rank}}\left(K\right) = {expected}" in page, page


def test_lam_is_written_lambda(sheet):
    page, printed = sheet("lam := 2\nlam_c := 3\n")
    assert not printed, printed
    assert r"\displaystyle \lambda & = &" in page and r"\lambda_{c}" in page, page


def test_lambda_as_a_name_says_what_to_write(sheet):
    _, printed = sheet("lambda := 2\n")
    assert "write lam, which the page writes λ" in printed, printed


def test_a_matrix_with_a_name_lacking_a_value_says_which(sheet):
    _, printed = sheet("E := 200[GPa]\nA := 10[cm^2]\nL := 2[m]\nK = E*A/L*[1, -1; -1, 1]*q\nnumeric(K)\n")
    assert "it needs values for: q" in printed, printed
