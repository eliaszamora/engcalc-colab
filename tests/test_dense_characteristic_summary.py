import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.label_layout import _build_dense_summary_groups
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot
from engcalc_colab.presentation import render_presented_plot


def _eval_cell(engine, source: str):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def _dense_six_series_moment_plot():
    engine = EngineeringEngine()
    _eval_cell(
        engine,
        """
        L := 4*m

        A1 := -6*tonf*m
        C1 := 1.50*tonf/m
        B1 := 7.50*tonf

        A2 := -22.4*tonf*m
        C2 := 5.00*tonf/m
        B2 := 25.00*tonf

        A3 := -8*tonf*m
        C3 := 2.00*tonf/m
        B3 := 10.00*tonf

        A4 := -19.2*tonf*m
        C4 := 4.80*tonf/m
        B4 := 24.00*tonf

        A5 := -14*tonf*m
        C5 := 3.50*tonf/m
        B5 := 17.50*tonf

        A6 := -16*tonf*m
        C6 := 4.20*tonf/m
        B6 := 21.00*tonf

        M_C1(x) = A1 + B1*x - C1*x^2
        M_C2(x) = A2 + B2*x - C2*x^2
        M_S1(x) = A3 + B3*x - C3*x^2
        M_S2(x) = A4 + B4*x - C4*x^2
        M_S3(x) = A5 + B5*x - C5*x^2
        M_S4(x) = A6 + B6*x - C6*x^2
        """,
    )
    return _eval_cell(
        engine,
        "plot(M_C1(x), M_C2(x), M_S1(x), M_S2(x), M_S3(x), M_S4(x), x, 0, L)",
    )[-1]


def test_dense_summary_groups_preserve_series_order_roles_and_colors():
    result = _dense_six_series_moment_plot()
    figure = render_plot(result)
    axis = figure.axes[0]
    groups = _build_dense_summary_groups(axis, result)

    expected_labels = [
        "M_C1(x)",
        "M_C2(x)",
        "M_S1(x)",
        "M_S2(x)",
        "M_S3(x)",
        "M_S4(x)",
    ]
    assert len(groups) == 2
    assert [float(group.x_quantity.magnitude) for group in groups] == pytest.approx(
        [0.0, 2.5]
    )
    assert [len(group.entries) for group in groups] == [6, 6]
    assert [entry.request.series.display_label for entry in groups[0].entries] == expected_labels
    assert [entry.request.series.display_label for entry in groups[1].entries] == expected_labels
    assert [entry.request.role for entry in groups[0].entries] == ["min"] * 6
    assert [entry.request.role for entry in groups[1].entries] == ["max"] * 6

    line_colors = {line.get_label(): line.get_color() for line in axis.lines}
    for group in groups:
        for entry in group.entries:
            assert entry.color == line_colors[entry.request.series.display_label]

    keys = {
        (entry.request.series_index, entry.request.role)
        for group in groups
        for entry in group.entries
    }
    assert len(keys) == 12


def test_dense_summary_formats_shared_units_once():
    figure = render_presented_plot(_dense_six_series_moment_plot())
    summaries = [
        axis
        for axis in figure.axes[1:]
        if axis.get_gid() == "engcalc-characteristic-summary"
    ]
    assert len(summaries) == 1
    summary = summaries[0]

    headers = [
        text.get_text()
        for text in summary.texts
        if text.get_gid() == "engcalc-summary-group-header"
    ]
    assert headers == ["x = 0 m", "x = 2.5 m"]

    values = [
        text.get_text()
        for text in summary.texts
        if text.get_gid() == "engcalc-summary-entry-value"
    ]
    assert len(values) == 12
    assert all("tonf" not in value for value in values)
    assert sum(text.get_text() == "Value [tonf·m]" for text in summary.texts) == 2
