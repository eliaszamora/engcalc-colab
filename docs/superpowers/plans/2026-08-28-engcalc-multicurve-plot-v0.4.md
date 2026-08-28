# EngCalc 0.4.0 Multi-curve `plot()` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend EngCalc's existing native `plot()` so one `%%eng` statement can either overlay several dimensionally compatible expressions or sweep one engineering function over several values of one parameter, while preserving the exact EngCalc 0.3.3 single-curve behavior.

**Architecture:** Keep the existing parser → symbolic/numeric engine → immutable plot transport → Matplotlib adapter → IPython magic separation. The parser gains a narrowly scoped `plot(..., parameter=[...])` grammar without enabling general Python lists or kwargs. `NumericContext` gains non-mutating expression evaluation and fixed sampling overrides. `PlotResult` becomes shared-x multi-series transport built from immutable `PlotSeries` records. The engine expands multi-expression/sweep requests into normalized series. `plotting.py` preserves the current 0.3.3 path for one series and adds a separate comparison path for 2+ series with lines, legend, extrema markers, and a characteristic-values panel outside the data area.

**Tech Stack:** Python 3.10+, SymPy >=1.13, Pint >=0.24, Matplotlib >=3.8, IPython notebook integration, pytest >=8.

**Spec:** `docs/superpowers/specs/2026-08-28-engcalc-multicurve-plot-v0.4-design.md`

## Global Constraints

- Base checkpoint is EngCalc 0.3.3, commit `81d743a14592412f7170306f3f6514e9f1b298c5`.
- Target release is exactly **0.4.0**.
- Existing `plot(expression, variable, start, end)` syntax and single-series rendering remain backward compatible.
- Existing 201-point deterministic sampling, dimensional-zero handling, unit labels, force·length moment unit order, positive-moment-down convention, smart extrema callouts, source ordering, and pyplot figure-closing behavior remain intact for one series.
- New positional multi-expression syntax is `plot(expr1, expr2, ..., variable, start, end)`; the final three positional arguments are always `variable, start, end`.
- New sweep syntax is `plot(expression, variable, start, end, parameter=[value1, value2, ...])`.
- Only one sweep parameter is accepted in 0.4.0.
- Sweep + multiple plotted expressions in the same call is rejected.
- Sweep list entries are complete numeric expressions such as `5*kN/m`; shorthand such as `[5, 10]*kN/m` is not supported.
- General Python lists, dictionaries, tuples, comprehensions, attribute access, subscripting, callbacks, and arbitrary keyword arguments remain unavailable.
- Sweep overrides and the plotting variable are local to evaluation and never mutate `NumericContext.values`.
- All series on one y-axis must be dimensionally compatible and are normalized to the first series' y unit.
- A multi-expression plot mixing moment-classified and non-moment-classified series is rejected.
- All-moment multi-series plots retain the existing positive-down y-axis convention.
- One series keeps the 0.3.3 translucent fill and smart in-plot extrema callouts.
- Two or more series use clean lines without fills, automatic legend, restrained extrema markers, and a figure-level characteristic-values panel outside the plotting data area.
- No arbitrary Matplotlib escape hatch, styling kwargs, dual y-axis, labeled dictionary cases, nested sweeps, or file export is introduced.
- Every implementation task follows RED → minimal GREEN → regression tests → commit.

---

### Task 1: Add the restricted sweep grammar and multi-series transport model

**Files:**
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/models.py`
- Modify: `tests/test_plot_parser.py`

**Interfaces:**
- Existing: `parse_cell(cell) -> list[ParsedStatement | ParsedNumericAssignment | ParsedHeading]`
- New transport: `PlotSeries(display_label, y_values, is_moment)`
- Revised transport: `PlotResult(statement, display_label, variable, x_values, series)`
- Backward compatibility: `PlotResult.y_values` remains readable only when exactly one series exists.

- [ ] **Step 1: Write failing parser/model tests**

Extend `tests/test_plot_parser.py` with tests equivalent to:

```python
import ast
import pytest

from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.models import PlotResult, PlotSeries
from engcalc_colab.parser import parse_cell


def test_plot_accepts_multiple_positional_expressions():
    statement = parse_cell("plot(M_D(x), M_L(x), x, 0, L)")[0]
    call = statement.expression.body
    assert call.func.id == "plot"
    assert len(call.args) == 5
    assert call.keywords == []


def test_plot_accepts_one_restricted_parameter_sweep_keyword():
    statement = parse_cell(
        "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])"
    )[0]
    call = statement.expression.body
    assert len(call.args) == 4
    assert len(call.keywords) == 1
    assert call.keywords[0].arg == "q"
    assert isinstance(call.keywords[0].value, ast.List)
    assert len(call.keywords[0].value.elts) == 2


def test_non_plot_keyword_arguments_remain_rejected():
    with pytest.raises(EngSyntaxError, match="keyword arguments are unsupported"):
        parse_cell("simplify(x, mode=[1])")


def test_plot_rejects_more_than_one_sweep_keyword():
    with pytest.raises(
        EngSyntaxError,
        match="plot accepts at most one sweep parameter",
    ):
        parse_cell("plot(M(x), x, 0, L, q=[1], P=[2])")


def test_plot_rejects_empty_or_non_list_sweep_values():
    with pytest.raises(EngSyntaxError, match="plot sweep list cannot be empty"):
        parse_cell("plot(M(x), x, 0, L, q=[])")
    with pytest.raises(EngSyntaxError, match="plot sweep values must be a list"):
        parse_cell("plot(M(x), x, 0, L, q=5*kN/m)")


