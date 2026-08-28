import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.collections import PathCollection, PolyCollection

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import _choose_panel_corner, render_plot


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
    eval_cell(
        engine,
        "M_D(x) = q_D*x*(L-x)/2\n"
        "M_L(x) = q_L*x*(L-x)/2\n"
        "q_D := 8*kN/m\nq_L := 5*kN/m\nL := 6*m",
    )
    return eval_cell(engine, "plot(M_D(x), M_L(x), x, 0, L)")[-1]


def sweep_moment_plot_result():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nL := 6*m")
    return eval_cell(
        engine,
        "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])",
    )[-1]


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


def test_render_plot_annotates_numeric_maximum_and_minimum_with_location():
    axis = render_plot(moment_plot_result()).axes[0]
    labels = [text.get_text() for text in axis.texts]

    assert any(label.startswith("max = 3.15") and "x = 2.50" in label for label in labels)
    assert any(label.startswith("min = -5.60") and "x = 0.00" in label for label in labels)


def test_render_plot_deduplicates_equal_maximum_and_minimum():
    axis = render_plot(constant_plot_result()).axes[0]
    labels = [text.get_text() for text in axis.texts]

    assert len(labels) == 1
    assert labels[0].startswith("max = min = 11.20")


def test_moment_units_render_in_engineering_force_length_order():
    axis = render_plot(moment_plot_result()).axes[0]
    labels = [text.get_text() for text in axis.texts]

    assert axis.get_ylabel() == "M(x) [tonf·m]"
    assert any("3.15 tonf·m" in label for label in labels)
    assert any("-5.60 tonf·m" in label for label in labels)


def test_edge_annotations_point_inward_horizontally():
    axis = render_plot(shear_plot_result()).axes[0]
    annotations = {text.get_text().split(" = ", 1)[0]: text for text in axis.texts}

    maximum = annotations["max"]
    minimum = annotations["min"]

    assert maximum.get_ha() == "left"
    assert maximum.get_position()[0] > 0
    assert minimum.get_ha() == "right"
    assert minimum.get_position()[0] < 0


def test_characteristic_labels_use_boxed_callouts():
    for result in (shear_plot_result(), moment_plot_result()):
        axis = render_plot(result).axes[0]
        for annotation in axis.texts:
            assert annotation.get_bbox_patch() is not None
            assert annotation.arrow_patch is not None
            assert annotation.get_zorder() > axis.lines[0].get_zorder()


def test_shear_characteristic_labels_move_away_from_curve_lobes():
    axis = render_plot(shear_plot_result()).axes[0]
    annotations = {text.get_text().split(" = ", 1)[0]: text for text in axis.texts}

    maximum = annotations["max"]
    minimum = annotations["min"]

    assert maximum.get_position()[1] >= 20
    assert minimum.get_position()[1] <= -20


def test_inverted_moment_labels_move_away_from_curve_lobes_visually():
    axis = render_plot(moment_plot_result()).axes[0]
    annotations = {text.get_text().split(" = ", 1)[0]: text for text in axis.texts}

    maximum = annotations["max"]
    minimum = annotations["min"]

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
    assert [text.get_text() for text in axis.get_legend().get_texts()] == [
        "M_D(x)",
        "M_L(x)",
    ]
    assert not any(
        isinstance(collection, PolyCollection)
        for collection in axis.collections
    )


def test_multiseries_moment_axis_keeps_positive_down_convention():
    axis = render_plot(multi_moment_plot_result()).axes[0]
    assert axis.yaxis_inverted()
    assert axis.get_ylabel() == "M(x) [kN·m]"


def test_multiseries_uses_one_restrained_extrema_marker_collection_per_series():
    axis = render_plot(sweep_moment_plot_result()).axes[0]
    markers = [
        item for item in axis.collections if isinstance(item, PathCollection)
    ]
    assert len(markers) == 3
    assert all(len(marker.get_offsets()) in (1, 2) for marker in markers)
    assert all(max(marker.get_sizes()) <= 28 for marker in markers)


def test_multiseries_characteristic_panel_is_inside_axes():
    figure = render_plot(sweep_moment_plot_result())
    axis = figure.axes[0]

    assert len(figure.texts) == 0
    panels = [
        text for text in axis.texts
        if "Characteristic values" in text.get_text()
    ]
    assert len(panels) == 1
    panel_text = panels[0].get_text()
    assert "q = 5" in panel_text
    assert "q = 10" in panel_text
    assert "q = 15" in panel_text
    assert "max =" in panel_text
    assert "min =" in panel_text
    assert "x =" in panel_text
    assert panels[0].get_transform() == axis.transAxes


def test_panel_chooser_uses_different_corners_for_different_occupancy():
    import matplotlib.pyplot as plt

    fig, axis = plt.subplots()
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 10)
    first = _choose_panel_corner(
        axis,
        [(8.5, 8.5), (9.0, 9.0), (9.5, 9.5)] * 30,
        "Characteristic values\nmax = 10\nmin = 0",
        legend_corner=None,
    )
    second = _choose_panel_corner(
        axis,
        [(0.5, 0.5), (1.0, 1.0), (1.5, 1.5)] * 30,
        "Characteristic values\nmax = 10\nmin = 0",
        legend_corner=None,
    )
    plt.close(fig)

    assert first != "upper right"
    assert second != "lower left"
    assert first != second


def test_panel_chooser_avoids_known_legend_corner():
    import matplotlib.pyplot as plt

    fig, axis = plt.subplots()
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 10)
    corner = _choose_panel_corner(
        axis,
        [(5.0, 5.0)],
        "Characteristic values\nmax = 10\nmin = 0",
        legend_corner="upper right",
    )
    plt.close(fig)

    assert corner != "upper right"


def test_characteristic_panel_bbox_stays_inside_axes():
    figure = render_plot(sweep_moment_plot_result())
    FigureCanvasAgg(figure)
    axis = figure.axes[0]
    panel = [
        text for text in axis.texts
        if "Characteristic values" in text.get_text()
    ][0]

    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    panel_box = panel.get_window_extent(renderer=renderer)
    axes_box = axis.get_window_extent(renderer=renderer)
    tolerance = 1.0

    assert panel_box.x0 >= axes_box.x0 - tolerance
    assert panel_box.y0 >= axes_box.y0 - tolerance
    assert panel_box.x1 <= axes_box.x1 + tolerance
    assert panel_box.y1 <= axes_box.y1 + tolerance


def test_render_plot_returns_closed_figure():
    import matplotlib.pyplot as plt
    figure = render_plot(moment_plot_result())
    assert figure.number not in plt.get_fignums()
