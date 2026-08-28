# EngCalc 0.3.0 Native `plot()` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a native `plot(expression, variable, start, end)` command to `%%eng` that reuses EngCalc's symbolic formulas and Pint-backed numerical state to create one unit-aware Matplotlib figure without redefining data in Python.

**Architecture:** Keep plotting side effects outside the symbolic engine. The parser accepts `plot` as a restricted EngCalc builtin; the engine returns an immutable `PlotResult` containing normalized Pint samples and display metadata; `src/engcalc_colab/plotting.py` converts that result into a closed Matplotlib `Figure`; `EngMagics.eng()` flushes pending MathJax equations before displaying the figure and then resumes source-order processing.

**Tech Stack:** Python 3.10+, SymPy >=1.13, Pint >=0.24, Matplotlib, IPython, pytest >=8.

**Spec:** `docs/superpowers/specs/2026-08-27-engcalc-native-plot-design.md`

## Global Constraints

- Public syntax is exactly `plot(expression, variable, start, end)` with four positional arguments.
- Keyword arguments remain unsupported.
- One curve and one Matplotlib figure are produced per `plot(...)` statement.
- Sampling count is exactly 201 points including both endpoints.
- Existing EngCalc symbolic and numerical state is reused; no Python-variable redefinition is required.
- A numeric value already stored for the plotting variable is overridden locally during sampling and must not be mutated.
- An exact dimensionless zero bound may be promoted to the compatible dimensional unit of the other bound.
- Bounds with incompatible dimensions and `end <= start` are rejected with concise line-aware EngCalc errors.
- The y-axis unit is fixed from the first sample; all later samples must convert compatibly to it.
- Matplotlib inherits the user's active `rcParams`; EngCalc adds no custom theme or hard-coded color.
- `plot(...)` itself produces no MathJax equation row; its output is only the figure.
- Existing notebooks without `plot(...)` must render identically to EngCalc 0.2.9.
- Matplotlib is a direct runtime dependency in 0.3.0.
- Target release version is exactly `0.3.0`.
- Multiple curves, style kwargs, target plot units, extrema/root annotations, `piecewise`, discontinuities, fills, legends, image export and arbitrary Matplotlib access are out of scope.

---

### Task 1: Reserve `plot` and introduce the transport model

**Files:**
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/models.py`
- Create: `tests/test_plot_parser.py`

**Interfaces:**
- Consumes: existing `parse_cell()` restricted AST and `ParsedStatement`.
- Produces: `PlotResult(statement, display_label, variable, x_values, y_values)` and parser recognition of `plot` as a reserved builtin name.

- [ ] **Step 1: Write failing parser/model tests**

Create `tests/test_plot_parser.py`:

```python
from engcalc_colab.models import PlotResult
from engcalc_colab.parser import parse_cell
from engcalc_colab.errors import EngSyntaxError


def test_plot_call_is_accepted_by_restricted_parser():
    statement = parse_cell("plot(M(x), x, 0, L)")[0]
    assert statement.target is None
    assert statement.expression.body.func.id == "plot"
    assert len(statement.expression.body.args) == 4


def test_plot_name_is_reserved_as_assignment_target():
    try:
        parse_cell("plot = 3")
    except EngSyntaxError as exc:
        assert "reserved identifier 'plot'" in str(exc)
    else:
        raise AssertionError("expected EngSyntaxError")


def test_plot_result_is_immutable_transport_data():
    statement = parse_cell("plot(M(x), x, 0, L)")[0]
    result = PlotResult(
        statement=statement,
        display_label="M(x)",
        variable="x",
        x_values=(1,),
        y_values=(2,),
    )
    assert result.display_label == "M(x)"
    assert result.variable == "x"
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
pytest -q tests/test_plot_parser.py
```

Expected: collection/import failure because `PlotResult` does not exist, and/or parser rejection because `plot` is not reserved/implemented.

- [ ] **Step 3: Add the minimal parser and model changes**

In `src/engcalc_colab/parser.py`, extend the builtin call set:

```python
_ALLOWED_CALLS = {
    "integral", "diff", "solve", "simplify", "expand", "factor",
    "subs", "eq", "sum", "numeric", "plot",
}
```

In `src/engcalc_colab/models.py`, add:

```python
@dataclass(frozen=True)
class PlotResult:
    statement: ParsedStatement
    display_label: str
    variable: str
    x_values: tuple[Any, ...]
    y_values: tuple[Any, ...]
