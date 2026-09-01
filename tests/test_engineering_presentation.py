"""RED contracts opening Engineering Presentation.

These encode the three presentation defects P-1, P-2 and P-3 as failing tests
before any production change, which is the discipline the Permanent Quality Gate
exists to enforce.

The contracts are deliberately written to be independent of the display policy
that will eventually be chosen. They assert that the rendered output does not
contradict the value it claims to present, and that a quantity is shown in a unit
of its own dimension. Which length unit a deflection ends up in, and whether the
product adopts engineering notation or significant figures, are separate
decisions; a further contract will pin those once they are approved.

P-1 and P-2 share a root cause in ``renderer._quantity_latex``, which formats with
fixed decimals over the stored unit without rescaling. P-3 does not: the audit
demonstrated that a "never renders as zero" property passes on the P-3 deflection
case, so it needs an oracle of its own.
"""

import re

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_result


_DISPLAYED_MAGNITUDE = re.compile(r"(-?\d+(?:\.\d+)?)\s*\\,")
_UNIT_TOKEN = re.compile(r"\\mathrm\{([^}]*)\}")
_DISPLAYED_PAIR = re.compile(r"(-?\d+(?:\.\d+)?)\s*\\,\s*\\mathrm\{([^}]*)\}")


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def displayed_magnitudes(latex: str) -> list[float]:
    """Every numeric magnitude the reader actually sees attached to a unit."""
    return [float(match) for match in _DISPLAYED_MAGNITUDE.findall(latex)]


def final_stage(latex: str) -> str:
    """The last stage of a rendered derivation: what the reader takes away."""
    return latex.rsplit("=", 1)[-1]


def substitution_stage(latex: str) -> str:
    """The middle stages: the numbers substituted into the symbolic form."""
    return "=".join(latex.split("=")[1:-1])


def displayed_quantities(latex: str, ureg):
    """Every ``magnitude unit`` pair the reader sees, as real quantities."""
    return [
        ureg.Quantity(float(magnitude), unit)
        for magnitude, unit in _DISPLAYED_PAIR.findall(latex)
    ]


# ---------------------------------------------------------------------------
# P-1 HIGH - automatic default rendering collapses a nonzero quantity to zero
# ---------------------------------------------------------------------------


def test_p1_default_rendering_never_shows_a_nonzero_quantity_as_zero():
    """``v := 8e-05*m`` must not render as ``0.00 m``.

    Policy-independent: whatever precision, notation or unit is chosen, a
    quantity that is not zero may not be presented as zero. The reader has no
    way to tell a collapsed value from a genuine one.
    """
    engine = EngineeringEngine()
    result = run_cell(engine, "v := 8e-05*m")[-1]

    assert result.quantity.magnitude != 0.0, "guard: the stored value is nonzero"

    latex = render_result(result)
    shown = displayed_magnitudes(latex)

    assert shown, f"expected a magnitude attached to a unit in: {latex!r}"
    assert all(value != 0.0 for value in shown), (
        f"a nonzero quantity is presented as zero: {latex!r}"
    )


def test_p1_default_rendering_agrees_with_the_value_it_presents():
    """What is shown must be what it is, to within the displayed precision.

    Stronger than the zero check and the real contract behind it: the rendered
    magnitude, read in the rendered unit, must reproduce the stored quantity.
    """
    engine = EngineeringEngine()
    result = run_cell(engine, "v := 8e-05*m")[-1]

    latex = render_result(result)
    tail = final_stage(latex)

    shown = displayed_magnitudes(tail)
    assert len(shown) == 1, f"expected exactly one final magnitude in: {latex!r}"

    units = _UNIT_TOKEN.findall(tail)
    assert units, f"expected a unit in: {latex!r}"

    displayed = engine.numeric_context.ureg.Quantity(shown[0], " * ".join(units))
    assert displayed.to(result.quantity.units).magnitude == pytest.approx(
        result.quantity.magnitude, rel=1e-2
    ), f"the rendered value contradicts the stored value: {latex!r}"


# ---------------------------------------------------------------------------
# P-2 HIGH - the substitution stage prints a nonzero factor as zero
# ---------------------------------------------------------------------------


_COLLAPSED_FACTOR = "v := 8e-05*m\nk = 2*v\nnumeric(k)"


def test_p2_substitution_stage_never_shows_a_nonzero_factor_as_zero():
    """``k = 2v = 2(0.00 m) = 0.00 m`` is a derivation that contradicts itself.

    Distinct site from P-1: this is the substitution printer, reached through
    ``_NumericSubstitutionLatexPrinter``, not the final value. A memoria de
    calculo whose shown steps do not produce its own stated result is worse than
    one that shows no steps at all.
    """
    engine = EngineeringEngine()
    result = run_cell(engine, _COLLAPSED_FACTOR)[-1]

    assert result.quantity.magnitude != 0.0, "guard: the stored value is nonzero"

    latex = render_result(result)
    shown = displayed_magnitudes(latex)

    assert shown, f"expected substituted magnitudes in: {latex!r}"
    assert all(value != 0.0 for value in shown), (
        f"the shown derivation collapses a nonzero factor to zero: {latex!r}"
    )


