# EngCalc Current Project Context

_Last updated: 2026-08-29 after the second PR #27 review corrective was completed, the definitive 0.7.0 source/wheel distribution gate passed, all five review threads were resolved, and the temporary validation workflow was removed._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` remains EngCalc **0.6.2** at `fff645936029f7348b2c080aa30eafab1116d532` until 0.7.0 is explicitly approved and merged.
- Active release branch: `feature/v0.7.0-scalar-engineering-math`.
- Open release PR: **#27 — `release: EngCalc 0.7.0 scalar engineering mathematics`**.
- Candidate package/runtime version: **0.7.0**.
- Latest product corrective commit: `d83ac69f45f57063750baece09b32e3ca52db1c8`.
- Definitive validated release tree: `0d9e2ae308f40f6cf7707a2de3970b985f7270a7`.
- Temporary final validation workflow was removed after the successful gate in `a296671ce11c08d8094e3ab1a2d6d222aff5d215`.
- PR #27 must **not** be merged without explicit user approval.

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

- No known functional release blocker remains in the validated 0.7.0 product/test tree.
- PR #27 accumulated five review threads during final inspection. All five have corrective evidence and are now resolved.
- A failed intermediate wheel smoke (`33232296558`) was a validation-harness mismatch: it tested `numeric(fn(angle-unit))`, while the approved unit-aware direct numeric contract is the Pint-backed `:=` path. No product/test file was changed to address that harness-only failure; the smoke was aligned to the tested public contract and the full gate was rerun successfully.
- **Do not invoke Codex, `@codex review`, Codex Cloud, or any action that may consume the user's Codex quota for EngCalc without explicit user authorization first.** Use direct inspection, repository tools, GitHub Actions and the existing test suite instead.
- PR #27 remains unmerged until the user explicitly authorizes merge.

## Validation evidence

### Original 0.7.0 implementation TDD

- Parser RED run `33229331526`: accepted syntax remained valid while reserved-name contracts failed as expected; parser then reached GREEN.
- Symbolic-engine RED run `33229446807`: new symbolic contracts failed at the expected unsupported boundaries before implementation.
- Numeric RED run `33229577297`: new numeric contracts failed at the expected unsupported boundaries before implementation.
- Integrated acceptance run `33229699540`: **74/74** focused scalar contracts and **336/336** complete source tests passed.
- The earlier distribution gates are superseded as final release evidence because review subsequently required product corrections.

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
- smoke explicitly verified exact `atan(1)` radian preservation, visible `rad` / `deg`, rejection of explicit `deg` / `rad` in the dimensionless-only scalar functions via the public Pint-backed `:=` path, user-function inverse-trig radian preservation, `sin(30*deg)`, `sqrt(9*m^2)`, unit-aware user-function evaluation and a 201-point plot;
- source-free complete suite against installed wheel: **350 passed in 67.12 s**;
- repeated complete source suite: **350 passed in 66.04 s**;
- validated artifact: `engcalc-colab-0.7.0-final-wheel`;
- artifact ID: **9708946389**;
- artifact ZIP digest: `sha256:f88e98b7cdee221587caee56b34d0dfae779d2591be3b01609f6af4ff0115668`.

### Chain of custody after definitive gate

- The final validation workflow was removed after the successful gate.
- No `src/` or `tests/` change is authorized after validated tree `0d9e2ae308f40f6cf7707a2de3970b985f7270a7` without rerunning the distribution gate.
- The final release check must compare that validated tree to the current release-branch head and require all post-gate differences to be CI/documentation-only.

## Roadmap / active plan

- The master roadmap remains on `planning/engcalc-evolution-roadmap`.
- Current release milestone: **0.7.0 — scalar engineering mathematics**.
- The next milestone after an approved/merged 0.7.0 is **0.7.1 — multi-argument user functions and generalized partial evaluation**.
- Do not start 0.7.1 until 0.7.0 is merged and the merged `main` tree is verified/documented.

## Exact next step

1. Compare definitive validated tree `0d9e2ae308f40f6cf7707a2de3970b985f7270a7` against the current release-branch head and confirm only the temporary-workflow removal plus this `CURRENT.md` update occurred after validation.
2. Re-fetch PR #27: require open/unmerged, mergeable, non-draft, zero unresolved review threads and no temporary workflow in the changed-file set.
3. Inspect the final `engine.py`, `numeric.py`, `parser.py` and `renderer.py` patches directly; stop if any new release blocker is found.
4. Update the PR description to identify `33232439088` / `0d9e2ae...` as the authoritative final gate and record all five review threads as resolved.
5. Stop and wait for explicit user authorization before merging PR #27.
6. After authorized merge, verify merged-product identity against the definitive validated product/test tree, update `CURRENT.md` on `main`, and only then begin 0.7.1.

## How to resume in a new conversation

Read this file first. EngCalc 0.7.0 is implemented on `feature/v0.7.0-scalar-engineering-math`; PR #27 is open and must remain unmerged until explicit user approval. Two rounds of final review correctives were reproduced RED and fixed GREEN. The definitive distribution gate is run `33232439088` on tree `0d9e2ae308f40f6cf7707a2de3970b985f7270a7`: 123 focused, 350 source, 350 installed-wheel and 350 repeated-source tests passed; final wheel artifact `9708946389`. All five review threads are resolved. Do not invoke Codex for this project without explicit user authorization. Next: prove post-gate tree identity, do the direct final PR inspection, update the PR body, and wait for explicit merge approval.