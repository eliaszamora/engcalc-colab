# EngCalc 0.6.0 Absolute-Value Envelope and In-Axes Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe general `abs(...)` operation, make `envelope(abs(...), ...)` produce a structural magnitude envelope while retaining signed source responses, and move multi-series/envelope characteristic panels inside the axes with deterministic automatic corner placement.

**Architecture:** Preserve the EngCalc 0.5.0 shared `plot/envelope` response-resolution pipeline. Capture outer-`abs` syntax before symbolic expansion, sample signed inner responses for faint context, sample absolute comparison responses for governing selection, and extend `PlotResult` only with envelope mode plus governing signed quantities. Keep rendering in `plotting.py`, but centralize axes-owned characteristic-panel placement in deterministic helpers shared by multi-series plots, signed envelopes, and magnitude envelopes.

**Tech Stack:** Python 3.10+, SymPy, Pint, Matplotlib, IPython/Jupyter, pytest.

**Spec:** `docs/superpowers/specs/2026-08-28-engcalc-abs-envelope-panel-v0.6-design.md`

## Global Constraints

- Base checkpoint: EngCalc 0.5.0 `main` at `01fe42376f61e7d0d3738049f01935368e2c2e16`.
- Public absolute-value syntax: `abs(expression)` only.
- `abs` remains an explicitly supported EngCalc operation; no arbitrary Python call dispatch.
- Existing signed `envelope(...)` remains algebraic pointwise max/min over the same 201 samples.
- Magnitude mode is selected only when every envelope source is syntactically outermost `abs(...)` before symbolic expansion.
- Mixed absolute/signed envelope sources are invalid.
- Magnitude envelopes display one nonnegative maximum-magnitude branch only.
- Magnitude-envelope faint source curves retain their original signed values.
- Governing source index and signed governing quantity are retained per sample.
- One sweep parameter only; plotting variable cannot be the sweep parameter.
- Pint dimensional normalization and sweep non-mutation remain unchanged.
- Signed moment envelopes retain positive moment downward.
- Characteristic panels for multi-series plots and both envelope modes are placed inside the axes; no fixed right-side figure margin.
- Panel candidate corners: upper right, upper left, lower right, lower left.
- Panel placement uses deterministic data-occupancy scoring plus a legend-corner penalty.
- Single-series `plot(...)` keeps its existing extrema callouts.
- No `abs_envelope(...)`, `envelope_abs(...)`, named-case dictionaries, adaptive sampling, symbolic crossover solver, or new runtime dependency.
- Target package/runtime version: `0.6.0`.

---

## File Structure

### Production files

- `src/engcalc_colab/parser.py` — reserve `abs` as a built-in EngCalc operation while keeping current keyword/list restrictions.
- `src/engcalc_colab/engine.py` — symbolic `abs`, outer-abs metadata, signed/comparison series resolution, magnitude reduction, governing signed metadata.
- `src/engcalc_colab/numeric.py` — Pint-safe absolute value for numeric AST and SymPy `Abs` evaluation.
- `src/engcalc_colab/models.py` — backward-compatible envelope mode and governing signed metadata.
- `src/engcalc_colab/plotting.py` — in-axes panel placement and magnitude renderer.
- `src/engcalc_colab/__init__.py` — version 0.6.0.
- `pyproject.toml` — version 0.6.0; no dependency changes.
- `README.md` — public syntax and semantics.

### Tests

- `tests/test_parser.py`
- `tests/test_engine.py`
- `tests/test_numeric_context.py`
- `tests/test_plot_engine.py`
- `tests/test_envelope_engine.py`
- `tests/test_plotting.py`
- `tests/test_envelope_plotting.py`
- `tests/test_acceptance_native_plot.py`
- `tests/test_magic.py`
- `tests/test_packaging.py`

---

### Task 1: Safe general `abs(...)`

**Files:**
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/numeric.py`
- Test: `tests/test_parser.py`
- Test: `tests/test_engine.py`
- Test: `tests/test_numeric_context.py`

**Interfaces:**
- Symbolic: `abs(expression)` -> `sympy.Abs(expression)`.
- Numeric AST: only a direct `abs` call, exactly one positional argument, no keywords.
- SymPy numeric evaluation: `sp.Abs(quantity-expression)` returns the Pint quantity magnitude with units preserved.

- [ ] **Step 1: Add parser tests**

Append to `tests/test_parser.py`:

```python
def test_parser_accepts_abs_expression():
    stmt = parse_cell("A = abs(x)")[0]
    assert ast.unparse(stmt.expression) == "abs(x)"


def test_parser_reserves_abs_as_builtin_operation():
    with pytest.raises(EngSyntaxError, match="reserved"):
        parse_cell("abs = 3")


def test_parser_rejects_abs_keyword_arguments():
    with pytest.raises(EngSyntaxError, match="keyword arguments are unsupported"):
        parse_cell("A = abs(x, mode=1)")
```

- [ ] **Step 2: Add engine arity and symbolic tests**

Append to `tests/test_engine.py`:

```python
def test_abs_builds_sympy_absolute_value():
    engine = EngineeringEngine()
    result = eval_cell(engine, "A = abs(x - 3)")[-1]
    x = sp.Symbol("x")
    assert result.value == sp.Abs(x - 3)


def test_abs_rejects_zero_arguments():
    engine = EngineeringEngine()
    with pytest_raises(EngEvaluationError) as captured:
        eval_cell(engine, "A = abs()")
    assert str(captured.value) == "line 1: abs expects 1 arguments: expression"


