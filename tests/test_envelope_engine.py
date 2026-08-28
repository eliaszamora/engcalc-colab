from dataclasses import FrozenInstanceError

import pytest

from engcalc_colab.models import PlotResult, PlotSeries
from engcalc_colab.parser import parse_cell


def test_plot_result_can_transport_envelope_metadata_immutably():
    statement = parse_cell("plot(A(x), B(x), x, 0, L)")[0]
    source = (
        PlotSeries("A(x)", (1, 3), False),
        PlotSeries("B(x)", (2, 2), False),
    )
    displayed = (
        PlotSeries("max", (2, 3), False),
        PlotSeries("min", (1, 2), False),
    )
    result = PlotResult(
        statement,
        "Comparison",
        "x",
        (0, 1),
        displayed,
        kind="envelope",
        source_series=source,
        source_labels=("A(x)", "B(x)"),
        governing_max=(1, 0),
        governing_min=(0, 1),
    )

    assert result.kind == "envelope"
    assert result.source_series == source
    assert result.source_labels == ("A(x)", "B(x)")
    assert result.governing_max == (1, 0)
    assert result.governing_min == (0, 1)

    with pytest.raises(FrozenInstanceError):
        result.kind = "plot"
