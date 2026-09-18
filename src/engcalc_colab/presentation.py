from __future__ import annotations

import matplotlib

from .label_layout import reflow_dense_characteristic_labels
from .models import PlotResult
from .plotting import _axis_label, render_plot

# The page's type, for a figure. MathJax sets the mathematics around a figure in a serif,
# and matplotlib set everything on it in DejaVu Sans - the engineer's "hay fuentes
# distintas", in the one output that had not yet been brought into the page. DejaVu
# Serif and mathtext's `dejavuserif` both ship with matplotlib, so there is nothing for
# Colab to lack; `cmr10`, the closer match to MathJax, has no bold and the title is bold.
_PAGE_TYPE = {
    "font.family": "DejaVu Serif",
    "mathtext.fontset": "dejavuserif",
}


def render_presented_plot(result: PlotResult):
    """Render a plot/envelope and apply user-facing presentation polish.

    Built inside the page's type, in an `rc_context`, and nothing afterwards. Each text
    takes its face and its mathematics' face when it is made and keeps both, so the
    figure reads the same when Colab draws it outside the context, and a tick matplotlib
    adds on a later draw copies the first tick's. Built in it rather than restyled after,
    too, because annotations are placed against the measured boxes of the ones already
    placed. Measured, not assumed: a first draft also restyled every text after the build
    and set the ticks' face on the axis, and mutation removed each without the figure
    changing. And the context rather than `rcParams`, so the engineer's own `plt.plot` in
    the next cell is exactly what it was.
    """
    with matplotlib.rc_context(_PAGE_TYPE):
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
            axis.set_ylabel(_axis_label(result.ylabel, result.series[0].y_values[0]))

        if has_text_override:
            figure.tight_layout()

        reflow_dense_characteristic_labels(figure, result)
    return figure
