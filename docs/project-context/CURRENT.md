# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.0 Matrix/CAS is fully integrated in `main`. PR #32 (`release: EngCalc 0.9.0 matrix CAS`) was merged after explicit user approval, and the resulting merge commit passed a fresh complete post-merge verification. The next release on the roadmap is 0.9.1 exact-first extrema/roots/intersections._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated release: **EngCalc 0.9.0 Matrix/CAS**.
- PR #32: **MERGED**.
- 0.9.0 merge commit: **`d22d5e0a62ce13800de8476c28d86a6d9415f1bd`** (`Merge pull request #32 ... release: EngCalc 0.9.0 matrix CAS`).
- Merge parents: previous `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d` and final release-branch head `7cbc6bc9150b16a1ead9861cf837f5aee0039c51`.
- Authoritative validated release commit before administrative cleanup: **`fb1be9e2e854f66f95414b9597dabceabaeb6470`** (`release: bump EngCalc to 0.9.0`).
- Runtime/package version integrated in `main`: **0.9.0**.
- Release branch `feature/v0.9.0-matrix-cas` is historical after merge; temporary pre/post-merge validation workflows were removed from it after evidence was captured.
- Formal design: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.0-matrix-cas-design.md`.
- Numeric-semantics clarification: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.0-matrix-cas-numeric-semantics-clarification.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.0-matrix-cas-implementation.md`.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.

## Approved behavior

### Existing behavior preserved

- `%%eng` remains a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Narrative, tables, plots, envelopes, multi-argument functions, Piecewise, numeric evaluation, precision/zero tolerance and presentation behavior remain regression requirements.
- Positive structural moment is plotted **downward**.
- Historical scalar `solve(eq, x)` remains supported.

### Integrated 0.9.0 Matrix/CAS contract

- Matrix literals use `[a, b, c]` for a row, `[a; b; c]` for a column and `[a, b; c, d]` for a general matrix. Commas separate columns and semicolons separate rows; multiline matrix literals are supported as presentation whitespace.
- Vectors are matrices; no mandatory public `vector()` / `row()` constructors were introduced.
- Symbolic matrices use immutable SymPy semantics. Matrix indexing is **1-based**; row/column vectors support one-index shorthand; slicing remains deferred.
- `A*B` is mathematical matrix multiplication; NumPy broadcasting or element-wise matrix semantics were not introduced.
- Core constructors/functions include `identity`, `zeros`, `diag`, `transpose`, `det`, `inv`, `trace`, `size`, `rank`, `rref`, `norm`, `eigenvals` and `eigenvects`.
- `simplify`, `expand`, `factor`, `subs`, `diff` and definite `integral` are matrix-aware entrywise where mathematically unambiguous. Scalar trig/log/exp functions reject whole-matrix inputs rather than inventing matrix-function semantics.
- Matrix-valued user functions preserve exact positional arity, simultaneous substitution and local-parameter shadowing.
- `solve(A,b)` is the exact linear-system API. Matrix systems require square `A`, matching column-vector RHS and a unique solution; exact symbolic algebra happens before numerical evaluation.
- `numeric(A)` evaluates matrices entry by entry through the existing unit-aware numeric context and returns an immutable `QuantityMatrix` boundary with Pint dimensionality preserved per entry.
- Heterogeneous engineering matrices are first-class; EngCalc never fabricates one fake matrix-wide unit. Exact zero may inherit a physical unit only when context makes that inheritance unambiguous.
- Matrix multiplication validates dimensional compatibility among terms contributing to each result cell while permitting different result cells to have different dimensions.
- Numerical `rank`, `rref`, `norm` and ordinary eigenanalysis require dimensionless or common-scale matrices; heterogeneous physical matrices are rejected rather than silently stripping units.
- Piecewise scalar expressions are supported inside matrix cells, including breakpoint and dimensional-zero behavior.
- Indexed scalar responses such as `K(x)[1,1]` work through the existing scalar `table`, `plot` and `envelope` APIs. Whole-matrix table/plot/envelope remains intentionally unsupported and is rejected with operation-specific scalar-response diagnostics.
- Symbolic, partial-numeric, homogeneous-numeric and heterogeneous-numeric matrices render through the existing source-order MathJax path; no parallel matrix display subsystem was introduced.
- The canonical structural worksheet supports numerical material data, multiline stiffness/load matrices, exact `solve(K,F)`, `numeric(K)` and `numeric(u)` in one `%%eng` flow.

### Deliberately deferred beyond 0.9.0

- Generalized structural eigenproblems `K phi = lambda M phi`.
- Sparse/global FEM matrices and block matrices.
- Slicing, least squares, pseudoinverse, SVD and NumPy-style broadcasting.
- Matrix-valued persistent `:=`.
- Mandatory LU/QR/Cholesky APIs.
- Whole-matrix `table`, `plot` and `envelope`.

## Open issues / user feedback

- `no_vertical_scroll()` remains outside Matrix/CAS scope.
- Multiline ordinary non-matrix function-call parsing remains a separate ergonomics item.
- Generalized structural eigenproblems need a future dedicated design/API.
- Auxiliary branch `noop` is non-product and contains no unique feature work.

## Validation evidence

### 0.9.0 implementation milestones

