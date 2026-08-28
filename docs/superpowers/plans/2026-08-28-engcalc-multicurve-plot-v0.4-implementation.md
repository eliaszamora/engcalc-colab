# EngCalc 0.4.0 Multi-curve Plot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend native `plot()` so one figure can compare several compatible EngCalc functions or sweep one function across several values of one engineering parameter while preserving all EngCalc 0.3.3 single-curve behavior.

**Architecture:** Keep the existing parser → symbolic/numeric engine → immutable plot transport → Matplotlib adapter boundary. Generalize `PlotResult` to shared x samples plus immutable `PlotSeries` records, add a narrow plot-only keyword/list grammar for parameter sweeps, extend `NumericContext` with non-mutating numerical-expression and shared-grid sampling helpers, and make `render_plot()` choose the existing single-series presentation or a line/legend/characteristic-panel multi-series presentation.

**Tech Stack:** Python 3.10+, SymPy, Pint, Matplotlib, IPython/Jupyter display, pytest.

**Spec:** `docs/superpowers/specs/2026-08-28-engcalc-multicurve-plot-v0.4-design.md`

## Global Constraints

- Base checkpoint is EngCalc **0.3.3** at commit `81d743a14592412f7170306f3f6514e9f1b298c5`.
- Target release is **0.4.0**.
- Existing `plot(M(x), x, 0, L)` behavior must remain visually and numerically compatible with 0.3.3.
- One `plot(...)` call always produces exactly one figure.
- Multi-expression syntax is `plot(expr1, expr2, ..., variable, start, end)`.
- Parameter-sweep syntax is `plot(expression, variable, start, end, parameter=[value1, value2, ...])`.
- Only one sweep parameter is allowed in 0.4.0.
- Sweep + multiple plotted expressions is rejected.
- Sweep lists are plot-only syntax; Python collection syntax must not become generally available in `%%eng`.
- Every sweep entry is a complete EngCalc numerical expression, e.g. `5*kN/m`; `[5, 10]*kN/m` shorthand is not supported.
- All series on one y-axis must have compatible dimensions.
- Mixed moment/non-moment multi-expression plots are rejected.
- All-moment plots preserve the existing positive-moment-down convention.
- Single-series plots keep fill, markers, and 0.3.3 smart max/min callouts.
- Multi-series plots use lines without fills, automatic legend, per-series extrema markers, and a characteristic-values panel outside the data area.
- Plot and sweep overrides must never mutate stored numerical values such as `x` or `q`.
- No arbitrary Matplotlib kwargs, Python `eval`/`exec`, attribute access, subscripting, comprehensions, dictionaries, callbacks, file access, or network access are introduced.

---

## File Map

- `src/engcalc_colab/models.py` — immutable plot transport models only.
- `src/engcalc_colab/parser.py` — restricted EngCalc grammar and plot-only sweep-list validation.
- `src/engcalc_colab/numeric.py` — Pint-backed evaluation, local overrides, x-grid creation, per-series sampling, cross-series unit normalization.
- `src/engcalc_colab/engine.py` — interpret `plot()` call shapes, expand functions, produce `PlotSeries` and `PlotResult` without Matplotlib.
- `src/engcalc_colab/plotting.py` — presentation only: lines, fill policy, legend, extrema, characteristic panel, moment inversion.
- `src/engcalc_colab/magic.py` — source-order display boundary; expected to require no structural change, only regression verification.
- `tests/test_plot_parser.py` — restricted grammar and plot transport model tests.
- `tests/test_numeric_context.py` — reusable numeric helper tests.
- `tests/test_plot_engine.py` — multi-series/sweep evaluation and non-mutation tests.
- `tests/test_plotting.py` — single-series regression and multi-series visual-structure tests.
- `tests/test_magic.py` — one-call/one-figure source-order integration.
- `tests/test_acceptance_native_plot.py` — end-to-end public syntax acceptance.
- `tests/test_packaging.py`, `pyproject.toml`, `src/engcalc_colab/__init__.py`, `README.md` — 0.4.0 release metadata and documentation.

---

### Task 1: Generalize the immutable plot transport model

**Files:**
- Modify: `src/engcalc_colab/models.py`
- Modify: `tests/test_plot_parser.py`

**Interfaces:**
- Produces: `PlotSeries(display_label: str, y_values: tuple[Any, ...], is_moment: bool)`.
- Produces: `PlotResult(statement, display_label, variable, x_values, series)` where `series` is `tuple[PlotSeries, ...]`.
- Later tasks must not store Matplotlib objects or mutable lists in these models.

- [ ] **Step 1: Write failing immutable-model tests**

Add to `tests/test_plot_parser.py`:

