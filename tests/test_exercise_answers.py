"""The gap map's exercises, checked against answers worked by hand.

`tools/gap_map.py` catches exceptions and nothing else. "15 of 18 exercises run end to
end" has always meant "15 raise no exception" - never that any of them is right. An
exercise can run perfectly and return a number that is wrong by a factor of a thousand,
or the right number with the wrong sign, and the gap map reports it as a success.

This file closes that. Every expected value below is worked from the statics rather than
read off a run, which is the difference between Level A evidence and asking the solver to
grade itself. Where a textbook formula exists it is quoted as a second, independent
check: a propped cantilever's prop reaction is 3qL/8 whatever EngCalc thinks, and a
simply supported UDL deflects 5qL^4/(384EI).

Exercises E5 and E12 are absent because they do not run: both need `check`, which the
project declined. E10 joined this file when `case`/`combo` was built.
"""

import math
import pathlib
import sys

import pytest
import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from gap_map_exercises import EXERCISES  # noqa: E402


def run_exercise(title_starts_with: str):
    """Run one exercise exactly as the gap map does, and keep engine and results."""
    source = next(
        source
        for title, _area, source in EXERCISES
        if title.startswith(title_starts_with + " ")
    )
    engine = EngineeringEngine()
    results = []
    for line in [ln for ln in source.strip().splitlines() if ln.strip()]:
        for item in parse_cell(line):
            if isinstance(item, ParsedHeading):
                continue
            results.append(engine.evaluate(item))
    return engine, [result for result in results if result is not None]


def value_of(engine, name: str, unit: str) -> float:
    """The numeric magnitude of a name defined in the symbolic namespace."""
    context = engine.numeric_context
    expression = engine.namespace[name]
    _substitutions, quantity = context.evaluate_symbolic(
        expression, overrides=context.unit_literal_overrides(expression)
    )
    return float(quantity.to(unit).magnitude)


def function_at(engine, name: str, argument, unit: str) -> float:
    """Evaluate a user function at one value of its parameter."""
    context = engine.numeric_context
    function = engine.functions[name]
    # From the engine, not `sp.Symbol(...)`: a definition captures its symbols with the
    # assumptions in force, and a bare symbol of the same name is a different symbol.
    variable = engine.resolve_symbol(function.parameters[0])
    expression = function.expression.subs(variable, sp.sympify(argument))
    _substitutions, quantity = context.evaluate_symbolic(
        expression, overrides=context.unit_literal_overrides(expression)
    )
    return float(quantity.to(unit).magnitude)


def test_e1_a_symmetric_span_shares_its_load_equally():
    """L = 6 m, q = 10 kN/m. Total 60 kN, split evenly: 30 kN each."""
    engine, results = run_exercise("E1")
    assert dict(results[-1].solutions).keys() == {"R_A", "R_B"}

    assert value_of(engine, "R_A", "kN") == pytest.approx(30.0)
    assert value_of(engine, "R_B", "kN") == pytest.approx(30.0)


def test_e2_a_point_load_off_centre_shifts_the_reactions():
    """L = 8 m, P = 40 kN at a = 3 m, q = 12 kN/m.

    Total = 40 + 96 = 136 kN. Moments about A: R_B*8 = 40*3 + 12*64/2 = 504, so
    R_B = 63 kN and R_A = 73 kN. The two differ, which is the point: a contract with a
    symmetric span cannot tell the reactions apart if they were ever swapped.
    """
    engine, _results = run_exercise("E2")
    assert value_of(engine, "R_A", "kN") == pytest.approx(73.0)
    assert value_of(engine, "R_B", "kN") == pytest.approx(63.0)


def test_e3_the_diagonal_carries_the_load_and_the_chord_takes_the_thrust():
    """P = 20 kN, theta = 30 deg.

    F_AB*sin(30) = 20 gives F_AB = 40 kN, and F_AB*cos(30) + F_AC = 0 gives
    F_AC = -20*sqrt(3) = -34.64 kN. The sign matters and is asserted: a chord in
    compression reported as tension is the kind of error that reaches a drawing.
    """
    engine, _results = run_exercise("E3")
    assert value_of(engine, "F_AB", "kN") == pytest.approx(40.0)
    assert value_of(engine, "F_AC", "kN") == pytest.approx(-20 * math.sqrt(3))


def test_e4_double_integration_reproduces_the_textbook_deflection():
    """The elastic curve derived from scratch must agree with 5qL^4/(384EI).

    L = 6 m, q = 10 kN/m, EI = 200 GPa * 80e6 mm^4 = 16000 kN*m^2, so the midspan
    deflection is 5*10*1296/(384*16000) = 10.547 mm, downward.

    Two independent routes to the same number: the exercise integrates V twice and
    solves for both constants of integration, and the closed form comes from a textbook.
    Agreement between them is what makes this Level A rather than a solver agreeing
    with itself.
    """
    engine, results = run_exercise("E4")

    closed_form = 5 * 10 * 6 ** 4 / (384 * 16000)
    assert results[-1].quantity.to("mm").magnitude == pytest.approx(
        -closed_form * 1000, rel=1e-9
    )
    assert closed_form * 1000 == pytest.approx(10.546875)

    # C2 = 0 from v(0) = 0, and C1 = -90/(EI) from v(L) = 0.
    assert sp.sympify(engine.namespace["C2"]) == 0


