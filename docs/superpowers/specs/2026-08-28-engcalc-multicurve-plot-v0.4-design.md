# EngCalc 0.4.0 — Multi-curve and parameter-sweep `plot()` Design

Date: 2026-08-28
Status: Ready for user review
Base checkpoint: EngCalc 0.3.3 (`81d743a`)

## Purpose

EngCalc 0.3.3 can plot one unit-aware engineering function at a time with:

```text
plot(expression, variable, start, end)
```

The next plotting capability must support engineering comparison workflows without forcing users back into a separate Python/Matplotlib cell. The primary use cases are:

1. overlay several compatible engineering functions on the same axes;
2. plot one function for several values of one load/parameter, such as several values of `q`;
3. preserve EngCalc state, units, moment-positive-down convention, and the polished 0.3.3 single-curve behavior.

This is a public-language extension, so the target release is **EngCalc 0.4.0**.

## Compatibility contract

The existing four-argument syntax remains valid and must render identically to EngCalc 0.3.3:

```text
plot(M(x), x, 0, L)
```

No existing notebook should need changes.

Single-curve plots retain:

- 201 deterministic samples including endpoints;
- Pint-aware x/y units;
- automatic horizontal zero line;
- current structural moment convention: positive moment plotted downward;
- current line/fill presentation;
- endpoint/extrema markers;
- EngCalc 0.3.3 smart max/min callouts;
- current source-order behavior inside `%%eng`.

## Public syntax

### 1. Multiple expressions on one plot

Canonical form:

```text
plot(expr1, expr2, ..., variable, start, end)
```

The final three positional arguments are always interpreted as:

```text
variable, start, end
```

Every preceding positional argument is a plotted expression. At least one expression is required.

Example:

```text
%%eng

M_D(x) = q_D*x*(L-x)/2
M_L(x) = q_L*x*(L-x)/2

q_D := 8*kN/m
q_L := 5*kN/m
L := 6*m

plot(M_D(x), M_L(x), x, 0, L)
```

The figure contains both curves on one shared axis and automatically displays a legend containing `M_D(x)` and `M_L(x)`.

### 2. One-expression parameter sweep

Canonical form:

```text
plot(expression, variable, start, end, parameter=[value1, value2, ...])
```

Example:

```text
%%eng

M(x) = q*x*(L-x)/2
L := 6*m

plot(
    M(x),
    x,
    0,
    L,
    q=[5*kN/m, 10*kN/m, 15*kN/m]
)
```

This produces three series on one shared axis with automatic labels equivalent to:

```text
q = 5 kN/m
q = 10 kN/m
q = 15 kN/m
```

The exact numeric formatting follows EngCalc's current numeric presentation settings where practical.

### Deliberately unsupported shorthand

The following shorthand is **not** part of 0.4.0:

```text
q=[5, 10, 15]*kN/m
```

Every sweep entry must be a complete EngCalc numerical expression:

```text
q=[5*kN/m, 10*kN/m, 15*kN/m]
```

Named numeric variables are also valid:

```text
q_1 := 5*kN/m
q_2 := 10*kN/m
q_3 := 15*kN/m
plot(M(x), x, 0, L, q=[q_1, q_2, q_3])
```

## Scope limits for 0.4.0

To keep the first multi-series release deterministic and understandable:

- only **one sweep parameter** is accepted per plot;
- a parameter sweep accepts exactly **one plotted expression**;
- multi-expression + sweep in the same `plot(...)` is rejected;
- nested/cartesian sweeps are deferred;
- named/dictionary cases such as `q={"D": ..., "1.2D+1.6L": ...}` are deferred;
- user-controlled colors, line styles, markers, axes, legends, and Matplotlib kwargs remain deferred;
- dual y-axes remain deferred.

These constraints leave a clean future path for labeled load combinations without making 0.4.0 a general plotting DSL.

## Parameter-sweep semantics

A sweep parameter is a **local numerical override** for that plot only.

If `q` already has a numeric assignment:

```text
q := 2.8*tonf/m
plot(M(x), x, 0, L, q=[2*tonf/m, 4*tonf/m])
```

then the two supplied values are used for the two plotted series, but the stored `q := 2.8*tonf/m` remains unchanged after the plot.

The same non-mutation rule applies to the plotting variable `x`.

The sweep parameter must occur in the symbolic plotted expression after EngCalc function expansion. Otherwise EngCalc raises a concise error rather than drawing duplicate curves.