```python
from dataclasses import FrozenInstanceError

from engcalc_colab.models import PlotResult, PlotSeries


def test_plot_result_transports_shared_x_grid_and_multiple_series():
    statement = parse_cell("plot(M_1(x), M_2(x), x, 0, L)")[0]
    series = (
        PlotSeries("M_1(x)", (1, 2), True),
        PlotSeries("M_2(x)", (3, 4), True),
    )
    result = PlotResult(statement, "M(x)", "x", (0, 1), series)

    assert result.display_label == "M(x)"
    assert result.x_values == (0, 1)
    assert tuple(item.display_label for item in result.series) == ("M_1(x)", "M_2(x)")


def test_plot_series_is_immutable():
    series = PlotSeries("M(x)", (1,), True)
    try:
        series.display_label = "V(x)"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("expected frozen PlotSeries")
```

Replace the old positional `PlotResult(..., y_values)` assertion so tests target the new series transport.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
pytest tests/test_plot_parser.py -v
```

Expected: FAIL because `PlotSeries` does not exist and `PlotResult` still exposes `y_values` directly.

- [ ] **Step 3: Implement the model change**

In `src/engcalc_colab/models.py` replace the monoseries plot model with:

```python
@dataclass(frozen=True)
class PlotSeries:
    display_label: str
    y_values: tuple[Any, ...]
    is_moment: bool


@dataclass(frozen=True)
class PlotResult:
    statement: ParsedStatement
    display_label: str
    variable: str
    x_values: tuple[Any, ...]
    series: tuple[PlotSeries, ...]
```

Do not add rendering fields, colors, Matplotlib handles, or mutable containers.

- [ ] **Step 4: Run the model tests and verify GREEN**

Run:

```bash
pytest tests/test_plot_parser.py -v
```

Expected: model tests PASS; existing parser behavior may still pass because parser syntax has not changed yet.

- [ ] **Step 5: Commit the model boundary**

```bash
git add src/engcalc_colab/models.py tests/test_plot_parser.py
git commit -m "refactor: generalize plot result for multiple series"
```

---

### Task 2: Add a narrow plot-only sweep grammar

**Files:**
- Modify: `src/engcalc_colab/parser.py`
- Modify: `tests/test_plot_parser.py`

**Interfaces:**
- Consumes: existing restricted `ast.Expression` parser.
- Produces: parsed `plot(...)` calls that may contain one `ast.keyword` whose value is a non-empty `ast.List`.
- Invariant: keyword/list syntax remains invalid everywhere except `plot(..., parameter=[...])`.

- [ ] **Step 1: Add parser tests for multi-expression and sweep syntax**

Add:

```python
def test_plot_accepts_multiple_positional_expressions():
    statement = parse_cell("plot(M_D(x), M_L(x), x, 0, L)")[0]
    call = statement.expression.body
    assert len(call.args) == 5
    assert call.keywords == []


def test_plot_accepts_one_parameter_sweep_keyword():
    statement = parse_cell(
        "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])"
    )[0]
    call = statement.expression.body
    assert len(call.args) == 4
    assert len(call.keywords) == 1
    assert call.keywords[0].arg == "q"
    assert len(call.keywords[0].value.elts) == 3
```

Add rejection tests:

```python
def assert_syntax_error(source, expected):
    try:
        parse_cell(source)
    except EngSyntaxError as exc:
        assert expected in str(exc)
    else:
        raise AssertionError("expected EngSyntaxError")


def test_non_plot_keyword_arguments_remain_forbidden():
    assert_syntax_error("numeric(A, unit=kN)", "keyword arguments are unsupported")


def test_plot_rejects_multiple_sweep_keywords():
    assert_syntax_error(
        "plot(M(x), x, 0, L, q=[5*kN/m], L=[4*m])",
        "plot accepts at most one sweep parameter",
    )


def test_plot_rejects_empty_sweep_list():
    assert_syntax_error(
        "plot(M(x), x, 0, L, q=[])",
        "plot sweep list cannot be empty",
    )


def test_list_syntax_remains_forbidden_outside_plot_sweep():
    assert_syntax_error("A = [1, 2]", "unsupported syntax 'List'")


def test_plot_sweep_rejects_comprehensions_and_unpacking():
    assert_syntax_error(
        "plot(M(x), x, 0, L, q=[v for v in x])",
        "unsupported syntax 'ListComp'",
    )
    assert_syntax_error(
        "plot(M(x), x, 0, L, q=[*x])",
        "unsupported syntax 'Starred'",
    )
