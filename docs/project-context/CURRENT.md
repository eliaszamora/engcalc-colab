# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–9 are complete with strict RED→GREEN evidence. Matrix Piecewise cells, indexed scalar table/plot/envelope integration, engineering diagnostics and the canonical structural worksheet are now accepted end to end. Task 10 — release/version/wheel validation for 0.9.0 — is the exact next step. Package/runtime version remains 0.8.0 until that release-closing task._

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
- Task 6 accepted clean RED test head: **`ac7c1f354f6e0b559f8e602471e9953f8779da06`**.
- Task 6 GREEN product commit: **`67b22d531955e8795e446afefc0ad0e698c9973d`** (`feat: solve exact linear matrix systems`).
- Task 6 temporary RED workflows removed in **`2ba11fa2cee0adb38a7bf26b9f537858d48627c8`** and **`937914a807e02e4cd7c69816c7c026513ce95c9a`**; RED correction harness removed in **`3b8805ea9bd29dca39c564b537b0017072ed7a3b`**.
- Task 6 final GREEN workflow removed in **`09d464f2e9f7882cb7d735e7b6654b818476cec8`**; implementation harness removed in **`13fc778f8078625b0dab2fec835d7c1ee873d70a`**.
- Task 7 RED tests were persisted before production at **`0fffcc691bccabcaecc4f3fb473297da289d0726`** and **`2bd1babad8639679895363936f317ab74696a562`**.
- Task 7 GREEN product commit: **`29c8363804f6078371fb28f03dbb0dd3a7e80e18`** (`feat: add guarded matrix analysis operations`).
- Task 7 temporary RED/GREEN workflows, implementation harness, residual Task 6 context script and self-cleanup workflow were removed in **`fdf9f6fcb3acac7f8c66f2a69ad9fdcbf595612c`**.
- Task 8 accepted corrected RED test head: **`a24b38d87cb5268f4088f89813da03d9242c6a0a`**.
- Task 8 GREEN product commit: **`37c0cdb79b2ae4c0b2a039082a50260fda668700`** (`feat: render matrix calculations with MathJax`).
- Task 8 temporary RED/GREEN workflows and apply/escape harnesses were removed in cleanup commits **`40c17e47c3eec775c991618b801f326a48e524c1`**, **`37cfc0b2e9577c2354edfc5e667eb440e782e93d`**, **`2b34fca73b2e2db8d44978c28bbd042c4a1428d2`** and **`04669837755ff276a6e0ccaa1722a0aa73ac1f47`**.
- Task 9 accepted RED test head: **`5ea9caa9caa38710e0f380ee842569c8a85f650f`**; RED workflow commit: **`15e82fbab9f9a7fd84d3ec1074941689821734c7`**.
- Task 9 GREEN product commit: **`6bd29dbb8fb417667f1fb1e264d9cbd146a2bbe0`** (`feat: integrate EngCalc matrix CAS workflows`).
- Task 9 temporary RED/GREEN workflows and implementation harness were removed in **`83240acde126ffad3ce547bf3205b157ee3bf3cf`**, **`7c6f1cd1c18faeb6ec8780f26712d51174f9ab1e`** and **`70adb774b70807d146cebc173ef946da43f3ca73`**.
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