Each sweep value must be fully numerical in the current `NumericContext` and all sweep values must be dimensionally compatible with one another. If the parameter already has a stored numerical value, sweep values must also be compatible with that stored dimensionality.

## Multi-series unit rules

All curves on one y-axis must be dimensionally compatible.

For each series:

1. EngCalc samples the expression using the shared x coordinates;
2. the series is internally normalized to a stable y unit;
3. every other series is converted to the first series' compatible y unit before rendering.

If two series have incompatible dimensions, the plot is rejected with a concise error such as:

```text
engcalc: line N: plot series have incompatible y dimensions
```

This intentionally blocks misleading combinations such as plotting shear and moment on the same ordinary y-axis.

The x-axis retains the 0.3.x bound normalization rules, including promotion of exact dimensionless zero when paired with a dimensional bound.

## Structural sign convention

A multi-series plot has one shared y-axis orientation.

EngCalc 0.4.0 classifies each series for the existing structural moment convention. If every series belongs to the moment family, the y-axis is inverted so positive moment remains downward.

A multi-expression plot that mixes moment-classified and non-moment-classified series is rejected rather than silently choosing inconsistent orientation semantics.

A parameter sweep inherits the classification of its single source expression, so a sweep of `M(x)` always retains positive-down moment presentation.

## Labels, title, and legend

### Single curve

No visible behavior change from 0.3.3.

### Parameter sweep

- title and y-axis quantity label use the source expression/function, e.g. `M(x)`;
- legend is automatic;
- each legend entry identifies the sweep parameter and value.

### Multiple expressions

- legend is automatic and uses each source display label, e.g. `M_D(x)`, `M_L(x)`;
- when all function labels clearly belong to one common family such as `M_*`, EngCalc uses that family for the title/y-axis quantity label, e.g. `M(x)`;
- otherwise the plot uses a neutral comparison title/quantity label while preserving the shared unit and exact series names in the legend.

Matplotlib's active color cycle assigns series colors. EngCalc does not hard-code a palette in the language contract.

## Multi-series visual policy

The current single-curve fill is useful for an isolated structural diagram but becomes visually muddy when several curves overlap.

Therefore:

- **one series:** preserve the existing line + translucent fill behavior;
- **two or more series:** render clean lines without area fills;
- the horizontal zero reference remains;
- each series may mark its characteristic extrema with restrained point markers;
- the legend is shown only when there is more than one series.

This preserves the existing diagram aesthetic while making comparisons readable.

## Characteristic values and anti-overlap policy

EngCalc 0.3.3 solved the single-curve max/min overlap problem with smart callouts. Reusing two callout boxes per series does not scale: a three-value `q` sweep would often place six labels at nearly identical x positions.

EngCalc 0.4.0 therefore uses two presentation modes:

### One series

Preserve the existing 0.3.3 in-plot max/min callouts unchanged.

### Two or more series

Do **not** place max/min text boxes over every curve. Instead, render a compact **characteristic-values panel** outside the plotting data area, associated with the figure. For each series it reports:

- series label;
- sampled maximum value and its x location;
- sampled minimum value and its x location.

The plot itself keeps small extrema markers in the corresponding series color so the panel values can be visually related to the curves without obscuring them.

This policy is deterministic and avoids relying on increasingly complex annotation-collision heuristics.

The panel is presentation-only; extrema continue to mean sampled extrema over the same 201 plot samples used by 0.3.x.

## Data model

The current `PlotResult` stores one `x_values`/`y_values` pair. Replace the single-series assumption with an explicit series model while keeping Matplotlib objects out of the engine.

Proposed models:

```python
@dataclass(frozen=True)
class PlotSeries:
    display_label: str
    y_values: tuple[Any, ...]
    is_moment: bool


@dataclass(frozen=True)
class PlotResult:
    statement: ParsedStatement
    variable: str
    x_values: tuple[Any, ...]
    series: tuple[PlotSeries, ...]
    display_label: str
```

`display_label` is plot-level presentation metadata (for example `M(x)` for a sweep), while every `PlotSeries` owns its legend label and normalized y samples.

The exact field names may be adjusted during implementation if tests reveal a clearer boundary, but the invariant is fixed: one `PlotResult` owns shared x data plus one or more immutable series records.

## Parser design

