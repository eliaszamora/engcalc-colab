r"""A moment computed out of a stress and a volume is still a moment.

RC-2B from the external reinforced-concrete trial. A flexural capacity written the way
anyone writes it,

    phiMn = phi*As*fy*z

comes out carrying `MPa*mm^3`, and the memoria said `2.84 x 10^8 MPa*mm^3` for
`284.30 kN*m`. The value is right and the unit is one nobody types.

Two causes, and the second was only found by tracing a fix that did not work.

The first is the one that reads like the whole story. `_unit_is_the_engineers` decides
whether a unit came from what was typed or from the algebra by comparing how much unit
the reader has to hold, and

    MPa * mm^3   ->  2 symbols
    kN * m       ->  2 symbols

tied, so the unit already there won. Counting symbols misses that `mm^3` is a cube. The
count is now weighted by exponent, which is the same idea the function was already
about, and it still compares against the family's own canonical member rather than an
absolute limit:

    MPa * mm^3   ->  1 + 3 = 4      kN * m   ->  1 + 1 = 2      replaced
    kgf * cm     ->  1 + 1 = 2      kN * m   ->  2              kept
    mm^4         ->  4              cm^4     ->  4              kept

Weighting the count changed nothing, which is how the second cause turned up. The family
table was keyed on `str(quantity.dimensionality)`, and that string is not stable: Pint
caches one dimensionality object per unit combination and prints its dimensions in the
order the first computation to reach it happened to build them. The capacity came out as

    [length] ** 2 * [mass] / [time] ** 2

in a session that had computed nothing else, missing the moment family entirely, and as

    [mass] * [length] ** 2 / [time] ** 2

in a session where anything had already touched that dimensionality, finding it. Same
sheet, two different units in the memoria, decided by what ran before. The table is now
keyed on the sorted pairs, which cannot be ordered two ways.

Everything after those two is a unit an engineer writes on purpose. They are the reason
this is a weighting and not a rule that simply prefers the family.
"""

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.renderer import _unit_family


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


CAPACITY = (
    "fy := 413.6854*MPa\n"
    "As := 1935.48*mm**2\n"
    "z := 394.53*mm\n"
    "phi := 0.9\n"
    "phiMn = phi*As*fy*z\n"
)


def test_a_capacity_from_stress_and_volume_reads_as_a_moment(cell):
    """The reported defect. 0.9 x 1935.48 mm^2 x 413.6854 MPa x 394.53 mm = 284.30 kN*m."""
    final = _final(cell(CAPACITY + "numeric(phiMn)\n"))
    assert "284.30" in final, final
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final
    assert "MPa" not in final, final


def test_the_family_lookup_does_not_depend_on_how_the_dimensionality_prints():
    """The real cause, and the one a `numeric(...)` contract cannot see.

    The table was keyed on `str(quantity.dimensionality)`. Pint caches one dimensionality
    object per unit combination and prints its dimensions in whatever order the first
    computation to reach it happened to build them, so the same capacity was

        [length] ** 2 * [mass] / [time] ** 2      (missed the family)
        [mass] * [length] ** 2 / [time] ** 2      (found it)

    depending on what the notebook had computed earlier in the session. Two runs of one
    sheet, two different units in the memoria.

    Passing the pairs in a deliberately awkward order is the whole test: a lookup that
    reads them as a set cannot be ordered two ways.
    """
    class _Quantity:
        def __init__(self, dimensionality):
            self.dimensionality = dimensionality

    moment = dict([("[time]", -2), ("[mass]", 1), ("[length]", 2)])
    assert _unit_family(_Quantity(moment)) == ("kN * m",)

    pressure = dict([("[time]", -2), ("[length]", -1), ("[mass]", 1)])
    assert _unit_family(_Quantity(pressure)) == ("MPa", "GPa")

    assert _unit_family(_Quantity({"[length]": 3})) == ()


