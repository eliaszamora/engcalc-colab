from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Annotation

from .models import PlotResult
from .plotting import (
    _CharacteristicRequest,
    _characteristic_requests,
    _compact_number,
    _quantity_label,
    _unit_label,
)


_CLUSTER_X_TOLERANCE_PX = 14.0
_DENSE_CLUSTER_SIZE = 3
_SUMMARY_MAX_COLUMNS = 2
_SUMMARY_TITLE_HEIGHT_IN = 0.18
_SUMMARY_GROUP_HEADER_HEIGHT_IN = 0.16
_SUMMARY_ROW_HEIGHT_IN = 0.14
_SUMMARY_PANEL_PADDING_IN = 0.08
_SUMMARY_GROUP_GAP_FRACTION = 0.05


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


def _reserve_summary_space(figure, axis, summary_height_in: float) -> None:
    """Add vertical summary room while preserving the axes' physical size."""
    old_width, old_height = (float(value) for value in figure.get_size_inches())
    position = axis.get_position()

    axes_left_in = float(position.x0) * old_width
    axes_bottom_in = float(position.y0) * old_height
    axes_width_in = float(position.width) * old_width
    axes_height_in = float(position.height) * old_height

    new_height = old_height + summary_height_in
    figure.set_size_inches(old_width, new_height, forward=False)
    axis.set_position(
        [
            axes_left_in / old_width,
            (axes_bottom_in + summary_height_in) / new_height,
            axes_width_in / old_width,
            axes_height_in / new_height,
        ]
    )


def _summary_height_inches(groups: tuple[_DenseSummaryGroup, ...]) -> float:
    grid_rows = [
        groups[index:index + _SUMMARY_MAX_COLUMNS]
        for index in range(0, len(groups), _SUMMARY_MAX_COLUMNS)
    ]
    body_height = sum(
        _SUMMARY_GROUP_HEADER_HEIGHT_IN
        + _SUMMARY_ROW_HEIGHT_IN * max(len(group.entries) for group in grid_row)
        for grid_row in grid_rows
    )
    return (
        2 * _SUMMARY_PANEL_PADDING_IN
        + _SUMMARY_TITLE_HEIGHT_IN
        + body_height
    )


def _group_x_header(group: _DenseSummaryGroup) -> str:
    quantity = group.x_quantity
    value = _compact_number(float(quantity.magnitude))
    unit = _unit_label(quantity)
    return f"x = {value}" if not unit else f"x = {value} {unit}"


def _common_y_unit(
    groups: tuple[_DenseSummaryGroup, ...],
    *,
    moment: bool,
) -> str | None:
    units = {
        _unit_label(entry.request.y_quantity, moment=moment)
        for group in groups
        for entry in group.entries
    }
    return next(iter(units)) if len(units) == 1 else None


def _entry_value_text(
    entry: _DenseSummaryEntry,
    *,
    moment: bool,
    common_unit: str | None,
) -> str:
    if common_unit is not None:
        return _compact_number(float(entry.request.y_quantity.magnitude))
    return _quantity_label(entry.request.y_quantity, moment=moment)


