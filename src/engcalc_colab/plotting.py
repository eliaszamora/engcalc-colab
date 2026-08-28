from __future__ import annotations

import math
import re

from .models import PlotResult


_MOMENT_LABEL = re.compile(r"^M(?:_[A-Za-z0-9]+|[0-9]+)?\(")
_FORCE_UNITS = {"N", "kN", "MN", "GN", "kgf", "tonf"}
_LENGTH_UNITS = {"mm", "cm", "m", "km"}


def _is_moment_plot(label: str) -> bool:
    return _MOMENT_LABEL.match(label.strip()) is not None


def _force_length_unit_order(unit: str) -> str:
    """Prefer the structural convention force·length for simple moments."""
    parts = unit.split("·")
    if (
        len(parts) == 2
        and parts[0] in _LENGTH_UNITS
        and parts[1] in _FORCE_UNITS
    ):
        return f"{parts[1]}·{parts[0]}"
    return unit


def _unit_label(quantity, *, moment: bool = False) -> str:
    if quantity.dimensionless:
        return ""
    unit = f"{quantity.units:~P}"
    return _force_length_unit_order(unit) if moment else unit


def _axis_label(name: str, quantity, *, moment: bool = False) -> str:
    unit = _unit_label(quantity, moment=moment)
    return name if not unit else f"{name} [{unit}]"


def _quantity_label(quantity, *, moment: bool = False) -> str:
    magnitude = float(quantity.magnitude)
    unit = _unit_label(quantity, moment=moment)
    value = f"{magnitude:.2f}"
    return value if not unit else f"{value} {unit}"


def _extreme_indices(values: list[float]) -> tuple[int, int]:
    maximum = max(range(len(values)), key=values.__getitem__)
    minimum = min(range(len(values)), key=values.__getitem__)
    return maximum, minimum


def _horizontal_annotation_placement(
    x: float,
    x_min: float,
    x_max: float,
) -> tuple[int, str]:
    span = x_max - x_min
    if span <= 0:
        return 16, "left"

    fraction = (x - x_min) / span
    if fraction >= 0.85:
        return -16, "right"
    return 16 if fraction <= 0.15 else 14, "left"


def _vertical_annotation_placement(
    label: str,
    *,
    inverted: bool,
) -> tuple[int, str]:
    """Move extrema callouts visually away from the diagram lobe."""
    if label == "max = min":
        return 26, "bottom"

    mathematical_maximum = label == "max"
    visually_above = (
        mathematical_maximum and not inverted
    ) or (
        not mathematical_maximum and inverted
    )

    if visually_above:
        return 26, "bottom"
    return -26, "top"


def _extrema_are_close(
    x_a: float,
    y_a: float,
    x_b: float,
    y_b: float,
    *,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> bool:
    x_span = x_max - x_min
    y_span = y_max - y_min
    if x_span <= 0 or y_span <= 0:
        return True

    relative_x = abs(x_a - x_b) / x_span
    relative_y = abs(y_a - y_b) / y_span
    return relative_x < 0.16 and relative_y < 0.18


def _annotate_extreme(
    axis,
    x_quantity,
    y_quantity,
    label: str,
    *,
    inverted: bool,
    line_color,
    x_min: float,
    x_max: float,
    stagger: int = 0,
) -> None:
    x = float(x_quantity.magnitude)
    y = float(y_quantity.magnitude)
    offset_x, horizontal_alignment = _horizontal_annotation_placement(
        x,
        x_min,
        x_max,
    )
    offset_y, vertical_alignment = _vertical_annotation_placement(
        label,
        inverted=inverted,
    )

    if stagger:
        offset_x += stagger if offset_x >= 0 else -stagger
        offset_y += 6 if offset_y >= 0 else -6

    text = (
        f"{label} = {_quantity_label(y_quantity, moment=inverted)}\n"
        f"x = {_quantity_label(x_quantity)}"
    )

    axis.annotate(
        text,
        xy=(x, y),
        xytext=(offset_x, offset_y),
        textcoords="offset points",
        ha=horizontal_alignment,
        va=vertical_alignment,
        fontsize=9,
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": axis.get_facecolor(),
            "edgecolor": line_color,
            "linewidth": 0.8,
            "alpha": 0.94,
        },
        arrowprops={
            "arrowstyle": "-",
            "linewidth": 0.8,
            "color": line_color,
            "alpha": 0.75,
            "shrinkA": 5,
            "shrinkB": 4,
        },
        annotation_clip=False,
    )


