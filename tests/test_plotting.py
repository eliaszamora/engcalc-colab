import matplotlib
matplotlib.use("Agg")

from matplotlib.collections import PathCollection, PolyCollection
from matplotlib.text import Annotation

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def plot_result(function_name, expression):
    engine = EngineeringEngine()
    eval_cell(engine, f"{function_name}(x) = {expression}")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 4*m")
    return eval_cell(engine, f"plot({function_name}(x), x, 0, L)")[-1]


def moment_plot_result():
    return plot_result("M", "-q*L^2/8 + 5*q*L*x/8 - q*x^2/2")


def shear_plot_result():
    return plot_result("V", "5*q*L/8 - q*x")


def constant_plot_result():
    return plot_result("C", "q*L")


def multi_moment_plot_result():
    engine = EngineeringEngine()
    eval_cell(engine, "M_D(x) = q_D*x*(L-x)/2\nM_L(x) = q_L*x*(L-x)/2\nq_D := 8*kN/m\nq_L := 5*kN/m\nL := 6*m")
    return eval_cell(engine, "plot(M_D(x), M_L(x), x, 0, L)")[-1]


def sweep_moment_plot_result():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nL := 6*m")
    return eval_cell(engine, "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])")[-1]


def annotations(axis):
    return [text for text in axis.texts if isinstance(text, Annotation)]


def test_render_plot_labels_axes_title_and_zero_reference():
    figure = render_plot(moment_plot_result())
    axis = figure.axes[0]
    assert axis.get_xlabel().startswith("x [")
    assert "m" in axis.get_xlabel()
    assert axis.get_ylabel().startswith("M(x) [")
    assert "tonf" in axis.get_ylabel()
    assert "m" in axis.get_ylabel()
    assert axis.get_title() == "M(x)"
    assert len(axis.lines) == 2


def test_render_plot_inverts_only_moment_diagrams():
    moment_axis = render_plot(moment_plot_result()).axes[0]
    shear_axis = render_plot(shear_plot_result()).axes[0]
    assert moment_axis.yaxis_inverted()
    assert not shear_axis.yaxis_inverted()


def test_render_plot_adds_engineering_visual_polish():
    axis = render_plot(moment_plot_result()).axes[0]
    assert axis.lines[0].get_linewidth() >= 2.0
    assert len(axis.collections) >= 2
    assert not axis.spines["top"].get_visible()
    assert not axis.spines["right"].get_visible()


def test_render_plot_annotates_compact_coordinates_at_extrema():
    axis = render_plot(moment_plot_result()).axes[0]
    labels = [item.get_text() for item in annotations(axis)]
    assert "(2.5, 3.15)" in labels
    assert "(0, -5.6)" in labels


def test_render_plot_deduplicates_equal_maximum_and_minimum():
    axis = render_plot(constant_plot_result()).axes[0]
    items = annotations(axis)
    assert len(items) == 1
    assert items[0].get_text() == "(0, 11.2)"


def test_moment_units_remain_on_axis_not_characteristic_labels():
    axis = render_plot(moment_plot_result()).axes[0]
    labels = [item.get_text() for item in annotations(axis)]
    assert axis.get_ylabel() == "M(x) [tonf·m]"
    assert set(labels) == {"(2.5, 3.15)", "(0, -5.6)"}
    assert all("tonf" not in label and "m" not in label for label in labels)


def test_edge_annotations_point_inward_horizontally():
    axis = render_plot(shear_plot_result()).axes[0]
    items = sorted(annotations(axis), key=lambda item: item.xy[0])
    left, right = items
    assert left.get_ha() == "left"
    assert left.get_position()[0] > 0
    assert right.get_ha() == "right"
    assert right.get_position()[0] < 0


def test_characteristic_labels_are_unboxed_without_leader_lines():
    for result in (shear_plot_result(), moment_plot_result()):
        axis = render_plot(result).axes[0]
        for annotation in annotations(axis):
            assert annotation.get_bbox_patch() is None
            assert annotation.arrow_patch is None
            assert annotation.get_zorder() > axis.lines[0].get_zorder()


def test_shear_characteristic_labels_move_away_from_curve_lobes():
    axis = render_plot(shear_plot_result()).axes[0]
    items = sorted(annotations(axis), key=lambda item: item.xy[0])
    maximum, minimum = items
    assert maximum.get_position()[1] >= 20
    assert minimum.get_position()[1] <= -20


def test_inverted_moment_labels_move_away_from_curve_lobes_visually():
    axis = render_plot(moment_plot_result()).axes[0]
    by_y = sorted(annotations(axis), key=lambda item: item.xy[1])
    minimum, maximum = by_y
    assert maximum.get_position()[1] <= -20
    assert minimum.get_position()[1] >= 20


