r"""The modes of a shear building with three storeys or more, computed as numbers.

A two-storey model worked: `eigenvals(inv(M)*K)` found the closed form of a quadratic and
`numeric(lam)` evaluated it. Three storeys did not, and four was worse:

    3 storeys   0.1 s    7 KB of cubic formula    "symbolic numeric value must be real and finite"
    4 storeys  81.5 s  760 KB of quartic formula  "unsupported piecewise relation"

A cubic with three real roots - which is what a shear building's frequency equation
always is - can only be written in radicals through complex numbers, so the closed form
the page printed could not even be evaluated. And nobody solves a frequency equation of
degree three by formula: the textbooks and every structural program compute the modes
numerically from the numeric matrices.

**So a matrix of three rows or more with names in it gets no closed form.** The page
shows the problem it is solving - `det(A - λ I) = 0` for the matrix the sheet built - and
`numeric(...)` computes the eigenvalues and mode shapes from the numbers, in ascending
order, which is how modes are numbered. A two-by-two keeps its closed form, and a matrix
of plain numbers keeps SymPy's exact answer (`diag(2, 1, 2)` still reads `1` and `2`).

The reference values below are computed by numpy inside each test from the same inputs,
in SI, so no number here was copied from the page it checks.
"""

import re
import time

import numpy as np
import pytest

import engcalc_colab.magic as magic

from conftest import block_text


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str) -> tuple[str, str]:
        captured.clear()
        magic.EngMagics().eng("", source)
        raw = "".join(str(getattr(obj, "data", "")) for obj in captured)
        return raw, block_text(raw)

    return run


def building(storeys: int) -> tuple[str, np.ndarray, np.ndarray]:
    """A shear building: storey stiffnesses in kN/m and floor masses in kg, the sheet that
    writes it, and the same two matrices in SI for numpy."""
    k = [3000.0 - 500.0 * i for i in range(storeys)]
    m = [600.0 - 50.0 * i for i in range(storeys)]
    lines = [f"k_{i + 1} := {k[i]:g}*kN/m" for i in range(storeys)]
    lines += [f"m_{i + 1} := {m[i]:g}*kg" for i in range(storeys)]
    rows = []
    stiffness = np.zeros((storeys, storeys))
    for i in range(storeys):
        row = []
        for j in range(storeys):
            if i == j:
                row.append(f"k_{i + 1} + k_{i + 2}" if i < storeys - 1 else f"k_{i + 1}")
                stiffness[i, j] = k[i] + (k[i + 1] if i < storeys - 1 else 0.0)
            elif abs(i - j) == 1:
                row.append(f"-k_{max(i, j) + 1}")
                stiffness[i, j] = -k[max(i, j)]
            else:
                row.append("0")
        rows.append(", ".join(row))
    lines.append("K = [" + "; ".join(rows) + "]")
    lines.append("M = diag(" + ", ".join(f"m_{i + 1}" for i in range(storeys)) + ")")
    return "\n".join(lines) + "\n", stiffness * 1000.0, np.diag(m)


def reference(stiffness, mass):
    values, vectors = np.linalg.eig(np.linalg.inv(mass) @ stiffness)
    order = np.argsort(values.real)
    return values.real[order], vectors.real[:, order]


def eigenvalues_on(page: str) -> list[float]:
    numeric = page.rsplit("\\\\[8pt]", 1)[-1]
    found = re.findall(r"\\lambda=([\d.]+) 1/s²", numeric)
    assert found, numeric
    return [float(value) for value in found]


def test_three_storeys_have_three_modes(cell, capsys):
    sheet, stiffness, mass = building(3)
    raw, page = cell(sheet + "lam = eigenvals(inv(M)*K)\nnumeric(lam)\n")
    capsys.readouterr()

    expected, _ = reference(stiffness, mass)
    assert eigenvalues_on(page) == pytest.approx(expected, rel=1e-4), page


def test_four_storeys_take_seconds_not_minutes(cell, capsys):
    """81.5 s and 760 KB before. The bound is generous on purpose: it is here to catch the
    closed form coming back, not to measure a machine."""
    sheet, stiffness, mass = building(4)
    started = time.perf_counter()
    raw, page = cell(sheet + "lam = eigenvals(inv(M)*K)\nnumeric(lam)\n")
    elapsed = time.perf_counter() - started
    capsys.readouterr()

    expected, _ = reference(stiffness, mass)
    assert eigenvalues_on(page) == pytest.approx(expected, rel=1e-4), page
    assert elapsed < 15.0, elapsed
    assert len(raw) < 20_000, len(raw)


def test_the_modes_are_the_eigenvectors_of_the_same_problem(cell, capsys):
    """Each mode shape satisfies `A φ = λ φ` for its own eigenvalue, is normalised the way
    the two-storey page already writes one - its last entry `1.00` - and the modes come
    in the order of their eigenvalues."""
    sheet, stiffness, mass = building(3)
    raw, page = cell(sheet + "phi = eigenvects(inv(M)*K)\nnumeric(phi)\n")
    capsys.readouterr()

    numeric = page.rsplit("\\\\[8pt]", 1)[-1]
    blocks = re.findall(
        r"\\lambda=([\d.]+) 1/s²,\\;m=1,\\;\\mathbfv_1=\[\\beginmatrix(.*?)\\endmatrix\]",
        numeric,
    )
    assert len(blocks) == 3, numeric
    expected, vectors = reference(stiffness, mass)
    for (value, body), lam, vector in zip(blocks, expected, vectors.T):
        shape = [float(entry) for entry in re.findall(r"-?[\d.]+", body)]
        assert shape[-1] == 1.0, shape
        assert float(value) == pytest.approx(lam, rel=1e-4)
        assert np.allclose(shape, vector / vector[-1], atol=6e-3), (shape, vector / vector[-1])


