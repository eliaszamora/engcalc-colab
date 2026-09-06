r"""A cell of a mixed-dimension matrix reads like the scalar it is.

The fifth place this same shape has turned up, and the one a stiffness matrix in mixed
coordinates walks straight into. `K` for a frame with two rotations and one translation
is dimensionally heterogeneous by nature - a moment per radian, a force, and a force per
length in the same matrix - which is physics and not a defect, and EngCalc is right to
keep each entry's own dimension rather than invent one for the matrix.

What was wrong is the unit each cell was shown in:

    4*E*I/L    as a scalar                 517.20 kN*m
               in a homogeneous matrix     517.20 kN*m
               in a heterogeneous matrix   5.17 x 10^8 GPa*mm^4/m

`5.17 x 10^8 GPa*mm^4/m` is `517.20 kN*m`. A homogeneous matrix shares one unit chosen by
`_aggregate_unit`, which consults the family; a heterogeneous one renders each cell on its
own through `_quantity_latex`, whose `declared` argument defaults to True - so every cell
kept whatever the algebra left it in.

`declared` has meant "the engineer wrote this unit" since the fix that made a definition
show the coefficient it was typed with. A cell of a computed matrix wrote nothing.
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


COLUMN = "E := 210*GPa\nI := 2278125*mm**4\nL := 3.7*m\nA := 625*mm**2\n"


def test_each_cell_of_a_mixed_matrix_reads_in_engineering_units(cell):
    """4EI/L = 517.20 kN*m and EA/L = 35472.97 kN/m. Different dimensions, one matrix,
    and each cell in a unit an engineer writes."""
    final = _final(cell(COLUMN + "K = [4*E*I/L, E*A/L]\nnumeric(K)\n"))
    assert "517.20" in final, final
    assert "35472.97" in final, final
    assert "GPa" not in final, final


def test_a_mixed_cell_agrees_with_the_same_value_alone(cell):
    scalar = _final(cell(COLUMN + "k = 4*E*I/L\nnumeric(k)\n"))
    mixed = _final(cell(COLUMN + "K = [4*E*I/L, E*A/L]\nnumeric(K)\n"))
    assert r"\mathrm{kN} \cdot \mathrm{m}" in scalar, scalar
    assert r"\mathrm{kN} \cdot \mathrm{m}" in mixed, mixed


def test_the_matrix_keeps_one_dimension_per_cell(cell):
    """The half that must not move. A mixed matrix does not get one unit imposed on it -
    that is what `## v0.9.0` means by preserving the dimensionality of each entry - so
    the two cells here carry different units and both are printed."""
    final = _final(cell(COLUMN + "K = [4*E*I/L, E*A/L]\nnumeric(K)\n"))
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in final, final


def test_a_unit_the_engineer_wrote_is_still_kept_in_a_mixed_matrix(cell):
    """`tonf/m` is one unit term against the family's two, so it is the engineer's and
    stays - in a matrix cell as anywhere else."""
    final = _final(cell(
        "q := 2.8*tonf/m\nM := 5*kN*m\nK = [q, M]\nnumeric(K)\n"
    ))
    assert r"\mathrm{tonf}" in final, final
    assert "2.80" in final, final


def test_a_homogeneous_matrix_is_unaffected(cell):
    """It goes through `_aggregate_unit` and shares one unit printed once."""
    final = _final(cell(COLUMN + "K = [4*E*I/L, 2*E*I/L]\nnumeric(K)\n"))
    assert final.count(r"\mathrm{kN} \cdot \mathrm{m}") == 1, final
    assert "517.20" in final and "258.60" in final, final
