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
- `src/engcalc_colab/errors.py` — user-facing EngCalc exceptions and centralized diagnostic hints.

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
- Produces: `_resolve_numeric_function_argument(self, node: ast.AST)` inside the evaluator, returning either an intentionally unresolved SymPy symbol/expression or a fully evaluated Pint quantity.
- Produces: `diagnostic_hint(code: str, **context) -> str` in `errors.py` as the single source for corrective user hints.

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

- [ ] **Step 3: Add the restricted numeric-argument resolver to `numeric(...)` function-call evaluation**

```python
def _resolve_numeric_function_argument(self, node: ast.AST):
    if isinstance(node, ast.Name):
        symbolic = self.visit(node)
        if isinstance(symbolic, sp.Symbol) and self.engine.numeric_context.get(node.id) is None:
            return symbolic
    return self.engine.numeric_context.evaluate_expression(ast.Expression(body=node))
```

Adapt the exact implementation to preserve current line-number/error wrapping, but keep this decision rule: a lone unassigned name may remain symbolic; a complete expression containing values/units is evaluated by `NumericContext`.

- [ ] **Step 4: Add RED diagnostic tests with concrete invalid dimensions**

```python
def test_unknown_numeric_name_error_names_the_missing_value(engine, parse_one):
    with pytest.raises(EngEvaluationError, match="unknown numeric name 'q_missing'"):
        engine.evaluate(parse_one("q := q_missing*kN/m"))


def test_numeric_function_dimension_error_names_function(engine, parse_one):
    engine.evaluate(parse_one("f(x) = L + x"))
    engine.evaluate(parse_one("L := 1*m"))
    with pytest.raises(
        EngEvaluationError,
        match="incompatible units while evaluating numeric function 'f'",
    ):
        engine.evaluate(parse_one("numeric(f(2*kN))"))
```

- [ ] **Step 5: Centralize corrective diagnostics and keep exception types stable**

`errors.py` must expose `diagnostic_hint`. Add stable codes `direct_numeric_argument`, `unknown_numeric_name`, `incompatible_function_units`, and `unresolved_numeric_symbols`. Do not change `EngEvaluationError`/`EngSyntaxError` inheritance.

- [ ] **Step 6: Add acceptance test for the professor-exercise ergonomics**

A `%%eng` test must prove `numeric(M_UU(0*m))` works directly without introducing `x0 := 0*m`.

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
- Numeric angle policy: forward trig accepts dimensionless or angle quantities and evaluates in radians; inverse trig returns a Pint radian quantity.

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

Also assert `sqrt`, trig names, `exp`, `log`, and `pi` cannot be used as assignment targets.

- [ ] **Step 2: Confirm RED**

Run: `pytest tests/test_scalar_math_parser.py -v`
Expected: unsupported/reserved-name failures for the new functions/constant.

- [ ] **Step 3: Add exact SymPy mappings in engine**

Use a fixed mapping, never dynamic `getattr(sympy, name)`:

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

Also test `sqrt(9*m^2) -> 3*m`, `atan(1)` returns radians, `numeric(atan(1), deg) -> 45 deg`, and `exp(2*m)` is rejected.

- [ ] **Step 5: Implement explicit NumericContext adapters**

Use `value ** 0.5` for unit-aware square root. Convert forward-trig angle quantities to radians with Pint before stdlib `math.sin/cos/tan`. For `asin/acos/atan`, evaluate a dimensionless magnitude and wrap the returned float in `ureg.radian`. `exp`/`log` accept only dimensionless quantities.

- [ ] **Step 6: Add plot and partial-numeric acceptance tests**

Use the executable example `f(x) = A*sin(pi*x/L)` with numeric `A`, `L`, and `plot(f(x), x, 0, L)`; also exercise `numeric(f(x))` under the pre-0.7.1 partial behavior to document its current boundary.

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
- `ParsedStatement` gains `parameters: tuple[str, ...] | None`; a compatibility `parameter` property returns the sole parameter for one-argument function definitions and `None` otherwise.
- `UserFunction` becomes `UserFunction(parameters: tuple[str, ...], expression: Any)` with the same one-argument compatibility property.
- `PartialNumericEvaluationResult` keeps `symbolic_expression`, `substitutions`, `unresolved_symbols` and gains `partial_expression` plus `display_arguments: tuple[Any, ...]`.

