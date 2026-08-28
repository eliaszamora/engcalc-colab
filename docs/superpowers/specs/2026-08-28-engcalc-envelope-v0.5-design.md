# EngCalc 0.5.0 — Engineering Envelope Design

Status: Ready for user review

Base checkpoint: EngCalc 0.4.0 on `main` at `8e2b629ae588f6166b2df1c48b1b3d08f42f9113`.

## 1. Goal

Add structural response envelopes with the smallest possible new user-facing and implementation surface.

The governing rule is:

> `envelope(...)` must feel exactly like `plot(...)`, reuse the same series-resolution pipeline, and only replace the final multi-series display with pointwise algebraic maximum/minimum envelopes.

The user should be able to obtain an envelope by changing essentially one word: `plot` -> `envelope`.

## 2. Public syntax

### Multiple expressions

```text
envelope(expr1, expr2, ..., variable, start, end)
```

Example:

```text
%%eng

M_1(x) = ...
M_2(x) = ...
M_3(x) = ...

envelope(M_1(x), M_2(x), M_3(x), x, 0, L)
```

### One-parameter sweep

```text
envelope(expression, variable, start, end, parameter=[value1, value2, ...])
```

Example:

```text
%%eng

L := 6*m
M(x) = q*x*(L-x)/2

envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
```

The sweep grammar is exactly the restricted one introduced by `plot(...)` in 0.4.0.

Only one sweep parameter is supported. Multi-expression + sweep is not supported in the same call.

## 3. Mathematical definition

`envelope(...)` is a signed algebraic envelope.

For source series `y_j(x)` on the common sampled abscissas `x_i`:

```text
y_max(x_i) = max_j y_j(x_i)
y_min(x_i) = min_j y_j(x_i)
```

It is NOT an absolute-value envelope.

EngCalc also retains:

```text
governing_max(x_i) = argmax_j y_j(x_i)
governing_min(x_i) = argmin_j y_j(x_i)
```

and a stable ordered tuple of source-series labels so each governing index remains meaningful after the source curves are hidden:

```text
source_labels = (label_0, label_1, ..., label_n)
```

This governing metadata is stored in 0.5.0 but is not required to be displayed yet.

## 4. Sampling and units

Envelope evaluation reuses the exact `plot(...)` 0.4.0 numerical contract:

- one common x domain;
- 201 uniformly spaced samples;
- Pint-aware bounds;
- local non-mutating sweep overrides;
- no persistence of the plotting variable;
- compatible source y-series converted to one common unit before comparison.

No adaptive sampling or symbolic intersection solver is introduced in 0.5.0.

Therefore the 0.5.0 envelope is explicitly a sampled envelope over the same 201 points used by plotting.

## 5. Minimal architecture

There must NOT be a separate `EnvelopeEngine`.

The existing 0.4.0 plot path should be factored so the difficult part is shared:

```text
_resolve_plot_series(...)
    -> x_values
    -> normalized source PlotSeries[]
    -> common display metadata
```

Then:

```text
plot(...)
    -> _resolve_plot_series(...)
    -> PlotResult(kind="plot", original source series)
```

and:

```text
envelope(...)
    -> _resolve_plot_series(...)
    -> pointwise max/min + argmax/argmin
    -> PlotResult(kind="envelope", two displayed envelope series)
```

This preserves one implementation path for:

- parsing;
- function expansion;
- numeric evaluation;
- units;
- sweep semantics;
- 201-point sampling;
- structural moment classification.

## 6. Result model

`PlotResult` remains the common renderer transport.

Conceptually it gains envelope metadata:

```python
PlotResult(
    ...,
    series=(...),
    kind="plot" | "envelope",
    source_labels=(),
    governing_max=None | tuple[int, ...],
    governing_min=None | tuple[int, ...],
)
```

For a normal `plot`, current behavior remains unchanged.

For an `envelope`:

- `series` contains exactly two displayed series: algebraic maximum and algebraic minimum;
- `source_labels` preserves the ordered identity of the hidden source series;
- `governing_max` and `governing_min` point into `source_labels`.

An equivalent internal shape is acceptable if these invariants remain true.

## 7. Dimensional and structural rules

Every source response series must be dimensionally compatible on one y axis.

Valid examples:

- multiple moments;
- multiple shears;
- multiple displacements.

Invalid examples:

- moment + shear;
- incompatible sweep dimensions.

All source series are normalized to the first source series' y unit before pointwise comparison.

Mixed moment/non-moment structural families remain invalid on one envelope axis.

## 8. Moment convention

Moment envelopes preserve the approved EngCalc convention:

- mathematical positive moment is displayed downward;
- mathematical negative moment is displayed upward.

`max` and `min` ALWAYS mean algebraic maximum and minimum, never visual lower/upper position.

The specification deliberately avoids the terms “upper envelope” and “lower envelope” because they become ambiguous when the y axis is inverted.

## 9. Default visual design

The 0.5.0 default figure shows ONLY the two envelope boundaries.

The original source curves are deliberately hidden.

The renderer shows:

- algebraic maximum boundary line;
- algebraic minimum boundary line;
- light translucent fill between those two boundaries;
- zero line;
- common x/y units;
- response-family title where available;
- restrained characteristic-value display;
- moment-axis inversion when applicable.

