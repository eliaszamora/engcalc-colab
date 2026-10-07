r"""What the sixth audit of the chapter 10 fixes found (2026-10-06).

Supports written as stiff springs, k_s from 1e16 to 1e20 kN/m:

- the zero rule measured K's null directions against the median of its columns; with a
  spring on half the degrees of freedom the median is the spring, and every soft mode was
  printed 0 - a pinned column's 9600 and 48000 kN read `[0, 0, 2.5e20]`;
- the window that says two λ are one was measured against the largest λ, the spring's,
  so every soft mode was a repeat of every other: a portal's 3352161 was printed twice
  and 3298107 lost.

Now the soft modes of a positive definite K come from its Cholesky factor, every guard is
measured against the λ it judges, a zero is a λ below its own round-off, and two estimates
that settle on one λ are refused. References: mpmath at 60 digits.
"""

import pathlib

import pytest

SHEETS = pathlib.Path(__file__).parent / "sheets"


def eigenvalues(source: str, unit: str) -> list[float]:
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.parser import parse_cell

    engine = EngineeringEngine()
    for item in parse_cell(source):
        engine.evaluate(item)
    return [float(q.to(unit).magnitude) for q in engine.numeric_context.matrices["l"].entries]


@pytest.mark.parametrize("spring", ["1e+16", "1e+18", "1e+20"])
def test_a_pinned_column_on_springs_keeps_its_soft_modes(spring):
    source = (SHEETS / "pinned_column_springs_1e20.eng").read_text(encoding="utf-8")
    got = eigenvalues(source.replace("k_s := 1e+20[kN/m]", f"k_s := {spring}[kN/m]"), "dimensionless")
    # 12 EI / L² and 60 EI / L² in units of P = 1 kN, and the springs' own.
    assert abs(got[0] - 9600) <= 1e-6 * 9600 and abs(got[1] - 48000) <= 1e-6 * 48000, got
    assert len(got) == 3, got


def test_a_portal_on_springs_with_a_consistent_mass_keeps_each_mode_once():
    got = eigenvalues((SHEETS / "portal_mass_springs_1e20.eng").read_text(encoding="utf-8"), "1/s**2")
    want = [18606.4151294899, 146831.76920108634, 1189288.5135140999, 1798562.6259589416,
            3298106.9134488297, 3352161.0292476523, 7706991.213042639, 9151337.53511818]
    for value, reference in zip(got, want):
        assert abs(value - reference) <= 1e-6 * reference, (got[:8], want)