### Implemented 0.9.0 behavior through Task 9

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
- `solve(A,b)` now overloads the existing `solve` command by evaluated first-operand type: matrix first operands use exact linear-system solving, while nonmatrix first operands preserve the historical scalar `solve(eq,x)` route.
- Matrix linear systems require square `A`, a column-vector RHS with matching rows and a unique solution; failures are translated to EngCalc diagnostics rather than leaking SymPy exceptions.
- Exact matrix solutions are immutable SymPy column matrices; no float conversion occurs during symbolic solve.
- Solved structural displacement vectors evaluate through `numeric(...)` to `QuantityMatrix` entries with Pint length dimensionality.
- Mixed translational/rotational stiffness products remain valid heterogeneous numerical matrices, with force and moment result cells retaining distinct dimensions.
- `rank(A)`, `rref(A)` and Frobenius `norm(A)` now operate exactly on immutable symbolic matrices; `rref` returns the reduced immutable matrix and `rank` remains exact.
- `eigenvals(A)` and `eigenvects(A)` now use deterministic immutable result models that retain algebraic multiplicity; exact eigenvectors remain immutable column matrices.
- Task 7 analysis names are reserved restricted-DSL functions and reject nonmatrix inputs with stable EngCalc diagnostics.
- `MatrixNumericGuard(operation, source_matrix)` records the physical source matrix without wrapping every symbolic expression in a second algebra type.
- Engine assignments and matrix-valued user functions preserve and substitute guard provenance into later `numeric(...)` calls.
- Dimensionless and homogeneous/common-scale source matrices are accepted for guarded numerical rank/RREF/norm/eigen analysis; homogeneous eigenvalues preserve their common physical unit.
- Heterogeneous physical source matrices are rejected for numerical `rank`, `rref`, `norm`, `eigenvals` and `eigenvects` with operation-specific common-scale diagnostics; units are never silently stripped.
- Symbolic row, column and general matrices render as native MathJax matrix structures through the existing engineering renderer; raw `Matrix([[...` representations are not exposed.
- Homogeneous `QuantityMatrix` output factors one compatible common display unit outside the matrix while rendering per-cell magnitudes with active precision/zero tolerance; adaptable zeros remain neutral.
- Heterogeneous numerical matrices retain the Pint unit of each cell and never fabricate one matrix-wide unit.
- Matrix `numeric(...)` preserves formula → substitution → final numerical stages; `result(...)` omits the substitution stage; partial numerical matrices show formula/substitution only and never fabricate a final `QuantityMatrix`.
- `MatrixShape`, eigenvalue multiplicities and eigenvector sets render deterministically; eigenvectors remain native matrices and homogeneous numerical eigenvalues retain physical units.
- `%%eng` continues to use the same `render_aligned_results` source-order MathJax path for scalar and matrix results; no parallel matrix display system was introduced.
- Piecewise scalar expressions inside matrix cells evaluate entrywise through matrix-valued user functions, including exact breakpoint ownership and dimensional-zero semantics.
- Indexed scalar matrix responses such as `K(x)[1,1]` flow through the existing scalar `table`, `plot` and `envelope` APIs without broadening those APIs to whole matrices.
- Whole-matrix `table`, `plot` and `envelope` inputs are rejected before scalar numeric sampling with concise operation-specific `response must be scalar` diagnostics.
- The canonical structural worksheet runs in one `%%eng` cell with numerical material data, multiline stiffness/load matrices, exact `solve(K,F)`, `numeric(K)` and `numeric(u)` in source-order MathJax without traceback.
- README now documents the 0.9.0 Matrix/CAS development syntax, one-based indexing, exact `solve(A,b)`, `numeric(A)`, per-entry dimensional semantics and whole-matrix table/plot limitation while runtime remains 0.8.0.

## Open issues / user feedback

- Task 10 must bump package/runtime/documentation contracts from 0.8.0 to 0.9.0 only after a version RED is observed.
- Task 10 must build the real wheel, validate wheel metadata and SHA-256, then verify from a clean external environment with `src/` excluded.
- The installed-wheel/source-free suite must pass before a release PR is opened.
- Whole-matrix `table`, `plot` and `envelope` remain deliberately out of scope; only indexed scalar matrix responses integrate with those scalar APIs.
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

### 0.9.0 Task 6 RED/GREEN evidence

