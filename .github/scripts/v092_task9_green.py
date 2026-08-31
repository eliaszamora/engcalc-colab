from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Task 9 anchor not found: {label}")
    return text.replace(old, new, 1)


# L-2: use Matplotlib's numeric font-weight contract without redesigning titles.
path = Path("src/engcalc_colab/presentation.py")
text = path.read_text()
text = text.replace('fontweight="semibold"', 'fontweight=600')
path.write_text(text)


# L-4: retain exact symbolic x metadata for exact ordinary-plot characteristic requests.
path = Path("src/engcalc_colab/plotting.py")
text = path.read_text()
text = replace_once(
    text,
    "import re\nfrom dataclasses import dataclass\n",
    "import re\nfrom dataclasses import dataclass\n\nimport sympy as sp\n",
    "SymPy plotting import",
)
text = replace_once(
    text,
    '''def _coordinate_label(x: float, y: float) -> str:\n    return f"({_compact_number(x)}, {_compact_number(y)})"\n''',
    '''def _compact_exact_x_label(symbolic, numeric: float) -> str:\n    if isinstance(symbolic, sp.Rational) and symbolic.q != 1:\n        return f"{symbolic.p}/{symbolic.q}"\n    return _compact_number(numeric)\n\n\ndef _coordinate_label(x: float, y: float, x_symbolic=None) -> str:\n    x_text = _compact_exact_x_label(x_symbolic, x)\n    return f"({x_text}, {_compact_number(y)})"\n''',
    "exact coordinate label helper",
)
text = replace_once(
    text,
    '''    role: str\n    inverted: bool\n''',
    '''    role: str\n    inverted: bool\n    x_symbolic: Any | None = None\n''',
    "characteristic request symbolic x",
)
old_request = '''                        role=request_role,\n                        inverted=inverted,\n                    )\n'''
new_request = '''                        role=request_role,\n                        inverted=inverted,\n                        x_symbolic=point.x_symbolic,\n                    )\n'''
text = replace_once(text, old_request, new_request, "exact request symbolic x assignment")
text = replace_once(
    text,
    '''    line_color,\n    occupied_boxes: list,\n) -> None:\n    x = float(x_quantity.magnitude)\n    y = float(y_quantity.magnitude)\n    text = _coordinate_label(x, y)\n''',
    '''    line_color,\n    occupied_boxes: list,\n    x_symbolic=None,\n) -> None:\n    x = float(x_quantity.magnitude)\n    y = float(y_quantity.magnitude)\n    text = _coordinate_label(x, y, x_symbolic)\n''',
    "annotation symbolic x parameter",
)
# There are two request-driven annotation loops (single-series and multi-series).
needle = '''            line_color=line_color,\n            occupied_boxes=occupied_boxes,\n        )\n'''
replacement = '''            line_color=line_color,\n            occupied_boxes=occupied_boxes,\n            x_symbolic=request.x_symbolic,\n        )\n'''
if text.count(needle) != 1:
    raise SystemExit(f"Task 9 expected one single-series request annotation anchor, found {text.count(needle)}")
text = text.replace(needle, replacement, 1)
needle = '''            line_color=line_colors[request.series_index],\n            occupied_boxes=occupied_boxes,\n        )\n'''
replacement = '''            line_color=line_colors[request.series_index],\n            occupied_boxes=occupied_boxes,\n            x_symbolic=request.x_symbolic,\n        )\n'''
if text.count(needle) != 1:
    raise SystemExit(f"Task 9 expected one multi-series request annotation anchor, found {text.count(needle)}")
text = text.replace(needle, replacement, 1)
# Apply L-2 consistently to ordinary and envelope titles in plotting.py.
text = text.replace('fontweight="semibold"', 'fontweight=600')
path.write_text(text)


# Persist Task 9 plotting contracts that were observed before product changes.
path = Path("tests/test_plotting.py")
text = path.read_text()
marker = "def test_presented_plot_title_does_not_emit_font_weight_warning(capsys):"
if marker not in text:
    text += '''\n\ndef test_presented_plot_title_does_not_emit_font_weight_warning(capsys):\n    from engcalc_colab.presentation import render_presented_plot\n\n    engine = EngineeringEngine()\n    result = eval_cell(\n        engine,\n        'f(x)=x\\nplot(f(x), x, 0, 1, title="Test")',\n    )[-1]\n    render_presented_plot(result)\n    captured = capsys.readouterr()\n    assert "font weight semibold" not in captured.err\n    assert "Failed to find font weight semibold" not in captured.err\n'''
marker = "def test_presented_plot_title_uses_numeric_weight_600():"
if marker not in text:
    text += '''\n\ndef test_presented_plot_title_uses_numeric_weight_600():\n    from engcalc_colab.presentation import render_presented_plot\n\n    engine = EngineeringEngine()\n    result = eval_cell(\n        engine,\n        'f(x)=x\\nplot(f(x), x, 0, 1, title="Test")',\n    )[-1]\n    axis = render_presented_plot(result).axes[0]\n    assert axis.title.get_fontweight() == 600\n'''
marker = "def test_exact_rational_characteristic_label_uses_symbolic_x_coordinate():"
if marker not in text:
    text += '''\n\ndef test_exact_rational_characteristic_label_uses_symbolic_x_coordinate():\n    engine = EngineeringEngine()\n    result = eval_cell(\n        engine,\n        "f(x)=-(x-1/3)^2+2\\nplot(f(x), x, 0, 1)",\n    )[-1]\n    axis = render_plot(result).axes[0]\n    exact = next(\n        item for item in annotations(axis)\n        if abs(float(item.xy[0]) - 1/3) < 1e-12\n    )\n    assert "1/3" in exact.get_text()\n    assert abs(float(exact.xy[0]) - 1/3) < 1e-12\n'''
path.write_text(text)


# Persist the already-GREEN negative-zero protection; no renderer product change is needed.
path = Path("tests/test_characteristics_rendering.py")
text = path.read_text()
marker = "def test_characteristic_rendering_normalizes_negative_zero_with_tolerance():"
if marker not in text:
    text += '''\n\ndef test_characteristic_rendering_normalizes_negative_zero_with_tolerance():\n    from engcalc_colab.engine import EngineeringEngine\n    from engcalc_colab.renderer import RenderSettings\n\n    engine = EngineeringEngine()\n    result = [\n        engine.evaluate(statement)\n        for statement in parse_cell(\n            "roots((x-1)*(x-1.0000001), x, 0, 2)"\n        )\n    ][-1]\n    html = renderer.render_characteristic_result(\n        result,\n        settings=RenderSettings(zero_tolerance=1e-10),\n    )\n    assert "-0.00" not in html\n    assert "-0.0" not in html\n    assert "-0\\\\," not in html\n'''
path.write_text(text)

print("Applied Task 9 exact characteristic presentation patch and persistent regressions.")
