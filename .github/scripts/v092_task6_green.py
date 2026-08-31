from pathlib import Path
import re


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Task 6 anchor not found: {label}")
    return text.replace(old, new, 1)


# NumericContext: one shared unit-literal override policy.
path = Path("src/engcalc_colab/numeric.py")
text = path.read_text()
old = '''    def resolve_target_unit_name(self, name: str):
        if name in _UNIT_ALIASES:
            return self.ureg.Unit(_UNIT_ALIASES[name])
        raise EngEvaluationError(f"unknown target unit '{name}'")

    def evaluate_unit_expression(self, expression: ast.Expression):
'''
new = '''    def resolve_target_unit_name(self, name: str):
        if name in _UNIT_ALIASES:
            return self.ureg.Unit(_UNIT_ALIASES[name])
        raise EngEvaluationError(f"unknown target unit '{name}'")

    def unit_literal_overrides(
        self,
        expression,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve free symbols that are direct supported unit literals.

        Explicit overrides take precedence over stored numeric values, and stored
        numeric values take precedence over interpreting a name as a unit alias.
        """
        fixed = dict(overrides or {})
        for symbol in sp.sympify(expression).free_symbols:
            name = symbol.name
            if name in fixed or name in self.values:
                continue
            if name in _UNIT_ALIASES:
                fixed[name] = self.resolve_target_unit_name(name)
        return fixed

    def evaluate_unit_expression(self, expression: ast.Expression):
'''
text = replace_once(text, old, new, "NumericContext.unit_literal_overrides")
path.write_text(text)


# Characteristics: domain bounds and candidate validation share NumericContext policy.
path = Path("src/engcalc_colab/characteristics.py")
text = path.read_text()
old = '''        _, quantity = context.evaluate_symbolic(expression)
'''
new = '''        _, quantity = context.evaluate_symbolic(
            expression,
            overrides=context.unit_literal_overrides(expression),
        )
'''
text = replace_once(text, old, new, "characteristic domain bound overrides")

helper_start = text.find("def _characteristic_literal_unit_overrides(")
if helper_start != -1:
    helper_end = text.find("\n\ndef _evaluate_root_candidate", helper_start)
    if helper_end == -1:
        raise SystemExit("Task 6 private characteristic unit helper end not found")
    text = text[:helper_start] + text[helper_end + 2:]

text, replacements = re.subn(
    r"_characteristic_literal_unit_overrides\(\s*context,\s*",
    "context.unit_literal_overrides(",
    text,
)
if replacements == 0 and "_characteristic_literal_unit_overrides" in text:
    raise SystemExit("Task 6 characteristic helper calls were not migrated")
if "_characteristic_literal_unit_overrides" in text:
    raise SystemExit("Task 6 left a private characteristic unit helper reference")
path.write_text(text)


# Engine: plot bounds use the same symbolic unit-literal policy. Table already
# resolves ordinary unit-literal AST bounds numerically; use the policy in its
# symbolic fallback as well so both paths have the same precedence contract.
path = Path("src/engcalc_colab/engine.py")
text = path.read_text()
old = '''        _, start_quantity = self.engine.numeric_context.evaluate_symbolic(start_expression)
        _, end_quantity = self.engine.numeric_context.evaluate_symbolic(end_expression)
'''
new = '''        _, start_quantity = self.engine.numeric_context.evaluate_symbolic(
            start_expression,
            overrides=self.engine.numeric_context.unit_literal_overrides(start_expression),
        )
        _, end_quantity = self.engine.numeric_context.evaluate_symbolic(
            end_expression,
            overrides=self.engine.numeric_context.unit_literal_overrides(end_expression),
        )
'''
text = replace_once(text, old, new, "plot direct unit-literal bounds")
old = '''        if isinstance(value, sp.Expr):
            _, value = self.engine.numeric_context.evaluate_symbolic(value)
        return value
'''
new = '''        if isinstance(value, sp.Expr):
            _, value = self.engine.numeric_context.evaluate_symbolic(
                value,
                overrides=self.engine.numeric_context.unit_literal_overrides(value),
            )
        return value
'''
text = replace_once(text, old, new, "table symbolic unit-literal fallback")
path.write_text(text)