```

- [ ] **Step 2: Run parser tests and verify RED**

```bash
pytest tests/test_plot_parser.py -v
```

Expected: multi-expression positional call parses already, but sweep cases FAIL because `ast.keyword`/`ast.List` are unsupported and all keywords are rejected.

- [ ] **Step 3: Implement parent-aware restricted validation**

In `parser.py`, add `ast.keyword` and `ast.List` to the syntactic node types that the validator can inspect, but do **not** make them generally legal. Build a parent map and enforce the narrow relationship:

```python
def _validate_ast(tree: ast.AST, line_no: int) -> None:
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise EngSyntaxError(
                f"line {line_no}: unsupported syntax '{type(node).__name__}'"
            )

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise EngSyntaxError(
                    f"line {line_no}: unsupported syntax '{type(node.func).__name__}'"
                )
            if node.func.id.startswith("__"):
                raise EngSyntaxError(
                    f"line {line_no}: unsupported function '{node.func.id}'"
                )
            if node.func.id != "plot" and node.keywords:
                raise EngSyntaxError(
                    f"line {line_no}: keyword arguments are unsupported"
                )
            if node.func.id == "plot":
                _validate_plot_keywords(node, line_no)

        if isinstance(node, ast.List):
            keyword = parents.get(node)
            call = parents.get(keyword) if isinstance(keyword, ast.keyword) else None
            if not (
                isinstance(keyword, ast.keyword)
                and isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "plot"
                and keyword.value is node
            ):
                raise EngSyntaxError(
                    f"line {line_no}: unsupported syntax 'List'"
                )
```

Add:

```python
def _validate_plot_keywords(node: ast.Call, line_no: int) -> None:
    if len(node.keywords) > 1:
        raise EngSyntaxError(
            f"line {line_no}: plot accepts at most one sweep parameter"
        )
    if not node.keywords:
        return

    keyword_node = node.keywords[0]
    if keyword_node.arg is None:
        raise EngSyntaxError(
            f"line {line_no}: plot does not support **kwargs"
        )
    if keyword_node.arg in _RESERVED or keyword.iskeyword(keyword_node.arg):
        raise EngSyntaxError(
            f"line {line_no}: invalid plot sweep parameter '{keyword_node.arg}'"
        )
    if not isinstance(keyword_node.value, ast.List):
        raise EngSyntaxError(
            f"line {line_no}: plot sweep values must use a list"
        )
    if not keyword_node.value.elts:
        raise EngSyntaxError(
            f"line {line_no}: plot sweep list cannot be empty"
        )
```

Ensure `_ALLOWED_NODES` contains `ast.keyword` and `ast.List`, but still omits `ast.ListComp`, `ast.Starred`, `ast.Dict`, `ast.Tuple`, `ast.Attribute`, and `ast.Subscript`.

- [ ] **Step 4: Run parser tests and full parser regression**

```bash
pytest tests/test_plot_parser.py tests/test_parser.py tests/test_numeric_parser.py -v
```

Expected: all PASS; non-plot calls still reject keywords and collection syntax.

- [ ] **Step 5: Commit the restricted grammar extension**

```bash
git add src/engcalc_colab/parser.py tests/test_plot_parser.py
git commit -m "feat: add restricted plot sweep grammar"
```

---

### Task 3: Add non-mutating numeric helpers for sweep values and shared x grids

**Files:**
- Modify: `src/engcalc_colab/numeric.py`
- Modify: `tests/test_numeric_context.py`

**Interfaces:**
- Produces: `NumericContext.evaluate_numeric_node(node: ast.AST) -> Quantity`.
- Produces: `NumericContext.make_plot_x_values(start, end, count=201) -> tuple[Quantity, ...]`.
- Produces: `NumericContext.sample_symbolic_on_x(expression, variable, x_values, overrides=None) -> tuple[Quantity, ...]`.
- Produces: `NumericContext.normalize_plot_series_units(series_values) -> tuple[tuple[Quantity, ...], ...]`.
- Preserves: `sample_symbolic(...)` as a compatibility wrapper for existing single-series callers/tests.

- [ ] **Step 1: Add failing numeric helper tests**

Add tests that construct a `NumericContext`, assign `q`/`L`, parse numeric nodes from existing parser expressions, and verify:

```python
def test_evaluate_numeric_node_does_not_store_value():
    context = NumericContext()
    context.assign("q", parse_cell("q := 2.8*tonf/m")[0].expression)
    node = parse_cell("tmp := 5*kN/m")[0].expression.body

    value = context.evaluate_numeric_node(node)

    assert value.to("kN/m").magnitude == 5
    assert context.get("tmp") is None


def test_shared_plot_x_grid_and_local_overrides_do_not_mutate_context():
    context = NumericContext()
    context.assign("L", parse_cell("L := 4*m")[0].expression)
    context.assign("q", parse_cell("q := 2.8*tonf/m")[0].expression)
    context.assign("x", parse_cell("x := 2.5*m")[0].expression)

    start, end = context.normalize_plot_bounds(
        context.ureg.Quantity(0), context.get("L")
    )
    xs = context.make_plot_x_values(start, end, count=201)
    x = sp.Symbol("x")
    q = sp.Symbol("q")
    ys = context.sample_symbolic_on_x(
        q * x,
        "x",
        xs,
        overrides={"q": context.ureg.Quantity(5, "kN/m")},
    )

    assert len(xs) == 201
    assert ys[-1].to("kN").magnitude == 20
    assert context.get("x").to("m").magnitude == 2.5
    assert context.get("q").to("tonf/m").magnitude == 2.8
