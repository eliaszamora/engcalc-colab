r"""One mode at a time: `lam[1]`, `phi[2]`.

`eigenvals(inv(M)*K)` lists every `ω²` a building has, and a memoria then works one mode:

    w_1 = sqrt(lam[1])
    T_1 = 2*pi/w_1

and that was refused - `matrix indexing requires a matrix` - so the period of a mode could
not be computed on the page that found it. The engineer could read `λ = 897.61 1/s²` off
one row and type it into the next, which is the copying a calculation sheet exists to
remove.

**A mode is numbered the way the textbooks number it**: ascending, counting a repeated
eigenvalue as many times as it repeats. The page writes the one it took as `λ₁` - the
closed form of a two-by-two's root would put a quadratic formula inside a square root, and
a three-storey matrix has no closed form at all - and `numeric(...)` computes it from the
numbers. `phi[i]` is that mode's shape, scaled the way the list of modes scales it.

The numbered list and the numbered mode have to agree, so `numeric(lam)` now lists a
closed form's eigenvalues in ascending order too.

The reference values are computed by numpy inside each test.
"""

import re

import numpy as np
import pytest

import engcalc_colab.magic as magic

from conftest import block_text

from test_a_building_with_many_storeys_has_modes import building, reference


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


def last_number(page: str, unit: str) -> float:
    row = page.rsplit("\\\\[8pt]", 1)[-1]
    found = re.findall(r"(-?[\d.]+) " + re.escape(unit) + r" \\endarray", row)
    assert found, row
    return float(found[-1])


def test_the_period_of_the_first_mode(cell, capsys):
    sheet, stiffness, mass = building(3)
    raw, page = cell(
        sheet
        + "lam = eigenvals(inv(M)*K)\n"
        + "w_1 = sqrt(lam[1])\nnumeric(w_1)\n"
        + "T_1 = 2*pi/w_1\nnumeric(T_1)\n"
    )
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    expected, _ = reference(stiffness, mass)
    # To the page's two decimals: 0.198 s reads `0.20 s`, as any period of that size does.
    assert last_number(page, "s") == pytest.approx(2 * np.pi / np.sqrt(expected[0]), abs=5e-3), page
    assert f"{np.sqrt(expected[0]):.2f} 1/s" in page, page
    assert r"\frac{2 \pi}{\sqrt{\lambda_{1}}}" in raw, raw
    # The substitution stage writes the mode's value, the way it writes a name's.
    assert (
        f"\\sqrt({expected[0]:.2f} 1/s²) \\\\[8pt] & = & \\displaystyle "
        f"{np.sqrt(expected[0]):.2f} 1/s"
    ) in page, page


def test_the_page_writes_the_mode_it_took(cell, capsys):
    """`√λ₁`, not a quadratic formula under a root and not the matrix."""
    sheet, _, _ = building(3)
    raw, page = cell(sheet + "lam = eigenvals(inv(M)*K)\nw_2 = sqrt(lam[2])\n")
    capsys.readouterr()

    definition = raw.rsplit("\\\\[8pt]", 1)[-1]
    assert r"w_{2} & = & \displaystyle \sqrt{\lambda_{2}}" in definition, definition


def test_a_mode_shape_is_the_shape_the_list_gives(cell, capsys):
    sheet, stiffness, mass = building(3)
    raw, page = cell(sheet + "phi = eigenvects(inv(M)*K)\nphi_2 = phi[2]\nnumeric(phi_2)\n")
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    row = page.rsplit("\\\\[8pt]", 1)[-1]
    shape = [float(entry) for entry in re.findall(r"-?\d+\.\d+", row)]
    _, vectors = reference(stiffness, mass)
    second = vectors[:, 1] / vectors[-1, 1]
    assert shape == pytest.approx(second, abs=6e-3), row
    # Row first, mode second; and the substitution stage writes each entry's value.
    assert r"\phi_{1,2}" in raw and r"\phi_{3,2}" in raw, raw
    assert raw.count(r"\left(1.00\right)") == 1, raw


def test_a_modal_mass_is_a_product_of_modes(cell, capsys):
    """`φᵀ M φ`, the next line of any modal analysis. It squares the entries of a mode
    shape, and a squared mode entry raised in the printer instead of rendering."""
    sheet, stiffness, mass = building(3)
    raw, page = cell(
        sheet + "phi = eigenvects(inv(M)*K)\nphi_1 = phi[1]\n"
        "M_1 = transpose(phi_1)*M*phi_1\nnumeric(M_1)\n"
    )
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    _, vectors = reference(stiffness, mass)
    first = vectors[:, 0] / vectors[-1, 0]
    assert last_number(page, "kg") == pytest.approx(first @ mass @ first, rel=2e-3), page
    assert r"\phi_{1,1}^{2}" in raw, raw


