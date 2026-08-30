from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Annotation, Text

from .models import PlotResult
from .plotting import _CharacteristicRequest, _characteristic_requests, _coordinate_label


_CLUSTER_X_TOLERANCE_PX = 14.0
_DENSE_CLUSTER_SIZE = 3
_MIN_BOTTOM_SPACE_IN = 1.65
_BOTTOM_SPACE_PER_LABEL_IN = 0.25
_BOTTOM_SPACE_PADDING_IN = 0.35
_BAND_EDGE_MARGIN_PX = 8.0
_RAIL_VERTICAL_GAP_PX = 12.0
_LEADER_LINEWIDTH = 0.75
_LEADER_ALPHA = 0.44


@dataclass(frozen=True)
class _DenseSummaryEntry:
    request: _CharacteristicRequest
    color: Any


@dataclass(frozen=True)
class _DenseSummaryGroup:
    x_quantity: Any
    entries: tuple[_DenseSummaryEntry, ...]


def _series_color(axis, display_label: str):
    for line in axis.lines:
        if line.get_label() == display_label:
            return line.get_color()
    return None


def _cluster_requests(axis, requests):
    positioned = []
    for request in requests:
        x = float(request.x_quantity.magnitude)
        y = float(request.y_quantity.magnitude)
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


def _build_dense_summary_groups(
    axis,
    result: PlotResult,
) -> tuple[_DenseSummaryGroup, ...]:
    requests = _characteristic_requests(result)
    positioned: list[tuple[float, _CharacteristicRequest]] = []

    for request in requests:
        x = float(request.x_quantity.magnitude)
        y = float(request.y_quantity.magnitude)
        display_x, _display_y = axis.transData.transform((x, y))
        positioned.append((float(display_x), request))

    positioned.sort(key=lambda item: item[0])
    clusters: list[list[tuple[float, _CharacteristicRequest]]] = []
    for item in positioned:
        if (
            not clusters
            or abs(item[0] - clusters[-1][-1][0]) > _CLUSTER_X_TOLERANCE_PX
        ):
            clusters.append([item])
        else:
            clusters[-1].append(item)

    role_order = {"max": 0, "min": 1}
    groups: list[_DenseSummaryGroup] = []
    for cluster in clusters:
        if len(cluster) < _DENSE_CLUSTER_SIZE:
            continue

        cluster_requests = [item[1] for item in cluster]
        cluster_requests.sort(
            key=lambda request: (request.series_index, role_order[request.role])
        )
        entries: list[_DenseSummaryEntry] = []
        for request in cluster_requests:
            color = _series_color(axis, request.series.display_label)
            if color is not None:
                entries.append(_DenseSummaryEntry(request=request, color=color))

        if len(entries) >= _DENSE_CLUSTER_SIZE:
            groups.append(
                _DenseSummaryGroup(
                    x_quantity=entries[0].request.x_quantity,
                    entries=tuple(entries),
                )
            )

    groups.sort(key=lambda group: float(group.x_quantity.magnitude))
    return tuple(groups)


def _text_box(annotation: Annotation, renderer):
    return Text.get_window_extent(annotation, renderer)


def _request_matches_annotation(
    request: _CharacteristicRequest,
    annotation: Annotation,
) -> bool:
    request_x = float(request.x_quantity.magnitude)
    request_y = float(request.y_quantity.magnitude)
    annotation_x = float(annotation.xy[0])
    annotation_y = float(annotation.xy[1])
    return math.isclose(
        request_x,
        annotation_x,
        rel_tol=1e-10,
        abs_tol=1e-10,
    ) and math.isclose(
        request_y,
        annotation_y,
        rel_tol=1e-10,
        abs_tol=1e-10,
    )


def _remove_dense_inline_annotations(axis, dense_requests) -> None:
    for item in list(axis.texts):
        if not isinstance(item, Annotation):
            continue
        if any(_request_matches_annotation(request, item) for request in dense_requests):
            item.remove()


def _bottom_space_inches(max_cluster_size: int) -> float:
    return max(
        _MIN_BOTTOM_SPACE_IN,
        _BOTTOM_SPACE_PER_LABEL_IN * max_cluster_size + _BOTTOM_SPACE_PADDING_IN,
    )


def _reserve_bottom_space(figure, axis, bottom_space_in: float) -> None:
    """Add vertical callout room while preserving the axes' physical size."""
    old_width, old_height = (float(value) for value in figure.get_size_inches())
    position = axis.get_position()

    axes_left_in = float(position.x0) * old_width
    axes_bottom_in = float(position.y0) * old_height
    axes_width_in = float(position.width) * old_width
    axes_height_in = float(position.height) * old_height

    new_height = old_height + bottom_space_in
    figure.set_size_inches(old_width, new_height, forward=False)
    axis.set_position(
        [
            axes_left_in / old_width,
            (axes_bottom_in + bottom_space_in) / new_height,
            axes_width_in / old_width,
            axes_height_in / new_height,
        ]
    )