def _style_axes(axis) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.set_axisbelow(True)
    axis.grid(True, which="major", alpha=0.22)


def _render_single_series(figure, axis, result: PlotResult) -> None:
    series = result.series[0]
    x_values = [float(value.magnitude) for value in result.x_values]
    y_values = [float(value.magnitude) for value in series.y_values]

    line = axis.plot(x_values, y_values, linewidth=2.2, zorder=3)[0]
    line_color = line.get_color()

    axis.fill_between(
        x_values,
        y_values,
        0.0,
        color=line_color,
        alpha=0.12,
        zorder=1,
    )
    axis.axhline(
        0.0,
        linewidth=1.0,
        color=axis.spines["bottom"].get_edgecolor(),
        alpha=0.75,
        zorder=2,
    )

    maximum_index, minimum_index = _extreme_indices(y_values)
    extreme_indices = {maximum_index, minimum_index}
    marker_indices = sorted({0, len(x_values) - 1} | extreme_indices)
    marker_sizes = [32 if index in extreme_indices else 20 for index in marker_indices]
    axis.scatter(
        [x_values[index] for index in marker_indices],
        [y_values[index] for index in marker_indices],
        s=marker_sizes,
        color=line_color,
        zorder=4,
    )

    inverted = series.is_moment
    if inverted:
        axis.invert_yaxis()

    x_min = min(x_values)
    x_max = max(x_values)
    y_min = min(y_values)
    y_max = max(y_values)
    maximum_value = y_values[maximum_index]
    minimum_value = y_values[minimum_index]

    annotation_kwargs = {
        "inverted": inverted,
        "line_color": line_color,
        "x_min": x_min,
        "x_max": x_max,
    }

    if math.isclose(maximum_value, minimum_value, rel_tol=1e-12, abs_tol=1e-12):
        _annotate_extreme(
            axis,
            result.x_values[maximum_index],
            series.y_values[maximum_index],
            "max = min",
            **annotation_kwargs,
        )
    else:
        close_extrema = _extrema_are_close(
            x_values[maximum_index],
            y_values[maximum_index],
            x_values[minimum_index],
            y_values[minimum_index],
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
        )
        _annotate_extreme(
            axis,
            result.x_values[maximum_index],
            series.y_values[maximum_index],
            "max",
            **annotation_kwargs,
        )
        _annotate_extreme(
            axis,
            result.x_values[minimum_index],
            series.y_values[minimum_index],
            "min",
            stagger=10 if close_extrema else 0,
            **annotation_kwargs,
        )

    axis.set_xlabel(_axis_label(result.variable, result.x_values[0]))
    axis.set_ylabel(
        _axis_label(
            result.display_label,
            series.y_values[0],
            moment=series.is_moment,
        )
    )
    axis.set_title(result.display_label, pad=10, fontweight="semibold")
    _style_axes(axis)
    axis.margins(x=0.02, y=0.16)
    figure.tight_layout()


def _characteristic_panel_text(result: PlotResult) -> str:
    lines = ["Characteristic values"]
    for series in result.series:
        values = [float(value.magnitude) for value in series.y_values]
        maximum_index, minimum_index = _extreme_indices(values)
        lines.extend([
            series.display_label,
            (
                "max = "
                f"{_quantity_label(series.y_values[maximum_index], moment=series.is_moment)}"
                "    x = "
                f"{_quantity_label(result.x_values[maximum_index])}"
            ),
            (
                "min = "
                f"{_quantity_label(series.y_values[minimum_index], moment=series.is_moment)}"
                "    x = "
                f"{_quantity_label(result.x_values[minimum_index])}"
            ),
            "",
        ])
    return "\n".join(lines).rstrip()


_PANEL_CORNERS = ("upper right", "upper left", "lower right", "lower left")


