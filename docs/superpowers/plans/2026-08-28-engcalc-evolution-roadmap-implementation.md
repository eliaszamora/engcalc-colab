# EngCalc Evolution Roadmap 0.6.0 → 1.0.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evolve EngCalc from the validated 0.6.0 symbolic/unit-aware plotting DSL into a stable 1.0 engineering calculation language with complete scalar math, ergonomic symbolic/numeric evaluation, tables, piecewise expressions, exact-first engineering analysis, matrices, named cases and a first-class verification workflow.

**Architecture:** Preserve the restricted AST/parser and the separation between symbolic SymPy state and Pint numeric state, but add explicit bridges and structured result types rather than arbitrary evaluation. Keep `engine.py` as the coordinator while moving new domain-heavy logic into focused modules (`characteristics.py`, `tabular.py`, `linear_algebra.py`, `verification.py`) so the current 36 kB engine does not become the implementation site for every future capability. Every release is independently mergeable and must pass source, installed-wheel smoke and installed-wheel full-suite gates.

**Tech Stack:** Python 3.11+, SymPy, Pint, Matplotlib, IPython/Jupyter magic, pytest, stdlib only unless a later release proves a new runtime dependency necessary.

**Spec:** `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`

## Global Constraints

- Start implementation only after EngCalc 0.6.0 PR #24 is merged to `main`.
- Preserve all 0.6.0 public syntax and the positive-moment-down plotting convention.
- Keep symbolic values and Pint quantities conceptually separate; improve the bridge rather than merging the namespaces.
- No arbitrary Python execution and no arbitrary SymPy function access.
- No new runtime dependency without an explicit design amendment.
- Every public feature must cross parser → engine → numeric context → renderer/magic when applicable.
- TDD is mandatory: failing test first, minimal implementation second, full regression third.
- Every release closes with source suite, real wheel build, clean-venv smoke from outside the repo, full suite against the wheel, repeated source suite, README/reference update and temporary-workflow cleanup.
- Version bumps happen only in the release-closing task for that release.

## File Structure Map

Existing core files:

- `src/engcalc_colab/parser.py` — restricted syntax, AST validation and statement parsing.
- `src/engcalc_colab/engine.py` — symbolic evaluation, user functions and high-level output coordination.
- `src/engcalc_colab/numeric.py` — Pint-backed numeric assignments, unit conversion and symbolic-to-numeric evaluation.
- `src/engcalc_colab/models.py` — public/internal immutable result models.
- `src/engcalc_colab/renderer.py` — MathJax/LaTeX rendering for calculation results.
- `src/engcalc_colab/plotting.py` — Matplotlib rendering for plot/envelope results.
- `src/engcalc_colab/magic.py` — `%%eng`, `%eng_reset`, `%eng_config` display orchestration.
- `src/engcalc_colab/errors.py` — user-facing EngCalc exceptions.

New focused modules introduced by this roadmap:

- `src/engcalc_colab/tabular.py` — table sampling and HTML rendering helpers.
- `src/engcalc_colab/characteristics.py` — exact-first roots/extrema/intersection solving and domain filtering.
- `src/engcalc_colab/linear_algebra.py` — matrix/vector construction, validation and unit-aware evaluation helpers.
- `src/engcalc_colab/verification.py` — check evaluation, utilization policy and summary rendering.

Do not split `parser.py` or `engine.py` merely for aesthetics. Revisit their boundaries only in Task 13 after the roadmap has exposed stable responsibilities.

---

### Task 0: Close the 0.6.0 Baseline Before Roadmap Work

**Files:**
- No product code changes.
- Verify PR #24 and `main` after merge.

**Interfaces:**
- Consumes: validated 0.6.0 branch with `abs`, magnitude envelopes and in-axes panels.
- Produces: `main` as the only legal base for Task 1.

- [ ] **Step 1: Verify PR #24 is still mergeable and not stale**

Check that its base is `main`, head is `feature/v0.6.0-abs-envelope-panel`, and no product file changed after the release gate.

- [ ] **Step 2: Merge PR #24 using the repository's established release merge strategy**

Do not combine roadmap code with this merge.

- [ ] **Step 3: Compare merged `main` tree with the validated 0.6.0 product tree**

Expected: identical product tree; history SHA may differ after squash.

- [ ] **Step 4: Run/confirm 0.6.0 release gate on merged content if tree identity cannot be proven**

Expected baseline: 226 tests from the 0.6.0 branch remain green.

- [ ] **Step 5: Create the Task 1 feature branch from merged `main`**

Suggested branch: `feature/v0.6.1-numeric-ergonomics`.