The 0.3.3 parser currently rejects all keyword arguments and does not allow `ast.List`. EngCalc 0.4.0 must not relax those restrictions globally.

### Positional multi-expression form

No new AST node type is needed. The evaluator interprets the final three positional arguments as `variable`, `start`, `end` and every earlier argument as a plotted expression.

### Sweep form

Add **call-aware restricted validation**:

- keyword arguments remain rejected for every EngCalc call except `plot`;
- `plot` accepts at most one keyword;
- the keyword name must be a valid non-reserved identifier and becomes the sweep parameter name;
- its value must be an `ast.List`;
- the list must be non-empty;
- list entries may contain only the already-supported EngCalc numerical-expression nodes/calls;
- list unpacking, comprehensions, attributes, subscripts, lambdas, dictionaries, tuples, arbitrary Python calls, and `**kwargs` remain forbidden.

`ast.List` is therefore not introduced as a general EngCalc value. It exists only as the syntactic container for a `plot` sweep keyword.

## Engine/evaluator design

Refactor the current `plot` handling into a small plot-request path rather than continuing to grow one `visit_Call()` branch.

Responsibilities:

1. parse the `plot` call shape into either:
   - single/multi-expression request; or
   - single-expression sweep request;
2. resolve the plotting variable and bounds once;
3. normalize bounds and construct the common 201 x samples once;
4. expand each symbolic expression/function;
5. evaluate each series using local numerical overrides;
6. normalize y units across series;
7. construct immutable `PlotSeries` records;
8. determine plot-level structural orientation/presentation metadata;
9. return `PlotResult` without mutating symbolic or numeric state.

The symbolic engine remains independent from Matplotlib.

### Sweep evaluation

The numeric sampling boundary should gain a controlled local-override mechanism so one series can evaluate with:

```text
{q: sweep_value}
```

while every other known numeric symbol continues to come from `NumericContext`.

No sweep assignment is persisted.

## Plotting adapter design

`src/engcalc_colab/plotting.py` remains the only Matplotlib-aware module.

Refactor `render_plot(result)` from one hard-coded y series to iteration over `result.series`.

It owns:

- Matplotlib line creation and color assignment;
- one-series fill vs multi-series line-only policy;
- zero line;
- moment-axis inversion from plot-level series classification;
- legend creation;
- per-series extrema markers;
- existing smart callouts for single-series plots;
- external characteristic-values panel for multi-series plots;
- shared unit labels, title, margins, grid, and figure layout;
- closing the pyplot-managed figure before returning it.

The adapter still receives only normalized quantities and presentation metadata.

## Magic/source-order behavior

No change is required to the high-level notebook sequencing contract.

A multi-series `PlotResult` is still one output-producing statement:

1. flush pending MathJax calculation rows;
2. render/display one Matplotlib figure;
3. continue with following EngCalc statements.

One `plot(...)` call always yields exactly one figure.

## Error contract

Required concise failures include:

- fewer than four positional arguments;
- no plotted expression before `variable, start, end`;
- non-identifier plotting variable;
- more than one sweep keyword;
- sweep keyword used with multiple expressions;
- empty sweep list;
- unsupported/non-numeric sweep entry;
- sweep parameter absent from the expanded expression;
- incompatible sweep-value dimensions;
- incompatible y dimensions between plotted series;
- mixed moment/non-moment classification in one multi-expression plot;
- existing bound and sampling failures from 0.3.x.

Errors remain line-aware `EngCalcError` messages without raw tracebacks and must not mutate EngCalc state.

## Security invariants

The feature must preserve EngCalc's restricted-language model.

In particular:

- no Python `eval`/`exec`;
- no Matplotlib objects/functions exposed to `%%eng`;
- no arbitrary keyword arguments;
- no attribute access;
- no subscripting into Python objects;
- no list comprehensions/generators;
- no file/network/callback access;
- sweep lists are parsed/evaluated only as EngCalc numeric expressions.

The parser should special-case only the narrow `plot(..., parameter=[...])` grammar rather than enabling Python collection syntax globally.

## TDD acceptance coverage

Implementation starts with failing tests for at least the following:

### Parser

1. existing four-argument `plot(M(x), x, 0, L)` remains accepted;
2. positional multi-expression `plot(M_D(x), M_L(x), x, 0, L)` is accepted;
3. `plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])` is accepted;
4. keyword arguments on non-`plot` calls remain rejected;
5. more than one plot keyword is rejected;
6. empty sweep list is rejected;
7. unsupported list syntax/comprehensions/unpacking is rejected;
8. list syntax outside the sweep slot remains rejected.