```

- [ ] **Step 4: Re-run the focused tests and verify GREEN**

Run:

```bash
pytest -q tests/test_plot_parser.py tests/test_parser.py
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit the parser/model slice**

```bash
git add src/engcalc_colab/parser.py src/engcalc_colab/models.py tests/test_plot_parser.py
git commit -m "feat: add plot command model"
```

---

### Task 2: Add deterministic unit-aware plot sampling primitives

**Files:**
- Modify: `src/engcalc_colab/numeric.py`
- Create: `tests/test_plot_sampling.py`

**Interfaces:**
- Consumes: `NumericContext.evaluate_symbolic(expression, overrides=...)` and Pint quantities.
- Produces:
  - `NumericContext.normalize_plot_bounds(start, end) -> tuple[Any, Any]`
  - `NumericContext.sample_symbolic(expression, variable, start, end, count=201) -> tuple[tuple[Any, ...], tuple[Any, ...]]`

- [ ] **Step 1: Write failing sampling tests**

Create `tests/test_plot_sampling.py`:

```python
import sympy as sp

from engcalc_colab.numeric import NumericContext
from engcalc_colab.errors import EngEvaluationError


def test_dimensionless_zero_is_promoted_to_dimensional_end_unit():
    context = NumericContext()
    zero = context.ureg.Quantity(0)
    end = 4 * context.ureg.m

    start_n, end_n = context.normalize_plot_bounds(zero, end)

    assert start_n.to("m").magnitude == 0
    assert end_n.to("m").magnitude == 4
    assert start_n.units == end_n.units


def test_sampling_contains_201_points_and_both_endpoints():
    context = NumericContext()
    q = 2.8 * context.ureg.tonf / context.ureg.m
    context.values["q"] = q
    x = sp.Symbol("x")
    expression = 7 * context.ureg.Quantity(1).magnitude * sp.Symbol("q") - sp.Symbol("q") * x
    start = 0 * context.ureg.m
    end = 4 * context.ureg.m

    xs, ys = context.sample_symbolic(expression, "x", start, end, count=201)

    assert len(xs) == 201
    assert len(ys) == 201
    assert xs[0].to("m").magnitude == 0
    assert xs[-1].to("m").magnitude == 4


def test_existing_plot_variable_value_is_not_mutated_by_sampling():
    context = NumericContext()
    context.values["x"] = 2.5 * context.ureg.m
    context.values["q"] = 2.8 * context.ureg.tonf / context.ureg.m
    expression = 5 * sp.Symbol("q") * 4 / 8 - sp.Symbol("q") * sp.Symbol("x")

    context.sample_symbolic(
        expression,
        "x",
        0 * context.ureg.m,
        4 * context.ureg.m,
        count=201,
    )

    assert context.values["x"].to("m").magnitude == 2.5


def test_incompatible_plot_bounds_fail_concisely():
    context = NumericContext()
    try:
        context.normalize_plot_bounds(0 * context.ureg.m, 4 * context.ureg.s)
    except EngEvaluationError as exc:
        assert "plot bounds have incompatible units" in str(exc)
    else:
        raise AssertionError("expected EngEvaluationError")


def test_plot_end_must_be_greater_than_start():
    context = NumericContext()
    try:
        context.normalize_plot_bounds(4 * context.ureg.m, 4 * context.ureg.m)
    except EngEvaluationError as exc:
        assert "plot end must be greater than start" in str(exc)
    else:
        raise AssertionError("expected EngEvaluationError")
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
pytest -q tests/test_plot_sampling.py
```

Expected: failures because `normalize_plot_bounds` and `sample_symbolic` are undefined.

- [ ] **Step 3: Implement bound normalization without mutating stored values**

Add to `NumericContext` in `src/engcalc_colab/numeric.py`:

```python
def normalize_plot_bounds(self, start, end):
    start = self._as_quantity(start)
    end = self._as_quantity(end)

    if start.dimensionless and not end.dimensionless:
        if float(start.magnitude) != 0.0:
            raise EngEvaluationError("plot bounds have incompatible units")
        start = self.ureg.Quantity(0, end.units)
    elif end.dimensionless and not start.dimensionless:
        if float(end.magnitude) != 0.0:
            raise EngEvaluationError("plot bounds have incompatible units")
        end = self.ureg.Quantity(0, start.units)

    try:
        end = end.to(start.units)
    except DimensionalityError as exc:
        raise EngEvaluationError("plot bounds have incompatible units") from exc

    if float(end.magnitude) <= float(start.magnitude):
        raise EngEvaluationError("plot end must be greater than start")
    return start, end
```

