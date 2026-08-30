# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 Piecewise is fully integrated in `main`. The 0.9.0 vectors/matrices/linear-systems milestone is now in formal design review on `planning/v0.9.0-matrix-cas`. The user approved the base architecture and syntax decisions; the written spec and its numeric-semantics clarification are committed and awaiting explicit written-spec approval before an implementation plan is created. No Matrix/CAS production code has started._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated branch: **`main`** at **`9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`**.
- Runtime/package version on `main`: **0.8.0**.
- Piecewise PR #31: **MERGED** at merge commit `eca248c376128da16ff9526751790aebe2089646`.
- Current planning branch: **`planning/v0.9.0-matrix-cas`**, created exactly from `main@9b90014f...`.
- 0.9.0 formal design spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.0-matrix-cas-design.md`.
- Normative numeric-semantics clarification: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.0-matrix-cas-numeric-semantics-clarification.md`.
- Main design commit: `650d35b7992b780dae9e9795271a94c3083b9068`.
- Numeric-semantics clarification commit: `dc3acd4b593e35bb11578f2a3ae54d252e846beb`.
- No Matrix/CAS source or product-test files have been modified.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge planning or implementation work to `main` without explicit user approval.

## Approved behavior

### Existing integrated behavior

- EngCalc 0.8.0 Piecewise remains closed and integrated.
- `%%eng` remains a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Narrative, tables, plots, envelopes, multi-argument functions, Piecewise, numeric evaluation, presentation polish and positive-moment-downward convention remain regression requirements.

### Approved 0.9.0 base design decisions

- Matrix syntax is mathematical/MATLAB-inspired and intentionally need not be valid Python.
- Canonical literals:
  - row vector: `[a, b, c]` -> `1 x n` matrix;
  - column vector: `[a; b; c]` -> `n x 1` matrix;
  - matrix: `[a, b; c, d]`.
- Commas separate columns; semicolons separate rows.
- Physical newlines inside an open matrix literal are presentation whitespace only.
- Vectors are matrices; there are no mandatory `vector()` / `row()` constructors.
- Matrix indexing is **1-based**.
- Symbolic matrices use immutable SymPy matrix semantics.
- `A*B` is matrix multiplication, not element-wise multiplication.
- `identity(n)`, `zeros(m,n)` and `diag(...)` are the initial special constructors.
- `transpose`, `det`, `inv`, `trace`, `rank`, `rref`, `norm`, `size`, `eigenvals`, `eigenvects` form the intended core matrix function family.
- Existing scalar CAS transforms such as `simplify`, `expand`, `factor`, `subs`, `diff`, and definite `integral` become matrix-aware where mathematically unambiguous.
- Matrix-valued user functions are supported.
- `solve(A,b)` is the canonical linear-system API while scalar `solve(eq,x)` remains unchanged.
- Exact symbolic solving precedes dimensional numerical evaluation.
- `numeric(A)` is the canonical numerical matrix evaluation path.
- Numerical matrix results preserve **per-entry Pint dimensionality**; a heterogeneous engineering matrix is first-class and must not be flattened to one fake unit.
- `QuantityMatrix` is a final numerical result boundary, not a second public matrix algebra language.
- Public matrix expressions remain symbolic-first; Pint validates resulting scalar cells when `numeric(...)` is requested.
- `rank`, `rref`, `norm`, and numerical eigenanalysis require a dimensionless or common-scale numerical matrix; heterogeneous dimensional matrices must be rejected for those numerical algorithms.
- Existing `table(...,[...])` point lists and plot/envelope sweep lists retain their contextual collection semantics and must not be reinterpreted as row vectors.
- Matrix-valued persistent `:=` assignment, generalized eigenproblems, sparse/FEM workflows, NumPy-style broadcasting and element-wise array operators are deferred.

## Open issues / user feedback

- Written 0.9.0 spec is awaiting explicit user review/approval.
- Detailed implementation dataclass boundaries for eigen/decomposition results must be chosen in the implementation plan, not ad hoc during coding.
- Optional LU/QR/Cholesky are lower priority than core matrix semantics and may move to a later 0.9.x if they threaten the core milestone.
- Multiline ordinary non-matrix function-call parsing remains a separate ergonomics item.
- `no_vertical_scroll()` remains outside Matrix/CAS.
- Auxiliary branch `noop` remains non-product and has no unique feature work.

## Validation evidence

### 0.8.0 integrated baseline

- Authoritative distribution gate: Actions `33316141809`, Python 3.13.15.
- Source before wheel: **557/557 GREEN**.
- Installed-wheel/source-free suite: **557/557 GREEN**.
- Source recheck: **557/557 GREEN**.
- Fresh final pre-merge gate: Actions `33316786989`, **557/557 GREEN in 116.63 s**.
- Post-merge compare `df11f1ec...` -> `eca248c3...`: **zero changed files**.

### 0.9.0 design evidence

- Planning branch created from exact current integrated baseline `main@9b90014f...`.
- Base architecture and syntax were explicitly approved by the user before the spec was written.
- Formal spec committed at `650d35b7...`.
- Design self-review found and resolved two dimensional-semantics ambiguities in normative clarification `dc3acd4b...`:
  1. `QuantityMatrix` is output-only/private numerical infrastructure rather than a parallel public CAS;
  2. numerical `rank`/`rref`/`norm`/eigen operations require dimensionless or common-scale matrices and must reject arbitrary heterogeneous physical matrices.
- No production validation is applicable yet because no product code has changed.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **DESIGN SPEC WRITTEN; USER SPEC-REVIEW GATE ACTIVE**.
  - Base design: approved.
  - Formal spec: written.
  - Numeric clarification: written.
  - Implementation plan: not started; blocked on written-spec approval.
  - Production code: not started.
- Later roadmap: 0.9.1 exact-first extrema/roots/intersections -> 0.9.2 exact envelopes/governing intervals -> 0.9.3 named response cases/combinations -> 0.10.x engineering verification -> 1.0.0 stabilization.

## Exact next step

1. Present the committed 0.9.0 matrix/CAS spec and normative numeric clarification to the user for review.
2. Do **not** write or execute a production implementation plan until the user explicitly approves the written spec.
3. After written-spec approval, invoke the planning workflow and create a RED->GREEN implementation plan from current `main`.
4. Only after that plan is approved may a dedicated implementation feature branch be created and production TDD begin.

## How to resume in a new conversation

Read this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. The active work is planning-only on `planning/v0.9.0-matrix-cas`. The user approved the matrix/CAS base design: `%%eng` remains a DSL; literals use `[a,b; c,d]`; vectors are row/column matrices; indexing is 1-based; SymPy is symbolic truth; Pint is numerical/unit truth per entry; `solve(A,b)` is the linear-system API; `QuantityMatrix` is an output boundary rather than a public parallel algebra. Read both `2026-08-30-engcalc-v0.9.0-matrix-cas-design.md` and `2026-08-30-engcalc-v0.9.0-matrix-cas-numeric-semantics-clarification.md`. The next action is the user's written-spec review gate. Do not start production code or an implementation plan before explicit approval.