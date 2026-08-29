from pathlib import Path


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


renderer_path = Path("src/engcalc_colab/renderer.py")
renderer = renderer_path.read_text()
renderer = replace_once(
    renderer,
    "import re\nfrom dataclasses import dataclass\n",
    "import re\nfrom dataclasses import dataclass\nfrom html import escape\n",
    label="renderer html import",
)
renderer = replace_once(
    renderer,
    "    PartialNumericEvaluationResult,\n)",
    "    PartialNumericEvaluationResult,\n    TableResult,\n)",
    label="renderer TableResult import",
)
renderer = replace_once(
    renderer,
    "\ndef render_result(result: CalculationResult, *, settings: RenderSettings | None = None) -> str:\n",
    '''\ndef _table_unit_text(unit) -> str:\n    if str(unit) == "dimensionless":\n        return ""\n    return format(unit, "~P")\n\n\ndef _table_header(label: str, unit) -> str:\n    safe_label = escape(label)\n    unit_text = _table_unit_text(unit)\n    if not unit_text:\n        return safe_label\n    return f"{safe_label} [{escape(unit_text)}]"\n\n\ndef _table_magnitude(quantity, settings: RenderSettings) -> str:\n    magnitude = float(quantity.magnitude)\n    if abs(magnitude) < settings.zero_tolerance:\n        magnitude = 0.0\n    return f"{magnitude:.{settings.precision}f}"\n\n\ndef render_table(\n    result: TableResult,\n    *,\n    settings: RenderSettings | None = None,\n) -> str:\n    """Render a unit-aware engineering table as compact scoped HTML."""\n    active_settings = settings or _DEFAULT_RENDER_SETTINGS\n    headers = [\n        _table_header(result.variable, result.point_unit),\n        *(\n            _table_header(column.display_label, column.unit)\n            for column in result.columns\n        ),\n    ]\n    header_html = "".join(f"<th>{header}</th>" for header in headers)\n\n    rows: list[str] = []\n    for row_index, point in enumerate(result.point_values):\n        cells = [_table_magnitude(point, active_settings)]\n        cells.extend(\n            _table_magnitude(column.values[row_index], active_settings)\n            for column in result.columns\n        )\n        rows.append(\n            "<tr>"\n            + "".join(f"<td>{cell}</td>" for cell in cells)\n            + "</tr>"\n        )\n\n    body_html = "".join(rows)\n    return (\n        '<style>'\n        '.engcalc-table{margin:0.35rem 0 0.55rem 0;overflow-x:auto;}'\n        '.engcalc-table table{border-collapse:collapse;font-size:0.92rem;line-height:1.35;}'\n        '.engcalc-table th,.engcalc-table td{'\n        'padding:0.28rem 0.62rem;border-bottom:1px solid rgba(127,127,127,0.20);'\n        'text-align:right;white-space:nowrap;}'\n        '.engcalc-table th{font-weight:600;border-bottom:1px solid rgba(127,127,127,0.42);}'\n        '.engcalc-table th:first-child,.engcalc-table td:first-child{text-align:left;}'\n        '</style>'\n        '<div class="engcalc-table"><table>'\n        f'<thead><tr>{header_html}</tr></thead>'\n        f'<tbody>{body_html}</tbody>'\n        '</table></div>'\n    )\n\n\ndef render_result(result: CalculationResult, *, settings: RenderSettings | None = None) -> str:\n''',
    label="renderer render_table insertion",
)
renderer_path.write_text(renderer)


magic_path = Path("src/engcalc_colab/magic.py")
magic = magic_path.read_text()
magic = replace_once(
    magic,
    "    PlotResult,\n)",
    "    PlotResult,\n    TableResult,\n)",
    label="magic TableResult import",
)
magic = replace_once(
    magic,
    "from .renderer import RenderSettings, render_aligned_results\n",
    "from .renderer import RenderSettings, render_aligned_results, render_table\n",
    label="magic render_table import",
)
magic = replace_once(
    magic,
    "                pending_results.append(result)\n",
    '''                if isinstance(result, TableResult):\n                    _display_equation_group(\n                        pending_results,\n                        self.render_settings,\n                    )\n                    pending_results.clear()\n                    display(\n                        HTML(\n                            render_table(\n                                result,\n                                settings=self.render_settings,\n                            )\n                        )\n                    )\n                    continue\n\n                pending_results.append(result)\n''',
    label="magic table dispatch",
)
magic_path.write_text(magic)
