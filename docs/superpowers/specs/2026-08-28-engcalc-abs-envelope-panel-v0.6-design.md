# EngCalc 0.6.0 — Absolute-Value Envelope Composition and In-Axes Panels

Status: Approved design, pending written-spec review

Base checkpoint: EngCalc 0.5.0 on `main` at `01fe42376f61e7d0d3738049f01935368e2c2e16`.

## 1. Goal

EngCalc 0.6.0 adds two tightly related improvements:

1. a general safe `abs(...)` operation that composes naturally with `plot(...)`, `numeric(...)`, symbolic expressions, and `envelope(...)`;
2. characteristic-value panels rendered inside the plotting axes with automatic corner placement, removing the current reserved right-hand margin.

The user-facing design must remain compact. No new public `abs_envelope(...)` or `envelope_abs(...)` function is introduced.

## 2. Public mathematical operation: `abs(...)`

`abs(expression)` becomes a normal EngCalc symbolic function.

Examples:

```text
A = abs(x)
plot(abs(V(x)), x, 0, L)
numeric(abs(P))
```

Internally the symbolic operation is represented with SymPy `Abs` and remains inside EngCalc's restricted AST/evaluation model.

### 2.1 Arity

`abs(...)` accepts exactly one positional argument and no keyword arguments.

Invalid:

```text
abs()
abs(a, b)
abs(x, mode=1)
```

### 2.2 Safety

Adding `abs` must not enable arbitrary Python builtins or arbitrary call dispatch. It is added explicitly to the EngCalc allow-list and evaluator, just like other supported symbolic operations.

## 3. Existing algebraic envelope remains unchanged

The EngCalc 0.5.0 contract remains valid:

```text
envelope(M_constr(x), M_uso(x), x, 0, L)
```

computes sampled signed algebraic boundaries:

```text
M_max(x_i) = max_j M_j(x_i)
M_min(x_i) = min_j M_j(x_i)
```

The plot retains both algebraic branches, source curves, governing indices, dimensional checks, sweep behavior, and the moment-positive-down convention.

## 4. Magnitude envelope through composition

When every source response passed to `envelope(...)` is explicitly wrapped at the outermost level in `abs(...)`, the request becomes a magnitude envelope.

Canonical multi-expression form:

```text
envelope(
    abs(V_constr(x)),
    abs(V_uso(x)),
    x, 0, L
)
```

Canonical sweep form:

```text
envelope(
    abs(V(x)),
    x, 0, L,
    q=[2*tonf/m, 3*tonf/m, 4*tonf/m]
)
```

### 4.1 Mathematical definition

For original signed source responses `V_j(x)`:

```text
V_abs_max(x_i) = max_j abs(V_j(x_i))
```

Only one emphasized envelope branch is displayed.

There is no displayed `min(abs(V))` curve because it is not part of the intended structural design demand.

### 4.2 Source curves remain signed

Although magnitude comparison uses `abs(...)`, the faint context curves must preserve the original signed source responses.

For example:

```text
V_constr(x)
V_uso(x)
```

are drawn with their physical signs, while the emphasized design curve is:

```text
|V|_max(x)
```

This keeps both structural interpretation and design magnitude visible at once.

### 4.3 Governing metadata

For each sampled x-position EngCalc must retain:

```text
governing source index
original signed governing value
absolute governing magnitude
source label
```

This metadata must remain available even though the displayed envelope branch is nonnegative.

## 5. Magnitude-envelope detection rule

Magnitude-envelope mode is selected only when every source expression is syntactically an outermost `abs(...)` call before symbolic expansion.

Valid magnitude envelope:

```text
envelope(abs(V1(x)), abs(V2(x)), x, 0, L)
```

Invalid mixed mode:

```text
envelope(abs(V1(x)), V2(x), x, 0, L)
```

The mixed form must fail with a concise error such as:

```text
envelope cannot mix absolute and signed response series
```

This avoids ambiguous semantics.

For a sweep request, the one plotted expression must be outermost `abs(...)` to select magnitude mode.

## 6. Why outermost syntax is preserved separately from symbolic value

For magnitude-envelope rendering, EngCalc needs two related representations:

1. the original signed response expression used for source-curve sampling;
2. the absolute-valued response used for governing-magnitude comparison.

Therefore the shared response resolver must preserve enough source-expression metadata to know whether the user wrote outermost `abs(...)` and, when so, what signed inner expression it contains.

No string parsing of rendered SymPy expressions should be used for this decision.

## 7. Sampling policy

Both signed and magnitude envelopes use the same 201 uniformly spaced x samples already established by `plot(...)` and `envelope(...)`.

No adaptive sampling, symbolic crossover solving, or analytical extremum solver is introduced in 0.6.0.

All source responses are normalized to compatible Pint units before comparison.

Magnitude comparison is performed on normalized numerical magnitudes at each sample.

## 8. Structural classification

Magnitude wrapping does not erase structural response classification.