def test_e6_the_macaulay_moment_peaks_under_the_load_and_closes_at_the_far_end():
    """L = 8 m, P = 40 kN at a = 3 m. R_A = 40*5/8 = 25 kN.

    M(3) = 25*3 = 75 kN*m, and M(8) = 25*8 - 40*5 = 0. The second is the real test of
    the bracket: before x = a the term must contribute nothing, and after it must
    contribute exactly P*(x - a). A bracket that stayed switched off would still give
    the peak and would leave 200 kN*m hanging at a free end.
    """
    engine, _results = run_exercise("E6")

    assert function_at(engine, "M", "3*m", "kN*m") == pytest.approx(75.0)
    assert function_at(engine, "M", "8*m", "kN*m") == pytest.approx(0.0, abs=1e-9)
    assert function_at(engine, "M", "2*m", "kN*m") == pytest.approx(50.0)


def test_e7_the_composite_centroid_and_second_moment():
    """A1 = 300x100 = 30000 mm^2 at 450 mm, A2 = 100x400 = 40000 mm^2 at 200 mm.

    y_bar = (30000*450 + 40000*200)/70000 = 307.143 mm.
    I = 300*100^3/12 + 30000*142.857^2  +  100*400^3/12 + 40000*107.143^2
      = 637.24e6 + 992.52e6 = 1629.76e6 mm^4.
    """
    engine, results = run_exercise("E7")

    y_bar = 21.5e6 / 70000
    assert y_bar == pytest.approx(307.142857, rel=1e-6)
    assert value_of(engine, "y_bar", "mm") == pytest.approx(y_bar)

    i_1 = 300 * 100 ** 3 / 12 + 30000 * (450 - y_bar) ** 2
    i_2 = 100 * 400 ** 3 / 12 + 40000 * (200 - y_bar) ** 2
    assert results[-1].quantity.to("mm**4").magnitude == pytest.approx(i_1 + i_2)
    assert (i_1 + i_2) == pytest.approx(1.6297619e9, rel=1e-6)


def test_e8_principal_stresses_and_the_angle_that_reaches_them():
    """sx = 80, sy = 20, txy = 30 MPa.

    Centre 50, radius sqrt(30^2 + 30^2) = 30*sqrt(2) = 42.426, so the principal
    stresses are 92.43 and 7.57 MPa. tan(2*theta_p) = 60/60 = 1, so theta_p = 22.5 deg -
    checked in degrees, because the exercise asks for degrees and a result silently in
    radians would read as a plausible 0.3927.
    """
    engine, results = run_exercise("E8")

    radius = 30 * math.sqrt(2)
    assert value_of(engine, "s1", "MPa") == pytest.approx(50 + radius)
    assert value_of(engine, "s2", "MPa") == pytest.approx(50 - radius)
    assert results[-1].quantity.to("deg").magnitude == pytest.approx(22.5)


def test_e9_the_prop_reaction_matches_three_eighths_of_the_load():
    """L = 6 m, q = 20 kN/m. The flexibility method must land on 3qL/8 = 45 kN.

    The exercise never mentions that formula: it integrates M_0*M_1 and M_1^2 and divides.
    Arriving at the textbook value from the virtual-work route is the check.
    """
    engine, results = run_exercise("E9")

    assert results[-1].quantity.to("kN").magnitude == pytest.approx(45.0)
    assert 3 * 20 * 6 / 8 == 45.0
    textbook = 3 * engine.resolve_symbol("L") * engine.resolve_symbol("q") / 8
    assert sp.simplify(sp.sympify(engine.namespace["V_B"]) - textbook) == 0


def test_e11_the_heavier_combination_governs_the_whole_span():
    """M_U1 = 14.4*x*(6-x) against M_U2 = 5.6*x*(6-x).

    1.2D + 1.6L is larger than 1.4D everywhere the moment is nonzero, so one
    combination governs the entire span and the envelope is that combination. A
    governing report that split the span would mean the crossover search invented a
    boundary where the two curves only touch, at the supports.
    """
    engine, results = run_exercise("E11")
    governing = results[-1]

    assert len(governing.intervals) == 1
    assert governing.intervals[0].label == "M_U1(x)"
    assert function_at(engine, "M_U1", "3*m", "kN*m") == pytest.approx(14.4 * 9)
    assert function_at(engine, "M_U2", "3*m", "kN*m") == pytest.approx(5.6 * 9)


