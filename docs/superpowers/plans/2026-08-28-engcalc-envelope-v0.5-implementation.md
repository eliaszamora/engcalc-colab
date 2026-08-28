# EngCalc 0.5.0 Engineering Envelope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fast `envelope(...)` command that reuses EngCalc 0.4.0 multi-series plotting, computes sampled algebraic max/min envelopes, keeps the original response curves faintly visible, and preserves structural plotting conventions.

**Architecture:** Generalize the existing plot-only sweep/parser and `_evaluate_plot()` path into one shared response-series resolver. Normal `plot(...)` packages the resolved source series unchanged; `envelope(...)` reduces the same normalized source series point-by-point to algebraic maximum/minimum while retaining source series and governing indices as metadata. `render_plot()` dispatches by `PlotResult.kind`, leaving all 0.4.0 plot paths unchanged and adding one focused envelope renderer.

**Tech Stack:** Python 3.10+, SymPy, Pint, Matplotlib, IPython/Jupyter, pytest.

**Spec:** `docs/superpowers/specs/2026-08-28-engcalc-envelope-v0.5-design.md`

## Global Constraints

- Base checkpoint is EngCalc 0.4.0 `main` commit `8e2b629ae588f6166b2df1c48b1b3d08f42f9113`.
- Public syntax is `envelope(expr1, expr2, ..., variable, start, end)` or one-expression `envelope(expression, variable, start, end, parameter=[...])`.
- `envelope(...)` means sampled algebraic pointwise maximum/minimum, never absolute magnitude.
- Use the same 201 uniformly spaced x samples as `plot(...)` 0.4.0.
- Reuse the same Pint-aware bounds, unit normalization, function expansion, and local sweep override semantics as `plot(...)`.
- At least two source series must exist after expansion.
- A single expression without a sweep is invalid for `envelope(...)`.
- One sweep parameter only; multi-expression plus sweep remains invalid.
- Original source curves must remain visible as thin, faint background curves with no source markers or callout boxes.
- Envelope maximum/minimum boundaries must be visually emphasized and lightly filled between them.
- Moment-positive-down convention remains unchanged.
- `max` and `min` always mean algebraic maximum/minimum, not screen position.
- Preserve source-series order, source labels, `argmax`, and `argmin` metadata.
- Do not add an `EnvelopeEngine`, adaptive sampling, symbolic intersection solving, arbitrary plotting kwargs, dictionaries, dual axes, or new runtime dependencies.
- Existing EngCalc 0.4.0 single-, multi-, and sweep-plot behavior must remain unchanged.
- Target release version is `0.5.0`.

---

## File Structure

### Production files to modify

- `src/engcalc_colab/models.py` — extend immutable plot transport with envelope metadata while keeping current positional construction compatible.
- `src/engcalc_colab/parser.py` — reserve `envelope` and generalize the current plot-only restricted sweep grammar to `plot` + `envelope` only.
- `src/engcalc_colab/engine.py` — extract shared source-series resolution, dispatch `envelope`, compute sampled max/min + governing indices, and package envelope metadata.
- `src/engcalc_colab/plotting.py` — add envelope-specific rendering with faint source curves, emphasized boundaries, fill-between, and compact global characteristic panel.
- `src/engcalc_colab/__init__.py` — bump runtime version to 0.5.0.
- `pyproject.toml` — bump package version to 0.5.0; no dependency changes.
- `README.md` — document envelope syntax, sampled semantics, faint source curves, units, sign convention, and intentionally deferred features.

### Test files to create

- `tests/test_envelope_parser.py` — restricted grammar and parser-security contract.
- `tests/test_envelope_engine.py` — multiple-expression envelope reduction, governing metadata, units, errors, and state semantics.
- `tests/test_envelope_plotting.py` — structural rendering assertions for faint source curves and emphasized envelopes.

### Existing tests to modify

- `tests/test_magic.py` — one-figure/source-order integration for envelope.
- `tests/test_acceptance_native_plot.py` — add end-to-end envelope acceptance while retaining all current plot acceptance tests.
- `tests/test_packaging.py` — require 0.5.0 package/runtime metadata.

---

### Task 1: Extend the immutable plot transport without breaking 0.4.0 callers

**Files:**
- Modify: `src/engcalc_colab/models.py`
- Test: `tests/test_plot_parser.py`
- Create: `tests/test_envelope_engine.py`

**Interfaces:**
- Consumes: existing `PlotSeries(display_label, y_values, is_moment)` and five-positional-argument `PlotResult(statement, display_label, variable, x_values, series)` construction.
- Produces:

```python
@dataclass(frozen=True)
class PlotResult:
    statement: ParsedStatement
    display_label: str
    variable: str
    x_values: tuple[Any, ...]
    series: tuple[PlotSeries, ...]
    kind: str = "plot"
    source_series: tuple[PlotSeries, ...] = ()
    source_labels: tuple[str, ...] = ()
    governing_max: tuple[int, ...] | None = None
    governing_min: tuple[int, ...] | None = None
```

- The existing `y_values` compatibility property remains unchanged: it works only when `len(series) == 1`.

- [ ] **Step 1: Add failing transport tests**

Append to `tests/test_plot_parser.py`:

```python
def test_plot_result_defaults_preserve_v040_plot_transport():
    statement = parse_cell("plot(M(x), x, 0, L)")[0]
    series = PlotSeries("M(x)", (1, 2), True)
    result = PlotResult(statement, "M(x)", "x", (0, 1), (series,))

    assert result.kind == "plot"
    assert result.source_series == ()
    assert result.source_labels == ()
    assert result.governing_max is None
    assert result.governing_min is None
    assert result.y_values == (1, 2)
```

Create the initial `tests/test_envelope_engine.py` with:

