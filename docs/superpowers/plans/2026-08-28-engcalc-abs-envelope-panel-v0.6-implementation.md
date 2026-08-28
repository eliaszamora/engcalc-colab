# EngCalc 0.6.0 Absolute-Value Envelope and In-Axes Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe general `abs(...)` operation, make `envelope(abs(...), ...)` produce a structural magnitude envelope while retaining signed source responses, and move multi-series/envelope characteristic panels inside the axes with deterministic automatic corner placement.

**Architecture:** Preserve the EngCalc 0.5.0 shared `plot/envelope` response-resolution pipeline. Add explicit outer-`abs` metadata before symbolic expansion so magnitude envelopes can sample signed inner responses for context while comparing their absolute values; extend `PlotResult` minimally with envelope mode and governing signed quantities. Keep rendering in `plotting.py`, but introduce small deterministic helpers for axes-owned characteristic panels so multi-series plots, signed envelopes, and magnitude envelopes share one placement policy without browser-dependent measurements.

**Tech Stack:** Python 3.10+, SymPy, Pint, Matplotlib, IPython/Jupyter, pytest.

**Spec:** `docs/superpowers/specs/2026-08-28-engcalc-abs-envelope-panel-v0.6-design.md`

## Global Constraints

- Base checkpoint is EngCalc 0.5.0 `main` commit `01fe42376f61e7d0d3738049f01935368e2c2e16`.
- Public absolute-value syntax is exactly `abs(expression)`.
- `abs(...)` is explicitly allow-listed; it must not expose arbitrary Python builtins or arbitrary call dispatch.
- Existing signed `envelope(...)` semantics remain sampled algebraic pointwise maximum/minimum.
- Magnitude-envelope mode is selected only when every source expression is syntactically outermost `abs(...)` before symbolic expansion.
- Mixed signed/absolute envelope sources are invalid.
- Magnitude envelopes display one nonnegative maximum-magnitude branch only.
- Magnitude-envelope faint source curves preserve their original signed values.
- Governing source index and original signed governing quantity are retained for every sample.
- Both signed and magnitude envelopes use the existing 201 uniformly spaced samples.
- One sweep parameter only; the plotting variable cannot be the sweep parameter.
- Existing Pint-aware dimensional normalization and non-mutating sweep semantics remain unchanged.
- Signed moment envelopes keep positive moment downward.
- Characteristic panels for multi-series plots and both envelope modes live inside the axes; no fixed right-side figure margin is reserved.
- Panel placement considers upper-right, upper-left, lower-right, and lower-left corners using deterministic data-occupancy scoring plus legend conflict penalty.
- Single-series `plot(...)` keeps its existing boxed extrema callouts.
- No `abs_envelope(...)`, `envelope_abs(...)`, arbitrary envelope mode keyword, named case dictionaries, adaptive sampling, symbolic crossover solving, or new runtime dependency is introduced.
- Target package/runtime version is `0.6.0`.

---

## File Structure

### Production files to modify

- `src/engcalc_colab/parser.py` — reserve and allow-list safe `abs(...)` without relaxing existing keyword/list restrictions.
- `src/engcalc_colab/engine.py` — evaluate symbolic `abs`, preserve outer-abs expression metadata, resolve signed/comparison source series, compute magnitude envelopes, and retain governing signed quantities.
- `src/engcalc_colab/numeric.py` — evaluate SymPy `Abs` against Pint quantities and support restricted numeric-expression `abs(...)` without general function dispatch.
- `src/engcalc_colab/models.py` — extend `PlotResult` with backward-compatible `envelope_mode` and `governing_signed` metadata.
- `src/engcalc_colab/plotting.py` — add deterministic in-axes panel placement and magnitude-envelope rendering while preserving single-series behavior.
- `src/engcalc_colab/__init__.py` — bump runtime version to 0.6.0.
- `pyproject.toml` — bump package version to 0.6.0; dependency list remains unchanged.
- `README.md` — document `abs(...)`, magnitude envelopes, signed source context, and in-axes characteristic panels.

### Tests to modify

- `tests/test_parser.py` — reserve/version assertions and safe `abs` parsing.
- `tests/test_engine.py` — symbolic `abs` behavior and arity.
- `tests/test_numeric_context.py` — Pint-preserving absolute value in numeric and SymPy evaluation.
- `tests/test_plot_engine.py` — `plot(abs(...))` sampling and structural classification.
- `tests/test_envelope_engine.py` — magnitude-envelope reduction, metadata, mixed-mode errors, units, sweep, state.
- `tests/test_plotting.py` — multi-series in-axes panel placement and no reserved right margin.
- `tests/test_envelope_plotting.py` — signed-envelope in-axes panel plus magnitude-envelope visual contract.
- `tests/test_acceptance_native_plot.py` — end-to-end `%%eng` magnitude envelope acceptance.
- `tests/test_magic.py` — source-order rendering with magnitude envelope if not already covered by acceptance.
- `tests/test_packaging.py` — release metadata 0.6.0.