def test_abs_rejects_multiple_arguments():
    engine = EngineeringEngine()
    with pytest_raises(EngEvaluationError) as captured:
        eval_cell(engine, "A = abs(x, 2)")
    assert str(captured.value) == "line 1: abs expects 1 arguments: expression"


def test_numeric_abs_end_to_end_preserves_units():
    engine = EngineeringEngine()
    eval_cell(engine, "P := -7*tonf")
    result = eval_cell(engine, "numeric(abs(P))")[-1]
    assert result.quantity.to("tonf").magnitude == 7.0
```

- [ ] **Step 3: Run parser/engine RED gate**

Run:

```bash
pytest -q tests/test_parser.py tests/test_engine.py
```

Expected:
- parser acceptance and keyword rejection may already pass under the generic parser;
- the reserved-target test fails until `abs` joins the EngCalc operation set;
- symbolic/arity/numeric-engine tests fail until evaluator support exists;
- all previous tests remain green.

- [ ] **Step 4: Implement parser reservation and symbolic evaluator**

In `src/engcalc_colab/parser.py`:

```python
_ALLOWED_CALLS = {
    "integral", "diff", "solve", "simplify", "expand", "factor",
    "subs", "eq", "sum", "numeric", "plot", "envelope", "abs"
}
```

Do not add `abs` to `_DISPLAY_SWEEP_CALLS`.

In `src/engcalc_colab/engine.py`, add after user-defined function dispatch:

```python
if name == "abs":
    self._require_arity(name, args, 1, "expression")
    return sp.Abs(args[0])
```

- [ ] **Step 5: Add NumericContext tests**

Append to `tests/test_numeric_context.py`:

```python
def test_numeric_ast_abs_preserves_pint_units():
    ctx = NumericContext()
    value = ctx.evaluate_expression(expr("abs(-3*tonf)"))
    assert value.to("tonf").magnitude == pytest.approx(3.0)


def test_sympy_abs_evaluation_preserves_pint_units():
    ctx = NumericContext()
    P = sp.Symbol("P")
    ctx.assign("P", expr("-7*tonf"))
    _, value = ctx.evaluate_symbolic(sp.Abs(P))
    assert value.to("tonf").magnitude == pytest.approx(7.0)
```

- [ ] **Step 6: Run NumericContext RED gate**

Run:

```bash
pytest -q tests/test_numeric_context.py
```

Expected: the two new tests fail because numeric AST and SymPy evaluators do not yet support absolute value.

- [ ] **Step 7: Implement restricted numeric absolute value**

In `NumericContext._evaluate_sympy()` before the unsupported-type error:

```python
if expr.func == sp.Abs and len(expr.args) == 1:
    return abs(self._evaluate_sympy(expr.args[0], substitutions))
```

In `_NumericAstEvaluator`:

```python
def visit_Call(self, node: ast.Call):
    if (
        not isinstance(node.func, ast.Name)
        or node.func.id != "abs"
        or len(node.args) != 1
        or node.keywords
    ):
        raise EngEvaluationError("unsupported numeric function")
    return abs(self.visit(node.args[0]))
```

- [ ] **Step 8: Verify Task 1 GREEN and commit**

Run:

```bash
pytest -q tests/test_parser.py tests/test_engine.py tests/test_numeric_context.py
pytest -q
```

Commit:

```bash
git add src/engcalc_colab/parser.py src/engcalc_colab/engine.py src/engcalc_colab/numeric.py tests/test_parser.py tests/test_engine.py tests/test_numeric_context.py
git commit -m "feat: add safe EngCalc absolute value"
```

---

### Task 2: Backward-compatible transport and response-expression metadata

**Files:**
- Modify: `src/engcalc_colab/models.py`
- Modify: `src/engcalc_colab/engine.py`
- Test: `tests/test_envelope_engine.py`
- Test: `tests/test_plot_engine.py`

**Interfaces:**

Extend `PlotResult` and `_PlotEvaluation` with:

```python
envelope_mode: str | None = None
governing_signed: tuple[Any, ...] | None = None
```

Introduce:

```python
@dataclass(frozen=True)
class _ResolvedExpression:
    source_label: str
    display_label: str
    signed_expression: object
    comparison_expression: object
    is_absolute: bool
```

Replace `_ResolvedResponseSeries` with the exact contract:

```python
@dataclass(frozen=True)
class _ResolvedResponseSeries:
    display_label: str
    variable: str
    x_values: tuple
    series: tuple[PlotSeries, ...]
    source_series: tuple[PlotSeries, ...]
    source_labels: tuple[str, ...]
    first_symbolic_expression: object
    envelope_mode: str | None = None
```

Meaning:
- `series`: normalized values used for ordinary plot display or envelope comparison;
- `source_series`: signed context values; equal to `series` except magnitude envelopes;
- `source_labels`: labels corresponding to `source_series`;
- `envelope_mode`: `None` for plot, `signed` or `magnitude` for envelope.

- [ ] **Step 1: Add transport RED tests**

Append to `tests/test_envelope_engine.py`:

```python
def test_plot_result_defaults_preserve_v050_transport():
    statement = parse_cell("plot(x, x, 0, 1)")[0]
    series = PlotSeries("x", (1, 2), False)
    result = PlotResult(statement, "x", "x", (0, 1), (series,))
    assert result.envelope_mode is None
    assert result.governing_signed is None


