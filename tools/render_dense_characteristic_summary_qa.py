from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Annotation

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


def _overlap_area(left, right) -> float:
    width = max(0.0, min(left.x1, right.x1) - max(left.x0, right.x0))
    height = max(0.0, min(left.y1, right.y1) - max(left.y0, right.y0))
    return float(width * height)


def main() -> None:
    result = _dense_six_series_moment_plot()

    baseline_figure = render_plot(result)
    baseline_canvas = FigureCanvasAgg(baseline_figure)
    baseline_canvas.draw()
    baseline_axis = baseline_figure.axes[0]
    baseline_box = baseline_axis.get_window_extent(baseline_canvas.get_renderer())

    figure = render_presented_plot(result)
    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    renderer = canvas.get_renderer()
    main_axis = figure.axes[0]
    main_box = main_axis.get_window_extent(renderer)

    summary_axes = [
        axis
        for axis in figure.axes[1:]
        if axis.get_gid() == "engcalc-characteristic-summary"
    ]
    assert len(summary_axes) == 1
    summary = summary_axes[0]

    groups = _build_dense_summary_groups(main_axis, result)
    summary_texts = list(summary.texts)
    summary_boxes = [text.get_window_extent(renderer) for text in summary_texts]

    overlap_count = 0
    for index, left in enumerate(summary_boxes):
        for right in summary_boxes[index + 1:]:
            if _overlap_area(left, right) > 0.0:
                overlap_count += 1

    figure_box = figure.bbox
    contained = all(
        box.x0 >= figure_box.x0
        and box.x1 <= figure_box.x1
        and box.y0 >= figure_box.y0
        and box.y1 <= figure_box.y1
        for box in summary_boxes
    )

    dense_annotations = [
        item for item in main_axis.texts if isinstance(item, Annotation)
    ]
    leader_count = sum(
        item.arrow_patch is not None for item in dense_annotations
    )

    summary_entry_count = sum(len(group.entries) for group in groups)
    metrics = {
        "baseline_figure_inches": [
            float(value) for value in baseline_figure.get_size_inches()
        ],
        "presented_figure_inches": [
            float(value) for value in figure.get_size_inches()
        ],
        "baseline_axes_px": [
            float(baseline_box.width),
            float(baseline_box.height),
        ],
        "presented_axes_px": [
            float(main_box.width),
            float(main_box.height),
        ],
        "dense_group_count": int(len(groups)),
        "summary_entry_count": int(summary_entry_count),
        "summary_text_count": int(len(summary_texts)),
        "summary_text_overlap_count": int(overlap_count),
        "all_summary_text_inside_figure": bool(contained),
        "dense_main_axis_annotation_count": int(len(dense_annotations)),
        "dense_leader_count": int(leader_count),
    }

    assert metrics["dense_group_count"] == 2
    assert metrics["summary_entry_count"] == 12
    assert metrics["summary_text_overlap_count"] == 0
    assert metrics["all_summary_text_inside_figure"] is True
    assert metrics["dense_main_axis_annotation_count"] == 0
    assert metrics["dense_leader_count"] == 0
    assert abs(
        metrics["presented_axes_px"][0] - metrics["baseline_axes_px"][0]
    ) <= 1.0
    assert abs(
        metrics["presented_axes_px"][1] - metrics["baseline_axes_px"][1]
    ) <= 1.0
    assert (
        metrics["presented_figure_inches"][0]
        == metrics["baseline_figure_inches"][0]
    )
    added_height = (
        metrics["presented_figure_inches"][1]
        - metrics["baseline_figure_inches"][1]
    )
    assert 0.0 < added_height < 1.85

    figure.savefig(
        "dense_characteristic_summary.png",
        dpi=160,
        bbox_inches=None,
    )
    with open(
        "dense_characteristic_summary_metrics.json",
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(metrics, handle, indent=2)


if __name__ == "__main__":
    main()
