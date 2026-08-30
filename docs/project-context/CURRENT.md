# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–3 are complete with strict RED→GREEN evidence. Exact matrix constructors and core functions are implemented and fully regression-tested. Task 4 — matrix-valued user functions and matrix-aware existing CAS transforms — is the exact next step. Package/runtime version remains 0.8.0._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated branch: **`main`** at **`9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`**.
- Runtime/package version on `main`: **0.8.0**.
- Piecewise PR #31: **MERGED**, merge commit `eca248c376128da16ff9526751790aebe2089646`.
- Active implementation branch: **`feature/v0.9.0-matrix-cas`**.
- Feature branch was created from exact `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`.
- Approved planning artifacts were copied into the feature branch without carrying planning-branch source/history changes; seed commit: `74d045f079a4458ffb31d9db0f195ffab433d659`.
- Formal 0.9.0 design: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.0-matrix-cas-design.md`.
- Normative numeric clarification: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.0-matrix-cas-numeric-semantics-clarification.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.0-matrix-cas-implementation.md`.
- Task 1 GREEN product commit: **`86ec35f3b5d20c517f794951e14fa7cd13af0121`** (`feat: parse EngCalc matrix literals`).
- Task 2 GREEN product commit: **`06bab76f06fc2a057ecdaab844eeb5717598fcd0`** (`feat: add symbolic matrix algebra and indexing`).
- Task 3 test-only RED commit: **`8e3ca7fb1054e0522556586541edb66d2408c354`**.
- Task 3 GREEN product commit: **`1b8ae5143d62dea1124411ef2e28bd61ef60db6e`** (`feat: add exact matrix constructors and core functions`).
- Task 3 temporary GREEN workflow removed in `4c573b0637e639f29ac3e24e8b617ffd7051a160`; temporary implementation harness removed in `bf32b52da8bc752c22506c6d14f811ad260be5c8`.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge implementation work to `main` without explicit user approval.

## Approved behavior

### Existing integrated behavior

- EngCalc 0.8.0 Piecewise is closed and integrated.
- `%%eng` is a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Narrative, tables, plots, envelopes, multi-argument functions, Piecewise, numeric evaluation, precision/zero tolerance, presentation polish and positive structural moment plotted downward remain regression requirements.

### Approved 0.9.0 Matrix/CAS contract

- Canonical literals use mathematical/MATLAB-inspired syntax: `[a, b, c]` row matrix, `[a; b; c]` column matrix, `[a, b; c, d]` general matrix.
- Commas separate columns; semicolons separate rows; physical newlines inside an open matrix literal are presentation whitespace.
- MATLAB whitespace-only column syntax is not supported; commas are mandatory.
- Vectors are matrices; there are no mandatory public `vector()` / `row()` constructors.
- Matrix indexing is **1-based**. Vector shorthand accepts one index; general matrices require two. Slicing is deferred.
- Symbolic matrices use immutable SymPy matrix semantics.
- `A*B` is matrix multiplication; no element-wise/broadcasting NumPy semantics are introduced.
- Core constructors: `identity(n)`, `zeros(m,n)`, `diag(...)`.
- Core functions: `transpose`, `det`, `inv`, `trace`, `rank`, `rref`, `norm`, `size`, `eigenvals`, `eigenvects`.
- `simplify`, `expand`, `factor`, `subs`, `diff` and definite `integral` become matrix-aware entrywise where mathematically unambiguous. Scalar trig functions remain scalar-only.
- Matrix-valued user functions are supported and retain existing exact positional arity and parameter-shadowing semantics.
- `solve(A,b)` is the canonical exact linear-system API; scalar `solve(eq,x)` remains unchanged.
- Exact symbolic algebra/solve happens first. `numeric(...)` performs dimensional evaluation afterwards.
- `numeric(A)` is the canonical numerical matrix path; matrix-valued persistent `:=` is deferred.
- Numerical matrix outputs preserve **per-entry Pint dimensionality**. Heterogeneous engineering matrices are first-class and are never flattened to one fake unit.
- `QuantityMatrix` is an immutable numerical output boundary, not a second public algebra engine.
- Exact dimensionless zero may inherit a physical unit only when the operation context makes the inheritance unambiguous.
- In matrix multiplication, every product term contributing to one result cell must be dimensionally compatible with the other terms in that cell; different result cells may have different dimensions.
- Numerical `rank`, `rref`, `norm` and ordinary eigenanalysis require a dimensionless or common-scale matrix; heterogeneous physical matrices are rejected rather than stripped of units.
- Existing `table(...,[...])` point lists and plot/envelope sweep lists remain contextual collections, not row matrices.
- Indexed scalar matrix entries may be used with scalar `table`, `plot` and `envelope`; whole-matrix table/plot/envelope remains outside 0.9.0.
- Piecewise scalar expressions may appear inside matrix cells.
- Generalized structural eigenproblems, sparse/global FEM matrices, block matrices, slicing, least squares, pseudoinverse, SVD, NumPy-style broadcasting and matrix-valued `:=` remain deferred.
- LU/QR/Cholesky are deferred from mandatory core 0.9.0.

