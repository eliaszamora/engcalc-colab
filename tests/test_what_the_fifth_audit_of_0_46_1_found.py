r"""What the fifth audit of the chapter 10 fixes found (2026-10-06).

A pencil a little out of symmetry - one entry of the column of the third audit typed
`-24002.4` against its mirror's `-24000` - was never polished, and G⁻¹K's bias beside a
stiff spring went through the check of 1e-14 moves: ω₁² = 1570.18 for 1515.90 with a
1e20 kN/m spring (main read 1512.14), and 1517.58 for 1517.59 with 1e16 (main had it
right). Every pencil is polished now; one that is not symmetric with its two-sided
Rayleigh quotient yᵀKx / yᵀGx. References: mpmath at 60 digits.
"""

import pathlib

import pytest

SHEETS = pathlib.Path(__file__).parent / "sheets"


def eigenvalues(source: str) -> list[float]:
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.parser import parse_cell

    engine = EngineeringEngine()
    for item in parse_cell(source):
        engine.evaluate(item)
    return [float(q.to("1/s**2").magnitude) for q in engine.numeric_context.matrices["l"].entries]


@pytest.mark.parametrize(
    "sheet, expected",
    [
        ("column_asymmetric_1e20.eng", [1515.9002, 23798.554, 107091.50]),
        ("column_asymmetric_1e16.eng", [1517.5933, 23798.554]),
    ],
)
def test_a_pencil_out_of_symmetry_beside_a_stiff_spring(sheet, expected):
    got = eigenvalues((SHEETS / sheet).read_text(encoding="utf-8"))
    for value, want in zip(got, expected):
        assert abs(value - want) <= 2e-7 * want + 1e-4, (got[:3], expected)
