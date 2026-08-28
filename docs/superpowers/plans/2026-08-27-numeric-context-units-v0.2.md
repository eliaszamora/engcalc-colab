# EngCalc 0.2.0 Numeric Context + Units Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend EngCalc so symbolic derivations can be evaluated numerically with Pint-backed engineering units without overwriting the symbolic namespace.

**Architecture:** Keep `EngineeringEngine` as the owner of symbolic SymPy state and add a parallel `NumericContext` responsible for unit-aware quantities and restricted numerical evaluation. The parser gains a dedicated numeric-assignment item for `:=`, while `numeric(expr)` remains an ordinary restricted EngCalc call whose result is represented explicitly and rendered through the existing three-column memory layout.

**Tech Stack:** Python 3.10+, SymPy, Pint, IPython notebook magics, pytest.

**Spec:** `docs/superpowers/specs/2026-08-27-numeric-context-units-v0.2-design.md`

## Global Constraints

- Version target is exactly `0.2.0`.
- Symbolic assignments with `=` keep existing 0.1.9 semantics.
- Numeric assignments use `:=` and never overwrite `namespace`, `functions`, or `symbols`.
- `numeric(expr)` evaluates from symbolic definitions plus the numeric context and never mutates symbolic formulas.
- Runtime numeric arithmetic uses Pint; no unrestricted `eval` or `exec` is introduced.
- Initial unit aliases: `mm`, `cm`, `m`, `N`, `kN`, `kgf`, `tonf`, `Pa`, `kPa`, `MPa`, `GPa`, `kg`, `s`, `rad`, `deg`.
- `tonf = 9.80665 * kilonewton`.
- Unit aliases are recognized only in numeric-context expressions; they are not globally reserved symbolic names.
- `numeric(...)` final quantities render with two decimal places in 0.2.0.
- Existing three-column equation layout and 4 pt / 8 pt vertical spacing remain unchanged.
- `%eng_reset` clears symbolic and numeric state and prints `engcalc state cleared`.
- Target-unit conversion, configurable precision, keyword arguments, arrays/tables, and multi-solution solve are out of scope.

---

### Task 1: Parser and result models for numeric syntax

**Files:**
- Modify: `src/engcalc_colab/models.py`
- Modify: `src/engcalc_colab/parser.py`
- Modify: `tests/test_parser.py`
- Create: `tests/test_numeric_parser.py`

**Interfaces:**
- Produces: `ParsedNumericAssignment(line_no: int, source: str, target: str, expression: ast.Expression, blank_before: bool)`.
- Produces: `NumericAssignmentResult` and `NumericEvaluationResult` dataclasses in `models.py` for later engine/renderer tasks.
- Parser output becomes `ParsedStatement | ParsedNumericAssignment | ParsedHeading`.
- `numeric` is added to `_ALLOWED_CALLS` and therefore to `_RESERVED`.

- [ ] **Step 1: Write failing parser tests for `:=`**

Create `tests/test_numeric_parser.py` with tests equivalent to:

```python
import ast
import pytest

from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.models import ParsedNumericAssignment
from engcalc_colab.parser import parse_cell


def test_numeric_assignment_is_parsed_separately_from_symbolic_assignment():
    item = parse_cell("q := 2.8*tonf/m")[0]
    assert isinstance(item, ParsedNumericAssignment)
    assert item.target == "q"
    assert ast.unparse(item.expression) == "2.8 * tonf / m"


def test_numeric_assignment_preserves_blank_before():
    items = parse_cell("A = q*L\n\nq := 2.8*tonf/m")
    assert items[1].blank_before is True


def test_numeric_function_target_is_rejected():
    with pytest.raises(EngSyntaxError, match="numeric assignment target"):
        parse_cell("M(x) := 2*kN*m")


def test_numeric_is_reserved_as_assignment_target():
    with pytest.raises(EngSyntaxError, match="reserved"):
        parse_cell("numeric = 3")
```

- [ ] **Step 2: Run the new parser tests and verify RED**

Run:

```bash
pytest -q tests/test_numeric_parser.py
```

Expected: failures because `ParsedNumericAssignment` does not exist and `:=` is not recognized.