### Implemented 0.9.0 behavior through Task 3

- Normal-expression matrix literals evaluate to immutable SymPy matrices with approved row/column/general orientation.
- Matrix literal cells must remain scalar; nested matrices in a cell are rejected.
- `A+B`, `A-B`, scalar multiplication/division, mathematical `A*B`, and exact integer square-matrix powers are implemented with stable EngCalc diagnostics.
- Matrix indexing is 1-based; row/column vectors additionally accept one-index shorthand; slicing remains unsupported.
- `EngineeringEngine.namespace` can hold scalar symbolic values or immutable matrix values.
- `identity(n)`, `zeros(m,n)` and `diag(...)` return immutable exact matrices; constructor dimensions must be positive exact integers and `diag` entries must be scalar.
- `transpose(A)` returns an immutable exact matrix.
- `det(A)` and `trace(A)` return exact scalar SymPy expressions and require square matrices.
- `inv(A)` returns an immutable exact inverse, requires a square matrix and rejects singular matrices with an EngCalc diagnostic.
- `size(A)` returns immutable transport `MatrixShape(rows, cols)`, not a Python tuple or matrix.
- All eight Task 3 names are reserved in the restricted DSL and continue to reject keyword arguments.
- Existing scalar behavior remains routed through the same engine and passes the complete regression suite.

## Open issues / user feedback

- Task 4 must add matrix-valued user functions and entrywise matrix-aware `simplify`, `expand`, `factor`, `subs`, `diff`, and definite `integral` while keeping scalar trig calls matrix-invalid.
- Piecewise scalar cells inside matrices must remain differentiable entrywise; derivative breakpoint metadata must not be lost for matrix-valued user functions.
- Matrix rendering/presentation has not yet been implemented; current work establishes symbolic truth before presentation.
- Numerical/unit-aware matrices (`QuantityMatrix`) remain a later task in this same approved 0.9.0 plan.
- `rank`, `rref`, `norm`, `eigenvals`, `eigenvects` and `solve(A,b)` are later exact tasks in the plan.
- `no_vertical_scroll()` remains outside Matrix/CAS.
- Multiline ordinary non-matrix function-call parsing remains a separate ergonomics item.
- Generalized eigenproblem `K phi = lambda M phi` needs a future dedicated design/API.
- Auxiliary branch `noop` is non-product and contains no unique feature work.

## Validation evidence

### 0.8.0 integrated baseline

- Authoritative distribution gate: Actions `33316141809`, Python 3.13.15.
- Source before wheel: **557/557 GREEN**.
- Installed-wheel/source-free suite: **557/557 GREEN**.
- Source recheck: **557/557 GREEN**.
- Fresh final pre-merge gate: Actions `33316786989`, **557/557 GREEN in 116.63 s**.
- Post-merge compare `df11f1ec...` → `eca248c3...`: **zero changed files**.

### 0.9.0 Task 0 execution evidence

- `feature/v0.9.0-matrix-cas` created from exact current `main@9b90014f...`.
- Fresh baseline workflow Actions `33320306377`, job `99280984551`, Python 3.13: **success**.
- Runtime check confirmed **0.8.0** and full baseline remained GREEN.

### 0.9.0 Task 1 RED/GREEN evidence

- RED Actions `33320679249`, job `99281977939`: **15 failed, 33 passed in 0.36 s**; artifact `9734793442`, digest `sha256:2f64721b6a7ebd24b17463d237cbac3ac6fbc8d7528dec56a107fe1a88f999f9`.
- GREEN Actions `33321037959`, job `99282936423`, Python 3.13: **48/48 focused GREEN in 0.13 s** and **569/569 full GREEN in 114.64 s**.
- Product commit `86ec35f3b5d20c517f794951e14fa7cd13af0121`.

### 0.9.0 Task 2 RED/GREEN evidence

- Test-only RED chain ended at `2181531f20b1b25170ceccf5a5cff9994cd9a867` before Task 2 production code.
- RED Actions `33321376876`, job `99283827183`, CPython 3.13.15: **27 failed in 3.77 s**; artifact `9734978830`, digest `sha256:a3eca9188d5f1ac9ac65897bd694b02cc553d0b7d6c9d09af1ee029f14c2042c`.
- GREEN Actions `33322956670`, job `99288034638`: **27/27 focused GREEN in 5.36 s** and **596/596 full GREEN in 119.52 s**.
- Product commit `06bab76f06fc2a057ecdaab844eeb5717598fcd0`; audit showed exactly new `matrix_core.py`, modified `engine.py`, modified `parser.py`.

