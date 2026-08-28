from __future__ import annotations

from .models import PlotResult


def _unit_label(quantity) -> str:
    if quantity.dimensionless:
        return ""
    return f"{quantity.units:~P}"


def _axis_label(name: str, quantity) -> str:
    unit = _unit_label(quantity)
    return name if not unit else f"{name} [{unit}]"


def render_plot(result: PlotResult):
    """Create one closed Matplotlib figure from normalized EngCalc plot data."""
    import matplotlib.pyplot as plt

    x_values = [float(value.magnitude) for value in result.x_values]
    y_values = [float(value.magnitude) for value in result.y_values]

    figure, axis = plt.subplots()
    axis.plot(x_values, y_values)
    axis.axhline(0.0, linewidth=0.8)
    axis.set_xlabel(_axis_label(result.variable, result.x_values[0]))
    axis.set_ylabel(_axis_label(result.display_label, result.y_values[0]))
    axis.set_title(result.display_label)
    figure.tight_layout()

    # IPython displays the returned figure explicitly. Closing it here prevents
    # pyplot/Jupyter from also auto-rendering the same figure a second time.
    plt.close(figure)
    return figure