- [ ] **Step 3: Add the new parsed/result dataclasses**

In `models.py`, add:

```python
@dataclass(frozen=True)
class ParsedNumericAssignment:
    line_no: int
    source: str
    target: str
    expression: ast.Expression
    blank_before: bool = False


@dataclass(frozen=True)
class NumericAssignmentResult:
    statement: ParsedNumericAssignment
    quantity: Any


@dataclass(frozen=True)
class NumericEvaluationResult:
    statement: ParsedStatement
    symbolic_expression: Any
    substitutions: dict[str, Any]
    quantity: Any
    display_name: str | None = None
```

- [ ] **Step 4: Implement top-level `:=` parsing before ordinary `=` parsing**

In `parser.py`:

- add `numeric` to `_ALLOWED_CALLS`;
- create `_split_top_level_numeric_assignment(text)` that scans bracket depth and detects exactly one top-level `:=`;
- require a simple identifier target validated by `_validate_target`;
- reject function-style numeric targets;
- normalize `^` to `**` on the RHS;
- validate the AST with the same restricted-node set;
- return `ParsedNumericAssignment` with `blank_before` preserved.

Do not alter ordinary `=` parsing behavior.

- [ ] **Step 5: Run parser tests and existing parser regression**

Run:

```bash
pytest -q tests/test_numeric_parser.py tests/test_parser.py
```

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

```bash
git add src/engcalc_colab/models.py src/engcalc_colab/parser.py tests/test_numeric_parser.py tests/test_parser.py
git commit -m "feat: parse numeric assignments"
```

---

### Task 2: Pint-backed NumericContext

**Files:**
- Create: `src/engcalc_colab/numeric.py`
- Create: `tests/test_numeric_context.py`
- Modify: `src/engcalc_colab/errors.py` only if a focused numeric error subclass improves clarity.

**Interfaces:**
- Produces: `NumericContext` with methods:
  - `reset() -> None`
  - `assign(name: str, expression: ast.Expression) -> pint.Quantity`
  - `evaluate_symbolic(expr: sp.Expr) -> tuple[dict[str, pint.Quantity], pint.Quantity]`
  - `get(name: str) -> pint.Quantity | None`
- Produces one internal Pint registry owned by the context.
- Numeric RHS names resolve in this order: previously assigned numeric values, supported unit aliases; otherwise error.

- [ ] **Step 1: Write failing NumericContext tests**

Create tests covering:

```python
import ast
import sympy as sp
import pytest

from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.numeric import NumericContext


def expr(text):
    return ast.parse(text.replace("^", "**"), mode="eval")


def test_assigns_engineering_quantity_with_tonf():
    ctx = NumericContext()
    q = ctx.assign("q", expr("2.8*tonf/m"))
    assert q.to("tonf/m").magnitude == pytest.approx(2.8)


def test_numeric_values_can_reference_previous_numeric_values():
    ctx = NumericContext()
    ctx.assign("q", expr("2.8*tonf/m"))
    ctx.assign("L", expr("4*m"))
    p = ctx.assign("P", expr("q*L"))
    assert p.to("tonf").magnitude == pytest.approx(11.2)


def test_tonf_conversion_is_exact_definition():
    ctx = NumericContext()
    force = ctx.assign("F", expr("1*tonf"))
    assert force.to("kN").magnitude == pytest.approx(9.80665)


def test_missing_numeric_symbol_in_symbolic_evaluation_is_concise():
    ctx = NumericContext()
    q, L = sp.symbols("q L")
    ctx.assign("q", expr("2.8*tonf/m"))
    with pytest.raises(EngEvaluationError, match="requires values for: L"):
        ctx.evaluate_symbolic(q*L)


def test_reset_clears_values():
    ctx = NumericContext()
    ctx.assign("L", expr("4*m"))
    ctx.reset()
    assert ctx.get("L") is None
```

Also test unknown names and incompatible numeric arithmetic produce `EngEvaluationError` without raw Pint tracebacks.

- [ ] **Step 2: Run NumericContext tests and verify RED**

Run:

```bash
pytest -q tests/test_numeric_context.py
```

Expected: import failure because `numeric.py` does not exist.

- [ ] **Step 3: Implement restricted numeric AST evaluation**

Create `numeric.py` with:

```python
class NumericContext:
    def __init__(self) -> None:
        self.ureg = UnitRegistry()
        self.ureg.define("tonf = 9.80665 * kilonewton")
        self.values: dict[str, Quantity] = {}
```

Implement an internal `ast.NodeVisitor` supporting only:

- integer/float constants;
- names;
- unary `+` / `-`;
- binary `+ - * / **`.

Name resolution:

1. `self.values[name]` if already assigned;
2. a hard-coded alias mapping to units from this registry;
3. otherwise `EngEvaluationError("unknown numeric name '...'" )`.

Catch Pint dimensionality/undefined-unit errors and convert them to concise `EngEvaluationError` messages.

- [ ] **Step 4: Implement safe SymPy-to-Pint evaluation**

`evaluate_symbolic(expr)` must:

- inspect `expr.free_symbols`;
- collect missing numeric names and fail deterministically with sorted names;
- recursively evaluate SymPy `Number`, `Symbol`, `Add`, `Mul`, and `Pow` nodes using Pint quantities;
- support dimensionless numeric results as ordinary Pint dimensionless quantities or numbers consistently;
- return `(substitutions, quantity)` without mutating `expr` or any symbolic namespace.

Do not convert the expression to Python source and do not call `eval`.

- [ ] **Step 5: Run NumericContext tests**

```bash
pytest -q tests/test_numeric_context.py
```

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

```bash
git add src/engcalc_colab/numeric.py src/engcalc_colab/errors.py tests/test_numeric_context.py
git commit -m "feat: add Pint numeric context"
```

---

### Task 3: Integrate numeric assignment and `numeric(...)` into EngineeringEngine

**Files:**
- Modify: `src/engcalc_colab/engine.py`
- Modify: `src/engcalc_colab/models.py`
- Create: `tests/test_numeric_engine.py`
- Modify: `tests/test_engine.py` if existing assertions require generalized result typing.

**Interfaces:**
- `EngineeringEngine.__init__` owns `self.numeric_context = NumericContext()`.
- `EngineeringEngine.evaluate(...)` accepts `ParsedStatement | ParsedNumericAssignment` and returns `EvaluationResult | NumericAssignmentResult | NumericEvaluationResult`.
- `numeric(expr)` is intercepted before the generic symbolic-call path.
- `%eng_reset` later calls `engine.reset()`, which clears `numeric_context` too.

- [ ] **Step 1: Write failing engine acceptance tests**

Cover this exact workflow:

```python
engine = EngineeringEngine()
run(engine, "V_B = 3*q*L/8")
run(engine, "q := 2.8*tonf/m")
run(engine, "L := 4*m")
result = run(engine, "numeric(V_B)")
assert result.quantity.to("tonf").magnitude == pytest.approx(4.2)
assert str(engine.namespace["V_B"]) == "3*L*q/8"
```

Also cover:

- `M_A = q*L^2/8` -> `5.6 tonf*m`;
- reassigning `q := 3.5*tonf/m` changes the numeric result but not `M_A`;
- `numeric(q*L^2/8)` direct expression;
- `V(x)` function plus `x := 2*m` evaluates numerically;
- wrong arity `numeric(a, b)` raises a concise line-aware error;
- missing values surface line-aware errors;
- `engine.reset()` clears both namespaces.

- [ ] **Step 2: Run numeric engine tests and verify RED**

```bash
pytest -q tests/test_numeric_engine.py
```

Expected: failures because engine does not know `ParsedNumericAssignment` or `numeric` semantics.

- [ ] **Step 3: Add NumericContext ownership and reset integration**

In `EngineeringEngine`:

```python
self.numeric_context = NumericContext()
```

and in `reset()`:

```python
self.numeric_context.reset()
```

- [ ] **Step 4: Evaluate ParsedNumericAssignment without touching symbolic state**

Add a dedicated branch before `_Evaluator` symbolic processing:

```python
if isinstance(statement, ParsedNumericAssignment):
    quantity = self.numeric_context.assign(statement.target, statement.expression)
    return NumericAssignmentResult(statement=statement, quantity=quantity)
```

No assignment to `namespace`, `functions`, or `symbols` is allowed in this branch.

- [ ] **Step 5: Implement `numeric(expr)` in `_Evaluator`**

Before generic argument evaluation in `visit_Call`:

- require exactly one argument;
- evaluate that argument symbolically using the existing evaluator, including expansion of named EngCalc functions;
- preserve a display name when the argument is a bare name such as `V_B`;
- call `engine.numeric_context.evaluate_symbolic(symbolic_expression)`;
- return a marker object or signal that `EngineeringEngine.evaluate` converts to `NumericEvaluationResult`.

The implementation must not insert the final numeric quantity into `namespace`.

- [ ] **Step 6: Run numeric engine tests plus existing engine suite**

```bash
pytest -q tests/test_numeric_engine.py tests/test_engine.py
```

Expected: PASS.

- [ ] **Step 7: Commit Task 3**

```bash
git add src/engcalc_colab/engine.py src/engcalc_colab/models.py tests/test_numeric_engine.py tests/test_engine.py
git commit -m "feat: evaluate symbolic results numerically"
```

---

### Task 4: Render numeric quantities and notebook flow

**Files:**
- Modify: `src/engcalc_colab/renderer.py`
- Modify: `src/engcalc_colab/magic.py`
- Create: `tests/test_numeric_renderer.py`
- Modify: `tests/test_magic.py`
- Modify: `tests/test_visual_layout.py` only for regression assertions that involve result unions.

**Interfaces:**
- `render_aligned_results(...)` accepts symbolic and numeric result variants.
- Numeric assignment row: `q | = | 2.80\,\mathrm{tonf}/\mathrm{m}`.
- Named numeric evaluation row keeps the named expression on the left and displays formula, substitution, and final value on the right.
- Direct `numeric(expression)` uses the symbolic expression as the left/display expression when no named target exists.
- Quantity formatting is centralized in renderer helpers; two decimal places are fixed in 0.2.0.

- [ ] **Step 1: Write failing renderer tests**

Tests must assert semantic LaTeX fragments rather than brittle full-string snapshots. Cover:

```python
assert r"\mathrm{tonf}" in latex
assert r"\mathrm{m}" in latex
assert "4.20" in latex
assert r"\begin{array}{lcl}" in latex
assert r"\\[4pt]" in consecutive_rows
assert r"\\[8pt]" in blank_separated_rows
```

For `numeric(V_B)`, assert the row contains:

- `V_B` on the left;
- the symbolic formula `3 q L / 8` in engineering factor order;
- substituted values with units;
- final `4.20 tonf`.

- [ ] **Step 2: Run renderer tests and verify RED**

```bash
pytest -q tests/test_numeric_renderer.py tests/test_magic.py
```

Expected: failures because renderer only understands `EvaluationResult`.

- [ ] **Step 3: Add quantity and substitution LaTeX helpers**

Implement focused helpers in `renderer.py`:

- `_quantity_latex(quantity, precision=2)`;
- `_unit_latex(unit)` using upright `\mathrm{...}` unit text;
- `_numeric_substitution_latex(symbolic_expression, substitutions)` that replaces each SymPy symbol with a parenthesized formatted quantity for display only.

Keep existing `_EngineeringLatexPrinter` for symbolic formulas.

- [ ] **Step 4: Extend row rendering by explicit result type**

`render_result(...)` dispatches:

- `EvaluationResult` -> current symbolic behavior unchanged;
- `NumericAssignmentResult` -> target `=` formatted quantity;
- `NumericEvaluationResult` -> formula/substitution/final quantity chain.

Preserve the existing three-column split on the first main equality only.

- [ ] **Step 5: Generalize magic buffering and reset message**

In `magic.py`:

- buffer the supported result union;
- keep heading flush behavior unchanged;
- let numeric and symbolic rows coexist inside one calculation block;
- change reset output to exactly `engcalc state cleared`.

- [ ] **Step 6: Run renderer, magic, and visual regressions**