### Engine/numeric

9. multi-expression result contains two normalized series on one shared x grid;
10. sweep result contains one series per supplied q value;
11. sweep labels preserve the parameter/value identity;
12. a stored global q value is not mutated by a sweep;
13. a stored x value is not mutated;
14. missing sweep parameter in the expression fails clearly;
15. incompatible sweep-value dimensions fail clearly;
16. incompatible y dimensions between expressions fail clearly;
17. mixed moment/non-moment multi-expression classification fails clearly;
18. all-moment multi-series plots preserve positive-down orientation metadata;
19. 201 common x samples and endpoint behavior remain unchanged.

### Plotting adapter

20. single-series rendering remains visually/structurally compatible with 0.3.3 behavior;
21. multi-series rendering creates one line per series and no area fills;
22. multi-series rendering creates a legend;
23. moment multi-series axis is inverted;
24. multi-series extrema use small per-series markers;
25. multi-series characteristic values are rendered outside the data area rather than as overlapping in-plot callout boxes;
26. figure is closed from pyplot's registry before return.

### Integration/release

27. `%%eng` displays one figure for one multi-series plot in correct source order;
28. all existing tests remain green;
29. clean wheel installation passes the complete test suite;
30. runtime/package version reports 0.4.0.

## Acceptance examples

### A. Existing behavior remains unchanged

```text
%%eng
q := 2.8*tonf/m
L := 4*m
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2
plot(M(x), x, 0, L)
```

Expected: one EngCalc 0.3.3-style moment diagram with positive moment downward and smart max/min callouts.

### B. Multiple engineering functions

```text
%%eng
q_D := 8*kN/m
q_L := 5*kN/m
L := 6*m
M_D(x) = q_D*x*(L-x)/2
M_L(x) = q_L*x*(L-x)/2
plot(M_D(x), M_L(x), x, 0, L)
```

Expected: one positive-down moment figure, two line series, legend, no overlapping area fills, and an external characteristic-values panel.

### C. Parameter sweep

```text
%%eng
L := 6*m
M(x) = q*x*(L-x)/2
plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
```

Expected: one positive-down moment figure, three line series, legend keyed by q, and max/min values for each series in the characteristic-values panel. No persistent q assignment is created or changed by the plot.

## Deferred follow-up: labeled load combinations

A future release may support an explicit labeled-case syntax, for example conceptually:

```text
plot(M(x), x, 0, L, q={
    "D": q_D,
    "L": q_L,
    "D + L": q_D + q_L,
    "1.2D + 1.6L": 1.2*q_D + 1.6*q_L
})
```

This is intentionally excluded from 0.4.0 because it requires a safe string/dictionary grammar and introduces a second concern—case naming—beyond the core multi-series engine. The 0.4.0 `PlotSeries` model is designed so labeled cases can be added later without replacing the renderer architecture.

## Alternatives considered

### A. Require users to define `M_1(x)`, `M_2(x)`, `M_3(x)` for every q value

Rejected. It duplicates engineering formulas and defeats the purpose of EngCalc's persistent symbolic context.

### B. Add a separate `plots(...)` or Matplotlib-like API

Rejected. One canonical `plot(...)` language feature is easier to learn and keeps existing notebooks coherent.

### C. Allow arbitrary Python-style lists/keywords globally

Rejected. It unnecessarily weakens the restricted grammar. Only the narrow sweep container is needed.

### D. Put max/min callout boxes on every multi-series curve

Rejected. Parameter sweeps commonly place extrema at the same x coordinates, making overlap inevitable. A characteristic-values panel is more legible and deterministic.

### E. Shared-x `PlotResult` with explicit immutable `PlotSeries`

Selected. It matches the real comparison problem, keeps evaluation testable, and preserves the existing parser/engine/plotting separation.

## Release and compatibility

Target version: **0.4.0**.

Reason: this extends the public `plot(...)` language and `PlotResult` model rather than correcting an existing 0.3.x behavior.

EngCalc 0.4.0 must preserve all 0.3.3 single-curve notebook behavior unless a regression test explicitly demonstrates an unavoidable conflict. The multi-series path is additive; it must not be used as justification for unrelated refactoring of symbolic, numeric, MathJax, or configuration behavior.