---

### Task 1: EngCalc 0.6.1 — Symbolic/Numeric Ergonomics and Diagnostics

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/numeric.py`
- Modify: `src/engcalc_colab/errors.py`
- Modify: `src/engcalc_colab/renderer.py`
- Test: `tests/test_engine.py`
- Test: `tests/test_numeric_context.py`
- Create: `tests/test_numeric_function_arguments.py`
- Create: `tests/test_diagnostics.py`
- Modify: `tests/test_magic.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: existing `numeric(...)`, `UserFunction`, Pint unit aliases.
- Produces: direct numeric function-argument bridge capable of evaluating complete numeric AST arguments before function substitution.
- Produces: diagnostic helper `format_engcalc_hint(message_key: str, **context) -> str` or equivalent centralized error-copy mechanism; do not scatter contradictory hints.

- [ ] **Step 1: Write RED tests for direct unit-bearing function arguments**

```python
def test_numeric_function_accepts_direct_unit_expression(engine, parse_one):
    engine.evaluate(parse_one("M(x) = q*x*(L-x)/2"))
    engine.evaluate(parse_one("q := 10*kN/m"))
    engine.evaluate(parse_one("L := 6*m"))
    result = engine.evaluate(parse_one("numeric(M(2.5*m))"))
    assert result.quantity.to("kN*m").magnitude == pytest.approx(43.75)


def test_numeric_parameter_function_accepts_direct_load_quantity(engine, parse_one):
    engine.evaluate(parse_one("R(q) = 5*q*L/8"))
    engine.evaluate(parse_one("L := 4*m"))
    result = engine.evaluate(parse_one("numeric(R(4*tonf/m))"))
    assert result.quantity.to("tonf").magnitude == pytest.approx(10.0)
```

- [ ] **Step 2: Run only the new tests and confirm the current 0.6.0 failure mode**

Run: `pytest tests/test_numeric_function_arguments.py -v`
Expected: FAIL because unit-bearing call arguments currently cross the symbolic/numeric boundary incorrectly.

- [ ] **Step 3: Add a restricted numeric-argument resolver to `numeric(...)` function-call evaluation**

Implementation contract:

```python
def _resolve_numeric_function_argument(self, node: ast.AST):
    """Return either an unresolved symbolic argument or a Pint quantity.

    Names that are intentionally unresolved symbols stay symbolic.
    Complete numeric/unit expressions are evaluated by NumericContext.
    """
```

The resolver must not make all ordinary symbolic calls unit-aware; it is used only by `numeric(...)` evaluation.

- [ ] **Step 4: Add RED diagnostic tests**

```python
def test_unknown_numeric_name_error_names_the_missing_value(engine, parse_one):
    with pytest.raises(EngEvaluationError, match="unknown numeric name 'q_missing'"):
        engine.evaluate(parse_one("q := q_missing*kN/m"))


def test_incompatible_numeric_function_argument_reports_expected_dimension(engine, parse_one):
    # Use an existing function whose formula forces an incompatible operation.
    ...
```

Replace the second fixture with a concrete dimensionally invalid expression from the current test helpers; expected text must distinguish incompatible units from unresolved symbols.

- [ ] **Step 5: Centralize corrective diagnostics and keep exception types stable**

Do not change `EngEvaluationError`/`EngSyntaxError` inheritance. Improve messages only.

- [ ] **Step 6: Add acceptance test for the professor-exercise ergonomics**

A `%%eng` test must prove `numeric(M_UU(0*m))` or an equivalent direct-unit argument works without introducing `x0 := 0*m`.

- [ ] **Step 7: Run full source suite**

Run: `pytest -q`
Expected: all 0.6.0 tests plus new 0.6.1 tests PASS.

- [ ] **Step 8: Update README and close release 0.6.1**

Document `solve(expr, x)` as the primary zero-equality shorthand while retaining `eq(...)` documentation for explicit equalities. Bump both version declarations to 0.6.1 only now.

- [ ] **Step 9: Run wheel gate and commit**

Build wheel, install clean, smoke from `/tmp`, run full suite against wheel, repeat source suite.
Commit message: `release: EngCalc 0.6.1 numeric ergonomics`.

---

### Task 2: EngCalc 0.7.0 — Scalar Engineering Mathematics