---

### Task 1: Add safe general `abs(...)` evaluation

**Files:**
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/numeric.py`
- Test: `tests/test_parser.py`
- Test: `tests/test_engine.py`
- Test: `tests/test_numeric_context.py`

**Interfaces:**
- Consumes: existing restricted AST parser and `_Evaluator.visit_Call()` dispatch.
- Produces: `abs(expression)` -> SymPy `Abs(expression)` in symbolic EngCalc; `NumericContext` can evaluate SymPy `Abs` and restricted numeric AST `abs(...)` while preserving Pint units.
- Security invariant: `_NumericAstEvaluator.visit_Call()` accepts only a direct `ast.Name(id="abs")`, exactly one positional argument, and no keywords.

- [ ] **Step 1: Add parser and symbolic-engine RED tests**

Append to `tests/test_parser.py`:

```python
def test_parser_accepts_abs_as_explicit_safe_operation():
    stmt = parse_cell("A = abs(x)")[0]
    assert ast.unparse(stmt.expression) == "abs(x)"


def test_parser_reserves_abs_as_builtin_operation():
    with pytest.raises(EngSyntaxError, match="reserved"):
        parse_cell("abs = 3")


def test_parser_rejects_abs_keyword_arguments():
    with pytest.raises(EngSyntaxError, match="keyword arguments are unsupported"):
        parse_cell("A = abs(x, mode=1)")
```

Append to `tests/test_engine.py`:

```python
def test_abs_builds_sympy_absolute_value():
    engine = EngineeringEngine()
    result = eval_cell(engine, "A = abs(x - 3)")[-1]
    x = sp.Symbol("x")
    assert result.value == sp.Abs(x - 3)


def test_abs_requires_exactly_one_argument():
    engine = EngineeringEngine()
    with pytest_raises(EngEvaluationError) as captured:
        eval_cell(engine, "A = abs(x, 2)")
    assert str(captured.value) == "line 1: abs expects 1 arguments: expression"
```

Note: `abs()` with zero arguments is syntactically invalid in the current parser's empty-call handling only if Python rejects it; if it parses, add the parallel engine assertion for `abs()` with the same arity message.

- [ ] **Step 2: Run focused parser/engine tests and verify RED**

Run:

```bash
pytest -q tests/test_parser.py tests/test_engine.py
```

Expected: new tests fail because `abs` is not in `_ALLOWED_CALLS` and engine has no `abs` branch; all pre-existing tests remain green.

- [ ] **Step 3: Implement the minimal parser and symbolic evaluator support**

In `src/engcalc_colab/parser.py`, add `abs` to the explicit call allow-list:

```python
_ALLOWED_CALLS = {
    "integral", "diff", "solve", "simplify", "expand", "factor",
    "subs", "eq", "sum", "numeric", "plot", "envelope", "abs"
}
```

Do not add `abs` to `_DISPLAY_SWEEP_CALLS`; therefore keyword arguments remain rejected by the existing generic keyword guard.

In `src/engcalc_colab/engine.py`, after user-defined function dispatch and before the other one-argument symbolic operations, add:

```python
if name == "abs":
    self._require_arity(name, args, 1, "expression")
    return sp.Abs(args[0])
```

- [ ] **Step 4: Add numeric RED tests**

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

- [ ] **Step 5: Run numeric tests and verify RED**

Run:

```bash
pytest -q tests/test_numeric_context.py
```

Expected: only the new absolute-value tests fail because `_NumericAstEvaluator` rejects `Call` and `_evaluate_sympy()` rejects SymPy `Abs`.

- [ ] **Step 6: Implement restricted numeric absolute value**

In `NumericContext._evaluate_sympy()` add before the final unsupported-type error:

```python
if expr.func == sp.Abs and len(expr.args) == 1:
    return abs(self._evaluate_sympy(expr.args[0], substitutions))