```python
from dataclasses import FrozenInstanceError

import pytest

from engcalc_colab.models import PlotResult, PlotSeries
from engcalc_colab.parser import parse_cell


def test_plot_result_can_transport_envelope_metadata_immutably():
    statement = parse_cell("plot(A(x), B(x), x, 0, L)")[0]
    source = (
        PlotSeries("A(x)", (1, 3), False),
        PlotSeries("B(x)", (2, 2), False),
    )
    displayed = (
        PlotSeries("max", (2, 3), False),
        PlotSeries("min", (1, 2), False),
    )
    result = PlotResult(
        statement,
        "Comparison",
        "x",
        (0, 1),
        displayed,
        kind="envelope",
        source_series=source,
        source_labels=("A(x)", "B(x)"),
        governing_max=(1, 0),
        governing_min=(0, 1),
    )

    assert result.kind == "envelope"
    assert result.source_series == source
    assert result.source_labels == ("A(x)", "B(x)")
    assert result.governing_max == (1, 0)
    assert result.governing_min == (0, 1)

    with pytest.raises(FrozenInstanceError):
        result.kind = "plot"
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
pytest -q tests/test_plot_parser.py tests/test_envelope_engine.py
```

Expected: failures report unexpected `PlotResult` keyword arguments such as `kind` / `source_series`, while all pre-existing plot transport assertions remain green.

- [ ] **Step 3: Implement the minimal model extension**

In `src/engcalc_colab/models.py`, add the defaulted fields after `series` exactly as specified in the Interfaces block. Do not change `PlotSeries` and do not remove or relax the existing `y_values` property.

- [ ] **Step 4: Verify GREEN and existing model compatibility**

Run:

```bash
pytest -q tests/test_plot_parser.py tests/test_envelope_engine.py
```

Expected: PASS.

Then run:

```bash
pytest -q tests/test_plot_engine.py tests/test_plotting.py
```

Expected: all current 0.4.0 plot tests remain PASS because the new fields have defaults.

- [ ] **Step 5: Commit**

```bash
git add src/engcalc_colab/models.py tests/test_plot_parser.py tests/test_envelope_engine.py
git commit -m "refactor: extend plot transport for envelopes"
```

---

### Task 2: Add `envelope` to the restricted parser without broadening Python syntax

**Files:**
- Modify: `src/engcalc_colab/parser.py`
- Create: `tests/test_envelope_parser.py`
- Regression: `tests/test_plot_parser.py`, `tests/test_parser.py`

**Interfaces:**
- Consumes: `_ALLOWED_CALLS`, `_validate_normal_node`, `_validate_plot_keywords`, `_validate_sweep_value`.
- Produces:

```python
_DISPLAY_SWEEP_CALLS = {"plot", "envelope"}

def _validate_display_sweep_keywords(node: ast.Call, line_no: int) -> None: ...

def _validate_sweep_value(node: ast.AST, line_no: int, call_name: str) -> None: ...
```

- Only calls in `_DISPLAY_SWEEP_CALLS` may contain one keyword whose value is a non-empty `ast.List` of restricted numeric-expression nodes.
- All messages should use the actual call name (`plot` or `envelope`) so existing plot error text stays unchanged.

- [ ] **Step 1: Write parser RED tests**

Create `tests/test_envelope_parser.py`:

```python
import ast

import pytest

from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell


def test_envelope_accepts_multiple_positional_response_expressions():
    statement = parse_cell("envelope(M_D(x), M_L(x), x, 0, L)")[0]
    call = statement.expression.body
    assert call.func.id == "envelope"
    assert len(call.args) == 5
    assert call.keywords == []


def test_envelope_name_is_reserved_as_assignment_target():
    with pytest.raises(EngSyntaxError, match="reserved identifier 'envelope'"):
        parse_cell("envelope = 3")


def test_envelope_accepts_one_restricted_parameter_sweep_keyword():
    statement = parse_cell(
        "envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])"
    )[0]
    call = statement.expression.body
    assert len(call.args) == 4
    assert len(call.keywords) == 1
    assert call.keywords[0].arg == "q"
    assert isinstance(call.keywords[0].value, ast.List)
    assert len(call.keywords[0].value.elts) == 2


def test_envelope_rejects_more_than_one_sweep_keyword():
    with pytest.raises(
        EngSyntaxError,
        match="envelope accepts at most one sweep parameter",
    ):
        parse_cell("envelope(M(x), x, 0, L, q=[1], P=[2])")


def test_envelope_rejects_empty_or_non_list_sweep_values():
    with pytest.raises(EngSyntaxError, match="envelope sweep list cannot be empty"):
        parse_cell("envelope(M(x), x, 0, L, q=[])")
    with pytest.raises(EngSyntaxError, match="envelope sweep values must be a list"):
        parse_cell("envelope(M(x), x, 0, L, q=5*kN/m)")


def test_envelope_sweep_rejects_comprehensions_nested_lists_and_unpacking():
    invalid = [
        "envelope(M(x), x, 0, L, q=[v for v in x])",
        "envelope(M(x), x, 0, L, q=[[1], [2]])",
        "envelope(M(x), x, 0, L, q=[*q_values])",
    ]
    for source in invalid:
        with pytest.raises(EngSyntaxError, match="unsupported"):
            parse_cell(source)


def test_keyword_arguments_remain_rejected_for_non_display_calls():
    with pytest.raises(EngSyntaxError, match="keyword arguments are unsupported"):
        parse_cell("simplify(x, q=[1, 2])")


def test_general_list_and_dictionary_syntax_remains_disabled():
    with pytest.raises(EngSyntaxError, match="unsupported syntax 'List'"):
        parse_cell("A = [1, 2]")
    with pytest.raises(EngSyntaxError, match="unsupported syntax 'Dict'"):
        parse_cell("A = {1: 2}")
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
pytest -q tests/test_envelope_parser.py tests/test_plot_parser.py tests/test_parser.py
```

Expected: envelope tests fail because `envelope` is not reserved/recognized and envelope keywords are rejected; all plot parser tests remain green.

- [ ] **Step 3: Implement narrow shared display-sweep validation**

In `src/engcalc_colab/parser.py`:

```python
_DISPLAY_SWEEP_CALLS = {"plot", "envelope"}

_ALLOWED_CALLS = {
    "integral", "diff", "solve", "simplify", "expand", "factor",
    "subs", "eq", "sum", "numeric", "plot", "envelope",
}
```

Replace the plot-only keyword branch with:

```python
if node.keywords:
    if node.func.id not in _DISPLAY_SWEEP_CALLS:
        raise EngSyntaxError(
            f"line {line_no}: keyword arguments are unsupported"
        )
    _validate_display_sweep_keywords(node, line_no)
```

Implement:

```python
def _validate_display_sweep_keywords(node: ast.Call, line_no: int) -> None:
    call_name = node.func.id
    if len(node.keywords) > 1:
        raise EngSyntaxError(
            f"line {line_no}: {call_name} accepts at most one sweep parameter"
        )

    keyword_node = node.keywords[0]
    if keyword_node.arg is None:
        raise EngSyntaxError(
            f"line {line_no}: {call_name} does not support keyword unpacking"
        )
    if (
        not _IDENTIFIER.fullmatch(keyword_node.arg)
        or keyword.iskeyword(keyword_node.arg)
        or keyword_node.arg in _RESERVED
    ):
        raise EngSyntaxError(
            f"line {line_no}: invalid {call_name} sweep parameter '{keyword_node.arg}'"
        )

    sweep_value = keyword_node.value
    if not isinstance(sweep_value, ast.List):
        if isinstance(
            sweep_value,
            (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
        ):
            raise EngSyntaxError(
                f"line {line_no}: unsupported {call_name} sweep syntax "
                f"'{type(sweep_value).__name__}'"
            )
        raise EngSyntaxError(
            f"line {line_no}: {call_name} sweep values must be a list"
        )
    if not sweep_value.elts:
        raise EngSyntaxError(
            f"line {line_no}: {call_name} sweep list cannot be empty"
        )

    for element in sweep_value.elts:
        _validate_sweep_value(element, line_no, call_name)
```

Update `_validate_sweep_value` to accept `call_name` and preserve the existing wording pattern:

```python
def _validate_sweep_value(node: ast.AST, line_no: int, call_name: str) -> None:
    if not isinstance(node, _SWEEP_VALUE_NODES):
        raise EngSyntaxError(
            f"line {line_no}: unsupported {call_name} sweep syntax "
            f"'{type(node).__name__}'"
        )
    for child in ast.iter_child_nodes(node):
        _validate_sweep_value(child, line_no, call_name)
```

- [ ] **Step 4: Verify parser GREEN and security regression**

Run:

```bash
pytest -q tests/test_envelope_parser.py tests/test_plot_parser.py tests/test_parser.py tests/test_numeric_parser.py
```

Expected: PASS. Existing plot messages must remain byte-for-byte compatible with their current tests.

- [ ] **Step 5: Commit**

```bash
git add src/engcalc_colab/parser.py tests/test_envelope_parser.py
git commit -m "feat: add restricted envelope grammar"
```

---

### Task 3: Share source-series resolution and implement multiple-expression envelope reduction

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Modify: `tests/test_envelope_engine.py`
- Regression: `tests/test_plot_engine.py`, `tests/test_acceptance_native_plot.py`

**Interfaces:**
- Consumes: current `_evaluate_plot`, `_evaluate_plot_sweep`, `_normalize_plot_series`, `_plot_expression_label`, `_common_plot_label`, `_is_moment_label`.
- Produces these private engine interfaces:

```python
@dataclass(frozen=True)
class _ResolvedResponseSeries:
    display_label: str
    variable: str
    x_values: tuple
    series: tuple[PlotSeries, ...]
    first_symbolic_expression: object


def _resolve_response_series(
    self,
    node: ast.Call,
    *,
    call_name: str,
) -> _ResolvedResponseSeries: ...


def _build_envelope(
    self,
    resolved: _ResolvedResponseSeries,
) -> tuple[
    tuple[PlotSeries, PlotSeries],
    tuple[int, ...],
    tuple[int, ...],
]: ...
```

- `self.plot_evaluation` becomes an immutable private transport rather than an expanding raw tuple:

```python
@dataclass(frozen=True)
class _PlotEvaluation:
    display_label: str
    variable: str
    x_values: tuple
    series: tuple[PlotSeries, ...]
    kind: str = "plot"
    source_series: tuple[PlotSeries, ...] = ()
    source_labels: tuple[str, ...] = ()
    governing_max: tuple[int, ...] | None = None
    governing_min: tuple[int, ...] | None = None
```

- `EngineeringEngine.evaluate()` maps `_PlotEvaluation` into `PlotResult` and uses a generic standalone error: `"plot/envelope display calls must be standalone statements"` is NOT required. Preserve exact `plot must be a standalone statement` for plots and use `envelope must be a standalone statement` for envelopes.

- [ ] **Step 1: Add RED tests for algebraic multiple-expression envelopes**

Append to `tests/test_envelope_engine.py`:

```python
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import PlotResult
from engcalc_colab.parser import parse_cell


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def test_envelope_multiple_expressions_computes_signed_pointwise_max_min():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_A(x) = q*x*(L-x)/2\n"
        "M_B(x) = -0.5*q*x*(L-x)/2\n"
        "q := 8*kN/m\nL := 6*m",
    )

    result = eval_cell(
        engine,
        "envelope(M_A(x), M_B(x), x, 0, L)",
    )[-1]

    assert isinstance(result, PlotResult)
    assert result.kind == "envelope"
    assert result.display_label == "M(x)"
    assert len(result.x_values) == 201
    assert len(result.series) == 2
    assert result.series[0].display_label == "M_max(x)"
    assert result.series[1].display_label == "M_min(x)"
    assert result.series[0].is_moment
    assert result.series[1].is_moment
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(36.0)
    assert result.series[1].y_values[100].to("kN*m").magnitude == pytest.approx(-18.0)


def test_envelope_retains_source_series_labels_and_governing_indices():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_A(x) = q*x*(L-x)/2\n"
        "M_B(x) = -0.5*q*x*(L-x)/2\n"
        "q := 8*kN/m\nL := 6*m",
    )
    result = eval_cell(engine, "envelope(M_A(x), M_B(x), x, 0, L)")[-1]

    assert [item.display_label for item in result.source_series] == [
        "M_A(x)",
        "M_B(x)",
    ]
    assert result.source_labels == ("M_A(x)", "M_B(x)")
    assert len(result.governing_max) == 201
    assert len(result.governing_min) == 201
    assert result.governing_max[100] == 0
    assert result.governing_min[100] == 1


def test_envelope_rejects_single_non_sweep_source():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x\nq := 5*kN/m\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="envelope requires at least two response series",
    ):
        eval_cell(engine, "envelope(M(x), x, 0, L)")


def test_envelope_cannot_be_assigned_to_symbol():
    engine = EngineeringEngine()
    with pytest.raises(
        EngEvaluationError,
        match="envelope must be a standalone statement",
    ):
        eval_cell(engine, "A = envelope(x, 2*x, x, 0, 4)")
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
pytest -q tests/test_envelope_engine.py tests/test_plot_engine.py
```