def test_plot_result_can_transport_magnitude_metadata():
    statement = parse_cell("envelope(abs(A(x)), abs(B(x)), x, 0, 1)")[0]
    source = (
        PlotSeries("A(x)", (-1, 2), False),
        PlotSeries("B(x)", (3, -4), False),
    )
    displayed = (PlotSeries("|V|_max(x)", (3, 4), False),)
    result = PlotResult(
        statement,
        "V(x)",
        "x",
        (0, 1),
        displayed,
        kind="envelope",
        source_series=source,
        source_labels=("A(x)", "B(x)"),
        governing_max=(1, 1),
        envelope_mode="magnitude",
        governing_signed=(3, -4),
    )
    assert result.envelope_mode == "magnitude"
    assert result.governing_signed == (3, -4)
```

- [ ] **Step 2: Run transport RED gate**

```bash
pytest -q tests/test_envelope_engine.py -k "transport"
```

Expected: fail only because new fields do not exist.

- [ ] **Step 3: Extend `PlotResult` and `_PlotEvaluation`**

Add defaults after current governing metadata and pass them through `EngineeringEngine.evaluate()`.

- [ ] **Step 4: Add `plot(abs(...))` RED tests**

Append to `tests/test_plot_engine.py`:

```python
def test_plot_abs_samples_nonnegative_shear_values():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*(L/2-x)\nq := 4*kN/m\nL := 4*m")
    result = eval_cell(engine, "plot(abs(V(x)), x, 0, L)")[-1]
    values = [item.to("kN").magnitude for item in result.series[0].y_values]
    assert values[0] == pytest.approx(8.0)
    assert values[100] == pytest.approx(0.0)
    assert values[-1] == pytest.approx(8.0)
    assert min(values) >= 0.0
    assert not result.series[0].is_moment


def test_plot_abs_preserves_moment_classification_from_inner_function():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nq := 4*kN/m\nL := 4*m")
    result = eval_cell(engine, "plot(abs(M(x)), x, 0, L)")[-1]
    assert result.series[0].is_moment
```

- [ ] **Step 5: Add `_ResolvedExpression` helper**

Implement:

```python
def _resolve_response_expression(self, node: ast.AST, variable: str) -> _ResolvedExpression:
    is_absolute = (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "abs"
    )
    if is_absolute:
        self._require_arity("abs", node.args, 1, "expression")
        signed_node = node.args[0]
        signed_expression = self.visit(signed_node)
        comparison_expression = sp.Abs(signed_expression)
        source_label = self._plot_expression_label(
            signed_node,
            variable,
            signed_expression,
        )
        display_label = f"|{source_label}|"
    else:
        signed_expression = self.visit(node)
        comparison_expression = signed_expression
        source_label = self._plot_expression_label(
            node,
            variable,
            signed_expression,
        )
        display_label = source_label

    return _ResolvedExpression(
        source_label=source_label,
        display_label=display_label,
        signed_expression=signed_expression,
        comparison_expression=comparison_expression,
        is_absolute=is_absolute,
    )
```

For normal `plot(...)`, sample `comparison_expression`; determine `is_moment` from `source_label`. Do not persist `source_series` in normal `PlotResult`.

- [ ] **Step 6: Verify plot regression and commit**

```bash
pytest -q tests/test_plot_engine.py tests/test_plot_parser.py tests/test_plotting.py
pytest -q
```

Commit:

```bash
git add src/engcalc_colab/models.py src/engcalc_colab/engine.py tests/test_envelope_engine.py tests/test_plot_engine.py
git commit -m "refactor: preserve response expression metadata"
```

---

### Task 3: Multi-expression magnitude envelopes

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Test: `tests/test_envelope_engine.py`

**Interfaces:**
- Signed envelope: `envelope_mode="signed"`, two displayed series, existing `governing_max/min` unchanged.
- Magnitude envelope: `envelope_mode="magnitude"`, one displayed series, signed `source_series`, `governing_max`, `governing_min=None`, `governing_signed` per sample.

- [ ] **Step 1: Add magnitude RED tests**

Append:

```python
def test_magnitude_envelope_keeps_signed_sources_and_one_abs_max_branch():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V_A(x) = 6*kN - 4*kN/m*x\n"
        "V_B(x) = -2*kN + 5*kN/m*x\n"
        "L := 2*m",
    )
    result = eval_cell(
        engine,
        "envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)",
    )[-1]

    assert result.envelope_mode == "magnitude"
    assert result.display_label == "V(x)"
    assert len(result.series) == 1
    assert result.source_labels == ("V_A(x)", "V_B(x)")
    assert [s.y_values[0].to("kN").magnitude for s in result.source_series] == pytest.approx([6.0, -2.0])
    assert [s.y_values[-1].to("kN").magnitude for s in result.source_series] == pytest.approx([-2.0, 8.0])
    assert result.series[0].y_values[0].to("kN").magnitude == pytest.approx(6.0)
    assert result.series[0].y_values[-1].to("kN").magnitude == pytest.approx(8.0)
    assert result.governing_max[0] == 0
    assert result.governing_max[-1] == 1
    assert result.governing_min is None
