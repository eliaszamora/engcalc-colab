import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import TableResult
from engcalc_colab.parser import parse_cell


def eval_cell(engine, source):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def define_standard_piecewise(engine):
    eval_cell(
        engine,
        "q(x) = piecewise(q1, x < a, q2, x <= L, 0)\n"
        "q1 := 8*kN/m\n"
        "q2 := 4*kN/m\n"
        "a := 3*m\n"
        "L := 6*m",
    )


def test_piecewise_uniform_table_keeps_exact_requested_row_count_and_endpoint_ownership():
    engine = EngineeringEngine()
    define_standard_piecewise(engine)

    result = eval_cell(engine, "table(q(x), x, 0, L, 21)")[-1]

    assert isinstance(result, TableResult)
    assert len(result.point_values) == 21
    assert len(result.columns[0].values) == 21
    assert result.point_values[10].to("m").magnitude == pytest.approx(3.0)
    assert result.columns[0].values[10].to("kN/m").magnitude == pytest.approx(4.0)
    assert result.columns[0].values[-1].to("kN/m").magnitude == pytest.approx(4.0)


def test_piecewise_explicit_table_keeps_exact_points_without_breakpoint_insertion():
    engine = EngineeringEngine()
    define_standard_piecewise(engine)

    result = eval_cell(engine, "table(q(x), x, [0, 3, 6, 8], m)")[-1]

    assert len(result.point_values) == 4
    assert [point.to("m").magnitude for point in result.point_values] == pytest.approx([0, 3, 6, 8])
    assert [value.to("kN/m").magnitude for value in result.columns[0].values] == pytest.approx([8, 4, 4, 0])


def test_piecewise_table_leading_exact_zero_inherits_response_unit_from_later_branches():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "q(x) = piecewise(0, x < a, q2, x <= L, 0)\n"
        "q2 := 4*kN/m\n"
        "a := 3*m\n"
        "L := 6*m",
    )

    result = eval_cell(engine, "table(q(x), x, [0, 3, 8], m)")[-1]

    assert str(result.columns[0].unit) != "dimensionless"
    assert [value.to("kN/m").magnitude for value in result.columns[0].values] == pytest.approx([0, 4, 0])


def test_piecewise_table_rejects_incompatible_units_across_sampled_branches():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "q(x) = piecewise(q1, x < a, q2, x <= L, 0)\n"
        "q1 := 8*kN\n"
        "q2 := 4*m\n"
        "a := 3*m\n"
        "L := 6*m",
    )

    with pytest.raises(EngEvaluationError, match="incompatible units"):
        eval_cell(engine, "table(q(x), x, [0, 4], m)")
