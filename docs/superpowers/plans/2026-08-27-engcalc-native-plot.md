# EngCalc 0.3.0 Native `plot()` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add native `plot(expression, variable, start, end)` support to `%%eng`, reusing EngCalc's symbolic formulas and Pint-backed numerical state to produce one unit-aware Matplotlib figure without redefining data in Python.

**Architecture:** Keep plotting side effects outside the symbolic engine. The parser accepts `plot` as a restricted builtin; the engine returns an immutable `PlotResult` containing normalized Pint samples and metadata; `src/engcalc_colab/plotting.py` converts that result into a closed Matplotlib `Figure`; `EngMagics.eng()` flushes pending MathJax equations before displaying the figure and then resumes source-order processing.

**Tech Stack:** Python 3.10+, SymPy >=1.13, Pint >=0.24, Matplotlib >=3.8, IPython, pytest >=8.

**Spec:** `docs/superpowers/specs/2026-08-27-engcalc-native-plot-design.md`

## Global Constraints

- Public syntax is exactly `plot(expression, variable, start, end)` with four positional arguments.
- `plot(...)` is an output statement, not a value-producing symbolic assignment.
- Keyword arguments remain unsupported.
- One curve and one figure are produced per `plot(...)`.
- Sampling count is exactly 201 points including both endpoints.
- Existing symbolic/numerical EngCalc state is reused directly.
- A stored numerical value for the plotting variable is overridden locally during sampling and is never mutated.
- An exact dimensionless zero bound may be promoted to the compatible dimensional unit of the other bound.
- Incompatible bound dimensions and `end <= start` are concise EngCalc errors.
- The y-axis unit is fixed from the first sample; later samples convert to that unit or fail.
- Matplotlib inherits active user `rcParams`; EngCalc sets no theme and no curve color.
- `plot(...)` creates no MathJax equation row; only the figure appears at that source position.
- Existing notebooks without `plot(...)` render identically to 0.2.9.
- Matplotlib is a direct runtime dependency.
- Target version is exactly `0.3.0`.
- Multiple curves, kwargs/styles, plot-unit overrides, extrema/root annotations, fills, legends, `piecewise`, discontinuities and file export are out of scope.

---

### Task 1: Reserve `plot` and add the transport model

**Files:**
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/models.py`
- Create: `tests/test_plot_parser.py`

**Interfaces:**
- Consumes: `parse_cell()` and `ParsedStatement`.
- Produces: immutable `PlotResult(statement, display_label, variable, x_values, y_values)` and a reserved `plot` builtin name.

- [ ] **Step 1: Write failing tests**

Create `tests/test_plot_parser.py`:

```python
from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.models import PlotResult
from engcalc_colab.parser import parse_cell


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
    result = PlotResult(statement, "M(x)", "x", (1,), (2,))
    assert result.display_label == "M(x)"
    assert result.variable == "x"
```

- [ ] **Step 2: Verify RED**

```bash
pytest -q tests/test_plot_parser.py
```

Expected: import/collection failure because `PlotResult` does not exist and/or parser behavior is incomplete.

- [ ] **Step 3: Implement the parser/model minimum**

In `src/engcalc_colab/parser.py`:

```python
_ALLOWED_CALLS = {
    "integral", "diff", "solve", "simplify", "expand", "factor",
    "subs", "eq", "sum", "numeric", "plot",
}
```

In `src/engcalc_colab/models.py`:

```python
@dataclass(frozen=True)
class PlotResult:
    statement: ParsedStatement
    display_label: str
    variable: str
    x_values: tuple[Any, ...]
    y_values: tuple[Any, ...]