def _render_summary_panel(
    figure,
    axis,
    groups: tuple[_DenseSummaryGroup, ...],
    *,
    summary_height_in: float,
    moment: bool,
) -> None:
    _figure_width, figure_height = (
        float(value) for value in figure.get_size_inches()
    )
    main_position = axis.get_position()
    panel_bottom_in = _SUMMARY_PANEL_PADDING_IN
    panel_height_in = summary_height_in - 2 * _SUMMARY_PANEL_PADDING_IN

    summary = figure.add_axes(
        [
            float(main_position.x0),
            panel_bottom_in / figure_height,
            float(main_position.width),
            panel_height_in / figure_height,
        ]
    )
    summary.set_gid("engcalc-characteristic-summary")
    summary.set_xlim(0.0, 1.0)
    summary.set_ylim(0.0, 1.0)
    summary.set_axis_off()

    common_unit = _common_y_unit(groups, moment=moment)
    title_fraction = _SUMMARY_TITLE_HEIGHT_IN / panel_height_in
    group_header_fraction = _SUMMARY_GROUP_HEADER_HEIGHT_IN / panel_height_in
    row_fraction = _SUMMARY_ROW_HEIGHT_IN / panel_height_in

    title = summary.text(
        0.0,
        0.98,
        "Characteristic points",
        transform=summary.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        fontweight="semibold",
    )
    title.set_gid("engcalc-summary-title")

    cursor_y = 1.0 - title_fraction
    grid_rows = tuple(
        groups[index:index + _SUMMARY_MAX_COLUMNS]
        for index in range(0, len(groups), _SUMMARY_MAX_COLUMNS)
    )

    for grid_row in grid_rows:
        column_count = len(grid_row)
        cell_width = (
            1.0 - _SUMMARY_GROUP_GAP_FRACTION * (column_count - 1)
        ) / column_count
        max_entries = max(len(group.entries) for group in grid_row)

        for column_index, group in enumerate(grid_row):
            cell_left = column_index * (
                cell_width + _SUMMARY_GROUP_GAP_FRACTION
            )
            cell_right = cell_left + cell_width

            header = summary.text(
                cell_left,
                cursor_y,
                _group_x_header(group),
                transform=summary.transAxes,
                ha="left",
                va="top",
                fontsize=8.2,
                fontweight="semibold",
            )
            header.set_gid("engcalc-summary-group-header")

            value_header_text = (
                "Value"
                if common_unit is None
                else f"Value [{common_unit}]"
            )
            summary.text(
                cell_right,
                cursor_y,
                value_header_text,
                transform=summary.transAxes,
                ha="right",
                va="top",
                fontsize=7.8,
            )

            separator_y = cursor_y - 0.72 * group_header_fraction
            summary.plot(
                [cell_left, cell_right],
                [separator_y, separator_y],
                linewidth=0.6,
                alpha=0.35,
                transform=summary.transAxes,
            )

        rows_top = cursor_y - group_header_fraction

        for column_index, group in enumerate(grid_row):
            cell_left = column_index * (
                cell_width + _SUMMARY_GROUP_GAP_FRACTION
            )
            cell_right = cell_left + cell_width
            marker_x = cell_left + 0.015 * cell_width
            label_x = cell_left + 0.055 * cell_width
            role_x = cell_left + 0.57 * cell_width
            value_x = cell_right

            for row_index, entry in enumerate(group.entries):
                row_y = rows_top - (row_index + 0.5) * row_fraction
                summary.plot(
                    [marker_x],
                    [row_y],
                    marker="o",
                    markersize=4.0,
                    linestyle="None",
                    color=entry.color,
                    transform=summary.transAxes,
                    clip_on=False,
                )

                label = summary.text(
                    label_x,
                    row_y,
                    entry.request.series.display_label,
                    transform=summary.transAxes,
                    ha="left",
                    va="center",
                    fontsize=8.0,
                    color=entry.color,
                )
                label.set_gid("engcalc-summary-entry-label")

                role = summary.text(
                    role_x,
                    row_y,
                    entry.request.role,
                    transform=summary.transAxes,
                    ha="left",
                    va="center",
                    fontsize=7.8,
                )
                role.set_gid("engcalc-summary-entry-role")

                value = summary.text(
                    value_x,
                    row_y,
                    _entry_value_text(
                        entry,
                        moment=moment,
                        common_unit=common_unit,
                    ),
                    transform=summary.transAxes,
                    ha="right",
                    va="center",
                    fontsize=8.0,
                )
                value.set_gid("engcalc-summary-entry-value")

        cursor_y = rows_top - max_entries * row_fraction


def reflow_dense_characteristic_labels(figure, result: PlotResult) -> None:
    """Move dense multi-series characteristic text to a compact summary panel."""
    if result.kind != "plot" or len(result.series) < 2:
        return

    axis = figure.axes[0]
    original_canvas = figure.canvas
    FigureCanvasAgg(figure)
    try:
        figure.canvas.draw()
        groups = _build_dense_summary_groups(axis, result)
        if not groups:
            return

        dense_requests = tuple(
            entry.request
            for group in groups
            for entry in group.entries
        )
        _remove_dense_inline_annotations(axis, dense_requests)

        summary_height_in = _summary_height_inches(groups)
        _reserve_summary_space(figure, axis, summary_height_in)
        _render_summary_panel(
            figure,
            axis,
            groups,
            summary_height_in=summary_height_in,
            moment=all(series.is_moment for series in result.series),
        )
        figure.canvas.draw()
    finally:
        figure.set_canvas(original_canvas)
