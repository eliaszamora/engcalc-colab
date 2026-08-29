# EngCalc Current Project Context

_Last updated: 2026-08-29 after PR #27 was explicitly approved by the user, merged into `main`, and the merged tree was verified to be product-identical to the validated 0.7.0 release head._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` now contains EngCalc **0.7.0**.
- PR **#27 — `release: EngCalc 0.7.0 scalar engineering mathematics`** merged successfully on 2026-08-29 after explicit user approval.
- Merge commit: `03212e2c47f16492e87aadc451efe8bee6b3ee11`.
- Merged PR head: `3dfeddcf25ce9fd6eb7b2f2b90e616db67c1002d`.
- Definitive validated release tree before cleanup: `0d9e2ae308f40f6cf7707a2de3970b985f7270a7`.
- Latest product corrective commit: `d83ac69f45f57063750baece09b32e3ca52db1c8`.
- `pyproject.toml` and `src/engcalc_colab/__init__.py` both report version **0.7.0** on `main`.
- Comparing merged PR head `3dfeddcf...` to merge commit `03212e2c...` returns **zero changed files**, proving that the merge introduced no product, test, documentation, or workflow content difference beyond the merge commit itself.
- Canonical Colab installation can again use `main` directly:

```python
%pip install -q --upgrade --no-cache-dir git+https://github.com/eliaszamora/engcalc-colab.git
%load_ext engcalc_colab
```

## Approved behavior

### Retained 0.6.x behavior

- `numeric(...)` renders formula → explicit numerical substitution → final result.
- `result(...)` renders formula → final result through the same numerical engine.
- Semantic MathJax spacing remains 4 pt for wrapped continuation rows, 8 pt for a new mathematical stage/consecutive source result, and 16 pt after an explicit blank source line.
- Direct unit-bearing user-function arguments from 0.6.2 remain supported, including dimensional-zero arguments.
- Structural positive moment remains plotted downward.
- Existing plot/envelope behavior, 201-point rendering grid, signed/magnitude envelope semantics and compact characteristic labels remain unchanged.

### EngCalc 0.7.0 scalar engineering mathematics

