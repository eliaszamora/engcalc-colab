import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Annotation, Text

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot
from engcalc_colab.presentation import render_presented_plot


_AXES_SIZE_TOLERANCE_PX = 1.0
_SUMMARY_GIDS = {
    "engcalc-summary-title",
    "engcalc-summary-group-header",
    "engcalc-summary-entry-label",
    "engcalc-summary-entry-role",
    "engcalc-summary-entry-value",
}


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


def _sparse_two_series_plot():
    engine = EngineeringEngine()
    _eval_cell(
        engine,
        """
        L := 4*m
        q1 := 2*kN/m
        q2 := 3*kN/m
        M_1(x) = q1*x*(L-x)/2
        M_2(x) = q2*x*(L-x)/2
        """,
    )
    return _eval_cell(engine, "plot(M_1(x), M_2(x), x, 0, L)")[-1]


def _annotations(axis):
    return [item for item in axis.texts if isinstance(item, Annotation)]


def _text_box(text, renderer):
    return Text.get_window_extent(text, renderer)


def _overlap_area(left, right):
    width = max(0.0, min(left.x1, right.x1) - max(left.x0, right.x0))
    height = max(0.0, min(left.y1, right.y1) - max(left.y0, right.y0))
    return width * height


def _summary_axes(figure):
    return [
        axis
        for axis in figure.axes[1:]
        if axis.get_gid() == "engcalc-characteristic-summary"
    ]


def _render(result):
    figure = render_presented_plot(result)
    axis = figure.axes[0]
    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    return figure, axis, _annotations(axis), canvas.get_renderer()


def _render_baseline(result):
    figure = render_plot(result)
    axis = figure.axes[0]
    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    return figure, axis, canvas.get_renderer()


def _render_dense_case():
    return _render(_dense_six_series_moment_plot())


def test_dense_characteristics_move_to_compact_summary():
    figure, _axis, items, _renderer = _render_dense_case()

    assert len(items) == 0
    assert len(_summary_axes(figure)) == 1

    summary = _summary_axes(figure)[0]
    assert len(
        [text for text in summary.texts if text.get_gid() == "engcalc-summary-group-header"]
    ) == 2
    assert len(
        [text for text in summary.texts if text.get_gid() == "engcalc-summary-entry-label"]
    ) == 12
    assert len(
        [text for text in summary.texts if text.get_gid() == "engcalc-summary-entry-role"]
    ) == 12
    assert len(
        [text for text in summary.texts if text.get_gid() == "engcalc-summary-entry-value"]
    ) == 12


def test_dense_summary_preserves_primary_plot_size_and_is_compact():
    result = _dense_six_series_moment_plot()
    baseline_figure, baseline_axis, baseline_renderer = _render_baseline(result)
    baseline_box = baseline_axis.get_window_extent(baseline_renderer)

    figure, axis, _items, renderer = _render(result)
    box = axis.get_window_extent(renderer)

    assert figure.get_figwidth() == baseline_figure.get_figwidth()
    assert abs(float(box.width) - float(baseline_box.width)) <= _AXES_SIZE_TOLERANCE_PX
    assert abs(float(box.height) - float(baseline_box.height)) <= _AXES_SIZE_TOLERANCE_PX
    added_height = figure.get_figheight() - baseline_figure.get_figheight()
    assert 0.0 < added_height < 1.85


def test_dense_summary_text_is_contained_and_collision_free():
    figure, _axis, _items, renderer = _render_dense_case()
    summaries = _summary_axes(figure)
    assert len(summaries) == 1
    summary = summaries[0]

    texts = [text for text in summary.texts if text.get_gid() in _SUMMARY_GIDS]
    assert len(texts) == 39

    figure_box = figure.bbox
    boxes = [_text_box(text, renderer) for text in texts]
    for box in boxes:
        assert box.x0 >= figure_box.x0
        assert box.x1 <= figure_box.x1
        assert box.y0 >= figure_box.y0
        assert box.y1 <= figure_box.y1

    for index, left in enumerate(boxes):
        for right in boxes[index + 1:]:
            assert _overlap_area(left, right) == 0.0


def test_sparse_two_label_clusters_keep_existing_inline_annotations():
    figure, axis, items, renderer = _render(_sparse_two_series_plot())
    axes_box = axis.get_window_extent(renderer)

    assert len(items) == 4
    assert len(_summary_axes(figure)) == 0
    assert all(item.arrow_patch is None for item in items)
    assert all(
        _text_box(item, renderer).x0 >= axes_box.x0
        and _text_box(item, renderer).x1 <= axes_box.x1
        and _text_box(item, renderer).y0 >= axes_box.y0
        and _text_box(item, renderer).y1 <= axes_box.y1
        for item in items
    )
    assert figure.get_figwidth() == matplotlib.rcParams["figure.figsize"][0]
    assert figure.get_figheight() == matplotlib.rcParams["figure.figsize"][1]
