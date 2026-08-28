# EngCalc 0.5.0 — Engineering Envelope Design

Status: Approved

Base checkpoint: EngCalc 0.4.0 on `main` at `8e2b629ae588f6166b2df1c48b1b3d08f42f9113`.

## 1. Goal

Add structural response envelopes with the smallest possible new user-facing and implementation surface.

The governing rule is:

> `envelope(...)` must feel like `plot(...)`, reuse the same series-resolution pipeline, and replace the final display with algebraic pointwise maximum/minimum envelopes while keeping the original source curves visible as faint context.

This keeps the feature simple to learn, fast to type, inexpensive to execute, and low-risk to maintain.

## 2. Public syntax

EngCalc 0.5.0 adds one new public function: `envelope`.

### 2.1 Multiple expressions

```text
envelope(expr1, expr2, ..., variable, start, end)
```

Example:

```text
%%eng

L := 6*m

M_1(x) = ...
M_2(x) = ...
M_3(x) = ...

envelope(M_1(x), M_2(x), M_3(x), x, 0, L)
```

The final three positional arguments have exactly the same meaning as in `plot(...)`:

- plotting variable;
- lower bound;
- upper bound.

Every preceding positional argument is one response series included in the envelope.

### 2.2 One-parameter sweep

The same restricted sweep grammar introduced in EngCalc 0.4.0 is supported:

```text
envelope(expression, variable, start, end, parameter=[value1, value2, ...])
```

Example:

```text
%%eng

L := 6*m
M(x) = q*x*(L-x)/2

envelope(
    M(x),
    x,
    0,
    L,
    q=[5*kN/m, 10*kN/m, 15*kN/m]
)
```

Only one sweep parameter is supported in 0.5.0, exactly as in `plot(...)` 0.4.0.

### 2.3 Deliberately unsupported in 0.5.0

The following remain out of scope:

- multiple simultaneous sweep parameters;
- named/dictionary cases;
- multi-expression plus sweep in the same call;
- user-facing Matplotlib kwargs;
- dual axes;
- analytical curve intersection solving;
- absolute envelopes;
- positive-only or negative-only envelope operators.

## 3. Mathematical definition

`envelope(...)` means algebraic pointwise maximum and minimum.

For response series `y_j(x)` sampled at the common EngCalc abscissas `x_i`:

```text
y_max(x_i) = max_j y_j(x_i)
y_min(x_i) = min_j y_j(x_i)
```

This definition is signed and algebraic. It is NOT an absolute-value envelope.

For example, `+150 kN·m` and `-150 kN·m` remain distinct structural responses.

EngCalc must also retain, as metadata, the index of the governing source series at every point:

```text
governing_max(x_i) = argmax_j y_j(x_i)
governing_min(x_i) = argmin_j y_j(x_i)
```

It must also retain the ordered source-series labels corresponding to those indices.

This metadata is not required to be fully shown in the first 0.5.0 UI, but it must be available internally so future governing-combination displays do not require recomputing or redesigning the envelope core.

## 4. Sampling policy

Envelope evaluation reuses the exact sampling contract of `plot(...)` 0.4.0:

- one common x domain;
- 201 uniformly spaced samples;
- Pint-aware x bounds;
- no mutation of EngCalc stored numeric state;
- the same local sweep override behavior;
- all input y-series converted to one compatible y unit before envelope reduction.

No new adaptive sampling or symbolic intersection solver is introduced in 0.5.0.

The envelope is therefore explicitly a sampled envelope over the same 201 points used by plotting.

## 5. Simplified architecture

The main implementation objective is to avoid a second evaluation engine.

The existing 0.4.0 `_evaluate_plot()` currently performs two conceptually separate jobs:

1. resolve the user request into normalized `x_values + PlotSeries[]`;
2. package those series as a normal plot result.

For 0.5.0, that first job should be extracted into a shared internal helper, conceptually:

```text
_resolve_plot_series(...)
    -> x_values
    -> normalized PlotSeries[]
    -> common display metadata
```

Then:

```text
plot(...)
    -> _resolve_plot_series(...)
    -> PlotResult(kind="plot", original series)
```

and:

```text
envelope(...)
    -> _resolve_plot_series(...)
    -> pointwise min/max reduction
    -> PlotResult(kind="envelope", two envelope series + original source series + governing metadata)
```

There must NOT be a separate `EnvelopeEngine`.

This keeps parser behavior, numeric evaluation, function expansion, units, sweep semantics, 201-point sampling, and structural moment classification on the existing 0.4.0 code path.

## 6. Result model

The smallest acceptable model change is to extend the plotting transport so the renderer can distinguish a normal comparison plot from an envelope plot.

Conceptually:

```python
PlotResult(
    ...,
    series=(...),
    kind="plot" | "envelope",
    source_series=(),
    source_labels=(),
    governing_max=None | tuple[int, ...],
    governing_min=None | tuple[int, ...],
)
```