**Files:**
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/numeric.py`
- Modify: `src/engcalc_colab/renderer.py`
- Create: `tests/test_scalar_math_parser.py`
- Create: `tests/test_scalar_math_engine.py`
- Create: `tests/test_scalar_math_numeric.py`
- Create: `tests/test_scalar_math_acceptance.py`
- Modify: `tests/test_acceptance_native_plot.py`
- Modify: `README.md`

**Interfaces:**
- Produces public symbolic functions: `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `exp`, `log`.
- Produces reserved symbolic constant: `pi`.
- Numeric angle policy: forward trig accepts dimensionless or angle quantities and evaluates in radians; inverse trig returns radians.

- [ ] **Step 1: Write parser RED tests for the complete scalar function whitelist and `pi`**

```python
@pytest.mark.parametrize("source", [
    "a = sqrt(x)", "b = sin(theta)", "c = cos(theta)", "d = tan(theta)",
    "e = asin(r)", "f = acos(r)", "g = atan(r)", "h = exp(z)", "i = log(z)",
    "p = pi",
])
def test_scalar_math_syntax_is_accepted(source):
    assert parse_cell(source)
```

Also assert these names become reserved assignment targets.

- [ ] **Step 2: Confirm RED**

Run: `pytest tests/test_scalar_math_parser.py -v`
Expected: unsupported/reserved-name failures for the new functions/constant.

- [ ] **Step 3: Add exact SymPy mappings in engine**

Use a fixed mapping, not dynamic `getattr(sympy, name)`:

```python
_SCALAR_SYMBOLIC_FUNCTIONS = {
    "sqrt": sp.sqrt,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "exp": sp.exp,
    "log": sp.log,
}
```

`pi` resolves to `sp.pi` and cannot be overwritten.

- [ ] **Step 4: Add numeric RED tests with units/domain rules**

```python
def test_sin_converts_degrees_to_radians(context):
    q = context.evaluate_expression(parse_numeric("sin(30*deg)"))
    assert q.dimensionless
    assert q.magnitude == pytest.approx(0.5)


def test_log_rejects_dimensional_quantity(context):
    with pytest.raises(EngEvaluationError, match="log requires a dimensionless argument"):
        context.evaluate_expression(parse_numeric("log(2*m)"))
```

Cover `sqrt(9*m^2) -> 3*m`, `atan(1)` in radians, `numeric(atan(1), deg) -> 45 deg`, and `exp` dimensional rejection.

- [ ] **Step 5: Implement explicit NumericContext adapters**

Do not rely on NumPy. Convert angle quantities to radians using Pint before `math.sin/cos/tan`; use stdlib `math` for numeric scalar evaluation.

- [ ] **Step 6: Add plot and partial-numeric acceptance tests**

Examples must include `f(x) = A*sin(pi*x/L)` with numeric `A`, `L`, and `plot(f(x), x, 0, L)`.

- [ ] **Step 7: Run regression, docs, version and wheel gate**

Close as 0.7.0 only after full installed-wheel validation.
Commit message: `release: EngCalc 0.7.0 scalar engineering math`.

---

### Task 3: EngCalc 0.7.1 — Multi-Argument User Functions and General Partial Evaluation

**Files:**
- Modify: `src/engcalc_colab/models.py`
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/numeric.py`
- Modify: `src/engcalc_colab/renderer.py`
- Create: `tests/test_multiarg_functions.py`
- Create: `tests/test_partial_numeric_general.py`
- Modify: `tests/test_engine.py`
- Modify: `tests/test_magic.py`
- Modify: `README.md`

**Interfaces:**
- Replace internal `UserFunction(parameter: str, expression)` with `UserFunction(parameters: tuple[str, ...], expression)`.
- Provide a compatibility property `parameter` only if exactly one parameter exists, so old internal tests can migrate without silently accepting wrong arity.
- General partial-evaluation output keeps `symbolic_expression`, known `substitutions`, unresolved names and a rendered partially evaluated expression.

- [ ] **Step 1: RED parser tests for multi-parameter definitions**

```python
def test_parses_multi_argument_function_definition():
    stmt = parse_cell("M(x, q, L) = q*x*(L-x)/2")[0]
    assert stmt.parameters == ("x", "q", "L")
```

Update `ParsedStatement` deliberately; do not encode multiple names back into the old single `parameter` string.

- [ ] **Step 2: RED engine tests for exact arity**

```python
def test_multiarg_function_substitutes_positionally(engine, parse_one):
    engine.evaluate(parse_one("f(x, a, b) = a*x + b"))
    result = engine.evaluate(parse_one("y = f(t, 2, 3)"))
    assert sp.simplify(result.value - (2*sp.Symbol("t") + 3)) == 0
