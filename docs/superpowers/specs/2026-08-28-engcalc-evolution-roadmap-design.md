# EngCalc Evolution Roadmap Design

## Status and baseline

This roadmap is now anchored to the canonical **EngCalc 0.7.2** product baseline on `main`. EngCalc 0.7.2 includes the restricted symbolic DSL, separate Pint-backed numeric context, unit-aware `numeric(...)`/`result(...)`, scalar engineering math, multi-argument functions, generalized partial evaluation, plotting/envelopes, and native engineering tables.

Release PR #29 merged EngCalc 0.7.2 into `main` on 2026-08-29. The authoritative 0.7.2 distribution gate is Actions `33266879721` on validated SHA `08a58e77c1ebace0790ba1082290e3a291a47948`.

**Roadmap correction (2026-08-29):** the previously planned **0.7.3 derivation-traces** milestone is retired as redundant and will not be released. The existing `numeric(...)` presentation already renders **formula → numerical substitution → final result**, while `result(...)` renders the compact **formula → final result** form. Fully evaluated and partial user-function calls also retain the known substitutions and evaluated symbolic structure. We therefore do not need a separate trace subsystem merely to reproduce behavior already present. More granular invented arithmetic/algebra steps remain intentionally out of scope unless a future concrete engineering workflow demonstrates a need for them.

The next planned product milestone is therefore **0.8.0 — piecewise expressions**.

## Product principles

1. EngCalc remains a safe restricted engineering DSL, not arbitrary Python execution.
2. Symbolic formulas and numerical values with units remain separate concepts, but normal engineering expressions should cross that boundary ergonomically.
3. Exact symbolic reasoning is preferred for engineering results; numerical sampling is primarily a rendering/fallback mechanism.
4. Every new public capability must work coherently through parser → engine → numeric context → renderer/magic → tests/docs.
5. Existing released syntax remains backward compatible unless a later 1.0 stabilization explicitly deprecates behavior.
6. Public APIs stay composable. Avoid one-off aliases when normal mathematical composition is sufficient.
7. Every release is TDD-first and must pass source tests, a built-wheel smoke test from outside the source tree, and the full suite against the installed wheel.
8. No new runtime dependency is added unless the capability cannot reasonably be implemented with Python, SymPy, Pint and Matplotlib already in the project.
9. Engineering-facing errors must say what failed and how to correct the input when a safe correction is known.
10. Documentation examples must be executable examples, not pseudocode presented as supported syntax.
11. Do not create a new public feature when an existing primitive already expresses the same engineering workflow clearly.

## Already complete — do not reimplement

- Unit-aware numeric assignments with `:=`.
- Unit conversion with `numeric(expression, target_unit)`.
- Global precision and zero-tolerance configuration.
- Detailed numerical presentation through `numeric(...)`: formula → substitution → result.
- Compact numerical presentation through `result(...)`: formula → result.
- Generalized partial numerical evaluation with known substitutions preserved.
- Scalar engineering mathematics (`sqrt`, trig/inverse trig, `exp`, `log`, `pi`).
- Multi-argument user functions.
- `plot(...)` with single series, multi-series and one-parameter sweeps.
- `envelope(...)` signed max/min reduction.
- `abs(...)` and magnitude-demand envelopes.
- 201-point unit-aware rendering grids.
- Structural moment convention: positive moment plotted downward.
- Native engineering tables with uniform-count and explicit-point forms.

## Release roadmap

**Versioning reconciliation (2026-08-29):** the release that actually shipped as 0.6.1 became the visual/presentation release. Numeric ergonomics therefore shipped as 0.6.2; 0.7.0, 0.7.1 and 0.7.2 retained their planned numbers. The formerly planned 0.7.3 is now retired rather than repurposed, so the next release number in this roadmap is 0.8.0.

### 0.6.2 — symbolic/numeric ergonomics and diagnostic quality — COMPLETE

Goal: remove avoidable friction exposed by engineering exercises without changing the conceptual architecture.

Delivered behavior includes direct unit-bearing user-function arguments, dimensional-zero preservation and improved numerical diagnostics.

### 0.7.0 — scalar engineering mathematics — COMPLETE

Delivered public functions:

- `sqrt(expression)`
- `sin(expression)`, `cos(expression)`, `tan(expression)`
- `asin(expression)`, `acos(expression)`, `atan(expression)`
- `exp(expression)`
- `log(expression)`
- constant `pi`

### 0.7.1 — multi-argument functions and generalized partial evaluation — COMPLETE

Delivered syntax includes:

```text
M(x, q, L) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2
sigma(M, y, I) = M*y/I
```

User functions support one or more positional parameters, exact arity, nested calls, fully numerical Pint evaluation and generalized partial evaluation while preserving unresolved caller symbols.

### 0.7.2 — engineering tables / evaluation by points — COMPLETE

Delivered forms include:

```text
table(M(x), x, 0, L, 21)
table(M_1(x), M_2(x), x, [0, 1, 2], m)
table(M(x), x, [0*m, 50*cm, 1*m])
```

Tables support uniform and explicit point definitions, compatible multiple response columns, unit normalization, native HTML rendering and non-mutating local evaluation of the table variable.

### Retired milestone — 0.7.3 derivation traces

**Status: RETIRED / NO RELEASE PLANNED.**

The milestone originally proposed a new trace system for engineering calculation memories. Colab verification against EngCalc 0.7.2 confirmed that the useful engineering-facing trace already exists:

```text
numeric(expression)
```

renders the formula, numerical substitution and final result, while:

```text
result(expression)
```

renders the compact formula and final result. Multi-argument and partial evaluations likewise show known substitutions and the remaining evaluated symbolic expression.

A separate trace subsystem would therefore duplicate existing behavior. EngCalc will not generate artificial arithmetic micro-steps such as `5^2 → 25 → 250/8 → 31.25` merely to make a derivation look longer. If a future operation such as `solve`, `integral` or `diff` reveals a specific missing engineering-memory representation, that requirement should be designed from that concrete workflow rather than from a generic trace abstraction.

### 0.8.0 — piecewise expressions — NEXT

Goal: represent loads, properties and response functions that change by interval.

Required syntax:

```text
q(x) = piecewise(q1, x < a, q2, x <= L, 0)
```

Required behavior:

- restricted comparison operators `<`, `<=`, `>`, `>=` are accepted only where a condition is expected;
- `piecewise(value, condition, ..., default)` requires value/condition pairs plus one default expression;
- symbolic manipulation, `numeric`, `table`, `plot`, `integral` and `diff` work when SymPy can evaluate the piecewise expression;
- branch result units must be compatible at numeric evaluation time.

Out of scope: boolean `and/or/not`, arbitrary Python conditionals.

### 0.8.1 — exact-first extrema, roots and intersections

Goal: separate engineering characteristic-value calculation from plot sampling.

Public functions:

```text
extrema(M(x), x, 0, L)
roots(V(x), x, 0, L)
intersections(M_1(x), M_2(x), x, 0, L)
```

Required behavior:

- symbolic solve first;
- keep only real solutions inside the requested domain;
- include interval endpoints for extrema;
- classify maxima/minima by exact symbolic evaluation when possible;
- if exact solve is unavailable, use an explicitly marked numerical fallback without adding SciPy;
- return structured characteristic results usable by renderers and later envelope logic.

### 0.8.2 — exact envelopes and governing intervals

Goal: make envelope engineering logic exact-first while retaining sampled rendering.

Required behavior:

- signed envelopes partition the domain at exact/fallback intersections of source responses;
- magnitude envelopes partition at equality of magnitudes;
- each interval stores the governing source case;
- exact characteristic values are used for summaries when available;
- the existing 201-point grid remains a renderer sampling policy, not the authoritative source of crossover locations;
- existing public envelope syntax remains valid.

### 0.8.3 — named response cases and combinations

Goal: make multi-case structural work readable and preserve governing-case identity.

Required syntax:

```text
case("Construction", M_UC(x))
case("1.2D + 1.6L", M_UU(x))
envelope(case("Construction", M_UC(x)), case("1.2D + 1.6L", M_UU(x)), x, 0, L)
```

Required behavior:

- string literals are allowed only in explicitly whitelisted metadata positions such as `case(...)`;
- case labels flow into legends, tables, envelope governing intervals and summaries;
- raw expressions remain supported with generated labels;
- case objects do not mutate or replace stored symbolic formulas.