```

In `_NumericAstEvaluator` add:

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

This is intentionally not a general function registry.

- [ ] **Step 7: Verify Task 1 GREEN and commit**

Run:

```bash
pytest -q tests/test_parser.py tests/test_engine.py tests/test_numeric_context.py
pytest -q
```

Expected: all tests pass.

Commit:

```bash
git add src/engcalc_colab/parser.py src/engcalc_colab/engine.py src/engcalc_colab/numeric.py tests/test_parser.py tests/test_engine.py tests/test_numeric_context.py
git commit -m "feat: add safe EngCalc absolute value"
```

---

### Task 2: Extend plot transport and preserve signed/comparison response metadata

**Files:**
- Modify: `src/engcalc_colab/models.py`
- Modify: `src/engcalc_colab/engine.py`
- Test: `tests/test_envelope_engine.py`
- Test: `tests/test_plot_engine.py`

**Interfaces:**
- Extends `PlotResult` with defaults:

```python
envelope_mode: str | None = None
governing_signed: tuple[Any, ...] | None = None
```

- Extends `_PlotEvaluation` with matching fields.
- Introduces private resolved-expression metadata:

```python
@dataclass(frozen=True)
class _ResolvedExpression:
    source_label: str
    display_label: str
    signed_expression: object
    comparison_expression: object
    is_absolute: bool
```

- Extends `_ResolvedResponseSeries` so `series` means the normalized values used for display/comparison, while `source_series` means signed source values used as faint context. For normal plots and signed envelopes they are equal; for magnitude envelopes they differ.

- [ ] **Step 1: Add RED transport tests**

Append to `tests/test_envelope_engine.py`:

```python
def test_plot_result_defaults_preserve_v050_transport():
    statement = parse_cell("plot(x, x, 0, 1)")[0]
    series = PlotSeries("x", (1, 2), False)
    result = PlotResult(statement, "x", "x", (0, 1), (series,))
    assert result.envelope_mode is None
    assert result.governing_signed is None


def test_plot_result_can_transport_magnitude_envelope_metadata():
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

- [ ] **Step 2: Run focused test and verify RED**

Run:

```bash
pytest -q tests/test_envelope_engine.py -k "transport"
```

Expected: fail because the new `PlotResult` fields do not exist.

- [ ] **Step 3: Extend immutable transport with backward-compatible defaults**

In `src/engcalc_colab/models.py` append after `governing_min`:

```python
envelope_mode: str | None = None
governing_signed: tuple[Any, ...] | None = None
```

In `_PlotEvaluation` add matching fields and pass them through in `EngineeringEngine.evaluate()` when creating `PlotResult`.

- [ ] **Step 4: Add RED tests for `plot(abs(...))` and structural classification**

Append to `tests/test_plot_engine.py`:

```python
def test_plot_abs_samples_nonnegative_values_and_keeps_shear_family():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*(L/2-x)\nq := 4*kN/m\nL := 4*m")
    result = eval_cell(engine, "plot(abs(V(x)), x, 0, L)")[-1]

    assert len(result.series) == 1
    values = [item.to("kN").magnitude for item in result.series[0].y_values]
    assert min(values) >= 0.0
    assert values[0] == pytest.approx(8.0)
    assert values[100] == pytest.approx(0.0)
    assert values[-1] == pytest.approx(8.0)
    assert not result.series[0].is_moment
```

Add a moment counterpart:

```python
def test_plot_abs_preserves_moment_classification_from_inner_function():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nq := 4*kN/m\nL := 4*m")
    result = eval_cell(engine, "plot(abs(M(x)), x, 0, L)")[-1]
    assert result.series[0].is_moment
```

- [ ] **Step 5: Implement expression metadata without changing existing plot semantics**

In `engine.py`, introduce `_ResolvedExpression` and a helper with this contract:

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

Use comparison expressions for ordinary `plot(abs(...))`, but compute `is_moment` from `source_label`, not the decorated `|...|` label.

For normal `plot(...)`, `source_series` does not need to be persisted into `PlotResult`; preserve the 0.5.0 result contract.

- [ ] **Step 6: Verify plot regression gate and commit**

Run:

```bash
pytest -q tests/test_plot_engine.py tests/test_plot_parser.py tests/test_plotting.py
pytest -q
```

Expected: all existing plot behavior plus new `plot(abs(...))` tests pass.

Commit:

```bash
git add src/engcalc_colab/models.py src/engcalc_colab/engine.py tests/test_envelope_engine.py tests/test_plot_engine.py
git commit -m "refactor: preserve response expression metadata"
```

---

### Task 3: Implement multi-expression magnitude envelopes

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Test: `tests/test_envelope_engine.py`

**Interfaces:**
- `envelope_mode="signed"` for existing algebraic envelopes.
- `envelope_mode="magnitude"` when every source expression is outermost `abs(...)`.
- Magnitude `PlotResult.series` contains exactly one `PlotSeries`.
- Magnitude `PlotResult.source_series` contains normalized signed source responses.
- `governing_max` stores the governing source index at every sample.
- `governing_min` is `None` in magnitude mode.
- `governing_signed` stores the original signed governing Pint quantity at every sample.

- [ ] **Step 1: Add RED tests for magnitude mode and mixed-mode rejection**

Append to `tests/test_envelope_engine.py`:

```python
def test_magnitude_envelope_keeps_signed_sources_and_returns_one_abs_max_branch():
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

    assert result.kind == "envelope"
    assert result.envelope_mode == "magnitude"
    assert result.display_label == "V(x)"
    assert len(result.series) == 1
    assert len(result.source_series) == 2
    assert result.source_labels == ("V_A(x)", "V_B(x)")

    left_sources = [s.y_values[0].to("kN").magnitude for s in result.source_series]
    right_sources = [s.y_values[-1].to("kN").magnitude for s in result.source_series]
    assert left_sources == pytest.approx([6.0, -2.0])
    assert right_sources == pytest.approx([-2.0, 8.0])

    envelope_values = [q.to("kN").magnitude for q in result.series[0].y_values]
    assert envelope_values[0] == pytest.approx(6.0)
    assert envelope_values[-1] == pytest.approx(8.0)
    assert min(envelope_values) >= 0.0
    assert result.governing_max[0] == 0
    assert result.governing_max[-1] == 1
    assert result.governing_min is None
    assert result.governing_signed[0].to("kN").magnitude == pytest.approx(6.0)
    assert result.governing_signed[-1].to("kN").magnitude == pytest.approx(8.0)
```

Add a sign-retention case where the governing magnitude is negative:

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

Add mixed-mode rejection:

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

- [ ] **Step 2: Run focused engine tests and verify RED**

Run:

```bash
pytest -q tests/test_envelope_engine.py -k "magnitude or absolute"
```

Expected: new tests fail because `envelope(...)` still treats `Abs` responses as a normal signed envelope.

- [ ] **Step 3: Generalize `_resolve_response_series()` for envelope mode**

Before sampling, build `_ResolvedExpression` metadata for every source node and determine:

```python
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

- sample `signed_expression` into `source_series`;
- sample `comparison_expression` into `series`;
- normalize both sets to the same first-source unit;
- derive common `display_label` from signed `source_label` values.

For signed mode and normal plot, `series` and sampled source values are identical.

- [ ] **Step 4: Split envelope reduction into signed and magnitude helpers**

Keep `_evaluate_envelope()` small:

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

The magnitude reducer should compare already-normalized absolute series pointwise:

```python
for sample_index in range(len(resolved.x_values)):
    magnitudes = [
        float(item.y_values[sample_index].magnitude)
        for item in resolved.series
    ]
    governing_index = max(range(len(magnitudes)), key=magnitudes.__getitem__)
    governing_indices.append(governing_index)
    magnitude_values.append(
        resolved.series[governing_index].y_values[sample_index]
    )
    governing_signed.append(
        resolved.source_series[governing_index].y_values[sample_index]
    )
```

Use one displayed `PlotSeries` whose label is generated by a helper. For common `V(x)`, use:

```python
"|V|_max(x)"
```

For `Comparison`, use:

```python
"|response|_max"
```

- [ ] **Step 5: Preserve signed-envelope 0.5.0 behavior explicitly**

Set `envelope_mode="signed"` on signed envelope results but leave:

- two displayed series;
- `governing_max` and `governing_min` values;
- source series;
- labels;
- moment classification

unchanged.

Update existing tests only where they should additionally assert:

```python
assert result.envelope_mode == "signed"
```

Do not change their numerical expectations.

- [ ] **Step 6: Run engine regression gate and commit**

Run:

```bash
pytest -q tests/test_envelope_engine.py tests/test_plot_engine.py
pytest -q
```

Expected: all tests pass.

Commit:

```bash
git add src/engcalc_colab/engine.py tests/test_envelope_engine.py
git commit -m "feat: add composable magnitude envelopes"
```

---

### Task 4: Complete magnitude sweep, units, and non-mutation semantics

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Test: `tests/test_envelope_engine.py`

**Interfaces:**
- Existing sweep grammar remains `envelope(expression, variable, start, end, parameter=[...])`.
- For magnitude mode, one outermost `abs(...)` expression expands to two or more signed source sweep series and parallel absolute comparison series.
- Sweep case labels remain `parameter = value unit`.

- [ ] **Step 1: Add sweep RED tests**

Append to `tests/test_envelope_engine.py`:

```python
def test_magnitude_envelope_parameter_sweep_keeps_signed_cases_and_abs_governing_curve():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*(L/2-x)\nL := 4*m")
    result = eval_cell(
        engine,
        "envelope(abs(V(x)), x, 0, L, q=[2*kN/m, 4*kN/m, -5*kN/m])",
    )[-1]

    assert result.envelope_mode == "magnitude"
    assert len(result.source_series) == 3
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

Add non-mutation:

```python
def test_magnitude_sweep_does_not_mutate_parameter_or_plotting_variable():
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

Add compatible-unit normalization:

```python
def test_magnitude_envelope_normalizes_compatible_source_units_before_abs_comparison():
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

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
pytest -q tests/test_envelope_engine.py -k "magnitude and (sweep or units or mutate or normalizes)"
```

Expected: failures expose any remaining one-series-only or signed-source sweep gaps.

- [ ] **Step 3: Generalize sweep sampling once, not with duplicate state logic**

Change `_evaluate_response_sweep()` to accept both symbolic forms:

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

For every sweep value, call `sample_symbolic()` with the same override once for signed values and, only when `preserve_signed_source` is true, once for absolute comparison values. When comparison and signed expressions are identical, reuse the sampled tuple rather than evaluating twice.

Normalize both output sets through the existing dimensional normalization path. Preserve the current errors for plotting-variable sweep, absent parameter, and incompatible sweep values.

- [ ] **Step 4: Run all envelope and numeric gates**

Run:

```bash
pytest -q tests/test_envelope_engine.py tests/test_numeric_context.py
pytest -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit Task 4**

```bash
git add src/engcalc_colab/engine.py tests/test_envelope_engine.py
git commit -m "test: harden magnitude envelope sweeps"
```

---

### Task 5: Move characteristic panels inside the axes with deterministic auto-placement

**Files:**
- Modify: `src/engcalc_colab/plotting.py`
- Test: `tests/test_plotting.py`
- Test: `tests/test_envelope_plotting.py`

**Interfaces:**
- Adds private corner constants and helpers:

```python
_PANEL_CORNERS = (
    "upper right",
    "upper left",
    "lower right",
    "lower left",
)

def _panel_footprint(text: str) -> tuple[float, float]: ...
def _choose_panel_corner(axis, data_xy, text: str, *, legend_corner: str | None) -> str: ...
def _add_characteristic_panel(axis, text: str, data_xy, *, legend_corner: str | None = None): ...
```

- Panel is created through `axis.text(..., transform=axis.transAxes, ...)`.
- No `figure.text(...)` is used by multi-series or envelope renderers after this task.
- `figure.tight_layout()` uses the full figure; no `rect=(0, 0, 0.73, 1)` reserve.

- [ ] **Step 1: Replace old outside-panel expectations with RED in-axes assertions**

Update `tests/test_plotting.py` by replacing `test_multiseries_moves_characteristic_values_outside_data_area` with:

```python
def test_multiseries_characteristic_panel_is_inside_axes_not_figure_margin():
    figure = render_plot(sweep_moment_plot_result())
    axis = figure.axes[0]

    assert len(figure.texts) == 0
    panel = [text for text in axis.texts if "Characteristic values" in text.get_text()]
    assert len(panel) == 1
    x, y = panel[0].get_position()
    assert 0.0 <= x <= 1.0
    assert 0.0 <= y <= 1.0
    assert panel[0].get_transform() == axis.transAxes
```

Update `tests/test_envelope_plotting.py` by replacing the outside-data-area test with:

```python
def test_envelope_characteristic_panel_is_inside_axes():
    figure = render_plot(moment_envelope_result())
    axis = figure.axes[0]
    assert len(figure.texts) == 0
    panel = [
        text for text in axis.texts
        if "Envelope characteristic values" in text.get_text()
    ]
    assert len(panel) == 1
    assert "max = 36.00 kN·m" in panel[0].get_text()
    assert "min = -18.00 kN·m" in panel[0].get_text()
    assert panel[0].get_transform() == axis.transAxes
```

- [ ] **Step 2: Add RED tests for changing corners based on data occupancy**

In `tests/test_plotting.py`, import the private chooser for focused deterministic testing:

```python
from engcalc_colab.plotting import _choose_panel_corner
```

Add:

```python
def test_panel_chooser_changes_corner_when_upper_right_is_occupied():
    import matplotlib.pyplot as plt

    fig, axis = plt.subplots()
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 10)
    upper_right_data = [(8.5, 8.5), (9.0, 9.0), (9.5, 9.5)] * 20
    corner = _choose_panel_corner(
        axis,
        upper_right_data,
        "Characteristic values\nmax = 10\nmin = 0",
        legend_corner=None,
    )
    plt.close(fig)
    assert corner != "upper right"


def test_panel_chooser_penalizes_known_legend_corner():
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

- [ ] **Step 3: Run plotting tests and verify RED**

Run:

```bash
pytest -q tests/test_plotting.py tests/test_envelope_plotting.py
```

Expected: failures because panels still live in `figure.text` and chooser does not exist.

- [ ] **Step 4: Implement deterministic panel footprint and corner scoring**

In `plotting.py`, add:

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

Add a helper that maps a data point to axes fractions using current limits, including inverted axes:

```python
def _data_to_axes_fraction(axis, x: float, y: float) -> tuple[float, float]:
    x0, x1 = axis.get_xlim()
    y0, y1 = axis.get_ylim()
    x_fraction = 0.5 if x1 == x0 else (x - x0) / (x1 - x0)
    y_fraction = 0.5 if y1 == y0 else (y - y0) / (y1 - y0)
    return x_fraction, y_fraction
