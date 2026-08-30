from pathlib import Path

RENDERER = Path("src/engcalc_colab/renderer.py")
MAGIC = Path("src/engcalc_colab/magic.py")

renderer = RENDERER.read_text(encoding="utf-8")
magic = MAGIC.read_text(encoding="utf-8")

if "def render_characteristic_result(" in renderer:
    raise SystemExit("Task 9 characteristic renderer already present; guarded patch will not reapply")

# ---- renderer.py ---------------------------------------------------------
old = """from .models import (\n    EigenvalueSet,\n    EigenvectorSet,\n    EvaluationResult,\n"""
new = """from .models import (\n    CharacteristicInterval,\n    CharacteristicPoint,\n    EigenvalueSet,\n    EigenvectorSet,\n    EvaluationResult,\n    ExtremaResult,\n    IntersectionsResult,\n"""
if old not in renderer:
    raise SystemExit("Task 9 renderer model-import anchor not found")
renderer = renderer.replace(old, new, 1)

old = """    PartialNumericEvaluationResult,\n    TableResult,\n)\n"""
new = """    PartialNumericEvaluationResult,\n    RootsResult,\n    TableResult,\n)\n"""
if old not in renderer:
    raise SystemExit("Task 9 renderer trailing model-import anchor not found")
renderer = renderer.replace(old, new, 1)

marker = "\ndef render_result(result: CalculationResult, *, settings: RenderSettings | None = None) -> str:\n"
if renderer.count(marker) != 1:
    raise SystemExit("Task 9 render_result insertion anchor mismatch")

helper = r'''
CharacteristicResult = RootsResult | IntersectionsResult | ExtremaResult


def _characteristic_role_text(role: str) -> str:
    return role.replace("_", " ")


def _characteristic_math(latex: str) -> str:
    return rf"\({latex}\)"


def _characteristic_quantity_math(quantity, settings: RenderSettings) -> str:
    return _characteristic_math(_quantity_latex(quantity, settings=settings))


def _characteristic_symbolic_math(value) -> str:
    return _characteristic_math(_latex(value))


def _characteristic_point_coordinate(
    point: CharacteristicPoint,
    variable: str,
    settings: RenderSettings,
) -> str:
    variable_html = _characteristic_symbolic_math(sp.Symbol(variable))
    if point.provenance == "numeric":
        return (
            f"{variable_html} ≈ "
            f"{_characteristic_quantity_math(point.x_quantity, settings)}"
        )

    symbolic = _characteristic_symbolic_math(point.x_symbolic)
    evaluated = _characteristic_quantity_math(point.x_quantity, settings)
    return f"{variable_html} = {symbolic} ({evaluated})"


def _characteristic_point_value(
    point: CharacteristicPoint,
    settings: RenderSettings,
) -> str | None:
    if point.value_symbolic is None and point.value_quantity is None:
        return None
    if point.provenance == "numeric" or point.value_symbolic is None:
        if point.value_quantity is None:
            return None
        return "value ≈ " + _characteristic_quantity_math(point.value_quantity, settings)

    symbolic = _characteristic_symbolic_math(point.value_symbolic)
    if point.value_quantity is None:
        return "value = " + symbolic
    evaluated = _characteristic_quantity_math(point.value_quantity, settings)
    return f"value = {symbolic} ({evaluated})"


def _characteristic_interval_text(
    interval: CharacteristicInterval,
    settings: RenderSettings,
) -> str:
    left = "[" if interval.lower_closed else "("
    right = "]" if interval.upper_closed else ")"
    lower = _quantity_latex(interval.lower_quantity, settings=settings)
    upper = _quantity_latex(interval.upper_quantity, settings=settings)
    return _characteristic_math(rf"{left}{lower},\;{upper}{right}")


def _characteristic_heading(result: CharacteristicResult) -> str:
    if isinstance(result, RootsResult):
        return f"Roots — {escape(result.display_label)}"
    if isinstance(result, IntersectionsResult):
        return (
            "Intersections — "
            f"{escape(result.left_label)} / {escape(result.right_label)}"
        )
    return f"Extrema — {escape(result.display_label)}"


def render_characteristic_result(
    result: CharacteristicResult,
    *,
    settings: RenderSettings | None = None,
) -> str:
    """Render one standalone exact-characteristic result as compact HTML/MathJax."""
    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    domain = (
        _characteristic_quantity_math(result.lower_quantity, active_settings)
        + " to "
        + _characteristic_quantity_math(result.upper_quantity, active_settings)
    )

    rows: list[str] = []
    for point in result.points:
        parts = [
            _characteristic_point_coordinate(
                point,
                result.variable,
                active_settings,
            )
        ]
        value_text = _characteristic_point_value(point, active_settings)
        if value_text is not None and not isinstance(result, RootsResult):
            parts.append(value_text)
        if point.roles:
            parts.append(
                ", ".join(_characteristic_role_text(role) for role in point.roles)
            )
        if point.side != "at":
            parts.append(escape(point.side))
        rows.append("<div class=\"engcalc-characteristic-row\">" + " · ".join(parts) + "</div>")

    for interval in result.intervals:
        interval_text = _characteristic_interval_text(interval, active_settings)
        if isinstance(result, RootsResult) or interval.role == "roots":
            text = f"all x in {interval_text}"
        elif isinstance(result, IntersectionsResult) or interval.role == "coincident":
            text = f"coincident on {interval_text}"
        else:
            role = escape(_characteristic_role_text(interval.role))
            text = f"{role} on {interval_text}"
            if interval.value_quantity is not None:
                text += (
                    " · value = "
                    + _characteristic_quantity_math(
                        interval.value_quantity,
                        active_settings,
                    )
                )
        rows.append(f'<div class="engcalc-characteristic-row">{text}</div>')

    if isinstance(result, ExtremaResult):
        if result.unbounded_above:
            rows.append('<div class="engcalc-characteristic-row">unbounded above</div>')
        if result.unbounded_below:
            rows.append('<div class="engcalc-characteristic-row">unbounded below</div>')

    if not rows:
        rows.append('<div class="engcalc-characteristic-row">no finite characteristic points</div>')

    return (
        '<style>'
        '.engcalc-characteristics{margin:0.35rem 0 0.55rem 0;'
        'font-size:0.94rem;line-height:1.45;}'
        '.engcalc-characteristics-title{font-weight:600;margin-bottom:0.15rem;}'
        '.engcalc-characteristics-domain{opacity:0.78;margin-bottom:0.18rem;}'
        '.engcalc-characteristic-row{margin:0.08rem 0;}'
        '</style>'
        '<div class="engcalc-characteristics">'
        f'<div class="engcalc-characteristics-title">{_characteristic_heading(result)}</div>'
        f'<div class="engcalc-characteristics-domain">Domain: {domain}</div>'
        + "".join(rows)
        + '</div>'
    )
'''
renderer = renderer.replace(marker, "\n" + helper + marker, 1)