```

Add a cross-series normalization test using one series in `kN*m` and another compatible series in `N*m`, plus an incompatible `kN` series that must raise `EngEvaluationError("plot series have incompatible y dimensions")`.

- [ ] **Step 2: Run focused tests and verify RED**

```bash
pytest tests/test_numeric_context.py -v
```

Expected: FAIL because the four new helper methods do not exist.

- [ ] **Step 3: Implement reusable numeric helpers**

Refactor the body currently duplicated inside `assign()` so a node can be evaluated without storing:

```python
def evaluate_numeric_node(self, node: ast.AST):
    try:
        value = _NumericAstEvaluator(self).visit(node)
        return self._as_quantity(value)
    except EngEvaluationError:
        raise
    except DimensionalityError as exc:
        raise EngEvaluationError("incompatible units") from exc
    except PintError as exc:
        raise EngEvaluationError(f"numeric unit evaluation failed: {exc}") from exc
    except Exception as exc:
        raise EngEvaluationError(f"numeric evaluation failed: {exc}") from exc
```

Then make `assign()` call `evaluate_numeric_node(expression.body)` before persisting.

Split plotting helpers:

```python
def make_plot_x_values(self, start, end, count=201):
    if count < 2:
        raise EngEvaluationError("plot sampling requires at least 2 points")
    start, end = self.normalize_plot_bounds(start, end)
    delta = end - start
    return tuple(
        start + delta * (index / (count - 1))
        for index in range(count)
    )


def sample_symbolic_on_x(
    self,
    expression,
    variable,
    x_values,
    overrides=None,
):
    ys = []
    y_unit = None
    base_overrides = dict(overrides or {})
    for x_value in x_values:
        local_overrides = dict(base_overrides)
        local_overrides[variable] = x_value
        _, y_value = self.evaluate_symbolic(
            expression,
            overrides=local_overrides,
        )
        if y_unit is None:
            y_unit = y_value.units
        try:
            y_value = y_value.to(y_unit)
        except DimensionalityError as exc:
            raise EngEvaluationError(
                "plot samples have incompatible result units"
            ) from exc
        ys.append(y_value)
    return tuple(ys)
```

Retain the old public helper as:

```python
def sample_symbolic(self, expression, variable, start, end, count=201):
    xs = self.make_plot_x_values(start, end, count=count)
    ys = self.sample_symbolic_on_x(expression, variable, xs)
    return xs, ys
```

Add cross-series normalization:

```python
def normalize_plot_series_units(self, series_values):
    if not series_values:
        return ()
    target_unit = series_values[0][0].units
    normalized = []
    for values in series_values:
        try:
            normalized.append(tuple(value.to(target_unit) for value in values))
        except DimensionalityError as exc:
            raise EngEvaluationError(
                "plot series have incompatible y dimensions"
            ) from exc
    return tuple(normalized)
```

- [ ] **Step 4: Run numeric regression tests**

```bash
pytest tests/test_numeric_context.py tests/test_numeric_engine.py tests/test_acceptance_numeric_units.py -v
```

Expected: all PASS, including the legacy `sample_symbolic()` behavior.

- [ ] **Step 5: Commit the numeric foundation**

```bash
git add src/engcalc_colab/numeric.py tests/test_numeric_context.py
git commit -m "refactor: add shared plot sampling helpers"
```

---

### Task 4: Build multi-expression and parameter-sweep series in the engine

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Modify: `tests/test_plot_engine.py`

**Interfaces:**
- Consumes: `PlotSeries`, new `NumericContext` helpers.
- Produces: `PlotResult(..., series=(...))` for every plot, including one-series plots.
- Private engine helpers: `_evaluate_plot_call`, `_plot_expression_label`, `_is_moment_label`, `_common_plot_label`, `_format_sweep_label`.

- [ ] **Step 1: Rewrite single-series assertions for the new transport and add multi-series tests**

Update old tests from `result.y_values` to `result.series[0].y_values` and add:

```python
def test_plot_builds_multiple_function_series_on_one_x_grid():
    engine = EngineeringEngine()
    eval_cell(engine, "M_D(x) = q_D*x*(L-x)/2\nM_L(x) = q_L*x*(L-x)/2")
    eval_cell(engine, "q_D := 8*kN/m\nq_L := 5*kN/m\nL := 6*m")

    result = eval_cell(engine, "plot(M_D(x), M_L(x), x, 0, L)")[-1]

    assert result.display_label == "M(x)"
    assert len(result.x_values) == 201
    assert [series.display_label for series in result.series] == ["M_D(x)", "M_L(x)"]
    assert all(series.is_moment for series in result.series)
    assert result.series[0].y_values[100].to("kN*m").magnitude == 72
    assert result.series[1].y_values[100].to("kN*m").magnitude == 45
