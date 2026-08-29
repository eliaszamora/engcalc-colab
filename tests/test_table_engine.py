import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError, EngSyntaxError
from engcalc_colab.models import TableResult
from engcalc_colab.parser import parse_cell


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def test_table_evaluates_direct_multiarg_response_on_uniform_grid():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M(x, q, L) = q*x*(L-x)/2\n"
        "qD := 4*kN/m\n"
        "L := 5*m",
    )

    result = eval_cell(engine, "table(M(x, qD, L), x, 0, L, 21)")[-1]

    assert isinstance(result, TableResult)
    assert result.mode == "uniform"
    assert result.variable == "x"
    assert len(result.point_values) == 21
    assert result.point_values[10].to("m").magnitude == pytest.approx(2.5)
    assert len(result.columns) == 1
    assert result.columns[0].values[10].to("kN*m").magnitude == pytest.approx(12.5)


def test_table_multiple_compatible_responses_preserve_source_order():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_D(x) = qD*x*(L-x)/2\n"
        "M_L(x) = qL*x*(L-x)/2\n"
        "qD := 4*kN/m\n"
        "qL := 2*kN/m\n"
        "L := 4*m",
    )

    result = eval_cell(engine, "table(M_D(x), M_L(x), x, 0, L, 3)")[-1]

    assert [column.display_label for column in result.columns] == ["M_D(x)", "M_L(x)"]
    assert result.columns[0].values[1].to("kN*m").magnitude == pytest.approx(8.0)
    assert result.columns[1].values[1].to("kN*m").magnitude == pytest.approx(4.0)


def test_table_explicit_unit_once_points_are_evaluated():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nq := 4*kN/m\nL := 2*m")

    result = eval_cell(engine, "table(M(x), x, [0, 1, 2], m)")[-1]

    assert result.mode == "explicit"
    assert [point.to("m").magnitude for point in result.point_values] == pytest.approx([0, 1, 2])
    assert [value.to("kN*m").magnitude for value in result.columns[0].values] == pytest.approx([0, 2, 0])


def test_table_explicit_mixed_compatible_point_units_are_evaluated():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*x\nq := 2*kN/m")

    result = eval_cell(engine, "table(V(x), x, [0*m, 50*cm, 1*m])")[-1]

    assert [point.to("m").magnitude for point in result.point_values] == pytest.approx([0, 0.5, 1])
    assert [value.to("kN").magnitude for value in result.columns[0].values] == pytest.approx([0, 1, 2])


def test_table_constant_numeric_response_works():
    engine = EngineeringEngine()
    eval_cell(engine, "P := 5*kN")

    result = eval_cell(engine, "table(P, x, 0, 2, 3)")[-1]

    assert [value.to("kN").magnitude for value in result.columns[0].values] == pytest.approx([5, 5, 5])


def test_table_nested_user_function_response_works():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M(x, q, L) = q*x*(L-x)/2\n"
        "qU(qD, qL) = 1.2*qD + 1.6*qL\n"
        "M_U(x) = M(x, qU(qD, qL), L)\n"
        "qD := 4*kN/m\n"
        "qL := 2*kN/m\n"
        "L := 5*m",
    )

    result = eval_cell(engine, "table(M_U(x), x, 0, L, 3)")[-1]

    assert result.columns[0].values[1].to("kN*m").magnitude == pytest.approx(25.0)


def test_table_scalar_math_response_works():
    engine = EngineeringEngine()
    eval_cell(engine, "v(x) = A*sin(pi*x/L)\nA := 2*mm\nL := 2*m")

    result = eval_cell(engine, "table(v(x), x, 0, L, 3)")[-1]

    assert result.columns[0].values[1].to("mm").magnitude == pytest.approx(2.0)


def test_table_locally_overrides_preexisting_numeric_variable_without_mutation():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*x\nq := 2*kN/m\nx := 9*m")

    result = eval_cell(engine, "table(V(x), x, 0*m, 2*m, 3)")[-1]

    assert result.columns[0].values[1].to("kN").magnitude == pytest.approx(2.0)
    assert engine.numeric_context.get("x").to("m").magnitude == pytest.approx(9.0)


def test_table_reports_unresolved_non_table_symbol():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x\nL := 2*m")

    with pytest.raises(EngEvaluationError) as exc_info:
        eval_cell(engine, "table(M(x), x, 0, L, 3)")

    assert str(exc_info.value).startswith("line 1:")
    assert "numeric evaluation requires values for: q" in str(exc_info.value)


def test_table_rejects_incompatible_response_dimensions():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V(x) = q*x\n"
        "M(x) = q*x^2\n"
        "q := 2*kN/m\n"
        "L := 2*m",
    )

    with pytest.raises(
        EngEvaluationError,
        match="table response columns have incompatible units",
    ):
        eval_cell(engine, "table(V(x), M(x), x, 0, L, 3)")


def test_table_invalid_count_is_rejected_end_to_end():
    engine = EngineeringEngine()
    with pytest.raises(
        EngEvaluationError,
        match="table count must be a dimensionless integer >= 2",
    ):
        eval_cell(engine, "table(x, x, 0, 1, 1)")


def test_table_invalid_variable_and_call_shape_remain_syntax_errors():
    engine = EngineeringEngine()
    with pytest.raises(EngSyntaxError, match="table variable must be a symbolic identifier"):
        eval_cell(engine, "table(x, x + 1, 0, 1, 3)")
    with pytest.raises(EngSyntaxError, match="unsupported table call shape"):
        eval_cell(engine, "table(x, x, 0)")


def test_table_cannot_be_assigned_to_symbol():
    engine = EngineeringEngine()
    with pytest.raises(EngEvaluationError, match="table must be a standalone statement"):
        eval_cell(engine, "A = table(x, x, 0, 1, 3)")
