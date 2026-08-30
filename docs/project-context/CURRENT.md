# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Task 0 baseline and Task 1 matrix-literal parser are complete with strict RED→GREEN evidence. Task 2 — immutable symbolic matrices, one-based indexing and matrix operators — is now the exact next step. Package/runtime version remains 0.8.0._

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
- Task 1 test-only RED chain ends at `8b0f62c333756c24167426156a92fc118748b137` before any Task 1 production code.
- Task 1 GREEN product commit: **`86ec35f3b5d20c517f794951e14fa7cd13af0121`** (`feat: parse EngCalc matrix literals`).
- Task 1 GREEN workflow removed in `95162527dfee1a796f1c772a31ee5a5d3aed939c`.
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

### Implemented 0.9.0 behavior through Task 1

- Normal-expression `[a,b,c]` is accepted as the parser representation for a future row matrix.
- Semicolon literals `[a,b;c,d]` are scanned before the restricted Python AST and stored as immutable parser bindings.
- Multiline matrix literals are consumed as one EngCalc statement while preserving the physical starting line.
- Top-level commas/semicolons inside matrix literals are distinguished from commas inside scalar function calls.
- Matrix cells continue through the existing restricted scalar validator, including Piecewise cells.
- Empty literals/rows, inconsistent row widths, nested matrix literals and unclosed literals have EngCalc-facing syntax diagnostics.
- `table(...,[...])` and plot/envelope sweep lists remain contextual collections, not matrix bindings.
- Task 1 is parser/model transport only; it deliberately does **not** yet construct SymPy matrices or perform matrix algebra.

## Open issues / user feedback

- Task 2 must turn parser matrix literals into `sympy.ImmutableMatrix`, add shape-aware algebra and implement one-based indexing without leaking raw SymPy exceptions.
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

### 0.9.0 Task 1 RED evidence

- New/migrated parser contracts were committed before Task 1 production code.
- RED workflow Actions **`33320679249`**, job **`99281977939`**: harness **success**, meaning pytest failed for the explicitly required missing-feature reasons.
- Exact RED result from artifact `9734793442` (`sha256:2f64721b6a7ebd24b17463d237cbac3ac6fbc8d7528dec56a107fe1a88f999f9`): **15 failed, 33 passed in 0.36 s**.
- Failures were the expected absence of general List support, semicolon/multiline matrix syntax, matrix-specific diagnostics and `matrix_literals` transport.
- The earlier malformed workflow `33320556349` created zero jobs and is explicitly not counted as TDD evidence.

### 0.9.0 Task 1 GREEN evidence

- GREEN workflow Actions **`33321037959`**, job **`99282936423`**, Python 3.13: **success**.
- Focused parser/list-context suite: **48/48 GREEN in 0.13 s**.
- Complete source suite: **569/569 GREEN in 114.64 s**.
- GREEN product commit: **`86ec35f3b5d20c517f794951e14fa7cd13af0121`**.
- Commit audit from workflow parent `a2876cec...` to product commit shows exactly three source files: new `matrix_syntax.py`, modified `models.py`, modified `parser.py`; no algebra/engine work was smuggled into Task 1.
- Temporary GREEN workflow removed in `95162527...` after validation.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–1 COMPLETE, TASK 2 NEXT**.
  - Base design/spec/clarification/implementation plan: approved.
  - Task 0 isolated baseline: COMPLETE.
  - Task 1 matrix literal parser: COMPLETE, 569/569 GREEN.
  - Task 2 immutable symbolic matrices, one-based indexing and matrix operators: NEXT.
  - Package/runtime version remains 0.8.0 until the release-closing task.
- Later roadmap: 0.9.1 exact-first extrema/roots/intersections → 0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization.

## Exact next step

1. Add Task 2 RED tests for immutable matrix construction/orientation, matrix/scalar operators, matrix multiplication shape contracts and one-based indexing/diagnostics.
2. Run the focused Task 2 suite and observe failures caused by missing matrix evaluation/indexing support.
3. Only after observed RED, create `matrix_core.py` and minimally modify parser/engine/models to construct immutable SymPy matrices and implement approved operators/indexing.
4. Run focused GREEN, then complete suite; commit production only after both pass.
5. Update this file with Task 2 RED/GREEN SHAs and counts before Task 3.
6. Do not invoke Codex and do not merge without explicit user authorization.

## How to resume in a new conversation

Read this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. 0.9.0 Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`. Task 0 baseline is complete. Task 1 parser/literal support is complete at product commit `86ec35f3b5d20c517f794951e14fa7cd13af0121`; its RED was 15 failed/33 passed and GREEN was 48/48 focused plus 569/569 full. Task 1 only transports matrix syntax; no SymPy matrix construction exists yet. The next action is Task 2 RED tests for actual immutable matrix values, shape-aware algebra and one-based indexing. Never invoke Codex and never merge without explicit user approval.
