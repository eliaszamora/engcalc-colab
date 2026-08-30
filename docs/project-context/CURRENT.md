# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.0 Matrix/CAS is implementation-complete and release-validated on `feature/v0.9.0-matrix-cas`. Release PR #32 (`release: EngCalc 0.9.0 matrix CAS`) is OPEN against `main`. No merge has been performed; explicit user approval is required before merging._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated branch: **`main`** at **`9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`**.
- Runtime/package version on `main`: **0.8.0**.
- Previous Piecewise release: PR #31 merged; merge commit `eca248c376128da16ff9526751790aebe2089646`.
- Release branch: **`feature/v0.9.0-matrix-cas`**, created from exact `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`.
- Runtime/package version on the release branch: **0.9.0**.
- Authoritative validated release commit: **`fb1be9e2e854f66f95414b9597dabceabaeb6470`** (`release: bump EngCalc to 0.9.0`).
- Post-release cleanup removed only temporary Task 10 validation files; cleanup commits include `8aa053e9f62835d3fc72595aced81d16d85385f0`, `1250c361b15795fd861d08f8295b8912ac99d327` and `a3b3c2a959fa3c8a61dbb3501079df787c87064e`.
- A fresh temporary pre-PR gate was added at `14fceb577e70ff62942e7ad1ec12dda0c266c1f3`, passed, and was removed at `69add5390273eb9ef87015e703a275c0a5ad6911`.
- Release PR: **#32**, title **`release: EngCalc 0.9.0 matrix CAS`**, head `feature/v0.9.0-matrix-cas` → base `main`, state **OPEN**, not merged.
- Formal design: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.0-matrix-cas-design.md`.
- Numeric-semantics clarification: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.0-matrix-cas-numeric-semantics-clarification.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.0-matrix-cas-implementation.md`.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge implementation work to `main` without explicit user approval.

## Approved behavior

### Existing integrated behavior preserved

- `%%eng` remains a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Narrative, tables, plots, envelopes, multi-argument functions, Piecewise, numeric evaluation, precision/zero tolerance and presentation behavior remain regression requirements.
- Positive structural moment is plotted **downward**.
- Historical scalar `solve(eq, x)` remains supported.

### 0.9.0 Matrix/CAS release contract

- Matrix literals use `[a, b, c]` for a row, `[a; b; c]` for a column and `[a, b; c, d]` for a general matrix. Commas separate columns and semicolons separate rows; multiline matrix literals are supported as presentation whitespace.
- Vectors are matrices; no mandatory public `vector()` / `row()` constructors were introduced.
- Symbolic matrices use immutable SymPy matrix semantics. Matrix indexing is **1-based**; row/column vectors support one-index shorthand; slicing remains deferred.
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

- **Release PR #32 is open and awaiting explicit user approval before any merge.**
- `no_vertical_scroll()` remains outside Matrix/CAS scope.
- Multiline ordinary non-matrix function-call parsing remains a separate ergonomics item.
- Generalized structural eigenproblems need a future dedicated design/API.
- Auxiliary branch `noop` is non-product and contains no unique feature work.

## Validation evidence

### 0.8.0 integrated baseline

- `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`, package/runtime 0.8.0.
- Previous authoritative 0.8.0 distribution gate: source **557/557 GREEN**, installed-wheel/source-free **557/557 GREEN**, source recheck **557/557 GREEN**.

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

### 0.9.0 Task 10 authoritative release evidence

- Version-contract RED Actions **`33332122781`**, job **`99312355766`**: **8 failed / 15 passed**. All failures were exclusively the intentional pre-release 0.8.0 runtime/package/documentation state.
- RED artifact **`9737944074`** (`task10-version-red-log`), digest `sha256:cadaa10ecdd683189e18418697586f9c46a20e2190654f58604c67a43b98b9fd`.
- Release GREEN Actions **`33332233490`**, job **`99312713507`**, Python 3.13: all release steps completed successfully.
- Release contract: **23/23 GREEN**.
- Complete source suite before wheel: **721/721 GREEN in 142.99 s**.
- Built wheel: **`engcalc_colab-0.9.0-py3-none-any.whl`**.
- Wheel metadata: **Version 0.9.0**.
- Wheel SHA-256: **`ea66fa231b5657695e2c38cefb324da220070a2f7c86557dddef19d2017a0719`**.
- External clean-environment/site-packages smoke: **PASS**. It explicitly verified row/column matrices, exact inverse, 1-based indexing, matrix-valued functions, exact `solve(K,F)`, displacement units, heterogeneous stiffness terms, Piecewise matrix cells and positive structural moment downward.
- Complete installed-wheel/source-free suite: **721/721 GREEN in 141.38 s** with imports proven to come from `site-packages` and `src/` excluded.
- Final repository source revalidation: **721/721 GREEN in 139.76 s**.
- Authoritative validated release commit: **`fb1be9e2e854f66f95414b9597dabceabaeb6470`**.
- Release artifact **`9738071240`** (`engcalc-0.9.0-release-validation`), digest `sha256:7f8971526a78de96fe7cf175ca133e4f664cfe67036028d705835e97070c12f1`.
- Post-validation compare from `fb1be9e2...` through the Task 10 cleanup shows only deletion of `.github/scripts/v090_task10_apply.py`, `.github/workflows/v090-task10-red.yml` and `.github/workflows/v090-task10-release-green.yml`; there are no post-validation changes to `src/`, tests, README or package metadata.
- Fresh pre-PR gate Actions **`33333014138`**, job **`99314884793`**, tested commit `14fceb577e70ff62942e7ad1ec12dda0c266c1f3`: `compileall`, `git diff --check` and complete `pytest -q` all completed successfully. The temporary gate workflow was then removed in `69add5390273eb9ef87015e703a275c0a5ad6911`.
- Net compare from authoritative release commit `fb1be9e2...` after pre-PR gate cleanup still contains only the three Task 10 temporary validation-file deletions.
- Release PR **#32** opened against exact `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. No merge has been performed.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION + RELEASE VALIDATION COMPLETE; PR #32 OPEN; MERGE AWAITS EXPLICIT USER APPROVAL**.
- Later roadmap: **0.9.1 exact-first extrema/roots/intersections → 0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Keep PR #32 open and review its evidence/status.
2. **Do not merge** until the user gives explicit approval in the conversation.
3. If approval is given, first re-fetch `main`, the PR head, CI/check state and mergeability to ensure nothing moved or regressed.
4. Merge only after that fresh pre-merge verification, then verify the resulting `main` state and update this context with the merge commit and post-merge evidence.
5. Do not invoke Codex unless the user explicitly authorizes it.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.0 Matrix/CAS is fully implemented and authoritatively release-validated on `feature/v0.9.0-matrix-cas`; the validated release commit is `fb1be9e2e854f66f95414b9597dabceabaeb6470`. PR #32 (`release: EngCalc 0.9.0 matrix CAS`) is OPEN against `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. Task 10 has real-wheel, clean-environment smoke, source-free installed-wheel and repeated source-suite evidence. Temporary validation workflows have been removed. The only next integration action is to wait for explicit user approval; never merge or invoke Codex without that authorization.
