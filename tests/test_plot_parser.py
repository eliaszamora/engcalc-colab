from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.models import PlotResult
from engcalc_colab.parser import parse_cell


def test_plot_call_is_accepted_by_restricted_parser():
    statement = parse_cell("plot(M(x), x, 0, L)")[0]
    assert statement.target is None
    assert statement.expression.body.func.id == "plot"
    assert len(statement.expression.body.args) == 4


def test_plot_name_is_reserved_as_assignment_target():
    try:
        parse_cell("plot = 3")
    except EngSyntaxError as exc:
        assert "reserved identifier 'plot'" in str(exc)
    else:
        raise AssertionError("expected EngSyntaxError")


def test_plot_result_is_immutable_transport_data():
    statement = parse_cell("plot(M(x), x, 0, L)")[0]
    result = PlotResult(statement, "M(x)", "x", (1,), (2,))
    assert result.display_label == "M(x)"
    assert result.variable == "x"