```

```python
def test_magnitude_envelope_retains_negative_signed_governing_value():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V_A(x) = -9*kN + 1*kN/m*x\n"
        "V_B(x) = 3*kN - 1*kN/m*x\n"
        "L := 2*m",
    )
    result = eval_cell(
        engine,
        "envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)",
    )[-1]
    assert result.series[0].y_values[0].to("kN").magnitude == pytest.approx(9.0)
    assert result.governing_signed[0].to("kN").magnitude == pytest.approx(-9.0)
    assert result.governing_max[0] == 0
```

```python
def test_envelope_rejects_mixed_absolute_and_signed_sources():
    engine = EngineeringEngine()
    eval_cell(engine, "V_A(x) = x\nV_B(x) = -x\nL := 2")
    with pytest.raises(
        EngEvaluationError,
        match="envelope cannot mix absolute and signed response series",
    ):
        eval_cell(engine, "envelope(abs(V_A(x)), V_B(x), x, 0, L)")
```

- [ ] **Step 2: Run magnitude RED gate**

```bash
pytest -q tests/test_envelope_engine.py -k "magnitude or mixed_absolute"
```

- [ ] **Step 3: Determine envelope mode before sampling**

In `_resolve_response_series()`:

```python
resolved_expressions = [
    self._resolve_response_expression(node, variable)
    for node in expression_nodes
]
absolute_flags = {item.is_absolute for item in resolved_expressions}
if call_name == "envelope" and len(absolute_flags) > 1:
    raise EngEvaluationError(
        "envelope cannot mix absolute and signed response series"
    )

envelope_mode = None
if call_name == "envelope":
    envelope_mode = "magnitude" if True in absolute_flags else "signed"
```

For magnitude mode:
- `series` samples `comparison_expression`;
- `source_series` samples `signed_expression`;
- `source_labels` use signed `source_label`;
- `display_label` comes from `_common_plot_label(source_labels, variable)`.

Normalize comparison and signed source sets to the same first comparison-series unit. `abs` preserves units, so both sets must be convertible to that target.

- [ ] **Step 4: Split signed and magnitude reducers**

Keep `_evaluate_envelope()` as dispatch:

```python
resolved = self._resolve_response_series(node, call_name="envelope")
if len(resolved.series) < 2:
    raise EngEvaluationError("envelope requires at least two response series")

if resolved.envelope_mode == "magnitude":
    self.plot_evaluation = self._build_magnitude_envelope(resolved)
else:
    self.plot_evaluation = self._build_signed_envelope(resolved)
return resolved.first_symbolic_expression
```

Magnitude reduction:

```python
magnitude_values = []
governing_indices = []
governing_signed = []

for sample_index in range(len(resolved.x_values)):
    magnitudes = [
        float(item.y_values[sample_index].magnitude)
        for item in resolved.series
    ]
    index = max(range(len(magnitudes)), key=magnitudes.__getitem__)
    governing_indices.append(index)
    magnitude_values.append(resolved.series[index].y_values[sample_index])
    governing_signed.append(resolved.source_series[index].y_values[sample_index])
```

Use label helper:

```python
def _magnitude_envelope_series_label(display_label: str, variable: str) -> str:
    suffix = f"({variable})"
    if display_label != "Comparison" and display_label.endswith(suffix):
        family = display_label[:-len(suffix)]
        return f"|{family}|_max({variable})"
    return "|response|_max"
```

- [ ] **Step 5: Mark existing signed envelopes explicitly**

Set `envelope_mode="signed"` while preserving all current numerical fields. Add to existing signed-envelope test:

```python
assert result.envelope_mode == "signed"
```

- [ ] **Step 6: Run engine regression and commit**

```bash
pytest -q tests/test_envelope_engine.py tests/test_plot_engine.py
pytest -q
```

Commit:

```bash
git add src/engcalc_colab/engine.py tests/test_envelope_engine.py
git commit -m "feat: add composable magnitude envelopes"
```

---

### Task 4: Magnitude sweep, units, and state semantics

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Test: `tests/test_envelope_engine.py`

**Interfaces:**

Change sweep helper to:

```python
def _evaluate_response_sweep(
    self,
    comparison_expression,
    signed_expression,
    comparison_label: str,
    source_label: str,
    variable: str,
    start_quantity,
    end_quantity,
    keyword_node: ast.keyword,
    *,
    call_name: str,
    preserve_signed_source: bool,
) -> tuple[list[PlotSeries], list[PlotSeries], tuple]:
```

Return `(comparison_series, source_series, x_values)`.

- [ ] **Step 1: Add magnitude-sweep RED tests**

```python
def test_magnitude_sweep_keeps_signed_cases_and_abs_governing_curve():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*(L/2-x)\nL := 4*m")
    result = eval_cell(
        engine,
        "envelope(abs(V(x)), x, 0, L, q=[2*kN/m, 4*kN/m, -5*kN/m])",
    )[-1]

    assert result.envelope_mode == "magnitude"
    assert result.source_labels == (
        "q = 2 kN/m",
        "q = 4 kN/m",
        "q = -5 kN/m",
    )
    assert result.source_series[2].y_values[0].to("kN").magnitude == pytest.approx(-10.0)
    assert result.series[0].y_values[0].to("kN").magnitude == pytest.approx(10.0)
    assert result.governing_max[0] == 2
    assert result.governing_signed[0].to("kN").magnitude == pytest.approx(-10.0)