- [ ] **Step 4: Implement scalar interpolation and y-unit normalization**

Add to `NumericContext`:

```python
def sample_symbolic(self, expression, variable, start, end, count=201):
    if count < 2:
        raise EngEvaluationError("plot sampling requires at least 2 points")

    start, end = self.normalize_plot_bounds(start, end)
    delta = end - start
    xs = tuple(start + delta * (index / (count - 1)) for index in range(count))

    ys = []
    y_unit = None
    for x_value in xs:
        _, y_value = self.evaluate_symbolic(
            expression,
            overrides={variable: x_value},
        )
        if y_unit is None:
            y_unit = y_value.units
        try:
            y_value = y_value.to(y_unit)
        except DimensionalityError as exc:
            raise EngEvaluationError("plot samples have incompatible result units") from exc
        ys.append(y_value)

    return xs, tuple(ys)
```

- [ ] **Step 5: Re-run sampling plus existing numeric tests**

Run:

```bash
pytest -q tests/test_plot_sampling.py tests/test_numeric_context.py tests/test_numeric_engine.py
```

Expected: all selected tests pass and the stored `x` value remains unchanged.

- [ ] **Step 6: Commit the numerical sampling slice**

```bash
git add src/engcalc_colab/numeric.py tests/test_plot_sampling.py
git commit -m "feat: add unit-aware plot sampling"
```

---

### Task 3: Implement `plot()` evaluation in the symbolic engine

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/models.py` only if needed for typing union imports
- Create: `tests/test_plot_engine.py`

**Interfaces:**
- Consumes: `PlotResult`, `NumericContext.normalize_plot_bounds`, `NumericContext.sample_symbolic`.
- Produces: `EngineeringEngine.evaluate(...) -> PlotResult` when the source statement is `plot(...)`.

- [ ] **Step 1: Write failing engine tests using the real structural example**

Create `tests/test_plot_engine.py`:

```python
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import PlotResult
from engcalc_colab.parser import parse_cell


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def test_plot_reuses_function_and_numeric_state():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = 5*q*L/8 - q*x")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 4*m")

    result = eval_cell(engine, "plot(V(x), x, 0, L)")[-1]

    assert isinstance(result, PlotResult)
    assert result.display_label == "V(x)"
    assert len(result.x_values) == 201
    assert result.x_values[-1].to("m").magnitude == 4


def test_plot_moment_preserves_dimensional_zero_at_right_boundary():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 4*m")

    result = eval_cell(engine, "plot(M(x), x, 0, L)")[-1]

    assert result.y_values[0].to("tonf*m").magnitude == -5.6
    assert abs(result.y_values[-1].to("tonf*m").magnitude) < 1e-12
    assert not result.y_values[-1].dimensionless


def test_plot_locally_overrides_preexisting_numeric_x():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = 5*q*L/8 - q*x")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 4*m\nx := 2.5*m")

    result = eval_cell(engine, "plot(V(x), x, 0, L)")[-1]

    assert len(result.x_values) == 201
    assert engine.numeric_context.get("x").to("m").magnitude == 2.5


def test_plot_reports_missing_non_plot_symbol():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = 5*q*L/8 - q*x\nL := 4*m")
    try:
        eval_cell(engine, "plot(V(x), x, 0, L)")
    except EngEvaluationError as exc:
        assert "numeric evaluation requires values for: q" in str(exc)
        assert str(exc).startswith("line 1:")
    else:
        raise AssertionError("expected EngEvaluationError")


def test_plot_requires_identifier_variable_and_four_arguments():
    engine = EngineeringEngine()
    for source, expected in [
        ("plot(x, x, 0)", "plot expects 4 arguments: expression, variable, start, end"),
        ("plot(x, x + 1, 0, 4)", "plot variable must be a symbolic identifier"),
    ]:
        try:
            eval_cell(engine, source)
        except EngEvaluationError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError("expected EngEvaluationError")