Expected: envelope calls fail as unsupported in the engine. Existing plot tests remain green.

- [ ] **Step 3: Add private evaluation transports and dispatch**

At the top of `engine.py`, import `dataclass` and define:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class _ResolvedResponseSeries:
    display_label: str
    variable: str
    x_values: tuple
    series: tuple[PlotSeries, ...]
    first_symbolic_expression: object


@dataclass(frozen=True)
class _PlotEvaluation:
    display_label: str
    variable: str
    x_values: tuple
    series: tuple[PlotSeries, ...]
    kind: str = "plot"
    source_series: tuple[PlotSeries, ...] = ()
    source_labels: tuple[str, ...] = ()
    governing_max: tuple[int, ...] | None = None
    governing_min: tuple[int, ...] | None = None
```

In `visit_Call`:

```python
if name == "plot":
    return self._evaluate_plot(node)
if name == "envelope":
    return self._evaluate_envelope(node)
```

Update `EngineeringEngine.evaluate()` so it reads `_PlotEvaluation` attributes and populates all `PlotResult` fields. Use `plot_evaluation.kind` to select the standalone error:

```python
if statement.target is not None:
    raise EngEvaluationError(
        f"{evaluator.plot_evaluation.kind} must be a standalone statement"
    )
```

- [ ] **Step 4: Extract the current plot source resolution with call-specific errors**

Move the request interpretation, bounds, source expression evaluation, sweep expansion, normalization, and mixed-family check from `_evaluate_plot()` into:

```python
def _resolve_response_series(
    self,
    node: ast.Call,
    *,
    call_name: str,
) -> _ResolvedResponseSeries:
```

Use the current 0.4.0 logic unchanged except every error prefix that currently says `plot` must interpolate `call_name`:

```python
if len(node.args) < 4:
    raise EngEvaluationError(
        f"{call_name} expects at least 4 positional arguments: "
        "expression[, ...], variable, start, end"
    )
```

```python
if not expression_nodes:
    raise EngEvaluationError(f"{call_name} requires at least one expression")
```

```python
if not isinstance(variable_node, ast.Name):
    raise EngEvaluationError(
        f"{call_name} variable must be a symbolic identifier"
    )
```

```python
if node.keywords and len(expression_nodes) != 1:
    raise EngEvaluationError(
        f"{call_name} parameter sweep requires exactly one expression"
    )
```

Generalize `_evaluate_plot_sweep(...)` to `_evaluate_response_sweep(..., call_name=...)` and likewise use `call_name` in absent-parameter and incompatible-unit errors. Keep existing plot strings unchanged when `call_name="plot"`.

Return:

```python
return _ResolvedResponseSeries(
    display_label=display_label,
    variable=variable,
    x_values=x_values,
    series=series,
    first_symbolic_expression=symbolic_expressions[0],
)
```

Then reduce `_evaluate_plot()` to:

```python
def _evaluate_plot(self, node: ast.Call):
    resolved = self._resolve_response_series(node, call_name="plot")
    self.plot_evaluation = _PlotEvaluation(
        display_label=resolved.display_label,
        variable=resolved.variable,
        x_values=resolved.x_values,
        series=resolved.series,
        kind="plot",
    )
    return resolved.first_symbolic_expression
```

Run the existing plot tests immediately after this extraction before implementing the reduction:

```bash
pytest -q tests/test_plot_engine.py tests/test_plotting.py tests/test_plot_parser.py
```

Expected: PASS. Do not proceed until the 0.4.0 behavior is green.

- [ ] **Step 5: Implement minimal pointwise envelope reduction**

Add label helper:

```python
@staticmethod
def _envelope_series_labels(display_label: str, variable: str) -> tuple[str, str]:
    suffix = f"({variable})"
    if display_label != "Comparison" and display_label.endswith(suffix):
        family = display_label[:-len(suffix)]
        return f"{family}_max({variable})", f"{family}_min({variable})"
    return "max", "min"
```

Add reduction:

```python
def _build_envelope(self, resolved: _ResolvedResponseSeries):
    source = resolved.series
    if len(source) < 2:
        raise EngEvaluationError("envelope requires at least two response series")

    maximum_values = []
    minimum_values = []
    governing_max = []
    governing_min = []

    for point_index in range(len(resolved.x_values)):
        magnitudes = [
            float(item.y_values[point_index].magnitude)
            for item in source
        ]
        max_index = max(range(len(source)), key=magnitudes.__getitem__)
        min_index = min(range(len(source)), key=magnitudes.__getitem__)
        governing_max.append(max_index)
        governing_min.append(min_index)
        maximum_values.append(source[max_index].y_values[point_index])
        minimum_values.append(source[min_index].y_values[point_index])

    max_label, min_label = self._envelope_series_labels(
        resolved.display_label,
        resolved.variable,
    )
    moment = source[0].is_moment
    return (
        (
            PlotSeries(max_label, tuple(maximum_values), moment),
            PlotSeries(min_label, tuple(minimum_values), moment),
        ),
        tuple(governing_max),
        tuple(governing_min),
    )