For example:

```text
abs(V(x))
```

must still be recognized as a shear/force response for display labeling and dimensional compatibility.

Likewise, a hypothetical:

```text
envelope(abs(M1(x)), abs(M2(x)), x, 0, L)
```

is mathematically valid as a magnitude envelope, but it is not the default recommended moment-design workflow because signed moment information is normally required for reinforcement-face interpretation.

The standard signed `envelope(M1, M2, ...)` remains the normal moment workflow.

## 9. Magnitude-envelope visual design

The magnitude envelope renderer shows:

- original signed source curves as thin, faint background lines;
- one emphasized nonnegative `|...|_max` branch;
- a light fill between zero and the magnitude envelope;
- the zero reference line;
- one legend entry for the magnitude envelope;
- a compact characteristic-value panel inside the axes;
- no per-source markers or source callout boxes.

The plot title should identify magnitude semantics, for example:

```text
|V(x)| envelope
```

or an equivalent compact form derived from the common response family.

The characteristic panel reports at minimum:

```text
|max| = <value>    x = <position>
governing signed value = <signed value>
```

The exact wording may be shortened if necessary for compact placement.

## 10. Existing envelope visual design

The signed algebraic envelope keeps its current visual semantics:

- faint signed source curves;
- emphasized algebraic maximum and minimum branches;
- light fill between max/min;
- zero line;
- moment-axis inversion when applicable;
- characteristic values.

The main 0.6.0 change for signed envelopes is panel placement inside the axes rather than outside the figure.

## 11. In-axes characteristic panel

The current 0.5.0 implementation uses `figure.text(...)` and reserves approximately the rightmost 27% of the figure for text. EngCalc 0.6.0 removes this reserved external area.

The panel must be placed inside the plotting axes using axes-relative coordinates.

Candidate corners:

```text
upper right
upper left
lower right
lower left
```

### 11.1 Placement objective

Choose the candidate corner with the lowest estimated visual interference with plotted data while also avoiding the legend location when possible.

The placement algorithm must be deterministic, inexpensive, and independent of browser pixel measurements.

### 11.2 Data-occupancy heuristic

For each candidate corner:

1. define a normalized corner region in axes coordinates;
2. estimate how many plotted sample points fall inside or near that region after mapping x/y values to normalized data coordinates;
3. assign a penalty for legend conflict;
4. choose the candidate with the smallest total penalty;
5. use a deterministic corner priority to break ties.

The exact scoring constants are implementation details, but tests must prove the panel changes corners when data occupancy changes.

### 11.3 Panel styling

The panel should remain visually secondary:

- small font;
- white/axes-colored background with high but not fully opaque alpha;
- restrained border;
- modest padding;
- no arrow;
- no figure-level reserved margin.

## 12. Scope of panel correction

The in-axes placement helper should be shared by:

- multi-series `plot(...)` characteristic panels;
- signed `envelope(...)` characteristic panels;
- magnitude `envelope(abs(...), ...)` characteristic panels.

Single-series `plot(...)` keeps its existing local extrema callouts and does not need a characteristic panel conversion in 0.6.0.

## 13. Shared result model

`PlotResult` remains the common rendering transport.

The result model may be extended minimally with explicit envelope mode and governing signed values, conceptually:

```python
envelope_mode = "signed" | "magnitude" | None
governing_signed = tuple[Quantity, ...] | None
```

Alternative field names are acceptable if they preserve these invariants:

- normal plots remain backward compatible;
- signed envelopes still expose max/min and governing max/min indices;
- magnitude envelopes expose one displayed branch;
- signed source series remain available for rendering;
- governing signed values remain recoverable without recomputation from rendered data.

## 14. Shared response-resolution architecture

No parallel magnitude-envelope engine is introduced.

The existing shared `plot/envelope` response resolver should be generalized so it can provide, for each source expression:

```text
display label
signed symbolic expression
comparison symbolic expression
is absolute-wrapped
structural family metadata
sampled signed source values
```

Normal plot and signed envelope use signed/comparison expressions identically.

Magnitude envelope samples signed source curves for context and absolute-valued comparison curves for governing selection.

## 15. Units and dimensional compatibility

`abs(...)` preserves the units of its operand.

Examples:

```text
abs(-3*tonf) -> 3 tonf
abs(-2*tonf/m) -> 2 tonf/m
```

Magnitude-envelope source series must remain dimensionally compatible under the same rules as signed envelopes.

Invalid combinations such as force plus moment remain rejected.

## 16. Sweep semantics

Magnitude envelopes support the existing one-parameter sweep grammar:

```text
envelope(abs(V(x)), x, 0, L, q=[...])
```

The sweep remains local and non-mutating.

The plotting variable cannot be used as the sweep parameter.

Only one sweep parameter is supported.

The original signed function must be evaluated for each sweep value so the faint source curves and governing signed metadata remain available.

## 17. Error behavior