def test_list_syntax_is_not_enabled_outside_plot_sweep():
    with pytest.raises(EngSyntaxError, match="unsupported syntax 'List'"):
        parse_cell("A = [1, 2]")


def test_plot_sweep_rejects_comprehensions_nested_lists_and_unpacking():
    invalid = [
        "plot(M(x), x, 0, L, q=[v for v in x])",
        "plot(M(x), x, 0, L, q=[[1], [2]])",
        "plot(M(x), x, 0, L, q=[*q_values])",
    ]
    for source in invalid:
        with pytest.raises(EngSyntaxError, match="unsupported"):
            parse_cell(source)


def test_plot_result_exposes_single_series_y_values_for_compatibility():
    statement = parse_cell("plot(M(x), x, 0, L)")[0]
    series = PlotSeries("M(x)", (1, 2), True)
    result = PlotResult(statement, "M(x)", "x", (0, 1), (series,))
    assert result.y_values == (1, 2)


def test_plot_result_does_not_fake_single_y_values_for_multi_series():
    statement = parse_cell("plot(A(x), B(x), x, 0, L)")[0]
    result = PlotResult(
        statement,
        "Comparison",
        "x",
        (0, 1),
        (
            PlotSeries("A(x)", (1, 2), False),
            PlotSeries("B(x)", (3, 4), False),
        ),
    )
    with pytest.raises(AttributeError, match="multi-series"):
        _ = result.y_values
```

Keep the existing tests that reserve the name `plot` and accept the original four-argument call.

- [ ] **Step 2: Verify RED**

Run:

```bash
pytest -q tests/test_plot_parser.py
```

Expected RED causes:
- the parser rejects `ast.keyword`/`ast.List`;
- `PlotSeries` does not exist;
- the current `PlotResult` still owns one `y_values` tuple directly.

- [ ] **Step 3: Implement immutable multi-series transport**

In `src/engcalc_colab/models.py`, replace the one-series storage with:

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

    @property
    def y_values(self) -> tuple[Any, ...]:
        if len(self.series) != 1:
            raise AttributeError("multi-series PlotResult has no single y_values")
        return self.series[0].y_values
```

The compatibility property is intentionally narrow: old single-series tests and consumers continue to work, but multi-series consumers must explicitly choose a series.

- [ ] **Step 4: Replace global AST-list enablement with call-aware validation**

Do **not** simply add `ast.List` and `ast.keyword` to `_ALLOWED_NODES` and accept them everywhere. Refactor `_validate_ast` into recursive validation so only a `plot` keyword may own one list.

Use a dedicated numeric-expression allowlist for sweep entries:

```python
_SWEEP_VALUE_NODES = (
    ast.BinOp,
    ast.UnaryOp,
    ast.Name,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.UAdd,
    ast.USub,
    ast.Load,
)
```

The call validation contract is:

```python
if isinstance(node, ast.Call):
    if not isinstance(node.func, ast.Name):
        ...
    if node.func.id.startswith("__"):
        ...

    if node.keywords:
        if node.func.id != "plot":
            raise EngSyntaxError(f"line {line_no}: keyword arguments are unsupported")
        if len(node.keywords) > 1:
            raise EngSyntaxError(
                f"line {line_no}: plot accepts at most one sweep parameter"
            )
        keyword_node = node.keywords[0]
        if keyword_node.arg is None:
            raise EngSyntaxError(
                f"line {line_no}: plot does not support keyword unpacking"
            )
        if (
            not _IDENTIFIER.fullmatch(keyword_node.arg)
            or keyword.iskeyword(keyword_node.arg)
            or keyword_node.arg in _RESERVED
        ):
            raise EngSyntaxError(
                f"line {line_no}: invalid plot sweep parameter '{keyword_node.arg}'"
            )
        if not isinstance(keyword_node.value, ast.List):
            raise EngSyntaxError(
                f"line {line_no}: plot sweep values must be a list"
            )
        if not keyword_node.value.elts:
            raise EngSyntaxError(
                f"line {line_no}: plot sweep list cannot be empty"
            )
```

Validate each sweep element recursively against `_SWEEP_VALUE_NODES`. Any nested `ast.List`, `ast.ListComp`, `ast.Starred`, `ast.Attribute`, `ast.Subscript`, `ast.Dict`, `ast.Tuple`, `ast.Call`, or other unapproved node inside a sweep list must raise a line-aware `unsupported plot sweep syntax '<NodeType>'` error.

All normal positional arguments still use the existing restricted expression validator. A list encountered anywhere except the one plot sweep keyword must continue to produce `unsupported syntax 'List'`.

- [ ] **Step 5: Verify GREEN plus parser regressions**

Run:

```bash
pytest -q tests/test_plot_parser.py tests/test_parser.py
```

Expected: all selected tests pass, including the old security tests for attributes, dunder calls, reserved targets, and ordinary keyword rejection.

- [ ] **Step 6: Commit Task 1**

```bash
git add src/engcalc_colab/parser.py src/engcalc_colab/models.py tests/test_plot_parser.py
git commit -m "feat: define restricted multi-series plot grammar"
```

---

### Task 2: Add non-mutating numeric sweep evaluation and fixed sampling overrides

**Files:**
- Modify: `src/engcalc_colab/numeric.py`
- Modify: `tests/test_numeric_context.py`
- Modify: `tests/test_plot_sampling.py`

**Interfaces:**
- New: `NumericContext.evaluate_expression(expression: ast.Expression) -> Quantity`
- Revised: `NumericContext.sample_symbolic(expression, variable, start, end, count=201, overrides=None)`
- Existing `assign()` delegates to the new non-mutating evaluator before persisting.