```

Implement `_evaluate_envelope()`:

```python
def _evaluate_envelope(self, node: ast.Call):
    resolved = self._resolve_response_series(node, call_name="envelope")
    envelope_series, governing_max, governing_min = self._build_envelope(resolved)
    self.plot_evaluation = _PlotEvaluation(
        display_label=resolved.display_label,
        variable=resolved.variable,
        x_values=resolved.x_values,
        series=envelope_series,
        kind="envelope",
        source_series=resolved.series,
        source_labels=tuple(item.display_label for item in resolved.series),
        governing_max=governing_max,
        governing_min=governing_min,
    )
    return resolved.first_symbolic_expression
```

Because `_normalize_plot_series()` has already converted source series to a common first-series unit, magnitude comparisons are valid without new Pint conversions inside the reduction loop.

- [ ] **Step 6: Verify GREEN and full plot regression**

Run:

```bash
pytest -q tests/test_envelope_engine.py tests/test_plot_engine.py tests/test_acceptance_native_plot.py
```

Expected: PASS.

Then:

```bash
pytest -q tests/test_parser.py tests/test_plot_parser.py tests/test_plotting.py
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/engcalc_colab/engine.py tests/test_envelope_engine.py
git commit -m "feat: compute sampled engineering envelopes"
```

---

### Task 4: Complete sweep, unit, state, and error semantics for envelopes

**Files:**
- Modify: `tests/test_envelope_engine.py`
- Modify: `src/engcalc_colab/engine.py` only if tests reveal shared-error/refactor gaps.
- Regression: `tests/test_numeric_context.py`, `tests/test_plot_sampling.py`, `tests/test_plot_engine.py`

**Interfaces:**
- Consumes: `_resolve_response_series(..., call_name="envelope")` and `_build_envelope(...)` from Task 3.
- Produces no new public API. It closes all semantic gaps required by the approved spec.

- [ ] **Step 1: Add sweep/state/unit RED tests**

Append:

```python
def test_envelope_parameter_sweep_reduces_expanded_series_and_retains_sources():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nL := 6*m")

    result = eval_cell(
        engine,
        "envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])",
    )[-1]

    assert len(result.source_series) == 3
    assert result.source_labels == tuple(
        item.display_label for item in result.source_series
    )
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(67.5)
    assert result.series[1].y_values[100].to("kN*m").magnitude == pytest.approx(22.5)
    assert result.governing_max[100] == 2
    assert result.governing_min[100] == 0


def test_envelope_sweep_preserves_existing_parameter_and_x_state():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M(x) = q*x*(L-x)/2\n"
        "q := 2.8*tonf/m\nL := 6*m\nx := 1.5*m",
    )

    eval_cell(
        engine,
        "envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])",
    )

    assert engine.numeric_context.get("q").to("tonf/m").magnitude == pytest.approx(2.8)
    assert engine.numeric_context.get("x").to("m").magnitude == pytest.approx(1.5)


def test_envelope_requires_at_least_two_sweep_values():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="envelope requires at least two response series",
    ):
        eval_cell(engine, "envelope(M(x), x, 0, L, q=[5*kN/m])")


def test_envelope_rejects_sweep_parameter_absent_from_expression():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x\nq := 5*kN/m\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="envelope sweep parameter 'P' is not used in the plotted expression",
    ):
        eval_cell(engine, "envelope(M(x), x, 0, L, P=[1*kN, 2*kN])")


def test_envelope_rejects_incompatible_sweep_dimensions():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x^2\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="envelope sweep values have incompatible units",
    ):
        eval_cell(engine, "envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN])")


def test_envelope_rejects_incompatible_source_y_dimensions():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V(x) = q*(L-x)\nM(x) = q*(L-x)^2\nq := 5*kN/m\nL := 2*m",
    )
    with pytest.raises(
        EngEvaluationError,
        match="envelope series have incompatible y dimensions",
    ):
        eval_cell(engine, "envelope(V(x), M(x), x, 0, L)")


def test_envelope_rejects_mixed_moment_and_non_moment_same_dimension():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_A(x) = q*x^2\nR(x) = q*x^2\nq := 5*kN/m\nL := 2*m",
    )
    with pytest.raises(
        EngEvaluationError,
        match="envelope cannot mix moment and non-moment series on one axis",
    ):
        eval_cell(engine, "envelope(M_A(x), R(x), x, 0, L)")
```

Also add a compatible-unit normalization test where one source is defined from `N` and another from `kN`; assert both envelope series use the first source series unit after resolution.

- [ ] **Step 2: Run focused tests and identify any RED gaps**

Run:

```bash
pytest -q tests/test_envelope_engine.py tests/test_numeric_context.py tests/test_plot_sampling.py
```

Expected: envelope sweep/state tests should mostly pass if Task 3 correctly generalized the existing plot path. Any failures must be limited to message wording or shared helper names, not a second sampling implementation.

- [ ] **Step 3: Fix only shared semantic gaps**

If `_normalize_plot_series` still hardcodes `plot` in its error, change its signature to:

```python
@staticmethod
def _normalize_response_series(
    series: tuple[PlotSeries, ...],
    *,
    call_name: str,
) -> tuple[PlotSeries, ...]:
```

and use:

```python
raise EngEvaluationError(
    f"{call_name} series have incompatible y dimensions"
)
```

Similarly, the mixed-family validation in `_resolve_response_series()` must use:

```python
raise EngEvaluationError(
    f"{call_name} cannot mix moment and non-moment series on one axis"
)
```

Do not duplicate numeric sampling or state logic.

- [ ] **Step 4: Verify envelope + plot semantics GREEN**

Run:

```bash
pytest -q \
  tests/test_envelope_engine.py \
  tests/test_plot_engine.py \
  tests/test_numeric_context.py \
  tests/test_plot_sampling.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/engcalc_colab/engine.py tests/test_envelope_engine.py
git commit -m "test: close envelope units and state semantics"
```

---

### Task 5: Render emphasized envelopes with faint source curves

**Files:**
- Modify: `src/engcalc_colab/plotting.py`
- Create: `tests/test_envelope_plotting.py`
- Regression: `tests/test_plotting.py`

**Interfaces:**
- Consumes `PlotResult(kind="envelope")` where:
  - `series[0]` = algebraic maximum boundary;
  - `series[1]` = algebraic minimum boundary;
  - `source_series` = original normalized responses in source order.
- Produces:

```python
def _render_envelope(figure, axis, result: PlotResult) -> None: ...

