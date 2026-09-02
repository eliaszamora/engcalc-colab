"""`governing(M_U1(x), M_U2(x), x, 0, L)` — which combination governs where.

This is the one item on the roadmap that only code can do. Finding where one load
combination overtakes another means equating them pairwise, solving the crossovers and
ordering the intervals; nobody does that by hand for a continuous span.

**Built on `intersections`, not on the envelope's sampling.** The envelope already
records which series is largest at each of its 201 sample points, and reading that back
would have been the obvious implementation - and would have produced approximate
boundaries. `intersections` is exact-first and returns the crossover symbolically, so the
interval boundaries are exact wherever the mathematics is. Measured before choosing:
for a parabolic and a linear combination it returns `L - 2*P/w`, not a sampled number.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError, EngSyntaxError
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


# A parabola and a straight line that cross once inside the span, at L - 2P/w = 3.2222 m.
_CROSSING = """L := 6*m
w := 28.8*kN/m
P := 40*kN
M_U1(x) = w*x*(L-x)/2
M_U2(x) = P*x
governing(M_U1(x), M_U2(x), x, 0, L)
"""


def test_the_span_is_split_at_the_crossover():
    engine = EngineeringEngine()
    result = run_cell(engine, _CROSSING)[-1]

    assert len(result.intervals) == 2
    first, second = result.intervals
    assert float(first.lower_quantity.to("m").magnitude) == pytest.approx(0.0)
    assert float(first.upper_quantity.to("m").magnitude) == pytest.approx(3.2222, rel=1e-3)
    assert float(second.upper_quantity.to("m").magnitude) == pytest.approx(6.0)


def test_each_interval_names_the_combination_that_governs_it():
    engine = EngineeringEngine()
    result = run_cell(engine, _CROSSING)[-1]

    assert [interval.label for interval in result.intervals] == ["M_U1(x)", "M_U2(x)"]


def test_the_boundary_is_exact_not_sampled():
    """The reason this is built on intersections rather than on the envelope.

    A 201-point sample of a 6 m span lands boundaries on a 30 mm grid. The crossover
    here is L - 2*P/w exactly, so the boundary must agree with the closed form far
    beyond sampling resolution.
    """
    engine = EngineeringEngine()
    result = run_cell(engine, _CROSSING)[-1]

    boundary = float(result.intervals[0].upper_quantity.to("m").magnitude)
    assert boundary == pytest.approx(6.0 - 2 * 40.0 / 28.8, rel=1e-12)


def test_a_single_combination_governs_the_whole_span():
    engine = EngineeringEngine()
    result = run_cell(
        engine,
        "L := 6*m\nqD := 8*kN/m\nqL := 12*kN/m\n"
        "M_U1(x) = 1.2*qD*x*(L-x)/2 + 1.6*qL*x*(L-x)/2\n"
        "M_U2(x) = 1.4*qD*x*(L-x)/2\n"
        "governing(M_U1(x), M_U2(x), x, 0, L)",
    )[-1]

    assert len(result.intervals) == 1
    assert result.intervals[0].label == "M_U1(x)"


def test_three_combinations():
    engine = EngineeringEngine()
    result = run_cell(
        engine,
        "L := 6*m\nw := 10*kN/m\nP := 30*kN\nM0 := 90*kN*m\n"
        "A(x) = P*x\nB(x) = w*x^2/2\nC(x) = M0\n"
        "governing(A(x), B(x), C(x), x, 0, L)",
    )[-1]
    # A(x) and B(x) cross at 6 m, A(x) meets C(x) at 3 m and B(x) meets C(x) at 4.24 m,
    # so there are two interior crossovers - but only one of them changes who governs.
    # C(x) holds the first 3 m and A(x) the rest, in two intervals and not three: a
    # boundary where nothing changes hands is not a boundary.
    assert [interval.label for interval in result.intervals] == ["C(x)", "A(x)"]
    assert float(result.intervals[0].upper_quantity.to("m").magnitude) == pytest.approx(3.0)


def test_it_renders_one_row_per_interval():
    import engcalc_colab.renderer as renderer

    engine = EngineeringEngine()
    latex = renderer.render_result(run_cell(engine, _CROSSING)[-1])
    assert "M_{U1}" in latex or "M_U1" in latex
    assert not [char for char in latex if ord(char) < 32]


def test_it_needs_at_least_two_responses():
    """One response governs itself; asking which of one governs is a mistake."""
    engine = EngineeringEngine()
    with pytest.raises((EngEvaluationError, EngSyntaxError)) as excinfo:
        run_cell(engine, "L := 6*m\nA(x) = 20*x\ngoverning(A(x), x, 0, L)")
    assert "two" in str(excinfo.value).lower()


def test_it_must_be_a_standalone_statement():
    engine = EngineeringEngine()
    with pytest.raises((EngEvaluationError, EngSyntaxError)):
        run_cell(
            engine,
            "L := 6*m\nA(x) = 20*x\nB(x) = 5*x\ng = governing(A(x), B(x), x, 0, L)",
        )
