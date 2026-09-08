r"""A kept name survives every formula after it, not only the first one.

On the frame benchmark, one line apart:

    R_3  =  [c_d  s_d   0    0 ]          the rotation written with its cosines
            [ 0    0   c_d  s_d]

    A_1  =  [0                     0                    0]
            [0                     0                    0]
            [1                     0                    0]        A_1 = R_1*L_1*T
            [0   (-x_1+x_2)/sqrt((-x_1+x_2)^2+(-y_1+y_2)^2)   0]
            [0  -(-y_1+y_2)/sqrt((-x_1+x_2)^2+(-y_1+y_2)^2)   0]
            [0                     0                    0]

Same page, same quantities, two ways of writing them. `A_1` should read `c_c` and
`-s_c` in that column, and `c_c` is exactly what `R_1` prints one line above.

**The rule was "all or nothing", and the nothing expands the kept names too.**
`_written_form` walks the statement and abandons the written form the moment it meets a
name that is defined and not kept. That guard is right on its own terms - substituting an
ordinary definition produces a form *wider* than the evaluated one, which is what it was
measured to prevent - but abandoning the written form falls back on the fully evaluated
expression, and that expression has the kept names expanded inside it. The barrier is
lost by the very branch meant to keep the page narrow, and on this sheet it is what makes
the assembled stiffness matrix run off the side of the page.

Measured in isolation, and it is not a matrix problem:

| `x = 2*L`         | keeps `L`  |
| `M = [L, 0; 0, L]`| keeps `L`  |
| `y = x`           | **expanded** |
| `N = M`           | **expanded** |
| `P = M*2`         | **expanded** |

One level, then gone.

**The fix uses something that was already there.** `written_namespace` holds each name's
written form - the expression with its kept names still standing - and only
`numeric(name)` was reading it. So a name that is not itself kept can still be replaced
by its written form, and the kept names inside it survive to the next formula, and the
one after that.

Scoped deliberately: the guard still fires, and a sheet with no `keep` in it renders
exactly as before. It is skipped only for a statement that reaches a kept name, which is
the only case where abandoning the written form loses one.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> str:
        captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def _last(latex: str) -> str:
    return latex.split(r"\\[8pt]")[-1].replace(r"\end{array}", "").strip()


GEOMETRY = "a := 3*m\nb := 4*m\nkeep L = sqrt(a^2 + b^2)\n"


def test_a_kept_name_survives_a_second_scalar_formula(cell):
    """`x = 2*L` keeps `L` today; `y = x` is the step that loses it."""
    final = _last(cell(GEOMETRY + "x = 2*L\ny = x\n"))
    assert "L" in final, final
    assert "sqrt" not in final, final


def test_a_kept_name_survives_being_carried_through_a_matrix(cell):
    final = _last(cell(GEOMETRY + "M = [L, 0; 0, L]\nN = M\n"))
    assert "L" in final, final
    assert "sqrt" not in final, final


def test_a_kept_name_survives_a_matrix_product(cell):
    final = _last(cell(GEOMETRY + "M = [L, 0; 0, L]\nP = M*2\n"))
    assert "L" in final, final
    assert "sqrt" not in final, final


def test_the_frame_chain_keeps_its_cosines(cell):
    """The benchmark's own shape, cut to its bones: a rotation written with cosines,
    then a product of it. This is the page that showed the defect."""
    sheet = (
        "x_1 := 0*m\nx_2 := 0*m\ny_1 := 0*m\ny_2 := 3.70*m\n"
        "keep L_c = sqrt((x_2 - x_1)^2 + (y_2 - y_1)^2)\n"
        "keep c_c = (x_2 - x_1)/L_c\n"
        "keep s_c = (y_2 - y_1)/L_c\n"
        "R_1 = [c_c, s_c; -s_c, c_c]\n"
        "S = [1, 0; 0, 1]\n"
        "A_1 = R_1*S\n"
    )
    final = _last(cell(sheet))
    assert "c_{c}" in final, final
    assert "s_{c}" in final, final
    assert "x_{2}" not in final, final


def test_the_same_matrix_under_two_names_reads_the_same_way(cell):
    """`R_2 = R_1` printed the expansion while `R_1` one line above printed the
    cosines. A memoria that states one quantity two ways is the defect, whichever of
    the two is prettier."""
    sheet = (
        "x_1 := 0*m\nx_2 := 0*m\ny_1 := 0*m\ny_2 := 3.70*m\n"
        "keep L_c = sqrt((x_2 - x_1)^2 + (y_2 - y_1)^2)\n"
        "keep c_c = (x_2 - x_1)/L_c\n"
        "R_1 = [c_c, 0; 0, c_c]\n"
        "R_2 = R_1\n"
    )
    latex = cell(sheet)
    rows = [row for row in latex.split(r"\\[8pt]") if "R_{1}" in row or "R_{2}" in row]
    assert len(rows) == 2, latex
    first, second = (
        row.split("& = &")[-1].replace(r"\end{array}", "").strip() for row in rows
    )
    assert first == second, (first, second)


# --- what must not move -------------------------------------------------------------

def test_a_sheet_with_no_kept_name_is_unchanged(cell):
    """The guard exists because substituting an ordinary definition widens the formula,
    and that measurement still stands. A statement that reaches no kept name keeps
    today's behaviour exactly: the evaluated expression, not a written one."""
    final = _last(cell("a := 3*m\nb := 4*m\nd = a + b\ne = 2*d\n"))
    assert "d" not in final.replace(r"\displaystyle", ""), final


def test_a_written_coefficient_survives_one_formula_further_down(cell):
    r"""The measurement that decided how far this goes.

    The first version of the fix only substituted a written form that itself held a kept
    name. Twenty-two sheets could not tell that apart from substituting every written
    form - all four in the repository that use `keep` included - so the case was built on
    purpose, from the README's own example, and the narrow rule turned out to be the
    worse one:

        narrow:  phiMn = fy phi As (-1.18 fy As / (2 b fc) + d)
        wide:    phiMn = fy phi As (-fy As / (2 0.85 b fc) + d)

    `a` is not kept and expands either way - the same names appear - but the 0.85 of
    ACI 318 §22.2.2.4.1 is on the page in only one of them, and "a coefficient written in
    a denominator stays there" is a change this repository made one release before `keep`
    existed. The narrow rule folded it back into a 1.18 one formula further down.
    """
    sheet = (
        "h := 500*mm\ncover := 40*mm\nfc := 28*MPa\nfy := 420*MPa\n"
        "b := 300*mm\nAs := 1935*mm**2\nphi := 0.9\n"
        "keep d = h - cover\n"
        "a = As*fy/(0.85*fc*b)\n"
        "phiMn = phi*As*fy*(d - a/2)\n"
    )
    final = _last(cell(sheet))
    assert "0.85" in final, final
    assert "1.18" not in final, final


def test_the_kept_name_still_evaluates_to_the_same_number(cell):
    """`keep` is a barrier in presentation and nothing else. The value must not move."""
    final = _last(cell(GEOMETRY + "x = 2*L\ny = x\nnumeric(y)\n"))
    assert "10.00" in final, final
    assert r"\mathrm{m}" in final, final
