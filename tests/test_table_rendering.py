from dataclasses import replace

import engcalc_colab.renderer as renderer_module
from conftest import block_text, table_cells
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import RenderSettings


def eval_cell(engine: EngineeringEngine, text: str):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def render_table(result, *, settings=None):
    assert hasattr(renderer_module, "render_table"), "render_table is not implemented"
    return renderer_module.render_table(result, settings=settings)


def test_render_table_places_units_once_in_headers_not_cells():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M(x) = q*x*(L-x)/2\n"
        "q := 4*kN/m\n"
        "L := 5*m",
    )
    result = eval_cell(engine, "table(M(x), x, 0, L, 3)")[-1]

    html = render_table(result)

    # Through the reader's view, one cell at a time. What this pins is unchanged - the
    # unit is named once, in the header, and never in a cell.
    header, rows = table_cells(html)
    assert header == ["x [m]", "M(x) [kN·m]"], header
    body = " ".join(cell for row in rows for cell in row)
    assert "kN" not in body
    assert "[m]" not in body


def test_render_table_uses_render_settings_precision_and_zero_tolerance():
    engine = EngineeringEngine()
    result = eval_cell(
        engine,
        "table(x, x, [0.0000004, 0.5, 1])",
    )[-1]

    html = render_table(
        result,
        settings=RenderSettings(precision=3, zero_tolerance=1e-6),
    )

    text = block_text(html)
    assert text.count("0.000") == 2, text
    assert text.count("0.500") == 2, text
    assert text.count("1.000") == 2, text


def test_render_table_omits_dimensionless_unit_suffixes():
    engine = EngineeringEngine()
    result = eval_cell(engine, "table(x^2, x, 0, 2, 3)")[-1]

    html = render_table(result)
    header, _ = table_cells(html)

    assert header == ["x", "x**2"], header


def test_render_table_preserves_response_and_row_order():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_D(x) = qD*x*(L-x)/2\n"
        "M_L(x) = qL*x*(L-x)/2\n"
        "qD := 4*kN/m\n"
        "qL := 2*kN/m\n"
        "L := 4*m",
    )
    result = eval_cell(engine, "table(M_D(x), M_L(x), x, 0, L, 3)")[-1]

    html = render_table(result)

    header, rows = table_cells(html)
    assert header == ["x [m]", "M_D(x) [kN·m]", "M_L(x) [kN·m]"], header
    # The order of the three numbers across the row is what this was about.
    assert ["2.00", "8.00", "4.00"] in rows, rows


def test_render_table_escapes_variable_and_response_labels():
    engine = EngineeringEngine()
    result = eval_cell(engine, "table(x, x, 0, 1, 2)")[-1]
    escaped_result = replace(
        result,
        variable="<x&>",
        columns=(
            replace(result.columns[0], display_label="<b>M&</b>"),
        ),
    )

    html = render_table(escaped_result)

    # A `Math` output now: a label can carry no markup into the page and no `&` into the
    # array, where it would open a column that is not there.
    assert "<" not in html and ">" not in html, html
    header, rows = table_cells(html)
    assert len(header) == 2 and all(len(row) == 2 for row in rows), (header, rows)
