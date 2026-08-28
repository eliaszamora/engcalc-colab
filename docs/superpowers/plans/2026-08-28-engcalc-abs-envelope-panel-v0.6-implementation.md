# EngCalc 0.6.0 Absolute-Value Envelope and In-Axes Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe general `abs(expression)`, make `envelope(abs(response), ...)` produce a maximum-magnitude structural envelope while retaining signed source responses, and move multi-series/envelope characteristic panels inside the axes with deterministic automatic corner placement.

**Architecture:** Keep the EngCalc 0.5.0 shared response-series pipeline. Capture outer `abs` syntax before symbolic expansion, carry both signed and comparison expressions through one resolver, and extend `PlotResult` only with envelope mode plus governing signed quantities. Keep rendering in `plotting.py`; share one in-axes panel-placement helper between multi-series plots, signed envelopes, and magnitude envelopes.

**Tech Stack:** Python 3.10+, SymPy, Pint, Matplotlib, IPython/Jupyter, pytest.

**Spec:** `docs/superpowers/specs/2026-08-28-engcalc-abs-envelope-panel-v0.6-design.md`

## Global Constraints

- Base: EngCalc 0.5.0 `main` commit `01fe42376f61e7d0d3738049f01935368e2c2e16`.
- `abs(expression)` is the only new public mathematical operation.
- No arbitrary Python function dispatch.
- Signed `envelope` remains algebraic pointwise max/min on 201 samples.
- Magnitude mode requires every envelope source to be syntactically outermost `abs`.
- Mixed signed/absolute envelope sources fail.
- Magnitude envelope displays one nonnegative max-magnitude branch.
- Faint magnitude-envelope source curves preserve sign.
- Governing source index and signed governing Pint quantity are retained per sample.
- Existing one-parameter sweep grammar, units, and non-mutation rules remain.
- Moment-positive-down remains.
- Multi-series and envelope characteristic panels are axes-owned; no fixed right margin.
- Candidate panel corners: upper right, upper left, lower right, lower left.
- Panel chooser scores plotted-data occupancy and penalizes the legend corner.
- Single-series renderer remains unchanged.
- No `abs_envelope`, `envelope_abs`, mode keyword, named cases, adaptive sampling, crossover solver, or new dependency.
- Release version: `0.6.0`.

---

## File Map

- `src/engcalc_colab/parser.py`: reserve `abs`; keep keyword/list restrictions.
- `src/engcalc_colab/engine.py`: symbolic `abs`; expression metadata; magnitude reduction; signed governing metadata.
- `src/engcalc_colab/numeric.py`: Pint-safe numeric `abs` and SymPy `Abs`.
- `src/engcalc_colab/models.py`: `envelope_mode`, `governing_signed`.
- `src/engcalc_colab/plotting.py`: in-axes panel chooser and magnitude renderer.
- `src/engcalc_colab/__init__.py`, `pyproject.toml`, `README.md`: release metadata/docs.
- Tests: `test_parser.py`, `test_engine.py`, `test_numeric_context.py`, `test_plot_engine.py`, `test_envelope_engine.py`, `test_plotting.py`, `test_envelope_plotting.py`, `test_acceptance_native_plot.py`, `test_magic.py`, `test_packaging.py`.

---

### Task 1: Safe general `abs(expression)`

**Files:** parser, engine, numeric context and their focused tests.

**Produces:**
- symbolic `abs(x)` -> `sp.Abs(x)`;
- numeric `abs(-3*tonf)` -> `3 tonf`;
- `numeric(abs(P))` works;
- zero/multi-argument calls fail; keyword calls remain forbidden.

- [ ] **Step 1: Add parser tests**

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

- [ ] **Step 2: Add engine tests**

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

- [ ] **Step 3: Run RED gate**

```bash
pytest -q tests/test_parser.py tests/test_engine.py
```

Expected: reservation/symbolic/arity/numeric-engine requirements are not all satisfied; previous tests remain green.

- [ ] **Step 4: Implement parser reservation and symbolic evaluator**

In `parser.py` include `"abs"` in `_ALLOWED_CALLS`; do not include it in `_DISPLAY_SWEEP_CALLS`.