- [ ] **Step 1: Write failing tests for non-mutating numeric evaluation**

Add to `tests/test_numeric_context.py`:

```python
def test_evaluate_expression_returns_quantity_without_persisting_assignment():
    ctx = NumericContext()

    value = ctx.evaluate_expression(expr("5*kN/m"))

    assert value.to("kN/m").magnitude == pytest.approx(5.0)
    assert ctx.values == {}


def test_evaluate_expression_can_reference_existing_numeric_values_without_mutation():
    ctx = NumericContext()
    ctx.assign("q_ref", expr("5*kN/m"))
    before = dict(ctx.values)

    value = ctx.evaluate_expression(expr("2*q_ref"))

    assert value.to("kN/m").magnitude == pytest.approx(10.0)
    assert ctx.values == before
```

- [ ] **Step 2: Write failing sampling tests for fixed overrides**

Add to `tests/test_plot_sampling.py`:

```python
def test_sampling_merges_fixed_parameter_override_without_mutating_context():
    context = NumericContext()
    context.assign("q", ast.parse("2.8*tonf/m", mode="eval"))
    q, x = sp.symbols("q x")
    override = 5 * context.ureg.kN / context.ureg.m

    xs, ys = context.sample_symbolic(
        q*x,
        "x",
        0 * context.ureg.m,
        2 * context.ureg.m,
        count=201,
        overrides={"q": override},
    )

    assert ys[-1].to("kN").magnitude == pytest.approx(10.0)
    assert context.get("q").to("tonf/m").magnitude == pytest.approx(2.8)


def test_plot_variable_sample_wins_over_same_name_in_fixed_overrides():
    context = NumericContext()
    x = sp.Symbol("x")

    xs, ys = context.sample_symbolic(
        x,
        "x",
        0 * context.ureg.m,
        2 * context.ureg.m,
        count=3,
        overrides={"x": 99 * context.ureg.m},
    )

    assert [value.to("m").magnitude for value in ys] == pytest.approx([0, 1, 2])
```

Add `import ast` and `import pytest` to `tests/test_plot_sampling.py` as required.

- [ ] **Step 3: Verify RED**

Run:

```bash
pytest -q tests/test_numeric_context.py tests/test_plot_sampling.py
```

Expected RED:
- `NumericContext.evaluate_expression` is missing;
- `sample_symbolic` does not accept fixed overrides.

- [ ] **Step 4: Factor numeric assignment evaluation without changing semantics**

In `NumericContext`, extract the current `assign` evaluation path:

```python
def evaluate_expression(self, expression: ast.Expression):
    try:
        value = _NumericAstEvaluator(self).visit(expression.body)
        return self._as_quantity(value)
    except EngEvaluationError:
        raise
    except DimensionalityError as exc:
        raise EngEvaluationError("incompatible units") from exc
    except PintError as exc:
        raise EngEvaluationError(f"numeric unit evaluation failed: {exc}") from exc
    except Exception as exc:
        raise EngEvaluationError(f"numeric evaluation failed: {exc}") from exc


def assign(self, name: str, expression: ast.Expression):
    quantity = self.evaluate_expression(expression)
    self.values[name] = quantity
    return quantity
```

This is the same restricted `_NumericAstEvaluator`; it does not introduce Python evaluation or new syntax.

- [ ] **Step 5: Add fixed overrides to deterministic sampling**

Change the signature to:

```python
def sample_symbolic(
    self,
    expression,
    variable,
    start,
    end,
    count=201,
    overrides: dict[str, Any] | None = None,
):
```

Inside the sample loop, merge fixed overrides without mutating either caller data or `self.values`:

```python
fixed_overrides = dict(overrides or {})
...
for x_value in xs:
    sample_overrides = dict(fixed_overrides)
    sample_overrides[variable] = x_value
    _, y_value = self.evaluate_symbolic(
        expression,
        overrides=sample_overrides,
    )
```

Keep all existing within-series y-unit normalization and errors unchanged.

- [ ] **Step 6: Verify GREEN plus numeric regression**

Run:

```bash
pytest -q \
  tests/test_numeric_context.py \
  tests/test_numeric_engine.py \
  tests/test_plot_sampling.py
```

Expected: all selected tests pass and the stored `q`/`x` values are unchanged after override sampling.

- [ ] **Step 7: Commit Task 2**

```bash
git add src/engcalc_colab/numeric.py tests/test_numeric_context.py tests/test_plot_sampling.py
git commit -m "feat: add non-mutating plot sweep overrides"
```

---

### Task 3: Expand `plot()` into multi-expression and parameter-sweep series in the engine

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Modify: `tests/test_plot_engine.py`
- Modify: `tests/test_acceptance_native_plot.py`

**Interfaces:**
- `_Evaluator.visit_Call()` delegates `plot` to a focused plot-evaluation helper.
- `PlotResult.series` contains one or more unit-normalized `PlotSeries` records sharing one `x_values` tuple.
- Existing `PlotResult.y_values` compatibility property keeps old single-series acceptance checks valid.

- [ ] **Step 1: Write failing multi-expression engine tests**

Extend `tests/test_plot_engine.py`:

```python
import pytest


def test_plot_builds_multiple_expression_series_on_one_shared_grid():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_D(x) = q_D*x*(L-x)/2\n"
        "M_L(x) = q_L*x*(L-x)/2\n"
        "q_D := 8*kN/m\nq_L := 5*kN/m\nL := 6*m",
    )

    result = eval_cell(engine, "plot(M_D(x), M_L(x), x, 0, L)")[-1]

    assert isinstance(result, PlotResult)
    assert len(result.x_values) == 201
    assert len(result.series) == 2
    assert [series.display_label for series in result.series] == ["M_D(x)", "M_L(x)"]
    assert result.display_label == "M(x)"
    assert all(series.is_moment for series in result.series)
    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(36.0)
    assert result.series[1].y_values[100].to("kN*m").magnitude == pytest.approx(22.5)
```

At `x = 3 m`, `q*x*(L-x)/2` gives `4.5*q`, hence 36 and 22.5 kN·m for 8 and 5 kN/m respectively.

- [ ] **Step 2: Write failing parameter-sweep tests**

Add:

```python
def test_plot_parameter_sweep_builds_one_series_per_value():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nL := 6*m")

    result = eval_cell(
        engine,
        "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])",
    )[-1]

    assert result.display_label == "M(x)"
    assert len(result.series) == 3
    assert all(series.is_moment for series in result.series)
    assert [
        series.y_values[100].to("kN*m").magnitude
        for series in result.series
    ] == pytest.approx([22.5, 45.0, 67.5])
    assert all("q =" in series.display_label for series in result.series)


def test_plot_sweep_does_not_mutate_existing_parameter_or_x_value():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M(x) = q*x*(L-x)/2\n"
        "q := 2.8*tonf/m\nL := 6*m\nx := 1.5*m",
    )

    eval_cell(engine, "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])")

    assert engine.numeric_context.get("q").to("tonf/m").magnitude == pytest.approx(2.8)
    assert engine.numeric_context.get("x").to("m").magnitude == pytest.approx(1.5)
```

- [ ] **Step 3: Write failing validation tests**

Add cases equivalent to:

```python
def test_plot_rejects_sweep_parameter_absent_from_expanded_expression():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x\nq := 5*kN/m\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="plot sweep parameter 'P' is not used in the plotted expression",
    ):
        eval_cell(engine, "plot(M(x), x, 0, L, P=[1*kN, 2*kN])")


def test_plot_rejects_incompatible_sweep_value_dimensions():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x^2\nL := 2*m")
    with pytest.raises(
        EngEvaluationError,
        match="plot sweep values have incompatible units",
    ):
        eval_cell(engine, "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN])")


def test_plot_rejects_multiple_expressions_with_sweep():
    engine = EngineeringEngine()
    with pytest.raises(
        EngEvaluationError,
        match="plot parameter sweep requires exactly one expression",
    ):
        eval_cell(engine, "plot(q*x, q*x^2, x, 0, 2, q=[1, 2])")


def test_plot_rejects_series_with_incompatible_y_dimensions():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "V(x) = q*(L-x)\nM(x) = q*(L-x)^2\nq := 5*kN/m\nL := 2*m",
    )
    with pytest.raises(
        EngEvaluationError,
        match="plot series have incompatible y dimensions",
    ):
        eval_cell(engine, "plot(V(x), M(x), x, 0, L)")


def test_plot_rejects_mixed_moment_and_non_moment_series_even_with_same_dimensions():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_A(x) = q*x^2\nR(x) = q*x^2\nq := 5*kN/m\nL := 2*m",
    )
    with pytest.raises(
        EngEvaluationError,
        match="plot cannot mix moment and non-moment series on one axis",
    ):
        eval_cell(engine, "plot(M_A(x), R(x), x, 0, L)")
```

Update the old arity test so a call with fewer than four positional arguments expects:

```text
plot expects at least 4 positional arguments: expression[, ...], variable, start, end
```

The existing non-identifier variable and `plot must be a standalone statement` tests remain.

- [ ] **Step 4: Verify RED**

Run:

```bash
pytest -q tests/test_plot_engine.py tests/test_acceptance_native_plot.py
```

Expected RED:
- current evaluator requires exactly four arguments;
- current `PlotResult` construction has no series expansion;
- sweep keyword values are not numerically evaluated;
- no cross-series normalization/classification exists.

- [ ] **Step 5: Refactor current plot handling into focused engine helpers**

In `engine.py`, import `re`, `DimensionalityError`, and `PlotSeries`.

Keep the current public evaluator flow, but make the `plot` branch delegate instead of embedding all logic in `visit_Call()`:

```python
if name == "plot":
    return self._evaluate_plot_call(node)
```

Implement helper methods on `_Evaluator` with these responsibilities:

```python
def _evaluate_plot_call(self, node: ast.Call): ...
def _plot_display_label(self, expression_node, symbolic_expression, variable): ...
def _is_moment_label(self, label: str) -> bool: ...
def _common_plot_label(self, labels: list[str], variable: str) -> str: ...
def _normalize_plot_series_units(self, series: list[PlotSeries]) -> tuple[PlotSeries, ...]: ...
def _format_sweep_label(self, name: str, quantity) -> str: ...
```

Use the existing moment naming convention regex:

```python
_MOMENT_LABEL = re.compile(r"^M(?:_[A-Za-z0-9]+|[0-9]+)?\(")
```

Use a common-family regex for labels such as `M_D(x)` / `M_L(x)` and `V_1(x)` / `V_2(x)`. If all recognized labels have the same family prefix and variable, return `<family>(<variable>)`; otherwise return `"Comparison"`.

- [ ] **Step 6: Parse the positional plot shape deterministically**

Inside `_evaluate_plot_call`:

```python
if len(node.args) < 4:
    raise EngEvaluationError(
        "plot expects at least 4 positional arguments: "
        "expression[, ...], variable, start, end"
    )

expression_nodes = node.args[:-3]
variable_node, start_node, end_node = node.args[-3:]

if not expression_nodes:
    raise EngEvaluationError("plot requires at least one expression")
if not isinstance(variable_node, ast.Name):
    raise EngEvaluationError("plot variable must be a symbolic identifier")
if node.keywords and len(expression_nodes) != 1:
    raise EngEvaluationError(
        "plot parameter sweep requires exactly one expression"
    )
```

Resolve and normalize `start`/`end` once using the existing `NumericContext` methods. Every resulting series uses the same domain and 201-point x grid.

- [ ] **Step 7: Implement ordinary multi-expression expansion**

For each positional expression:

1. call `self.visit(expression_node)` to obtain the expanded SymPy expression;
2. derive its source-facing display label exactly as the existing one-series code does for user functions;
3. call `sample_symbolic(..., count=201)`;
4. create `PlotSeries(display_label, y_values, is_moment)`;
5. keep the first returned `x_values` as the shared grid and assert subsequent grids are identical by construction.

After all series exist:

1. normalize every ordinate to the first series' y unit;
2. if conversion raises `DimensionalityError`, raise `EngEvaluationError("plot series have incompatible y dimensions")`;
3. if `len({series.is_moment for series in series_list}) > 1`, raise `EngEvaluationError("plot cannot mix moment and non-moment series on one axis")`;
4. build the plot-level display label from the common-family helper.

- [ ] **Step 8: Implement one-parameter sweep expansion**

For the one allowed keyword:

```python
sweep_keyword = node.keywords[0]
parameter_name = sweep_keyword.arg
symbolic_expression = self.visit(expression_nodes[0])
parameter_symbol = self.engine.resolve_symbol(parameter_name)

if parameter_symbol not in sp.sympify(symbolic_expression).free_symbols:
    raise EngEvaluationError(
        f"plot sweep parameter '{parameter_name}' is not used in the plotted expression"
    )
```

Evaluate each list element without storing it:

```python
sweep_values = [
    self.engine.numeric_context.evaluate_expression(ast.Expression(body=item))
    for item in sweep_keyword.value.elts
]
```

Choose the compatibility unit as:
- the currently stored parameter unit if that numeric value exists;
- otherwise the first sweep value's unit.

Convert every sweep value to that unit. Any failure becomes:

```text
plot sweep values have incompatible units
```

For each normalized sweep value call:

```python
x_values, y_values = self.engine.numeric_context.sample_symbolic(
    symbolic_expression,
    variable,
    start_quantity,
    end_quantity,
    count=201,
    overrides={parameter_name: sweep_value},
)
```

Create one `PlotSeries` per value. The plot-level `display_label` is the original expression/function label; the series label is `<parameter> = <compact quantity>`.

Use Pint's abbreviated pretty unit formatting (`~P`) and a compact numeric representation so labels are readable, e.g. `q = 5 kN/m`, without changing EngCalc's stored values.

- [ ] **Step 9: Build the revised `PlotResult` in `EngineeringEngine.evaluate`**

Change `plot_evaluation` from the old four-tuple to data matching the revised transport:

```python
display_label, variable, x_values, series = evaluator.plot_evaluation
return PlotResult(
    statement=statement,
    display_label=display_label,
    variable=variable,
    x_values=x_values,
    series=series,
)
```

Do not mutate symbolic namespace/functions or numeric values while producing a plot.

- [ ] **Step 10: Add end-to-end transport acceptance cases**

Extend `tests/test_acceptance_native_plot.py` while retaining the existing V/M one-curve test:

```python
def test_multicurve_plot_end_to_end():
    engine = EngineeringEngine()
    cell = """
M_D(x) = q_D*x*(L-x)/2
M_L(x) = q_L*x*(L-x)/2
q_D := 8*kN/m
q_L := 5*kN/m
L := 6*m
plot(M_D(x), M_L(x), x, 0, L)
"""
    result = [
        engine.evaluate(stmt) for stmt in parse_cell(cell)
    ][-1]
    assert len(result.series) == 2
    assert len(result.x_values) == 201
    assert result.display_label == "M(x)"


def test_parameter_sweep_plot_end_to_end():
    engine = EngineeringEngine()
    cell = """
M(x) = q*x*(L-x)/2
L := 6*m
plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
"""
    result = [
        engine.evaluate(stmt) for stmt in parse_cell(cell)
    ][-1]
    assert len(result.series) == 3
    assert result.series[-1].y_values[100].to("kN*m").magnitude == pytest.approx(67.5)
```

Add `import pytest` to that file.

- [ ] **Step 11: Verify GREEN plus plot-engine regression**

Run:

```bash
pytest -q \
  tests/test_plot_parser.py \
  tests/test_numeric_context.py \
  tests/test_plot_sampling.py \
  tests/test_plot_engine.py \
  tests/test_acceptance_native_plot.py
```

Expected: all selected tests pass, including the old one-series `result.y_values` assertions through the compatibility property.

- [ ] **Step 12: Commit Task 3**

```bash
git add src/engcalc_colab/engine.py tests/test_plot_engine.py tests/test_acceptance_native_plot.py
git commit -m "feat: evaluate multi-series and swept plots"
```

---

### Task 4: Render readable multi-series structural comparisons without annotation collisions

**Files:**
- Modify: `src/engcalc_colab/plotting.py`
- Modify: `tests/test_plotting.py`

**Interfaces:**
- Existing: `render_plot(result: PlotResult) -> matplotlib.figure.Figure`
- Single-series path remains compatible with 0.3.3.
- Multi-series path renders one figure with N data lines, one zero reference, automatic legend, extrema markers, and one figure-level characteristic-values panel.