def test_a_mode_normalised_by_its_first_entry_is_a_fraction(cell, capsys):
    """`phi_1/phi_1[1]`, the other common scaling of a mode. A mode entry that SymPy
    thought non-commutative - it inherits that from the matrix in its arguments - would
    print `φ₂,₁ · 1/φ₁,₁` instead of a fraction."""
    sheet, stiffness, mass = building(3)
    raw, page = cell(
        sheet + "phi = eigenvects(inv(M)*K)\nphi_1 = phi[1]\npsi_1 = phi_1/phi_1[1]\nnumeric(psi_1)\n"
    )
    capsys.readouterr()

    assert r"\frac{\phi_{2,1}}{\phi_{1,1}}" in raw, raw
    _, vectors = reference(stiffness, mass)
    first = vectors[:, 0] / vectors[0, 0]
    row = page.rsplit("\\\\[8pt]", 1)[-1]
    assert [float(entry) for entry in re.findall(r"-?\d+\.\d+", row)] == pytest.approx(first, abs=6e-3), row


def test_the_mode_shapes_of_a_closed_form_are_listed_in_mode_order(cell, capsys):
    raw, page = cell("a := 5/s^2\nb := 2/s^2\nA = diag(a, b)\nphi = eigenvects(A)\nnumeric(phi)\n")
    capsys.readouterr()

    numeric = page.rsplit("\\\\[8pt]", 1)[-1]
    assert re.findall(r"\\lambda=([\d.]+) 1/s²", numeric) == ["2.00", "5.00"], numeric


def test_a_closed_form_in_names_is_numbered_by_its_numbers(cell, capsys):
    """`diag(a, b)` with `a` the larger: SymPy lists `a` first, and the numbers - and
    `lam[1]` - put `b` first."""
    raw, page = cell(
        "a := 5/s^2\nb := 2/s^2\nA = diag(a, b)\nlam = eigenvals(A)\nnumeric(lam)\n"
        "l_1 = lam[1]\nnumeric(l_1)\n"
    )
    capsys.readouterr()

    assert "\\lambda=2.00 1/s²,\\;m=1\\; ; \\;\\lambda=5.00 1/s²,\\;m=1" in page, page
    assert page.rstrip().endswith("2.00 1/s² \\endarray"), page


def test_a_closed_form_is_listed_in_the_order_its_modes_are_numbered(cell, capsys):
    """Two storeys keep their quadratic. `lam[1]` is the smaller root, and the list must
    say the same thing in the same order."""
    sheet, stiffness, mass = building(2)
    raw, page = cell(
        sheet + "lam = eigenvals(inv(M)*K)\nnumeric(lam)\n"
        "l_1 = lam[1]\nnumeric(l_1)\nl_2 = lam[2]\nnumeric(l_2)\n"
    )
    capsys.readouterr()

    listed = [float(value) for value in re.findall(r"\\lambda=([\d.]+) 1/s²", page)]
    taken = [
        float(value)
        for value in re.findall(r"displaystyle ([\d.]+) 1/s² (?:\\\\\[8pt\]|\\endarray)", page)
    ]
    expected, _ = reference(stiffness, mass)
    assert listed == pytest.approx(expected, rel=1e-4), page
    assert taken[-2:] == pytest.approx(expected, rel=1e-4), page


def test_a_repeated_eigenvalue_is_numbered_as_many_times_as_it_repeats(cell, capsys):
    raw, page = cell(
        "a := 2/s^2\nb := 5/s^2\nA = diag(b, a, a)\nlam = eigenvals(A)\n"
        "l_2 = lam[2]\nnumeric(l_2)\nl_3 = lam[3]\nnumeric(l_3)\n"
    )
    capsys.readouterr()

    rows = page.split("l_2")[-1]
    found = re.findall(r"displaystyle ([\d.]+) 1/s² (?:\\\\\[8pt\]|\\endarray)", rows)
    assert found[-2:] == ["2.00", "5.00"], rows


def test_a_matrix_of_numbers_has_numbered_modes_too(cell, capsys):
    """And its exact eigenvalues are listed in the order they are numbered. SymPy's own
    order put `2` before `2 - √2`, so `lam[1]` would have been the second one listed."""
    raw, page = cell("A = [2, 1, 0; 1, 2, 1; 0, 1, 2]\nlam = eigenvals(A)\nnumeric(lam[1])\n")
    printed = capsys.readouterr().out
    assert "engcalc:" not in printed, printed

    assert "\\lambda=2 - \\sqrt2,\\;m=1\\; ; \\;\\lambda=2,\\;m=1\\; ; \\;\\lambda=\\sqrt2 + 2" in page, page
    assert page.rstrip().endswith(f"{2 - np.sqrt(2):.2f} \\endarray"), page


# --- what must be refused -------------------------------------------------------------


def test_a_mode_past_the_last_is_refused(cell, capsys):
    sheet, _, _ = building(3)
    cell(sheet + "lam = eigenvals(inv(M)*K)\nw_4 = sqrt(lam[4])\n")
    printed = capsys.readouterr().out

    assert "mode 4" in printed and "3 modes" in printed, printed


def test_a_mode_takes_one_index(cell, capsys):
    sheet, _, _ = building(3)
    cell(sheet + "phi = eigenvects(inv(M)*K)\nx = phi[1, 2]\n")
    printed = capsys.readouterr().out

    assert "one index" in printed, printed