### 0.9.0 — vectors, matrices and linear systems

Goal: add a safe first-class linear-algebra layer for engineering calculations.

Required syntax:

```text
A = matrix([a11, a12], [a21, a22])
b = vector(b1, b2)
x = linsolve(A, b)
```

Public operations:

- `matrix(...)`, `vector(...)`, `transpose(...)`, `det(...)`, `inv(...)`, `linsolve(...)`;
- ordinary `+`, `-`, `*`, scalar powers where mathematically valid.

Required behavior:

- nested lists are accepted only in whitelisted matrix/table constructs;
- dimensions are validated before algebra;
- symbolic matrices use SymPy Matrix types;
- numeric evaluation supports dimensionally homogeneous matrix/vector entries and rejects misleading mixed-dimensional operations explicitly;
- matrix rendering uses readable bracketed LaTeX, not Python list syntax.

Out of scope: sparse matrices, eigenvalue workflows, heterogeneous-unit FEM assembly.

### 0.10.0 — engineering verification system

Goal: introduce the differentiating equation → data → substitution → result → unit → criterion → verification workflow.

Required syntax:

```text
check(Mu <= phiMn)
check("Flexión positiva", Mu <= phiMn)
check("Flecha", delta <= L/360)
```

Required behavior:

- restricted comparison conditions `<=`, `<`, `>=`, `>`;
- compatible-unit enforcement before comparison;
- structured result with label, left/right quantities, operator, pass/fail and optional utilization ratio;
- for normal nonnegative `lhs <= rhs` demand/capacity checks, utilization is `lhs/rhs`;
- for `lhs >= rhs` minimum requirements, utilization is `rhs/lhs` when meaningful;
- ratios are omitted rather than fabricated when signs/zero/semantics make a ratio misleading;
- checks render clearly in `%%eng` and preserve calculation source order.

### 0.10.1 — verification collections and summaries

Goal: summarize many checks without losing the detailed individual calculation outputs.

Required syntax:

```text
summary()
```

Required behavior:

- `check(...)` results are collected in execution order for the current EngCalc state;
- `summary()` renders a table with verification, demand/left side, capacity/right side, utilization when available and status;
- `%eng_reset` clears accumulated verification state;
- headings remain independent presentation elements; explicit check labels are authoritative.

### 1.0.0 — language/API stabilization and release engineering

Goal: freeze a coherent first stable public language after all roadmap capabilities have proven themselves.

Required work:

- define public grammar and compatibility/deprecation policy;
- split oversized engine/parser modules only where repeated roadmap work demonstrates a stable responsibility boundary;
- complete user-facing reference documentation for every public function and magic command;
- add acceptance examples spanning structural, geotechnical/hydraulic or general engineering scalar workflows, tables, piecewise expressions, matrices and checks;
- run CI across supported Python versions;
- build and test wheel/sdist from clean environments;
- publish a GitHub Release and prepare PyPI Trusted Publishing if repository/account configuration permits it;
- no feature is added solely to reach 1.0.

## Cross-release acceptance rules

Every release must:

1. add RED tests before production code;
2. keep the full previous suite green;
3. include parser/engine/numeric/renderer tests when the feature crosses those layers;
4. include at least one `%%eng` acceptance test for new user-visible behavior;
5. document executable syntax in README/reference docs;
6. bump both `pyproject.toml` and `src/engcalc_colab/__init__.py` only at the release-closing task;
7. build the actual wheel;
8. install that wheel in a clean virtual environment;
9. run a smoke test from outside the repository source tree;
10. run the full suite against the installed wheel;
11. remove temporary validation workflows before merge.

## Explicitly deferred beyond 1.0 roadmap

- arbitrary Python execution or arbitrary SymPy function access;
- multi-parameter Cartesian plot/envelope sweeps;
- full structural-analysis solver primitives (`beam(...)`, frame elements, stiffness assembly);
- ETABS/SAP2000 integration;
- adaptive plotting as a substitute for exact engineering analysis;
- symbolic proof generation or invented step-by-step algebra not backed by the engine;
- heterogeneous-unit finite-element matrices;
- arbitrary styling kwargs for Matplotlib.