```

Add sweep/non-mutation coverage:

```python
def test_plot_parameter_sweep_creates_one_series_per_value_without_mutation():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 6*m\nx := 1.5*m")

    result = eval_cell(
        engine,
        "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])",
    )[-1]

    assert result.display_label == "M(x)"
    assert len(result.series) == 3
    assert [round(series.y_values[100].to("kN*m").magnitude, 8) for series in result.series] == [45, 90, 135]
    assert all(series.display_label.startswith("q = ") for series in result.series)
    assert engine.numeric_context.get("q").to("tonf/m").magnitude == 2.8
    assert engine.numeric_context.get("x").to("m").magnitude == 1.5
```

Add concise failures for:

```text
plot(M_D(x), M_L(x), x, 0, L, q=[...])
plot(M(x), x, 0, L, z=[1, 2])              # z absent from expanded expression
plot(M(x), x, 0, L, x=[1*m, 2*m])          # sweep parameter equals plotting variable
plot(M(x), x, 0, L, q=[5*kN/m, 2*m])       # incompatible sweep dimensions
plot(V(x), M(x), x, 0, L)                   # incompatible y dimensions
plot(M(x), W(x), x, 0, L)                   # compatible dimensions but mixed moment classification
```

For the last case define `W(x)` with moment-compatible units but a non-`M...` function name so classification—not units—is what fails.

- [ ] **Step 2: Run engine tests and verify RED**

```bash
pytest tests/test_plot_engine.py -v
```

Expected: FAIL because engine still enforces exactly four arguments and constructs monoseries `PlotResult`.

- [ ] **Step 3: Extract plot-call interpretation from `visit_Call()`**

Replace the current `if name == "plot": ...` block with:

```python
if name == "plot":
    return self._evaluate_plot_call(node)
```

Use this call-shape split:

```python
def _evaluate_plot_call(self, node: ast.Call):
    if len(node.args) < 4:
        raise EngEvaluationError(
            "plot expects at least 4 positional arguments: expression[, expression...], variable, start, end"
        )

    expression_nodes = list(node.args[:-3])
    variable_node, start_node, end_node = node.args[-3:]

    if not isinstance(variable_node, ast.Name):
        raise EngEvaluationError("plot variable must be a symbolic identifier")

    if node.keywords and len(expression_nodes) != 1:
        raise EngEvaluationError(
            "plot parameter sweep supports exactly one plotted expression"
        )
```

For sweep calls, validate the keyword name is different from `variable`, expand the one symbolic expression, verify the sweep symbol occurs in `symbolic_expression.free_symbols`, and evaluate each list entry with `numeric_context.evaluate_numeric_node()`.

For positional multi-expression calls, evaluate each expression node normally.

Resolve bounds once, then call:

```python
x_values = self.engine.numeric_context.make_plot_x_values(
    start_quantity,
    end_quantity,
    count=201,
)
```

Sample each expression through `sample_symbolic_on_x(...)`, passing `{parameter_name: sweep_quantity}` only for sweep series. Normalize all series through `normalize_plot_series_units(...)` before constructing `PlotSeries` objects.

- [ ] **Step 4: Add deterministic label/classification helpers**

Use the existing structural naming convention, generalized from the 0.3.3 plotting regex:

```python
_MOMENT_LABEL = re.compile(r"^M(?:_[A-Za-z0-9]+|[0-9]+)?\(")


def _is_moment_label(label: str) -> bool:
    return _MOMENT_LABEL.match(label.strip()) is not None
```

Reuse the current function-call display-label logic in a helper:

```python
def _plot_expression_label(self, node, symbolic_expression, variable):
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in self.engine.functions
    ):
        return f"{node.func.id}({variable})"
    return str(symbolic_expression)
```

For common plot labels, derive the function family before the first underscore. `M_D(x)` + `M_L(x)` becomes `M(x)`. Otherwise use `Comparison`.

Format sweep labels using Pint's abbreviated pretty unit format and a compact magnitude:

```python
def _format_sweep_label(name, quantity):
    magnitude = f"{float(quantity.magnitude):g}"
    if quantity.dimensionless:
        return f"{name} = {magnitude}"
    return f"{name} = {magnitude} {quantity.units:~P}"