# Persist the public Task 6 contract after RED has been observed.
path = Path("tests/test_characteristics_engine.py")
text = path.read_text()
marker = "def test_direct_unit_literals_are_consistent_across_domain_bearing_apis():"
if marker not in text:
    text += '''\n\ndef _task6_seeded_engine():
    engine = EngineeringEngine()
    evaluate_cell(
        engine,
        "L := 6*m\\n"
        "q := 12*kN/m\\n"
        "M(x) = q*x*(L-x)/2\\n"
        "M2(x) = q*x*(L-x)/3\\n"
        "V(x) = q*(L/2-x)",
    )
    return engine


def test_direct_unit_literals_are_consistent_across_domain_bearing_apis():
    engine = _task6_seeded_engine()

    roots = evaluate_cell(engine, "roots(V(x), x, 0*m, 6*m)")
    extrema = evaluate_cell(engine, "extrema(M(x), x, 0*m, 6000*mm)")
    intersections = evaluate_cell(
        engine, "intersections(M(x), M2(x), x, 0*m, 6*m)"
    )
    plot = evaluate_cell(engine, "plot(M(x), x, 0*m, 6*m)")
    table = evaluate_cell(engine, "table(M(x), x, 0*m, 6*m, 5)")

    assert roots.points[0].x_quantity.to("m").magnitude == pytest.approx(3.0)
    peak = next(point for point in extrema.points if "global_max" in point.roles)
    assert peak.x_quantity.to("mm").magnitude == pytest.approx(3000.0)
    assert len(intersections.points) == 2
    assert plot.x_values[-1].to("m").magnitude == pytest.approx(6.0)
    assert table.point_values[-1].to("m").magnitude == pytest.approx(6.0)


def test_direct_unit_literal_bounds_reject_incompatible_domain_units():
    engine = _task6_seeded_engine()
    with pytest.raises(EngEvaluationError, match="incompatible"):
        evaluate_cell(engine, "roots(V(x), x, 0*m, 2*s)")
'''
path.write_text(text)


# Focused NumericContext precedence contract.
path = Path("tests/test_numeric_context.py")
text = path.read_text()
marker = "def test_unit_literal_overrides_respects_explicit_and_stored_precedence():"
if marker not in text:
    text += '''\n\ndef test_unit_literal_overrides_respects_explicit_and_stored_precedence():
    ctx = NumericContext()
    meter_symbol = sp.Symbol("m", real=True)

    inferred = ctx.unit_literal_overrides(6 * meter_symbol)
    assert inferred["m"] == ctx.ureg.Unit("meter")

    explicit = ctx.ureg.Unit("centimeter")
    assert ctx.unit_literal_overrides(
        6 * meter_symbol, {"m": explicit}
    )["m"] == explicit

    ctx.values["m"] = ctx.ureg.Quantity(2, "second")
    assert "m" not in ctx.unit_literal_overrides(6 * meter_symbol)
    _, stored = ctx.evaluate_symbolic(6 * meter_symbol)
    assert stored.to("second").magnitude == pytest.approx(12.0)
'''
path.write_text(text)


# Plot-specific persistent coverage complements the five-API public matrix.
path = Path("tests/test_characteristics_plot_integration.py")
text = path.read_text()
marker = "def test_plot_accepts_direct_unit_literal_bounds():"
if marker not in text:
    text += '''\n\ndef test_plot_accepts_direct_unit_literal_bounds():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "L := 6*m\\n"
        "q := 12*kN/m\\n"
        "M(x) = q*x*(L-x)/2\\n"
        "plot(M(x), x, 0*m, 6000*mm)",
    )

    assert isinstance(result, PlotResult)
    assert result.x_values[0].to("m").magnitude == pytest.approx(0.0)
    assert result.x_values[-1].to("m").magnitude == pytest.approx(6.0)
    peak = _global_point(result.series[0], "global_max")
    assert peak.x_quantity.to("mm").magnitude == pytest.approx(3000.0)
'''
path.write_text(text)

print("Applied Task 6 centralized direct unit-literal bound handling and tests.")
