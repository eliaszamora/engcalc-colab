# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–2 are complete with strict RED→GREEN evidence. Immutable symbolic matrices, mathematical matrix operators and one-based indexing are now implemented and fully regression-tested. Task 3 — constructors and core exact matrix functions — is the exact next step. Package/runtime version remains 0.8.0._

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
- Task 2 test-only RED chain ends at **`2181531f20b1b25170ceccf5a5cff9994cd9a867`** before any Task 2 production code.
- Task 2 GREEN product commit: **`06bab76f06fc2a057ecdaab844eeb5717598fcd0`** (`feat: add symbolic matrix algebra and indexing`).
- Task 2 GREEN workflow removed in **`3dd98ab3189f32045248527e6fcee58a026a4f03`**.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge implementation work to `main` without explicit user approval.

## Approved behavior

### Existing integrated behavior

- EngCalc 0.8.0 Piecewise is closed and integrated.
- `%%eng` is a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Narrative, tables, plots, envelopes, multi-argument functions, Piecewise, numeric evaluation, precision/zero tolerance, presentation polish and positive structural moment plotted downward remain regression requirements.

### Approved 0.9.0 Matrix/CAS contract

- Canonical literals use mathematical/MATLAB-inspired syntax:
  - `[a, b, c]` → row matrix `1 x n`;
  - `[a; b; c]` → column matrix `n x 1`;
  - `[a, b; c, d]` → general matrix.
- Commas separate columns; semicolons separate rows; physical newlines inside an open matrix literal are presentation whitespace.
- MATLAB whitespace-only column syntax such as `[a b]` is not supported; commas are mandatory.
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
- LU/QR/Cholesky are explicitly deferred from the mandatory core 0.9.0 implementation plan so they cannot block the core release; they may be a later 0.9.x follow-up.

### Implemented 0.9.0 behavior through Task 2

- Normal-expression `[a,b,c]` evaluates to an immutable `1 x n` SymPy row matrix.
- Semicolon literals such as `[a;b;c]` and `[a,b;c,d]` evaluate to immutable column/general matrices while preserving Task 1 parsing and multiline behavior.
- Matrix literal cells must remain scalar; nested matrices in a cell are rejected.
- `A+B` and `A-B` require two matrices of equal shape; scalar/matrix mixed addition/subtraction is rejected with EngCalc diagnostics.
- `2*A` and `A*2` perform scalar multiplication; `A*B` performs mathematical matrix multiplication, never element-wise broadcasting.
- `A/2` is supported; matrix/matrix division and scalar/matrix division are rejected.
- Matrix powers accept exact integer exponents only, require a square matrix, and preserve immutable exact symbolic output. `A^0`, positive powers and negative integer powers are supported.
- Row-by-column multiplication remains a `1 x 1` matrix and column-by-row multiplication remains the corresponding outer-product matrix.
- Matrix indexing is 1-based. General matrices require two indices; row/column vectors additionally accept one-index shorthand. Two-index access also works on vectors.
- Matrix indices must be positive exact integers; zero, negative, float and symbolic indices are rejected. Out-of-range diagnostics report the attempted index and matrix shape.
- Python/NumPy slicing syntax remains unsupported and is rejected at parser level.
- `EngineeringEngine.namespace` can now hold scalar symbolic values or immutable matrix values.
- Existing scalar behavior remains routed through the same operator paths and passed the complete regression suite.

## Open issues / user feedback

- Task 3 must add exact constructors `identity`, `zeros`, `diag` and core exact functions `transpose`, `det`, `inv`, `trace`, `size`, including stable diagnostics and immutable matrix returns.
- Matrix rendering/presentation has not yet been implemented; current work through Task 2 establishes symbolic truth and algebra semantics first.
- Numerical/unit-aware matrices (`QuantityMatrix`) remain a later task in this same approved 0.9.0 plan.
- `no_vertical_scroll()` remains outside Matrix/CAS.
- Multiline ordinary non-matrix function-call parsing remains a separate ergonomics item; 0.9.0 adds only matrix-literal multiline continuation.
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
- Temporary baseline workflow removed before Task 1.

### 0.9.0 Task 1 RED/GREEN evidence