def _stack_vertical_centers(
    heights: list[float],
    *,
    lower: float,
    upper: float,
) -> list[float]:
    if not heights:
        return []

    total_height = sum(heights) + _RAIL_VERTICAL_GAP_PX * max(0, len(heights) - 1)
    available = upper - lower
    start = lower + max(0.0, 0.5 * (available - total_height))

    centers = []
    cursor = start
    for height in heights:
        centers.append(cursor + 0.5 * height)
        cursor += height + _RAIL_VERTICAL_GAP_PX
    return centers


def _create_bottom_callout(
    figure,
    axis,
    request: _CharacteristicRequest,
    *,
    x_fraction: float,
    y_fraction: float,
):
    x = float(request.x_quantity.magnitude)
    y = float(request.y_quantity.magnitude)
    line_color = _series_color(axis, request.series.display_label)
    annotation = axis.annotate(
        _coordinate_label(x, y),
        xy=(x, y),
        xycoords="data",
        xytext=(x_fraction, y_fraction),
        textcoords=figure.transFigure,
        ha="left",
        va="center",
        fontsize=8.5,
        color=line_color,
        zorder=7,
        annotation_clip=False,
        arrowprops={
            "arrowstyle": "-",
            "color": line_color,
            "linewidth": _LEADER_LINEWIDTH,
            "alpha": _LEADER_ALPHA,
            "shrinkA": 4.0,
            "shrinkB": 4.0,
        },
    )
    annotation.set_clip_on(False)
    if annotation.arrow_patch is not None:
        annotation.arrow_patch.set_clip_on(False)
        annotation.arrow_patch.set_zorder(2.4)
    return annotation


def _layout_bottom_cluster(
    figure,
    axis,
    cluster,
    *,
    bottom_space_in: float,
) -> list[Annotation]:
    requests = [item[2] for item in cluster]
    requests.sort(
        key=lambda request: float(
            axis.transData.transform(
                (
                    float(request.x_quantity.magnitude),
                    float(request.y_quantity.magnitude),
                )
            )[1]
        )
    )

    figure_height_px = float(figure.bbox.height)
    figure_width_px = float(figure.bbox.width)
    band_upper_px = bottom_space_in * float(figure.dpi) - _BAND_EDGE_MARGIN_PX
    band_lower_px = _BAND_EDGE_MARGIN_PX

    provisional_centers = [
        band_lower_px + (index + 1) * (band_upper_px - band_lower_px) / (len(requests) + 1)
        for index in range(len(requests))
    ]
    annotations = [
        _create_bottom_callout(
            figure,
            axis,
            request,
            x_fraction=0.5,
            y_fraction=center / figure_height_px,
        )
        for request, center in zip(requests, provisional_centers)
    ]

    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    boxes = [_text_box(annotation, renderer) for annotation in annotations]
    heights = [float(box.height) for box in boxes]
    max_width = max(float(box.width) for box in boxes)

    target_centers = _stack_vertical_centers(
        heights,
        lower=band_lower_px,
        upper=band_upper_px,
    )

    anchor_x_values = [
        float(
            axis.transData.transform(
                (
                    float(request.x_quantity.magnitude),
                    float(request.y_quantity.magnitude),
                )
            )[0]
        )
        for request in requests
    ]
    anchor_x = sum(anchor_x_values) / len(anchor_x_values)
    rail_left_px = min(
        max(anchor_x - 0.5 * max_width, _BAND_EDGE_MARGIN_PX),
        figure_width_px - _BAND_EDGE_MARGIN_PX - max_width,
    )
    rail_x_fraction = rail_left_px / figure_width_px

    for annotation, target_y in zip(annotations, target_centers):
        annotation.set_position((rail_x_fraction, target_y / figure_height_px))
        annotation.set_ha("left")
        annotation.set_va("center")

    figure.canvas.draw()
    return annotations


def reflow_dense_characteristic_labels(figure, result: PlotResult) -> None:
    """Move only dense multi-series characteristic clusters to a bottom band.

    Characteristic-point mathematics remains owned by the plotting layer.
    Clusters with fewer than three labels retain the existing inline layout.
    Dense clusters receive aligned callouts below the axes with leader lines.
    The figure grows only vertically so the plot keeps its original visible size.
    """
    if result.kind != "plot" or len(result.series) < 2:
        return

    axis = figure.axes[0]
    requests = _characteristic_requests(result)
    if len(requests) < _DENSE_CLUSTER_SIZE:
        return

    original_canvas = figure.canvas
    FigureCanvasAgg(figure)
    try:
        figure.canvas.draw()
        clusters = _cluster_requests(axis, requests)
        dense_clusters = [
            cluster for cluster in clusters if len(cluster) >= _DENSE_CLUSTER_SIZE
        ]
        if not dense_clusters:
            return

        dense_requests = [
            item[2]
            for cluster in dense_clusters
            for item in cluster
        ]
        _remove_dense_inline_annotations(axis, dense_requests)

        max_cluster_size = max(len(cluster) for cluster in dense_clusters)
        bottom_space_in = _bottom_space_inches(max_cluster_size)
        _reserve_bottom_space(figure, axis, bottom_space_in)
        figure.canvas.draw()

        for cluster in dense_clusters:
            _layout_bottom_cluster(
                figure,
                axis,
                cluster,
                bottom_space_in=bottom_space_in,
            )
    finally:
        figure.set_canvas(original_canvas)