```

Also test too few and too many arguments.

- [ ] **Step 3: Implement parser/model migration and engine substitution**

The function call implementation must build `dict(zip(parameters, args, strict=True))` or an equivalent exact-arity substitution map.

- [ ] **Step 4: RED generalized partial-evaluation tests**

```python
def test_partial_numeric_preserves_symbol_inside_trig_expression(engine, parse_one):
    engine.evaluate(parse_one("f(x, A, L) = A*sin(pi*x/L)"))
    engine.evaluate(parse_one("A := 10*mm"))
    engine.evaluate(parse_one("L := 4*m"))
    result = engine.evaluate(parse_one("numeric(f(x, A, L))"))
    assert result.unresolved_symbols == ("x",)
```

The rendered partial result must contain the evaluated `A`/`L` information and retain `x` symbolically.

- [ ] **Step 5: Replace polynomial-only rendering dependency with a general partial-substitution representation**

Keep `evaluate_partial_polynomial` temporarily if older tests still use it, but new rendering must not require a polynomial decomposition. Introduce a structured representation in `PartialNumericEvaluationResult`, for example:

```python
@dataclass(frozen=True)
class PartialNumericEvaluationResult:
    ...
    known_substitutions: tuple[tuple[str, object], ...]
    unresolved_symbols: tuple[str, ...]
```

Use one authoritative field name consistently across engine and renderer.

- [ ] **Step 6: Add backward-compatibility tests for all existing one-argument functions**

All existing plot/envelope/numeric tests must remain unchanged in behavior.

- [ ] **Step 7: Close 0.7.1 with docs and wheel gate**

Commit message: `release: EngCalc 0.7.1 multi-argument functions`.

---

### Task 4: EngCalc 0.7.2 — Tables and Evaluation by Points

**Files:**
- Create: `src/engcalc_colab/tabular.py`
- Modify: `src/engcalc_colab/models.py`
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/magic.py`
- Create: `tests/test_table_parser.py`
- Create: `tests/test_table_engine.py`
- Create: `tests/test_table_rendering.py`
- Create: `tests/test_table_acceptance.py`
- Modify: `README.md`

**Interfaces:**
- Add `TableSeries(display_label: str, values: tuple)` and `TableResult(variable, x_values, series)` models.
- Public forms:
  - `table(expr1, ..., variable, [point1, ...])`
  - `table(expr1, ..., variable, start, end, count)`
- Add `render_table(result: TableResult) -> IPython.display.HTML` in `tabular.py`.

- [ ] **Step 1: RED parser tests for list points restricted to `table(...)`**

Ensure ordinary expressions still reject arbitrary lists.

- [ ] **Step 2: RED engine tests for unit-aware point sampling and no mutation**

```python
def test_table_points_do_not_mutate_existing_x(engine, parse_one):
    engine.evaluate(parse_one("M(x) = q*x"))
    engine.evaluate(parse_one("q := 2*kN"))
    engine.evaluate(parse_one("x := 99*m"))
    result = engine.evaluate(parse_one("table(M(x), x, [0*m, 1*m, 2*m])"))
    assert engine.numeric_context.get("x").to("m").magnitude == 99
    assert len(result.x_values) == 3
```

- [ ] **Step 3: Implement table resolver by reusing response-series normalization rules**

Do not duplicate unit-compatibility logic from plot/envelope. Extract a private/shared response evaluator only if the current engine helper can be reused cleanly.

- [ ] **Step 4: RED HTML-render tests**

Assert headers contain variable and series labels with units; values honor `%eng_config precision`.

- [ ] **Step 5: Integrate `TableResult` into `%%eng` source ordering**

`Math → Table → Math` must flush pending equation groups exactly like figures do.

- [ ] **Step 6: Acceptance-test the professor Excel 21-station use case entirely inside EngCalc**

Use uniform form `table(..., x, 0, L, 21)` and verify 21 rows without Python-side sampling.

- [ ] **Step 7: Close 0.7.2 with wheel gate**

Commit message: `release: EngCalc 0.7.2 engineering tables`.

---

### Task 5: EngCalc 0.7.3 — Derivation Traces

**Files:**
- Modify: `src/engcalc_colab/models.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/renderer.py`
- Modify: `src/engcalc_colab/magic.py`
- Create: `tests/test_derivation_steps.py`
- Modify: `tests/test_magic.py`
- Modify: `README.md`

**Interfaces:**
- Add `DerivationStep(kind: str, expression: object, label: str | None = None)`.
- Add `derivation_steps: tuple[DerivationStep, ...]` to ordinary symbolic evaluation results.
- Extend `RenderSettings` with `steps: Literal["off", "compact", "full"]`, default `compact` only if backward visual tests approve; otherwise default `off` and document opt-in.

- [ ] **Step 1: RED config tests for `steps=off|compact|full` and invalid values**