def test_e13_the_required_second_moment_for_a_span_over_300_limit():
    """5qL^4/(384EI) = L/300 solved for I.

    d_adm = 6/300 = 0.02 m, so I = 5*10e3*1296/(384*200e9*0.02) = 4.21875e-5 m^4,
    which is 42.19e6 mm^4. Checked in mm^4 because that is the unit a section table
    is written in, and a result of 4.2e-5 with the right dimension would pass a laxer
    assertion while being unusable.
    """
    _engine, results = run_exercise("E13")

    required = 5 * 10e3 * 6 ** 4 / (384 * 200e9 * 0.02)
    assert required == pytest.approx(4.21875e-5, rel=1e-9)
    assert results[-1].quantity.to("mm**4").magnitude == pytest.approx(
        42187500.0, rel=1e-9
    )


def test_e14_the_euler_length_is_four_pi_metres():
    """E*I = 200 GPa * 40e6 mm^4 = 8000 kN*m^2, so pi^2*EI/L^2 = 500 kN gives
    L = pi*sqrt(8000/500) = 4*pi = 12.566 m."""
    _engine, results = run_exercise("E14")
    assert results[-1].quantity.to("m").magnitude == pytest.approx(4 * math.pi, rel=1e-9)


def test_e15_the_moment_exceeds_its_limit_between_three_minus_and_plus_root_five():
    """5x(6-x) > 20 is x^2 - 6x + 4 < 0, so 3 - sqrt(5) < x < 3 + sqrt(5)."""
    _engine, results = run_exercise("E15")
    interval = results[-1].intervals[0]

    assert interval.lower_quantity.to("m").magnitude == pytest.approx(3 - math.sqrt(5))
    assert interval.upper_quantity.to("m").magnitude == pytest.approx(3 + math.sqrt(5))
    assert not interval.lower_closed and not interval.upper_closed


def test_e16_a_declared_positive_length_simplifies_out_of_its_square_root():
    """sqrt(L^2) is |L|, and only becomes L because the sheet said L > 0.

    Asserted as `L` rather than as "something simpler": without the assumption SymPy
    returns Abs(L), which is also a correct simplification and a different answer.
    """
    _engine, results = run_exercise("E16")
    assert sp.sympify(results[-1].value) == sp.Symbol("L", positive=True)


def test_e17_the_evaluated_sum_of_five_loads():
    """sum(P*i, i, 1, 5) = P*15 = 150 kN. The arithmetic series, not five times P."""
    _engine, results = run_exercise("E17")
    assert results[-1].quantity.to("kN").magnitude == pytest.approx(150.0)


def test_e18_the_reported_maximum_moment_reaches_the_summary():
    """qL^2/8 = 10*36/8 = 45 kN*m, and the summary carries that same value."""
    _engine, results = run_exercise("E18")
    summary = results[-1]

    assert [name for name, _value in summary.entries] == ["M_max"]
    quantity = summary.entries[0][1]
    assert quantity.to("kN*m").magnitude == pytest.approx(45.0)


def test_e10_the_factored_combination_totals_what_the_code_requires():
    """L = 6 m, qD = 8 kN/m, qL = 12 kN/m, and U1 = 1.2D + 1.6L.

    At midspan the dead moment is 8*36/8 = 36 kN*m and the live one 12*36/8 = 54, so
    U1 is 1.2*36 + 1.6*54 = 129.6 kN*m. Worked here rather than read off the run.

    E10 was the last exercise with a real capability gap. It now runs, and this is what
    it must answer; the gap map only ever said it stopped raising.
    """
    engine, _results = run_exercise("E10")

    assert function_at(engine, "D", "3*m", "kN*m") == pytest.approx(36.0)
    assert function_at(engine, "Lv", "3*m", "kN*m") == pytest.approx(54.0)
    assert function_at(engine, "U1", "3*m", "kN*m") == pytest.approx(129.6)


def test_e10_the_combination_still_carries_its_factors():
    """The reason `combo` exists, asserted on the exercise it was built for.

    A combination that totalled correctly and printed `0.6*qD*x*(L-x)` would pass the
    property above and lose the thing a reviewer checks.
    """
    engine, _results = run_exercise("E10")
    combination = engine.functions["U1"]

    assert combination.parameters == ("x",)
    # The stored expression is expanded, as it must be to plot; the terms are what the
    # page shows, and they are what this pins.
    assert "1.2" in _rendered_combination(engine)
    assert "1.6" in _rendered_combination(engine)


def _rendered_combination(engine):
    from engcalc_colab.renderer import render_aligned_results

    source = next(
        source
        for title, _area, source in EXERCISES
        if title.startswith("E10 ")
    )
    fresh = EngineeringEngine()
    results = []
    for line in [ln for ln in source.strip().splitlines() if ln.strip()]:
        for item in parse_cell(line):
            if isinstance(item, ParsedHeading):
                continue
            outcome = fresh.evaluate(item)
            if outcome is not None:
                results.append(outcome)
    from engcalc_colab.models import LoadCombinationResult

    combination = next(r for r in results if isinstance(r, LoadCombinationResult))
    return render_aligned_results([combination])