- Public fixed scalar functions: `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `exp`, `log`; public constant: `pi`.
- These names are reserved from user scalar assignment, numeric assignment and function-parameter use.
- The symbolic layer uses a fixed explicit SymPy mapping; arbitrary SymPy access is not exposed.
- `sqrt` propagates units through a one-half power.
- `sin`, `cos` and `tan` accept dimensionless values or angle quantities and convert degree quantities to radians before evaluation.
- `asin`, `acos` and `atan` require **truly unitless** dimensionless inputs and return explicit Pint radian quantities. Explicit `deg` or `rad` inputs are rejected even though Pint classifies angle dimensions as dimensionless.
- `exp` and `log` likewise require truly unitless dimensionless inputs and reject explicit angle quantities.
- Exact inverse-trig expressions remain unevaluated symbolically until the numeric layer can attach the required angle unit; e.g. `numeric(atan(1))` returns a radian quantity rather than a plain dimensionless `pi/4`.
- Inverse-trig nodes are also preserved through one-argument user-function substitution; e.g. `f(x) = atan(x)`, `a = f(1)`, `numeric(a)` retains radians.
- Explicit angle units are preserved in notebook rendering even though Pint classifies angles as dimensionless; `a := atan(1)` visibly includes `rad`, and `numeric(atan(1), deg)` visibly includes `deg`.
- Scalar math works inside user functions and native plots, including `f(x) = A*sin(pi*x/L)` and the existing 201-point plot grid.
- `numeric(f(x))` may intentionally retain `x` unresolved; generalized non-polynomial partial evaluation remains deferred to 0.7.1.
- Multi-argument user functions remain deferred to 0.7.1.

## Open issues / user feedback

- No known functional regression or release blocker remains open for merged 0.7.0.
- PR #27 accumulated five review threads during final inspection; all five were corrected where necessary, answered, and resolved before merge.
- Intermediate wheel smoke `33232296558` failed only because its validation harness exercised a different symbolic boundary than the approved Pint-backed direct numeric contract. No product/test change was made for that harness-only failure; the smoke was aligned with the public contract and the definitive gate passed.
- **Do not invoke Codex, `@codex review`, Codex Cloud, or any action that may consume the user's Codex quota for EngCalc without explicit user authorization first.** Use direct inspection, repository tools, GitHub Actions and the existing test suite instead.

## Validation evidence

### Original 0.7.0 implementation TDD

- Parser RED run `33229331526`, followed by GREEN parser contracts.
- Symbolic-engine RED run `33229446807`.
- Numeric RED run `33229577297`.
- Integrated acceptance run `33229699540`: **74/74** focused scalar contracts and **336/336** complete source tests passed.

### First review corrective RED → GREEN

- Regression contracts covered exact inverse-trig radian preservation and explicit `rad` / `deg` rendering.
- RED run `33231160212`: **3/3 failed** for the reported pre-corrective defects.
- First corrective implementation commit: `ed7716fb5d965661934bd2309d6ccfee2b417cf3`.
- GREEN run `33231261259`: **32/32** focused and **339/339** complete source tests passed.

### Second review corrective RED → GREEN

- Added contracts requiring `asin`, `acos`, `atan`, `exp` and `log` to reject explicit `deg` and `rad` quantities, plus preservation of inverse-trig nodes through user-function substitution.
- RED run `33232038361`: **11 failed, 3 passed**, reproducing exactly the ten explicit-angle acceptance defects and one user-function radian-loss defect.
- Second corrective implementation commit: `d83ac69f45f57063750baece09b32e3ca52db1c8`.
- GREEN run `33232136886`: **63/63** focused and **350/350** complete source tests passed.

### Definitive EngCalc 0.7.0 distribution gate

GitHub Actions run **`33232439088`** on tree **`0d9e2ae308f40f6cf7707a2de3970b985f7270a7`** completed successfully:

- release metadata: PASS (`0.7.0` in package and `pyproject.toml`);
- focused 0.7.0 contracts: **123 passed in 14.73 s**;
- complete source suite: **350 passed in 66.96 s**;
- real wheel `engcalc_colab-0.7.0-py3-none-any.whl`: built successfully;
- clean virtual-environment wheel installation: PASS;
- installed-wheel smoke from `/tmp` with empty `PYTHONPATH`: PASS;
- smoke explicitly verified exact `atan(1)` radian preservation, visible `rad` / `deg`, rejection of explicit `deg` / `rad` in the dimensionless-only scalar functions through the public Pint-backed `:=` path, user-function inverse-trig radian preservation, `sin(30*deg)`, `sqrt(9*m^2)`, unit-aware user-function evaluation and a 201-point plot;
- source-free complete suite against installed wheel: **350 passed in 67.12 s**;
- repeated complete source suite: **350 passed in 66.04 s**;
- validated artifact: `engcalc-colab-0.7.0-final-wheel`;
- artifact ID: **9708946389**;
- artifact ZIP digest: `sha256:f88e98b7cdee221587caee56b34d0dfae779d2591be3b01609f6af4ff0115668`.

### Merge verification

- PR #27 merged as `03212e2c47f16492e87aadc451efe8bee6b3ee11` with second parent `3dfeddcf25ce9fd6eb7b2f2b90e616db67c1002d`.
- `main` points to that merge commit.
- The merge commit is GitHub-verified.
- Comparing `3dfeddcf25ce9fd6eb7b2f2b90e616db67c1002d` → `03212e2c47f16492e87aadc451efe8bee6b3ee11` yields **no file differences**.
- `pyproject.toml` and package `__version__` on `main` both report **0.7.0**.
- Therefore the merged product/test tree is identical to the fully inspected release head whose product/tests are downstream of the definitive validated distribution-gate tree.

## Roadmap / active plan

- The master roadmap remains on `planning/engcalc-evolution-roadmap`.
- Completed milestone: **0.7.0 — scalar engineering mathematics**.
- Next milestone: **0.7.1 — multi-argument user functions and generalized partial evaluation**.
- 0.7.1 must start from the verified merged 0.7.0 `main` baseline.
- Preserve TDD RED → GREEN and run a fresh source/wheel distribution gate before any 0.7.1 release merge.

## Exact next step

1. Read the 0.7.1 roadmap/spec from `planning/engcalc-evolution-roadmap` and reconcile it with the now-merged 0.7.0 behavior.
2. Define the narrow 0.7.1 acceptance contract before implementation, centered on:
   - multi-argument user functions such as `f(x, a) = ...`;
   - positional argument count/validation and reserved-name rules;
   - numeric evaluation with units for each argument;
   - generalized partial evaluation of non-polynomial expressions while preserving unresolved symbols;
   - compatibility with `numeric(...)`, `result(...)`, `plot(...)`, existing one-argument functions, scalar math and unit semantics.
3. Create a dedicated 0.7.1 feature branch from current `main`.
4. Add RED tests first; only then implement the minimum code needed to turn them GREEN.
5. Run focused tests, the complete source suite, wheel installation/smoke, source-free installed-wheel suite and repeated source suite.
6. Open the 0.7.1 PR only after the distribution gate is clean; do not merge without explicit user approval.

## How to resume in a new conversation

Read this file first. EngCalc **0.7.0 is merged into `main`** via PR #27, merge commit `03212e2c47f16492e87aadc451efe8bee6b3ee11`. The definitive 0.7.0 distribution gate is run `33232439088`: 123 focused, 350 source, 350 installed-wheel and 350 repeated-source tests passed; artifact `9708946389`. Merge verification found zero file differences between the inspected PR head and the merge commit, and both package/runtime version sources on `main` report 0.7.0. All five PR review threads are resolved. Do not invoke Codex for EngCalc without explicit user authorization. The next milestone is **0.7.1 — multi-argument user functions and generalized partial evaluation**; begin by reading the roadmap/spec and freezing the acceptance contract before writing implementation code.