Alternative internal shapes are acceptable if they preserve these invariants:

- `PlotResult` remains the common rendering transport;
- no parallel envelope-specific renderer input model is introduced unless implementation evidence proves it necessary;
- a normal 0.4.0 plot continues to behave identically;
- envelope results carry exactly two displayed envelope series;
- envelope results retain the original normalized source series for faint rendering;
- ordered source labels and governing indices remain available for later governing-case displays.

## 7. Dimensional rules

The envelope requires every source series to be dimensionally compatible on the same y axis.

This is the same rule as multi-series `plot(...)` 0.4.0.

Examples:

- multiple moment series: valid;
- multiple shear series: valid;
- moment plus shear: invalid;
- incompatible sweep values: invalid.

All source series are normalized to the first series' y unit before pointwise comparison.

## 8. Structural moment convention

If the source family is a moment family, the envelope plot preserves the approved EngCalc structural convention:

- mathematical positive moment appears downward;
- mathematical negative moment appears upward.

The pointwise maximum/minimum remains mathematical, not visual.

Therefore `M_max(x)` is the algebraic maximum even though it may appear lower on an inverted moment axis, and `M_min(x)` is the algebraic minimum even though it may appear higher.

The implementation must not rename them based on screen position.

Mixed moment/non-moment inputs remain invalid on one envelope axis.

## 9. Default visual design

The default envelope figure shows both the envelope boundaries and the original source curves in a subdued way.

The envelope renderer should show:

- all original source curves as thin, faint background lines;
- envelope maximum boundary line;
- envelope minimum boundary line;
- light translucent fill between the two envelope boundaries;
- zero line;
- common x/y units;
- plot title identifying the response family when available;
- restrained characteristic-value display;
- structural moment-axis inversion when applicable.

The source curves must remain visually secondary to the envelope boundaries:

- thinner linewidth than the envelope boundaries;
- noticeably lower opacity;
- no markers on source curves;
- no source-curve value callouts.

There is no requirement to show a full legend entry for every source curve in 0.5.0. A minimal legend limited to the two envelope boundaries is preferred.

The displayed boundary labels use mathematically unambiguous wording such as `max` / `min`, or equivalent `M_max` / `M_min` when a common family is known.

## 10. Characteristic values

The envelope visualization should report global characteristic values for the two envelope boundaries without placing dense boxes over the data region.

At minimum:

- global maximum envelope value and x-location;
- global minimum envelope value and x-location.

The renderer should reuse the visual lessons from 0.3.3/0.4.0 and avoid annotation overlap.

A compact external panel is preferred when inline callouts would collide with the envelope region.

Source-series governing metadata is retained internally but is not required to be fully rendered in 0.5.0.

## 11. Parser design

`envelope` is added to the restricted EngCalc call allow-list.

Its grammar is intentionally identical to `plot` for the supported forms.

The existing special-case restricted sweep-list validator should be generalized narrowly so it can validate the same one-keyword list syntax for both:

```text
plot(..., q=[...])
envelope(..., q=[...])
```

Do not enable arbitrary keyword arguments or general Python lists.

Lists remain valid only as the special sweep container for these supported engineering display calls.

No `eval`, `exec`, attributes, subscripts, comprehensions, dictionary literals, lambdas, arbitrary callbacks, filesystem access, or network access are introduced.

## 12. Evaluation flow

For `envelope(expr1, expr2, ..., x, x0, x1)`:

1. parse with the same restricted positional grammar as multi-series `plot`;
2. resolve x variable and bounds once;
3. generate the shared 201-point x grid;
4. expand/evaluate every source response series using the 0.4.0 numeric path;
5. normalize every y series to a common compatible unit;
6. verify common structural orientation family;
7. require at least two source response series after expansion;
8. for each sample index, compute algebraic max, min, argmax, and argmin;
9. create two displayed `PlotSeries`: envelope maximum and envelope minimum;
10. retain the normalized source series for faint rendering;
11. store governing indices and ordered source labels as metadata;
12. return one `PlotResult(kind="envelope")`;
13. render one figure in normal `%%eng` source order.

For a sweep envelope, the existing sweep expansion first produces the normalized source series, after which the same reduction path is used.

## 13. State semantics

Envelope evaluation must be non-mutating in exactly the same way as 0.4.0 sweep plotting.

Examples:

- if `q` already has a stored value, `envelope(..., q=[...])` does not replace it;
- the plotting variable `x` is never persisted by sampling;
- user functions and symbolic namespace are unchanged;
- only the returned plotting/envelope result is new.

## 14. Error behavior

Reuse existing `plot(...)` errors wherever the cause is shared.

Envelope-specific or shared validation must cover:

- too few positional arguments;
- no source expression;
- non-identifier x variable;
- multiple sweep keywords;
- sweep plus multiple source expressions;
- empty sweep;
- unsupported sweep syntax;
- sweep parameter absent from expanded expression;
- incompatible sweep dimensions;
- incompatible y-series dimensions;
- mixed moment/non-moment series;
- invalid bounds;
- sampling failures;
- fewer than two source series after expansion.

Therefore `envelope(M(x), x, 0, L)` without a sweep is invalid and should return a concise message equivalent to:

```text
envelope requires at least two response series
```

A single expression WITH a sweep is valid only when the sweep expands to two or more series.

## 15. Performance

Envelope reduction is intentionally simple.

For `S` source series and the fixed `N=201` samples:

```text
O(S * N)
```

The reduction cost is negligible relative to expression evaluation.

Rendering the faint source curves adds only a small linear drawing cost and does not justify a separate optimization subsystem.

## 16. Backward compatibility

EngCalc 0.5.0 must preserve all EngCalc 0.4.0 `plot(...)` behavior.

In particular:

- existing single-series plot rendering remains unchanged;
- existing multi-series plot rendering remains unchanged;
- existing sweep plots remain unchanged;
- all current parser restrictions remain in force;
- moment positive-down convention remains unchanged;
- current units and 201-point sampling remain unchanged.

`envelope(...)` is additive.

## 17. TDD acceptance coverage

Implementation must be driven by RED -> GREEN tests.

### Parser

1. accept multi-expression envelope;
2. accept one-expression sweep envelope;
3. reject unsupported/multiple sweep keywords;
4. reject empty sweep;
5. keep lists outside plot/envelope sweep rejected;
6. keep attributes, subscripts, comprehensions, arbitrary calls, and dictionaries rejected.

### Engine

7. reject one-source non-sweep envelope;
8. reject a sweep that expands to fewer than two source series;
9. compute pointwise algebraic maximum correctly;
10. compute pointwise algebraic minimum correctly;
11. retain source series in normalized order;
12. retain ordered source labels;
13. retain governing max indices;
14. retain governing min indices;
15. use the same 201 x samples as plot;
16. normalize compatible units before comparison;
17. reject incompatible y dimensions;
18. reject mixed moment/non-moment inputs;
19. support parameter sweep envelope;
20. preserve stored sweep parameter state;
21. preserve plotting-variable state.

### Renderer

22. render exactly two emphasized envelope boundary lines;
23. render original source curves faintly behind the envelope;
24. source curves have lower linewidth/opacity than envelope boundaries;
25. source curves have no markers or callout boxes;
26. fill only between max/min boundaries;
27. retain zero line;
28. invert moment y-axis;
29. expose global max/min characteristic values outside or clear of the data region;
30. close pyplot figure after construction;
31. keep all existing 0.4.0 plot renderer tests green.

### Integration/release

32. end-to-end multiple-expression envelope in `%%eng`;
33. end-to-end sweep envelope in `%%eng`;
34. existing full suite green;
35. package/runtime version 0.5.0;
36. build real 0.5.0 wheel;
37. install wheel in a clean environment;
38. installed-wheel envelope smoke test.

## 18. Canonical acceptance examples

### A. Multiple response functions

```text
%%eng

L := 6*m
q1 := 5*kN/m
q2 := 8*kN/m

M_1(x) = q1*x*(L-x)/2
M_2(x) = q2*x*(L-x)/2

envelope(M_1(x), M_2(x), x, 0, L)
```

Expected:

- two emphasized envelope boundaries;
- original source curves visible faintly behind them;
- common moment units;
- positive moment downward;
- algebraic maximum/minimum correct at every sampled x.

### B. Parameter sweep

```text
%%eng

L := 6*m
M(x) = q*x*(L-x)/2

envelope(
    M(x),
    x,
    0,
    L,
    q=[5*kN/m, 10*kN/m, 15*kN/m]
)
```

Expected:

- sweep creates three faint source series;
- two emphasized envelope boundaries are displayed;
- stored `q` remains unchanged;
- characteristic extrema are readable.

### C. Signed response test

Acceptance must include opposite-sign source responses to prove that `max/min` are algebraic, not absolute-magnitude operations.

## 19. Deliberately deferred

- governing source labels by x interval;
- governing-source color bands;
- named load cases/combinations;
- exact crossover/intersection locations;
- adaptive sampling;
- absolute envelope;
- positive/negative design-envelope helpers;
- direct ETABS/SAP2000 response-set envelopes.

These should build on the stored source series and governing metadata rather than alter the 0.5.0 envelope definition.

## 20. Acceptance criterion

EngCalc 0.5.0 succeeds if a user who already understands `plot(...)` can obtain a correct structural envelope simply by replacing `plot` with `envelope`, without extra declarations or plotting API knowledge, while still seeing the original response curves faintly in the background.