- The accepted Task 6 RED contract head is **`ac7c1f354f6e0b559f8e602471e9953f8779da06`**. Earlier RED attempts were not accepted as evidence because the mixed-DOF hand reference was corrected before the clean gate.
- Clean RED Actions **`33326041862`**, job **`99296222756`**, CPython **3.13.15**: **6 failed, 2 passed in 1.77 s**. The six failures were precisely the missing matrix `solve(A,b)` overload/diagnostics; the two passes proved mixed-DOF heterogeneous numerical multiplication and historical scalar `solve(eq,x)` remained intact.
- Clean RED artifact **`9736251229`**, digest **`sha256:ab69156dcb60063bdc4d0cdf4f1b9ada5082cc4c273d7e81931f84e0d5fea806`**.
- Final GREEN Actions **`33326265185`**, job **`99296815169`**, CPython **3.13.15**: compile check + `git diff --check` GREEN; **23/23 focused GREEN in 4.12 s**; **665/665 full GREEN in 111.51 s**.
- Product commit **`67b22d531955e8795e446afefc0ad0e698c9973d`** (`feat: solve exact linear matrix systems`) changed exactly two production files: `src/engcalc_colab/engine.py` (+7) and new `src/engcalc_colab/matrix_solve.py` (+35).
- GREEN logs artifact **`9736336536`**, digest **`sha256:e576126b0b7b730935ddd8e8b4244b6b7deee5454abc94fdce58358e95912e33`**.
- The first GREEN run stopped before pytest because a harness validation used `git diff --name-only` for an untracked new file; no product commit occurred. The validation was corrected to distinguish tracked modifications from the untracked new module, after which the final GREEN run passed.
- Temporary Task 6 workflows and implementation/correction harnesses were removed after preserving evidence.
- The runner's Node 20 deprecation/forced Node 24 warning is infrastructure-only and not an EngCalc product failure.

### 0.9.0 Task 7 RED/GREEN evidence

- Task 7 exact-analysis tests were committed at **`0fffcc691bccabcaecc4f3fb473297da289d0726`** and dimensional/provenance tests at **`2bd1babad8639679895363936f317ab74696a562`**, before any Task 7 production code.
- RED Actions **`33326737368`**, job **`99298108349`**, CPython **3.13.15**: **19 failed in 4.58 s**. All failures were the expected absence/reservation gap for `rank`, `rref`, `norm`, `eigenvals`, `eigenvects` and their guard infrastructure; there were no unrelated collection/regression failures.
- RED artifact **`9736448408`**, digest **`sha256:862eb9f86a4c05810f35254a58c2d41de33a770104a9bb294fc68e5abd59788d`**.
- Final GREEN Actions **`33327637858`**, job **`99300495358`**, CPython **3.13.15**: compile check + `git diff --check` + exact patch audit GREEN; **55/55 focused GREEN in 8.57 s**; **684/684 full GREEN in 134.17 s**.
- Product commit **`29c8363804f6078371fb28f03dbb0dd3a7e80e18`** (`feat: add guarded matrix analysis operations`) contains exactly five production files: modified `engine.py`, new `matrix_analysis.py`, modified `matrix_numeric.py`, modified `models.py` and modified `parser.py`; total **300 additions, 0 deletions**.
- GREEN logs artifact **`9736728954`**, digest **`sha256:0a4b600ed140f64b0bf3284a87a5a3778ebdefdc0d6f800a7a1ccabd3b22699a`**.
- Cleanup Actions **`33327852770`** removed exactly the Task 7 RED/GREEN workflows, Task 7 implementation harness, residual Task 6 context script and its self-cleanup workflow; cleanup commit **`fdf9f6fcb3acac7f8c66f2a69ad9fdcbf595612c`**.
- The runner's Node 20 deprecation/forced Node 24 warning is infrastructure-only and not an EngCalc product failure.

### 0.9.0 Task 8 RED/GREEN evidence

