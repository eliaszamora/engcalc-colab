# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 Piecewise remains fully integrated in `main`. The 0.9.0 Matrix/CAS implementation plan has been explicitly approved for inline execution. `feature/v0.9.0-matrix-cas` was created from exact `main@9b90014f...`, seeded only with the approved planning documents, and passed the fresh Task 0 baseline gate on Python 3.13. Production Matrix/CAS code has not started yet; Task 1 parser RED is the active next step._

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
- Planning design commit: `650d35b7992b780dae9e9795271a94c3083b9068`.
- Numeric-semantics clarification commit: `dc3acd4b593e35bb11578f2a3ae54d252e846beb`.
- Initial implementation-plan commit: `0013ccd8ef04a1efe31329613fbdc9f72efaa4e8`.
- Plan self-review correction: `2e722ee7c64ab0eeb72f7614db05af42622e7576`.
- Task 0 temporary baseline workflow commit: `965b8b716578d0414e3819cd1239b3219404daae`; workflow removed in `9dd2b1248decb9423134754d391bac8da843738c`.
- No Matrix/CAS `src/` file or product test has been modified yet.
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

## Open issues / user feedback

- Task 1 must deliberately migrate the three historical parser tests that rejected `A = [1,2]`; in 0.9.0 this becomes a valid row vector while table/plot/envelope list contexts remain collections.
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

### 0.9.0 design/planning evidence

- Planning branch was created from exact integrated `main@9b90014f...`.
- Base architecture and syntax were explicitly approved before the written spec.
- Written design + numeric clarification were explicitly approved.
- Implementation plan was explicitly approved for inline execution on 2026-08-30.
- Plan self-review found and corrected the historical `[1,2]` test-contract conflict.
- Self-review correction workflow Actions `33319867712`, job `99279839857`: **success**; temporary workflow removed.

### 0.9.0 Task 0 execution evidence

- `feature/v0.9.0-matrix-cas` created from exact current `main@9b90014f...`.
- Feature seed commit `74d045f0...` contains only the approved design/spec/plan/context documents relative to main.
- Fresh baseline workflow Actions **`33320306377`**, job **`99280984551`**, Python **3.13**: **success**.
- Runtime check inside the baseline workflow confirmed **0.8.0**.
- Complete source suite step completed successfully. Because the product/test tree is identical to the authoritative 0.8.0 baseline apart from planning docs and the temporary workflow, this is the same 557-test baseline with zero failures.
- Temporary baseline workflow removed in `9dd2b124...` before Task 1.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASK 0 COMPLETE, TASK 1 NEXT**.
  - Base design: approved.
  - Formal written spec: approved.
  - Numeric clarification: approved.
  - Implementation plan: approved.
  - Implementation branch: created and baseline-validated.
  - Task 0 isolated baseline: complete.
  - Task 1 parser/literal TDD: not started; next action is RED tests.
  - Package/runtime version remains 0.8.0 until the release-closing task.
- Later roadmap: 0.9.1 exact-first extrema/roots/intersections → 0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization.

## Exact next step

1. On `feature/v0.9.0-matrix-cas`, add Task 1 RED tests for row/column/general literals, multiline continuation, diagnostics, and contextual-list preservation.
2. Deliberately migrate the three old `[1,2]` rejection tests to the approved row-vector contract.
3. Run focused parser tests and confirm the expected RED for missing matrix syntax/multiline support.
4. Only after observed RED, implement `matrix_syntax.py` plus the minimal `models.py`/`parser.py` changes.
5. Run focused GREEN, parser regressions, then complete suite.
6. Update this file with RED/GREEN SHAs and counts before advancing to Task 2.
7. Do not invoke Codex and do not merge without explicit user authorization.

## How to resume in a new conversation

Read this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`, runtime 0.8.0, authoritative baseline 557/557 GREEN. 0.9.0 Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`, created from that exact main SHA and seeded only with approved planning artifacts. Task 0 baseline workflow `33320306377` / job `99280984551` passed on Python 3.13 and its temporary workflow was removed. No Matrix/CAS production code/tests have been committed yet. The next action is Task 1 RED parser tests for `[a,b]`, `[a;b]`, `[a,b;c,d]`, multiline matrix literals and list-context preservation, followed by minimal parser implementation only after the RED is observed. Never invoke Codex and never merge without explicit user approval.