- [ ] **Step 1: RED parser tests for multi-parameter definitions**

```python
def test_parses_multi_argument_function_definition():
    stmt = parse_cell("M(x, q, L) = q*x*(L-x)/2")[0]
    assert stmt.parameters == ("x", "q", "L")
```

- [ ] **Step 2: RED engine tests for exact arity**

```python
def test_multiarg_function_substitutes_positionally(engine, parse_one):
    engine.evaluate(parse_one("f(x, a, b) = a*x + b"))
    result = engine.evaluate(parse_one("y = f(t, 2, 3)"))
    assert sp.simplify(result.value - (2*sp.Symbol("t") + 3)) == 0
```

Add explicit error tests for two arguments supplied to a three-parameter function and four arguments supplied to the same function.

- [ ] **Step 3: Implement parser/model migration and engine substitution**

The function call implementation must validate `len(args) == len(function.parameters)` and build a deterministic substitution map from parameters to arguments. Update every existing internal use of `statement.parameter`/`function.parameter` in the same commit.

- [ ] **Step 4: RED generalized partial-evaluation tests**

```python
def test_partial_numeric_preserves_symbol_inside_trig_expression(engine, parse_one):
    engine.evaluate(parse_one("f(x, A, L) = A*sin(pi*x/L)"))
    engine.evaluate(parse_one("A := 10*mm"))
    engine.evaluate(parse_one("L := 4*m"))
    result = engine.evaluate(parse_one("numeric(f(x, A, L))"))
    assert result.unresolved_symbols == ("x",)
    assert result.display_arguments == (sp.Symbol("x"), sp.Symbol("A"), sp.Symbol("L"))
```

- [ ] **Step 5: Replace polynomial-only rendering dependency with general partial substitution**

Use this exact target model shape:

```python
@dataclass(frozen=True)
class PartialNumericEvaluationResult:
    statement: ParsedStatement
    symbolic_expression: Any
    substitutions: dict[str, Any]
    unresolved_symbols: tuple[str, ...]
    partial_expression: Any
    display_name: str | None = None
    display_arguments: tuple[Any, ...] = ()
```

`partial_expression` is the symbolic expression after known scalar substitutions have been applied while unresolved symbols remain symbolic. Retire `evaluated_terms` after migrating its existing renderer/tests in this release.

- [ ] **Step 6: Add backward-compatibility tests for all existing one-argument functions**

All existing plot/envelope/numeric examples must preserve user-visible behavior.

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
- Add `TableSeries(display_label: str, values: tuple[Any, ...])`.
- Add `TableResult(statement, variable: str, x_values: tuple[Any, ...], series: tuple[TableSeries, ...])`.
- Public forms: `table(expr1, expr2, x, [0*m, 1*m])` and `table(expr1, expr2, x, 0, L, 21)`; one expression is equally valid.
- Add `render_table(result: TableResult, settings: RenderSettings) -> IPython.display.HTML` in `tabular.py`.

- [ ] **Step 1: RED parser tests for list points restricted to `table(...)`**

Ordinary expressions must continue rejecting arbitrary lists; plot/envelope sweep lists retain their current restricted grammar.

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

- [ ] **Step 3: Implement table resolver by reusing response-series unit normalization**

The explicit-list form evaluates exactly the supplied positions. The uniform form generates `count` inclusive positions from `start` to `end`; require integer `count >= 2`. Both use local overrides and never mutate stored variables.

- [ ] **Step 4: RED HTML-render tests**

Assert headers contain variable and series labels with units; rows honor `%eng_config precision`; multi-series values align in one row per x-position.

- [ ] **Step 5: Integrate `TableResult` into `%%eng` source ordering**

`Math → Table → Math` must flush pending equation groups exactly like figures do.

- [ ] **Step 6: Acceptance-test the professor Excel 21-station use case entirely inside EngCalc**