- [ ] **Step 1: Add reusable multi-series test fixtures**

Add helpers to `tests/test_plotting.py`:

```python
def multi_moment_plot_result():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "M_D(x) = q_D*x*(L-x)/2\n"
        "M_L(x) = q_L*x*(L-x)/2\n"
        "q_D := 8*kN/m\nq_L := 5*kN/m\nL := 6*m",
    )
    return eval_cell(engine, "plot(M_D(x), M_L(x), x, 0, L)")[-1]


def sweep_moment_plot_result():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = q*x*(L-x)/2\nL := 6*m")
    return eval_cell(
        engine,
        "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])",
    )[-1]
```

- [ ] **Step 2: Write failing visual-structure tests**

Import `PolyCollection` alongside `PathCollection`, then add:

```python
def test_multiseries_render_uses_lines_legend_and_no_area_fills():
    figure = render_plot(multi_moment_plot_result())
    axis = figure.axes[0]

    # two data lines plus the horizontal zero reference
    assert len(axis.lines) == 3
    assert axis.get_legend() is not None
    assert [text.get_text() for text in axis.get_legend().get_texts()] == [
        "M_D(x)",
        "M_L(x)",
    ]
    assert not any(
        isinstance(collection, PolyCollection)
        for collection in axis.collections
    )


def test_multiseries_moment_axis_keeps_positive_down_convention():
    axis = render_plot(multi_moment_plot_result()).axes[0]
    assert axis.yaxis_inverted()
    assert axis.get_ylabel() == "M(x) [kN·m]"


def test_multiseries_uses_one_restrained_extrema_marker_collection_per_series():
    axis = render_plot(sweep_moment_plot_result()).axes[0]
    markers = [
        item for item in axis.collections if isinstance(item, PathCollection)
    ]
    assert len(markers) == 3
    assert all(len(marker.get_offsets()) in (1, 2) for marker in markers)
    assert all(max(marker.get_sizes()) <= 28 for marker in markers)


def test_multiseries_moves_characteristic_values_outside_data_area():
    figure = render_plot(sweep_moment_plot_result())
    axis = figure.axes[0]

    # No 0.3.3 boxed extrema annotations are placed over the data curves.
    assert axis.texts == []

    panel_text = "\n".join(text.get_text() for text in figure.texts)
    assert "Characteristic values" in panel_text
    assert "q = 5" in panel_text
    assert "q = 10" in panel_text
    assert "q = 15" in panel_text
    assert "max =" in panel_text
    assert "min =" in panel_text
    assert "x =" in panel_text
```

All current single-series plotting tests stay in place unchanged.

- [ ] **Step 3: Verify RED**

Run:

```bash
pytest -q tests/test_plotting.py
```

Expected RED: current `render_plot` accesses one `result.y_values`, draws one fill, has no legend, and creates in-axis callouts.

- [ ] **Step 4: Split rendering into explicit single-series and multi-series paths**

Keep `render_plot` as the public entrypoint:

```python
def render_plot(result: PlotResult):
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots()
    if len(result.series) == 1:
        _render_single_series(figure, axis, result)
    else:
        _render_multi_series(figure, axis, result)

    plt.close(figure)
    return figure
```

Move the current 0.3.3 implementation into `_render_single_series` with the smallest possible edits. It must preserve:
- line width and Matplotlib color cycle;
- translucent `fill_between`;
- zero line;
- deduplicated endpoint/extrema marker collection;
- current `_annotate_extreme` callouts and anti-overlap placement;
- moment positive-down inversion;
- force·length unit display;
- title, grid, margins, hidden top/right spines, and layout.

Use `result.series[0].is_moment` as the source of orientation instead of re-inferring it from the plot-level label.

- [ ] **Step 5: Implement the multi-series line/legend path**

For each `PlotSeries`:

```python
line = axis.plot(
    x_values,
    [float(value.magnitude) for value in series.y_values],
    linewidth=2.0,
    label=series.display_label,
    zorder=3,
)[0]
```

Do **not** call `fill_between` in the multi-series path.

After all data lines:
- add one horizontal zero line;
- call `axis.legend()`;
- invert y only when all series have `is_moment=True` (the engine already rejects a mixed classification);
- apply the existing grid/spine presentation.

- [ ] **Step 6: Add one extrema marker collection per series**

For each series:

1. calculate sampled max/min indices with `_extreme_indices`;
2. deduplicate if max and min coincide;
3. call `axis.scatter` once for that series using its line color;
4. use restrained size no larger than 28;
5. do not add endpoint markers unless an endpoint is itself a max/min in the multi-series path.

This keeps series/color association while avoiding the visual density of the single-diagram endpoint treatment.

- [ ] **Step 7: Add the figure-level characteristic-values panel**

Create a pure text builder so panel content can be tested independently:

```python
def _characteristic_panel_text(result: PlotResult) -> str:
    lines = ["Characteristic values"]
    for series in result.series:
        values = [float(value.magnitude) for value in series.y_values]
        maximum_index, minimum_index = _extreme_indices(values)
        lines.extend([
            series.display_label,
            (
                "max = "
                f"{_quantity_label(series.y_values[maximum_index], moment=series.is_moment)}"
                "    x = "
                f"{_quantity_label(result.x_values[maximum_index])}"
            ),
            (
                "min = "
                f"{_quantity_label(series.y_values[minimum_index], moment=series.is_moment)}"
                "    x = "
                f"{_quantity_label(result.x_values[minimum_index])}"
            ),
            "",
        ])
    return "\n".join(lines).rstrip()
```