```

If some series are classified as moment and others are not, raise:

```text
plot cannot mix moment and non-moment series on one axis
```

Do this after unit compatibility has been established so dimensional errors remain the primary error for `V(x)` + `M(x)`.

- [ ] **Step 5: Construct the new `PlotResult` in `EngineeringEngine.evaluate()`**

Change `plot_evaluation` payload to:

```python
(
    display_label,
    variable,
    x_values,
    plot_series,
)
```

and return:

```python
return PlotResult(
    statement=statement,
    display_label=display_label,
    variable=variable,
    x_values=x_values,
    series=plot_series,
)
```

Retain `plot must be a standalone statement` behavior unchanged.

- [ ] **Step 6: Run engine and acceptance regressions**

```bash
pytest tests/test_plot_engine.py tests/test_engine.py tests/test_acceptance_native_plot.py -v
```

Expected: all PASS after updating existing single-series assertions to the new transport model.

- [ ] **Step 7: Commit the engine behavior**

```bash
git add src/engcalc_colab/engine.py tests/test_plot_engine.py tests/test_acceptance_native_plot.py
git commit -m "feat: evaluate multi-curve and parameter-sweep plots"
```

---

### Task 5: Render readable multi-series structural comparison plots

**Files:**
- Modify: `src/engcalc_colab/plotting.py`
- Modify: `tests/test_plotting.py`

**Interfaces:**
- Consumes: `PlotResult.series` and shared `x_values`.
- Produces: one closed Matplotlib figure.
- One-series path must retain 0.3.3 layout and annotation behavior.
- Multi-series path: line-only curves, legend, extrema markers, outside characteristic panel.

- [ ] **Step 1: Keep every existing single-series plotting assertion and add multi-series tests**

Add helper:

```python
def multi_moment_plot_result():
    engine = EngineeringEngine()
    eval_cell(engine, "M_D(x) = q_D*x*(L-x)/2\nM_L(x) = q_L*x*(L-x)/2")
    eval_cell(engine, "q_D := 8*kN/m\nq_L := 5*kN/m\nL := 6*m")
    return eval_cell(engine, "plot(M_D(x), M_L(x), x, 0, L)")[-1]
```

Add tests:

```python
def test_multi_series_plot_uses_lines_legend_and_no_area_fill():
    figure = render_plot(multi_moment_plot_result())
    axis = figure.axes[0]

    # two data lines + zero reference
    assert len(axis.lines) == 3
    assert axis.get_legend() is not None
    assert [text.get_text() for text in axis.get_legend().get_texts()] == [
        "M_D(x)", "M_L(x)"
    ]

    from matplotlib.collections import PolyCollection
    assert not any(isinstance(item, PolyCollection) for item in axis.collections)


def test_multi_series_plot_preserves_positive_moment_down():
    axis = render_plot(multi_moment_plot_result()).axes[0]
    assert axis.yaxis_inverted()


def test_multi_series_extrema_use_markers_without_axis_callout_boxes():
    figure = render_plot(multi_moment_plot_result())
    axis = figure.axes[0]

    assert axis.texts == []
    marker_sets = [
        item for item in axis.collections
        if isinstance(item, PathCollection)
    ]
    assert len(marker_sets) == 2


def test_multi_series_characteristic_panel_is_outside_data_axis():
    figure = render_plot(multi_moment_plot_result())
    panel_text = "\n".join(text.get_text() for text in figure.texts)

    assert "M_D(x)" in panel_text
    assert "M_L(x)" in panel_text
    assert "max" in panel_text
    assert "min" in panel_text
    assert "x =" in panel_text
```

All existing 0.3.3 tests—moment inversion, force·length unit order, inward boxed callouts, curve-lobe separation, one deduplicated marker collection, and closed figure—must remain present and pass.

- [ ] **Step 2: Run plotting tests and verify RED**

```bash
pytest tests/test_plotting.py -v
```

Expected: FAIL because `render_plot()` still reads `result.y_values` and assumes one curve.

- [ ] **Step 3: Split single-series and multi-series rendering paths**

At the top of `render_plot()` compute shared x magnitudes and choose:

```python
if len(result.series) == 1:
    _render_single_series(axis, result, x_values)
else:
    _render_multi_series(axis, figure, result, x_values)
```

Move the existing 0.3.3 line/fill/marker/callout logic nearly verbatim into `_render_single_series(...)`. Do not redesign it while doing this task.

For `_render_multi_series(...)`:

```python
for series in result.series:
    y_values = [float(value.magnitude) for value in series.y_values]
    line = axis.plot(
        x_values,
        y_values,
        linewidth=2.0,
        label=series.display_label,
        zorder=3,
    )[0]
    maximum_index, minimum_index = _extreme_indices(y_values)
    marker_indices = sorted({maximum_index, minimum_index})
    axis.scatter(
        [x_values[index] for index in marker_indices],
        [y_values[index] for index in marker_indices],
        s=24,
        color=line.get_color(),
        zorder=4,
    )
```

Do not call `fill_between()` on the multi-series path.

- [ ] **Step 4: Add the characteristic-values panel**

Build one compact figure-level string with deterministic series order:

```text
Characteristic values
M_D(x)
max = 72.00 kN·m   x = 3.00 m
min = 0.00 kN·m    x = 0.00 m