def _panel_footprint(text: str) -> tuple[float, float]:
    lines = text.splitlines() or [""]
    max_chars = max(len(line) for line in lines)
    width = min(0.46, max(0.22, 0.14 + 0.006 * max_chars))
    height = min(0.72, max(0.16, 0.08 + 0.043 * len(lines)))
    return width, height


def _data_to_axes_fraction(axis, x: float, y: float) -> tuple[float, float]:
    x0, x1 = axis.get_xlim()
    y0, y1 = axis.get_ylim()
    return (
        0.5 if x1 == x0 else (x - x0) / (x1 - x0),
        0.5 if y1 == y0 else (y - y0) / (y1 - y0),
    )


def _panel_rectangle(corner: str, width: float, height: float):
    padding = 0.02
    if corner == "upper right":
        return (1.0 - padding - width, 1.0 - padding - height, 1.0 - padding, 1.0 - padding)
    if corner == "upper left":
        return (padding, 1.0 - padding - height, padding + width, 1.0 - padding)
    if corner == "lower right":
        return (1.0 - padding - width, padding, 1.0 - padding, padding + height)
    return (padding, padding, padding + width, padding + height)


def _choose_panel_corner(
    axis,
    data_xy: list[tuple[float, float]],
    text: str,
    legend_corner: str | None,
) -> str:
    width, height = _panel_footprint(text)
    axes_points = [
        _data_to_axes_fraction(axis, x, y)
        for x, y in data_xy
    ]

    scored = []
    for order, corner in enumerate(_PANEL_CORNERS):
        left, bottom, right, top = _panel_rectangle(corner, width, height)
        expanded = (left - 0.04, bottom - 0.04, right + 0.04, top + 0.04)
        score = 1000 if corner == legend_corner else 0
        for x, y in axes_points:
            if left <= x <= right and bottom <= y <= top:
                score += 3
            if expanded[0] <= x <= expanded[2] and expanded[1] <= y <= expanded[3]:
                score += 1
        scored.append((score, order, corner))

    return min(scored)[2]


def _add_characteristic_panel(
    axis,
    text: str,
    data_xy: list[tuple[float, float]],
    legend_corner: str | None = None,
):
    corner = _choose_panel_corner(
        axis,
        data_xy,
        text,
        legend_corner=legend_corner,
    )
    anchors = {
        "upper right": (0.98, 0.98, "right", "top"),
        "upper left": (0.02, 0.98, "left", "top"),
        "lower right": (0.98, 0.02, "right", "bottom"),
        "lower left": (0.02, 0.02, "left", "bottom"),
    }
    x, y, ha, va = anchors[corner]
    return axis.text(
        x,
        y,
        text,
        transform=axis.transAxes,
        ha=ha,
        va=va,
        fontsize=8.5,
        zorder=8,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": axis.get_facecolor(),
            "edgecolor": axis.spines["bottom"].get_edgecolor(),
            "linewidth": 0.8,
            "alpha": 0.94,
        },
    )


def _render_multi_series(figure, axis, result: PlotResult) -> None:
    x_values = [float(value.magnitude) for value in result.x_values]
    panel_data: list[tuple[float, float]] = []

    for series in result.series:
        y_values = [float(value.magnitude) for value in series.y_values]
        panel_data.extend(zip(x_values, y_values))
        line = axis.plot(
            x_values,
            y_values,
            linewidth=2.0,
            label=series.display_label,
            zorder=3,
        )[0]
        line_color = line.get_color()

        maximum_index, minimum_index = _extreme_indices(y_values)
        marker_indices = sorted({maximum_index, minimum_index})
        axis.scatter(
            [x_values[index] for index in marker_indices],
            [y_values[index] for index in marker_indices],
            s=26,
            color=line_color,
            zorder=4,
        )

    axis.axhline(
        0.0,
        linewidth=1.0,
        color=axis.spines["bottom"].get_edgecolor(),
        alpha=0.75,
        zorder=2,
    )
    axis.legend(loc="upper right")

    moment = all(series.is_moment for series in result.series)
    if moment:
        axis.invert_yaxis()

    axis.set_xlabel(_axis_label(result.variable, result.x_values[0]))
    axis.set_ylabel(
        _axis_label(
            result.display_label,
            result.series[0].y_values[0],
            moment=moment,
        )
    )
    axis.set_title(result.display_label, pad=10, fontweight="semibold")
    _style_axes(axis)
    axis.margins(x=0.02, y=0.12)

    _add_characteristic_panel(
        axis,
        _characteristic_panel_text(result),
        panel_data,
        legend_corner="upper right",
    )
    figure.tight_layout()