def test_a_fresh_session_computing_only_the_capacity_still_reads_kn_m():
    """End to end in an interpreter that has computed nothing else.

    This is the run that failed. Every in-process contract here shares one registry with
    every test that ran before it, so by the time one of them reaches a moment the
    ordering has long been decided by something else. A subprocess is the only way to
    ask the question the notebook asks.
    """
    import subprocess
    import sys
    import textwrap

    program = textwrap.dedent(
        """
        import matplotlib; matplotlib.use("Agg")
        import engcalc_colab.magic as magic
        captured = []
        magic.display = captured.append
        magic.EngMagics().eng("", (
            "fy := 413.6854*MPa\\n"
            "As := 1935.48*mm**2\\n"
            "z := 394.53*mm\\n"
            "phi := 0.9\\n"
            "phiMn = phi*As*fy*z\\n"
            "numeric(phiMn)\\n"
        ))
        print("".join(getattr(o, "data", "") for o in captured))
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, timeout=180
    )
    assert result.returncode == 0, result.stderr
    assert "284.30" in result.stdout, result.stdout
    assert "MPa" not in result.stdout.split("& = &")[-1], result.stdout


def test_a_moment_written_in_kgf_cm_is_left_alone(cell):
    """A real unit, typed on purpose, and no more to hold than `kN*m`."""
    final = _final(cell("M := 1000*kgf*cm\nnumeric(M)\n"))
    assert "1000.00" in final and r"\mathrm{kgf}" in final, final


def test_a_moment_written_in_n_mm_is_left_alone(cell):
    final = _final(cell("M := 1e6*N*mm\nnumeric(M)\n"))
    assert r"\mathrm{N}" in final and r"\mathrm{mm}" in final, final
    assert r"\mathrm{kN} \cdot \mathrm{m}" not in final, final


def test_a_force_in_tonf_is_left_alone(cell):
    """The case the function was written for. One symbol against the family's one."""
    final = _final(cell("P := 5*tonf\nnumeric(P)\n"))
    assert "5.00" in final and r"\mathrm{tonf}" in final, final


def test_a_stiffness_in_kn_per_mm_is_left_alone(cell):
    final = _final(cell("k := 12*kN/mm\nnumeric(k)\n"))
    assert "12.00" in final and r"\frac{\mathrm{kN}}{\mathrm{mm}}" in final, final


def test_a_second_moment_of_area_in_mm4_is_left_alone(cell):
    """Weighting by exponent makes `mm^4` cost four, and the family's `cm^4` costs four too.

    A rule that weighted exponents without comparing against the family's own would
    have moved every inertia an engineer writes in mm^4.
    """
    final = _final(cell("I := 80e6*mm**4\nnumeric(I)\n"))
    assert r"\mathrm{mm}^{4}" in final, final


def test_a_stress_from_force_over_area_reads_as_mpa(cell):
    """Exponents are counted by magnitude, and this is the case that says why.

    `kN/mm^2` is one symbol up and one down. Summed with their signs those cancel to
    zero, which is less than the family's `MPa`, so the unit the algebra produced would
    look simpler than the unit an engineer reads and a 500 MPa stress would print as
    `0.50 kN/mm^2`. Burden does not cancel: a denominator is still something to hold.
    """
    final = _final(cell("P := 100*kN\nA := 200*mm**2\nsigma = P/A\nnumeric(sigma)\n"))
    assert "500.00" in final and r"\mathrm{MPa}" in final, final


def test_the_deflection_still_reaches_millimetres(cell):
    """P-3, the case the family selection exists for, must not move."""
    final = _final(cell(
        "L := 6*m\nq := 10*kN/m\nE := 200*GPa\nI := 80e6*mm**4\n"
        "d = 5*q*L^4/(384*E*I)\nnumeric(d)\n"
    ))
    assert "10.55" in final and r"\mathrm{mm}" in final, final


def test_a_declared_compound_is_still_the_engineers(cell):
    """What the engineer typed on a `:=` line is kept, as everywhere else."""
    latex = cell("W := 2.84e8*MPa*mm**3\n")
    assert "MPa" in latex, latex