New or clarified errors must cover:

- unsupported `abs` arity;
- keyword arguments to `abs`;
- mixed absolute/signed envelope sources;
- magnitude envelope with fewer than two expanded source series;
- incompatible units;
- invalid sweep usage;
- existing envelope and plot validation errors unchanged.

Error wording should remain concise and consistent with current EngCalc style.

## 18. Backward compatibility

EngCalc 0.6.0 must preserve all 0.5.0 behavior except the intentionally improved panel placement.

Specifically:

- single-series plotting remains unchanged;
- multi-series source curves and extrema markers remain unchanged except panel location/layout;
- signed envelope calculations remain unchanged;
- moment-positive-down convention remains unchanged;
- existing 201-point sampling remains unchanged;
- all current parser restrictions remain in force;
- no existing valid `plot(...)` or `envelope(...)` syntax changes meaning.

## 19. TDD acceptance coverage

Implementation must follow RED -> GREEN cycles.

### Parser / symbolic operation

1. accept `abs(x)`;
2. accept nested `abs(V(x))` in `plot`;
3. accept `abs(...)` in `numeric(...)`;
4. reject zero-argument `abs`;
5. reject multi-argument `abs`;
6. reject keyword arguments to `abs`;
7. preserve existing restricted-call security.

### Engine — general abs

8. evaluate symbolic `abs` to SymPy `Abs`;
9. numeric absolute value preserves Pint units;
10. normal `plot(abs(V(x)))` samples absolute values correctly.

### Engine — magnitude envelope

11. detect all-outermost-abs multi-expression envelope;
12. detect outermost-abs sweep envelope;
13. reject mixed abs/signed sources;
14. keep signed source series for rendering;
15. compute `max(abs(source))` pointwise;
16. return one displayed magnitude branch;
17. retain governing source indices;
18. retain governing signed quantities;
19. retain ordered source labels;
20. preserve sweep non-mutation;
21. reject incompatible units;
22. preserve signed-envelope behavior unchanged.

### Renderer

23. signed source curves remain on both sides of zero when applicable;
24. magnitude envelope branch is nonnegative;
25. magnitude fill is between zero and the envelope branch;
26. magnitude legend contains only the emphasized magnitude branch;
27. signed envelope still renders two emphasized branches;
28. characteristic panels for multi-plot and both envelope modes are axes-owned text/annotation objects, not figure-level `figure.text` panels;
29. no right-hand figure width is reserved for the panel;
30. placement heuristic can choose at least two different corners based on data occupancy;
31. placement avoids the legend corner when an alternative has lower conflict;
32. panel remains inside axes bounds;
33. existing single-series rendering remains unchanged.

### Integration / release

34. `%%eng` end-to-end magnitude envelope works;
35. `%%eng` source order remains correct;
36. existing full suite remains green;
37. package/runtime version becomes 0.6.0;
38. build real 0.6.0 wheel;
39. install wheel in clean environment;
40. installed-wheel smoke test covers `abs`, signed envelope, magnitude envelope, and in-axes panel;
41. full suite passes against installed wheel from outside the source tree.

## 20. Canonical acceptance examples

### A. Signed moment envelope

```text
%%eng

M_constr(x) = ...
M_uso(x) = ...

envelope(M_constr(x), M_uso(x), x, 0, L)
```

Expected:

- two emphasized signed envelope branches;
- faint signed source curves;
- positive moment downward;
- characteristic panel inside the axes.

### B. Magnitude shear envelope

```text
%%eng

V_constr(x) = ...
V_uso(x) = ...

envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)
```

Expected:

- original signed shear curves shown faintly;
- one emphasized nonnegative `|V|_max` curve;
- fill from zero to `|V|_max`;
- governing signed value retained;
- characteristic panel inside the axes.

### C. Magnitude sweep

```text
%%eng

V(x) = ...

envelope(abs(V(x)), x, 0, L, q=[2*tonf/m, 3*tonf/m, 4*tonf/m])
```

Expected:

- one signed source curve per sweep case;
- one nonnegative magnitude envelope;
- no mutation of stored `q`;
- panel placed inside the axes.

## 21. Deferred scope

Not included in 0.6.0:

- `abs_envelope(...)` or `envelope_abs(...)` aliases;
- arbitrary envelope modes via keyword arguments;
- named load-case dictionaries;
- multi-parameter sweeps;
- analytical crossover solving;
- adaptive sampling;
- exact browser-pixel collision detection;
- automatic structural-design decisions based solely on response name;
- automatic conversion of every shear envelope to magnitude mode without explicit `abs(...)`.

## 22. Acceptance criterion

EngCalc 0.6.0 is successful if a user can express a structural magnitude envelope by composing familiar mathematical syntax:

```text
envelope(abs(...), ...)
```

without learning a second envelope command, while still seeing the original signed response curves and while all characteristic panels remain compactly inside the plotting area without sacrificing figure width.