In `engine.py` after user-function dispatch:

```python
if name == "abs":
    self._require_arity(name, args, 1, "expression")
    return sp.Abs(args[0])
```

- [ ] **Step 5: Add NumericContext tests**

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

```bash
pytest -q tests/test_numeric_context.py
```

- [ ] **Step 7: Implement restricted numeric absolute value**

In `NumericContext._evaluate_sympy()`:

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

- [ ] **Step 8: Verify GREEN and commit**

```bash
pytest -q tests/test_parser.py tests/test_engine.py tests/test_numeric_context.py
pytest -q
git add src/engcalc_colab/parser.py src/engcalc_colab/engine.py src/engcalc_colab/numeric.py tests/test_parser.py tests/test_engine.py tests/test_numeric_context.py
git commit -m "feat: add safe EngCalc absolute value"
```

---

### Task 2: Backward-compatible transport and response metadata

**Files:** `models.py`, `engine.py`, `test_envelope_engine.py`, `test_plot_engine.py`.

**Produces exact transport fields:**

```python
# PlotResult and _PlotEvaluation additions
envelope_mode: str | None = None
governing_signed: tuple[Any, ...] | None = None
```

**Produces exact private dataclasses:**

```python
@dataclass(frozen=True)
class _ResolvedExpression:
    source_label: str
    display_label: str
    signed_expression: object
    comparison_expression: object
    is_absolute: bool


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

- [ ] **Step 1: Add transport RED tests**

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
    result = PlotResult(
        statement,
        "V(x)",
        "x",
        (0, 1),
        (PlotSeries("|V|_max(x)", (3, 4), False),),
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

- [ ] **Step 2: Verify RED and add fields**

```bash
pytest -q tests/test_envelope_engine.py -k "transport"
```

Add fields to `PlotResult`, `_PlotEvaluation`, and `EngineeringEngine.evaluate()` pass-through.

- [ ] **Step 3: Add `plot(abs(response))` tests**

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

- [ ] **Step 4: Implement expression resolver**

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
        source_label = self._plot_expression_label(signed_node, variable, signed_expression)
        display_label = f"|{source_label}|"
    else:
        signed_expression = self.visit(node)
        comparison_expression = signed_expression
        source_label = self._plot_expression_label(node, variable, signed_expression)
        display_label = source_label
    return _ResolvedExpression(
        source_label=source_label,
        display_label=display_label,
        signed_expression=signed_expression,
        comparison_expression=comparison_expression,
        is_absolute=is_absolute,
    )
```

Ordinary `plot` samples `comparison_expression`; `is_moment` derives from `source_label`.

- [ ] **Step 5: Verify plot regression and commit**

```bash
pytest -q tests/test_plot_engine.py tests/test_plot_parser.py tests/test_plotting.py
pytest -q
git add src/engcalc_colab/models.py src/engcalc_colab/engine.py tests/test_envelope_engine.py tests/test_plot_engine.py
git commit -m "refactor: preserve response expression metadata"
```

---

### Task 3: Multi-expression magnitude envelope

**Files:** `engine.py`, `test_envelope_engine.py`.

**Contract:**
- signed mode: two displayed branches, existing max/min metadata;
- magnitude mode: one displayed branch, signed source series, `governing_max`, `governing_min=None`, `governing_signed`.

- [ ] **Step 1: Add RED tests**

```python
def test_magnitude_envelope_keeps_signed_sources_and_one_abs_max_branch():
    engine = EngineeringEngine()
    eval_cell(engine, "V_A(x) = 6*kN - 4*kN/m*x\nV_B(x) = -2*kN + 5*kN/m*x\nL := 2*m")
    result = eval_cell(engine, "envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)")[-1]
    assert result.envelope_mode == "magnitude"
    assert result.display_label == "V(x)"
    assert len(result.series) == 1
    assert result.source_labels == ("V_A(x)", "V_B(x)")
    assert [s.y_values[0].to("kN").magnitude for s in result.source_series] == pytest.approx([6.0, -2.0])
    assert [s.y_values[-1].to("kN").magnitude for s in result.source_series] == pytest.approx([-2.0, 8.0])
    assert result.series[0].y_values[0].to("kN").magnitude == pytest.approx(6.0)
    assert result.series[0].y_values[-1].to("kN").magnitude == pytest.approx(8.0)
    assert result.governing_max == tuple(result.governing_max)
    assert result.governing_min is None
```

