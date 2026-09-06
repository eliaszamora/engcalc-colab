r"""An evaluation with no name on its left still opens a relation, not a loose line.

Found by reading `tools/memoria.eng`, this repository's own reference sheet, after
0.28.0. Its moment section renders:

    M(x)  =  q x L / 2 - q x^2 / 2
             q L^2 / 8                       <- no equals sign, no subject
          =  (10.00 kN/m) (6.00 m)^2 / 8
          =  45.00 kN*m

`q L^2 / 8` is the moment at midspan and it is correct. What is wrong is that it hangs
there: an engineer reading the page sees it as a wrapped continuation of the line above,
because that is exactly what a row with an empty identity column and no `=` means
everywhere else in this renderer.

The cause is `_append_assignment_stage`, which opens a stage with ` & & body` when it is
given no left-hand side. In isolation that is defensible - the expression is its own
subject - but consecutive statements share one aligned array, so the row lands directly
under the previous statement's and inherits its reading.

It is not about `subs`. `numeric(q*L)` does the same thing, and so does any evaluation of
an expression that was not assigned a name.

The fix is the one a hand calculation already uses: put the expression in the identity
column, where the `=` of the next stage attaches to it.

    q L^2 / 8  =  (10.00 kN/m) (6.00 m)^2 / 8
               =  45.00 kN*m

Older than this session: present in 0.27.1 at `a1b9cf5`, from `8b5f95a`, which introduced
bounded semantic stages.
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


BEAM = "L := 6*m\nq := 10*kN/m\nR_A = q*L/2\nM(x) = R_A*x - q*x^2/2\n"


# --- the defect --------------------------------------------------------------------

def test_the_reference_memoria_does_not_float_its_midspan_moment(cell):
    """The page that found it: `tools/memoria.eng`, moment section."""
    latex = cell(BEAM + "numeric(subs(M(x), x, L/2))\n")
    assert r"\frac{q L^{2}}{8} & = &" in latex, latex
    assert r"& & \displaystyle \frac{q L^{2}}{8}" not in latex, latex
    assert "45.00" in latex, latex


def test_an_unnamed_expression_opens_a_relation(cell):
    """Not about `subs`. Any evaluation of an unassigned expression did this."""
    latex = cell(BEAM + "numeric(q*L)\n")
    assert r"q L & = &" in latex, latex
    assert r"& & \displaystyle q L " not in latex, latex
    assert "60.00" in latex, latex


def test_the_relation_still_reaches_its_value(cell):
    """The stages after the first must still be there and still align."""
    latex = cell(BEAM + "numeric(q*L)\n")
    assert latex.count(" & = & ") >= 2, latex


# --- what must not move -------------------------------------------------------------

def test_a_named_evaluation_is_untouched(cell):
    """`numeric(M(L/2))` already named its subject and must read exactly as it did."""
    latex = cell(BEAM + "numeric(M(L/2))\n")
    assert r"M\left(\frac{L}{2}\right) & = &" in latex, latex
    assert "45.00" in latex, latex


def test_an_assignment_is_untouched(cell):
    latex = cell(
        "L := 6*m\nq := 10*kN/m\nE := 200*GPa\nI_z := 80e6*mm**4\n"
        "d_max = 5*q*L^4/(384*E*I_z)\nnumeric(d_max)\n"
    )
    assert r"d_{max} & = &" in latex, latex
    assert "10.55" in latex, latex


WIDE = (
    "L_vano := 6.25*m\nq_serv := 12.5*kN/m\nE_acero := 205*GPa\n"
    "I_seccion := 83.6e6*mm**4\nk_apoyo := 1.15\n"
)


def test_a_formula_too_wide_to_sit_beside_its_value_is_not_promoted(cell):
    """The width guard, and the one place this change deliberately leaves the old shape.

    `5 k q L^4 / (384 E I)` beside its own substitution measures 124 against a budget of
    104, so promoting it would give the array an identity column the width of the page
    and push every other row's `=` off to the right. It keeps the rows it had.

    That means a wide unnamed evaluation still opens with a loose row. It is a smaller
    set than the one being fixed - the reference memoria has none - and the alternative
    costs the whole page, so it is recorded as a remainder in NEXT.md rather than traded
    for a worse layout.
    """
    latex = cell(WIDE + "numeric(5*k_apoyo*q_serv*L_vano^4/(384*E_acero*I_seccion))\n")
    assert r"& & \displaystyle \frac{5 k_{apoyo}" in latex, latex


def test_a_narrow_formula_of_the_same_page_is_promoted(cell):
    """The other side of the width guard: same sheet, a formula that does fit."""
    latex = cell(WIDE + "numeric(k_apoyo*q_serv*L_vano^2/8)\n")
    assert r"\frac{k_{apoyo} q_{serv} L_{vano}^{2}}{8} & = &" in latex, latex


def test_a_multi_row_formula_keeps_every_row(cell):
    """Promotion takes `formula_rows[0]` and drops the stage. A formula that wrapped to
    nine rows would lose eight of them silently, which is a worse defect than the one
    being fixed and is why the promotion asks for a single row."""
    setup = "".join(f"{n}_x := {i + 2}*m\n" for i, n in enumerate("abcdefghi"))
    expr = " + ".join(f"{i + 2}*{n}_x" for i, n in enumerate("abcdefghi"))
    latex = cell(setup + f"numeric({expr})\n")
    for i, n in enumerate("abcdefghi"):
        assert rf"{i + 2} {n}_{{x}}" in latex, (n, latex)


def test_the_promoted_formula_is_written_once(cell):
    """It moves into the identity column; it does not also stay where it was, and it
    does not repeat on every following stage."""
    latex = cell(BEAM + "numeric(subs(M(x), x, L/2))\n")
    assert latex.count(r"\frac{q L^{2}}{8}") == 1, latex


def test_a_symbolic_row_is_untouched(cell):
    """`R_A = q*L/2` is a definition, not an evaluation, and never had this shape."""
    latex = cell(BEAM)
    assert r"R_{A} & = & \displaystyle \frac{q L}{2}" in latex, latex
