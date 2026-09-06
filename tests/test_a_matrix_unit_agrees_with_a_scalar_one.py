r"""A value reads the same whether it is a scalar or a cell of a matrix.

Found by working a matrix frame analysis. A lateral stiffness assembled from element
matrices came out as

    70303.22 GPa*mm^2/m

which is `70303.22 kN/m` written in units nobody uses. The same expression outside a
matrix reads `kN/m`, and has since 0.10.0:

    k = E*A/L        numeric(k)   ->  21875.00 kN/m          the scalar path
    K = [E*A/L]      numeric(K)   ->  21875.00 GPa*mm^2/m    the matrix path

Same number, same dimension, two answers, decided by whether it was in a matrix.

The cause is a tie. `_aggregate_unit` scores each candidate by how far it puts the
magnitudes from the readable band, and `GPa*mm^2/m` and `kN/m` are the *same* unit under
two names - 1 GPa*mm^2/m is exactly 1 kN/m - so they score identically. The comparison is
a strict `<`, and the seed is the unit the value arrived in, so the algebra's unit wins
every tie.

Keeping a tie is right when the unit is the engineer's own: `tonf/m` should not lose to
`kN/m` for scoring the same. But `_aggregate_unit` has already asked, four lines earlier,
and `GPa*mm^2/m` is four unit terms against the family's two. A unit that has been judged
not to be the engineer's does not then get to win a tie against the family.
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


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


INPUTS = "E := 210*GPa\nA := 625*mm**2\nL := 6*m\n"


def test_a_stiffness_in_a_matrix_reads_as_a_stiffness(cell):
    """The defect. 210 GPa x 625 mm^2 / 6 m = 21875 kN/m either way."""
    final = _final(cell(INPUTS + "K = [E*A/L]\nnumeric(K)\n"))
    assert "21875.00" in final, final
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in final, final
    assert "GPa" not in final, final


def test_the_scalar_and_the_matrix_agree(cell):
    """The contract that says what is actually wrong: not that a matrix picks a bad
    unit, but that it picks a different one from the scalar beside it."""
    scalar = _final(cell(INPUTS + "k = E*A/L\nnumeric(k)\n"))
    matrix = _final(cell(INPUTS + "K = [E*A/L]\nnumeric(K)\n"))
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in scalar, scalar
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in matrix, matrix


def test_a_unit_the_engineer_wrote_still_wins_its_tie(cell):
    """The half that must not move. `tonf/m` is one unit term against `kN/m`'s two, so
    it is the engineer's and is kept - scoring the same as a family member is not a
    reason to replace it. Only a unit already judged to be the algebra's loses a tie."""
    final = _final(cell("q := 2.8*tonf/m\nQ = [q]\nnumeric(Q)\n"))
    assert r"\mathrm{tonf}" in final, final
    assert "2.80" in final, final


def test_a_matrix_of_several_cells_still_shares_one_unit(cell):
    """`_aggregate_unit` exists to give a whole matrix one unit rather than one per
    cell, and that is unchanged: the unit is printed once, outside the brackets."""
    latex = cell(INPUTS + "K = [E*A/L, 2*E*A/L; 3*E*A/L, 4*E*A/L]\nnumeric(K)\n")
    final = _final(latex)
    assert final.count(r"\frac{\mathrm{kN}}{\mathrm{m}}") == 1, final
    # The digits moved outside the brackets once, which is a separate change and does
    # not touch what this asserts: one unit, printed once, for the whole matrix.
    assert "10^{3}" in final, final
    assert "21.88" in final and "87.50" in final, final


def test_a_column_of_a_table_is_unaffected(cell):
    """`_aggregate_unit` serves table columns too, and a table of a declared unit must
    keep reading in it."""
    latex = cell(
        "L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L - x)/2\n"
        "table(M(x), x, 0*m, L, 3)\n"
    )
    assert "kN" in latex, latex