### 0.9.0 Task 3 RED evidence

- Task 3 tests were committed first at **`8e3ca7fb1054e0522556586541edb66d2408c354`**, before any Task 3 production code.
- RED harness commit `15900217c52c67f285cb63efb3f954b225c05fb0`; Actions **`33323351004`**, CPython 3.13.
- Exact RED result: **30 failed, 1 passed in 3.80 s**.
- The 30 failures were the expected absence of `identity`, `zeros`, `diag`, `transpose`, `det`, `inv`, `trace`, `size` and `MatrixShape`; the one passing test preserved the historical keyword-argument restriction.
- RED artifact **`9735523579`**, digest **`sha256:0493babcbc1c14a4a88ea086cf0617085bbea3fa53e7f13bfbe8eee2c0f83b83`**.
- Temporary RED workflow was removed in `dcaccee9c07533f8120616ddb18187807adcb41a`.

### 0.9.0 Task 3 GREEN evidence

- Final GREEN workflow Actions **`33323899152`**, job **`99290546647`**, CPython **3.13.15**: **success**.
- Patch compile check and `git diff --check`: **GREEN**.
- Focused Task 3 suite: **31/31 GREEN in 4.21 s**.
- Complete source suite: **627/627 GREEN in 88.53 s**.
- Product commit: **`1b8ae5143d62dea1124411ef2e28bd61ef60db6e`** (`feat: add exact matrix constructors and core functions`).
- Product commit audit shows exactly four production changes: `src/engcalc_colab/engine.py`, `src/engcalc_colab/matrix_core.py`, `src/engcalc_colab/models.py`, `src/engcalc_colab/parser.py`; no unrelated product files changed.
- GREEN logs artifact **`9735690795`**, digest **`sha256:57ab0b4c3c9f2606e82aeca0bc9c0f71988d33c5db5db1649b75013e13d2ab2d`**.
- Initial Task 3 GREEN attempts failed only in temporary CI harness/configuration before functional pytest; no production commit was made until the final focused and full suites both passed.
- Temporary final GREEN workflow and implementation harness were removed after validation.
- The only runner warning was GitHub Actions' Node 20 deprecation/forced Node 24 compatibility warning; it is not an EngCalc product failure.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–3 COMPLETE, TASK 4 NEXT**.
  - Base design/spec/clarification/implementation plan: approved.
  - Task 0 isolated baseline: COMPLETE.
  - Task 1 matrix literal parser: COMPLETE, 569/569 GREEN.
  - Task 2 immutable symbolic matrices, matrix operators and one-based indexing: COMPLETE, 596/596 GREEN.
  - Task 3 constructors and core exact matrix functions: COMPLETE, 31/31 focused + 627/627 full GREEN.
  - Task 4 matrix-valued user functions and matrix-aware existing CAS transforms: NEXT.
  - Package/runtime version remains 0.8.0 until the release-closing task.
- Later roadmap: 0.9.1 exact-first extrema/roots/intersections → 0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization.

## Exact next step

1. Add Task 4 RED tests in `tests/test_matrix_user_functions.py` for matrix-valued functions such as `R(theta)` and structural `k(E,I,L)`, exact arity and local-parameter shadowing.
2. Add Task 4 RED tests in `tests/test_matrix_calculus.py` for entrywise `simplify`, `expand`, `factor`, `subs`, `diff`, and definite `integral`.
3. Include a Piecewise-cell derivative regression and preserve derivative-breakpoint metadata required by later numeric evaluation.
4. Run only the new Task 4 tests and confirm failures are caused by missing matrix-valued substitution/CAS behavior, not malformed tests.
5. Only after observed RED, implement minimal `map_matrix_entries(...)` and matrix-aware symbolic substitution/CAS dispatch.
6. Keep scalar trig calls matrix-invalid.
7. Run focused GREEN, then the complete suite; commit production only after both pass.
8. Update this file with Task 4 RED/GREEN SHAs and counts before Task 5.
9. Do not invoke Codex and do not merge without explicit user authorization.

## How to resume in a new conversation

Read this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`. Tasks 0–3 are complete. Task 3 introduced exact `identity/zeros/diag/transpose/det/inv/trace/size` behavior at `1b8ae5143d62dea1124411ef2e28bd61ef60db6e`; its RED was 30 failed / 1 passed and its final GREEN was 31/31 focused plus 627/627 complete. The exact next action is Task 4 RED for matrix-valued user functions and matrix-aware entrywise CAS transforms. Never invoke Codex and never merge without explicit user approval.
