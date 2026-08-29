import matplotlib
matplotlib.use("Agg")

from matplotlib.collections import PathCollection, PolyCollection
from matplotlib.text import Annotation

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def moment_envelope_result():
    engine = EngineeringEngine()
    eval_cell(engine, "M_A(x) = q*x*(L-x)/2\nM_B(x) = -0.5*q*x*(L-x)/2\nM_C(x) = 0.6*q*x*(L-x)/2\nq := 8*kN/m\nL := 6*m")
    return eval_cell(engine, "envelope(M_A(x), M_B(x), M_C(x), x, 0, L)")[-1]


def coincident_moment_envelope_result():
    engine = EngineeringEngine()
    eval_cell(engine, "M_A(x) = C\nM_B(x) = C\nC := 5*kN*m\nL := 2*m")
    return eval_cell(engine, "envelope(M_A(x), M_B(x), x, 0, L)")[-1]


def shear_magnitude_envelope_result():
    engine = EngineeringEngine()
    eval_cell(engine, "V_constr(x) = R_constr - q_constr*x\nV_uso(x) = R_uso + q_uso*x\nR_constr := 6*kN\nq_constr := 4*kN/m\nR_uso := -9*kN\nq_uso := 1*kN/m\nL := 2*m")
    return eval_cell(engine, "envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)")[-1]


def annotations(axis):
    return [text for text in axis.texts if isinstance(text, Annotation)]


def test_envelope_renders_original_source_curves_as_faint_background_context():
    axis = render_plot(moment_envelope_result()).axes[0]
    faint_lines = [line for line in axis.lines if line.get_label() == "_nolegend_" and (line.get_alpha() or 1.0) <= 0.35]
    assert len(faint_lines) == 3
    assert all(line.get_linewidth() < 2.0 for line in faint_lines)


def test_envelope_emphasizes_only_maximum_and_minimum_boundaries():
    axis = render_plot(moment_envelope_result()).axes[0]
    envelope_lines = [line for line in axis.lines if line.get_label() in {"M_max(x)", "M_min(x)"}]
    assert len(envelope_lines) == 2
    assert all(line.get_linewidth() >= 2.2 for line in envelope_lines)
    assert all((line.get_alpha() or 1.0) >= 0.9 for line in envelope_lines)


def test_envelope_fills_only_between_maximum_and_minimum_boundaries():
    axis = render_plot(moment_envelope_result()).axes[0]
    fills = [collection for collection in axis.collections if isinstance(collection, PolyCollection)]
    assert len(fills) == 1


def test_envelope_source_curves_have_no_source_markers_or_source_callouts():
    axis = render_plot(moment_envelope_result()).axes[0]
    markers = [collection for collection in axis.collections if isinstance(collection, PathCollection)]
    assert len(markers) <= 1
    assert not any("M_A" in item.get_text() or "M_B" in item.get_text() or "M_C" in item.get_text() for item in annotations(axis))


def test_envelope_preserves_moment_positive_down_and_engineering_units():
    axis = render_plot(moment_envelope_result()).axes[0]
    assert axis.yaxis_inverted()
    assert axis.get_ylabel() == "M(x) [kN·m]"
    assert axis.get_title() == "M(x) envelope"


def test_envelope_legend_contains_only_the_two_boundaries():
    axis = render_plot(moment_envelope_result()).axes[0]
    legend = axis.get_legend()
    assert legend is not None
    assert [text.get_text() for text in legend.get_texts()] == ["M_max(x)", "M_min(x)"]


def test_signed_envelope_replaces_panel_with_global_compact_coordinate_annotations():
    figure = render_plot(moment_envelope_result())
    axis = figure.axes[0]
    items = annotations(axis)
    labels = [item.get_text() for item in items]

    assert len(figure.texts) == 0
    assert not any("Envelope characteristic values" in text.get_text() for text in axis.texts)
    assert len(items) == 2
    assert "(3, 36)" in labels
    assert "(3, -18)" in labels
    assert all(item.xy == (3.0, 36.0) or item.xy == (3.0, -18.0) for item in items)
    assert all(item.arrow_patch is None and item.get_bbox_patch() is None for item in items)


def test_signed_envelope_deduplicates_coincident_global_extrema():
    axis = render_plot(coincident_moment_envelope_result()).axes[0]
    items = annotations(axis)

    assert len(items) == 1
    assert items[0].get_text() == "(0, 5)"
    assert items[0].xy == (0.0, 5.0)


def test_envelope_keeps_zero_reference_line():
    axis = render_plot(moment_envelope_result()).axes[0]
    zero_lines = [line for line in axis.lines if line.get_label() == "_zero"]
    assert len(zero_lines) == 1


def test_magnitude_envelope_shows_signed_sources_and_one_nonnegative_boundary():
    axis = render_plot(shear_magnitude_envelope_result()).axes[0]
    faint = [line for line in axis.lines if line.get_label() == "_nolegend_"]
    boundaries = [line for line in axis.lines if line.get_label() == "|V|_max(x)"]
    assert len(faint) == 2
    assert any(min(line.get_ydata()) < 0 for line in faint)
    assert len(boundaries) == 1
    assert min(boundaries[0].get_ydata()) >= 0.0
    assert axis.get_ylabel() == "V(x) [kN]"
    assert axis.get_title() == "|V(x)| envelope"
    assert not axis.yaxis_inverted()


def test_magnitude_envelope_fill_and_legend():
    axis = render_plot(shear_magnitude_envelope_result()).axes[0]
    fills = [collection for collection in axis.collections if isinstance(collection, PolyCollection)]
    assert len(fills) == 1
    assert [text.get_text() for text in axis.get_legend().get_texts()] == ["|V|_max(x)"]


def test_magnitude_envelope_replaces_panel_with_one_compact_coordinate_annotation():
    figure = render_plot(shear_magnitude_envelope_result())
    axis = figure.axes[0]
    items = annotations(axis)

    assert len(figure.texts) == 0
    assert not any("Magnitude envelope" in text.get_text() for text in axis.texts)
    assert len(items) == 1
    assert items[0].get_text() == "(0, 9)"
    assert items[0].xy == (0.0, 9.0)
    assert items[0].arrow_patch is None
    assert items[0].get_bbox_patch() is None


def test_envelope_render_returns_closed_figure():
    import matplotlib.pyplot as plt
    figure = render_plot(moment_envelope_result())
    assert figure.number not in plt.get_fignums()
