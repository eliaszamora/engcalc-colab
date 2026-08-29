from itertools import combinations
import re

import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Annotation

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot


_COORDINATE_LABEL = re.compile(r"^\(-?\d+(?:\.\d+)?, -?\d+(?:\.\d+)?\)$")


def eval_cell(engine, source: str):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def propped_cantilever_stage_moment_plot():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        """
        L := 4*m
        qC := 2*tonf/m
        qD := 4*tonf/m
        qL := 3*tonf/m
        M_C(x) = -qC*L^2/2 + qC*L*x - qC*x^2/2
        M_D(x) = -qD*L^2/8 + 5*qD*L*x/8 - qD*x^2/2
        M_L(x) = -qL*L^2/8 + 5*qL*L*x/8 - qL*x^2/2
        """,
    )
    return eval_cell(engine, "plot(M_C(x), M_D(x), M_L(x), x, 0, L)")[-1]


def signed_moment_envelope():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        """
        q := 8*kN/m
        L := 6*m
        M_A(x) = q*x*(L-x)/2
        M_B(x) = -0.5*q*x*(L-x)/2
        M_C(x) = 0.6*q*x*(L-x)/2
        """,
    )
    return eval_cell(engine, "envelope(M_A(x), M_B(x), M_C(x), x, 0, L)")[-1]


def magnitude_shear_envelope():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        """
        R_constr := 6*kN
        q_constr := 4*kN/m
        R_uso := -9*kN
        q_uso := 1*kN/m
        L := 2*m
        V_constr(x) = R_constr - q_constr*x
        V_uso(x) = R_uso + q_uso*x
        """,
    )
    return eval_cell(engine, "envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)")[-1]


def annotations(axis):
    return [item for item in axis.texts if isinstance(item, Annotation)]


def text_box(annotation, renderer):
    return annotation.get_window_extent(renderer)


def test_characteristic_labels_are_coordinate_only_without_units_boxes_or_leaders():
    for result in (
        propped_cantilever_stage_moment_plot(),
        signed_moment_envelope(),
        magnitude_shear_envelope(),
    ):
        axis = render_plot(result).axes[0]
        items = annotations(axis)
        assert items
        for item in items:
            text = item.get_text()
            assert _COORDINATE_LABEL.fullmatch(text), text
            assert "=" not in text
            assert "kN" not in text and "tonf" not in text and "m" not in text
            assert item.arrow_patch is None
            assert item.get_bbox_patch() is None


def test_compact_coordinate_labels_do_not_overlap_each_other_axes_or_legend():
    figure = render_plot(propped_cantilever_stage_moment_plot())
    axis = figure.axes[0]
    items = annotations(axis)
    assert len(items) == 6

    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    renderer = canvas.get_renderer()
    axes_box = axis.get_window_extent(renderer)
    legend_box = axis.get_legend().get_window_extent(renderer)
    boxes = [text_box(item, renderer).expanded(1.05, 1.12) for item in items]

    for left, right in combinations(boxes, 2):
        assert not left.overlaps(right), (left, right)

    for box in boxes:
        assert box.x0 >= axes_box.x0 - 1
        assert box.x1 <= axes_box.x1 + 1
        assert box.y0 >= axes_box.y0 - 1
        assert box.y1 <= axes_box.y1 + 1
        assert not box.overlaps(legend_box)


def test_compact_coordinate_labels_do_not_cover_sampled_curve_points():
    figure = render_plot(propped_cantilever_stage_moment_plot())
    axis = figure.axes[0]
    items = annotations(axis)

    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    renderer = canvas.get_renderer()

    curve_points = []
    for line in axis.lines:
        if line.get_label() == "_zero":
            continue
        curve_points.extend(
            axis.transData.transform((float(x), float(y)))
            for x, y in zip(line.get_xdata(), line.get_ydata())
        )

    for item in items:
        box = text_box(item, renderer).expanded(1.04, 1.10)
        anchor = axis.transData.transform(item.xy)
        for point in curve_points:
            if abs(point[0] - anchor[0]) < 1e-6 and abs(point[1] - anchor[1]) < 1e-6:
                continue
            assert not (box.x0 <= point[0] <= box.x1 and box.y0 <= point[1] <= box.y1), (
                item.get_text(),
                item.xy,
                box,
                point,
            )
