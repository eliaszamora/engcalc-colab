from __future__ import annotations

from .label_layout import reflow_dense_characteristic_labels
from .models import PlotResult
from .plotting import _axis_label, render_plot


def render_presented_plot(result: PlotResult):
    """Render a plot/envelope and apply user-facing presentation polish."""
    figure = render_plot(result)
    axis = figure.axes[0]

    has_text_override = (
        result.title is not None
        or result.xlabel is not None
        or result.ylabel is not None
    )
    if result.title is not None:
        axis.set_title(result.title, pad=10, fontweight=700)
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

    if has_text_override:
        figure.tight_layout()

    reflow_dense_characteristic_labels(figure, result)
    return figure
