# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–5 are complete with strict RED→GREEN evidence. Pint-backed numerical matrices now preserve per-entry dimensionality, homogeneous target-unit conversion, exact-zero adaptability and partial matrix evaluation. Task 6 — exact `solve(A,b)` plus dimensional structural solve acceptance — is the exact next step. Package/runtime version remains 0.8.0._

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
- Task 4 RED test commits: **`6ce1cdf4e9d7c140747308240a3efd3fc733438b`** and **`02b7369ad6403c560555a72223feca79e72313a7`**.
- Task 4 GREEN product commit: **`501b6af2ef9eb228f7e69fb560479caa05f9dfb7`** (`feat: support matrix-valued CAS functions`).
- Task 4 temporary RED workflow removed in `a3d5b311e42de417b091784a3688799249f92903`; final GREEN workflow removed in `ca85d897e0983c6746a2e8c0d435062b0d35f220`; implementation harness removed in `bd28e033bdf3a1ba6dbcc628886db1950d3dff6e`.
- Task 5 RED test commits: **`fb0339b59fe42e14f1a4e6914a290cd1d596df06`** and **`b6c424273e922bd3434eb0108df9f55b5e9acb62`**.
- Task 5 RED workflow commit: **`7a595e9a0a3c2367b70e1ee169513d48ded749b2`**; RED workflow removed in **`dbb3e6f751426c76c7a15441370a96de0a3b9dff`**.
- Task 5 GREEN product commit: **`68f8a23`** (`feat: evaluate matrices with Pint units`).
- Task 5 final GREEN workflow removed in **`c104a6a29a7e533eee01d4261a88f551dfa2715d`**; implementation harness removed in **`d17c28fd87ae58567c75b92116389de2e713b431`**.
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

### Implemented 0.9.0 behavior through Task 5

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
- Matrix-valued user functions preserve exact positional arity, simultaneous substitution, local-parameter shadowing and inverse-trig node semantics.
- `simplify`, `expand`, `factor`, `subs`, `diff` and definite `integral` explicitly map entrywise over immutable matrices.
- Matrix Piecewise differentiation remains entrywise and stores the union of explicit breakpoint metadata for later numeric evaluation.
- Scalar symbolic functions such as `sin`, `cos`, `tan`, inverse trig, `sqrt`, `exp` and `log` reject whole-matrix arguments instead of silently introducing unintended matrix-function semantics.
- `map_matrix_entries(...)` is the single immutable entrywise CAS mapping primitive; `substitute_symbolic_value(...)` centralizes scalar/matrix function substitution while preserving existing scalar behavior.
- `QuantityMatrix` is now the immutable Pint-valued numerical output boundary; it deliberately exposes no public matrix arithmetic parallel to SymPy.
- `numeric(A)` evaluates immutable symbolic matrices cell by cell through the existing `NumericContext`, preserving Pint dimensionality per entry.
- Homogeneous numerical matrices accept a single compatible target unit through `numeric(A, unit)`; heterogeneous matrices reject a single incompatible matrix-wide target unit with a coordinate-aware diagnostic.
- Exact symbolic zeros are tracked as adaptable zero cells and inherit a target unit only when the requested homogeneous conversion makes that inheritance unambiguous.
- Matrix numeric failures identify the one-based failing coordinate, e.g. `[2,1]`, while `QuantityMatrix.entry(row,col)` remains internal zero-based storage.
- Partial numerical matrices return `PartialMatrixNumericEvaluationResult` with deterministic unresolved-symbol ordering and known Pint substitutions; target-unit conversion remains blocked until fully numeric.
- Matrix-valued user functions use the existing argument-binding/shadowing rules during `numeric(...)`; `result(A)` follows the same full/partial matrix evaluation route.

## Open issues / user feedback

- Task 6 must add exact `solve(A,b)` for square linear systems while preserving existing scalar `solve(eq,x)` behavior and translating shape/singularity failures to EngCalc diagnostics.
- Matrix rendering/presentation has not yet been implemented; current work establishes symbolic and numeric truth before final presentation.
- Exact matrix linear systems and dimensional structural solve acceptance are now the active next task in the approved 0.9.0 plan.
- `rank`, `rref`, `norm`, `eigenvals` and `eigenvects` remain later exact/common-scale guarded tasks after `solve(A,b)`.
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

### 0.9.0 Task 4 RED/GREEN evidence

- Task 4 user-function tests were committed at **`6ce1cdf4e9d7c140747308240a3efd3fc733438b`** and matrix-calculus tests at **`02b7369ad6403c560555a72223feca79e72313a7`**, before Task 4 production code.
- RED Actions **`33324597889`**, job **`99292391302`**, CPython **3.13.15**: **2 failed, 13 passed in 3.64 s**.
- RED established two genuine missing contracts: `factor(A)` was not entrywise and scalar `sin(A)` was incorrectly accepted. The other 13 approved behaviors already happened to work through SymPy and were retained rather than artificially broken.
- RED artifact **`9735856775`**, digest **`sha256:33dbf248cab35c24c2051e77943d1e413fa8ca00f17bcada5772fe984f60d871`**.
- Final GREEN Actions **`33324742050`**, job **`99292774054`**, CPython **3.13.15**: compile check + `git diff --check` GREEN; **15/15 focused GREEN in 3.35 s**; **642/642 full GREEN in 126.22 s**.
- Product commit **`501b6af2ef9eb228f7e69fb560479caa05f9dfb7`** changed exactly `src/engcalc_colab/engine.py` and `src/engcalc_colab/matrix_core.py`: 70 additions, 10 deletions; no unrelated product files changed.
- GREEN logs artifact **`9735923490`**, digest **`sha256:d4afefbff29b0344d3f2fe1529bbd9c3450d3640a7ec8b3701c89e7ed3b19da9`**.
- Temporary Task 4 RED/GREEN workflows and implementation harness were removed after evidence was preserved.
- The only runner warning was GitHub Actions' Node 20 deprecation/forced Node 24 compatibility warning; it is not an EngCalc product failure.