```

- [ ] **Step 2: Run engine tests and verify RED**

Run:

```bash
pytest -q tests/test_plot_engine.py
```

Expected: failures because `_Evaluator.visit_Call()` has no `plot` implementation and `EngineeringEngine.evaluate()` does not return `PlotResult`.

- [ ] **Step 3: Extend the engine result union and imports**

In `src/engcalc_colab/engine.py`, import `PlotResult` and add it to the return annotation of `EngineeringEngine.evaluate()`.

- [ ] **Step 4: Implement `plot` before generic argument evaluation**

Inside `_Evaluator.visit_Call()`, before the `numeric` branch, add a dedicated `plot` branch with this structure:

```python
if name == "plot":
    self._require_arity(name, node.args, 4, "expression, variable, start, end")
    variable_node = node.args[1]
    if not isinstance(variable_node, ast.Name):
        raise EngEvaluationError("plot variable must be a symbolic identifier")
    variable = variable_node.id

    expression_node = node.args[0]
    symbolic_expression = self.visit(expression_node)

    start_expression = self.visit(node.args[2])
    end_expression = self.visit(node.args[3])
    _, start_quantity = self.engine.numeric_context.evaluate_symbolic(start_expression)
    _, end_quantity = self.engine.numeric_context.evaluate_symbolic(end_expression)
    start_quantity, end_quantity = self.engine.numeric_context.normalize_plot_bounds(
        start_quantity,
        end_quantity,
    )

    x_values, y_values = self.engine.numeric_context.sample_symbolic(
        symbolic_expression,
        variable,
        start_quantity,
        end_quantity,
        count=201,
    )

    if (
        isinstance(expression_node, ast.Call)
        and isinstance(expression_node.func, ast.Name)
        and expression_node.func.id in self.engine.functions
    ):
        display_label = f"{expression_node.func.id}({variable})"
    else:
        display_label = str(symbolic_expression)

    self.plot_result = PlotResult(
        statement=self.current_statement,
        display_label=display_label,
        variable=variable,
        x_values=x_values,
        y_values=y_values,
    )
    return symbolic_expression
```

Do not literally introduce `current_statement` into `_Evaluator`; instead keep construction of `PlotResult` in `EngineeringEngine.evaluate()` where the `statement` object already exists. The evaluator should store a tuple payload analogous to `numeric_evaluation`, for example:

```python
self.plot_evaluation = (display_label, variable, x_values, y_values)
```

Then `EngineeringEngine.evaluate()` converts that payload into `PlotResult(statement=statement, ...)` before any ordinary `EvaluationResult` is returned.

- [ ] **Step 5: Ensure local sampling overrides the plot variable**

Before calling `sample_symbolic`, verify that evaluating `symbolic_expression` does not eagerly require the numeric value of the plotting variable. Only `sample_symbolic(... overrides={variable: x_value})` supplies it. Do not write into `numeric_context.values[variable]`.

- [ ] **Step 6: Run engine/numeric regression tests**

Run:

```bash
pytest -q tests/test_plot_engine.py tests/test_plot_sampling.py tests/test_engine.py tests/test_numeric_engine.py
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit the engine slice**

```bash
git add src/engcalc_colab/engine.py src/engcalc_colab/models.py tests/test_plot_engine.py
git commit -m "feat: evaluate native plot statements"
```

---

### Task 4: Render plots with Matplotlib and preserve notebook source order

**Files:**
- Create: `src/engcalc_colab/plotting.py`
- Modify: `src/engcalc_colab/magic.py`
- Create: `tests/test_plotting.py`
- Modify: `tests/test_magic.py`

**Interfaces:**
- Consumes: `PlotResult` from the engine.
- Produces: `render_plot(result: PlotResult) -> matplotlib.figure.Figure` and source-ordered figure display in `%%eng`.

- [ ] **Step 1: Write failing plotting-adapter tests**

Create `tests/test_plotting.py`:

```python
import matplotlib
matplotlib.use("Agg")

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def _moment_plot_result():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 4*m")
    return eval_cell(engine, "plot(M(x), x, 0, L)")[-1]


def test_render_plot_labels_axes_title_and_zero_reference():
    result = _moment_plot_result()
    figure = render_plot(result)
    axis = figure.axes[0]

    assert axis.get_xlabel().startswith("x [")
    assert "m" in axis.get_xlabel()
    assert axis.get_ylabel().startswith("M(x) [")
    assert "tonf" in axis.get_ylabel()
    assert "m" in axis.get_ylabel()
    assert axis.get_title() == "M(x)"
    assert len(axis.lines) == 2


def test_render_plot_returns_closed_figure_to_prevent_duplicate_jupyter_output():
    import matplotlib.pyplot as plt

    result = _moment_plot_result()
    figure = render_plot(result)

    assert figure.number not in plt.get_fignums()
```

