# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 Piecewise remains fully integrated in `main`. The user has approved the written 0.9.0 vectors/matrices/linear-systems design and numeric-semantics clarification. A complete RED→GREEN implementation plan is now written and self-reviewed on `planning/v0.9.0-matrix-cas`; no Matrix/CAS production code has started. The next gate is explicit approval of the implementation plan before creating `feature/v0.9.0-matrix-cas`._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated branch: **`main`** at **`9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`**.
- Runtime/package version on `main`: **0.8.0**.
- Piecewise PR #31: **MERGED**, merge commit `eca248c376128da16ff9526751790aebe2089646`.
- Current planning branch: **`planning/v0.9.0-matrix-cas`**, created from `main@9b90014f...`.
- Formal 0.9.0 design: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.0-matrix-cas-design.md`.
- Normative numeric clarification: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.0-matrix-cas-numeric-semantics-clarification.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.0-matrix-cas-implementation.md`.
- Design commit: `650d35b7992b780dae9e9795271a94c3083b9068`.
- Numeric-semantics clarification commit: `dc3acd4b593e35bb11578f2a3ae54d252e846beb`.
- Initial implementation-plan commit: `0013ccd8ef04a1efe31329613fbdc9f72efaa4e8`.
- Plan self-review correction: `2e722ee7c64ab0eeb72f7614db05af42622e7576`.
- Temporary self-review workflow removed in `5e7e2690ee53eb87d839e59fecee0ef23e5e5161`.
- No Matrix/CAS `src/` file or product test has been modified.
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

- The complete implementation plan is written and awaits explicit user approval before execution.
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
- Written design + numeric clarification were subsequently explicitly approved by the user's instruction to proceed to the implementation-planning step.
- Formal spec: `650d35b7...`.
- Numeric clarification: `dc3acd4b...`.
- Implementation plan: `0013ccd8...`, covering Tasks 0–10 from isolated baseline through wheel validation and PR gate.
- Required plan self-review found one real historical-contract conflict: three 0.8.0 parser tests explicitly rejected `[1,2]`. The corrected plan at `2e722ee7...` now requires those tests to migrate deliberately to the approved row-vector semantics while preserving table/sweep collection behavior and dictionary/comprehension/nested-list/unpacking restrictions.
- Self-review correction workflow Actions `33319867712`, job `99279839857`: **success**. The temporary workflow was then removed.
- No product/source validation is applicable yet because no Matrix/CAS production code has changed.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **SPEC APPROVED; IMPLEMENTATION PLAN WRITTEN + SELF-REVIEWED; PLAN-APPROVAL GATE ACTIVE**.
  - Base design: approved.
  - Formal written spec: approved.
  - Numeric clarification: approved.
  - Implementation plan: written and self-reviewed.
  - Production branch: not created.
  - Production code: not started.
- Later roadmap: 0.9.1 exact-first extrema/roots/intersections → 0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization.

## Exact next step

1. Present the completed implementation plan to the user for explicit approval.
2. After approval, re-read this context plus both specs and the plan, then verify the current `main` SHA.
3. Create `feature/v0.9.0-matrix-cas` from the exact current `main`; copy only the approved planning artifacts if needed.
4. Execute Task 0: fresh full baseline and runtime-version check.
5. Start Task 1 with parser tests RED before modifying production code.
6. Continue RED→GREEN task-by-task, focused tests then full suite, updating `CURRENT.md` at every state change.
7. Do not invoke Codex and do not merge without explicit user authorization.

## How to resume in a new conversation

Read this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`, runtime 0.8.0, baseline 557/557 GREEN. Active work is planning-only on `planning/v0.9.0-matrix-cas`. The user approved the 0.9.0 design/spec: MATLAB-style `[a,b; c,d]`, vectors as matrices, one-based indexing, immutable SymPy symbolic truth, per-entry Pint numerical truth, exact `solve(A,b)`, `QuantityMatrix` as output boundary, and contextual table/sweep lists preserved. The complete implementation plan is `docs/superpowers/plans/2026-08-30-engcalc-v0.9.0-matrix-cas-implementation.md`, initially committed at `0013ccd8...` and corrected after self-review at `2e722ee7...`. No Matrix/CAS production code exists yet. The next gate is explicit user approval of the implementation plan; only then create `feature/v0.9.0-matrix-cas` and execute Task 0/Task 1 TDD.