import pytest
from IPython.display import HTML, Math
from matplotlib.figure import Figure

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.magic import EngMagics
from engcalc_colab.models import TableResult
from engcalc_colab.parser import parse_cell


def eval_cell(engine: EngineeringEngine, text: str):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def test_acceptance_primary_automatic_21_point_engineering_table():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M(x) = q*x*(L-x)/2\n"
        "q := 4*kN/m\n"
        "L := 5*m",
    )

    result = eval_cell(engine, "table(M(x), x, 0, L, 21)")[-1]

    assert isinstance(result, TableResult)
    assert result.mode == "uniform"
    assert len(result.point_values) == 21
    assert result.point_values[0].to("m").magnitude == pytest.approx(0.0)
    assert result.point_values[10].to("m").magnitude == pytest.approx(2.5)
    assert result.point_values[-1].to("m").magnitude == pytest.approx(5.0)
    assert result.columns[0].values[10].to("kN*m").magnitude == pytest.approx(12.5)


def test_acceptance_multiple_moment_responses_share_one_table():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_D(x) = qD*x*(L-x)/2\n"
        "M_L(x) = qL*x*(L-x)/2\n"
        "M_U(x) = (1.2*qD + 1.6*qL)*x*(L-x)/2\n"
        "qD := 4*kN/m\n"
        "qL := 2*kN/m\n"
        "L := 4*m",
    )

    result = eval_cell(
        engine,
        "table(M_D(x), M_L(x), M_U(x), x, 0, L, 5)",
    )[-1]

    assert [column.display_label for column in result.columns] == [
        "M_D(x)",
        "M_L(x)",
        "M_U(x)",
    ]
    assert result.columns[0].values[2].to("kN*m").magnitude == pytest.approx(8.0)
    assert result.columns[1].values[2].to("kN*m").magnitude == pytest.approx(4.0)
    assert result.columns[2].values[2].to("kN*m").magnitude == pytest.approx(16.0)


def test_acceptance_unit_once_explicit_points():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nq := 4*kN/m\nL := 2*m")

    result = eval_cell(engine, "table(M(x), x, [0, 0.5, 1, 1.5, 2], m)")[-1]

    assert result.mode == "explicit"
    assert [p.to("m").magnitude for p in result.point_values] == pytest.approx(
        [0, 0.5, 1, 1.5, 2]
    )
    assert [v.to("kN*m").magnitude for v in result.columns[0].values] == pytest.approx(
        [0, 1.5, 2, 1.5, 0]
    )


def test_acceptance_fully_explicit_mixed_compatible_units():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*x\nq := 2*kN/m")

    result = eval_cell(engine, "table(V(x), x, [0*m, 50*cm, 1*m, 150*cm])")[-1]

    assert [p.to("m").magnitude for p in result.point_values] == pytest.approx(
        [0, 0.5, 1, 1.5]
    )
    assert [v.to("kN").magnitude for v in result.columns[0].values] == pytest.approx(
        [0, 1, 2, 3]
    )


def test_acceptance_dimensionless_table():
    engine = EngineeringEngine()

    result = eval_cell(engine, "table(x^2, x, 0, 2, 5)")[-1]

    assert str(result.point_unit) == "dimensionless"
    assert [p.magnitude for p in result.point_values] == pytest.approx([0, 0.5, 1, 1.5, 2])
    assert [v.magnitude for v in result.columns[0].values] == pytest.approx([0, 0.25, 1, 2.25, 4])


def test_acceptance_descending_uniform_range_preserves_direction():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*x\nq := 2*kN/m\nL := 2*m")

    result = eval_cell(engine, "table(V(x), x, L, 0, 5)")[-1]

    assert [p.to("m").magnitude for p in result.point_values] == pytest.approx(
        [2, 1.5, 1, 0.5, 0]
    )
    assert [v.to("kN").magnitude for v in result.columns[0].values] == pytest.approx(
        [4, 3, 2, 1, 0]
    )


def test_acceptance_real_eng_mixes_heading_equations_table_plot_in_source_order(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = EngMagics(shell=None)
    magics.eng(
        "",
        "## Simply supported beam\n"
        "M(x) = q*x*(L-x)/2\n"
        "q := 4*kN/m\n"
        "L := 5*m\n"
        "table(M(x), x, 0, L, 5)\n"
        "plot(M(x), x, 0, L)\n"
        "A = q*L",
    )

    assert [type(item) for item in displayed] == [HTML, Math, HTML, Figure, Math]
    assert "Simply supported beam" in displayed[0].data
    assert "engcalc-table" in displayed[2].data
    assert "x [m]" in displayed[2].data
    assert "M(x) [kN·m]" in displayed[2].data
    assert displayed[3].axes[0].get_xlabel() == "x [m]"