Render it with `figure.text(...)`, not `axis.text(...)`, so it is outside the plotting data area. Reserve space using a multi-series-specific layout rectangle, for example:

```python
figure.text(
    0.76,
    0.50,
    _characteristic_panel_text(result),
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

The exact rectangle may be adjusted during GREEN implementation if Matplotlib emits layout warnings, but the invariant is fixed: the panel is figure-level and must not overlap the data axes.

- [ ] **Step 8: Make axis unit formatting use plot-level moment metadata**

Allow `_axis_label` to receive an explicit `moment` flag so a normalized comparison title such as `M(x)` or `Comparison` does not accidentally control unit ordering:

```python
def _axis_label(name: str, quantity, *, moment: bool = False) -> str:
    unit = _unit_label(quantity, moment=moment)
    return name if not unit else f"{name} [{unit}]"
```

For y-axis labeling use:

```python
moment = all(series.is_moment for series in result.series)
axis.set_ylabel(
    _axis_label(
        result.display_label,
        result.series[0].y_values[0],
        moment=moment,
    )
)
```

The x-axis remains non-moment.

- [ ] **Step 9: Verify GREEN and single-series visual regression**

Run:

```bash
pytest -q tests/test_plotting.py
```

Expected:
- every existing 0.3.3 single-series test still passes unchanged;
- all new multi-series tests pass;
- returned figures are still closed from pyplot's registry.

- [ ] **Step 10: Commit Task 4**

```bash
git add src/engcalc_colab/plotting.py tests/test_plotting.py
git commit -m "feat: render readable multi-series structural plots"
```

---

### Task 5: Integrate notebook behavior, document 0.4.0, bump version, and verify the release wheel

**Files:**
- Modify: `tests/test_magic.py`
- Modify: `tests/test_acceptance_native_plot.py`
- Modify: `tests/test_parser.py`
- Modify: `tests/test_packaging.py`
- Modify: `src/engcalc_colab/__init__.py`
- Modify: `pyproject.toml`
- Modify: `README.md`

**Interfaces:**
- One `plot(...)` statement still yields exactly one displayed `matplotlib.figure.Figure`.
- Package/runtime version becomes `0.4.0`.
- README documents both additive plot syntaxes and the multi-series visual policy.

- [ ] **Step 1: Add a notebook sequencing test for one multi-series figure**

Extend `tests/test_magic.py`:

```python
def test_eng_magic_displays_one_figure_for_parameter_sweep_in_source_order(monkeypatch):
    import engcalc_colab.magic as magic_module
    from matplotlib.figure import Figure

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "A = q*L\n"
        "M(x) = q*x*(L-x)/2\n"
        "L := 6*m\n"
        "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])\n"
        "B = 2*A",
    )

    assert [type(item) for item in displayed] == [Math, Figure, Math]
```

No production change in `magic.py` should be necessary unless this test exposes an actual sequencing assumption: `PlotResult` remains one output object.

- [ ] **Step 2: Verify notebook integration GREEN before release versioning**

Run:

```bash
pytest -q tests/test_magic.py tests/test_acceptance_native_plot.py
```

Expected: all tests pass using the multi-series `PlotResult` as one figure-producing statement.

- [ ] **Step 3: Change version assertions first and verify release RED**

In `tests/test_parser.py` change:

```python
assert __version__ == "0.4.0"
```

In `tests/test_packaging.py`, rename the version test and change its assertion to:

```python
def test_pyproject_version_is_0_4_0():
    assert _project_metadata()["version"] == "0.4.0"
```

Run:

```bash
pytest -q tests/test_parser.py tests/test_packaging.py
```

Expected: exactly the version assertions fail because production still reports 0.3.3. Any unrelated failure must be fixed before proceeding.

- [ ] **Step 4: Bump package and runtime version to 0.4.0**

In `pyproject.toml`:

```toml
version = "0.4.0"
```

In `src/engcalc_colab/__init__.py`:

```python
__version__ = "0.4.0"
```

Do not change runtime dependencies; SymPy, Pint, and Matplotlib remain sufficient.

- [ ] **Step 5: Update the README with the exact 0.4.0 user contract**

Add a `v0.4.0 multi-series plotting` section before the historical 0.3.0 section and update the plotting command reference.

Document these canonical examples exactly:

```text
# Several compatible functions on one axis
plot(M_D(x), M_L(x), x, 0, L)

# One function swept over one parameter
plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
```

Document:
- final three positional arguments are `variable, start, end`;
- sweep uses one keyword and a non-empty list of complete numeric expressions;
- sweep does not persist/overwrite the parameter value;
- multiple y series must have compatible dimensions;
- all-moment comparisons keep positive moment downward;
- one series keeps fill + in-plot extrema callouts;
- multi-series comparisons use line-only rendering, legend, extrema markers, and an external characteristic-values panel;
- one sweep parameter only in 0.4.0;
- arbitrary plot styling, labeled dictionaries, multi-parameter sweeps, and dual axes are not supported.

Update stale language that says multiple curves/keywords are universally unsupported. Preserve the 0.3.0 historical description as historical context where useful.

- [ ] **Step 6: Run the complete source-tree regression suite**

Run:

```bash
python -m pip install -e '.[dev]'
pytest -q
```

Expected: every existing and new test passes. Record the final pass count in the release/PR summary rather than hard-coding a count in production docs.

- [ ] **Step 7: Build the actual 0.4.0 wheel**

From a clean working tree after the tests:

```bash
rm -rf dist .venv-release
python -m pip wheel . --no-deps -w dist
```

Expected artifact:

```text
dist/engcalc_colab-0.4.0-py3-none-any.whl
```

If the wheel name differs only because of standard wheel tag normalization, use the actual generated filename in the next command; do not rename package metadata manually.

- [ ] **Step 8: Install and smoke-test the real wheel in a fresh environment**

Run:

```bash
python -m venv .venv-release
.venv-release/bin/python -m pip install --upgrade pip
.venv-release/bin/python -m pip install dist/engcalc_colab-0.4.0-py3-none-any.whl pytest
```

Then run this smoke script with the fresh interpreter:

```bash
.venv-release/bin/python - <<'PY'
from engcalc_colab import __version__
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot

