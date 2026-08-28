import matplotlib
matplotlib.use("Agg")

from matplotlib.collections import PathCollection, PolyCollection

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def moment_envelope_result():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_A(x) = q*x*(L-x)/2\n"
        "M_B(x) = -0.5*q*x*(L-x)/2\n"
        "M_C(x) = 0.6*q*x*(L-x)/2\n"
        "q := 8*kN/m\nL := 6*m",
    )
    return eval_cell(
        engine,
        "envelope(M_A(x), M_B(x), M_C(x), x, 0, L)",
    )[-1]


def test_envelope_renders_original_source_curves_as_faint_background_context():
    axis = render_plot(moment_envelope_result()).axes[0]
    faint_lines = [
        line for line in axis.lines
        if line.get_label() == "_nolegend_" and (line.get_alpha() or 1.0) <= 0.35
    ]

    assert len(faint_lines) == 3
    assert all(line.get_linewidth() < 2.0 for line in faint_lines)


def test_envelope_emphasizes_only_maximum_and_minimum_boundaries():
    axis = render_plot(moment_envelope_result()).axes[0]
    envelope_lines = [
        line for line in axis.lines
        if line.get_label() in {"M_max(x)", "M_min(x)"}
    ]

    assert len(envelope_lines) == 2
    assert all(line.get_linewidth() >= 2.2 for line in envelope_lines)
    assert all((line.get_alpha() or 1.0) >= 0.9 for line in envelope_lines)


def test_envelope_fills_only_between_maximum_and_minimum_boundaries():
    axis = render_plot(moment_envelope_result()).axes[0]
    fills = [
        collection for collection in axis.collections
        if isinstance(collection, PolyCollection)
    ]
    assert len(fills) == 1


def test_envelope_source_curves_have_no_markers_or_inline_callouts():
    axis = render_plot(moment_envelope_result()).axes[0]
    markers = [
        collection for collection in axis.collections
        if isinstance(collection, PathCollection)
    ]
    panels = [
        text for text in axis.texts
        if "Envelope characteristic values" in text.get_text()
    ]

    assert len(markers) <= 1
    assert len(panels) == 1
    assert all(not text.get_text().startswith(("max =", "min =")) for text in axis.texts)


def test_envelope_preserves_moment_positive_down_and_engineering_units():
    axis = render_plot(moment_envelope_result()).axes[0]

    assert axis.yaxis_inverted()
    assert axis.get_ylabel() == "M(x) [kN·m]"
    assert axis.get_title() == "M(x) envelope"


def test_envelope_legend_contains_only_the_two_boundaries():
    axis = render_plot(moment_envelope_result()).axes[0]
    legend = axis.get_legend()

    assert legend is not None
    assert [text.get_text() for text in legend.get_texts()] == [
        "M_max(x)",
        "M_min(x)",
    ]


def test_signed_envelope_characteristic_panel_is_inside_axes():
    figure = render_plot(moment_envelope_result())
    axis = figure.axes[0]

    assert len(figure.texts) == 0
    panels = [
        text for text in axis.texts
        if "Envelope characteristic values" in text.get_text()
    ]
    assert len(panels) == 1
    panel_text = panels[0].get_text()
    assert "max = 36.00 kN·m" in panel_text
    assert "min = -18.00 kN·m" in panel_text
    assert "x = 3.00 m" in panel_text
    assert panels[0].get_transform() == axis.transAxes


def test_envelope_keeps_zero_reference_line():
    axis = render_plot(moment_envelope_result()).axes[0]
    zero_lines = [line for line in axis.lines if line.get_label() == "_zero"]
    assert len(zero_lines) == 1


def test_envelope_render_returns_closed_figure():
    import matplotlib.pyplot as plt

    figure = render_plot(moment_envelope_result())
    assert figure.number not in plt.get_fignums()