```python
def test_magnitude_envelope_retains_negative_signed_governing_value():
    engine = EngineeringEngine()
    eval_cell(engine, "V_A(x) = -9*kN + 1*kN/m*x\nV_B(x) = 3*kN - 1*kN/m*x\nL := 2*m")
    result = eval_cell(engine, "envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)")[-1]
    assert result.series[0].y_values[0].to("kN").magnitude == pytest.approx(9.0)
    assert result.governing_signed[0].to("kN").magnitude == pytest.approx(-9.0)
    assert result.governing_max[0] == 0
```

```python
def test_envelope_rejects_mixed_absolute_and_signed_sources():
    engine = EngineeringEngine()
    eval_cell(engine, "V_A(x) = x\nV_B(x) = -x\nL := 2")
    with pytest.raises(EngEvaluationError, match="envelope cannot mix absolute and signed response series"):
        eval_cell(engine, "envelope(abs(V_A(x)), V_B(x), x, 0, L)")
```

- [ ] **Step 2: Run RED gate**

```bash
pytest -q tests/test_envelope_engine.py -k "magnitude or mixed_absolute"
```

- [ ] **Step 3: Detect mode in shared resolver**

```python
resolved_expressions = [self._resolve_response_expression(node, variable) for node in expression_nodes]
absolute_flags = {item.is_absolute for item in resolved_expressions}
if call_name == "envelope" and len(absolute_flags) > 1:
    raise EngEvaluationError("envelope cannot mix absolute and signed response series")

envelope_mode = None
if call_name == "envelope":
    envelope_mode = "magnitude" if True in absolute_flags else "signed"
```

Magnitude mode samples comparison expressions into `series`, signed expressions into `source_series`, and computes common display family from signed labels.

- [ ] **Step 4: Split reduction helpers**

```python
resolved = self._resolve_response_series(node, call_name="envelope")
if len(resolved.series) < 2:
    raise EngEvaluationError("envelope requires at least two response series")
self.plot_evaluation = (
    self._build_magnitude_envelope(resolved)
    if resolved.envelope_mode == "magnitude"
    else self._build_signed_envelope(resolved)
)
return resolved.first_symbolic_expression
```

Magnitude pointwise reduction:

```python
magnitude_values = []
governing_indices = []
governing_signed = []
for sample_index in range(len(resolved.x_values)):
    values = [float(item.y_values[sample_index].magnitude) for item in resolved.series]
    index = max(range(len(values)), key=values.__getitem__)
    governing_indices.append(index)
    magnitude_values.append(resolved.series[index].y_values[sample_index])
    governing_signed.append(resolved.source_series[index].y_values[sample_index])
```

Label helper:

```python
def _magnitude_envelope_series_label(display_label: str, variable: str) -> str:
    suffix = f"({variable})"
    if display_label != "Comparison" and display_label.endswith(suffix):
        family = display_label[:-len(suffix)]
        return f"|{family}|_max({variable})"
    return "|response|_max"
```

Set signed envelopes to `envelope_mode="signed"` without changing their values.

- [ ] **Step 5: Verify and commit**

```bash
pytest -q tests/test_envelope_engine.py tests/test_plot_engine.py
pytest -q
git add src/engcalc_colab/engine.py tests/test_envelope_engine.py
git commit -m "feat: add composable magnitude envelopes"
```

---

### Task 4: Magnitude sweep, units, and state

**Files:** `engine.py`, `test_envelope_engine.py`.

**Sweep helper signature:**

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

- [ ] **Step 1: Add RED tests**