### 0.9.0 Task 5 RED/GREEN evidence

- Task 5 numerical-matrix tests were committed before production code at **`fb0339b59fe42e14f1a4e6914a290cd1d596df06`** and **`b6c424273e922bd3434eb0108df9f55b5e9acb62`**.
- RED Actions **`33325205662`**, job **`99293997738`**, CPython **3.13.15**: **15 failed in 3.58 s**, with no collection errors. Full numeric cases failed because `numeric(...)` rejected `ImmutableDenseMatrix`; partial cases still entered the scalar missing-value path, exactly establishing the missing Task 5 boundary.
- RED artifact **`9736021588`**, digest **`sha256:c7cf07b50c8d8398e4fdf943375a0ee1bbc7dbad5646b27af9b32c420b4f466d`**.
- Final GREEN Actions **`33325415322`**, job **`99294564132`**, CPython **3.13.15**: compile check + `git diff --check` GREEN; **27/27 focused GREEN in 5.52 s**; **657/657 full GREEN in 129.46 s**.
- Product commit **`68f8a23`** (`feat: evaluate matrices with Pint units`) changed exactly four production files: `src/engcalc_colab/engine.py`, new `src/engcalc_colab/matrix_numeric.py`, `src/engcalc_colab/models.py`, and `src/engcalc_colab/numeric.py`; audit from `c4aee7b...` shows 301 additions and 23 deletions with no unrelated product files.
- GREEN logs artifact **`9736111856`**, digest **`sha256:660b95eaadf0f5d74ab54b7a9b6ced43858f69b7cde377f297348bb7ca914a49`**.
- Temporary Task 5 RED/GREEN workflows and implementation harness were removed after evidence was preserved.
- The only runner warning was GitHub Actions' Node 20 deprecation/forced Node 24 compatibility warning; it is not an EngCalc product failure.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–5 COMPLETE, TASK 6 NEXT**.
  - Base design/spec/clarification/implementation plan: approved.
  - Task 0 isolated baseline: COMPLETE.
  - Task 1 matrix literal parser: COMPLETE, 569/569 GREEN.
  - Task 2 immutable symbolic matrices, matrix operators and one-based indexing: COMPLETE, 596/596 GREEN.
  - Task 3 constructors and core exact matrix functions: COMPLETE, 31/31 focused + 627/627 full GREEN.
  - Task 4 matrix-valued user functions and matrix-aware existing CAS transforms: COMPLETE, 15/15 focused + 642/642 full GREEN.
  - Task 5 Pint-backed numerical matrices and partial numeric matrices: COMPLETE, 27/27 focused + 657/657 full GREEN.
  - Task 6 exact `solve(A,b)` and dimensional structural solve acceptance: NEXT.
  - Package/runtime version remains 0.8.0 until the release-closing task.
- Later roadmap: 0.9.1 exact-first extrema/roots/intersections → 0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization.

## Exact next step

1. Add Task 6 RED tests in `tests/test_matrix_solve.py` for exact `solve(A,b)` using the two-DOF stiffness system from the approved plan.
2. Verify `K*u-F` simplifies to the exact zero matrix and preserve existing scalar `solve(eq,x)` behavior.
3. Add explicit EngCalc diagnostics for nonsquare `A`, row-vector RHS, wrong RHS length and singular/non-unique systems.
4. Add dimensional acceptance: with `k1 := 20*kN/mm`, `k2 := 15*kN/mm`, `P := 30*kN`, `numeric(u)` must return a `2 x 1` `QuantityMatrix` whose entries have length dimensionality.
5. Add a mixed translational/rotational DOF case whose symbolic stiffness multiplication evaluates numerically to heterogeneous force/moment result cells without imposing one matrix-wide unit.
6. Run the new Task 6 tests RED before production.
7. Implement `matrix_solve.py` and overload `solve` by evaluated first-argument type; keep the scalar `solve(eq,x)` route unchanged where possible.
8. Run focused GREEN (`test_matrix_solve` + scalar solve regression) and then the complete suite; persist production only after both pass.
9. Update this file with Task 6 RED/GREEN SHAs and counts before Task 7 matrix analysis.
10. Do not invoke Codex and do not merge without explicit user authorization.

## How to resume in a new conversation

Read this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`. Tasks 0–5 are complete. Task 5 product commit `68f8a23` implements Pint-backed `QuantityMatrix`, per-entry dimensionality, homogeneous target-unit conversion, exact-zero adaptability, coordinate diagnostics, partial numerical matrices and `result(A)` parity; final verification was 27/27 focused plus 657/657 complete. The exact next action is Task 6 RED for exact `solve(A,b)`, shape/singularity diagnostics and dimensional structural solve acceptance. Never invoke Codex and never merge without explicit user approval.