assert __version__ == "0.4.0"

engine = EngineeringEngine()
cell = """
M(x) = q*x*(L-x)/2
L := 6*m
plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
"""
result = [engine.evaluate(stmt) for stmt in parse_cell(cell)][-1]
assert len(result.series) == 3
assert result.series[-1].y_values[100].to("kN*m").magnitude == 67.5

figure = render_plot(result)
axis = figure.axes[0]
assert axis.yaxis_inverted()
assert axis.get_legend() is not None
assert len(axis.get_legend().get_texts()) == 3
assert "Characteristic values" in "\n".join(
    text.get_text() for text in figure.texts
)

print("EngCalc 0.4.0 wheel smoke PASS")
PY
```

Expected output:

```text
EngCalc 0.4.0 wheel smoke PASS
```

On Windows, use `.venv-release\Scripts\python.exe` in place of `.venv-release/bin/python`; the test logic is identical.

- [ ] **Step 9: Re-run the source suite after wheel verification**

Run:

```bash
pytest -q
```

Expected: all tests still pass. This detects accidental local-file changes made during release verification.

- [ ] **Step 10: Commit Task 5**

```bash
git add \
  src/engcalc_colab/__init__.py \
  pyproject.toml \
  README.md \
  tests/test_magic.py \
  tests/test_acceptance_native_plot.py \
  tests/test_parser.py \
  tests/test_packaging.py
git commit -m "release: prepare EngCalc 0.4.0 multi-series plots"
```

Do not tag the release until the implementation branch has passed review and its final integration strategy is known; a squash merge would otherwise leave a tag pointing at a non-main commit.

---

## Final verification checklist

Before declaring EngCalc 0.4.0 complete, verify all of the following in one clean checkout of the implementation head:

- [ ] `plot(M(x), x, 0, L)` still gives the EngCalc 0.3.3 single-series presentation.
- [ ] `plot(M_D(x), M_L(x), x, 0, L)` gives exactly one figure with two compatible series and a legend.
- [ ] `plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])` gives exactly one figure with three series.
- [ ] Sweep evaluation creates no persistent `q` assignment when none existed and does not overwrite an existing `q` assignment.
- [ ] Existing numeric `x` values remain unchanged by plotting.
- [ ] Multi-series y dimensions are normalized or rejected; no misleading mixed-unit y-axis is produced.
- [ ] Mixed moment/non-moment comparison is rejected.
- [ ] All-moment comparison uses positive moment downward.
- [ ] Multi-series figures have no area fills and no overlapping in-axis max/min boxes.
- [ ] Characteristic max/min values and x locations appear in the external figure panel for every series.
- [ ] Ordinary non-plot keyword arguments and collection syntax remain rejected by the restricted parser.
- [ ] Existing symbolic, unit, MathJax, config, headings, and one-curve tests remain green.
- [ ] `pytest -q` passes from the source tree.
- [ ] A freshly installed `engcalc_colab-0.4.0` wheel passes the dedicated smoke test.
- [ ] `pyproject.toml` and `engcalc_colab.__version__` both report `0.4.0`.

## Self-review

### Spec coverage

- Multiple positional expressions: Task 1 parser + Task 3 engine + Task 4 renderer.
- One-parameter sweep: Tasks 1–3.
- Restricted/safe list grammar: Task 1.
- Non-mutating q/x overrides: Task 2 and Task 3 tests.
- Shared x grid and 201 samples: Tasks 2–3.
- Cross-series unit compatibility: Task 3.
- Moment-positive-down multi-series behavior: Tasks 3–4.
- Legend and no-fill comparison presentation: Task 4.
- Characteristic-values panel outside data area: Task 4.
- Single-series 0.3.3 preservation: compatibility model + all current plotting regression tests.
- One figure in source order: Task 5 magic test.
- Version/docs/wheel release gate: Task 5.

### Placeholder scan

No implementation step contains `TBD`, `TODO`, a placeholder owner/repository, or an unspecified target version. The repository, branch-independent paths, exact public syntax, error contracts, test commands, and release version are concrete.

### Type/interface consistency

- `parse_cell` still emits the existing statement models; `plot` remains an ordinary restricted call at the parser boundary.
- `NumericContext.evaluate_expression` returns a Pint quantity without persistence; `assign` persists exactly once after that evaluation.
- `sample_symbolic` continues returning `(x_values, y_values)` for one symbolic expression and only adds an optional fixed-overrides input.
- `PlotSeries.y_values` is one normalized ordinate tuple; `PlotResult.x_values` is shared across all series.
- `PlotResult.y_values` exists only as a backward-compatible single-series property.
- `EngineeringEngine.evaluate` still returns one `PlotResult` for one plot statement.
- `render_plot` still consumes one `PlotResult` and returns one closed Matplotlib `Figure`.
- `EngMagics.eng()` therefore requires no architectural sequencing change for multiple series.
