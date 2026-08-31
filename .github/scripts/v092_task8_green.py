from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Task 8 anchor not found: {label}")
    return text.replace(old, new, 1)


# Renderer: characteristic results have a distinct HTML renderer contract.
path = Path("src/engcalc_colab/renderer.py")
text = path.read_text()
old = '''def render_result(result: CalculationResult, *, settings: RenderSettings | None = None) -> str:
    active_settings = settings or _DEFAULT_RENDER_SETTINGS
'''
new = '''def render_result(result: CalculationResult, *, settings: RenderSettings | None = None) -> str:
    if isinstance(result, (RootsResult, IntersectionsResult, ExtremaResult)):
        raise TypeError(
            "render_result does not support characteristic results; "
            "use render_characteristic_result"
        )

    active_settings = settings or _DEFAULT_RENDER_SETTINGS
'''
text = replace_once(text, old, new, "render_result characteristic guard")
path.write_text(text)


# Piecewise: reuse the existing stable unresolved-symbol diagnostic hint.
path = Path("src/engcalc_colab/characteristics.py")
text = path.read_text()
old = '''from .errors import EngEvaluationError
'''
new = '''from .errors import EngEvaluationError, diagnostic_hint
'''
text = replace_once(text, old, new, "diagnostic_hint import")
old = '''        else:
            raise EngEvaluationError(
                "piecewise characteristic domain could not be partitioned safely: "
                f"missing numeric value for '{name}'"
            )
'''
new = '''        else:
            hint = diagnostic_hint("unresolved_numeric_symbols", names=(name,))
            raise EngEvaluationError(
                "piecewise characteristic domain could not be partitioned safely: "
                f"missing numeric value for '{name}'. {hint}"
            )
'''
text = replace_once(text, old, new, "Piecewise missing-symbol diagnostic")
path.write_text(text)


# Persist L-1 renderer contract.
path = Path("tests/test_renderer.py")
text = path.read_text()
if "import pytest\n" not in text:
    text = "import pytest\n\n" + text
marker = "def test_render_result_rejects_characteristic_results_with_targeted_guidance(source):"
if marker not in text:
    text += '''\n\n@pytest.mark.parametrize(
    "source",
    [
        "roots(x-1, x, 0, 2)",
        "intersections(x, 2-x, x, 0, 2)",
        "extrema(-(x-1)^2, x, 0, 2)",
    ],
)
def test_render_result_rejects_characteristic_results_with_targeted_guidance(source):
    engine = EngineeringEngine()
    result = engine.evaluate(parse_cell(source)[0])
    with pytest.raises(
        TypeError,
        match=(
            "render_result does not support characteristic results; "
            "use render_characteristic_result"
        ),
    ):
        render_result(result)
'''
path.write_text(text)


# Persist the approved L-3 contract and the direct substitution-path regression
# that actually reproduced the missing hint on the current Task 7 tree.
path = Path("tests/test_characteristics_piecewise_extrema.py")
text = path.read_text()
marker = "def test_piecewise_characteristic_missing_value_has_actionable_hint():"
if marker not in text:
    text += '''\n\ndef test_piecewise_characteristic_missing_value_has_actionable_hint():
    from engcalc_colab.errors import EngEvaluationError

    context = NumericContext()
    x, a = sp.symbols("x a", real=True)
    expr = sp.Piecewise((x, x < a), (2*x, True), evaluate=False)
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    with pytest.raises(EngEvaluationError) as exc_info:
        solve_extrema_exact(expr, x, domain, context)
    message = str(exc_info.value)
    assert "a" in message
    assert "a := <value>*<unit>" in message
'''
marker = "def test_piecewise_substitution_missing_branch_symbol_has_actionable_hint():"
if marker not in text:
    text += '''\n\ndef test_piecewise_substitution_missing_branch_symbol_has_actionable_hint():
    from engcalc_colab.errors import EngEvaluationError

    context = NumericContext()
    x, q = sp.symbols("x q", real=True)
    expr = sp.Piecewise((q*x, x < 2), (x, True), evaluate=False)
    domain = normalize_analysis_domain(context, sp.Integer(0), sp.Integer(4))

    with pytest.raises(EngEvaluationError) as exc_info:
        solve_extrema_exact(expr, x, domain, context)
    message = str(exc_info.value)
    assert "q" in message
    assert "q := <value>*<unit>" in message
'''
path.write_text(text)

print("Applied Task 8 explicit characteristic renderer/diagnostic contracts and tests.")
