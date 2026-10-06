r"""A value too large for a float is refused with a message, not a traceback.

    K := zeros(40, 40) + 1e9*identity(40)
    D_0 := det(K)

The determinant is 10^360, worked out exactly by mpmath and then handed to a float, which
holds up to 1.8 × 10^308: it became `inf` and the printer raised `OverflowError` out of the
cell (his book, chapter 10: a 38 x 38 stiffness matrix in newtons). `x := 1e300*1e300` and
`x := 10^400` crashed the same way. Each now stops the cell with `engcalc:` and a sentence
naming the value, as any other refusal does, and the lines above it are still shown.
`x = 1e300*1e300` printed `inf`: SymPy holds the exact number, so it is written in powers
of ten.
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


@pytest.mark.parametrize(
    "line",
    [
        "D_0 := det(K)",
        "x := 1e300*1e300",
        "x := -1e300*1e300",
        "x := 10^400",
        "x := 1e300[N]*1e300[m]",
    ],
)
def test_the_line_is_refused_and_says_why(sheet, line):
    page, printed = sheet("K := zeros(40, 40) + 1e9*identity(40)\na := 2[m]\n" + line + "\n")
    assert "engcalc:" in printed, printed
    assert "too large" in printed, printed
    assert "a & = &" in page, page  # the lines above are still shown
    assert "inf" not in page, page


def test_a_formula_line_holds_it_exactly_and_writes_it(sheet):
    # SymPy keeps `1e600` as a number; only the printer's float read it as `inf`.
    page, printed = sheet("x = 1e300*1e300\n")
    assert "engcalc:" not in printed, printed
    assert r"1.00 \times 10^{600}" in page and "inf" not in page, page


def test_a_determinant_says_its_size(sheet):
    _, printed = sheet("K := zeros(40, 40) + 1e9*identity(40)\nD_0 := det(K)\n")
    assert "det" in printed and "10^360" in printed, printed


def test_a_large_determinant_that_fits_is_shown(sheet):
    page, printed = sheet("K := zeros(30, 30) + 1e9*identity(30)\nD_0 := det(K)\n")
    assert "engcalc:" not in printed, printed
    assert "10^{270}" in page, page