def _envelope_characteristic_panel_text(result: PlotResult) -> str:
    maximum_series, minimum_series = result.series
    maximum_values = [float(value.magnitude) for value in maximum_series.y_values]
    minimum_values = [float(value.magnitude) for value in minimum_series.y_values]
    maximum_index = max(range(len(maximum_values)), key=maximum_values.__getitem__)
    minimum_index = min(range(len(minimum_values)), key=minimum_values.__getitem__)
    moment = maximum_series.is_moment

    return "\n".join([
        "Envelope characteristic values",
        (
            "max = "
            f"{_quantity_label(maximum_series.y_values[maximum_index], moment=moment)}"
            "    x = "
            f"{_quantity_label(result.x_values[maximum_index])}"
        ),
        (
            "min = "
            f"{_quantity_label(minimum_series.y_values[minimum_index], moment=moment)}"
            "    x = "
            f"{_quantity_label(result.x_values[minimum_index])}"
        ),
    ])


def _render_envelope(figure, axis, result: PlotResult) -> None:
    x_values = [float(value.magnitude) for value in result.x_values]
    panel_data: list[tuple[float, float]] = []

    for source_series in result.source_series:
        source_y = [float(value.magnitude) for value in source_series.y_values]
        panel_data.extend(zip(x_values, source_y))
        axis.plot(
            x_values,
            source_y,
            linewidth=1.0,
            alpha=0.22,
            label="_nolegend_",
            zorder=1,
        )

    maximum_series, minimum_series = result.series
    maximum_y = [float(value.magnitude) for value in maximum_series.y_values]
    minimum_y = [float(value.magnitude) for value in minimum_series.y_values]
    panel_data.extend(zip(x_values, maximum_y))
    panel_data.extend(zip(x_values, minimum_y))

    maximum_line = axis.plot(
        x_values,
        maximum_y,
        linewidth=2.5,
        alpha=1.0,
        label=maximum_series.display_label,
        zorder=4,
    )[0]
    minimum_line = axis.plot(
        x_values,
        minimum_y,
        linewidth=2.5,
        alpha=1.0,
        label=minimum_series.display_label,
        zorder=4,
    )[0]

    axis.fill_between(
        x_values,
        minimum_y,
        maximum_y,
        color=maximum_line.get_color(),
        alpha=0.10,
        zorder=2,
    )
    axis.axhline(
        0.0,
        linewidth=1.0,
        color=axis.spines["bottom"].get_edgecolor(),
        alpha=0.75,
        label="_zero",
        zorder=3,
    )
    axis.legend(handles=[maximum_line, minimum_line], loc="upper right")

    moment = maximum_series.is_moment
    if moment:
        axis.invert_yaxis()

    axis.set_xlabel(_axis_label(result.variable, result.x_values[0]))
    axis.set_ylabel(
        _axis_label(
            result.display_label,
            maximum_series.y_values[0],
            moment=moment,
        )
    )
    axis.set_title(
        f"{result.display_label} envelope",
        pad=10,
        fontweight="semibold",
    )
    _style_axes(axis)
    axis.margins(x=0.02, y=0.12)

    _add_characteristic_panel(
        axis,
        _envelope_characteristic_panel_text(result),
        panel_data,
        legend_corner="upper right",
    )
    figure.tight_layout()


def render_plot(result: PlotResult):
    """Create one closed Matplotlib figure from normalized EngCalc plot data."""
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots()
    if result.kind == "envelope":
        _render_envelope(figure, axis, result)
    elif len(result.series) == 1:
        _render_single_series(figure, axis, result)
    else:
        _render_multi_series(figure, axis, result)

    # IPython displays the returned figure explicitly. Closing it here prevents
    # pyplot/Jupyter from also auto-rendering the same figure a second time.
    plt.close(figure)
    return figure
