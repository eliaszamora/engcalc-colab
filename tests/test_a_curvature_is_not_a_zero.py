r"""A curvature reads in `1/m`, and is never a zero it is not.

The reference sheet `formas.eng`, rendered with no palette:

    κ  =  M_u / (E I)
       =  (183.60 kN·m) / ((23500.00 MPa) (5.40×10⁹ mm⁴))
       =  0.00 kN·m/(MPa·mm⁴)

The curvature is 1.45×10⁻³ 1/m. `kN·m/(MPa·mm⁴)` is 10⁹ per metre, so the magnitude it
arrives with is 1.45e-12, under the zero tolerance, and the page printed a zero. With `E`
in GPa the same curvature is above the tolerance and reads `2.81×10⁻⁹ kN·m/(GPa·mm⁴)` -
the right number, in a unit no reader can use.

**Why.** A curvature is `[length]⁻¹`, and no family table held that dimension. With no
family, `_unit_is_the_engineers` has no shape to compare against and answers True for
anything - so the four-factor unit the algebra built was treated as one the engineer
wrote, and a value the engineer writes is judged zero in its own unit. That is the rule
`test_a_deflection_is_not_a_zero` exists to keep away from units nobody wrote.

**So the dimension gets its family**: `1/m` on an SI or metric-technical sheet - a length
is a metre in both - and `1/in` on a US customary one, where the curvature of a section
is written per inch. One member each, the way time has one: `1/mm` would win nothing a
reader wants, and a band rule choosing between them would only move the digits.

A curvature somebody typed - `kappa := 0.003/m` - is kept as typed, and a palette still
decides before any of this (#156: `1/cm` on a kgf sheet).
"""

import pytest

import engcalc_colab.magic as magic

from conftest import block_text


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str, *, palette: str = "") -> str:
        magics = magic.EngMagics()
        captured.clear()
        if palette:
            magics.eng_units(palette)
            captured.clear()
        magics.eng("", source)
        return block_text("".join(str(getattr(obj, "data", "")) for obj in captured))

    return run


def final(page: str) -> str:
    """The last `= value` row of the working."""
    return page.split("&=&")[-1] if "&=&" in page else page.split("& = & \\displaystyle")[-1]


FORMAS = (
    "b := 300*mm\nh := 600*mm\nE := 23500*MPa\n"
    "keep I = b*h^3/12\nM_u := 183.6*kN*m\n"
    "keep kappa = M_u/(E*I)\nreport(kappa)\nsummary()\n"
)


def test_the_reference_sheet_s_curvature_is_not_a_zero(cell, capsys):
    """The page it came from: through the working and through the summary."""
    page = cell(FORMAS)
    capsys.readouterr()

    assert "0.00145 1/m" in page, page
    assert page.rstrip().endswith("\\kappa 0.00145 1/m"), page
    assert "MPa·mm⁴" not in page.split("5.40×10⁹ mm⁴)")[-1], page


def test_a_curvature_above_the_tolerance_reads_per_metre_too(cell, capsys):
    """`E` in GPa: never a zero, and still `kN·m/(GPa·mm⁴)` - the half of the defect that
    printed a true number nobody could read."""
    page = cell("E := 200*GPa\nI := 8e7*mm^4\nM := 45*kN*m\nkappa = M/(E*I)\nnumeric(kappa)\n")
    capsys.readouterr()

    assert final(page).strip().endswith("0.00281 1/m \\endarray"), page


def test_a_sheet_in_kilogram_force_reads_per_metre(cell, capsys):
    """Metric-technical with no palette. A length is a metre in both systems."""
    page = cell(
        "E := 2.1e6*kgf/cm^2\nI := 540000*cm^4\nM := 18700*kgf*m\n"
        "kappa = M/(E*I)\nnumeric(kappa)\n"
    )
    capsys.readouterr()

    # 1.87e6 kgf·cm / (2.1e6 kgf/cm² · 540000 cm⁴) = 1.65e-6 per cm
    assert final(page).strip().endswith("0.000165 1/m \\endarray"), page


def test_a_sheet_in_tonnes_force_reads_per_metre(cell, capsys):
    """The metric-technical table is only asked when a force survives the division. With
    `kgf` above and below it cancels and the sheet reads as SI - which is why a mutant
    removing the technical entry passed the test above. A moment in `tonf·m` over a
    modulus in `kgf/cm²` keeps both forces, so this one reaches it."""
    page = cell(
        "E := 2.1e6*kgf/cm^2\nI := 540000*cm^4\nM := 18.7*tonf*m\n"
        "kappa = M/(E*I)\nnumeric(kappa)\n"
    )
    capsys.readouterr()

    assert final(page).strip().endswith("0.000165 1/m \\endarray"), page


def test_a_sheet_in_us_customary_units_reads_per_inch(cell, capsys):
    """`kip·ft/(ksi·in⁴)` is a curvature per inch times twelve."""
    page = cell("E := 29000*ksi\nI := 1500*inch^4\nM := 300*kip*ft\nkappa = M/(E*I)\nnumeric(kappa)\n")
    capsys.readouterr()

    assert final(page).strip().endswith("1/in \\endarray"), page
    assert "8.28×10⁻⁵ 1/in" in page or "0.0000828 1/in" in page, page


# --- what must not move ---------------------------------------------------------------


def test_a_curvature_somebody_typed_is_kept(cell, capsys):
    page = cell("kappa := 0.003/m\nnumeric(kappa)\n")
    capsys.readouterr()

    assert final(page).strip().endswith("0.003 1/m \\endarray"), page


def test_a_palette_still_decides(cell, capsys):
    """#156's derivation: `1/cm` on a kgf sheet, before any family is asked."""
    page = cell(FORMAS, palette="kgf")
    capsys.readouterr()

    assert "1/cm" in page and "1/m " not in page, page