No legend containing every hidden source curve is shown.

Boundary labels use mathematically explicit wording such as `max` / `min`, or `M_max` / `M_min` when a common moment family is known.

## 10. Characteristic values

At minimum, the figure reports:

- global algebraic maximum envelope value and x-location;
- global algebraic minimum envelope value and x-location.

These values must not obscure the envelope region. A compact external panel is preferred when inline callouts would collide with the data.

Governing source identities are retained internally but not displayed in 0.5.0.

## 11. Parser design and safety

`envelope` is added to the restricted EngCalc call allow-list.

The existing special restricted sweep-list validator is generalized only enough to support:

```text
plot(..., q=[...])
envelope(..., q=[...])
```

General Python lists and arbitrary keyword arguments remain unsupported.

No `eval`, `exec`, attributes, subscripts, comprehensions, dictionaries, lambdas, callbacks, filesystem access, or network access are introduced.

## 12. Evaluation flow

For multiple expressions:

1. parse using the same positional contract as `plot`;
2. resolve variable and bounds once;
3. create the common 201-point x grid;
4. evaluate each source response using the shared 0.4.0 series path;
5. normalize y units;
6. verify structural-family compatibility;
7. require at least two source series;
8. compute max/min/argmax/argmin at every sample index;
9. construct exactly two displayed envelope `PlotSeries`;
10. retain ordered source labels and governing indices;
11. return one `PlotResult(kind="envelope")`;
12. render one figure in normal `%%eng` source order.

For a parameter sweep, the existing sweep expansion first produces the hidden source series, after which steps 5-12 are identical.

## 13. State semantics

Envelope evaluation is non-mutating:

- an existing stored sweep parameter is unchanged;
- the plotting variable is not persisted;
- symbolic functions and namespace are unchanged;
- only the returned envelope result is new.

## 14. Minimum source count

A meaningful envelope requires at least two source series after expansion.

Therefore this is invalid:

```text
envelope(M(x), x, 0, L)
```

with a concise error equivalent to:

```text
envelope requires at least two response series
```

A one-expression sweep is valid only if its list expands to at least two series.

## 15. Performance

Envelope reduction is a direct sampled reduction:

```text
O(S * 201)
```

for `S` source series.

Its cost is negligible relative to source expression evaluation. No optimization subsystem is needed.

## 16. Backward compatibility

EngCalc 0.5.0 must preserve all 0.4.0 plotting behavior:

- single-series plot rendering unchanged;
- multi-series plot rendering unchanged;
- sweep plotting unchanged;
- parser restrictions unchanged except adding `envelope` to the same safe display-call family;
- units unchanged;
- 201-point sampling unchanged;
- moment positive-down convention unchanged.

`envelope(...)` is purely additive.

## 17. TDD acceptance coverage

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
11. retain ordered source labels;
12. retain governing max indices;
13. retain governing min indices;
14. use the same 201 x samples as plot;
15. normalize compatible units before comparison;
16. reject incompatible y dimensions;
17. reject mixed moment/non-moment inputs;
18. support parameter sweep envelope;
19. preserve stored sweep parameter state;
20. preserve plotting-variable state.

### Renderer

21. render exactly two envelope boundary lines;
22. do not render original source curves;
23. fill only between max/min boundaries;
24. retain zero line;
25. invert moment y-axis;
26. expose global max/min characteristic values outside or clear of the data region;
27. close pyplot figure after construction;
28. keep all existing 0.4.0 plot renderer tests green.

### Integration/release

29. end-to-end multiple-expression envelope in `%%eng`;
30. end-to-end sweep envelope in `%%eng`;
31. existing full suite green;
32. package/runtime version 0.5.0;
33. build real 0.5.0 wheel;
34. install wheel in a clean environment;
35. installed-wheel envelope smoke test.

## 18. Canonical acceptance examples

### Multiple response functions

```text
%%eng

L := 6*m
q1 := 5*kN/m
q2 := 8*kN/m

M_1(x) = q1*x*(L-x)/2
M_2(x) = q2*x*(L-x)/2

envelope(M_1(x), M_2(x), x, 0, L)
```

Expected: only max/min boundaries are displayed, in common moment units, with positive moment downward.

### Parameter sweep

```text
%%eng

L := 6*m
M(x) = q*x*(L-x)/2

envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
```

Expected: three hidden source series are reduced to two displayed envelope boundaries; stored `q` remains unchanged.

### Signed response test

Acceptance must include opposite-sign source responses to prove that `max/min` are algebraic, not absolute-magnitude operations.

## 19. Deliberately deferred

- showing faint source curves;
- governing source labels by x interval;
- governing-source color bands;
- named load cases/combinations;
- exact crossover/intersection locations;
- adaptive sampling;
- absolute envelope;
- positive/negative design-envelope helpers;
- direct ETABS/SAP2000 response-set envelopes.

The stored `source_labels + governing indices` metadata is intended to support those later without changing the 0.5.0 envelope definition.

## 20. Acceptance criterion

EngCalc 0.5.0 succeeds if a user who already understands `plot(...)` can obtain a correct structural envelope simply by replacing `plot` with `envelope`, without extra declarations or plotting API knowledge.
