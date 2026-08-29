from __future__ import annotations

import math

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Annotation

from .models import PlotResult
from .plotting import (
    _CALLOUT_CLEARANCE_X,
    _CALLOUT_CLEARANCE_Y,
    _annotate_characteristic,
    _annotation_box,
    _series_response_symbol,
)


_CLUSTER_X_TOLERANCE_PX = 14.0


def _extreme_indices(values: list[float]) -> tuple[int, int]:
    maximum = max(range(len(values)), key=values.__getitem__)
    minimum = min(range(len(values)), key=values.__getitem__)
    return maximum, minimum


def _series_color(axis, display_label: str):
    for line in axis.lines:
        if line.get_label() == display_label:
            return line.get_color()
    return None


def _characteristic_requests(axis, result: PlotResult):
    requests = []
    inverted = all(series.is_moment for series in result.series)

    for series in result.series:
        y_values = [float(value.magnitude) for value in series.y_values]
        maximum_index, minimum_index = _extreme_indices(y_values)
        line_color = _series_color(axis, series.display_label)
        if line_color is None:
            continue

        response_label = _series_response_symbol(result, series)
        requests.append(
            (
                result.x_values[maximum_index],
                series.y_values[maximum_index],
                response_label,
                "max",
                inverted,
                line_color,
            )
        )
        if not math.isclose(
            y_values[maximum_index],
            y_values[minimum_index],
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            requests.append(
                (
                    result.x_values[minimum_index],
                    series.y_values[minimum_index],
                    response_label,
                    "min",
                    inverted,
                    line_color,
                )
            )

    return requests


def _cluster_requests(axis, requests):
    positioned = []
    for request in requests:
        x_quantity, y_quantity, *_ = request
        x = float(x_quantity.magnitude)
        y = float(y_quantity.magnitude)
        display_x, display_y = axis.transData.transform((x, y))
        positioned.append((float(display_x), float(display_y), request))

    positioned.sort(key=lambda item: (item[0], item[1]))
    clusters = []
    for item in positioned:
        if not clusters:
            clusters.append([item])
            continue
        previous_x = clusters[-1][-1][0]
        if abs(item[0] - previous_x) <= _CLUSTER_X_TOLERANCE_PX:
            clusters[-1].append(item)
        else:
            clusters.append([item])
    return clusters


def _box_center(box) -> tuple[float, float]:
    return (0.5 * (box.x0 + box.x1), 0.5 * (box.y0 + box.y1))


def _reassign_cluster_slots(
    figure,
    axis,
    annotations: list[Annotation],
    occupied_boxes: list,
    occupied_start: int,
) -> None:
    if len(annotations) < 2:
        return

    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    slots = sorted(
        (_box_center(_annotation_box(annotation, renderer)) for annotation in annotations),
        key=lambda center: center[1],
    )

    pixels_to_points = 72.0 / float(figure.dpi)
    for annotation, (target_x, target_y) in zip(annotations, slots):
        anchor_x, anchor_y = axis.transData.transform(annotation.xy)
        annotation.set_position(
            (
                (target_x - float(anchor_x)) * pixels_to_points,
                (target_y - float(anchor_y)) * pixels_to_points,
            )
        )
        annotation.set_ha("center")
        annotation.set_va("center")

    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    del occupied_boxes[occupied_start:]
    for annotation in annotations:
        occupied_boxes.append(
            _annotation_box(annotation, renderer).expanded(
                _CALLOUT_CLEARANCE_X,
                _CALLOUT_CLEARANCE_Y,
            )
        )


def reflow_dense_characteristic_labels(figure, result: PlotResult) -> None:
    """Re-place multi-series characteristic labels in spatial reading order.

    The plotting layer remains authoritative for which characteristic points
    exist. This pass only changes annotation placement for multi-series plots.
    """
    if result.kind != "plot" or len(result.series) < 2:
        return

    axis = figure.axes[0]
    requests = _characteristic_requests(axis, result)
    if len(requests) < 2:
        return

    for item in list(axis.texts):
        if isinstance(item, Annotation):
            item.remove()

    original_canvas = figure.canvas
    FigureCanvasAgg(figure)
    try:
        figure.canvas.draw()
        occupied_boxes: list = []
        for cluster in _cluster_requests(axis, requests):
            cluster.sort(key=lambda item: item[1])
            occupied_start = len(occupied_boxes)
            cluster_annotations: list[Annotation] = []
            for _, _, request in cluster:
                (
                    x_quantity,
                    y_quantity,
                    response_label,
                    role,
                    inverted,
                    line_color,
                ) = request
                _annotate_characteristic(
                    axis,
                    x_quantity,
                    y_quantity,
                    response_label,
                    role=role,
                    inverted=inverted,
                    line_color=line_color,
                    occupied_boxes=occupied_boxes,
                )
                annotation = axis.texts[-1]
                if isinstance(annotation, Annotation):
                    cluster_annotations.append(annotation)

            _reassign_cluster_slots(
                figure,
                axis,
                cluster_annotations,
                occupied_boxes,
                occupied_start,
            )
    finally:
        figure.set_canvas(original_canvas)