```python
def test_magnitude_sweep_keeps_signed_cases_and_abs_governing_curve():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*(L/2-x)\nL := 4*m")
    result = eval_cell(engine, "envelope(abs(V(x)), x, 0, L, q=[2*kN/m, 4*kN/m, -5*kN/m])")[-1]
    assert result.source_labels == ("q = 2 kN/m", "q = 4 kN/m", "q = -5 kN/m")
    assert result.source_series[2].y_values[0].to("kN").magnitude == pytest.approx(-10.0)
    assert result.series[0].y_values[0].to("kN").magnitude == pytest.approx(10.0)
    assert result.governing_max[0] == 2
    assert result.governing_signed[0].to("kN").magnitude == pytest.approx(-10.0)
```

```python
def test_magnitude_sweep_does_not_mutate_parameter_or_x():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = q*(L/2-x)\nq := 2.8*tonf/m\nL := 4*m\nx := 1*m")
    eval_cell(engine, "envelope(abs(V(x)), x, 0, L, q=[2*kN/m, 4*kN/m])")
    assert engine.numeric_context.get("q").to("tonf/m").magnitude == pytest.approx(2.8)
    assert engine.numeric_context.get("x").to("m").magnitude == pytest.approx(1.0)
```

```python
def test_magnitude_envelope_normalizes_compatible_units_before_comparison():
    engine = EngineeringEngine()
    eval_cell(engine, "V_A(x) = -q_A*x\nV_B(x) = q_B*x\nq_A := 1*kN/m\nq_B := 1500*N/m\nL := 2*m")
    result = eval_cell(engine, "envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)")[-1]
    assert result.series[0].y_values[-1].to("kN").magnitude == pytest.approx(3.0)
    assert result.governing_signed[-1].to("kN").magnitude == pytest.approx(3.0)
```

- [ ] **Step 2: Run RED gate**

```bash
pytest -q tests/test_envelope_engine.py -k "magnitude and (sweep or mutate or normalizes)"
```

- [ ] **Step 3: Implement shared sweep sampling**

For each sweep value:
1. sample `comparison_expression` with current local override;
2. if `preserve_signed_source` and expressions differ, sample `signed_expression` with the same override;
3. otherwise reuse comparison values as source values;
4. label both with the same `parameter = value unit` string;
5. normalize both sets to the first comparison-series unit.

Retain current plotting-variable, absent-parameter, incompatible-sweep-unit, and non-mutation errors.

- [ ] **Step 4: Verify and commit**

```bash
pytest -q tests/test_envelope_engine.py tests/test_numeric_context.py
pytest -q
git add src/engcalc_colab/engine.py tests/test_envelope_engine.py
git commit -m "test: harden magnitude envelope sweeps"
```

---

### Task 5: In-axes panel auto-placement

**Files:** `plotting.py`, `test_plotting.py`, `test_envelope_plotting.py`.

**Private interfaces:**
- `_panel_footprint(text: str) -> tuple[float, float]`
- `_data_to_axes_fraction(axis, x: float, y: float) -> tuple[float, float]`
- `_choose_panel_corner(axis, data_xy: list[tuple[float, float]], text: str, legend_corner: str | None) -> str`
- `_add_characteristic_panel(axis, text: str, data_xy: list[tuple[float, float]], legend_corner: str | None = None)`

- [ ] **Step 1: Replace external-panel tests**

```python
def test_multiseries_characteristic_panel_is_inside_axes():
    figure = render_plot(sweep_moment_plot_result())
    axis = figure.axes[0]
    assert len(figure.texts) == 0
    panels = [text for text in axis.texts if "Characteristic values" in text.get_text()]
    assert len(panels) == 1
    assert panels[0].get_transform() == axis.transAxes
```

```python
def test_signed_envelope_characteristic_panel_is_inside_axes():
    figure = render_plot(moment_envelope_result())
    axis = figure.axes[0]
    assert len(figure.texts) == 0
    panels = [text for text in axis.texts if "Envelope characteristic values" in text.get_text()]
    assert len(panels) == 1
    assert "max = 36.00 kN·m" in panels[0].get_text()
    assert "min = -18.00 kN·m" in panels[0].get_text()
    assert panels[0].get_transform() == axis.transAxes
```

- [ ] **Step 2: Add corner-choice tests**

