r"""A unit written into a matrix reads as a unit in its eigenvalues too.

    A   = [2 kN/m, 0; 0, 3 kN/m]      the metre upright
    lam = {λ = 2 kN/m ; λ = 3 kN/m}   the metre italic, a variable

The matrix row set its units upright and the eigenvalue set two lines below did not: the
printer sets a name of several letters upright on its own, so `kN` survived, and `m`, `s`
and `N` came out as variables. It is #96's defect in the one printer #230 left without
unit literals - `_analysis_scalar_latex` - and #230's contract file wrote it down rather
than fixing it blind, because no sheet here drew an eigenvalue holding a unit. The audit of
0.31.14 found one.

Two things were missing, not one. The engine never collected the unit names of an
eigenvalue or eigenvector set (`_unit_literals_of` looked only at SymPy expressions), and
the renderer, which already had the row's unit literals, never handed them to either
printer, nor to the vectors, nor to the matrix of a set with no closed form.

What must not change: a name the sheet has given a value to is not a unit, whatever the
alias table says, and stays a variable.
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


STIFFNESS = "A = [2*kN/m, 0; 0, 3*kN/m]\n"


def test_an_eigenvalue_reads_its_metre_upright(cell, capsys):
    raw = cell(STIFFNESS + "lam = eigenvals(A)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert (
        r"\lambda=\frac{2\,\mathrm{kN}}{\mathrm{m}}\; ; \;\lambda=\frac{3\,\mathrm{kN}}{\mathrm{m}}"
        in raw
    ), raw


def test_the_eigenvalues_beside_the_vectors_read_it_upright(cell, capsys):
    raw = cell(STIFFNESS + "phi = eigenvects(A)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\lambda=\frac{2\,\mathrm{kN}}{\mathrm{m}},\;\mathbf{v}_{1}=" in raw, raw
    assert r"\frac{2\,\mathrm{kN}}{m}" not in raw, raw


def test_a_vector_holding_a_unit_reads_it_upright(cell, capsys):
    """The vector is a matrix of its own and was drawn without the row's units."""
    raw = cell("B = [1*s, 1*m; 0, 2*s]\nphi = eigenvects(B)\n")
    assert "engcalc:" not in capsys.readouterr().out
    vectors = raw.split(r"\phi")[-1]
    # One metre per second, written with its one since a unit alone is
    # (test_a_unit_alone_is_written_with_its_one); what this pins is that it is upright.
    assert r"\frac{1\,\mathrm{m}}{\mathrm{s}}" in vectors, vectors
    assert r"\frac{m}{s}" not in vectors and r"1\,m}" not in vectors, vectors


def test_a_set_with_no_closed_form_draws_its_matrix_with_upright_units(cell, capsys):
    """Three rows with a name in them seek no formula: the row is `det(A - λI) = 0`, and
    its matrix is the sheet's own matrix, which must read the way the sheet's row did."""
    raw = cell(
        "k := 1*kN/m\nK = [2*k, -1*kN/m, 0; -1*kN/m, 2*k, -k; 0, -k, k]\nlam = eigenvals(K)\n"
    )
    assert "engcalc:" not in capsys.readouterr().out
    determinant = raw.split(r"\mathit{lam}")[-1]
    assert r"\det\left(" in determinant, determinant
    # `-1*kN/m`, written with its one since a unit alone is, sign and all
    # (test_a_unit_alone_is_written_with_its_one); what this pins is that it is upright.
    assert r"\frac{1\,\mathrm{kN}}{\mathrm{m}}" in determinant, determinant
    assert r"\frac{\mathrm{kN}}{m}" not in determinant, determinant


def test_a_name_with_a_value_is_still_a_variable(cell, capsys):
    """`m := 2 kg` makes `m` a mass: the eigenvalue holding it keeps it italic."""
    raw = cell("m := 2*kg\nC = [m, 0; 0, 3*kg]\nlam = eigenvals(C)\n")
    assert "engcalc:" not in capsys.readouterr().out
    eigenvalues = raw.split(r"\mathit{lam}")[-1]
    assert r"\lambda=m" in eigenvalues, eigenvalues
    assert r"\lambda=\mathrm{m}" not in eigenvalues, eigenvalues
