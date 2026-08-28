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


def _axis_label(name: str, quantity) -> str:
    unit = _unit_label(quantity, moment=_is_moment_plot(name))
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
        return 8, "left"

    fraction = (x - x_min) / span
    if fraction >= 0.85:
        return -10, "right"
    return 10 if fraction <= 0.15 else 8, "left"


def _vertical_annotation_placement(
    y: float,
    y_min: float,
    y_max: float,
    *,
    inverted: bool,
) -> tuple[int, str]:
    span = y_max - y_min
    if span <= 0:
        return 11, "bottom"

    fraction_from_bottom = (y - y_min) / span
    if inverted:
        fraction_from_bottom = 1.0 - fraction_from_bottom

    if fraction_from_bottom >= 0.80:
        return -12, "top"
    if fraction_from_bottom <= 0.20:
        return 12, "bottom"
    return 10, "bottom"


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
    y_min: float,
    y_max: float,
) -> None:
    x = float(x_quantity.magnitude)
    y = float(y_quantity.magnitude)
    offset_x, horizontal_alignment = _horizontal_annotation_placement(
        x,
        x_min,
        x_max,
    )
    offset_y, vertical_alignment = _vertical_annotation_placement(
        y,
        y_min,
        y_max,
        inverted=inverted,
    )
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
        arrowprops={
            "arrowstyle": "-",
            "linewidth": 0.8,
            "color": line_color,
            "alpha": 0.75,
        },
        annotation_clip=False,
    )


def render_plot(result: PlotResult):
    """Create one closed Matplotlib figure from normalized EngCalc plot data."""
    import matplotlib.pyplot as plt

    x_values = [float(value.magnitude) for value in result.x_values]
    y_values = [float(value.magnitude) for value in result.y_values]

    figure, axis = plt.subplots()
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

    inverted = _is_moment_plot(result.display_label)
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
        "y_min": y_min,
        "y_max": y_max,
    }

    if math.isclose(maximum_value, minimum_value, rel_tol=1e-12, abs_tol=1e-12):
        _annotate_extreme(
            axis,
            result.x_values[maximum_index],
            result.y_values[maximum_index],
            "max = min",
            **annotation_kwargs,
        )
    else:
        _annotate_extreme(
            axis,
            result.x_values[maximum_index],
            result.y_values[maximum_index],
            "max",
            **annotation_kwargs,
        )
        _annotate_extreme(
            axis,
            result.x_values[minimum_index],
            result.y_values[minimum_index],
            "min",
            **annotation_kwargs,
        )

    axis.set_xlabel(_axis_label(result.variable, result.x_values[0]))
    axis.set_ylabel(_axis_label(result.display_label, result.y_values[0]))
    axis.set_title(result.display_label, pad=10, fontweight="semibold")
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.set_axisbelow(True)
    axis.grid(True, which="major", alpha=0.22)
    axis.margins(x=0.02, y=0.12)
    figure.tight_layout()

    # IPython displays the returned figure explicitly. Closing it here prevents
    # pyplot/Jupyter from also auto-rendering the same figure a second time.
    plt.close(figure)
    return figure