- [ ] **Step 2: RED solve/integral/diff trace tests**

```python
def test_solve_trace_contains_normalized_equation_and_solution(engine, parse_one):
    result = engine.evaluate(parse_one("R = solve(R - q*L, R)"))
    assert [step.kind for step in result.derivation_steps] == ["equation", "solution"]
```

For integral/diff, test unevaluated operator + evaluated result; do not demand invented intermediate algebra.

- [ ] **Step 3: Implement traces at the exact operation sites in `_Evaluator.visit_Call`**

Never introspect private SymPy algorithms to manufacture steps.

- [ ] **Step 4: Render traces without duplicating the final assignment line**

Compact/full output must remain readable in calculation memories.

- [ ] **Step 5: Acceptance-test the propped-cantilever derivation**

Verify `R_B(q) = solve(delta_B, R_B_aux)` renders compatibility equation and solved reaction coherently.

- [ ] **Step 6: Close 0.7.3 with wheel gate**

Commit message: `release: EngCalc 0.7.3 derivation traces`.

---

### Task 6: EngCalc 0.8.0 — Piecewise Expressions

**Files:**
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/numeric.py`
- Modify: `src/engcalc_colab/renderer.py`
- Create: `tests/test_piecewise_parser.py`
- Create: `tests/test_piecewise_engine.py`
- Create: `tests/test_piecewise_numeric.py`
- Create: `tests/test_piecewise_plot_table.py`
- Modify: `README.md`

**Interfaces:**
- Public `piecewise(value1, condition1, ..., default)`.
- Restricted comparison AST support only in condition contexts.

- [ ] **Step 1: RED parser tests for allowed and forbidden comparison contexts**

```python
def test_piecewise_accepts_comparison_condition():
    assert parse_cell("q(x) = piecewise(q1, x < a, q2, x <= L, 0)")


def test_bare_comparison_is_still_rejected_outside_condition_context():
    with pytest.raises(EngSyntaxError):
        parse_cell("flag = x < a")
```

- [ ] **Step 2: Implement context-aware AST validation for `ast.Compare`**

Allow only one comparator and operators `< <= > >=`; reject chained comparisons and equality/inequality in 0.8.0.

- [ ] **Step 3: RED symbolic and numeric tests**

Build `sp.Piecewise` from value/condition pairs plus default. Numeric evaluation must evaluate only the selected branch and enforce compatible output units across sampled/tabled results.

- [ ] **Step 4: Test integration, differentiation, table and plot workflows**

Use a two-zone distributed load represented by symbols `q1`, `q2`, `a`, `L` with numeric assignments carrying units.

- [ ] **Step 5: Close 0.8.0 with wheel gate**

Commit message: `release: EngCalc 0.8.0 piecewise expressions`.

---

### Task 7: EngCalc 0.8.1 — Exact-First Characteristic Analysis

**Files:**
- Create: `src/engcalc_colab/characteristics.py`
- Modify: `src/engcalc_colab/models.py`
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/magic.py`
- Modify: `src/engcalc_colab/renderer.py`
- Create: `tests/test_characteristic_roots.py`
- Create: `tests/test_characteristic_extrema.py`
- Create: `tests/test_characteristic_intersections.py`
- Create: `tests/test_characteristic_acceptance.py`
- Modify: `README.md`

**Interfaces:**
- Add `CharacteristicPoint(x_value, y_value=None, kind=None, exact=True)`.
- Add `CharacteristicResult(kind, variable, points, method)`.
- Public calls: `roots(expr, x, start, end)`, `extrema(expr, x, start, end)`, `intersections(expr1, expr2, x, start, end)`.

- [ ] **Step 1: RED exact-root tests**

```python
def test_roots_filters_real_solutions_to_domain(engine, parse_one):
    result = engine.evaluate(parse_one("roots((x-1)*(x-3), x, 0, 2)"))
    assert [float(p.x_value) for p in result.points] == [1.0]
    assert result.method == "exact"
```

- [ ] **Step 2: Implement pure characteristic helpers in `characteristics.py`**

Functions must accept SymPy expressions/domain values and return deterministic structured points; they must not know about IPython display.

- [ ] **Step 3: RED extrema tests including endpoints**

For `M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2`, prove the exact interior maximum occurs at `5*L/8` and the interval endpoints are considered for global min/max.

- [ ] **Step 4: Implement numerical fallback without SciPy**

Use SymPy numeric root tools and/or deterministic bracketing based on an internal coarse scan. Mark fallback points `exact=False` and `method="numeric"`; never label them exact.