```

- [ ] **Step 4: Verify GREEN and parser regression**

```bash
pytest -q tests/test_plot_parser.py tests/test_parser.py
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/engcalc_colab/parser.py src/engcalc_colab/models.py tests/test_plot_parser.py
git commit -m "feat: add plot command model"
```

---

### Task 2: Add deterministic unit-aware sampling

**Files:**
- Modify: `src/engcalc_colab/numeric.py`
- Create: `tests/test_plot_sampling.py`

**Interfaces:**
- Consumes: `NumericContext.evaluate_symbolic(expression, overrides=...)` and Pint quantities.
- Produces:
  - `normalize_plot_bounds(start, end) -> tuple[Quantity, Quantity]`
  - `sample_symbolic(expression, variable, start, end, count=201) -> tuple[tuple[Quantity, ...], tuple[Quantity, ...]]`

- [ ] **Step 1: Write failing sampling tests**

Create `tests/test_plot_sampling.py`:

```python
import sympy as sp

from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.numeric import NumericContext


def test_dimensionless_zero_is_promoted_to_dimensional_end_unit():
    context = NumericContext()
    start, end = context.normalize_plot_bounds(
        context.ureg.Quantity(0),
        4 * context.ureg.m,
    )
    assert start.to("m").magnitude == 0
    assert end.to("m").magnitude == 4
    assert start.units == end.units


def test_sampling_contains_201_points_and_both_endpoints():
    context = NumericContext()
    context.values["q"] = 2.8 * context.ureg.tonf / context.ureg.m
    context.values["L"] = 4 * context.ureg.m
    q, L, x = sp.symbols("q L x")
    expression = 5*q*L/8 - q*x

    xs, ys = context.sample_symbolic(
        expression, "x", 0 * context.ureg.m, 4 * context.ureg.m, count=201
    )

    assert len(xs) == 201
    assert len(ys) == 201
    assert xs[0].to("m").magnitude == 0
    assert xs[-1].to("m").magnitude == 4
    assert ys[0].to("tonf").magnitude == 7.0