M_L(x)
max = 45.00 kN·m   x = 3.00 m
min = 0.00 kN·m    x = 0.00 m
```

Use the existing `_quantity_label(...)` so moment units keep force·length ordering. Place it with `figure.text(...)` at the right side of the figure, not with `axis.annotate(...)` or `axis.text(...)`.

Reserve space with:

```python
figure.tight_layout(rect=(0.0, 0.0, 0.73, 1.0))
```

for multi-series plots. Keep ordinary `figure.tight_layout()` for one series.

Use a modest figure-level bbox derived from the figure/axes face color; do not introduce hard-coded EngCalc colors.

- [ ] **Step 5: Apply shared labels and orientation**

Use the first series' first y quantity for the shared y-unit label:

```python
axis.set_ylabel(
    _axis_label(
        result.display_label,
        result.series[0].y_values[0],
        moment=all(series.is_moment for series in result.series),
    )
)
```

Refactor `_axis_label` to accept an explicit `moment` flag instead of reclassifying the plot from its plot-level title. This prevents `Comparison` titles from losing engineering unit ordering.

Invert the y-axis when:

```python
all(series.is_moment for series in result.series)
```

Call `axis.legend()` only for `len(result.series) > 1`.

- [ ] **Step 6: Run plotting and engine regressions**

```bash
pytest tests/test_plotting.py tests/test_plot_engine.py -v
```

Expected: all PASS; single-series tests demonstrate no regression and multi-series tests demonstrate the new visual structure.

- [ ] **Step 7: Commit the renderer**

```bash
git add src/engcalc_colab/plotting.py tests/test_plotting.py
git commit -m "feat: render readable multi-series structural plots"
```

---

### Task 6: Verify notebook source order and end-to-end public syntax

**Files:**
- Modify: `tests/test_magic.py`
- Modify: `tests/test_acceptance_native_plot.py`
- Modify only if required by a failing regression: `src/engcalc_colab/magic.py`

**Interfaces:**
- Consumes: one `PlotResult` representing one or many series.
- Produces: exactly one displayed figure per `plot(...)` statement in source order.

- [ ] **Step 1: Add a multi-series magic sequencing test**

Reuse the existing display monkeypatch pattern in `tests/test_magic.py` and add a cell equivalent to:

```text
A = q*L
q := 5*kN/m
L := 6*m
M(x) = q*x*(L-x)/2
plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])
B = 2*A
```

Assert the captured outputs remain:

1. preceding math/equation group;
2. exactly one Matplotlib figure;
3. following math/equation group.

Also assert the figure legend has exactly two entries.

- [ ] **Step 2: Add public acceptance tests for both new syntaxes**

In `tests/test_acceptance_native_plot.py`, add one acceptance case for:

```text
plot(M_D(x), M_L(x), x, 0, L)
```

and one for:

```text
plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
```

Validate returned/displayed figures structurally—series count, legend labels, moment inversion—not by pixel snapshots.

- [ ] **Step 3: Run the integration tests and verify expected state**

```bash
pytest tests/test_magic.py tests/test_acceptance_native_plot.py -v
```

Expected: preferably PASS without changes to `magic.py`, because it already branches on `PlotResult`. If a failure proves the magic accesses removed `PlotResult.y_values`, update only that access; do not redesign batching or display flow.

- [ ] **Step 4: Run the complete pre-release suite**

```bash
pytest -q
```

Expected: all tests PASS before any version bump.

- [ ] **Step 5: Commit integration coverage**

```bash
git add tests/test_magic.py tests/test_acceptance_native_plot.py src/engcalc_colab/magic.py
git commit -m "test: validate multi-series plots in notebook flow"
```

If `magic.py` was unchanged, omit it from `git add`.

---

### Task 7: Release EngCalc 0.4.0 and document the public contract

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/engcalc_colab/__init__.py`
- Modify: `tests/test_packaging.py`
- Modify: any existing runtime-version assertion test found by `grep -R '0\.3\.3' tests src -n`
- Modify: `README.md`

**Interfaces:**
- Produces: package/runtime version `0.4.0`.
- Produces: user documentation for single plot, multi-expression comparison, and one-parameter sweep.

- [ ] **Step 1: Make release-version tests RED first**

Change the packaging assertion to:

```python
def test_pyproject_version_is_0_4_0():
    assert _project_metadata()["version"] == "0.4.0"
```

Search for all runtime/package version assertions:

```bash
grep -R "0\.3\.3" tests src README.md pyproject.toml -n
```

Update only test expectations first, then run:

```bash
pytest tests/test_packaging.py -v
```

Expected: version assertion FAILS while dependency assertions remain PASS.

- [ ] **Step 2: Bump package/runtime metadata to 0.4.0**

In `pyproject.toml`:

```toml
version = "0.4.0"
```

In `src/engcalc_colab/__init__.py` set:

```python
__version__ = "0.4.0"
```

Do not add new runtime dependencies; SymPy, Pint, and Matplotlib already cover the feature.

- [ ] **Step 3: Update README with the exact 0.4.0 syntax and limits**

