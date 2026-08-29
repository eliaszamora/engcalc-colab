from itertools import combinations

import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Annotation

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot


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


def label_box(annotation, renderer):
    return annotation.get_window_extent(renderer)


def placement_diagnostic(item, renderer):
    box = label_box(item, renderer)
    return {
        "text": item.get_text(),
        "xy": tuple(float(value) for value in item.xy),
        "offset": tuple(float(value) for value in item.get_position()),
        "ha": item.get_ha(),
        "va": item.get_va(),
        "box": tuple(float(value) for value in (box.x0, box.y0, box.x1, box.y1)),
    }


def test_propped_cantilever_characteristic_labels_do_not_overlap():
    figure = render_plot(propped_cantilever_stage_moment_plot())
    axis = figure.axes[0]
    items = [text for text in axis.texts if isinstance(text, Annotation)]

    assert len(items) == 6

    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    renderer = canvas.get_renderer()
    boxes = [label_box(item, renderer).expanded(1.04, 1.08) for item in items]

    for (left_index, left), (right_index, right) in combinations(enumerate(boxes), 2):
        assert not left.overlaps(right), (
            placement_diagnostic(items[left_index], renderer),
            placement_diagnostic(items[right_index], renderer),
        )


def test_propped_cantilever_labels_stay_inside_axes_and_clear_of_legend():
    figure = render_plot(propped_cantilever_stage_moment_plot())
    axis = figure.axes[0]
    items = [text for text in axis.texts if isinstance(text, Annotation)]

    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    renderer = canvas.get_renderer()
    axes_box = axis.get_window_extent(renderer)
    legend_box = axis.get_legend().get_window_extent(renderer)

    for item in items:
        box = label_box(item, renderer)
        diagnostic = placement_diagnostic(item, renderer)
        assert box.x0 >= axes_box.x0 - 1, diagnostic
        assert box.x1 <= axes_box.x1 + 1, diagnostic
        assert box.y0 >= axes_box.y0 - 1, diagnostic
        assert box.y1 <= axes_box.y1 + 1, diagnostic
        assert not box.expanded(1.02, 1.05).overlaps(legend_box), diagnostic