```python
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

- [ ] **Step 3: Add full-bbox-inside-axes test**

```python
def test_characteristic_panel_bbox_stays_inside_axes():
    figure = render_plot(sweep_moment_plot_result())
    axis = figure.axes[0]
    panel = [text for text in axis.texts if "Characteristic values" in text.get_text()][0]
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    panel_box = panel.get_window_extent(renderer=renderer)
    axes_box = axis.get_window_extent(renderer=renderer)
    tolerance = 1.0
    assert panel_box.x0 >= axes_box.x0 - tolerance
    assert panel_box.y0 >= axes_box.y0 - tolerance
    assert panel_box.x1 <= axes_box.x1 + tolerance
    assert panel_box.y1 <= axes_box.y1 + tolerance
```

- [ ] **Step 4: Run RED gate**

```bash
pytest -q tests/test_plotting.py tests/test_envelope_plotting.py
```

- [ ] **Step 5: Implement footprint and coordinate conversion**

```python
_PANEL_CORNERS = ("upper right", "upper left", "lower right", "lower left")


def _panel_footprint(text: str) -> tuple[float, float]:
    lines = text.splitlines() or [""]
    max_chars = max(len(line) for line in lines)
    width = min(0.46, max(0.22, 0.14 + 0.006 * max_chars))
    height = min(0.72, max(0.16, 0.08 + 0.043 * len(lines)))
    return width, height


def _data_to_axes_fraction(axis, x: float, y: float) -> tuple[float, float]:
    x0, x1 = axis.get_xlim()
    y0, y1 = axis.get_ylim()
    return (
        0.5 if x1 == x0 else (x - x0) / (x1 - x0),
        0.5 if y1 == y0 else (y - y0) / (y1 - y0),
    )
```

- [ ] **Step 6: Implement corner scoring**

For each candidate rectangle built from the footprint and 0.02 axes padding:
- +3 for each point inside;
- +1 for each point in the rectangle expanded by 0.04;
- +1000 if candidate equals `legend_corner`;
- choose minimum `(score, _PANEL_CORNERS.index(corner))`.

- [ ] **Step 7: Implement axes-owned panel**

```python
def _add_characteristic_panel(axis, text, data_xy, *, legend_corner=None):
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

- [ ] **Step 8: Wire multi-series and signed envelope renderers**

Collect all visible response `(x, y)` data; use `axis.legend(loc="upper right")`; call panel helper with `legend_corner="upper right"`; remove both `figure.text(...)` calls and both `tight_layout(rect=(0, 0, 0.73, 1))` calls; use `figure.tight_layout()`.

If the bbox test reveals that estimated footprint is too small for a long panel, increase `_panel_footprint` width/height constants only until the bbox remains inside axes; do not reintroduce an external margin.

- [ ] **Step 9: Verify and commit**

```bash
pytest -q tests/test_plotting.py tests/test_envelope_plotting.py
pytest -q
git add src/engcalc_colab/plotting.py tests/test_plotting.py tests/test_envelope_plotting.py
git commit -m "fix: place characteristic panels inside plots"
```

---

### Task 6: Magnitude-envelope renderer

**Files:** `plotting.py`, `test_envelope_plotting.py`.

- [ ] **Step 1: Add magnitude fixture**

```python
def shear_magnitude_envelope_result():
    engine = EngineeringEngine()
    eval_cell(engine, "V_constr(x) = 6*kN - 4*kN/m*x\nV_uso(x) = -9*kN + 1*kN/m*x\nL := 2*m")
    return eval_cell(engine, "envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)")[-1]
```

- [ ] **Step 2: Add visual RED tests**

```python
def test_magnitude_envelope_shows_signed_sources_and_one_nonnegative_boundary():
    axis = render_plot(shear_magnitude_envelope_result()).axes[0]
    faint = [line for line in axis.lines if line.get_label() == "_nolegend_"]
    assert len(faint) == 2
    assert any(min(line.get_ydata()) < 0 for line in faint)
    boundaries = [line for line in axis.lines if line.get_label() == "|V|_max(x)"]
    assert len(boundaries) == 1
    assert min(boundaries[0].get_ydata()) >= 0.0
```