```bash
pytest -q tests/test_numeric_renderer.py tests/test_magic.py tests/test_visual_layout.py
```

Expected: PASS.

- [ ] **Step 7: Commit Task 4**

```bash
git add src/engcalc_colab/renderer.py src/engcalc_colab/magic.py tests/test_numeric_renderer.py tests/test_magic.py tests/test_visual_layout.py
git commit -m "feat: render unit-aware numeric calculations"
```

---

### Task 5: Packaging, version, documentation, and full acceptance

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/engcalc_colab/__init__.py`
- Modify: `README.md`
- Modify: `tests/test_packaging.py`
- Modify: `tests/test_parser.py` version assertion if present.
- Create or modify: `tests/test_acceptance_numeric_units.py`

**Interfaces:**
- Runtime dependency includes `pint>=0.24` or the minimum version verified locally.
- `engcalc_colab.__version__ == "0.2.0"`.
- README documents the 0.2.0 syntax and its deferred limitations.

- [ ] **Step 1: Write failing packaging/version tests**

Update tests to require:

```python
assert _project_metadata()["version"] == "0.2.0"
assert __version__ == "0.2.0"
assert any(dep.lower().startswith("pint") for dep in dependencies)
```

- [ ] **Step 2: Run packaging tests and verify RED**

```bash
pytest -q tests/test_packaging.py tests/test_parser.py
```

Expected: FAIL on version/dependency assertions.

- [ ] **Step 3: Update package metadata**

Set:

```toml
version = "0.2.0"
dependencies = ["sympy>=1.13", "pint>=0.24"]
```

and:

```python
__version__ = "0.2.0"
```

If the installed local Pint version requires a different safe floor, use the lowest verified compatible version and document the reason in the PR.

- [ ] **Step 4: Add end-to-end acceptance test**

Create an IPython-magic or engine-level acceptance test matching the approved spec:

```text
V_B = 3*q*L/8
V_A = 5*q*L/8
M_A = q*L^2/8
q := 2.8*tonf/m
L := 4*m
numeric(V_B)
numeric(V_A)
numeric(M_A)
```

Assert final quantities are 4.20 tonf, 7.00 tonf, and 5.60 tonf*m, and symbolic definitions remain unchanged.

Then reassign:

```text
q := 3.5*tonf/m
numeric(M_A)
```

and assert the new result is 7.00 tonf*m with the symbolic `M_A` still unchanged.

- [ ] **Step 5: Update README command reference and examples**

Document:

- symbolic `=` vs numeric `:=`;
- `numeric(expr)`;
- supported units;
- numeric values referencing previously defined numeric values;
- formula -> substitution -> result rendering;
- 2-decimal default;
- `%eng_reset` now clears all EngCalc state;
- deferred conversion/precision syntax.

- [ ] **Step 6: Run the full test suite fresh**

```bash
pytest -q
```

Expected: all tests PASS with zero failures.

- [ ] **Step 7: Run a manual acceptance snippet in a fresh Python/IPython process**

Install editable package with dev dependencies if needed, load the extension, run the acceptance cell, and inspect that no traceback is emitted and the three numerical values are correct.

- [ ] **Step 8: Commit Task 5**

```bash
git add pyproject.toml src/engcalc_colab/__init__.py README.md tests/test_packaging.py tests/test_parser.py tests/test_acceptance_numeric_units.py
git commit -m "release: prepare EngCalc 0.2.0"
```

---

## Final verification and integration checklist

- [ ] Re-read the approved spec and map every included requirement to Tasks 1-5.
- [ ] Confirm deferred features were not accidentally introduced.
- [ ] Run `pytest -q` fresh and record the exact passing count.
- [ ] Inspect `git diff main...HEAD` and verify only intended source, tests, docs, and metadata changed.
- [ ] Open a pull request targeting `main` with the spec and plan linked in the body.
- [ ] Verify GitHub reports the PR mergeable and inspect the PR patch before merge.
- [ ] Squash-merge the PR.
- [ ] Fetch `main` after merge and verify `pyproject.toml` reports `0.2.0` and `numeric.py` is present.
