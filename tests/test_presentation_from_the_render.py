"""Three presentation defects found by rendering a memoria and reading it.

None was found by a test, because every test here asserts that a LaTeX string contains a
substring and all three produce strings with the right substrings in them. They were
found by `tools/render_memoria.py` and a pair of eyes.

- `I_z := 80e6*mm**4` printed as `80000000.00 mm^4`. Eight zeros nobody writes or counts.
- `eqFy` printed in italic, which MathJax spaces as a product: `e q F y`.
- a wrapped product began its continuation with `\\cdot`, and once large magnitudes
  became `8.00 \\cdot 10^7` that line read `\\cdot 1/(8.00 \\cdot 10^7 mm^4)` - the same
  mark carrying two meanings four characters apart.
"""

import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import (
    RenderSettings,
    _latex,
    _magnitude_text,
    render_aligned_results,
)


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def rendered(source: str) -> str:
    engine = EngineeringEngine()
    results = [result for result in run_cell(engine, source) if result is not None]
    return render_aligned_results(results)


def test_a_second_moment_of_area_is_not_eight_zeros():
    latex = rendered("I_z := 80e6*mm**4")

    assert "80000000" not in latex
    assert r"8.00 \times 10^{7}" in latex, latex
    # The unit the engineer declared is kept. Converting to cm^4 would also remove the
    # zeros and would overrule a choice they made on the page.
    assert r"\mathrm{mm}^{4}" in latex


def test_a_steel_modulus_in_megapascals_is_left_alone():
    """This is why the ceiling is a million and not a hundred thousand.

    `200000 MPa` is how a steel modulus is written. Rendering it `2.00 x 10^5 MPa` would
    be a worse reading than the problem being fixed, so the threshold has to sit above
    it. Without this contract, tightening the ceiling looks free.
    """
    settings = RenderSettings()
    assert _magnitude_text(200000.0, settings) == "200000.00"
    assert _magnitude_text(999999.0, settings) == "999999.00"
    assert r"\times" in _magnitude_text(1e6, settings)


def test_the_floor_case_still_falls_back_and_ordinary_numbers_do_not():
    """P-1 from the other side, and the band in between left untouched."""
    settings = RenderSettings()
    assert r"\times 10^{-5}" in _magnitude_text(1.05e-5, settings)
    for magnitude in (6.0, 45.0, 10.55, 12566.37, 0.02):
        assert r"\times" not in _magnitude_text(magnitude, settings)


def test_a_multi_letter_name_is_one_name_and_not_a_product():
    assert _latex(sp.Symbol("eqFy")) == r"\mathrm{eqFy}"
    assert _latex(sp.Symbol("Lk")) == r"\mathrm{Lk}"


def test_greek_names_are_still_greek():
    """The rule tests what SymPy already made of the base, so `theta` stays a theta.

    Uprighting every multi-letter base without that check turns every angle in a stress
    transformation into the upright word "theta".
    """
    assert _latex(sp.Symbol("theta")) == r"\theta"
    assert _latex(sp.Symbol("sigma_1")) == r"\sigma_{1}"
    assert _latex(sp.Symbol("phi_Mn")) == r"\phi_{Mn}"


def test_single_letters_and_their_subscripts_are_unchanged():
    """Only the base is touched, and only when it is more than one letter.

    A quantity is a single italic letter, which is the whole convention; `d_{max}` in
    italic is near-universal in practice and changing it would churn every name in the
    project for a defect nobody reported.
    """
    assert _latex(sp.Symbol("x")) == "x"
    assert _latex(sp.Symbol("R_A")) == "R_{A}"
    assert _latex(sp.Symbol("d_max")) == "d_{max}"
    assert _latex(sp.Symbol("I_z")) == "I_{z}"


def test_the_reactions_block_reads_as_names_rather_than_products():
    latex = rendered(
        "L := 6*m\n"
        "q := 10*kN/m\n"
        "eqFy = eq(R_A + R_B, q*L)\n"
        "eqMA = eq(R_B*L, q*L*L/2)\n"
        "solve(eqFy, eqMA, R_A, R_B)"
    )
    assert r"\mathrm{eqFy}" in latex
    assert r"\mathrm{eqMA}" in latex


def test_a_power_of_ten_and_a_wrapped_product_use_different_marks():
    """The two meanings must not share a glyph.

    A wrapped product starts its continuation with `\\cdot`, which is a contracted
    choice and stays. Once large magnitudes started rendering in scientific notation,
    a continuation line read `\\cdot 1/(8.00 \\cdot 10^7 mm^4)` and the reader had no way
    to tell the break marker from the power of ten. Scientific notation now uses
    `\\times`, which is its conventional mark anyway.
    """
    latex = rendered(
        "L := 6*m\n"
        "q := 10*kN/m\n"
        "E := 200*GPa\n"
        "I_z := 80e6*mm**4\n"
        "d = 5*q*L^4/(384*E*I_z)\n"
        "numeric(d)"
    )

    assert r"\times 10^{7}" in latex, latex
    assert r"\quad \cdot " in latex, latex
    # The continuation carries the break mark and the power of ten, and they differ.
    continuation = [row for row in latex.split(r"\\") if r"\quad \cdot" in row]
    assert continuation, latex
    assert r"\times" in continuation[0]
    assert continuation[0].count(r"\cdot") == 1, continuation[0]