```python
def test_magnitude_envelope_fill_and_legend():
    axis = render_plot(shear_magnitude_envelope_result()).axes[0]
    fills = [item for item in axis.collections if isinstance(item, PolyCollection)]
    assert len(fills) == 1
    assert [text.get_text() for text in axis.get_legend().get_texts()] == ["|V|_max(x)"]
```

```python
def test_magnitude_panel_reports_signed_governing_case_inside_axes():
    figure = render_plot(shear_magnitude_envelope_result())
    axis = figure.axes[0]
    panel = [text for text in axis.texts if "Magnitude envelope" in text.get_text()][0]
    assert "|max| = 9.00 kN" in panel.get_text()
    assert "signed = -9.00 kN" in panel.get_text()
    assert "V_uso(x)" in panel.get_text()
    assert panel.get_transform() == axis.transAxes
```

- [ ] **Step 3: Run RED gate**

```bash
pytest -q tests/test_envelope_plotting.py -k "magnitude"
```

- [ ] **Step 4: Implement magnitude panel formatter**

```python
def _magnitude_envelope_characteristic_panel_text(result: PlotResult) -> str:
    series = result.series[0]
    values = [float(value.magnitude) for value in series.y_values]
    index = max(range(len(values)), key=values.__getitem__)
    governing_index = result.governing_max[index]
    signed_value = result.governing_signed[index]
    return "\n".join([
        "Magnitude envelope",
        f"|max| = {_quantity_label(series.y_values[index], moment=series.is_moment)}    x = {_quantity_label(result.x_values[index])}",
        f"signed = {_quantity_label(signed_value, moment=series.is_moment)}",
        f"governing = {result.source_labels[governing_index]}",
    ])
```

- [ ] **Step 5: Split envelope body rendering**

Shared `_render_envelope()` renders faint signed source curves and zero line, then:

```python
if result.envelope_mode == "magnitude":
    _render_magnitude_envelope_body(figure, axis, result, x_values)
else:
    _render_signed_envelope_body(figure, axis, result, x_values)
```

Magnitude body:
- one line, linewidth 2.5, zorder 4;
- fill `0 -> magnitude_y` with alpha 0.10;
- legend only magnitude line;
- y-axis uses signed common response family/unit;
- title `|V(x)| envelope` for display label `V(x)`;
- moment inversion still follows `series[0].is_moment`;
- panel occupancy uses signed-source and magnitude points.

- [ ] **Step 6: Verify and commit**

```bash
pytest -q tests/test_envelope_plotting.py tests/test_plotting.py
pytest -q
git add src/engcalc_colab/plotting.py tests/test_envelope_plotting.py
git commit -m "feat: render magnitude envelope design demand"
```

---

### Task 7: Integration, docs, version, clean-wheel gate

**Files:** acceptance, magic, packaging/version tests, README, `__init__.py`, `pyproject.toml`; temporary CI workflow only if needed.

- [ ] **Step 1: Add end-to-end acceptance**

```python
def test_native_magnitude_envelope_acceptance():
    engine = EngineeringEngine()
    cell = """
V_constr(x) = 6*kN - 4*kN/m*x
V_uso(x) = -9*kN + 1*kN/m*x
L := 2*m

envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)
"""
    result = [engine.evaluate(stmt) for stmt in parse_cell(cell)][-1]
    assert isinstance(result, PlotResult)
    assert result.envelope_mode == "magnitude"
    assert len(result.series) == 1
    assert len(result.source_series) == 2
    figure = render_plot(result)
    axis = figure.axes[0]
    assert len(figure.texts) == 0
    assert any("Magnitude envelope" in text.get_text() for text in axis.texts)
```

- [ ] **Step 2: Add magic source-order test**

Reuse the existing display-capture harness in `test_magic.py`; create one cell whose displayed outputs are Math, magnitude-envelope Figure, Math and assert exactly that order.

- [ ] **Step 3: Run integration gate**

```bash
pytest -q tests/test_acceptance_native_plot.py tests/test_magic.py
```

- [ ] **Step 4: Introduce version RED**

Update packaging tests and parser version assertion to `0.6.0`, then run:

```bash
pytest -q tests/test_packaging.py tests/test_parser.py
```

Expected: old version metadata is the only failure category.

- [ ] **Step 5: Bump version**