Use `table(M_UC(x), M_UU(x), x, 0, L, 21)` and an equivalent shear table. Verify exactly 21 rows without Python-side sampling.

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
- Add `DerivationStep(kind: str, expression: Any, label: str | None = None)`.
- Add `derivation_steps: tuple[DerivationStep, ...] = ()` to `EvaluationResult`.
- Extend `RenderSettings` with `steps: Literal["off", "compact", "full"] = "off"` to preserve 0.7.2 visual behavior by default.

- [ ] **Step 1: RED config tests for `steps=off|compact|full` and invalid values**

`%eng_config steps=compact` and `steps=full` must update only the rendering setting; `steps=verbose` must print a stable invalid-option error and preserve the previous setting.

- [ ] **Step 2: RED solve/integral/diff trace tests**

```python
def test_solve_trace_contains_normalized_equation_and_solution(engine, parse_one):
    result = engine.evaluate(parse_one("R = solve(R - q*L, R)"))
    assert [step.kind for step in result.derivation_steps] == ["equation", "solution"]
```

Integral traces must contain `integral` and `evaluated`; differentiation traces must contain `derivative` and `evaluated`.

- [ ] **Step 3: Implement traces at exact operation sites in `_Evaluator.visit_Call`**

For `solve`, store the normalized `Eq` and solved expression. For `integral`, store unevaluated `sp.Integral` and evaluated result. For `diff`, store `sp.Derivative` and evaluated result. `simplify`, `expand`, `factor` store input and transformed output. Never inspect private SymPy algorithms.

- [ ] **Step 4: Render `off`, `compact` and `full` deterministically**

`off`: current output only. `compact`: operation line + assignment result. `full`: every stored `DerivationStep` + assignment result. Do not duplicate the same expression twice when operation result equals final assignment value.

- [ ] **Step 5: Acceptance-test the propped-cantilever derivation**

Verify `R_B(q) = solve(delta_B, R_B_aux)` renders the compatibility equation and solved reaction coherently under `steps=full`.

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
- Public `piecewise(value1, condition1, value2, condition2, default)` generalized to any positive number of value/condition pairs plus exactly one default.
- Restricted comparison AST support only in condition contexts.

- [ ] **Step 1: RED parser tests for allowed and forbidden comparison contexts**

```python
def test_piecewise_accepts_comparison_condition():
    assert parse_cell("q(x) = piecewise(q1, x < a, q2, x <= L, q0)")


def test_bare_comparison_is_rejected_outside_condition_context():
    with pytest.raises(EngSyntaxError):
        parse_cell("flag = x < a")
```

- [ ] **Step 2: Implement context-aware AST validation for `ast.Compare`**

Allow exactly one comparator and only `< <= > >=`; reject chained comparisons and `== !=` in 0.8.0.

- [ ] **Step 3: RED symbolic and numeric tests**

Build `sp.Piecewise` from value/condition pairs plus default. Use `q0 := 0*kN/m`, `q1 := 10*kN/m`, `q2 := 5*kN/m` in numeric tests so all branches carry compatible dimensions.

- [ ] **Step 4: Test integration, differentiation, table and plot workflows**

Use a two-zone distributed load with `q1`, `q2`, `q0`, `a`, `L`; verify table/plot samples switch branches at the exact comparison boundaries.

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
- Add `CharacteristicPoint(x_value: Any, y_value: Any | None = None, kind: str | None = None, exact: bool = True)`.
- Add `CharacteristicResult(statement, kind: str, variable: str, points: tuple[CharacteristicPoint, ...], method: str)`.
- Public calls: `roots(expr, x, start, end)`, `extrema(expr, x, start, end)`, `intersections(expr1, expr2, x, start, end)`.

- [ ] **Step 1: RED exact-root tests**

```python
def test_roots_filters_real_solutions_to_domain(engine, parse_one):
    result = engine.evaluate(parse_one("roots((x-1)*(x-3), x, 0, 2)"))
    assert [float(p.x_value) for p in result.points] == [1.0]
    assert result.method == "exact"
```

- [ ] **Step 2: Implement pure characteristic helpers in `characteristics.py`**

Use these helper contracts:

```python
def _inside_domain_exact(value: sp.Expr, start: sp.Expr, end: sp.Expr) -> bool | None:
    lower = sp.simplify(value - start)
    upper = sp.simplify(end - value)
    if lower.is_nonnegative is True and upper.is_nonnegative is True:
        return True
    if lower.is_negative is True or upper.is_negative is True:
        return False
    return None


def exact_real_roots(
    expr: sp.Expr,
    variable: sp.Symbol,
    start: sp.Expr,
    end: sp.Expr,
) -> tuple[tuple[sp.Expr, ...], tuple[sp.Expr, ...]]:
    accepted: list[sp.Expr] = []
    undecidable: list[sp.Expr] = []
    for candidate in sp.solve(sp.Eq(expr, 0), variable):
        if candidate.is_real is False:
            continue
        inside = _inside_domain_exact(candidate, start, end)
        if inside is True:
            accepted.append(sp.simplify(candidate))
        elif inside is None:
            undecidable.append(sp.simplify(candidate))
    accepted = sorted(set(accepted), key=sp.default_sort_key)
    undecidable = sorted(set(undecidable), key=sp.default_sort_key)
    return tuple(accepted), tuple(undecidable)
```

Candidates in the second tuple are validated numerically in Step 4; they are never silently dropped or mislabeled exact.

- [ ] **Step 3: RED extrema tests including endpoints**

For the propped-beam moment expression, assert an exact critical point `5*L/8`; after numeric assignments, assert global max/min include both critical points and endpoints.

- [ ] **Step 4: Implement numerical fallback without SciPy**

Use a deterministic internal scan of 401 points to create sign-change brackets, then SymPy numerical refinement from bracket midpoints. Deduplicate roots within the configured zero tolerance. Candidates returned as `undecidable` by `exact_real_roots` enter the same numerical domain-validation path. Mark fallback points `exact=False` and `method="numeric"`.

- [ ] **Step 5: Integrate rendering and `%%eng`**

Characteristic results render as concise Math/HTML calculation outputs, never as implicit plots.

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
- Add `GoverningInterval(start: Any, end: Any, source_index: int, exact_boundaries: bool)`.
- Extend `PlotResult` with `crossover_points: tuple[CharacteristicPoint, ...] = ()` and `governing_intervals: tuple[GoverningInterval, ...] = ()` while preserving sampled `governing_max/min` arrays for renderer compatibility.

- [ ] **Step 1: RED crossover tests with a non-grid intersection**

Use `f1(x) = x` and `f2(x) = 1/3` on `[0, 1]`; assert stored crossover is exactly `1/3`, which is not a 201-grid x-value.

- [ ] **Step 2: Build interval partitioning from exact/fallback intersection output**

Partition `[start, end]` by ordered crossover points. For each open interval, evaluate source responses at its symbolic midpoint when possible; otherwise use a numeric midpoint. Store the governing source index.

- [ ] **Step 3: Add magnitude-envelope crossover logic**

For two signed source functions `f`, `g`, solve `f**2 - g**2 = 0`; validate each candidate by comparing `Abs(f)` and `Abs(g)` within zero tolerance before accepting it as a magnitude crossover.

- [ ] **Step 4: Make exact characteristic data authoritative for panel summaries**

Use exact/fallback characteristic analysis for extrema and governing case transitions. Keep the 201-point grid only for drawing curves/fill.

- [ ] **Step 5: Regression-test all 0.5/0.6 envelope visuals and semantics**

Positive moment remains downward, source curves remain faint, magnitude envelope remains one nonnegative branch, and legacy sampled governing arrays remain populated.

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
- Add `ResponseCase(label: str, expression: Any)`.
- Public `case("label", expression)` is accepted only as a response wrapper consumed by `plot`, `envelope` and `table` in 0.8.3.

- [ ] **Step 1: RED parser tests for whitelisted strings**

Strings remain rejected as general expression constants. Accept a string only as the first argument of `case(...)`; reject missing/empty labels and more than two arguments.

- [ ] **Step 2: RED plot/envelope label tests**

```python
def test_named_cases_flow_to_envelope_sources(engine, parse_one):
    result = engine.evaluate(parse_one(
        'envelope(case("Construction", M1(x)), case("Service", M2(x)), x, 0, L)'
    ))
    assert result.source_labels == ("Construction", "Service")
```

- [ ] **Step 3: Implement case unwrapping in the shared response resolver**

Do not store labels in the symbolic namespace and do not alter the wrapped expression.