- Task 1 test-only RED chain ended at `8b0f62c333756c24167426156a92fc118748b137` before production code.
- RED Actions `33320679249`, job `99281977939`: **15 failed, 33 passed in 0.36 s**; artifact `9734793442`, digest `sha256:2f64721b6a7ebd24b17463d237cbac3ac6fbc8d7528dec56a107fe1a88f999f9`.
- GREEN Actions `33321037959`, job `99282936423`, Python 3.13: **48/48 focused GREEN in 0.13 s** and **569/569 full GREEN in 114.64 s**.
- Product commit `86ec35f3b5d20c517f794951e14fa7cd13af0121`; audit showed exactly new `matrix_syntax.py`, modified `models.py`, modified `parser.py`.
- Temporary GREEN workflow removed in `95162527dfee1a796f1c772a31ee5a5d3aed939c`.

### 0.9.0 Task 2 RED evidence

- Task 2 matrix-algebra/indexing tests were committed before any Task 2 production code; test-only chain ended at **`2181531f20b1b25170ceccf5a5cff9994cd9a867`**.
- RED workflow Actions **`33321376876`**, job **`99283827183`**, CPython **3.13.15**: harness **success**, confirming the expected missing-feature failures.
- Exact RED result: **27 failed in 3.77 s**.
- Failures were the expected absence of immutable matrix materialization, evaluator support for row-list matrices, parser/evaluator `Subscript`, matrix shape diagnostics, scalar/matrix operation restrictions and matrix-power contracts.
- RED artifact **`9734978830`**, digest **`sha256:a3eca9188d5f1ac9ac65897bd694b02cc553d0b7d6c9d09af1ee029f14c2042c`**.
- Temporary RED workflow removed in **`91ff7b6837cbcb504ab831cca5158c0ea5cd84be`**.

### 0.9.0 Task 2 GREEN evidence

- GREEN workflow Actions **`33322956670`**, job **`99288034638`**, CPython **3.13.15**: **success**.
- Focused Task 2 suite: **27/27 GREEN in 5.36 s**.
- Complete source suite: **596/596 GREEN in 119.52 s**.
- Product commit: **`06bab76f06fc2a057ecdaab844eeb5717598fcd0`**.
- Product commit audit from workflow parent `f4a5805d6cb6f684d8198350afc092aa7ebe1dc3` shows exactly three source changes: new `src/engcalc_colab/matrix_core.py`, modified `src/engcalc_colab/engine.py`, modified `src/engcalc_colab/parser.py`; no unrelated product files changed.
- GREEN logs artifact **`9735440722`**, digest **`sha256:2811524d746f422f30ea20df558786a30a978a74be3ee4ccbc78306e668d9dbf`**.
- Temporary GREEN workflow removed in **`3dd98ab3189f32045248527e6fcee58a026a4f03`** after validation.
- The only runner warning was GitHub Actions' Node 20 deprecation/forced Node 24 compatibility warning; it is not an EngCalc product failure.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–2 COMPLETE, TASK 3 NEXT**.
  - Base design/spec/clarification/implementation plan: approved.
  - Task 0 isolated baseline: COMPLETE.
  - Task 1 matrix literal parser: COMPLETE, 569/569 GREEN.
  - Task 2 immutable symbolic matrices, matrix operators and one-based indexing: COMPLETE, 596/596 GREEN.
  - Task 3 constructors and core exact matrix functions: NEXT.
  - Package/runtime version remains 0.8.0 until the release-closing task.
- Later roadmap: 0.9.1 exact-first extrema/roots/intersections → 0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization.

## Exact next step

1. Add Task 3 RED tests for `identity(n)`, `zeros(m,n)`, `diag(...)`, `transpose`, `det`, `inv`, `trace` and immutable `size(A)` transport.
2. Include invalid-dimension diagnostics for constructors plus nonsquare/singular matrix diagnostics for exact functions.
3. Run focused Task 3 tests and observe failures caused by unreserved/unimplemented matrix functions.
4. Only after observed RED, add the approved names to the restricted parser and implement the minimal exact helpers in `matrix_core.py`, `engine.py` and the `MatrixShape` result model.
5. Run focused GREEN, then the complete suite; commit production only after both pass.
6. Update this file with Task 3 RED/GREEN SHAs and counts before Task 4.
7. Do not invoke Codex and do not merge without explicit user authorization.

## How to resume in a new conversation

Read this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`. Tasks 0–2 are complete. Task 1 introduced matrix literal transport at `86ec35f3...`. Task 2 introduced immutable SymPy matrices, mathematical matrix operators and one-based indexing at `06bab76f06fc2a057ecdaab844eeb5717598fcd0`; its RED was 27 failures and its GREEN was 27/27 focused plus 596/596 complete. The next action is Task 3 RED for constructors `identity/zeros/diag` and exact functions `transpose/det/inv/trace/size`, followed by minimal implementation only after RED is observed. Never invoke Codex and never merge without explicit user approval.
