import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Annotation

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot


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


def _annotations(axis):
    return [item for item in axis.texts if isinstance(item, Annotation)]


def _box_center_y(annotation, renderer):
    box = annotation.get_window_extent(renderer)
    return 0.5 * (box.y0 + box.y1)


def _anchor_display_y(axis, annotation):
    return float(axis.transData.transform(annotation.xy)[1])


def _assert_cluster_preserves_visual_order(axis, cluster, renderer):
    ordered_by_anchor = sorted(cluster, key=lambda item: _anchor_display_y(axis, item))
    label_centers = [_box_center_y(item, renderer) for item in ordered_by_anchor]
    assert label_centers == sorted(label_centers), [
        (item.get_text(), item.xy, center)
        for item, center in zip(ordered_by_anchor, label_centers)
    ]


def test_dense_shared_x_characteristic_labels_follow_anchor_visual_order():
    figure = render_plot(_dense_six_series_moment_plot())
    axis = figure.axes[0]
    items = _annotations(axis)
    assert len(items) == 12

    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    renderer = canvas.get_renderer()

    left_cluster = [item for item in items if abs(float(item.xy[0])) < 1e-9]
    interior_cluster = [item for item in items if abs(float(item.xy[0]) - 2.5) < 0.03]
    assert len(left_cluster) == 6
    assert len(interior_cluster) == 6

    _assert_cluster_preserves_visual_order(axis, left_cluster, renderer)
    _assert_cluster_preserves_visual_order(axis, interior_cluster, renderer)
