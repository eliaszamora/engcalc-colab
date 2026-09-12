from dataclasses import replace

import engcalc_colab.renderer as renderer_module
from conftest import block_text
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

    # Through the reader's view: the header is `x [$\mathrm{m}$]` in the markup now,
    # because the block is a `Markdown` output and its units typeset. What this pins is
    # unchanged - the unit is named once, in the header, and never in a cell.
    assert "x [m]" in block_text(html)
    assert "M(x) [kN·m]" in block_text(html)
    body = block_text(html.split("<tbody>", 1)[1])
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
    header = html.split("<thead>", 1)[1].split("</thead>", 1)[0]

    assert "dimensionless" not in header
    assert "[" not in header
    assert ">x<" in header
    assert ">x**2<" in header


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

    assert html.index("M_D(x)") < html.index("M_L(x)")
    # The row as the reader reads it. A cell is `$8.00$` in the markup now, so the
    # literal `<td>` spelling this used cannot be matched - and the order of the three
    # numbers across the row is what it was about.
    assert "2.00 8.00 4.00" in block_text(html)


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

    assert "<x&>" not in html
    assert "<b>M&</b>" not in html
    assert "&lt;x&amp;&gt;" in html
    assert "&lt;b&gt;M&amp;&lt;/b&gt;" in html
