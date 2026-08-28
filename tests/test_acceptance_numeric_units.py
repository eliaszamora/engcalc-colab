import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def test_approved_numeric_units_acceptance_flow_preserves_symbolic_source_of_truth():
    engine = EngineeringEngine()

    results = run_cell(
        engine,
        """
V_B = 3*q*L/8
V_A = 5*q*L/8
M_A = q*L^2/8
q := 2.8*tonf/m
L := 4*m
numeric(V_B)
numeric(V_A)
numeric(M_A)
""",
    )

    assert results[-3].quantity.to("tonf").magnitude == pytest.approx(4.2)
    assert results[-2].quantity.to("tonf").magnitude == pytest.approx(7.0)
    assert results[-1].quantity.to("tonf*m").magnitude == pytest.approx(5.6)
    assert str(engine.namespace["V_B"]) == "3*L*q/8"
    assert str(engine.namespace["V_A"]) == "5*L*q/8"
    assert str(engine.namespace["M_A"]) == "L**2*q/8"

    symbolic_before = engine.namespace["M_A"]
    updated = run_cell(engine, "q := 3.5*tonf/m\nnumeric(M_A)")[-1]

    assert updated.quantity.to("tonf*m").magnitude == pytest.approx(7.0)
    assert engine.namespace["M_A"] == symbolic_before