- [ ] **Step 2: Write failing notebook sequencing test**

Append to `tests/test_magic.py`:

```python
def test_eng_magic_flushes_math_before_plot_and_resumes_after(monkeypatch):
    import engcalc_colab.magic as magic_module
    from IPython.display import Math
    from matplotlib.figure import Figure

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "A = q*L\nq := 2.8*tonf/m\nL := 4*m\n"
        "plot(A*x, x, 0, L)\nB = 2*A",
    )

    assert [type(item) for item in displayed] == [Math, Figure, Math]
```

- [ ] **Step 3: Run focused tests and verify RED**

Run:

```bash
pytest -q tests/test_plotting.py tests/test_magic.py::test_eng_magic_flushes_math_before_plot_and_resumes_after
```

Expected: import failure for `engcalc_colab.plotting` and/or sequencing failure because `PlotResult` is still batched into MathJax.

- [ ] **Step 4: Implement `plotting.py` without a custom theme**

Create `src/engcalc_colab/plotting.py`:

```python
from __future__ import annotations

from .models import PlotResult


def _unit_label(quantity) -> str:
    if quantity.dimensionless:
        return ""
    return f"{quantity.units:~P}"


def _axis_label(name: str, quantity) -> str:
    unit = _unit_label(quantity)
    return name if not unit else f"{name} [{unit}]"


def render_plot(result: PlotResult):
    import matplotlib.pyplot as plt

    x_values = [float(value.magnitude) for value in result.x_values]
    y_values = [float(value.magnitude) for value in result.y_values]

    figure, axis = plt.subplots()
    axis.plot(x_values, y_values)
    axis.axhline(0.0, linewidth=0.8)
    axis.set_xlabel(_axis_label(result.variable, result.x_values[0]))
    axis.set_ylabel(_axis_label(result.display_label, result.y_values[0]))
    axis.set_title(result.display_label)
    figure.tight_layout()
    plt.close(figure)
    return figure
```

Do not set a color or Matplotlib style; the user's existing `rcParams` remain authoritative.

- [ ] **Step 5: Teach `EngMagics.eng()` to treat `PlotResult` as an output boundary**

In `src/engcalc_colab/magic.py`:

```python
from .models import PlotResult
from .plotting import render_plot
```

Then change the statement-processing path from unconditional append:

```python
pending_results.append(self.engine.evaluate(item))
```

to:

```python
result = self.engine.evaluate(item)
if isinstance(result, PlotResult):
    _display_equation_group(pending_results, self.render_settings)
    pending_results.clear()
    display(render_plot(result))
    continue
pending_results.append(result)
```

Do not add `PlotResult` to the `CalculationResult` alias used by `render_aligned_results`; plots must never enter the MathJax renderer.

- [ ] **Step 6: Run adapter, sequencing and existing magic tests**

Run:

```bash
pytest -q tests/test_plotting.py tests/test_magic.py tests/test_headings.py
```

Expected: all selected tests pass, and the sequencing test sees exactly Math → Figure → Math.

- [ ] **Step 7: Commit the notebook display slice**

```bash
git add src/engcalc_colab/plotting.py src/engcalc_colab/magic.py tests/test_plotting.py tests/test_magic.py
git commit -m "feat: render native plots in eng cells"
```

---

### Task 5: Acceptance case, packaging, documentation and 0.3.0 release gate

**Files:**
- Create: `tests/test_acceptance_native_plot.py`
- Modify: `tests/test_packaging.py`
- Modify: `tests/test_parser.py`
- Modify: `pyproject.toml`
- Modify: `src/engcalc_colab/__init__.py`
- Modify: `README.md`
- Temporary during validation only: `.github/workflows/native-plot-validation.yml`

**Interfaces:**
- Consumes: complete `plot()` flow from Tasks 1–4.
- Produces: user-facing EngCalc 0.3.0 release with Matplotlib declared as runtime dependency.

- [ ] **Step 1: Write the end-to-end structural acceptance test**

Create `tests/test_acceptance_native_plot.py`:

```python
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import PlotResult
from engcalc_colab.parser import parse_cell


def test_propped_cantilever_native_plot_end_to_end():
    engine = EngineeringEngine()
    cell = """
V(x) = 5*q*L/8 - q*x
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2
q := 2.8*tonf/m
L := 4*m
plot(V(x), x, 0, L)
plot(M(x), x, 0, L)
"""
    results = [engine.evaluate(stmt) for stmt in parse_cell(cell)]
    plots = [result for result in results if isinstance(result, PlotResult)]

    assert len(plots) == 2
    shear, moment = plots
    assert len(shear.x_values) == 201
    assert shear.x_values[-1].to("m").magnitude == 4
    assert abs(moment.y_values[-1].to("tonf*m").magnitude) < 1e-12
```

- [ ] **Step 2: Put release metadata in RED before changing version/dependencies**

Modify `tests/test_packaging.py` so it requires:

```python
def test_pyproject_version_is_0_3_0():
    assert _project_metadata()["version"] == "0.3.0"


def test_matplotlib_is_a_runtime_dependency():
    assert "matplotlib" in _dependency_names()
```

Modify the existing version assertion in `tests/test_parser.py`:

```python
assert __version__ == "0.3.0"
```

Run:

```bash
pytest -q tests/test_acceptance_native_plot.py tests/test_packaging.py tests/test_parser.py
```

Expected: plot acceptance passes after Tasks 1–4; release tests fail only because current metadata still reports 0.2.9 and Matplotlib is not yet declared.

- [ ] **Step 3: Bump package metadata and runtime dependency**

In `pyproject.toml` set:

```toml
version = "0.3.0"
dependencies = ["sympy>=1.13", "pint>=0.24", "matplotlib>=3.8"]
```

In `src/engcalc_colab/__init__.py` set:

```python
__version__ = "0.3.0"
```

- [ ] **Step 4: Update README command reference and example**

Document all of the following in `README.md`:

```text
plot(expression, variable, start, end)
```

Canonical example:

```text
%%eng
V(x) = 5*q*L/8 - q*x
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2
q := 2.8*tonf/m
L := 4*m
plot(V(x), x, 0, L)
plot(M(x), x, 0, L)
```

State explicitly that 0.3.0 creates one curve/figure per call, uses 201 samples, infers natural units, reuses EngCalc state, ignores a stored numeric value for the sampling variable locally, and does not yet support kwargs/multiple curves/custom styles/piecewise plotting.

- [ ] **Step 5: Run the full local/CI-equivalent suite**

Run:

```bash
pytest -q
```

Expected: complete suite passes.

- [ ] **Step 6: Add a temporary wheel-validation workflow**

Create `.github/workflows/native-plot-validation.yml` on the feature branch:

```yaml
name: Native plot validation

on:
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      MPLBACKEND: Agg
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install validation dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install 'pytest>=8' 'build>=1' 'ipython>=8'
      - name: Build and install release wheel
        run: |
          python -m build --wheel
          python -m pip install --force-reinstall dist/engcalc_colab-0.3.0-py3-none-any.whl
          python -c "import engcalc_colab; assert engcalc_colab.__version__ == '0.3.0'"
      - name: Run tests
        run: pytest -q
```

- [ ] **Step 7: Open/update the PR and wait for a green wheel gate**

The PR body must record:

```text
- parser/model RED then GREEN
- sampling RED then GREEN
- engine RED then GREEN
- plotting/magic RED then GREEN
- release RED limited to version/dependency metadata
- final wheel build/install of engcalc-colab 0.3.0
- full pytest pass count from the fresh final run
```

Do not claim a pass count until the final CI run has completed successfully.

- [ ] **Step 8: Remove the temporary workflow after the green gate**

Delete:

```text
.github/workflows/native-plot-validation.yml
```

Then verify the final diff contains only permanent source, tests, documentation and package metadata.

- [ ] **Step 9: Final review and squash merge**

Review these invariants before merge:

```text
plot is restricted EngCalc syntax, not arbitrary Python
PlotResult contains data, not Matplotlib objects
sampling does not mutate stored x
MathJax output is unchanged when no plot is present
plot flushes equation groups in source order
plotting.py sets no colors/styles
Matplotlib is a declared runtime dependency
version is 0.3.0
```

Then squash merge with the PR head SHA pinned.

- [ ] **Step 10: Verify `main` after merge**

Fetch from `main` and confirm:

```text
pyproject.toml -> version 0.3.0 + matplotlib>=3.8
src/engcalc_colab/__init__.py -> __version__ 0.3.0
src/engcalc_colab/plotting.py exists
parser reserves plot
README documents plot(expression, variable, start, end)
```

Report the final merge SHA and the fresh final test count.
