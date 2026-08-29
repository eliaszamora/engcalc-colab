from __future__ import annotations

import math

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Annotation, Text

from .models import PlotResult
from .plotting import _coordinate_label, _series_response_symbol


_CLUSTER_X_TOLERANCE_PX = 14.0
_DENSE_CLUSTER_SIZE = 3
_SIDE_SPACE_IN = 1.65
_LEFT_RAIL_OFFSET_IN = 1.00
_RIGHT_RAIL_OFFSET_IN = 0.28
_RAIL_EDGE_MARGIN_PX = 7.0
_RAIL_VERTICAL_GAP_PX = 12.0
_LEADER_LINEWIDTH = 0.75
_LEADER_ALPHA = 0.52


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


def _spread_vertical_centers(
    desired_centers: list[float],
    heights: list[float],
    *,
    lower: float,
    upper: float,
) -> list[float]:
    """Preserve reading order while enforcing robust vertical clearance."""
    if not desired_centers:
        return []

    centers = list(desired_centers)
    for index in range(1, len(centers)):
        minimum_separation = (
            0.5 * heights[index - 1]
            + 0.5 * heights[index]
            + _RAIL_VERTICAL_GAP_PX
        )
        centers[index] = max(centers[index], centers[index - 1] + minimum_separation)

    preferred_shift = sum(
        desired - current for desired, current in zip(desired_centers, centers)
    ) / len(centers)
    minimum_shift = lower + 0.5 * heights[0] - centers[0]
    maximum_shift = upper - 0.5 * heights[-1] - centers[-1]
    shift = min(max(preferred_shift, minimum_shift), maximum_shift)
    return [center + shift for center in centers]


def _cluster_side(axis, cluster) -> str:
    x_values = [float(item[2][0].magnitude) for item in cluster]
    anchor_x = sum(x_values) / len(x_values)
    x0, x1 = axis.get_xlim()
    if math.isclose(x0, x1, rel_tol=0.0, abs_tol=1e-15):
        return "right"
    fraction = (anchor_x - x0) / (x1 - x0)
    return "left" if fraction < 0.5 else "right"


def _reserve_side_space(figure, axis, *, use_left: bool, use_right: bool) -> None:
    """Add external rail room while preserving the axes' physical size."""
    if not use_left and not use_right:
        return

    old_width, old_height = (float(value) for value in figure.get_size_inches())
    position = axis.get_position()
    axes_left_in = float(position.x0) * old_width
    axes_bottom_fraction = float(position.y0)
    axes_width_in = float(position.width) * old_width
    axes_height_fraction = float(position.height)

    extra_left = _SIDE_SPACE_IN if use_left else 0.0
    extra_right = _SIDE_SPACE_IN if use_right else 0.0
    new_width = old_width + extra_left + extra_right
    figure.set_size_inches(new_width, old_height, forward=False)
    axis.set_position(
        [
            (axes_left_in + extra_left) / new_width,
            axes_bottom_fraction,
            axes_width_in / new_width,
            axes_height_fraction,
        ]
    )


def _rail_x_fraction(figure, axis, side: str) -> float:
    width = float(figure.get_figwidth())
    position = axis.get_position()
    if side == "left":
        return float(position.x0) - _LEFT_RAIL_OFFSET_IN / width
    return float(position.x1) + _RIGHT_RAIL_OFFSET_IN / width


def _text_box(annotation: Annotation, renderer):
    return Text.get_window_extent(annotation, renderer)


def _request_matches_annotation(request, annotation: Annotation) -> bool:
    x_quantity, y_quantity, *_ = request
    request_x = float(x_quantity.magnitude)
    request_y = float(y_quantity.magnitude)
    annotation_x = float(annotation.xy[0])
    annotation_y = float(annotation.xy[1])
    return math.isclose(request_x, annotation_x, rel_tol=1e-10, abs_tol=1e-10) and math.isclose(
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


def _create_external_callout(figure, axis, request, *, side: str, rail_x: float, y_fraction: float):
    x_quantity, y_quantity, _response_label, _role, _inverted, line_color = request
    x = float(x_quantity.magnitude)
    y = float(y_quantity.magnitude)
    annotation = axis.annotate(
        _coordinate_label(x, y),
        xy=(x, y),
        xycoords="data",
        xytext=(rail_x, y_fraction),
        textcoords=figure.transFigure,
        ha="right" if side == "left" else "left",
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


def _layout_external_side(figure, axis, entries, *, side: str) -> list[Annotation]:
    """Lay one side's dense requests on a single external aligned rail."""
    if not entries:
        return []

    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    axes_box = axis.get_window_extent(renderer)
    rail_x = _rail_x_fraction(figure, axis, side)
    figure_height_px = float(figure.bbox.height)

    ordered = sorted(
        entries,
        key=lambda request: float(
            axis.transData.transform(
                (float(request[0].magnitude), float(request[1].magnitude))
            )[1]
        ),
    )
    desired_centers = [
        float(
            axis.transData.transform(
                (float(request[0].magnitude), float(request[1].magnitude))
            )[1]
        )
        for request in ordered
    ]

    annotations = [
        _create_external_callout(
            figure,
            axis,
            request,
            side=side,
            rail_x=rail_x,
            y_fraction=desired_y / figure_height_px,
        )
        for request, desired_y in zip(ordered, desired_centers)
    ]

    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    heights = [float(_text_box(annotation, renderer).height) for annotation in annotations]
    target_centers = _spread_vertical_centers(
        desired_centers,
        heights,
        lower=float(axes_box.y0 + _RAIL_EDGE_MARGIN_PX),
        upper=float(axes_box.y1 - _RAIL_EDGE_MARGIN_PX),
    )
    for annotation, target_y in zip(annotations, target_centers):
        annotation.set_position((rail_x, target_y / figure_height_px))

    figure.canvas.draw()
    return annotations


def reflow_dense_characteristic_labels(figure, result: PlotResult) -> None:
    """Move only dense multi-series characteristic clusters to external rails.

    Characteristic-point mathematics remains owned by the plotting layer.
    Clusters with fewer than three labels retain the existing inline layout.
    Dense clusters receive external aligned callouts with leader lines.
    """
    if result.kind != "plot" or len(result.series) < 2:
        return

    axis = figure.axes[0]
    requests = _characteristic_requests(axis, result)
    if len(requests) < _DENSE_CLUSTER_SIZE:
        return

    original_canvas = figure.canvas
    FigureCanvasAgg(figure)
    try:
        figure.canvas.draw()
        clusters = _cluster_requests(axis, requests)
        dense_clusters = [cluster for cluster in clusters if len(cluster) >= _DENSE_CLUSTER_SIZE]
        if not dense_clusters:
            return

        side_entries = {"left": [], "right": []}
        dense_requests = []
        for cluster in dense_clusters:
            side = _cluster_side(axis, cluster)
            for _, _, request in cluster:
                side_entries[side].append(request)
                dense_requests.append(request)

        _remove_dense_inline_annotations(axis, dense_requests)
        _reserve_side_space(
            figure,
            axis,
            use_left=bool(side_entries["left"]),
            use_right=bool(side_entries["right"]),
        )
        figure.canvas.draw()

        _layout_external_side(figure, axis, side_entries["left"], side="left")
        _layout_external_side(figure, axis, side_entries["right"], side="right")
    finally:
        figure.set_canvas(original_canvas)