- [ ] **Step 5: Integrate rendering and `%%eng`**

Characteristic results should be concise calculation outputs, not plots.

- [ ] **Step 6: Close 0.8.1 with wheel gate**

Commit message: `release: EngCalc 0.8.1 exact-first characteristics`.

---

### Task 8: EngCalc 0.8.2 — Exact Envelopes and Governing Intervals

**Files:**
- Modify: `src/engcalc_colab/characteristics.py`
- Modify: `src/engcalc_colab/models.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/plotting.py`
- Modify: `tests/test_envelope_engine.py`
- Modify: `tests/test_magnitude_envelope_engine.py`
- Create: `tests/test_exact_envelope_intervals.py`
- Create: `tests/test_exact_magnitude_envelope_intervals.py`
- Modify: `README.md`

**Interfaces:**
- Add `GoverningInterval(start, end, source_index, exact_boundaries: bool)`.
- Extend `PlotResult` envelope metadata with exact/fallback crossover points and governing intervals while preserving current `governing_max/min` sampled arrays for renderer compatibility during migration.

- [ ] **Step 1: RED crossover tests with a non-grid intersection**

Choose two simple functions whose crossover is intentionally not one of the 201 existing sample x-values. Assert the stored crossover equals the symbolic solution, not the nearest sample.

- [ ] **Step 2: Build interval partitioning from `intersections(...)` output**

For each interval, evaluate source responses at a safe interior probe point to select the governing branch.

- [ ] **Step 3: Add magnitude-envelope crossover logic**

Solve equality of magnitudes using an exact-safe transformation such as `f**2 - g**2 = 0` plus validation, avoiding unsupported direct `Abs` solve assumptions.

- [ ] **Step 4: Make exact characteristic data authoritative for panel summaries**

Keep the 201-point grid for drawing curves/fill only.

- [ ] **Step 5: Regression-test all 0.5/0.6 envelope visuals and semantics**

Positive moment remains downward, source curves remain faint, magnitude envelope remains one nonnegative branch.

- [ ] **Step 6: Close 0.8.2 with wheel gate**

Commit message: `release: EngCalc 0.8.2 exact envelopes`.

---

### Task 9: EngCalc 0.8.3 — Named Response Cases

**Files:**
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/models.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/plotting.py`
- Modify: `src/engcalc_colab/tabular.py`
- Create: `tests/test_case_parser.py`
- Create: `tests/test_cases_plot_envelope.py`
- Create: `tests/test_cases_table.py`
- Modify: `README.md`

**Interfaces:**
- Add `ResponseCase(label: str, expression: object)` internal/public result wrapper.
- Public `case("label", expression)` accepted only inside response-consuming operations in the first release.

- [ ] **Step 1: RED parser tests for whitelisted strings**

Strings remain rejected generally but are accepted as the first argument of `case(...)`.

- [ ] **Step 2: RED plot/envelope label tests**

```python
def test_named_cases_flow_to_envelope_sources(engine, parse_one):
    result = engine.evaluate(parse_one(
        'envelope(case("Construction", M1(x)), case("Service", M2(x)), x, 0, L)'
    ))
    assert result.source_labels == ("Construction", "Service")
```

- [ ] **Step 3: Implement case unwrapping in the shared response resolver**

Do not store labels in symbolic namespace and do not change the underlying expressions.

- [ ] **Step 4: Render labels in legends, governing intervals and tables**

- [ ] **Step 5: Close 0.8.3 with wheel gate**

Commit message: `release: EngCalc 0.8.3 named response cases`.

---

### Task 10: EngCalc 0.9.0 — Vectors, Matrices and Linear Systems

**Files:**
- Create: `src/engcalc_colab/linear_algebra.py`
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/models.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/numeric.py`
- Modify: `src/engcalc_colab/renderer.py`
- Create: `tests/test_matrix_parser.py`
- Create: `tests/test_matrix_symbolic.py`
- Create: `tests/test_matrix_numeric.py`
- Create: `tests/test_linear_systems.py`
- Create: `tests/test_matrix_acceptance.py`
- Modify: `README.md`

**Interfaces:**
- Public: `matrix([row...], ...)`, `vector(...)`, `transpose(...)`, `det(...)`, `inv(...)`, `linsolve(A, b)`.
- Internal helpers in `linear_algebra.py` validate shape/dimensions and convert homogeneous Pint matrix entries safely.

- [ ] **Step 1: RED parser tests for nested lists only inside `matrix(...)`**

Ordinary list syntax must remain rejected elsewhere except already-whitelisted `table` point lists.

- [ ] **Step 2: RED symbolic matrix-operation tests**