- [ ] **Step 4: Render labels in legends, governing intervals and tables**

When a governing interval points to `source_index`, resolve its user-visible name through `source_labels`.

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
- Public constructors/operations: `matrix([a11, a12], [a21, a22])`, `vector(b1, b2)`, `transpose(A)`, `det(A)`, `inv(A)`, `linsolve(A, b)`.
- Symbolic storage uses `sp.MatrixBase` instances.
- Numeric homogeneous matrix evaluation stores a common entry unit plus a magnitude matrix; vector evaluation does the same.
- For `linsolve(A, b)`, if A entries share unit `uA` and b entries share unit `ub`, the solution vector has unit `ub/uA`.

- [ ] **Step 1: RED parser tests for nested lists only inside `matrix(...)`**

Ordinary list syntax remains rejected outside already-whitelisted `table` point lists and matrix rows.

- [ ] **Step 2: RED symbolic matrix-operation tests**

Test matrix addition, scalar multiplication, matrix multiplication through `*`, transpose, determinant and inverse. Shape errors must be EngCalc errors, not raw SymPy tracebacks.

- [ ] **Step 3: Implement explicit SymPy Matrix construction and operation routing**

Do not expose Python/SymPy object methods such as `A.inv()` in the DSL.

- [ ] **Step 4: RED `linsolve(A, b)` tests**

Require square A, matching b length and a unique solution in 0.9.0. Singular/multiple-solution systems produce a clear `EngEvaluationError`.

- [ ] **Step 5: Add homogeneous-unit numeric matrix evaluation**

Normalize A entries to one compatible unit and b entries to one compatible unit, solve the pure magnitude system, then attach `ub/uA` to every solution component. Reject heterogeneous entry dimensions explicitly.

- [ ] **Step 6: Render matrices as LaTeX brackets**

No Python list representation in user output.

- [ ] **Step 7: Acceptance-test a 2×2 stiffness-style linear system**

Use A in `kN/m` and b in `kN`; verify `linsolve(A, b)` returns displacement components in `m` and reproduces A·u=b numerically.

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
- Add `CheckResult(statement, label: str | None, left_quantity: Any, operator: str, right_quantity: Any, passed: bool, utilization: float | None = None)`.
- Public `check(condition)` and `check("label", condition)`.
- Comparison support inside `check`: `<`, `<=`, `>`, `>=`; exactly one comparison.

- [ ] **Step 1: RED parser tests for comparison expressions in check context**

`check(Mu <= phiMn)` and `check("Flexion", Mu <= phiMn)` parse; arbitrary assignment `flag = Mu <= phiMn` remains rejected.

- [ ] **Step 2: RED unit-compatibility and utilization tests**

```python
def test_check_compares_compatible_quantities(engine, parse_one):
    engine.evaluate(parse_one("Mu := 110*kN*m"))
    engine.evaluate(parse_one("phiMn := 125*kN*m"))
    result = engine.evaluate(parse_one('check("Flexion", Mu <= phiMn)'))
    assert result.passed is True
    assert result.utilization == pytest.approx(0.88)
```

Also assert `check(Vu <= phiMn)` rejects `kN` versus `kN*m` before comparing magnitudes.

- [ ] **Step 3: Implement exact utilization policy in `verification.py`**

```python
def compute_utilization(left, operator: str, right) -> float | None:
    left_mag = float(left.magnitude)
    right_mag = float(right.magnitude)
    if left_mag < 0 or right_mag < 0:
        return None
    if operator in {"<", "<="} and right_mag != 0:
        return left_mag / right_mag
    if operator in {">", ">="} and left_mag != 0:
        return right_mag / left_mag
    return None
```

Convert right to left units before passing quantities to this helper.

- [ ] **Step 4: Integrate CheckResult rendering into source order**

Render label, criterion, substituted quantities, utilization if available and textual/symbolic PASS/FAIL. Status must remain understandable without color.

- [ ] **Step 5: Acceptance-test a structural mini-memory**

Use one flexure check, one shear check and one deflection check; make one criterion fail and assert the three statuses.

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
- `EngineeringEngine` gains `verification_results: list[CheckResult]` initialized empty and cleared by `reset()`.
- Add `VerificationSummaryResult(statement, checks: tuple[CheckResult, ...])`.
- Public standalone `summary()` returns the current snapshot.