```

```python
def test_magnitude_sweep_does_not_mutate_parameter_or_x():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V(x) = q*(L/2-x)\nq := 2.8*tonf/m\nL := 4*m\nx := 1*m",
    )
    eval_cell(
        engine,
        "envelope(abs(V(x)), x, 0, L, q=[2*kN/m, 4*kN/m])",
    )
    assert engine.numeric_context.get("q").to("tonf/m").magnitude == pytest.approx(2.8)
    assert engine.numeric_context.get("x").to("m").magnitude == pytest.approx(1.0)
```

```python
def test_magnitude_envelope_normalizes_compatible_units_before_comparison():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V_A(x) = -q_A*x\n"
        "V_B(x) = q_B*x\n"
        "q_A := 1*kN/m\nq_B := 1500*N/m\nL := 2*m",
    )
    result = eval_cell(
        engine,
        "envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)",
    )[-1]
    assert result.series[0].y_values[-1].to("kN").magnitude == pytest.approx(3.0)
    assert result.governing_signed[-1].to("kN").magnitude == pytest.approx(3.0)
```

- [ ] **Step 2: Run sweep RED gate**

```bash
pytest -q tests/test_envelope_engine.py -k "magnitude and (sweep or mutate or units or normalizes)"
```

- [ ] **Step 3: Implement shared sweep sampling**

For each sweep value:
1. sample `comparison_expression` with the existing local override;
2. if `preserve_signed_source` and expressions differ, sample `signed_expression` with the identical override;
3. otherwise reuse comparison values as source values;
4. use the same sweep label for both series.

Preserve current validation:
- sweep parameter is named;
- sweep parameter is not plotting variable;
- parameter appears in expanded expression;
- sweep values have compatible units;
- stored parameter/x are not mutated.

- [ ] **Step 4: Verify and commit**

```bash
pytest -q tests/test_envelope_engine.py tests/test_numeric_context.py
pytest -q
```

Commit:

```bash
git add src/engcalc_colab/engine.py tests/test_envelope_engine.py
git commit -m "test: harden magnitude envelope sweeps"
```

---

### Task 5: In-axes characteristic panel auto-placement

**Files:**
- Modify: `src/engcalc_colab/plotting.py`
- Test: `tests/test_plotting.py`
- Test: `tests/test_envelope_plotting.py`

**Interfaces:**

```python
_PANEL_CORNERS = (
    "upper right",
    "upper left",
    "lower right",
    "lower left",
)


def _panel_footprint(text: str) -> tuple[float, float]:
    ...


def _choose_panel_corner(
    axis,
    data_xy: list[tuple[float, float]],
    text: str,
    *,
    legend_corner: str | None,
) -> str:
    ...


def _add_characteristic_panel(
    axis,
    text: str,
    data_xy: list[tuple[float, float]],
    *,
    legend_corner: str | None = None,
):
    ...
```

Implementation code in the steps below replaces the signature placeholders above.

- [ ] **Step 1: Replace old outside-panel expectations**

In `tests/test_plotting.py`:

```python
def test_multiseries_characteristic_panel_is_inside_axes():
    figure = render_plot(sweep_moment_plot_result())
    axis = figure.axes[0]
    assert len(figure.texts) == 0
    panels = [text for text in axis.texts if "Characteristic values" in text.get_text()]
    assert len(panels) == 1
    assert panels[0].get_transform() == axis.transAxes
    x, y = panels[0].get_position()
    assert 0.0 <= x <= 1.0
    assert 0.0 <= y <= 1.0
```

In `tests/test_envelope_plotting.py`:

```python
def test_signed_envelope_characteristic_panel_is_inside_axes():
    figure = render_plot(moment_envelope_result())
    axis = figure.axes[0]
    assert len(figure.texts) == 0
    panels = [
        text for text in axis.texts
        if "Envelope characteristic values" in text.get_text()
    ]
    assert len(panels) == 1
    assert "max = 36.00 kN·m" in panels[0].get_text()
    assert "min = -18.00 kN·m" in panels[0].get_text()
    assert panels[0].get_transform() == axis.transAxes
```

- [ ] **Step 2: Add deterministic corner-selection RED tests**

Import `_choose_panel_corner` in `tests/test_plotting.py`, then add:

```python
def test_panel_chooser_uses_different_corners_for_different_occupancy():
    import matplotlib.pyplot as plt

    fig, axis = plt.subplots()
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 10)

    upper_right_data = [(8.5, 8.5), (9.0, 9.0), (9.5, 9.5)] * 30
    lower_left_data = [(0.5, 0.5), (1.0, 1.0), (1.5, 1.5)] * 30

    first = _choose_panel_corner(
        axis,
        upper_right_data,
        "Characteristic values\nmax = 10\nmin = 0",
        legend_corner=None,
    )
    second = _choose_panel_corner(
        axis,
        lower_left_data,
        "Characteristic values\nmax = 10\nmin = 0",
        legend_corner=None,
    )
    plt.close(fig)

    assert first != "upper right"
    assert second != "lower left"
    assert first != second
```

```python
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
```

- [ ] **Step 3: Run panel RED gate**

```bash
pytest -q tests/test_plotting.py tests/test_envelope_plotting.py
```

- [ ] **Step 4: Implement panel footprint**

```python
_PANEL_CORNERS = (
    "upper right",
    "upper left",
    "lower right",
    "lower left",
)


def _panel_footprint(text: str) -> tuple[float, float]:
    lines = text.splitlines() or [""]
    max_chars = max(len(line) for line in lines)
    width = min(0.46, max(0.22, 0.14 + 0.006 * max_chars))
    height = min(0.72, max(0.16, 0.08 + 0.043 * len(lines)))
    return width, height
