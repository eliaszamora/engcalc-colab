from __future__ import annotations

from .models import PlotResult
from .plotting import _axis_label, render_plot


def render_presented_plot(result: PlotResult):
    """Render a plot/envelope and apply optional user-facing text overrides."""
    figure = render_plot(result)
    if result.title is None and result.xlabel is None and result.ylabel is None:
        return figure

    axis = figure.axes[0]
    if result.title is not None:
        axis.set_title(result.title, pad=10, fontweight="semibold")
    if result.xlabel is not None:
        axis.set_xlabel(_axis_label(result.xlabel, result.x_values[0]))
    if result.ylabel is not None:
        first_series = result.series[0]
        axis.set_ylabel(
            _axis_label(
                result.ylabel,
                first_series.y_values[0],
                moment=first_series.is_moment,
            )
        )

    figure.tight_layout()
    return figure
