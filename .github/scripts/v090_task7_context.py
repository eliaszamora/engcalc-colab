from pathlib import Path
import re

path = Path("docs/project-context/CURRENT.md")
text = path.read_text(encoding="utf-8")

text, count = re.subn(
    r"_Last updated: 2026-08-30 — .*?_\n",
    "_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–7 are complete with strict RED→GREEN evidence. Exact rank/RREF/Frobenius norm/eigen analysis now includes deterministic result models and provenance-aware common-scale numerical guards. Task 8 — native MathJax matrix rendering and numerical presentation — is the exact next step. Package/runtime version remains 0.8.0._\n",
    text,
    count=1,
)
assert count == 1

marker = "- Task 6 final GREEN workflow removed in **`09d464f2e9f7882cb7d735e7b6654b818476cec8`**; implementation harness removed in **`13fc778f8078625b0dab2fec835d7c1ee873d70a`**.\n"
assert marker in text
text = text.replace(
    marker,
    marker
    + "- Task 7 RED tests were persisted before production at **`0fffcc691bccabcaecc4f3fb473297da289d0726`** and **`2bd1babad8639679895363936f317ab74696a562`**.\n"
    + "- Task 7 GREEN product commit: **`29c8363804f6078371fb28f03dbb0dd3a7e80e18`** (`feat: add guarded matrix analysis operations`).\n"
    + "- Task 7 temporary RED/GREEN workflows, implementation harness, residual Task 6 context script and self-cleanup workflow were removed in **`fdf9f6fcb3acac7f8c66f2a69ad9fdcbf595612c`**.\n",
    1,
)

text = text.replace(
    "### Implemented 0.9.0 behavior through Task 6\n",
    "### Implemented 0.9.0 behavior through Task 7\n",
    1,
)
impl_marker = "- Mixed translational/rotational stiffness products remain valid heterogeneous numerical matrices, with force and moment result cells retaining distinct dimensions.\n"
assert impl_marker in text
text = text.replace(
    impl_marker,
    impl_marker
    + "- `rank(A)`, `rref(A)` and Frobenius `norm(A)` now operate exactly on immutable symbolic matrices; `rref` returns the reduced immutable matrix and `rank` remains exact.\n"
    + "- `eigenvals(A)` and `eigenvects(A)` now use deterministic immutable result models that retain algebraic multiplicity; exact eigenvectors remain immutable column matrices.\n"
    + "- Task 7 analysis names are reserved restricted-DSL functions and reject nonmatrix inputs with stable EngCalc diagnostics.\n"
    + "- `MatrixNumericGuard(operation, source_matrix)` records the physical source matrix without wrapping every symbolic expression in a second algebra type.\n"
    + "- Engine assignments and matrix-valued user functions preserve and substitute guard provenance into later `numeric(...)` calls.\n"
    + "- Dimensionless and homogeneous/common-scale source matrices are accepted for guarded numerical rank/RREF/norm/eigen analysis; homogeneous eigenvalues preserve their common physical unit.\n"
    + "- Heterogeneous physical source matrices are rejected for numerical `rank`, `rref`, `norm`, `eigenvals` and `eigenvects` with operation-specific common-scale diagnostics; units are never silently stripped.\n",
    1,
)

text = text.replace(
    "- Task 7 must add exact `rank`, `rref`, Frobenius `norm`, `eigenvals` and `eigenvects` plus provenance-aware numerical guards for operations that require a dimensionless or common-scale source matrix.\n",
    "- Task 8 must add native MathJax rendering for symbolic, partial and numerical matrices plus deterministic rendering for shape/eigen result models.\n",
    1,
)
text = text.replace(
    "- Matrix rendering/presentation has not yet been implemented; current work establishes symbolic and numeric truth before final presentation.\n",
    "- Matrix rendering/presentation is now the active next task; symbolic and numeric matrix truth is established through Task 7.\n",
    1,
)
text = text.replace(
    "- Exact/common-scale guarded matrix analysis is now the active next task in the approved 0.9.0 plan.\n",
    "- Task 8 must extend the existing engineering renderer rather than introduce a parallel display system.\n",
    1,
)
text = text.replace(
    "- Matrix rendering/presentation remains Task 8 after Task 7 analysis semantics and guard provenance are stable.\n",
    "- Task 9 Piecewise/table/plot integration and end-to-end structural acceptance remains after Task 8 rendering.\n",
    1,
)