- [ ] **Step 1: RED collection-order and reset tests**

Evaluate two successful `check(...)` statements and assert summary preserves execution order; call `engine.reset()` and assert summary is empty.

- [ ] **Step 2: Implement collection only after a check evaluates successfully**

A check that raises before producing `CheckResult` must not modify `verification_results`.

- [ ] **Step 3: RED summary rendering test**

Require columns: Verification, Criterion, Limit, Utilization, Status. Render an empty utilization cell when the model value is `None`.

- [ ] **Step 4: Integrate `summary()` as standalone output**

Reject assignment `x = summary()` with `EngEvaluationError("summary must be a standalone statement")`.

- [ ] **Step 5: Acceptance-test a multi-check calculation memory**

Run `check(...)`, normal equations, more `check(...)`, then `summary()` and assert source-order display plus complete summary rows.

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

Generate a checked list from the parser whitelist and magic methods. The expected public call families at this point are scalar math, `integral`, `diff`, `solve`, algebraic transforms, `numeric`, `table`, `plot`, `envelope`, `piecewise`, `roots`, `extrema`, `intersections`, `case`, matrix operations, `check`, and `summary`.

- [ ] **Step 2: Define compatibility/deprecation policy**

Document that 1.x preserves valid 1.0 syntax unless a deprecation path is announced; document any experimental area explicitly.

- [ ] **Step 3: Review module sizes and split only stable responsibilities**

Candidate extractions are allowed only when roadmap code demonstrates repeated cohesive clusters. Preserve import-level compatibility for `engcalc_colab` public imports.

- [ ] **Step 4: Build executable reference-example tests**

Create one fixture per documented category: scalar math + units; multi-argument partial evaluation; table; piecewise; extrema/intersections; exact envelope with named cases; matrix/linsolve; check + summary. Every EngCalc code block in reference docs must map to an executable fixture in `tests/test_reference_examples.py`.

- [ ] **Step 5: Run supported-Python CI matrix**

Read the Python floor from `pyproject.toml`; test that floor plus every currently supported minor version up to the CI runner's stable Python version. Remove a version from the declared support range if dependencies cannot install cleanly instead of marking a failing job allowed-to-fail.

- [ ] **Step 6: Build wheel and sdist and test both from clean environments**

For each artifact, install into a fresh venv and run smoke imports from `/tmp` plus the full test suite with `PYTHONPATH` cleared.

- [ ] **Step 7: Run full regression and visual acceptance set**

Include the professor Excel example as one structural case and add at least one non-structural scalar/table/check example so the stable language remains general engineering tooling.

- [ ] **Step 8: Bump to 1.0.0 and prepare release metadata**

Update both version declarations only after every gate above is green.

- [ ] **Step 9: Create GitHub Release and attach built artifacts**

If PyPI Trusted Publishing is already configured and authorized, publish 1.0.0. If not, leave the tested wheel/sdist attached to GitHub Release and record the exact missing repository/account configuration; never invent credentials.

- [ ] **Step 10: Final verification-before-completion**

Record exact source-test count, installed-wheel test count, sdist test count, Python-version matrix and artifact SHA-256 hashes in release notes.

Commit message: `release: EngCalc 1.0.0`.

---

## Dependency and Priority Graph

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

- 0.7.3 derivation traces may move after 0.8.3 if exact engineering analysis becomes the immediate priority; no later feature consumes trace data.
- 0.9.0 matrices may move after 0.10.1; matrices and verification state are independent.
- 0.8.1 must precede 0.8.2.
- 0.7.0 must precede 0.7.1 because generalized partial acceptance covers trig/exp/log expressions.
- 0.8.0 should precede 0.8.1 hardening because piecewise domains expose important root/extrema edge cases.
- 0.8.3 must precede 0.10.0 only for shared restricted string-literal infrastructure; if checks are reprioritized earlier, extract that parser infrastructure as part of the check release.

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

Never merge a release branch with a known failing gate. After a history-only squash, tree identity may prove the merged product bytes are the validated bytes, but retain the original test evidence in the PR/release record.