```

- [ ] **Step 5: Implement normalized-data helper and scoring**

```python
def _data_to_axes_fraction(axis, x: float, y: float) -> tuple[float, float]:
    x0, x1 = axis.get_xlim()
    y0, y1 = axis.get_ylim()
    x_fraction = 0.5 if x1 == x0 else (x - x0) / (x1 - x0)
    y_fraction = 0.5 if y1 == y0 else (y - y0) / (y1 - y0)
    return x_fraction, y_fraction
```

For each corner, create a rectangle using footprint plus 0.02 padding. Score:
- `3` per sample inside rectangle;
- `1` per sample inside rectangle expanded by `0.04`;
- `1000` if corner equals `legend_corner`;
- choose minimum `(score, corner_priority_index)`.

- [ ] **Step 6: Implement axes-owned panel**

```python
def _add_characteristic_panel(
    axis,
    text: str,
    data_xy: list[tuple[float, float]],
    *,
    legend_corner: str | None = None,
):
    corner = _choose_panel_corner(
        axis,
        data_xy,
        text,
        legend_corner=legend_corner,
    )
    anchors = {
        "upper right": (0.98, 0.98, "right", "top"),
        "upper left": (0.02, 0.98, "left", "top"),
        "lower right": (0.98, 0.02, "right", "bottom"),
        "lower left": (0.02, 0.02, "left", "bottom"),
    }
    x, y, ha, va = anchors[corner]
    return axis.text(
        x,
        y,
        text,
        transform=axis.transAxes,
        ha=ha,
        va=va,
        fontsize=8.5,
        zorder=8,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": axis.get_facecolor(),
            "edgecolor": axis.spines["bottom"].get_edgecolor(),
            "linewidth": 0.8,
            "alpha": 0.94,
        },
    )
```

- [ ] **Step 7: Wire multi-series and signed envelope renderers**

For each renderer:
- collect data points from visible response curves;
- set legend with `loc="upper right"`;
- call `_add_characteristic_panel(..., legend_corner="upper right")`;
- remove `figure.text(...)`;
- replace `figure.tight_layout(rect=(0.0, 0.0, 0.73, 1.0))` with `figure.tight_layout()`.

Do not modify `_render_single_series()`.

- [ ] **Step 8: Verify and commit**

```bash
pytest -q tests/test_plotting.py tests/test_envelope_plotting.py
pytest -q
```

Commit:

```bash
git add src/engcalc_colab/plotting.py tests/test_plotting.py tests/test_envelope_plotting.py
git commit -m "fix: place characteristic panels inside plots"
```

---

### Task 6: Magnitude-envelope renderer

**Files:**
- Modify: `src/engcalc_colab/plotting.py`
- Test: `tests/test_envelope_plotting.py`

**Interfaces:**
- `_render_envelope()` branches on `result.envelope_mode`.
- Signed mode: two emphasized branches, fill between them.
- Magnitude mode: one emphasized branch, fill from zero to branch.
- Both modes: signed faint source curves.
- Magnitude panel: max magnitude, x, signed governing value, governing source label.

- [ ] **Step 1: Add magnitude fixture**

```python
def shear_magnitude_envelope_result():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V_constr(x) = 6*kN - 4*kN/m*x\n"
        "V_uso(x) = -9*kN + 1*kN/m*x\n"
        "L := 2*m",
    )
    return eval_cell(
        engine,
        "envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)",
    )[-1]
```

- [ ] **Step 2: Add magnitude visual RED tests**

```python
def test_magnitude_envelope_shows_signed_sources_and_one_nonnegative_boundary():
    axis = render_plot(shear_magnitude_envelope_result()).axes[0]
    faint_lines = [line for line in axis.lines if line.get_label() == "_nolegend_"]
    assert len(faint_lines) == 2
    assert any(min(line.get_ydata()) < 0 for line in faint_lines)

    boundaries = [line for line in axis.lines if line.get_label() == "|V|_max(x)"]
    assert len(boundaries) == 1
    assert min(boundaries[0].get_ydata()) >= 0.0
```

```python
def test_magnitude_envelope_fill_and_legend():
    axis = render_plot(shear_magnitude_envelope_result()).axes[0]
    fills = [c for c in axis.collections if isinstance(c, PolyCollection)]
    assert len(fills) == 1
    assert [text.get_text() for text in axis.get_legend().get_texts()] == ["|V|_max(x)"]
```

```python
def test_magnitude_panel_reports_signed_governing_case_inside_axes():
    figure = render_plot(shear_magnitude_envelope_result())
    axis = figure.axes[0]
    panels = [text for text in axis.texts if "Magnitude envelope" in text.get_text()]
    assert len(panels) == 1
    text = panels[0].get_text()
    assert "|max| = 9.00 kN" in text
    assert "signed = -9.00 kN" in text
    assert "V_uso(x)" in text
    assert panels[0].get_transform() == axis.transAxes
