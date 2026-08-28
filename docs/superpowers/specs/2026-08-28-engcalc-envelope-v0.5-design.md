# EngCalc 0.5.0 — Engineering Envelope Design

Status: Ready for user review

Base checkpoint: EngCalc 0.4.0 on `main` at `8e2b629ae588f6166b2df1c48b1b3d08f42f9113`.

## 1. Goal

Add structural response envelopes to EngCalc with the smallest possible new user-facing surface and the smallest possible new implementation surface.

The guiding rule is:

> `envelope(...)` must feel exactly like `plot(...)`, reuse the same series-resolution pipeline, and only replace the final multi-series display with pointwise maximum/minimum envelopes.

This is intended to keep the feature simple to learn, fast to type, inexpensive to execute, and low-risk to maintain.

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

This definition is signed and algebraic.

It is NOT an absolute-value envelope.

For example, `+150 kN·m` and `-150 kN·m` remain distinct structural responses.

EngCalc must also retain, as metadata, the index of the governing source series at every point:

```text
governing_max(x_i) = argmax_j y_j(x_i)
governing_min(x_i) = argmin_j y_j(x_i)
```

This metadata is not required to be shown in the first 0.5.0 UI, but it must be available internally so future governing-combination displays do not require recomputing or redesigning the envelope core.

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
    -> PlotResult(kind="envelope", two envelope series + governing metadata)
```

There must NOT be a separate `EnvelopeEngine`.

This keeps:

- parser behavior;
- numeric evaluation;
- function expansion;
- units;
- sweep semantics;
- 201-point sampling;
- structural moment classification

on the existing 0.4.0 code path.

## 6. Result model

The smallest acceptable model change is to extend the plotting transport so the renderer can distinguish a normal comparison plot from an envelope plot.

Conceptually:

```python
PlotResult(
    ...,
    series=(...),
    kind="plot" | "envelope",
    governing_max=None | tuple[int, ...],
    governing_min=None | tuple[int, ...],
)
```

Alternative internal shapes are acceptable if they preserve these invariants:

- `PlotResult` remains the common rendering transport;
- no parallel envelope-specific renderer input model is introduced unless implementation evidence proves it necessary;
- a normal 0.4.0 plot continues to behave identically;
- envelope results carry exactly two displayed envelope series plus governing-source metadata.

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

Therefore:

- `M_max(x)` is the algebraic maximum even though it may appear lower on an inverted moment axis;
- `M_min(x)` is the algebraic minimum even though it may appear higher.

The implementation must not rename them based on screen position.

Mixed moment/non-moment inputs remain invalid on one envelope axis.

## 9. Default visual design

The default envelope figure intentionally shows ONLY the two envelope boundaries.

Original source curves are not drawn in 0.5.0.

This is the approved simplicity rule.

The envelope renderer should show:

- upper/algebraic-minimum boundary line;
- lower/algebraic-maximum boundary line, subject to axis convention;
- light translucent fill between the two boundaries;
- zero line;
- common x/y units;
- plot title identifying the response family when available;
- restrained characteristic-value display;
- structural moment-axis inversion when applicable.

There is no legend containing every source curve because the source curves are deliberately hidden.

The displayed boundary labels should use mathematically unambiguous wording such as:

```text
max
min
```

or equivalent `M_max`, `M_min` when a common family is known.

## 10. Characteristic values

The envelope visualization should report global characteristic values for the two envelope boundaries without placing dense boxes over the data region.

At minimum:

- global maximum envelope value and x-location;
- global minimum envelope value and x-location.

The renderer should reuse the visual lessons from 0.3.3/0.4.0 and avoid annotation overlap.

A compact external panel is preferred when inline callouts would collide with the envelope region.

Source-series governing metadata is retained internally but is not required to be rendered in 0.5.0.

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
7. for each sample index, compute algebraic max, min, argmax, and argmin;
8. create two displayed `PlotSeries`: envelope maximum and envelope minimum;
9. store governing indices as metadata;
10. return one `PlotResult(kind="envelope")`;
11. render one figure in normal `%%eng` source order.

For a sweep envelope, steps 3-11 are identical after the existing sweep expansion produces the normalized source series.

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
- sampling failures.

At least two source series must be available after request expansion for a meaningful envelope.

Therefore:

```text
envelope(M(x), x, 0, L)
```

without a sweep is invalid and should return a concise message equivalent to:

```text
envelope requires at least two response series
```

A single expression WITH a sweep is valid when the sweep expands to two or more series.

## 15. Performance

Envelope reduction is intentionally simple.

For `S` source series and the fixed `N=201` samples:

```text
O(S * N)
```

The reduction cost is negligible relative to expression evaluation.

No optimization subsystem is required.

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

Minimum coverage:

### Parser

1. accept multi-expression envelope;
2. accept one-expression sweep envelope;
3. reject unsupported keywords;
4. reject more than one sweep keyword;
5. reject empty sweep;
6. keep lists outside plot/envelope sweep rejected;
7. keep arbitrary calls/attributes/subscripts/comprehensions rejected.

### Engine

8. reject a one-series non-sweep envelope;
9. compute pointwise algebraic maximum correctly;
10. compute pointwise algebraic minimum correctly;
11. retain governing max indices;
12. retain governing min indices;
13. use the same 201 x samples as source plotting;
14. normalize compatible units before comparison;
15. reject incompatible y dimensions;
16. reject mixed moment/non-moment inputs;
17. support parameter sweep envelope;
18. preserve stored sweep parameter value;
19. preserve plotting-variable state;
20. preserve source-order/one-result semantics.

### Renderer

21. render exactly two response boundary lines for an envelope;
22. do not render original source curves;
23. fill only between envelope min/max;
24. retain zero line;
25. invert moment y-axis;
26. expose global max/min characteristic values without overlapping the main data area;
27. close pyplot figure after construction;
28. leave normal 0.4.0 plot tests unchanged and green.

### Integration/release

29. end-to-end multiple-expression envelope in `%%eng`;
30. end-to-end sweep envelope in `%%eng`;
31. existing full suite green;
32. package/runtime version 0.5.0;
33. build real 0.5.0 wheel;
34. install wheel in clean environment;
35. installed-wheel envelope smoke test.

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

- two envelope boundaries only;
- both in common moment units;
- moment positive-down;
- maximum envelope equals the larger algebraic response at every sampled x;
- minimum envelope equals the smaller algebraic response at every sampled x.

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

- sweep creates three hidden source series;
- displayed result contains only envelope max/min;
- q state remains unchanged after evaluation;
- characteristic extrema are readable.

### C. Signed structural responses

A test case must include responses of opposite sign so that signed algebraic behavior is explicit.

Expected:

```text
max(x) = algebraically greatest source value
min(x) = algebraically smallest source value
```

not maximum absolute magnitude.

## 19. Deferred roadmap

Possible later additions, deliberately excluded from 0.5.0:

- optional faint source-curve display;
- governing source labels by x interval;
- governing-source color bands;
- named load cases/combinations;
- exact crossover/intersection locations;
- adaptive sampling;
- absolute envelope with sign preservation;
- positive/negative design-envelope helpers;
- direct ETABS/SAP2000 response-set envelopes.

These should build on the stored governing metadata rather than alter the 0.5.0 core definition.

## 20. Acceptance criterion

EngCalc 0.5.0 is successful if a user who already knows `plot(...)` can obtain a correct structural envelope by replacing `plot` with `envelope`, with no extra declarations and no additional plotting API knowledge.