- Task 8 renderer/magic tests were written before accepted production code. The corrected clean RED head was **`a24b38d87cb5268f4088f89813da03d9242c6a0a`**.
- Corrected RED Actions **`33330073653`**, job **`99306945957`**, CPython **3.13.15**: **13 failed, 3 passed in 4.36 s**. The three passes were pre-existing SymPy matrix-printing capability; the 13 failures were the missing matrix numeric/partial/shape/eigen/`%%eng` presentation paths.
- Corrected RED artifact **`9737377959`**, digest **`sha256:a7c0508b5c17717c2d5b7cc87f8ba889f99e3a703920f671a309b128e481f9c5`**.
- A prior candidate run (`33329742934`) exposed a CI harness defect: `pytest | tee` lacked `pipefail`, so pytest failures were swallowed and candidate commit `08f4906da33557ef66c66407cb411b90d80179f3` was created prematurely. That commit was explicitly invalidated and reverted in **`1b9aedebcdde0c598244178014e6d4fe799ce533`** before re-running RED/GREEN. Four assertions were then corrected where they overconstrained string substrings, canonical heterogeneous units, or a nonexistent partial-final numeric stage; test intent remained aligned with the approved spec.
- Final GREEN Actions **`33330195507`**, job **`99307284768`**, CPython **3.13.15**, with `set -o pipefail`: compile check + `git diff --check` + exact renderer-only patch audit GREEN; **65/65 focused GREEN in 11.59 s**; **700/700 full GREEN in 117.35 s**.
- Product commit **`37c0cdb79b2ae4c0b2a039082a50260fda668700`** (`feat: render matrix calculations with MathJax`) changed exactly one production file: `src/engcalc_colab/renderer.py` (**251 additions, 4 deletions**).
- GREEN logs artifact **`9737440675`**, digest **`sha256:c0531c7c1bb334aeaa8264b82af11d6351bd64fa23b4a808ae6f4bac1cfe0d5d`**.
- Task 8 RED/GREEN workflows and apply/escape harnesses were removed after evidence preservation; no product source changed during cleanup.
- The runner's Node 20 deprecation/forced Node 24 warning remains infrastructure-only and is not an EngCalc product failure.

### 0.9.0 Task 9 RED/GREEN evidence

- Task 9 acceptance/integration contracts were persisted before production in `tests/test_matrix_acceptance.py`, `tests/test_matrix_integration.py` and the extended `tests/test_matrix_diagnostics.py`; accepted test head **`5ea9caa9caa38710e0f380ee842569c8a85f650f`**.
- RED Actions **`33330893770`**, job **`99309133015`**, CPython **3.13.15**: **4 failed, 25 passed in 4.65 s**. The 25 passes established that Piecewise matrix cells, indexed scalar table/plot/envelope behavior, canonical structural worksheet and mandatory historical diagnostics were already correct. The four genuine gaps were README Matrix/CAS documentation plus concise whole-matrix rejection messages for `table`, `plot` and `envelope`.
- RED artifact **`9737606835`**, digest **`sha256:6c062c92d15fb2de3c3df43362c2c361951714f4a48e30cd79ab10a9d4da2d2c`**.
- Final GREEN Actions **`33331638868`**, job **`99311093809`**, CPython **3.13.15**, with `set -o pipefail`: compile check + `git diff --check` + exact two-file patch audit GREEN; **29/29 Task 9 focused GREEN in 6.24 s**; **164/164 Matrix/CAS acceptance GREEN in 27.38 s**; **721/721 complete suite GREEN in 139.26 s**.
- Product commit **`6bd29dbb8fb417667f1fb1e264d9cbd146a2bbe0`** (`feat: integrate EngCalc matrix CAS workflows`) changed exactly `README.md` (+16) and `src/engcalc_colab/engine.py` (+12), with no deletions and no unrelated product files.
- GREEN logs artifact **`9737847921`**, digest **`sha256:539dddd248c7f9f2c5e2a138adeb9838d2a1f7d37b1de55d6c125b0055d5bd9a`**.
- Post-validation compare `6bd29dbb...` → `70adb774...` contains only deletion of the Task 9 RED/GREEN workflows and implementation harness; no `src/`, README or product-test changes occurred after the validated product tree.
- The runner's Node 20 deprecation/forced Node 24 warning remains infrastructure-only and is not an EngCalc product failure.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–9 COMPLETE, TASK 10 RELEASE VALIDATION NEXT**.
  - Base design/spec/clarification/implementation plan: approved.
  - Task 0 isolated baseline: COMPLETE.
  - Task 1 matrix literal parser: COMPLETE, 569/569 GREEN.
  - Task 2 immutable symbolic matrices, matrix operators and one-based indexing: COMPLETE, 596/596 GREEN.
  - Task 3 constructors and core exact matrix functions: COMPLETE, 31/31 focused + 627/627 full GREEN.
  - Task 4 matrix-valued user functions and matrix-aware existing CAS transforms: COMPLETE, 15/15 focused + 642/642 full GREEN.
  - Task 5 Pint-backed numerical matrices and partial numeric matrices: COMPLETE, 27/27 focused + 657/657 full GREEN.
  - Task 6 exact `solve(A,b)` and dimensional structural solve acceptance: COMPLETE, 23/23 focused + 665/665 full GREEN.
  - Task 7 rank/RREF/norm/eigen analysis and common-scale numeric guards: COMPLETE, 55/55 focused + 684/684 full GREEN.
  - Task 8 native MathJax rendering for symbolic/partial/numerical matrices and analysis models: COMPLETE, 65/65 focused + 700/700 full GREEN.
  - Task 9 Piecewise/table/plot integration, diagnostics and end-to-end structural acceptance: COMPLETE, 29/29 focused + 164/164 Matrix/CAS acceptance + 721/721 full GREEN.
  - Task 10 release 0.9.0, installed-wheel/source-free validation and release PR: NEXT.
  - Package/runtime version remains 0.8.0 until Task 10's version GREEN.