# ---- magic.py ------------------------------------------------------------
old = """from .models import (\n    EvaluationResult,\n    NumericAssignmentResult,\n"""
new = """from .models import (\n    EvaluationResult,\n    ExtremaResult,\n    IntersectionsResult,\n    NumericAssignmentResult,\n"""
if old not in magic:
    raise SystemExit("Task 9 magic model-import anchor not found")
magic = magic.replace(old, new, 1)

old = """    PlotResult,\n    TableResult,\n)\n"""
new = """    PlotResult,\n    RootsResult,\n    TableResult,\n)\n"""
if old not in magic:
    raise SystemExit("Task 9 magic trailing model-import anchor not found")
magic = magic.replace(old, new, 1)

old = "from .renderer import RenderSettings, render_aligned_results, render_table\n"
new = (
    "from .renderer import (\n"
    "    RenderSettings,\n"
    "    render_aligned_results,\n"
    "    render_characteristic_result,\n"
    "    render_table,\n"
    ")\n"
)
if old not in magic:
    raise SystemExit("Task 9 magic renderer-import anchor not found")
magic = magic.replace(old, new, 1)

marker = """                if isinstance(result, TableResult):\n                    _display_equation_group(\n                        pending_results,\n                        self.render_settings,\n                    )\n                    pending_results.clear()\n                    display(\n                        HTML(\n                            render_table(\n                                result,\n                                settings=self.render_settings,\n                            )\n                        )\n                    )\n                    continue\n\n                pending_results.append(result)\n"""
replacement = """                if isinstance(result, TableResult):\n                    _display_equation_group(\n                        pending_results,\n                        self.render_settings,\n                    )\n                    pending_results.clear()\n                    display(\n                        HTML(\n                            render_table(\n                                result,\n                                settings=self.render_settings,\n                            )\n                        )\n                    )\n                    continue\n\n                if isinstance(result, (RootsResult, IntersectionsResult, ExtremaResult)):\n                    _display_equation_group(\n                        pending_results,\n                        self.render_settings,\n                    )\n                    pending_results.clear()\n                    display(\n                        HTML(\n                            render_characteristic_result(\n                                result,\n                                settings=self.render_settings,\n                            )\n                        )\n                    )\n                    continue\n\n                pending_results.append(result)\n"""
if marker not in magic:
    raise SystemExit("Task 9 magic routing anchor not found")
magic = magic.replace(marker, replacement, 1)

RENDERER.write_text(renderer, encoding="utf-8")
MAGIC.write_text(magic, encoding="utf-8")