- Task 1 parser: `86ec35f3b5d20c517f794951e14fa7cd13af0121` — matrix literals.
- Task 2 symbolic core: `06bab76f06fc2a057ecdaab844eeb5717598fcd0` — immutable matrix algebra and 1-based indexing.
- Task 3 exact constructors/functions: `1b8ae5143d62dea1124411ef2e28bd61ef60db6e` — final full suite **627/627 GREEN**.
- Task 4 matrix-aware CAS/user functions: `501b6af2ef9eb228f7e69fb560479caa05f9dfb7` — final full suite **642/642 GREEN**.
- Task 5 Pint numerical matrices: `68f8a23` — final full suite **657/657 GREEN**.
- Task 6 exact matrix solve: `67b22d531955e8795e446afefc0ad0e698c9973d` — final full suite **665/665 GREEN**.
- Task 7 guarded matrix analysis: `29c8363804f6078371fb28f03dbb0dd3a7e80e18` — final full suite **684/684 GREEN**.
- Task 8 MathJax matrix rendering: `37c0cdb79b2ae4c0b2a039082a50260fda668700` — final full suite **700/700 GREEN**.
- Task 9 end-to-end Matrix/CAS integration: `6bd29dbb8fb417667f1fb1e264d9cbd146a2bbe0` — **29/29 focused**, **164/164 Matrix/CAS acceptance**, **721/721 complete GREEN**.

### 0.9.0 authoritative release gate

- Version-contract RED Actions **`33332122781`**, job **`99312355766`**: **8 failed / 15 passed**, exclusively the intentional pre-release 0.8.0 version/documentation state.
- RED artifact **`9737944074`**, digest `sha256:cadaa10ecdd683189e18418697586f9c46a20e2190654f58604c67a43b98b9fd`.
- Release GREEN Actions **`33332233490`**, job **`99312713507`**, Python 3.13.
- Release contract: **23/23 GREEN**.
- Complete source suite before wheel: **721/721 GREEN in 142.99 s**.
- Wheel: **`engcalc_colab-0.9.0-py3-none-any.whl`**; metadata **Version 0.9.0**.
- Wheel SHA-256: **`ea66fa231b5657695e2c38cefb324da220070a2f7c86557dddef19d2017a0719`**.
- External clean-environment/site-packages smoke: **PASS**.
- Complete installed-wheel/source-free suite: **721/721 GREEN in 141.38 s** with imports proven to come from `site-packages` and `src/` excluded.
- Final repository source revalidation: **721/721 GREEN in 139.76 s**.
- Authoritative validated release commit: **`fb1be9e2e854f66f95414b9597dabceabaeb6470`**.
- Release artifact **`9738071240`**, digest `sha256:7f8971526a78de96fe7cf175ca133e4f664cfe67036028d705835e97070c12f1`.
- Post-validation product audit found no changes to `src/`, tests, README or package metadata after the authoritative release tree; subsequent differences before merge were validation-harness cleanup plus project-context documentation only.

### Final pre-merge and post-merge gates

- Fresh final pre-merge Actions **`33333349074`**, job **`99315783415`**, tested branch commit `49ea6c96d91d9dbaacb91ab240b0676664dd2c31`: installation, `compileall`, `git diff --check` and complete `pytest -q` all **success**.
- The sole commit after that tested tree and before merge removed `.github/workflows/v090-final-premerge.yml`; no product/test/documentation semantics changed.
- User explicitly approved the merge.
- PR #32 merged with expected head guard `7cbc6bc9150b16a1ead9861cf837f5aee0039c51`; GitHub returned merge commit **`d22d5e0a62ce13800de8476c28d86a6d9415f1bd`**.
- Post-merge Actions **`33333566096`**, job **`99316363602`** checked out **exactly `d22d5e0a62ce13800de8476c28d86a6d9415f1bd`**, asserted that SHA, then ran installation, `compileall`, `git diff --check` and complete `pytest -q`: **success**.
- The post-merge validation workflow was hosted temporarily on the historical feature branch and removed afterward; it never modified `main`.
- No Codex review or Codex Cloud was invoked during release or merge closure.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **COMPLETE + RELEASE-VALIDATED + MERGED**.
- **0.9.1 exact-first extrema / roots / intersections:** NEXT DESIGN/IMPLEMENTATION RELEASE.
- Later roadmap: **0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Treat `main` with EngCalc 0.9.0 as the new canonical baseline.
2. Before implementing 0.9.1, design/spec exact-first extrema, roots and intersections and define their interaction with units, Piecewise, matrices/indexed scalar responses, tables/plots/envelopes and engineering diagnostics.
3. Start 0.9.1 from the current integrated `main` only after the design/spec is approved.
4. Continue RED → GREEN TDD, focused tests before full suite, and the same real-wheel/source-free release discipline.
5. Do not invoke Codex unless explicitly authorized by the user.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.0 Matrix/CAS is fully integrated and validated in `main`. PR #32 was merged with merge commit `d22d5e0a62ce13800de8476c28d86a6d9415f1bd`; a complete post-merge gate against that exact SHA succeeded. The 0.9.0 authoritative wheel/release evidence remains attached to Actions `33332233490` / artifact `9738071240`. The next roadmap item is 0.9.1 exact-first extrema/roots/intersections; begin with design/spec from the integrated `main`, and never invoke Codex without explicit authorization.