- Later roadmap: 0.9.1 exact-first extrema/roots/intersections → 0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization.

## Exact next step

1. Start Task 10 with version-contract RED tests first: change `tests/test_version.py`, `tests/test_packaging.py` and only the intentional version assertion in `tests/test_parser.py` so they require exactly `0.9.0` plus final Matrix/CAS README release wording.
2. Run that focused version suite RED and verify failures are only the current 0.8.0 runtime/package/documentation state; do not change product/version metadata before observing RED.
3. Apply the minimal version bump to `pyproject.toml` and `src/engcalc_colab/__init__.py`, and promote README wording from development scope to the 0.9.0 release section without changing Matrix/CAS semantics.
4. Run the release-contract GREEN, then the complete source suite.
5. Build `engcalc_colab-0.9.0-py3-none-any.whl`; verify wheel metadata says exactly `Version: 0.9.0` and record SHA-256.
6. Create a clean external virtual environment outside the repository, install only the wheel plus test-host requirements, and run the mandatory Matrix/CAS smoke with the working directory outside the source tree.
7. Run the complete source-free suite against installed `site-packages`, prove `src/` is not on `PYTHONPATH` and record the imported module path.
8. Repeat the complete source suite on the repository tree after installed-wheel validation.
9. Permit only validation-harness cleanup and `CURRENT.md` updates after the authoritative validated release SHA; prove no source/tests/README/package metadata changed afterward.
10. Open the release PR titled `release: EngCalc 0.9.0 matrix CAS` with all RED/GREEN, wheel and source-free evidence, then stop before merge for explicit user approval. Do not invoke Codex.

## How to resume in a new conversation

Read this file first. EngCalc 0.8.0 remains integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`. Tasks 0–9 are complete. Task 9 product commit `6bd29dbb8fb417667f1fb1e264d9cbd146a2bbe0` closes Piecewise-cell, indexed scalar table/plot/envelope, whole-matrix diagnostics, README Matrix/CAS documentation and the canonical structural worksheet; final verification was 29/29 focused, 164/164 Matrix/CAS acceptance and 721/721 complete. The exact next action is Task 10 version RED for the 0.9.0 package/release contract, followed by wheel and source-free validation. Never invoke Codex and never merge without explicit user approval.