```toml
version = "0.6.0"
```

```python
__version__ = "0.6.0"
```

Do not change dependencies.

- [ ] **Step 6: Update README**

Document these exact examples:

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

State signed envelope unchanged, signed source context retained, mixed mode rejected, panels inside graph, and no `abs_envelope` alias.

- [ ] **Step 7: Source full suite**

```bash
pytest -q
```

Record exact count.

- [ ] **Step 8: Build and install wheel**

```bash
rm -rf build dist
python -m build --wheel
test -f dist/engcalc_colab-0.6.0-py3-none-any.whl
python -m venv /tmp/engcalc-v060-wheel
/tmp/engcalc-v060-wheel/bin/python -m pip install --upgrade pip
/tmp/engcalc-v060-wheel/bin/python -m pip install dist/engcalc_colab-0.6.0-py3-none-any.whl pytest ipython
```

- [ ] **Step 9: Installed-wheel smoke from `/tmp`**

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
assert result.series[0].y_values[0].to("kN").magnitude == 9.0
assert result.governing_signed[0].to("kN").magnitude == -9.0
figure = render_plot(result)
axis = figure.axes[0]
assert len(figure.texts) == 0
assert any("Magnitude envelope" in text.get_text() for text in axis.texts)

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

- [ ] **Step 10: Full suite against installed wheel**

In Actions:

```bash
cd /tmp
PYTHONPATH= /tmp/engcalc-v060-wheel/bin/python -m pytest -q -c /dev/null "$GITHUB_WORKSPACE/tests"
```

Outside Actions use the repository test directory absolute path.

- [ ] **Step 11: Repeat source suite**

```bash
pytest -q
```

- [ ] **Step 12: Remove temporary CI workflow**

If `.github/workflows/engcalc-v060-validation.yml` was created solely for validation, delete it after the successful gate and verify its cleanup commit contains only that deletion.

- [ ] **Step 13: Final diff review**

```bash
git diff main...HEAD --stat
git diff main...HEAD -- src/engcalc_colab/parser.py src/engcalc_colab/numeric.py src/engcalc_colab/engine.py src/engcalc_colab/models.py src/engcalc_colab/plotting.py
```

Confirm no arbitrary function dispatch, no alias envelope API, signed-envelope math unchanged, single-series renderer unchanged, no figure-level characteristic panels in multi/envelope paths, and no new dependency.

- [ ] **Step 14: Commit release files**

```bash
git add README.md pyproject.toml src/engcalc_colab/__init__.py tests/test_acceptance_native_plot.py tests/test_magic.py tests/test_packaging.py tests/test_parser.py
git commit -m "release: prepare EngCalc 0.6.0"
```

---

## Final Acceptance Checklist

- [ ] Symbolic `abs` works.
- [ ] Zero/multiple argument `abs` fails concisely.
- [ ] Numeric/Pint absolute value works.
- [ ] `numeric(abs(P))` works.
- [ ] `plot(abs(V(x)))` works.
- [ ] `plot(abs(M(x)))` preserves moment classification.
- [ ] Signed envelope numerical behavior matches 0.5.0.
- [ ] Magnitude envelope has one max-magnitude branch.
- [ ] Magnitude source curves preserve signs.
- [ ] Governing index and signed value are retained.
- [ ] Mixed signed/absolute envelope fails.
- [ ] Magnitude sweep and units work without state mutation.
- [ ] Multi-series panel is axes-owned.
- [ ] Signed-envelope panel is axes-owned.
- [ ] Magnitude-envelope panel is axes-owned.
- [ ] Panel chooser changes corner with data occupancy.
- [ ] Legend corner is penalized.
- [ ] Entire rendered panel bbox remains inside axes.
- [ ] No fixed right-side margin remains.
- [ ] Single-series callouts remain unchanged.
- [ ] Moment-positive-down remains.
- [ ] Source full suite passes.
- [ ] Real 0.6.0 wheel builds and installs cleanly.
- [ ] Installed-wheel smoke passes.
- [ ] Installed-wheel full suite passes outside source tree.
- [ ] README matches final syntax.
- [ ] Temporary validation workflow is absent from final product diff.