def _envelope_characteristic_panel_text(result: PlotResult) -> str: ...
```

- `render_plot()` dispatch order:

```python
if result.kind == "envelope":
    _render_envelope(figure, axis, result)
elif len(result.series) == 1:
    _render_single_series(...)
else:
    _render_multi_series(...)
```

- No source-curve markers or source-curve annotations.
- Use Matplotlib's active color cycle; do not introduce a user-facing custom palette.

- [ ] **Step 1: Write renderer RED tests**

Create `tests/test_envelope_plotting.py`:

```python
import matplotlib
matplotlib.use("Agg")

from matplotlib.collections import PathCollection, PolyCollection

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def envelope_result():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_A(x) = q*x*(L-x)/2\n"
        "M_B(x) = -0.5*q*x*(L-x)/2\n"
        "M_C(x) = 0.6*q*x*(L-x)/2\n"
        "q := 8*kN/m\nL := 6*m",
    )
    return eval_cell(
        engine,
        "envelope(M_A(x), M_B(x), M_C(x), x, 0, L)",
    )[-1]


def test_envelope_render_draws_faint_sources_and_two_emphasized_boundaries():
    axis = render_plot(envelope_result()).axes[0]

    data_lines = [line for line in axis.lines if line.get_label() != "_zero"]
    # 3 faint source curves + 2 envelope boundaries + zero reference may all
    # live in axis.lines, so classify by alpha/linewidth rather than count only.
    faint = [
        line for line in axis.lines
        if line.get_alpha() is not None and line.get_alpha() <= 0.35
    ]
    emphasized = [
        line for line in axis.lines
        if line.get_label() in {"M_max(x)", "M_min(x)"}
    ]

    assert len(faint) == 3
    assert len(emphasized) == 2
    assert all(line.get_linewidth() < emphasized[0].get_linewidth() for line in faint)
    assert all(line.get_alpha() < 0.5 for line in faint)


def test_envelope_render_fills_between_boundaries_only():
    axis = render_plot(envelope_result()).axes[0]
    fills = [item for item in axis.collections if isinstance(item, PolyCollection)]
    assert len(fills) == 1


def test_envelope_source_curves_have_no_markers_or_callouts():
    figure = render_plot(envelope_result())
    axis = figure.axes[0]
    markers = [item for item in axis.collections if isinstance(item, PathCollection)]

    assert len(markers) <= 1
    assert len(axis.texts) == 0


def test_envelope_moment_axis_keeps_positive_down_and_engineering_units():
    axis = render_plot(envelope_result()).axes[0]
    assert axis.yaxis_inverted()
    assert axis.get_ylabel() == "M(x) [kN·m]"


def test_envelope_legend_contains_boundaries_not_every_source_curve():
    axis = render_plot(envelope_result()).axes[0]
    legend = axis.get_legend()
    assert legend is not None
    assert [text.get_text() for text in legend.get_texts()] == [
        "M_max(x)",
        "M_min(x)",
    ]


def test_envelope_characteristic_values_are_outside_data_area():
    figure = render_plot(envelope_result())
    axis = figure.axes[0]

    assert len(axis.texts) == 0
    panel = "\n".join(text.get_text() for text in figure.texts)
    assert "Envelope characteristic values" in panel
    assert "max =" in panel
    assert "min =" in panel
    assert "x =" in panel


def test_envelope_render_returns_closed_figure():
    import matplotlib.pyplot as plt
    figure = render_plot(envelope_result())
    assert figure.number not in plt.get_fignums()
```

When classifying zero-line labels, production should explicitly set `label="_zero"` on the envelope zero reference to make structural tests deterministic without affecting the legend.

- [ ] **Step 2: Run renderer tests and verify RED**

Run:

```bash
pytest -q tests/test_envelope_plotting.py tests/test_plotting.py
```

Expected: envelope tests fail because `render_plot()` currently treats the two envelope boundaries as a normal multi-series plot. Existing 0.4.0 plot renderer tests remain green.

- [ ] **Step 3: Implement the envelope renderer**

Add:

```python
def _envelope_characteristic_panel_text(result: PlotResult) -> str:
    maximum = result.series[0]
    minimum = result.series[1]
    maximum_values = [float(value.magnitude) for value in maximum.y_values]
    minimum_values = [float(value.magnitude) for value in minimum.y_values]
    maximum_index = max(range(len(maximum_values)), key=maximum_values.__getitem__)
    minimum_index = min(range(len(minimum_values)), key=minimum_values.__getitem__)
    moment = maximum.is_moment
    return "\n".join([
        "Envelope characteristic values",
        (
            f"max = {_quantity_label(maximum.y_values[maximum_index], moment=moment)}"
            f"    x = {_quantity_label(result.x_values[maximum_index])}"
        ),
        (
            f"min = {_quantity_label(minimum.y_values[minimum_index], moment=moment)}"
            f"    x = {_quantity_label(result.x_values[minimum_index])}"
        ),
    ])