```

- [ ] **Step 3: Run magnitude renderer RED gate**

```bash
pytest -q tests/test_envelope_plotting.py -k "magnitude"
```

- [ ] **Step 4: Add magnitude panel formatter**

```python
def _magnitude_envelope_characteristic_panel_text(result: PlotResult) -> str:
    magnitude_series = result.series[0]
    values = [float(value.magnitude) for value in magnitude_series.y_values]
    index = max(range(len(values)), key=values.__getitem__)
    governing_index = result.governing_max[index]
    signed_value = result.governing_signed[index]
    source_label = result.source_labels[governing_index]
    return "\n".join([
        "Magnitude envelope",
        (
            "|max| = "
            f"{_quantity_label(magnitude_series.y_values[index], moment=magnitude_series.is_moment)}"
            "    x = "
            f"{_quantity_label(result.x_values[index])}"
        ),
        (
            "signed = "
            f"{_quantity_label(signed_value, moment=magnitude_series.is_moment)}"
        ),
        f"governing = {source_label}",
    ])
```

- [ ] **Step 5: Split envelope body rendering**

Shared `_render_envelope()` renders faint signed source curves and zero line. Then:

```python
if result.envelope_mode == "magnitude":
    _render_magnitude_envelope_body(figure, axis, result, x_values)
else:
    _render_signed_envelope_body(figure, axis, result, x_values)
```

Magnitude body requirements:
- one line, linewidth `2.5`, zorder `4`;
- `fill_between(x_values, 0.0, magnitude_y, alpha=0.10, zorder=2)`;
- legend only magnitude line;
- y-axis label uses signed common response family and unit;
- title `|V(x)| envelope` for display label `V(x)`;
- invert moment axis if magnitude series is moment-classified;
- panel uses signed-source + magnitude data points for occupancy scoring.

- [ ] **Step 6: Verify signed and magnitude rendering together**

```bash
pytest -q tests/test_envelope_plotting.py tests/test_plotting.py
pytest -q
```

- [ ] **Step 7: Commit**

```bash
git add src/engcalc_colab/plotting.py tests/test_envelope_plotting.py
git commit -m "feat: render magnitude envelope design demand"
```

---

### Task 7: Integration, documentation, version 0.6.0, and clean-wheel gate

**Files:**
- Modify: `tests/test_acceptance_native_plot.py`
- Modify: `tests/test_magic.py`
- Modify: `tests/test_packaging.py`
- Modify: `tests/test_parser.py`
- Modify: `README.md`
- Modify: `src/engcalc_colab/__init__.py`
- Modify: `pyproject.toml`
- Temporary during execution only: `.github/workflows/engcalc-v060-validation.yml`

**Interfaces:**
- Version: `0.6.0`.
- Wheel: `engcalc_colab-0.6.0-py3-none-any.whl`.
- No runtime dependency additions.

- [ ] **Step 1: Add end-to-end acceptance test**

```python
def test_native_magnitude_envelope_acceptance():
    engine = EngineeringEngine()
    cell = """
V_constr(x) = 6*kN - 4*kN/m*x
V_uso(x) = -9*kN + 1*kN/m*x
L := 2*m

envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)
"""
    results = [engine.evaluate(stmt) for stmt in parse_cell(cell)]
    result = results[-1]

    assert isinstance(result, PlotResult)
    assert result.kind == "envelope"
    assert result.envelope_mode == "magnitude"
    assert len(result.series) == 1
    assert len(result.source_series) == 2

    figure = render_plot(result)
    axis = figure.axes[0]
    assert len(figure.texts) == 0
    assert any("Magnitude envelope" in text.get_text() for text in axis.texts)
    assert [text.get_text() for text in axis.get_legend().get_texts()] == [
        "|V|_max(x)"
    ]
```

Use existing imports/helpers in that test file; add only missing `PlotResult` or `render_plot` imports.

- [ ] **Step 2: Add magnitude-envelope source-order magic test**

Reuse the current `tests/test_magic.py` display-capture helper. Construct a cell whose outputs are:

```text
Math -> Figure -> Math
```

with the figure generated by `envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)`.

Assert exactly that order; do not build a second IPython harness.

- [ ] **Step 3: Run integration gate**

```bash
pytest -q tests/test_acceptance_native_plot.py tests/test_magic.py
```

- [ ] **Step 4: Introduce release-version RED**

In `tests/test_packaging.py`:

```python
def test_pyproject_version_is_0_6_0():
    assert _project_metadata()["version"] == "0.6.0"


def test_runtime_version_is_0_6_0():
    assert engcalc_colab.__version__ == "0.6.0"
```

In `tests/test_parser.py::test_package_version_and_statement_model`:

```python
assert __version__ == "0.6.0"
```

Run:

```bash
pytest -q tests/test_packaging.py tests/test_parser.py
```

Expected: only old-version assertions fail.

- [ ] **Step 5: Bump version**

`pyproject.toml`:

```toml
version = "0.6.0"
```

`src/engcalc_colab/__init__.py`:

```python
__version__ = "0.6.0"
```

Do not alter dependency declarations.

- [ ] **Step 6: Update README**

Add canonical examples:

```text
%%eng

V_constr(x) = 6*kN - 4*kN/m*x
V_uso(x) = -9*kN + 1*kN/m*x
L := 2*m

envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)
```

```text
%%eng

V(x) = q*(L/2-x)
L := 4*m

