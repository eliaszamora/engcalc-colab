from pathlib import Path
import pytest
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import (
    EvaluationResult, NumericAssignmentResult, NumericEvaluationResult,
    PartialNumericEvaluationResult, PlotResult, TableResult,
)
from engcalc_colab.parser import parse_cell

def test_realistic_piecewise_workflow_preserves_result_order_and_contracts():
    engine = EngineeringEngine()
    source = (
        "q1 := 8*kN/m\nq2 := 4*kN/m\na := 3*m\nL := 6*m\n"
        "q(x) = piecewise(q1, x < a, q2, x <= L, 0)\n"
        "numeric(q(x))\nnumeric(q(2*m))\n"
        "table(q(x), x, 0, L, 21)\nplot(q(x), x, 0, L)"
    )
    results = [engine.evaluate(item) for item in parse_cell(source)]
    assert [type(item) for item in results] == [
        NumericAssignmentResult, NumericAssignmentResult,
        NumericAssignmentResult, NumericAssignmentResult,
        EvaluationResult, PartialNumericEvaluationResult,
        NumericEvaluationResult, TableResult, PlotResult,
    ]
    assert results[6].quantity.to("kN/m").magnitude == pytest.approx(8.0)
    assert len(results[7].point_values) == 21
    assert len(results[8].x_values) == 201
    assert results[8].series[0].segment_starts

def test_readme_documents_the_executable_piecewise_contract():
    readme = Path("README.md").read_text()
    required = [
        "## v0.8.0 Piecewise expressions",
        "piecewise(q1, x < a, q2, x <= L, 0)",
        "mandatory default", "numeric(q(x))",
        "table(q(x), x, 0, L, 21)", "201-point base grid",
        "derivative", "breakpoint", "0.8.0 limitations",
    ]
    for item in required:
        assert item in readme