Cover addition, scalar multiplication, matrix multiplication through `*`, transpose, determinant and inverse.

- [ ] **Step 3: Implement explicit SymPy Matrix construction and operation routing**

Do not allow Python object methods such as `A.inv()` in the DSL.

- [ ] **Step 4: RED `linsolve(A, b)` tests**

Reject non-square/incompatible systems clearly; return a vector result for unique systems only in 0.9.0.

- [ ] **Step 5: Add homogeneous-unit numeric matrix evaluation**

Allow matrices/vectors whose entries share compatible dimensions; normalize to one unit before array algebra. Reject heterogeneous engineering matrices explicitly with a message that 0.9.0 does not support heterogeneous-unit matrices.

- [ ] **Step 6: Render matrices as LaTeX brackets**

No Python list representation in user output.

- [ ] **Step 7: Acceptance-test a 2×2 stiffness-style linear system**

Use dimensionally homogeneous coefficients and forces; verify displacements with units.

- [ ] **Step 8: Close 0.9.0 with wheel gate**

Commit message: `release: EngCalc 0.9.0 linear algebra`.

---

### Task 11: EngCalc 0.10.0 — Engineering Verification System

**Files:**
- Create: `src/engcalc_colab/verification.py`
- Modify: `src/engcalc_colab/parser.py`
- Modify: `src/engcalc_colab/models.py`
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/magic.py`
- Create: `tests/test_check_parser.py`
- Create: `tests/test_check_engine.py`
- Create: `tests/test_check_units.py`
- Create: `tests/test_check_rendering.py`
- Create: `tests/test_check_acceptance.py`
- Modify: `README.md`

**Interfaces:**
- Add `CheckResult(label, left_quantity, operator, right_quantity, passed, utilization=None)`.
- Public `check(condition)` and `check("label", condition)`.
- Comparison support inside `check`: `<`, `<=`, `>`, `>=`; exactly one comparison.

- [ ] **Step 1: RED parser tests for comparison expressions only in check/piecewise-safe contexts**

- [ ] **Step 2: RED unit-compatibility tests**

```python
def test_check_compares_compatible_quantities(engine, parse_one):
    engine.evaluate(parse_one("Mu := 110*kN*m"))
    engine.evaluate(parse_one("phiMn := 125*kN*m"))
    result = engine.evaluate(parse_one('check("Flexion", Mu <= phiMn)'))
    assert result.passed is True
    assert result.utilization == pytest.approx(0.88)
```

Also reject `kN` versus `kN*m` before comparing magnitudes.

- [ ] **Step 3: Implement utilization policy in `verification.py`**

```python
def compute_utilization(left, operator, right):
    # <=/< : left/right when both are nonnegative and right != 0
    # >=/> : right/left when both are nonnegative and left != 0
    # otherwise None
```

Never use a ratio when signs or zeros make it misleading.

- [ ] **Step 4: Integrate CheckResult rendering into source order**

Render label, criterion, substituted quantities, utilization if available and clear PASS/FAIL status. Avoid arbitrary colors as semantic necessity; text/symbols must remain sufficient.

- [ ] **Step 5: Acceptance-test a structural mini-memory**

Use flexure, shear and deflection checks with units and one failing criterion.

- [ ] **Step 6: Close 0.10.0 with wheel gate**

Commit message: `release: EngCalc 0.10.0 engineering checks`.

---

### Task 12: EngCalc 0.10.1 — Verification Collections and Summary Tables

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/magic.py`
- Modify: `src/engcalc_colab/verification.py`
- Modify: `src/engcalc_colab/models.py`
- Create: `tests/test_check_summary.py`
- Modify: `tests/test_magic.py`
- Modify: `README.md`

**Interfaces:**
- Engine keeps `verification_results: list[CheckResult]` in execution order.
- Public standalone `summary()` returns `VerificationSummaryResult`.
- `%eng_reset` clears the collection.

- [ ] **Step 1: RED collection-order and reset tests**

- [ ] **Step 2: Implement collection only after a check evaluates successfully**

Failed-to-evaluate checks must not appear in summary state.

- [ ] **Step 3: RED summary rendering test**

Columns: Verification, Criterion/Demand, Limit/Capacity, Utilization, Status. Omit utilization cell content when model value is `None`.

- [ ] **Step 4: Integrate `summary()` as standalone output**

Reject assignment such as `x = summary()`.

- [ ] **Step 5: Acceptance-test a multi-check calculation memory**

- [ ] **Step 6: Close 0.10.1 with wheel gate**

Commit message: `release: EngCalc 0.10.1 verification summaries`.