validation = """\n### 0.9.0 Task 7 RED/GREEN evidence\n\n- Task 7 exact-analysis tests were committed at **`0fffcc691bccabcaecc4f3fb473297da289d0726`** and dimensional/provenance tests at **`2bd1babad8639679895363936f317ab74696a562`**, before any Task 7 production code.\n- RED Actions **`33326737368`**, job **`99298108349`**, CPython **3.13.15**: **19 failed in 4.58 s**. All failures were the expected absence/reservation gap for `rank`, `rref`, `norm`, `eigenvals`, `eigenvects` and their guard infrastructure; there were no unrelated collection/regression failures.\n- RED artifact **`9736448408`**, digest **`sha256:862eb9f86a4c05810f35254a58c2d41de33a770104a9bb294fc68e5abd59788d`**.\n- Final GREEN Actions **`33327637858`**, job **`99300495358`**, CPython **3.13.15**: compile check + `git diff --check` + exact patch audit GREEN; **55/55 focused GREEN in 8.57 s**; **684/684 full GREEN in 134.17 s**.\n- Product commit **`29c8363804f6078371fb28f03dbb0dd3a7e80e18`** (`feat: add guarded matrix analysis operations`) contains exactly five production files: modified `engine.py`, new `matrix_analysis.py`, modified `matrix_numeric.py`, modified `models.py` and modified `parser.py`; total **300 additions, 0 deletions**.\n- GREEN logs artifact **`9736728954`**, digest **`sha256:0a4b600ed140f64b0bf3284a87a5a3778ebdefdc0d6f800a7a1ccabd3b22699a`**.\n- Cleanup Actions **`33327852770`** removed exactly the Task 7 RED/GREEN workflows, Task 7 implementation harness, residual Task 6 context script and its self-cleanup workflow; cleanup commit **`fdf9f6fcb3acac7f8c66f2a69ad9fdcbf595612c`**.\n- The runner's Node 20 deprecation/forced Node 24 warning is infrastructure-only and not an EngCalc product failure.\n\n"""
assert "\n## Roadmap / active plan\n" in text
text = text.replace("\n## Roadmap / active plan\n", validation + "## Roadmap / active plan\n", 1)

text = text.replace(
    "- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–6 COMPLETE, TASK 7 NEXT**.",
    "- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–7 COMPLETE, TASK 8 NEXT**.",
    1,
)
text = text.replace(
    "  - Task 7 rank/RREF/norm/eigen analysis and common-scale numeric guards: NEXT.",
    "  - Task 7 rank/RREF/norm/eigen analysis and common-scale numeric guards: COMPLETE, 55/55 focused + 684/684 full GREEN.\n  - Task 8 native MathJax rendering for symbolic/partial/numerical matrices and analysis models: NEXT.",
    1,
)

new_tail = """## Exact next step\n\n1. Add Task 8 RED tests in `tests/test_matrix_renderer.py` and `tests/test_matrix_magic.py` before changing renderer production code.\n2. Require symbolic row/column/general matrices to render through the existing engineering MathJax path as matrix LaTeX, never raw `Matrix([[...` text.\n3. Define homogeneous numerical-matrix presentation with one common unit and per-cell magnitudes, including adaptable zero display under active precision/zero-tolerance settings.\n4. Define heterogeneous numerical-matrix presentation with the correct Pint unit in each cell and no fabricated matrix-wide unit.\n5. Preserve the existing `numeric(...)` versus `result(...)` stage semantics for matrices and partial matrix results.\n6. Render `MatrixShape`, eigenvalue multiplicities and eigenvectors deterministically using the existing renderer; Task 8 may add only minimal renderer-facing model metadata if required.\n7. Run Task 8 tests RED before production changes, then implement by extending `renderer.py`/`magic.py` rather than adding a parallel display system.\n8. Run focused GREEN across Task 8 plus renderer/magic regressions, then run the complete suite; persist product only after both gates pass.\n9. Perform user-facing/Colab presentation QA after machine GREEN because Task 8 is visual output.\n10. Update this file with Task 8 evidence before Task 9 integration. Do not invoke Codex and do not merge without explicit user authorization.\n\n## How to resume in a new conversation\n\nRead this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`. Tasks 0–7 are complete. Task 7 product commit `29c8363804f6078371fb28f03dbb0dd3a7e80e18` adds exact rank/RREF/Frobenius norm/eigen analysis plus provenance-aware common-scale numerical guards; final verification was 55/55 focused and 684/684 complete. The exact next action is Task 8 RED for native MathJax rendering of symbolic, partial and numerical matrices and deterministic analysis-result presentation. Never invoke Codex and never merge without explicit user approval.\n"""
text, count = re.subn(
    r"## Exact next step\n\n.*?## How to resume in a new conversation\n\n.*?\Z",
    new_tail,
    text,
    flags=re.S,
)
assert count == 1

path.write_text(text, encoding="utf-8")