def test_the_page_shows_the_problem_and_not_a_formula(cell, capsys):
    """The definition row: the frequency equation for the matrix the sheet built, and no
    root of anything."""
    sheet, _, _ = building(3)
    raw, page = cell(sheet + "lam = eigenvals(inv(M)*K)\n")
    capsys.readouterr()

    definition = raw.rsplit("\\\\[8pt]", 1)[-1]
    assert r"\det" in definition and r"\lambda I" in definition, definition
    assert r"\sqrt" not in definition, definition


def test_the_mode_shapes_show_their_problem_too(cell, capsys):
    """`(A - λ I) v = 0` for `eigenvects`, where an empty set `{}` would otherwise stand."""
    sheet, _, _ = building(3)
    raw, page = cell(sheet + "phi = eigenvects(inv(M)*K)\n")
    capsys.readouterr()

    definition = raw.rsplit("\\\\[8pt]", 1)[-1]
    assert r"\lambda I\right) \mathbf{v} = 0" in definition, definition


def test_a_repeated_eigenvalue_is_counted_once_with_its_multiplicity(cell, capsys):
    """Floating point splits a repeated root by a few parts in 10¹⁶; the page must still
    say `m = 2`, the way SymPy's exact answer does for a matrix of numbers."""
    raw, page = cell("a := 2/s^2\nb := 5/s^2\nA = diag(a, a, b)\nnumeric(eigenvals(A))\n")
    capsys.readouterr()

    numeric = page.rsplit("\\\\[8pt]", 1)[-1]
    assert re.findall(r"\\lambda=([\d.]+) 1/s²,\\;m=(\d)", numeric) == [
        ("2.00", "2"),
        ("5.00", "1"),
    ], numeric


def test_a_unit_asked_for_is_kept_without_a_closed_form_too(cell, capsys):
    """`N/(kg·m)` and not `kN/(kg·m)`: the entries of `inv(M)*K` already carry the second,
    so asking for it converted nothing and a mutant that ignored the request passed."""
    sheet, stiffness, mass = building(3)
    raw, page = cell(sheet + "lam = eigenvals(inv(M)*K)\nnumeric(lam, N/(kg*m))\n")
    capsys.readouterr()

    numeric = page.rsplit("\\\\[8pt]", 1)[-1]
    found = [float(value) for value in re.findall(r"\\lambda=([\d.]+) N/\(kg·m\)", numeric)]
    expected, _ = reference(stiffness, mass)
    assert found == pytest.approx(expected, rel=1e-4), numeric


def test_a_dimensionless_matrix_has_modes_too(cell, capsys):
    """No common unit to take the numbers in: the eigenvalues are plain numbers."""
    raw, page = cell("a := 2\nA = [a, 1, 0; 1, a, 1; 0, 1, a]\nnumeric(eigenvals(A))\n")
    capsys.readouterr()

    numeric = page.rsplit("\\\\[8pt]", 1)[-1]
    found = [float(value) for value in re.findall(r"\\lambda=([\d.]+),", numeric)]
    assert found == pytest.approx(np.sort(np.linalg.eigvals([[2, 1, 0], [1, 2, 1], [0, 1, 2]])), abs=6e-3)


def test_complex_eigenvalues_are_refused_by_name(cell, capsys):
    """A stiffness over a mass never has them. A matrix that does is refused with a
    sentence that says so, not handed on as the real part."""
    raw, page = cell("w := 2/s\nA = [0, -w, 0; w, 0, 0; 0, 0, w]\nnumeric(eigenvals(A))\n")
    printed = capsys.readouterr().out

    assert "complex eigenvalues" in printed, printed


def test_a_name_with_no_value_is_named(cell, capsys):
    raw, page = cell("A = [a, 1, 0; 1, a, 1; 0, 1, a]\nnumeric(eigenvals(A))\n")
    printed = capsys.readouterr().out

    assert "numeric evaluation requires values for: a" in printed, printed


# --- what must not move ---------------------------------------------------------------


def test_two_storeys_keep_their_closed_form(cell, capsys):
    sheet, stiffness, mass = building(2)
    raw, page = cell(sheet + "lam = eigenvals(inv(M)*K)\nnumeric(lam)\n")
    capsys.readouterr()

    assert r"\sqrt" in raw, raw
    expected, _ = reference(stiffness, mass)
    assert eigenvalues_on(page) == pytest.approx(expected, rel=1e-4), page


def test_a_matrix_of_numbers_keeps_its_exact_eigenvalues(cell, capsys):
    raw, page = cell("A = diag(2, 1, 2)\nlam = eigenvals(A)\n")
    capsys.readouterr()

    assert "\\lambda=1,\\;m=1\\; ; \\;\\lambda=2,\\;m=2" in page, page
