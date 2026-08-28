# EngCalc Evolution Roadmap Design

## Status and baseline

This roadmap starts from the validated EngCalc 0.6.0 product tree on `feature/v0.6.0-abs-envelope-panel`. EngCalc 0.6.0 already provides a restricted symbolic DSL, a separate Pint-backed numeric context, unit conversion through `numeric(expr, unit)`, precision/tolerance configuration, headings, native single/multi-series plotting, parameter sweeps, signed envelopes, magnitude envelopes through `envelope(abs(...))`, and in-axes characteristic panels.

The open 0.6.0 release PR must be merged to `main` before any roadmap implementation branch begins.

## Product principles

1. EngCalc remains a safe restricted engineering DSL, not arbitrary Python execution.
2. Symbolic formulas and numerical values with units remain separate concepts, but normal engineering expressions should cross that boundary ergonomically.
3. Exact symbolic reasoning is preferred for engineering results; numerical sampling is primarily a rendering/fallback mechanism.
4. Every new public capability must work coherently through parser → engine → numeric context → renderer/magic → tests/docs.
5. Existing 0.6.0 syntax remains backward compatible unless a later 1.0 stabilization explicitly deprecates behavior.
6. Public APIs stay composable. Avoid one-off aliases such as `abs_envelope(...)` when normal mathematical composition is sufficient.
7. Every release is TDD-first and must pass source tests, a built-wheel smoke test from outside the source tree, and the full suite against the installed wheel.
8. No new runtime dependency is added unless the capability cannot reasonably be implemented with Python, SymPy, Pint and Matplotlib already in the project.
9. Engineering-facing errors must say what failed and how to correct the input when a safe correction is known.
10. Documentation examples must be executable examples, not pseudocode presented as supported syntax.

## Already complete — do not reimplement

- Unit-aware numeric assignments with `:=`.
- Unit conversion with `numeric(expression, target_unit)`.
- Global precision and zero-tolerance configuration.
- Partial numeric rendering for the currently supported polynomial case.
- `plot(...)` with single series, multi-series and one-parameter sweeps.
- `envelope(...)` signed max/min reduction.
- `abs(...)` and magnitude-demand envelopes.
- 201-point unit-aware rendering grids.
- Structural moment convention: positive moment plotted downward.

## Release roadmap

### 0.6.1 — symbolic/numeric ergonomics and diagnostic quality

Goal: remove avoidable friction exposed by the professor-Excel exercise without changing the conceptual architecture.

Required behavior:

- `numeric(M(2.5*m))`, `numeric(V(L/2))`, and `numeric(R(4*tonf/m))` work directly when the function argument is a complete numeric/unit expression.
- Existing `numeric(M(x))` partial evaluation remains valid when `x` is intentionally unresolved.
- `solve(expression, unknown)` remains the recommended shorthand for `expression = 0`; `solve(eq(left, right), unknown)` remains supported.
- Error messages distinguish unknown numeric names, incompatible units, unresolved symbols and unsupported symbolic/numeric crossings.
- Error text includes a corrective example when EngCalc can determine one safely.

Out of scope: new scalar math functions, multiple function parameters, tables.

### 0.7.0 — scalar engineering mathematics

Goal: make EngCalc a sufficiently complete scalar engineering calculator.

Public functions:

- `sqrt(expression)`
- `sin(expression)`, `cos(expression)`, `tan(expression)`
- `asin(expression)`, `acos(expression)`, `atan(expression)`
- `exp(expression)`
- `log(expression)` (natural logarithm)
- constant `pi`

Numeric rules:

- `sqrt` propagates units through a power of 1/2.
- `sin/cos/tan` accept dimensionless values or angle quantities; degree quantities are converted to radians internally.
- inverse trigonometric functions return radians and can be converted with `numeric(..., deg)`.
- `exp` and `log` require dimensionless arguments.
- all functions work symbolically, numerically, in user functions and in plotting.

Out of scope: hyperbolic functions, arbitrary special functions.

### 0.7.1 — multi-argument functions and generalized partial evaluation

Goal: remove the one-argument user-function limitation and make partial substitution work beyond polynomials.

Required syntax:

```text
M(x, q, L) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2
sigma(M, y, I) = M*y/I
```

Required behavior:

- User functions support one or more named parameters.
- Arity is checked exactly at call time.
- Existing one-argument definitions remain unchanged.
- `numeric(M(x, qD, L))` evaluates every known argument/value while preserving only unresolved symbolic arguments.
- Partial evaluation supports expressions involving the scalar-math functions from 0.7.0, not only polynomial terms.
- Rendering shows original formula, known substitutions and the remaining symbolic expression without fabricating units for unresolved symbols.

Out of scope: default arguments, keyword arguments, variadic user functions.

### 0.7.2 — engineering tables / evaluation by points

Goal: make pointwise engineering evaluation a first-class output rather than requiring Python/pandas validation code.

Required forms:

```text
table(M(x), x, [0*m, 1*m, 2*m, 3*m, 4*m])
table(M_1(x), M_2(x), x, [0*m, 1*m, 2*m])
table(M(x), x, 0, L, 21)
```

Required behavior:

- explicit-point and uniform-count forms;
- one or more dimensionally compatible response expressions;
- point units normalized consistently;
- output rendered as an HTML table inside `%%eng` in source order;
- no mutation of stored values for the table variable;
- downloadable/export APIs are deferred.

### 0.7.3 — derivation traces for calculation memories

Goal: improve the equation → operation → result narrative without attempting to reproduce SymPy's internal algorithms.

Public configuration:

```text
%eng_config steps=off
%eng_config steps=compact
%eng_config steps=full
```

Required behavior:

- `solve`, `integral`, `diff`, `simplify`, `expand`, `factor` can attach structured derivation steps.
- compact mode shows operation input and final transformed result.
- full mode additionally shows normalized equation/derivative/integral forms and substitutions that EngCalc itself performs.
- no fake algebraic intermediate steps are generated when SymPy does not expose them safely.

### 0.8.0 — piecewise expressions

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
- exact characteristic values are used for panel summaries when available;
- the existing 201-point grid remains a renderer sampling policy, not the authoritative source of crossover locations;
- 0.5/0.6 public envelope syntax remains valid.

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
