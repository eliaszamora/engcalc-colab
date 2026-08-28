# EngCalc 0.3.0 — Native `plot()` Design

Date: 2026-08-27
Status: Proposed for implementation after user review

## Purpose

EngCalc already owns the symbolic expression and the Pint-backed numerical data needed to evaluate an engineering function. Users should not have to repeat formulas and numerical values in a separate Python cell merely to draw a diagram.

EngCalc 0.3.0 adds a native plotting statement inside `%%eng`:

```text
plot(expression, variable, start, end)
```

The first release is intentionally narrow. It provides one curve per `plot(...)`, automatic engineering units, deterministic sampling, and clear validation errors. It does not add styling keywords, multiple curves, automatic extrema, piecewise/discontinuous plotting, or plot-specific unit conversion.

## User-facing contract

Canonical example:

```text
%%eng

## Fuerzas internas

V(x) = 5*q*L/8 - q*x
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2

## Datos

q := 2.8*tonf/m
L := 4*m

## Diagramas

plot(V(x), x, 0, L)
plot(M(x), x, 0, L)
```

Each `plot(...)` produces one Matplotlib figure in the output sequence at the location of the statement. The symbolic and numerical EngCalc state already defined in the cell, or persisted from earlier `%%eng` cells, is reused directly.

### Exact v0.3.0 syntax

```text
plot(expression, variable, start, end)
```

- `expression`: any EngCalc symbolic expression that becomes fully numerical when the plotting variable is supplied. A defined EngCalc function call such as `V(x)` or `M(x)` is the primary use case.
- `variable`: a symbolic identifier, for example `x`.
- `start`, `end`: bounds that must be numerically evaluable from the current EngCalc numerical context. They may contain known symbols such as `L`.
- Exactly four positional arguments are accepted.
- Keyword arguments remain unsupported in 0.3.0.

### Plotting variable semantics

The second argument is always the independent sampling variable for this plot. If the same name already has a numeric assignment such as `x := 2.5*m`, `plot(M(x), x, 0, L)` still samples `x` across the requested interval. The existing numeric value of `x` is not deleted or mutated; it is simply overridden locally for each plot sample.

This makes plotting independent of point evaluations such as `numeric(M(x))` performed elsewhere in the notebook.

## Output behavior

Each figure uses Matplotlib and inherits the user's active Matplotlib `rcParams` rather than installing a separate EngCalc visual theme.

Default figure contents:

- one line for the requested expression;
- horizontal reference line at `y = 0`;
- x-axis label: `<variable> [<unit>]`, for example `x [m]`;
- y-axis label: expression/function label plus result unit, for example `M(x) [tonf·m]`;
- title: the display expression/function label, for example `M(x)`;
- 201 sample points including both endpoints;
- `tight_layout()` before display.

EngCalc does not invert structural signs automatically. The plotted ordinate uses exactly the sign convention of the symbolic expression.

### Unit selection

The x-axis uses the natural unit resolved from the bounds:

1. If both bounds are dimensional and compatible, the start unit is used.
2. If one bound is an exact dimensionless zero and the other is dimensional, the zero is promoted to the dimensional bound's unit. This supports the common form `plot(M(x), x, 0, L)` when `L := 4*m`.
3. If both bounds are dimensionless, the x-axis is dimensionless.
4. Incompatible bound dimensions are rejected.

All sampled x values are generated in the chosen x-axis unit.

The y-axis uses the natural Pint unit of the first evaluated sample. Every subsequent sample is converted to that same compatible unit before plotting. Dimensional inconsistency is rejected rather than silently coerced.

A dimensionless axis omits square-bracket units from its label.

## Architecture

### 1. Parser

Add `plot` to the EngCalc reserved/builtin call set. Existing restricted-AST rules remain unchanged: no arbitrary Python execution, attribute access, or keyword arguments are introduced.

`plot` remains syntactically an EngCalc call rather than a Python/Matplotlib escape hatch.

### 2. Model

Add an immutable `PlotResult` model containing only plotting data and presentation metadata, not Matplotlib objects. Proposed fields:

```python
@dataclass(frozen=True)
class PlotResult:
    statement: ParsedStatement
    display_label: str
    variable: str
    x_values: tuple[Any, ...]
    y_values: tuple[Any, ...]
```

`x_values` and `y_values` are Pint quantities normalized to one x unit and one y unit respectively.

This keeps Matplotlib outside the symbolic engine and makes sampling independently testable.

### 3. Engine / evaluator

`_Evaluator.visit_Call()` recognizes `plot` before ordinary function dispatch.

Responsibilities:

- enforce four arguments;
- enforce that argument 2 is an identifier;
- resolve the expression symbolically, including EngCalc user functions;
- evaluate `start` and `end` numerically;
- normalize compatible bound units and promote an exact dimensionless zero when appropriate;
- require `end > start` after normalization;
- sample 201 coordinates including endpoints;
- evaluate the symbolic expression at each coordinate using a local numeric override for the plotting variable;
- require every other free symbol to have a numeric value;
- normalize all y quantities to the first sample's unit;
- return `PlotResult` without mutating symbolic functions, numeric assignments, or the plotting variable's stored value.