Replace the obsolete statement that native plotting does not support multiple curves. Document these three canonical examples:

```text
plot(M(x), x, 0, L)
```

```text
plot(M_D(x), M_L(x), x, 0, L)
```

```text
plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
```

Document:

- shared compatible y units;
- automatic legend for multiple series;
- line-only multi-series presentation;
- external characteristic-values panel;
- single sweep parameter;
- sweep values are local and non-mutating;
- complete expression per sweep entry;
- labeled dictionaries/load-combination names remain deferred;
- arbitrary Matplotlib kwargs remain unsupported.

Also update the unit/plot section version labels that still say `v0.3.0` where they now describe current behavior.

- [ ] **Step 4: Run the complete source-tree suite**

```bash
pytest -q
```

Expected: all tests PASS.

- [ ] **Step 5: Build and install the real wheel in a clean virtual environment**

Run:

```bash
rm -rf dist build *.egg-info
python -m build
python -m venv .venv-release
. .venv-release/bin/activate
python -m pip install --upgrade pip
python -m pip install dist/engcalc_colab-0.4.0-py3-none-any.whl
python - <<'PY'
from engcalc_colab import __version__
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot

assert __version__ == "0.4.0"
engine = EngineeringEngine()
for stmt in parse_cell("M(x) = q*x*(L-x)/2\nL := 6*m"):
    engine.evaluate(stmt)
result = engine.evaluate(
    parse_cell("plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])")[0]
)
figure = render_plot(result)
axis = figure.axes[0]
assert len(result.series) == 3
assert axis.yaxis_inverted()
assert len(axis.get_legend().get_texts()) == 3
assert any("max" in text.get_text() for text in figure.texts)
print("EngCalc 0.4.0 multi-series wheel smoke PASS")
PY
```

Expected: script prints `EngCalc 0.4.0 multi-series wheel smoke PASS`.

If `python -m build` is unavailable in the development environment, install the build frontend into the development environment with `python -m pip install build` before running the build command; do not add `build` to EngCalc runtime dependencies.

- [ ] **Step 6: Run tests against the installed wheel rather than the source tree**

From a directory outside the repository or with `PYTHONPATH` cleared:

```bash
PYTHONPATH= .venv-release/bin/python -m pytest -q
```

If pytest is not installed in the release venv, install it only into that validation environment:

```bash
.venv-release/bin/python -m pip install pytest
PYTHONPATH= .venv-release/bin/python -m pytest -q
```

Expected: complete suite PASS using the wheel installation.

- [ ] **Step 7: Commit release metadata and docs**

```bash
git add pyproject.toml src/engcalc_colab/__init__.py tests README.md
git commit -m "release: EngCalc 0.4.0 multi-series plotting"
```

- [ ] **Step 8: Final branch verification before PR/merge**

```bash
git status --short
git log --oneline --decorate -8
pytest -q
```

Expected:

- clean working tree;
- task-sized commits visible in history;
- full suite PASS;
- no temporary validation workflow or release virtual environment committed.

Do not tag or merge until this final gate passes.

---

## Self-Review

### Spec coverage

- Backward-compatible single-series `plot(...)`: Tasks 1, 4, 5, 6.
- Positional multi-expression plotting: Tasks 2, 4, 5, 6.
- One-parameter sweep grammar: Tasks 2, 3, 4, 6.
- Plot-only list/keyword security boundary: Task 2.
- Non-mutating sweep/x overrides: Tasks 3 and 4.
- Shared 201-point x grid: Tasks 3 and 4.
- Cross-series dimensional compatibility: Tasks 3 and 4.
- Moment-positive-down consistency: Tasks 4 and 5.
- Automatic legend and no multi-series fill: Task 5.
- Single-series 0.3.3 smart callouts preserved: Task 5.
- Multi-series extrema markers plus external characteristic panel: Task 5.
- One plot statement → one figure in source order: Task 6.
- Release version/docs/wheel validation: Task 7.
- Deferred dictionaries, labeled combinations, multiple sweep parameters, dual axes, arbitrary Matplotlib options: explicitly excluded from every implementation task.

### Placeholder scan

No `TBD`, `TODO`, unspecified validation step, or open-ended “handle edge cases” instruction remains. Every task names concrete files, tests, expected failures, implementation interfaces, and verification commands.

### Type/interface consistency

- `PlotResult.series` is defined in Task 1 and consumed consistently in Tasks 4–6.
- `PlotSeries.y_values` is the only per-series ordinate store.
- `NumericContext.make_plot_x_values`, `sample_symbolic_on_x`, `evaluate_numeric_node`, and `normalize_plot_series_units` are defined in Task 3 before engine use in Task 4.
- The plotting adapter never receives symbolic expressions or numerical context objects; it consumes normalized `PlotResult` only.
- The notebook magic continues to receive one `PlotResult` per source `plot(...)` statement, independent of series count.