def test_plot_uses_one_deduplicated_marker_collection():
    shear_axis = render_plot(shear_plot_result()).axes[0]
    moment_axis = render_plot(moment_plot_result()).axes[0]
    shear_markers = [item for item in shear_axis.collections if isinstance(item, PathCollection)]
    moment_markers = [item for item in moment_axis.collections if isinstance(item, PathCollection)]
    assert len(shear_markers) == 1
    assert len(shear_markers[0].get_offsets()) == 2
    assert max(shear_markers[0].get_sizes()) <= 34
    assert len(moment_markers) == 1
    assert len(moment_markers[0].get_offsets()) == 3
    assert max(moment_markers[0].get_sizes()) <= 34


def test_multiseries_render_uses_lines_legend_and_no_area_fills():
    figure = render_plot(multi_moment_plot_result())
    axis = figure.axes[0]
    assert len(axis.lines) == 3
    assert axis.get_legend() is not None
    assert [text.get_text() for text in axis.get_legend().get_texts()] == ["M_D(x)", "M_L(x)"]
    assert not any(isinstance(collection, PolyCollection) for collection in axis.collections)


def test_multiseries_moment_axis_keeps_positive_down_convention():
    axis = render_plot(multi_moment_plot_result()).axes[0]
    assert axis.yaxis_inverted()
    assert axis.get_ylabel() == "M(x) [kN·m]"


def test_multiseries_uses_one_restrained_extrema_marker_collection_per_series():
    axis = render_plot(sweep_moment_plot_result()).axes[0]
    markers = [item for item in axis.collections if isinstance(item, PathCollection)]
    assert len(markers) == 3
    assert all(len(marker.get_offsets()) in (1, 2) for marker in markers)
    assert all(max(marker.get_sizes()) <= 28 for marker in markers)


def test_multiseries_replaces_characteristic_panel_with_compact_point_annotations():
    figure = render_plot(multi_moment_plot_result())
    axis = figure.axes[0]
    items = annotations(axis)
    labels = [item.get_text() for item in items]

    assert len(figure.texts) == 0
    assert not any("Characteristic values" in text.get_text() for text in axis.texts)
    assert len(items) == 4
    assert labels.count("(3, 36)") == 1
    assert labels.count("(3, 22.5)") == 1
    assert labels.count("(0, 0)") == 2

    for item in items:
        assert item.xy is not None
        assert item.get_transform() != axis.transAxes
        assert item.arrow_patch is None
        assert item.get_bbox_patch() is None


def test_sweep_multiseries_characteristics_are_attached_to_each_curve_not_a_box():
    axis = render_plot(sweep_moment_plot_result()).axes[0]
    items = annotations(axis)
    assert len(items) == 6
    assert all(item.get_text().startswith("(") and item.get_text().endswith(")") for item in items)
    assert all("=" not in item.get_text() for item in items)
    assert not any("Characteristic values" in text.get_text() for text in axis.texts)


def test_render_plot_returns_closed_figure():
    import matplotlib.pyplot as plt
    figure = render_plot(moment_plot_result())
    assert figure.number not in plt.get_fignums()


def test_presented_plot_title_does_not_emit_font_weight_warning(capsys):
    from engcalc_colab.presentation import render_presented_plot

    engine = EngineeringEngine()
    result = eval_cell(
        engine,
        'f(x)=x\nplot(f(x), x, 0, 1, title="Test")',
    )[-1]
    render_presented_plot(result)
    captured = capsys.readouterr()
    assert "font weight semibold" not in captured.err
    assert "Failed to find font weight semibold" not in captured.err


def test_presented_plot_title_uses_numeric_weight_600():
    from engcalc_colab.presentation import render_presented_plot

    engine = EngineeringEngine()
    result = eval_cell(
        engine,
        'f(x)=x\nplot(f(x), x, 0, 1, title="Test")',
    )[-1]
    axis = render_presented_plot(result).axes[0]
    assert axis.title.get_fontweight() == 600


def test_exact_rational_characteristic_label_uses_symbolic_x_coordinate():
    engine = EngineeringEngine()
    result = eval_cell(
        engine,
        "f(x)=-(x-1/3)^2+2\nplot(f(x), x, 0, 1)",
    )[-1]
    axis = render_plot(result).axes[0]
    exact = next(
        item for item in annotations(axis)
        if abs(float(item.xy[0]) - 1/3) < 1e-12
    )
    assert "1/3" in exact.get_text()
    assert abs(float(exact.xy[0]) - 1/3) < 1e-12
