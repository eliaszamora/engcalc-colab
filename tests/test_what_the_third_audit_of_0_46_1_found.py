r"""What the third audit of the chapter 10 fixes found (2026-10-06).

- Every pencil went through the best conditioned K + σG. A support modelled as a stiff
  spring makes σ huge, and λ = 1/μ - σ lost the small eigenvalues: `K = diag(1e13, 1, 2)`
  against `G = I` printed 0.00 for 1.00, and a column's ω² with a 1e16 kN/m spring read
  0.00 for 1517.59, in silence - main had them right. Now σ stays 0 when K is well enough
  conditioned, and each λ is the Rayleigh quotient xᵀKx / xᵀGx on the written matrices.
- With a singular G the units of K went unchecked: an entry in kN/m among kN·m printed
  numbers in kN. Refused again, as K's inverse refuses it.
- "The second matrix is zero" was said of a G that is not.
- A bound typed in metres was said in millimetres.
"""

import contextlib
import io
import re

import numpy as np
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


def written(matrix, unit="kN/m") -> str:
    return "; ".join(", ".join(f"{float(value)!r}[{unit}]" for value in row) for row in matrix)


def shown_column(page: str, name: str = "l") -> str:
    return page.split(f"{name} & = &", 1)[1].split(r"\end{array}", 1)[0]


def eigenvalues_shown(page: str) -> list[float]:
    column = shown_column(page).split(r"\operatorname{eigenvals}", 1)[1]
    column = column.replace(r"\rule{0pt}{0.7em}", "")
    values = []
    for mantissa, exponent in re.findall(r"(-?\d+\.\d+)(?: \\times 10\^\{(-?\d+)\})?", column):
        values.append(float(mantissa) * 10 ** int(exponent or 0))
    return values


def test_a_stiff_entry_keeps_the_small_eigenvalues(sheet):
    page, printed = sheet(
        f"K := [{written(np.diag([1e13, 1, 2]))}]\nG := [{written(np.eye(3))}]\nl := eigenvals(K, G)\n"
    )
    assert "engcalc:" not in printed, printed
    assert eigenvalues_shown(page) == [1.0, 2.0, 1e13], page


SHEETS = __import__("pathlib").Path(__file__).parent / "sheets"


@pytest.mark.parametrize("spring", ["1e14", "1e16"])
def test_a_column_with_a_penalty_spring(sheet, spring):
    """The audit's column: four beam elements, masses in kg and kg·m², a lateral support
    as a stiff spring. ω₁² = 1517.59 1/s² by mpmath at 60 digits, whatever the spring."""
    page, printed = sheet((SHEETS / f"column_{spring}.eng").read_text(encoding="utf-8"))
    assert "engcalc:" not in printed, printed
    shown = eigenvalues_shown(page)
    assert abs(shown[0] - 1517.59) <= 0.01, shown
    assert abs(shown[1] - 23798.55) <= 0.01, shown


def test_a_well_conditioned_pencil_is_as_main_had_it(sheet):
    page, printed = sheet(
        "K := [12[kN/m], -6[kN/m]; -6[kN/m], 4[kN/m]]\nG := [1.2[kN/m], -0.1[kN/m]; -0.1[kN/m], 0.13[kN/m]]\n"
        "l := eigenvals(K, G)\n"
    )
    stiffness = np.array([[12, -6], [-6, 4.0]])
    geometric = np.array([[1.2, -0.1], [-0.1, 0.13]])
    for value in sorted(np.linalg.eigvals(np.linalg.solve(geometric, stiffness)).real):
        assert f"{value:.2f}" in shown_column(page), page


def test_units_of_k_are_checked_beside_a_singular_g(sheet):
    _, printed = sheet(
        "K := [2[kN/m], 1[kN/m], 0[kN/m]; 1[kN/m], 3[kN*m], 0[kN]; 0[kN/m], 0[kN], 4[kN/m]]\n"
        "G := [1[1/m], 0, 0[1/m]; 0, 0[m], 0; 0[1/m], 0, 1[1/m]]\nl := eigenvals(K, G)\n"
    )
    assert "engcalc:" in printed and "does not fit" in printed, printed


def test_a_g_that_is_not_zero_is_not_called_zero(sheet):
    _, printed = sheet(
        "K := [1e30[kN/m], 0[kN/m]; 0[kN/m], 1e30[kN/m]]\nG := [1[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m]]\n"
        "l := eigenvals(K, G)\n"
    )
    assert "is zero" not in printed, printed


def test_a_bound_typed_in_metres_stays_in_metres(sheet):
    _, printed = sheet("x := solve(eq(x, 3[m]), x, 0.2[m], 1.5[m])\n")
    assert "0.20 m" in printed and "1.50 m" in printed, printed
    _, printed = sheet("x := solve(eq(x, 3[m]), x, 200[mm], 1.5[m])\n")
    assert "200.00 mm" in printed and "1.50 m" in printed, printed