```

Implement `_render_envelope` with this rendering order:

```python
def _render_envelope(figure, axis, result: PlotResult) -> None:
    x_values = [float(value.magnitude) for value in result.x_values]

    for source in result.source_series:
        source_y = [float(value.magnitude) for value in source.y_values]
        axis.plot(
            x_values,
            source_y,
            linewidth=1.0,
            alpha=0.22,
            label="_nolegend_",
            zorder=1,
        )

    maximum, minimum = result.series
    max_y = [float(value.magnitude) for value in maximum.y_values]
    min_y = [float(value.magnitude) for value in minimum.y_values]

    max_line = axis.plot(
        x_values,
        max_y,
        linewidth=2.4,
        label=maximum.display_label,
        zorder=4,
    )[0]
    min_line = axis.plot(
        x_values,
        min_y,
        linewidth=2.4,
        label=minimum.display_label,
        zorder=4,
    )[0]

    axis.fill_between(
        x_values,
        min_y,
        max_y,
        color=max_line.get_color(),
        alpha=0.10,
        zorder=2,
    )
    axis.axhline(
        0.0,
        linewidth=1.0,
        color=axis.spines["bottom"].get_edgecolor(),
        alpha=0.75,
        label="_zero",
        zorder=3,
    )
    axis.legend(handles=[max_line, min_line])

    moment = maximum.is_moment and minimum.is_moment
    if moment:
        axis.invert_yaxis()

    axis.set_xlabel(_axis_label(result.variable, result.x_values[0]))
    axis.set_ylabel(
        _axis_label(
            result.display_label,
            maximum.y_values[0],
            moment=moment,
        )
    )
    axis.set_title(f"{result.display_label} envelope", pad=10, fontweight="semibold")
    _style_axes(axis)
    axis.margins(x=0.02, y=0.12)

    figure.text(
        0.76,
        0.50,
        _envelope_characteristic_panel_text(result),
        ha="left",
        va="center",
        fontsize=8.5,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": axis.get_facecolor(),
            "edgecolor": axis.spines["bottom"].get_edgecolor(),
            "linewidth": 0.8,
            "alpha": 0.96,
        },
    )
    figure.tight_layout(rect=(0.0, 0.0, 0.73, 1.0))
```

Do not draw source scatter markers and do not call `_annotate_extreme` for envelope/source curves.

Update `render_plot()` with envelope-first dispatch.

- [ ] **Step 4: Verify envelope renderer GREEN and 0.4.0 renderer regression**

Run:

```bash
pytest -q tests/test_envelope_plotting.py tests/test_plotting.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/engcalc_colab/plotting.py tests/test_envelope_plotting.py
git commit -m "feat: render structural response envelopes"
```

---

### Task 6: Validate `%%eng` source order and end-to-end envelope acceptance

**Files:**
- Modify: `tests/test_magic.py`
- Modify: `tests/test_acceptance_native_plot.py`
- Modify: `src/engcalc_colab/magic.py` only if a failing test proves the current `PlotResult` dispatch is insufficient.

**Interfaces:**
- Consumes: `PlotResult(kind="envelope")` and existing `magic.py` behavior that flushes pending MathJax before any `PlotResult`, displays one Matplotlib figure, and resumes equation grouping.
- Produces no new magic syntax; `%%eng` remains unchanged.

- [ ] **Step 1: Add source-order integration test**

Append to `tests/test_magic.py`:

```python
def test_eng_magic_displays_one_envelope_figure_in_source_order(monkeypatch):
    import engcalc_colab.magic as magic_module
    from matplotlib.figure import Figure

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "A = q*L\n"
        "M_A(x) = q*x*(L-x)/2\n"
        "M_B(x) = -q*x*(L-x)/4\n"
        "q := 8*kN/m\nL := 6*m\n"
        "envelope(M_A(x), M_B(x), x, 0, L)\n"
        "B = 2*A",
    )

    assert [type(item) for item in displayed] == [Math, Figure, Math]
```

- [ ] **Step 2: Add end-to-end acceptance tests**

Append to `tests/test_acceptance_native_plot.py`:

```python
def test_acceptance_native_envelope_multiple_functions():
    engine = EngineeringEngine()
    results = eval_cell(
        engine,
        "M_A(x) = q*x*(L-x)/2\n"
        "M_B(x) = -q*x*(L-x)/4\n"
        "q := 8*kN/m\nL := 6*m\n"
        "envelope(M_A(x), M_B(x), x, 0, L)",
    )
    result = results[-1]
    figure = render_plot(result)
    axis = figure.axes[0]

    assert result.kind == "envelope"
    assert len(result.source_series) == 2
    assert len(result.series) == 2
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(36.0)
    assert result.series[1].y_values[100].to("kN*m").magnitude == pytest.approx(-18.0)
    assert axis.yaxis_inverted()


def test_acceptance_native_envelope_parameter_sweep():
    engine = EngineeringEngine()
    results = eval_cell(
        engine,
        "M(x) = q*x*(L-x)/2\n"
        "L := 6*m\n"
        "envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])",
    )
    result = results[-1]
    figure = render_plot(result)

    assert len(result.source_series) == 3
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(67.5)
    assert result.series[1].y_values[100].to("kN*m").magnitude == pytest.approx(22.5)
    assert figure.axes[0].get_legend() is not None
```

Reuse the file's existing imports/helpers rather than duplicating them if already present.

- [ ] **Step 3: Run integration tests**

Run:

```bash
pytest -q tests/test_magic.py tests/test_acceptance_native_plot.py
```

Expected: PASS without production changes to `magic.py`. If it fails because `magic.py` checks a more specific old transport shape, make the smallest generic `PlotResult` fix and rerun.

- [ ] **Step 4: Run the complete pre-release suite**

Run:

```bash
pytest -q
```

Expected: full suite PASS before any version bump.

- [ ] **Step 5: Commit**

```bash
git add tests/test_magic.py tests/test_acceptance_native_plot.py src/engcalc_colab/magic.py
git commit -m "test: validate envelopes in notebook flow"
```

If `magic.py` did not change, omit it from `git add`.

---

### Task 7: Release EngCalc 0.5.0 and verify the real wheel

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/engcalc_colab/__init__.py`
- Modify: `tests/test_packaging.py`
- Modify: `README.md`
- No new runtime dependencies.

**Interfaces:**
- Produces package/runtime `__version__ == "0.5.0"` and documentation for both envelope call forms.

- [ ] **Step 1: Change only version expectations and verify RED**

Update `tests/test_packaging.py` expectations from `0.4.0` to `0.5.0`, including both package metadata and runtime `engcalc_colab.__version__` assertions.

Run:

```bash
pytest -q tests/test_packaging.py
```

Expected: exactly the version assertions fail with `0.4.0 != 0.5.0`; dependency assertions remain green.

- [ ] **Step 2: Apply the minimal version bump**

In `pyproject.toml`:

```toml
version = "0.5.0"
```

In `src/engcalc_colab/__init__.py`:

```python
__version__ = "0.5.0"
```

Do not change runtime dependencies.

Run:

```bash
pytest -q tests/test_packaging.py
```

Expected: PASS.

- [ ] **Step 3: Document the 0.5.0 envelope workflow**