The plot operation is therefore unit-aware evaluation, not arbitrary plotting code.

### 4. Plotting adapter

Create `src/engcalc_colab/plotting.py`.

It receives a `PlotResult` and creates the Matplotlib figure. It has no access to the symbolic engine or parser.

Conceptual interface:

```python
def render_plot(result: PlotResult):
    ...
    return figure
```

The adapter converts Pint quantities to plain magnitudes only after the engine has normalized their units.

Matplotlib is imported lazily inside this plotting boundary so importing `engcalc_colab` itself does not initialize plotting state.

### 5. Notebook magic sequencing

`EngMagics.eng()` currently batches calculation results into MathJax equation groups. Plot results cannot be inserted into a MathJax array.

When a `PlotResult` is encountered:

1. flush all pending equation results through the existing MathJax renderer;
2. call `render_plot(plot_result)`;
3. display the returned Matplotlib figure;
4. continue parsing/evaluating the remaining `%%eng` statements.

This preserves source order. For example:

```text
A = ...
plot(A*x, x, 0, L)
B = ...
```

renders the `A` equation, then the plot, then the `B` equation.

Headings retain their existing behavior and can appear before/after plots.

## Dependency policy

Add a direct runtime dependency on Matplotlib in `pyproject.toml` because `plot()` is a public EngCalc feature. The implementation must not rely on Colab happenstance or on the user's unrelated imports.

NumPy is not required as a direct EngCalc API dependency for sampling; the engine can construct 201 Pint coordinates deterministically with scalar interpolation. Matplotlib may bring NumPy transitively, but EngCalc does not expose NumPy as part of this feature contract.

## Error handling

Errors remain concise `EngCalcError` messages with source line numbers and no traceback.

Required failure cases include:

- wrong arity: `plot expects 4 arguments: expression, variable, start, end`;
- non-identifier plotting variable;
- missing numerical values for non-plot symbols, reported by name;
- bounds with incompatible dimensions;
- non-numerical bounds;
- `end <= start` after unit normalization;
- incompatible y dimensions across samples;
- an expression/function that cannot be numerically evaluated over the interval.

A plotting error must not partially modify EngCalc state.

## Security

`plot()` does not expose Matplotlib functions, filenames, callbacks, Python objects, or arbitrary kwargs to the EngCalc language.

All four arguments pass through the existing restricted AST. `plot` only receives symbolic expressions and unit-aware numeric data produced by EngCalc itself.

## TDD acceptance tests

Implementation begins with failing tests covering at least:

1. parser reserves/accepts `plot` and rejects assignment to the name `plot`;
2. `plot(V(x), x, 0, L)` reuses an existing symbolic function and numeric `q`, `L` values;
3. exact zero lower bound is promoted to metres when `L` is in metres;
4. x samples contain 201 points and include 0 m and 4 m;
5. propped-cantilever `M(x)` samples reproduce the known boundary values, including `M(L) = 0 tonf·m` with dimensional zero;
6. a pre-existing `x := 2.5*m` is not mutated and does not collapse the plot to one point;
7. missing `q` produces a concise error naming `q`;
8. incompatible bound units fail clearly;
9. reversed/equal bounds fail clearly;
10. plot adapter labels x/y axes with normalized units and creates a horizontal zero line;
11. `%%eng` flushes equations before a plot and resumes equations afterward in source order;
12. existing symbolic/numeric/render tests remain green;
13. release wheel declares/installs Matplotlib and reports version 0.3.0.

## Explicit non-goals for 0.3.0

The following are intentionally deferred:

- multiple curves in one `plot()`;
- `plots(...)` or subplots;
- keyword/style arguments;
- colors, line styles, markers, legends, fills, or themes controlled from EngCalc syntax;
- explicit x/y target-unit conversion inside `plot`;
- annotations of maxima, minima, roots, reactions, or characteristic points;
- automatic structural-diagram sign inversion;
- piecewise/discontinuous-function handling and jump markers;
- logarithmic axes;
- 3D plots;
- exporting/saving image files from EngCalc;
- arbitrary Matplotlib access.

These can be layered later without changing the four-argument v0.3.0 contract.

## Alternatives considered

### A. Let `plot()` call Matplotlib directly inside the symbolic evaluator

Rejected. It couples symbolic evaluation to notebook graphics, makes tests more fragile, and makes a future non-notebook renderer harder.

### B. Parse `plot(...)` as a special top-level directive outside the normal expression parser

Rejected for 0.3.0. The existing restricted call grammar already provides the necessary safety and line-number/error infrastructure. A separate grammar path would duplicate parsing logic.

### C. Engine returns unit-normalized `PlotResult`; plotting adapter owns Matplotlib

Selected. It keeps symbolic/numeric evaluation deterministic and testable while isolating the side-effecting graphical layer.

## Release and compatibility

Target version: **0.3.0** because native graphical output is a new public capability rather than a 0.2.x corrective.

Existing notebooks without `plot(...)` must render identically to 0.2.9. Existing `%eng_config`, `%eng_reset`, `numeric(...)`, symbolic functions, and unit behavior remain unchanged.