def test_existing_plot_variable_value_is_not_mutated_by_sampling():
    context = NumericContext()
    context.values["x"] = 2.5 * context.ureg.m
    context.values["q"] = 2.8 * context.ureg.tonf / context.ureg.m
    context.values["L"] = 4 * context.ureg.m
    q, L, x = sp.symbols("q L x")

    context.sample_symbolic(
        5*q*L/8 - q*x,
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

- [ ] **Step 2: Verify RED**

```bash
pytest -q tests/test_plot_sampling.py
```

Expected: missing-method failures.

- [ ] **Step 3: Implement bound normalization**

Add to `NumericContext`:

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

- [ ] **Step 4: Implement sampling with local overrides**

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

- [ ] **Step 5: Verify GREEN and numeric regression**

```bash
pytest -q tests/test_plot_sampling.py tests/test_numeric_context.py tests/test_numeric_engine.py
```

Expected: all selected tests pass; `context.values["x"]` remains unchanged.

- [ ] **Step 6: Commit**

```bash
git add src/engcalc_colab/numeric.py tests/test_plot_sampling.py
git commit -m "feat: add unit-aware plot sampling"
```

---

### Task 3: Evaluate `plot()` in the EngCalc engine

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Create: `tests/test_plot_engine.py`

**Interfaces:**
- Consumes: `PlotResult`, `normalize_plot_bounds`, `sample_symbolic`.
- Produces: `EngineeringEngine.evaluate(statement) -> PlotResult` for a standalone `plot(...)` statement.

- [ ] **Step 1: Write failing engine tests**

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
        assert str(exc).startswith("line 1:")
        assert "numeric evaluation requires values for: q" in str(exc)
    else:
        raise AssertionError("expected EngEvaluationError")


def test_plot_requires_identifier_variable_and_four_arguments():
    engine = EngineeringEngine()
    cases = [
        ("plot(x, x, 0)", "plot expects 4 arguments: expression, variable, start, end"),
        ("plot(x, x + 1, 0, 4)", "plot variable must be a symbolic identifier"),
    ]
    for source, expected in cases:
        try:
            eval_cell(engine, source)
        except EngEvaluationError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError("expected EngEvaluationError")


def test_plot_cannot_be_assigned_to_symbol():
    engine = EngineeringEngine()
    try:
        eval_cell(engine, "A = plot(x, x, 0, 4)")
    except EngEvaluationError as exc:
        assert "plot must be a standalone statement" in str(exc)
    else:
        raise AssertionError("expected EngEvaluationError")
```

- [ ] **Step 2: Verify RED**

```bash
pytest -q tests/test_plot_engine.py
```

Expected: `plot` is unsupported by the evaluator.

- [ ] **Step 3: Add plot payload state to `_Evaluator`**

In `_Evaluator.__init__`:

```python
self.plot_evaluation = None
```

Import `PlotResult` in `engine.py` and add it to `EngineeringEngine.evaluate()`'s return union.

- [ ] **Step 4: Implement the exact `plot` evaluator branch**

Add before the existing `numeric` branch in `_Evaluator.visit_Call()`:

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

    self.plot_evaluation = (display_label, variable, x_values, y_values)
    return symbolic_expression
```

- [ ] **Step 5: Convert the payload into `PlotResult` in `EngineeringEngine.evaluate()`**

Immediately after:

```python
value = evaluator.visit(statement.expression.body)
```

add:

```python
if evaluator.plot_evaluation is not None:
    if statement.target is not None:
        raise EngEvaluationError("plot must be a standalone statement")
    display_label, variable, x_values, y_values = evaluator.plot_evaluation
    return PlotResult(
        statement=statement,
        display_label=display_label,
        variable=variable,
        x_values=x_values,
        y_values=y_values,
    )
```

This branch runs before numeric/partial-numeric and ordinary assignment handling.

- [ ] **Step 6: Verify GREEN and engine regression**

```bash
pytest -q tests/test_plot_engine.py tests/test_plot_sampling.py tests/test_engine.py tests/test_numeric_engine.py
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/engcalc_colab/engine.py tests/test_plot_engine.py
git commit -m "feat: evaluate native plot statements"
```

---

### Task 4: Add Matplotlib adapter and source-ordered notebook display

**Files:**
- Create: `src/engcalc_colab/plotting.py`
- Modify: `src/engcalc_colab/magic.py`
- Create: `tests/test_plotting.py`
- Modify: `tests/test_magic.py`

**Interfaces:**
- Consumes: `PlotResult`.
- Produces: `render_plot(result: PlotResult) -> matplotlib.figure.Figure` and Math → Figure → Math sequencing in `%%eng`.

- [ ] **Step 1: Write failing adapter tests**

Create `tests/test_plotting.py`:

```python
import matplotlib
matplotlib.use("Agg")

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import render_plot


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def moment_plot_result():
    engine = EngineeringEngine()
    eval_cell(engine, "M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2")
    eval_cell(engine, "q := 2.8*tonf/m\nL := 4*m")
    return eval_cell(engine, "plot(M(x), x, 0, L)")[-1]


def test_render_plot_labels_axes_title_and_zero_reference():
    figure = render_plot(moment_plot_result())
    axis = figure.axes[0]
    assert axis.get_xlabel().startswith("x [")
    assert "m" in axis.get_xlabel()
    assert axis.get_ylabel().startswith("M(x) [")
    assert "tonf" in axis.get_ylabel()
    assert "m" in axis.get_ylabel()
    assert axis.get_title() == "M(x)"
    assert len(axis.lines) == 2


def test_render_plot_returns_closed_figure():
    import matplotlib.pyplot as plt
    figure = render_plot(moment_plot_result())
    assert figure.number not in plt.get_fignums()
```

- [ ] **Step 2: Write failing magic sequencing test**

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

- [ ] **Step 3: Verify RED**

```bash
pytest -q tests/test_plotting.py tests/test_magic.py::test_eng_magic_flushes_math_before_plot_and_resumes_after
```

Expected: missing `plotting.py` and/or sequencing failure.

- [ ] **Step 4: Implement `plotting.py` without custom styling**

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

Do not specify a curve color or Matplotlib style.

- [ ] **Step 5: Add PlotResult as an output boundary in `EngMagics.eng()`**

Import:

```python
from .models import PlotResult
from .plotting import render_plot
```

Replace unconditional append with:

```python
result = self.engine.evaluate(item)
if isinstance(result, PlotResult):
    _display_equation_group(pending_results, self.render_settings)
    pending_results.clear()
    display(render_plot(result))
    continue
pending_results.append(result)
```

Do not add `PlotResult` to the MathJax `CalculationResult` alias.

- [ ] **Step 6: Verify GREEN and magic/headings regression**

```bash
pytest -q tests/test_plotting.py tests/test_magic.py tests/test_headings.py
```

Expected: all selected tests pass and source order is exactly Math → Figure → Math.

- [ ] **Step 7: Commit**

```bash
git add src/engcalc_colab/plotting.py src/engcalc_colab/magic.py tests/test_plotting.py tests/test_magic.py
git commit -m "feat: render native plots in eng cells"
```

---

### Task 5: Acceptance, packaging, documentation and release gate

**Files:**
- Create: `tests/test_acceptance_native_plot.py`
- Modify: `tests/test_packaging.py`
- Modify: `tests/test_parser.py`
- Modify: `pyproject.toml`
- Modify: `src/engcalc_colab/__init__.py`
- Modify: `README.md`
- Temporary only: `.github/workflows/native-plot-validation.yml`

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: installable EngCalc 0.3.0 with Matplotlib runtime support.

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

- [ ] **Step 2: Put release metadata in RED before changing it**

In `tests/test_packaging.py`, require:

```python
def test_pyproject_version_is_0_3_0():
    assert _project_metadata()["version"] == "0.3.0"


def test_matplotlib_is_a_runtime_dependency():
    assert "matplotlib" in _dependency_names()
```

In `tests/test_parser.py`, change the package-version assertion to:

```python
assert __version__ == "0.3.0"
```

Run:

```bash
pytest -q tests/test_acceptance_native_plot.py tests/test_packaging.py tests/test_parser.py
```

Expected: acceptance passes; release assertions fail only because metadata is still 0.2.9 and Matplotlib is not declared.

- [ ] **Step 3: Bump package metadata**

In `pyproject.toml`:

```toml
version = "0.3.0"
dependencies = ["sympy>=1.13", "pint>=0.24", "matplotlib>=3.8"]
```

In `src/engcalc_colab/__init__.py`:

```python
__version__ = "0.3.0"
```

- [ ] **Step 4: Update README**

Document:

```text
plot(expression, variable, start, end)
```

and the canonical example:

```text
%%eng
V(x) = 5*q*L/8 - q*x
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2
q := 2.8*tonf/m
L := 4*m
plot(V(x), x, 0, L)
plot(M(x), x, 0, L)
```

State explicitly: one figure per call, 201 samples, natural units, reuse of EngCalc state, local override of any stored sampling-variable value, and no kwargs/multiple curves/custom styles/piecewise support in 0.3.0.

- [ ] **Step 5: Run the full suite**

```bash
pytest -q
```

Expected: complete suite passes.

- [ ] **Step 6: Add temporary wheel-validation CI**

Create `.github/workflows/native-plot-validation.yml`:

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

- [ ] **Step 7: Open/update PR and obtain fresh GREEN evidence**

PR body must record each RED/GREEN phase, the final wheel build/install, runtime version check and fresh full-suite pass count. Do not state a pass count until the final run completes.

- [ ] **Step 8: Remove temporary workflow**

Delete `.github/workflows/native-plot-validation.yml` after the green release gate. Verify the final diff contains only permanent source, tests, docs and metadata.

- [ ] **Step 9: Final review and squash merge**

Verify:

```text
plot remains restricted EngCalc syntax
PlotResult contains no Matplotlib object
sampling never mutates stored x
non-plot MathJax output is unchanged
plot flushes equations in source order
plotting.py specifies no colors/styles
Matplotlib is a direct dependency
version is 0.3.0
```

Then squash merge with expected head SHA pinned.

- [ ] **Step 10: Post-merge verification on `main`**

Confirm:

```text
pyproject.toml -> version 0.3.0 and matplotlib>=3.8
src/engcalc_colab/__init__.py -> __version__ 0.3.0
src/engcalc_colab/plotting.py exists
parser reserves plot
README documents plot(expression, variable, start, end)
```

Report the merge SHA and only the fresh final test count.