```

Build candidate rectangles from the footprint with 0.02 axes padding. Score:

- `3` points for each sample inside the candidate rectangle;
- `1` point for each sample inside a 0.04-expanded neighborhood;
- `1000` penalty if candidate equals the known legend corner;
- tie-break by `_PANEL_CORNERS` order.

Do not rely on browser dimensions or OCR.

- [ ] **Step 5: Implement axes-owned panel creation**

Map corner to axes anchor/alignment:

```python
anchors = {
    "upper right": (0.98, 0.98, "right", "top"),
    "upper left": (0.02, 0.98, "left", "top"),
    "lower right": (0.98, 0.02, "right", "bottom"),
    "lower left": (0.02, 0.02, "left", "bottom"),
}
```

Create the text with:

```python
axis.text(
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

- [ ] **Step 6: Wire helper into multi-series and signed envelope renderers**

For each renderer:

1. collect `(x, y)` pairs from all visible response curves (exclude the zero line);
2. use a deterministic legend corner, initially `"upper right"`, via `axis.legend(loc="upper right", ...)`;
3. call `_add_characteristic_panel(..., legend_corner="upper right")`;
4. replace `figure.tight_layout(rect=(0.0, 0.0, 0.73, 1.0))` with `figure.tight_layout()`.

Single-series `_render_single_series()` remains untouched.

- [ ] **Step 7: Run plotting regression gate and commit**

Run:

```bash
pytest -q tests/test_plotting.py tests/test_envelope_plotting.py
pytest -q
```

Expected: panels are axes-owned, automatic corner tests pass, no right-side margin is reserved, single-series tests remain unchanged.

Commit:

```bash
git add src/engcalc_colab/plotting.py tests/test_plotting.py tests/test_envelope_plotting.py
git commit -m "fix: place characteristic panels inside plots"
```

---

### Task 6: Render magnitude envelopes with signed context and governing information

**Files:**
- Modify: `src/engcalc_colab/plotting.py`
- Test: `tests/test_envelope_plotting.py`

**Interfaces:**
- `_render_envelope()` dispatches internally on `result.envelope_mode`.
- Signed mode keeps two emphasized branches and fill between them.
- Magnitude mode renders one emphasized nonnegative branch and fill from zero to it.
- Faint `result.source_series` remain signed in both modes.
- Magnitude panel includes global maximum magnitude, x-location, governing signed value, and governing source label.

- [ ] **Step 1: Add magnitude-result fixture and RED visual tests**

Append to `tests/test_envelope_plotting.py`:

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

Add:

```python
def test_magnitude_envelope_renders_signed_source_curves_but_one_nonnegative_boundary():
    axis = render_plot(shear_magnitude_envelope_result()).axes[0]
    faint_lines = [
        line for line in axis.lines
        if line.get_label() == "_nolegend_"
    ]
    assert len(faint_lines) == 2
    assert any(min(line.get_ydata()) < 0 for line in faint_lines)

    boundary = [
        line for line in axis.lines
        if line.get_label() == "|V|_max(x)"
    ]
    assert len(boundary) == 1
    assert min(boundary[0].get_ydata()) >= 0.0
```

Add fill and legend assertions:

```python
def test_magnitude_envelope_fills_from_zero_and_legend_has_only_abs_max():
    axis = render_plot(shear_magnitude_envelope_result()).axes[0]
    fills = [
        collection for collection in axis.collections
        if isinstance(collection, PolyCollection)
    ]
    assert len(fills) == 1
    legend = axis.get_legend()
    assert legend is not None
    assert [text.get_text() for text in legend.get_texts()] == ["|V|_max(x)"]
```

Add panel content:

```python
def test_magnitude_envelope_panel_reports_governing_signed_value_and_case_inside_axes():
    figure = render_plot(shear_magnitude_envelope_result())
    axis = figure.axes[0]
    panel = [
        text for text in axis.texts
        if "Magnitude envelope" in text.get_text()
    ]
    assert len(panel) == 1
    text = panel[0].get_text()
    assert "|max| = 9.00 kN" in text
    assert "signed = -9.00 kN" in text
    assert "V_uso(x)" in text
    assert panel[0].get_transform() == axis.transAxes
```

- [ ] **Step 2: Run magnitude plotting tests and verify RED**

Run:

```bash
pytest -q tests/test_envelope_plotting.py -k "magnitude"
```

Expected: fail because current renderer destructures exactly two envelope series.

- [ ] **Step 3: Add magnitude characteristic panel formatter**

Implement:

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

- [ ] **Step 4: Split signed and magnitude rendering paths without duplicating source rendering**

Refactor `_render_envelope()` so shared setup renders signed faint source curves and zero line once, then:

```python
if result.envelope_mode == "magnitude":
    _render_magnitude_envelope_body(figure, axis, result, x_values)
else:
    _render_signed_envelope_body(figure, axis, result, x_values)
```

Magnitude body:

- one line `linewidth=2.5`, `zorder=4`;
- `axis.fill_between(x_values, 0.0, magnitude_y, alpha=0.10, zorder=2)`;
- legend contains only magnitude line;
- use common signed response family for y-axis label;
- title `|V(x)| envelope` when display label is `V(x)`;
- preserve moment inversion when `series[0].is_moment` is true;
- feed all signed-source and magnitude points into `_add_characteristic_panel()`.

- [ ] **Step 5: Verify signed-envelope rendering is unchanged except panel placement**

Run:

```bash
pytest -q tests/test_envelope_plotting.py
```

Expected: signed tests and magnitude tests all pass.

- [ ] **Step 6: Run full plotting/engine gate and commit**

Run:

```bash
pytest -q tests/test_envelope_engine.py tests/test_envelope_plotting.py tests/test_plotting.py
pytest -q
```

Expected: all tests pass.

Commit:

```bash
git add src/engcalc_colab/plotting.py tests/test_envelope_plotting.py
git commit -m "feat: render magnitude envelope design demand"
```

---

### Task 7: End-to-end integration, documentation, version 0.6.0, and clean-wheel release gate

**Files:**
- Modify: `tests/test_acceptance_native_plot.py`
- Modify: `tests/test_magic.py`
- Modify: `tests/test_packaging.py`
- Modify: `tests/test_parser.py`
- Modify: `README.md`
- Modify: `src/engcalc_colab/__init__.py`
- Modify: `pyproject.toml`
- Temporary validation workflow during execution only: `.github/workflows/engcalc-v060-validation.yml`

**Interfaces:**
- Public package/runtime version: `0.6.0`.
- No runtime dependency additions.
- Clean wheel filename: `engcalc_colab-0.6.0-py3-none-any.whl`.

- [ ] **Step 1: Add end-to-end acceptance RED test**

Append to `tests/test_acceptance_native_plot.py`:

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

If `tests/test_acceptance_native_plot.py` does not already import `PlotResult` and `render_plot`, add those exact imports.

- [ ] **Step 2: Add or update source-order magic test**

In `tests/test_magic.py`, add a cell containing a symbolic output before and after the magnitude envelope and assert the emitted display object order remains:

```text
Math -> Figure -> Math
```

Reuse the existing display-capture helper in that file; do not create a second IPython harness.

- [ ] **Step 3: Run integration tests before version bump**

Run:

```bash
pytest -q tests/test_acceptance_native_plot.py tests/test_magic.py
```

Expected: functional integration tests pass if Tasks 1-6 are complete.

- [ ] **Step 4: Introduce release-version RED tests**

Update `tests/test_packaging.py`:

```python
def test_pyproject_version_is_0_6_0():
    assert _project_metadata()["version"] == "0.6.0"


def test_runtime_version_is_0_6_0():
    assert engcalc_colab.__version__ == "0.6.0"
```

Update `tests/test_parser.py::test_package_version_and_statement_model` to expect:

```python
assert __version__ == "0.6.0"
```

Run:

```bash
pytest -q tests/test_packaging.py tests/test_parser.py
```

Expected: exactly the version assertions fail while all other tests pass.

- [ ] **Step 5: Bump package/runtime version without changing dependencies**

In `pyproject.toml`:

```toml
version = "0.6.0"
```

In `src/engcalc_colab/__init__.py`:

```python
__version__ = "0.6.0"
```

Do not alter `sympy`, `pint`, or `matplotlib` dependency floors.

- [ ] **Step 6: Update README public documentation**

Add a `v0.6.0` section above the 0.5.0 envelope section with these canonical examples:

```text
%%eng

V_constr(x) = 6*kN - 4*kN/m*x
V_uso(x) = -9*kN + 1*kN/m*x
L := 2*m

envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)
```

and:

```text
%%eng

V(x) = q*(L/2-x)
L := 4*m

envelope(abs(V(x)), x, 0, L, q=[2*tonf/m, 3*tonf/m, 4*tonf/m])
```

Document explicitly:

- `abs(...)` is a safe EngCalc mathematical operation;
- normal `envelope(...)` remains signed algebraic max/min;
- all-outermost-`abs(...)` envelope means maximum magnitude;
- faint context curves preserve signed response;
- mixed signed/absolute sources are rejected;
- characteristic panels now auto-place inside the graph;
- no `abs_envelope(...)` command exists.

- [ ] **Step 7: Run source full suite**

Run:

```bash
pytest -q
```

Expected: full suite passes.

Record the exact test count in the eventual PR body; do not hard-code a predicted count in release claims.

- [ ] **Step 8: Build the real 0.6.0 wheel**

Run:

```bash
rm -rf build dist
python -m build --wheel
ls -l dist/engcalc_colab-0.6.0-py3-none-any.whl
```

Expected: wheel exists with version 0.6.0.

- [ ] **Step 9: Install wheel in a clean environment**

Run:

```bash
python -m venv /tmp/engcalc-v060-wheel
/tmp/engcalc-v060-wheel/bin/python -m pip install --upgrade pip
/tmp/engcalc-v060-wheel/bin/python -m pip install dist/engcalc_colab-0.6.0-py3-none-any.whl pytest ipython
```

Expected: installation succeeds without pulling any new EngCalc runtime dependency beyond those already declared.

- [ ] **Step 10: Run installed-wheel smoke test outside the source tree**

From `/tmp` run:

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

Expected output:

```text
EngCalc 0.6.0 installed-wheel smoke PASS
```

- [ ] **Step 11: Run full suite against installed wheel from outside repository source**

Run:

```bash
cd /tmp
PYTHONPATH= /tmp/engcalc-v060-wheel/bin/python -m pytest -q -c /dev/null "$GITHUB_WORKSPACE/tests"
```

When executing outside GitHub Actions, replace `$GITHUB_WORKSPACE/tests` with the absolute repository test directory. Expected: same full suite passes against the installed wheel.

- [ ] **Step 12: Repeat source full suite after wheel validation**

Return to repository root and run:

```bash
pytest -q
```

Expected: full suite passes again.

- [ ] **Step 13: Remove temporary release-validation workflow if one was used**

If execution created `.github/workflows/engcalc-v060-validation.yml` solely to obtain CI evidence, delete it after the final successful gate and verify the cleanup commit changes only that temporary workflow.

- [ ] **Step 14: Final diff review and commit release changes**

Review:

```bash
git diff main...HEAD --stat
git diff main...HEAD -- src/engcalc_colab/parser.py src/engcalc_colab/numeric.py src/engcalc_colab/engine.py src/engcalc_colab/models.py src/engcalc_colab/plotting.py
```

Confirm:

- no `abs_envelope`/`envelope_abs` public API exists;
- no arbitrary Python function execution was enabled;
- signed envelope math did not change;
- single-series plotting did not change;
- no external right panel remains in multi-series/envelope rendering;
- no new runtime dependency was added.

Commit remaining release files:

```bash
git add README.md pyproject.toml src/engcalc_colab/__init__.py tests/test_acceptance_native_plot.py tests/test_magic.py tests/test_packaging.py tests/test_parser.py
git commit -m "release: prepare EngCalc 0.6.0"
```

---

## Final Acceptance Checklist

Before opening a PR, all of the following must be true:

- [ ] `abs(expression)` works symbolically.
- [ ] Numeric `abs(...)` preserves Pint units.
- [ ] `plot(abs(V(x)), ...)` works without losing structural family classification.
- [ ] Existing signed envelope returns algebraic max/min exactly as 0.5.0.
- [ ] `envelope(abs(V1(x)), abs(V2(x)), ...)` returns one maximum-magnitude branch.
- [ ] Magnitude envelope source curves retain original signs.
- [ ] Magnitude envelope stores governing source indices and signed governing quantities.
- [ ] Mixed absolute/signed envelope sources are rejected.
- [ ] Magnitude sweep works with compatible units and does not mutate stored state.
- [ ] Multi-series characteristic panel is inside axes.
- [ ] Signed-envelope characteristic panel is inside axes.
- [ ] Magnitude-envelope characteristic panel is inside axes.
- [ ] Automatic panel placement responds to data occupancy and legend conflict.
- [ ] No fixed ~27% right-hand panel margin remains.
- [ ] Single-series extrema callouts are unchanged.
- [ ] Moment-positive-down convention remains unchanged.
- [ ] Full source suite is green.
- [ ] Real 0.6.0 wheel builds.
- [ ] Clean-environment wheel installation succeeds.
- [ ] Installed-wheel smoke test passes.
- [ ] Full suite is green against installed wheel outside source tree.
- [ ] README documents the final syntax and semantics.
- [ ] Temporary validation workflow is absent from the final product diff.
