from __future__ import annotations

import math
import re

from .models import PlotResult


_MOMENT_LABEL = re.compile(r"^M(?:_[A-Za-z0-9]+|[0-9]+)?\(")


def _unit_label(quantity) -> str:
    if quantity.dimensionless:
        return ""
    return f"{quantity.units:~P}"


def _axis_label(name: str, quantity) -> str:
    unit = _unit_label(quantity)
    return name if not unit else f"{name} [{unit}]"


def _quantity_label(quantity) -> str:
    magnitude = float(quantity.magnitude)
    unit = _unit_label(quantity)
    value = f"{magnitude:.2f}"
    return value if not unit else f"{value} {unit}"


def _is_moment_plot(label: str) -> bool:
    return _MOMENT_LABEL.match(label.strip()) is not None


def _extreme_indices(values: list[float]) -> tuple[int, int]:
    maximum = max(range(len(values)), key=values.__getitem__)
    minimum = min(range(len(values)), key=values.__getitem__)
    return maximum, minimum


def _annotate_extreme(
    axis,
    x_quantity,
    y_quantity,
    label: str,
    *,
    is_maximum: bool,
    inverted: bool,
    line_color,
) -> None:
    x = float(x_quantity.magnitude)
    y = float(y_quantity.magnitude)
    move_up = (is_maximum and inverted) or (not is_maximum and not inverted)
    offset_y = 11 if move_up else -18
    vertical_alignment = "bottom" if move_up else "top"
    text = f"{label} = {_quantity_label(y_quantity)}\nx = {_quantity_label(x_quantity)}"

    axis.annotate(
        text,
        xy=(x, y),
        xytext=(8, offset_y),
        textcoords="offset points",
        ha="left",
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

    axis.scatter(
        [x_values[0], x_values[-1]],
        [y_values[0], y_values[-1]],
        s=28,
        color=line_color,
        zorder=4,
    )

    maximum_index, minimum_index = _extreme_indices(y_values)
    extreme_indices = sorted({maximum_index, minimum_index})
    axis.scatter(
        [x_values[index] for index in extreme_indices],
        [y_values[index] for index in extreme_indices],
        s=38,
        color=line_color,
        zorder=5,
    )

    inverted = _is_moment_plot(result.display_label)
    if inverted:
        axis.invert_yaxis()

    maximum_value = y_values[maximum_index]
    minimum_value = y_values[minimum_index]
    if math.isclose(maximum_value, minimum_value, rel_tol=1e-12, abs_tol=1e-12):
        _annotate_extreme(
            axis,
            result.x_values[maximum_index],
            result.y_values[maximum_index],
            "max = min",
            is_maximum=True,
            inverted=inverted,
            line_color=line_color,
        )
    else:
        _annotate_extreme(
            axis,
            result.x_values[maximum_index],
            result.y_values[maximum_index],
            "max",
            is_maximum=True,
            inverted=inverted,
            line_color=line_color,
        )
        _annotate_extreme(
            axis,
            result.x_values[minimum_index],
            result.y_values[minimum_index],
            "min",
            is_maximum=False,
            inverted=inverted,
            line_color=line_color,
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