def test_p2_substituted_factors_agree_with_the_values_they_stand_for():
    """Each substituted factor must be the value of the symbol it replaces.

    Deliberately compared against the stored quantity rather than against the
    assignment's own rendering. Comparing the two renderings passes while both
    are wrong in the same way, which is how a collapsed derivation stays
    internally consistent and still lies.
    """
    engine = EngineeringEngine()
    results = run_cell(engine, _COLLAPSED_FACTOR)

    stored = results[0].quantity
    latex = render_result(results[-1])
    substituted = displayed_quantities(substitution_stage(latex), engine.numeric_context.ureg)

    assert substituted, f"expected substituted factors in: {latex!r}"
    assert any(
        factor.dimensionality == stored.dimensionality
        and factor.to(stored.units).magnitude == pytest.approx(
            stored.magnitude, rel=1e-2
        )
        for factor in substituted
    ), (
        f"no substituted factor stands for the stored value {stored}: "
        f"{[str(factor) for factor in substituted]} in {latex!r}"
    )


# ---------------------------------------------------------------------------
# P-3 MEDIUM - a derived quantity keeps an unreadable compound unit
# ---------------------------------------------------------------------------


_DEFLECTION = """d = P*L^3/(48*E*I_z)
P := 54*kN
L := 5*m
E := 200*GPa
I_z := 1.25e-4*m^4
numeric(d)
"""


def test_p1_inside_a_homogeneous_matrix_keeps_real_zeros_distinguishable():
    """P-1 also lives on the matrix cell path, through ``_magnitude_latex``.

    Found while designing the fix, not by the original audit. A homogeneous
    quantity matrix factors its unit out and renders bare cells, so the collapse
    happens there too - and worse: the matrix below has two genuine zeros and two
    nonzero cells, and renders as four identical ``0.00``. Nothing on the page
    tells the reader a value was lost.
    """
    import engcalc_colab.renderer as renderer
    from engcalc_colab.renderer import RenderSettings

    engine = EngineeringEngine()
    results = run_cell(engine, "d := 8e-05*m\nA = [d, 0; 0, 2*d]\nnumeric(A)")
    quantity_matrix = results[-1].quantity_matrix

    real = [float(quantity.magnitude) for quantity in quantity_matrix]
    assert sorted(value == 0.0 for value in real) == [False, False, True, True], (
        "guard: the matrix must hold two genuine zeros and two nonzero cells"
    )

    latex = renderer._quantity_matrix_latex(quantity_matrix, RenderSettings(precision=2))
    zeros_shown = len(re.findall(r"(?<!\d)0\.00(?!\d)", latex))

    assert zeros_shown == 2, (
        f"a genuine zero and a collapsed value are indistinguishable: {latex!r}"
    )


def test_p3_a_length_is_presented_in_a_unit_of_length():
    """A deflection renders as ``5625.00 kN/(GPa.m)`` instead of a length.

    Policy-independent: the contract is that a quantity whose dimension is a
    length is shown in a single unit of length. Which length unit - metre,
    millimetre - is a separate, approved decision, and this test deliberately
    does not constrain it.

    This is why P-3 is a third contract and not a consequence of the first two.
    The rendered value here is numerically correct, so every "never renders as
    zero" and every value-agreement property passes on it, exactly as the audit
    demonstrated.
    """
    engine = EngineeringEngine()
    result = run_cell(engine, _DEFLECTION)[-1]

    assert result.quantity.check("[length]"), "guard: a deflection is a length"

    latex = render_result(result)
    tail = final_stage(latex)

    assert "\\frac" not in tail, (
        f"a length is presented as a ratio of unrelated units: {tail!r}"
    )

    units = _UNIT_TOKEN.findall(tail)
    assert len(units) == 1, (
        f"a length must be shown in one unit, not {units!r}: {tail!r}"
    )

    shown_unit = engine.numeric_context.ureg.Unit(units[0])
    assert shown_unit.dimensionality == result.quantity.units.dimensionality, (
        f"the shown unit is not a unit of the quantity's own dimension: {tail!r}"
    )


def test_p3_is_not_detected_by_the_p1_and_p2_contracts():
    """Demonstrates that P-3 needs its own oracle.

    The deflection renders a correct number in a correct unit, so it satisfies
    both the zero contract and the value-agreement contract while remaining
    unreadable. Recorded as a test so the distinction cannot be lost by someone
    later folding the three defects into one property.

    This one is GREEN today and must stay GREEN after the fix, so it is compared
    at display precision. A tighter tolerance passes only while the deflection
    renders as an exact 5625.00 and fails the moment it renders as a rounded
    5.63 mm - which is the fix working. Measured, not anticipated.
    """
    engine = EngineeringEngine()
    result = run_cell(engine, _DEFLECTION)[-1]

    latex = render_result(result)
    tail = final_stage(latex)
    shown = displayed_magnitudes(tail)

    assert len(shown) == 1
    assert shown[0] != 0.0, "P-3 is not a zero-collapse defect"

    units = _UNIT_TOKEN.findall(tail)
    displayed = engine.numeric_context.ureg.Quantity(shown[0], units[0])
    for unit in units[1:]:
        displayed = displayed / engine.numeric_context.ureg.Unit(unit)

    assert displayed.dimensionality == result.quantity.dimensionality
    assert displayed.to(result.quantity.units).magnitude == pytest.approx(
        result.quantity.magnitude, rel=1e-2
    ), "P-3 is not a value-agreement defect: the number shown is correct"