envelope(abs(V(x)), x, 0, L, q=[2*tonf/m, 3*tonf/m, 4*tonf/m])
```

Document:
- `abs(...)` safe mathematical operation;
- signed `envelope(...)` unchanged;
- all-outermost-`abs` envelope = maximum magnitude;
- signed faint source curves retained;
- mixed mode rejected;
- panels auto-place inside graph;
- no `abs_envelope(...)` alias.

- [ ] **Step 7: Source full suite**

```bash
pytest -q
```

Record exact count from output for PR evidence.

- [ ] **Step 8: Build real wheel**

```bash
rm -rf build dist
python -m build --wheel
test -f dist/engcalc_colab-0.6.0-py3-none-any.whl
```

- [ ] **Step 9: Install clean wheel**

```bash
python -m venv /tmp/engcalc-v060-wheel
/tmp/engcalc-v060-wheel/bin/python -m pip install --upgrade pip
/tmp/engcalc-v060-wheel/bin/python -m pip install dist/engcalc_colab-0.6.0-py3-none-any.whl pytest ipython
```

- [ ] **Step 10: Installed-wheel smoke test from `/tmp`**

```bash
cd /tmp
/tmp/engcalc-v060-wheel/bin/python - <<'PY'
import engcalc_colab
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot

assert engcalc_colab.__version__ == "0.6.0"

engine = EngineeringEngine()
cell = """
V_constr(x) = 6*kN - 4*kN/m*x
V_uso(x) = -9*kN + 1*kN/m*x
L := 2*m
envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)
"""
result = [engine.evaluate(stmt) for stmt in parse_cell(cell)][-1]
assert result.envelope_mode == "magnitude"
assert len(result.series) == 1
assert len(result.source_series) == 2
assert result.series[0].y_values[0].to("kN").magnitude == 9.0
assert result.governing_signed[0].to("kN").magnitude == -9.0

figure = render_plot(result)
axis = figure.axes[0]
assert len(figure.texts) == 0
assert any("Magnitude envelope" in text.get_text() for text in axis.texts)
assert [text.get_text() for text in axis.get_legend().get_texts()] == ["|V|_max(x)"]

signed_engine = EngineeringEngine()
signed_cell = """
M_A(x) = q*x*(L-x)/2
M_B(x) = -0.5*q*x*(L-x)/2
q := 8*kN/m
L := 6*m
envelope(M_A(x), M_B(x), x, 0, L)
"""
signed = [signed_engine.evaluate(stmt) for stmt in parse_cell(signed_cell)][-1]
assert signed.envelope_mode == "signed"
assert len(signed.series) == 2
assert render_plot(signed).axes[0].yaxis_inverted()

print("EngCalc 0.6.0 installed-wheel smoke PASS")
PY
```

Expected:

```text
EngCalc 0.6.0 installed-wheel smoke PASS
```

- [ ] **Step 11: Full suite against installed wheel outside source tree**

Under GitHub Actions:

```bash
cd /tmp
PYTHONPATH= /tmp/engcalc-v060-wheel/bin/python -m pytest -q -c /dev/null "$GITHUB_WORKSPACE/tests"
```

Outside Actions, substitute the repository test directory absolute path.

- [ ] **Step 12: Repeat source suite**

```bash
pytest -q
```

- [ ] **Step 13: Remove temporary validation workflow if created**

If `.github/workflows/engcalc-v060-validation.yml` was created solely for release validation, delete it after the final successful gate. Verify the cleanup commit contains only that deletion.

- [ ] **Step 14: Final diff review**

```bash
git diff main...HEAD --stat
git diff main...HEAD -- src/engcalc_colab/parser.py src/engcalc_colab/numeric.py src/engcalc_colab/engine.py src/engcalc_colab/models.py src/engcalc_colab/plotting.py
```

Verify:
- no `abs_envelope`/`envelope_abs` public API;
- no arbitrary function execution;
- signed-envelope math unchanged;
- single-series renderer unchanged;
- no figure-level characteristic panel in multi-series/envelope paths;
- no new runtime dependency.

- [ ] **Step 15: Commit release files**

```bash
git add README.md pyproject.toml src/engcalc_colab/__init__.py tests/test_acceptance_native_plot.py tests/test_magic.py tests/test_packaging.py tests/test_parser.py
git commit -m "release: prepare EngCalc 0.6.0"
```

---

## Final Acceptance Checklist

- [ ] `abs(expression)` works symbolically.
- [ ] `abs()` and multi-argument `abs` fail with concise arity errors.
- [ ] Numeric `abs` preserves Pint units.
- [ ] `numeric(abs(P))` works end-to-end.
- [ ] `plot(abs(V(x)), ...)` samples nonnegative values.
- [ ] `plot(abs(M(x)), ...)` retains moment classification.
- [ ] Signed envelope still returns 0.5.0 algebraic max/min.
- [ ] Magnitude envelope returns one maximum-magnitude branch.
- [ ] Magnitude source curves preserve signs.
- [ ] Governing source index and signed governing quantity are retained.
- [ ] Mixed signed/absolute envelope sources are rejected.
- [ ] Magnitude sweep works and does not mutate state.
- [ ] Compatible units normalize before magnitude comparison.
- [ ] Multi-series panel is inside axes.
- [ ] Signed-envelope panel is inside axes.
- [ ] Magnitude-envelope panel is inside axes.
- [ ] Panel chooser demonstrates different corners for different occupancy.
- [ ] Legend corner is penalized.
- [ ] No fixed right-side panel margin remains.
- [ ] Single-series callouts remain unchanged.
- [ ] Moment-positive-down remains unchanged.
- [ ] Full source suite passes.
- [ ] Real 0.6.0 wheel builds.
- [ ] Clean wheel installation passes.
- [ ] Installed-wheel smoke passes.
- [ ] Full suite passes against installed wheel outside source tree.
- [ ] README matches final public syntax.
- [ ] Temporary validation workflow is absent from final product diff.