---

### Task 13: EngCalc 1.0.0 — Stabilization, Documentation and Release Engineering

**Files:**
- Review/modify: all `src/engcalc_colab/*.py` only where stable responsibility splits are justified.
- Create: `docs/reference/language.md`
- Create: `docs/reference/functions.md`
- Create: `docs/reference/units.md`
- Create: `docs/reference/plotting-envelopes.md`
- Create: `docs/reference/tables-characteristics.md`
- Create: `docs/reference/matrices.md`
- Create: `docs/reference/verifications.md`
- Create: `tests/test_reference_examples.py`
- Modify: `README.md`
- Modify: `pyproject.toml`
- Modify: `src/engcalc_colab/__init__.py`

**Interfaces:**
- Produces the first declared stable grammar/API contract.
- No new user-facing feature is required in 1.0.

- [ ] **Step 1: Inventory every public function, magic and result form**

Generate a checked list from parser whitelist and magic methods; reconcile it with docs. Any undocumented public call is a release blocker.

- [ ] **Step 2: Define compatibility/deprecation policy**

Document that 1.x preserves valid 1.0 syntax unless a deprecation path is announced; document experimental areas, if any, explicitly rather than implicitly.

- [ ] **Step 3: Review module sizes and split only stable responsibilities**

Candidate extractions are allowed only when roadmap code demonstrates repeated cohesive clusters. Preserve import-level compatibility.

- [ ] **Step 4: Build executable reference-example tests**

Examples must cover:

```text
# scalar math + units
# multi-argument partial evaluation
# table
# piecewise
# extrema/intersections
# exact envelope with named cases
# matrix/linsolve
# check + summary
```

Every code block presented as EngCalc syntax in reference docs must be represented by an executable test fixture.

- [ ] **Step 5: Run supported-Python CI matrix**

At minimum use the Python floor declared in `pyproject.toml` and current stable versions validated by dependencies. Do not claim unsupported versions.

- [ ] **Step 6: Build wheel and sdist and test both from clean environments**

Run imports/tests from a directory outside the repository.

- [ ] **Step 7: Run full regression and visual acceptance set**

Include the professor Excel example as one structural acceptance case, but also include non-structural scalar/table/check examples so 1.0 is not accidentally structure-specific.

- [ ] **Step 8: Bump to 1.0.0 and prepare release metadata**

Update both version declarations only after every gate above is green.

- [ ] **Step 9: Create GitHub Release and attach built artifacts**

If PyPI Trusted Publishing is already configured and authorized, publish 1.0.0; otherwise document the missing account/repository configuration and leave the tested artifacts attached to GitHub Release rather than inventing credentials.

- [ ] **Step 10: Final verification-before-completion**

Record exact source-test count, installed-wheel test count, sdist test count, Python-version matrix and artifact hashes in release notes.

Commit message: `release: EngCalc 1.0.0`.

---

## Dependency and Priority Graph

Execution order is intentionally mostly linear because later features consume earlier language primitives:

```text
0.6.0 merge
   ↓
0.6.1 numeric ergonomics
   ↓
0.7.0 scalar math
   ↓
0.7.1 multi-arg + general partial
   ↓
0.7.2 tables
   ↓
0.7.3 derivation traces
   ↓
0.8.0 piecewise
   ↓
0.8.1 exact characteristics
   ↓
0.8.2 exact envelopes
   ↓
0.8.3 named cases
   ↓
0.9.0 matrices
   ↓
0.10.0 checks
   ↓
0.10.1 summaries
   ↓
1.0.0 stabilization
```

Allowed reprioritization after 0.7.2:

- 0.7.3 derivation traces can move later if exact analysis is more valuable operationally.
- 0.9.0 matrices can move after 0.10.1 if verification workflows are higher priority; neither subsystem is required by the other.
- 0.8.1 must precede 0.8.2.
- 0.7.0 must precede generalized partial evaluation acceptance examples involving trig/exp/log.
- 0.8.0 should precede exact-analysis hardening because piecewise domains expose important root/extrema edge cases.

## Release Gate Template for Every Version

Use the same closing evidence format every time:

```text
Source install/version: PASS
Source full suite: N passed
Wheel built: engcalc_colab-X.Y.Z-py3-none-any.whl
Clean venv install: PASS
Smoke from /tmp: PASS
Full suite against installed wheel: N passed
Repeated source suite: N passed
Temporary workflow cleanup: PASS
README/reference executable examples: PASS
```

Never merge a release branch with a known failing gate and never use tree-shape arguments as a substitute for tests unless the exact validated tree identity is proven after a history-only squash.