Add a README section headed similar to:

```markdown
## v0.5.0 engineering envelopes
```

It must include these exact canonical forms:

```text
envelope(M_1(x), M_2(x), M_3(x), x, 0, L)
```

and:

```text
envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
```

Document explicitly:

- envelope = sampled algebraic max/min, not absolute value;
- same 201 samples as plot;
- compatible units required;
- original source curves appear faintly behind the emphasized max/min boundaries;
- moment positive-down convention is preserved;
- sweep state is not mutated;
- one sweep parameter only;
- named/dictionary cases, exact intersections, absolute envelope, and multiple simultaneous sweeps remain deferred.

Do not remove historical 0.4.0 multi-series documentation.

- [ ] **Step 4: Run the full source suite from the release tree**

Run:

```bash
pytest -q
```

Expected: all tests PASS.

Record the exact count in the PR/release notes; do not predict the number in advance.

- [ ] **Step 5: Build the real 0.5.0 wheel**

Run:

```bash
rm -rf dist
python -m pip install --upgrade build
python -m build --wheel
ls -l dist/engcalc_colab-0.5.0-py3-none-any.whl
```

Expected: wheel exists at `dist/engcalc_colab-0.5.0-py3-none-any.whl`.

- [ ] **Step 6: Install the wheel into a clean virtual environment**

Run:

```bash
python -m venv /tmp/engcalc-v050-wheel
/tmp/engcalc-v050-wheel/bin/python -m pip install --upgrade pip
/tmp/engcalc-v050-wheel/bin/python -m pip install dist/engcalc_colab-0.5.0-py3-none-any.whl
```

Expected: clean install succeeds without source-tree editable installation.

- [ ] **Step 7: Smoke-test the installed wheel, not the checkout**

Run from `/tmp`:

```bash
cd /tmp
/tmp/engcalc-v050-wheel/bin/python - <<'PY'
from engcalc_colab import __version__
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot

assert __version__ == "0.5.0"

engine = EngineeringEngine()
cell = """
M_A(x) = q*x*(L-x)/2
M_B(x) = -q*x*(L-x)/4
q := 8*kN/m
L := 6*m
envelope(M_A(x), M_B(x), x, 0, L)
"""
result = [engine.evaluate(stmt) for stmt in parse_cell(cell)][-1]
assert result.kind == "envelope"
assert len(result.source_series) == 2
assert len(result.series) == 2
assert abs(result.series[0].y_values[100].to("kN*m").magnitude - 36.0) < 1e-12
assert abs(result.series[1].y_values[100].to("kN*m").magnitude + 18.0) < 1e-12

figure = render_plot(result)
axis = figure.axes[0]
assert axis.yaxis_inverted()
assert axis.get_legend() is not None
assert len(axis.get_legend().get_texts()) == 2
assert "Envelope characteristic values" in "\n".join(
    text.get_text() for text in figure.texts
)

source_lines = [
    line for line in axis.lines
    if line.get_alpha() is not None and line.get_alpha() <= 0.35
]
assert len(source_lines) == 2

print("EngCalc 0.5.0 envelope wheel smoke PASS")
PY
```

Expected output:

```text
EngCalc 0.5.0 envelope wheel smoke PASS
```

- [ ] **Step 8: Re-run the source suite after wheel verification**

Return to the repository and run:

```bash
pytest -q
```

Expected: full suite PASS again.

- [ ] **Step 9: Commit release metadata and documentation**

```bash
git add pyproject.toml src/engcalc_colab/__init__.py tests/test_packaging.py README.md
git commit -m "release: EngCalc 0.5.0 engineering envelopes"
```

- [ ] **Step 10: Final verification gate before PR/merge**

Run:

```bash
git status --short
git log --oneline --decorate -10
pytest -q
```

Expected:

- working tree clean;
- task commits visible;
- full test suite PASS.

Do not merge or tag until this gate and the installed-wheel smoke test both pass.

---

## Plan Self-Review

### Spec coverage

- Public multi-expression envelope syntax: Task 2 parser + Task 3 engine.
- One-parameter sweep envelope syntax: Task 2 parser + Task 4 engine semantics.
- Signed algebraic pointwise max/min: Task 3.
- Governing `argmax`/`argmin`: Task 3.
- Ordered source labels and retained normalized source series: Tasks 1 and 3.
- 201-point shared sampling: Tasks 3 and 4 reuse existing numeric path; acceptance tests assert length.
- Unit compatibility/normalization: Task 4.
- State non-mutation: Task 4.
- Minimum two source series: Tasks 3 and 4.
- Moment positive-down: Tasks 3 and 5.
- Faint original source curves: Task 5.
- No source markers/callouts: Task 5.
- Emphasized max/min with fill-between: Task 5.
- External characteristic values: Task 5.
- Notebook source order: Task 6.
- Existing 0.4.0 plotting parity: every task includes targeted regression; Task 6 full suite.
- 0.5.0 package/docs/wheel: Task 7.
- Security restrictions/no arbitrary Python syntax: Task 2.
- No parallel envelope engine/new dependencies/adaptive solver: architecture and Tasks 3/7 explicitly preserve these constraints.

### Placeholder scan

No `TBD`, `TODO`, "implement later", unspecified validation, or unnamed test steps remain. Deferred features are intentional product scope exclusions from the approved spec, not implementation placeholders.

### Type consistency

- `PlotResult.kind`, `source_series`, `source_labels`, `governing_max`, and `governing_min` are introduced once in Task 1 and used with the same names thereafter.
- `_ResolvedResponseSeries` and `_PlotEvaluation` are defined in Task 3 before any later task depends on them.
- Envelope displayed series order is consistently maximum first, minimum second.
- Governing indices consistently reference `source_series` / `source_labels` source order.
- `render_plot()` receives the same `PlotResult` transport used by normal plotting; no second renderer model appears.

## Execution Handoff

Plan implementation must start from an isolated execution branch/worktree based on the approved design branch or current `main` as appropriate, using the superpowers execution workflow. The design/spec is already approved; no additional brainstorming is required unless implementation reveals a material contradiction in the approved contract.
