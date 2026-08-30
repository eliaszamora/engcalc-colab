import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Annotation, Text

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot
from engcalc_colab.presentation import render_presented_plot


_MIN_RAIL_VERTICAL_CLEARANCE_PX = 10.0
_AXES_SIZE_TOLERANCE_PX = 1.0


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


def _text_box(annotation, renderer):
    return Text.get_window_extent(annotation, renderer)


def _box_center_y(annotation, renderer):
    box = _text_box(annotation, renderer)
    return 0.5 * (box.y0 + box.y1)


def _anchor_display_y(axis, annotation):
    return float(axis.transData.transform(annotation.xy)[1])


def _overlap_area(left, right):
    width = max(0.0, min(left.x1, right.x1) - max(left.x0, right.x0))
    height = max(0.0, min(left.y1, right.y1) - max(left.y0, right.y0))
    return width * height


def _assert_cluster_preserves_visual_order(axis, cluster, renderer):
    ordered_by_anchor = sorted(cluster, key=lambda item: _anchor_display_y(axis, item))
    label_centers = [_box_center_y(item, renderer) for item in ordered_by_anchor]
    assert label_centers == sorted(label_centers), [
        (item.get_text(), item.xy, center)
        for item, center in zip(ordered_by_anchor, label_centers)
    ]


def _assert_single_label_rail(cluster, renderer, *, tolerance_px: float = 3.0):
    boxes = [_text_box(item, renderer) for item in cluster]
    left_edges = [float(box.x0) for box in boxes]
    right_edges = [float(box.x1) for box in boxes]
    left_spread = max(left_edges) - min(left_edges)
    right_spread = max(right_edges) - min(right_edges)
    assert min(left_spread, right_spread) <= tolerance_px, {
        "left_spread": left_spread,
        "right_spread": right_spread,
        "labels": [item.get_text() for item in cluster],
    }


def _assert_minimum_vertical_clearance(cluster, renderer):
    boxes = sorted(
        (_text_box(item, renderer) for item in cluster),
        key=lambda box: float(box.y0),
    )
    clearances = [
        float(upper.y0 - lower.y1)
        for lower, upper in zip(boxes, boxes[1:])
    ]
    assert min(clearances) >= _MIN_RAIL_VERTICAL_CLEARANCE_PX, clearances


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


def test_dense_shared_x_characteristic_labels_follow_anchor_visual_order():
    _, axis, items, renderer = _render_dense_case()
    assert len(items) == 12

    left_cluster = [item for item in items if abs(float(item.xy[0])) < 1e-9]
    interior_cluster = [item for item in items if abs(float(item.xy[0]) - 2.5) < 0.03]
    assert len(left_cluster) == 6
    assert len(interior_cluster) == 6

    _assert_cluster_preserves_visual_order(axis, left_cluster, renderer)
    _assert_cluster_preserves_visual_order(axis, interior_cluster, renderer)


def test_dense_shared_x_groups_use_bottom_callout_band_with_leaders():
    figure, axis, items, renderer = _render_dense_case()
    axes_box = axis.get_window_extent(renderer)
    figure_box = figure.bbox
    left_cluster = [item for item in items if abs(float(item.xy[0])) < 1e-9]
    interior_cluster = [item for item in items if abs(float(item.xy[0]) - 2.5) < 0.03]
    assert len(left_cluster) == 6
    assert len(interior_cluster) == 6

    _assert_single_label_rail(left_cluster, renderer)
    _assert_single_label_rail(interior_cluster, renderer)
    assert all(item.arrow_patch is not None for item in left_cluster + interior_cluster)

    boxes = [_text_box(item, renderer) for item in left_cluster + interior_cluster]
    assert all(box.y1 < axes_box.y0 for box in boxes)
    assert all(
        box.x0 >= figure_box.x0
        and box.x1 <= figure_box.x1
        and box.y0 >= figure_box.y0
        for box in boxes
    )


def test_dense_shared_x_groups_have_robust_vertical_clearance():
    _, _, items, renderer = _render_dense_case()
    left_cluster = [item for item in items if abs(float(item.xy[0])) < 1e-9]
    interior_cluster = [item for item in items if abs(float(item.xy[0]) - 2.5) < 0.03]
    assert len(left_cluster) == 6
    assert len(interior_cluster) == 6

    _assert_minimum_vertical_clearance(left_cluster, renderer)
    _assert_minimum_vertical_clearance(interior_cluster, renderer)


def test_dense_callout_band_adds_height_without_adding_width_or_shrinking_axes():
    result = _dense_six_series_moment_plot()
    baseline_figure, baseline_axis, baseline_renderer = _render_baseline(result)
    baseline_axes_box = baseline_axis.get_window_extent(baseline_renderer)

    figure, axis, items, renderer = _render(result)
    axes_box = axis.get_window_extent(renderer)
    boxes = [_text_box(item, renderer) for item in items]

    assert figure.get_figwidth() == matplotlib.rcParams["figure.figsize"][0]
    assert figure.get_figheight() > matplotlib.rcParams["figure.figsize"][1]
    assert abs(float(axes_box.width) - float(baseline_axes_box.width)) <= _AXES_SIZE_TOLERANCE_PX
    assert abs(float(axes_box.height) - float(baseline_axes_box.height)) <= _AXES_SIZE_TOLERANCE_PX

    for index, left in enumerate(boxes):
        for right in boxes[index + 1:]:
            assert _overlap_area(left, right) == 0.0

    assert baseline_figure.get_figwidth() == matplotlib.rcParams["figure.figsize"][0]


def test_sparse_two_label_clusters_keep_existing_inline_annotations():
    figure, axis, items, renderer = _render(_sparse_two_series_plot())
    axes_box = axis.get_window_extent(renderer)
    assert len(items) == 4
    assert all(item.arrow_patch is None for item in items)
    assert all(
        _text_box(item, renderer).x0 >= axes_box.x0
        and _text_box(item, renderer).x1 <= axes_box.x1
        for item in items
    )
    assert figure.get_figwidth() == matplotlib.rcParams["figure.figsize"][0]
    assert figure.get_figheight() == matplotlib.rcParams["figure.figsize"][1]
