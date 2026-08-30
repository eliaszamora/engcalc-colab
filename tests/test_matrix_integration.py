import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import PlotResult, TableResult
from engcalc_colab.parser import parse_cell


def eval_cell(engine: EngineeringEngine, source: str):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def _matrix_response_engine() -> EngineeringEngine:
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "K(x) = [q*x, 0; 0, 2*q*x]\n"
        "q := 2*kN/m\n"
        "L := 2*m",
    )
    return engine


def test_indexed_matrix_entry_flows_into_table_as_scalar_response():
    engine = _matrix_response_engine()
    result = eval_cell(engine, "table(K(x)[1,1], x, [0*m, 1*m, 2*m])")[-1]

    assert isinstance(result, TableResult)
    assert [value.to("kN").magnitude for value in result.columns[0].values] == pytest.approx([0, 2, 4])


def test_indexed_matrix_entry_flows_into_plot_as_scalar_response():
    engine = _matrix_response_engine()
    result = eval_cell(engine, "plot(K(x)[1,1], x, 0*m, L)")[-1]

    assert isinstance(result, PlotResult)
    assert result.kind == "plot"
    assert len(result.x_values) == 201
    assert result.series[0].y_values[100].to("kN").magnitude == pytest.approx(2.0)


def test_indexed_matrix_entries_flow_into_envelope_as_scalar_responses():
    engine = _matrix_response_engine()
    result = eval_cell(
        engine,
        "envelope(K(x)[1,1], K(x)[2,2], x, 0*m, L)",
    )[-1]

    assert isinstance(result, PlotResult)
    assert result.kind == "envelope"
    assert result.series[0].y_values[100].to("kN").magnitude == pytest.approx(4.0)
    assert result.series[1].y_values[100].to("kN").magnitude == pytest.approx(2.0)


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("table(K(x), x, [0*m, 1*m, 2*m])", "table response must be scalar"),
        ("plot(K(x), x, 0*m, L)", "plot response must be scalar"),
        (
            "envelope(K(x), K(x), x, 0*m, L)",
            "envelope response must be scalar",
        ),
    ],
)
def test_whole_matrix_is_rejected_by_scalar_response_apis(source, message):
    engine = _matrix_response_engine()
    with pytest.raises(EngEvaluationError, match=message):
        eval_cell(engine, source)


def test_existing_explicit_table_list_remains_collection_not_row_matrix():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*x\nq := 2*kN/m")
    result = eval_cell(engine, "table(V(x), x, [0*m, 50*cm, 1*m])")[-1]
    assert isinstance(result, TableResult)
    assert [point.to("m").magnitude for point in result.point_values] == pytest.approx([0, 0.5, 1])


def test_existing_plot_sweep_list_remains_collection_not_row_matrix():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nL := 2*m")
    result = eval_cell(engine, "plot(M(x), x, 0*m, L, q=[2*kN/m, 4*kN/m])")[-1]
    assert isinstance(result, PlotResult)
    assert len(result.series) == 2
