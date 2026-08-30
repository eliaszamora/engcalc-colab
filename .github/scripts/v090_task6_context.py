from pathlib import Path
import re

path = Path("docs/project-context/CURRENT.md")
text = path.read_text(encoding="utf-8")

text, count = re.subn(
    r"_Last updated: 2026-08-30 — .*?_\n",
    "_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–6 are complete with strict RED→GREEN evidence. Exact `solve(A,b)` now supports square linear systems, structural dimensional evaluation and stable matrix diagnostics while preserving scalar `solve(eq,x)`. Task 7 — exact matrix analysis plus common-scale numerical guards — is the exact next step. Package/runtime version remains 0.8.0._\n",
    text,
    count=1,
)
assert count == 1

marker = "- Task 5 final GREEN workflow removed in **`c104a6a29a7e533eee01d4261a88f551dfa2715d`**; implementation harness removed in **`d17c28fd87ae58567c75b92116389de2e713b431`**.\n"
assert marker in text
text = text.replace(
    marker,
    marker
    + "- Task 6 accepted clean RED test head: **`ac7c1f354f6e0b559f8e602471e9953f8779da06`**.\n"
    + "- Task 6 GREEN product commit: **`67b22d531955e8795e446afefc0ad0e698c9973d`** (`feat: solve exact linear matrix systems`).\n"
    + "- Task 6 temporary RED workflows removed in **`2ba11fa2cee0adb38a7bf26b9f537858d48627c8`** and **`937914a807e02e4cd7c69816c7c026513ce95c9a`**; RED correction harness removed in **`3b8805ea9bd29dca39c564b537b0017072ed7a3b`**.\n"
    + "- Task 6 final GREEN workflow removed in **`09d464f2e9f7882cb7d735e7b6654b818476cec8`**; implementation harness removed in **`13fc778f8078625b0dab2fec835d7c1ee873d70a`**.\n",
    1,
)

text = text.replace(
    "### Implemented 0.9.0 behavior through Task 5\n",
    "### Implemented 0.9.0 behavior through Task 6\n",
    1,
)
impl_marker = "- Matrix-valued user functions use the existing argument-binding/shadowing rules during `numeric(...)`; `result(A)` follows the same full/partial matrix evaluation route.\n"
assert impl_marker in text
text = text.replace(
    impl_marker,
    impl_marker
    + "- `solve(A,b)` now overloads the existing `solve` command by evaluated first-operand type: matrix first operands use exact linear-system solving, while nonmatrix first operands preserve the historical scalar `solve(eq,x)` route.\n"
    + "- Matrix linear systems require square `A`, a column-vector RHS with matching rows and a unique solution; failures are translated to EngCalc diagnostics rather than leaking SymPy exceptions.\n"
    + "- Exact matrix solutions are immutable SymPy column matrices; no float conversion occurs during symbolic solve.\n"
    + "- Solved structural displacement vectors evaluate through `numeric(...)` to `QuantityMatrix` entries with Pint length dimensionality.\n"
    + "- Mixed translational/rotational stiffness products remain valid heterogeneous numerical matrices, with force and moment result cells retaining distinct dimensions.\n",
    1,
)

text = text.replace(
    "- Task 6 must add exact `solve(A,b)` for square linear systems while preserving existing scalar `solve(eq,x)` behavior and translating shape/singularity failures to EngCalc diagnostics.\n",
    "- Task 7 must add exact `rank`, `rref`, Frobenius `norm`, `eigenvals` and `eigenvects` plus provenance-aware numerical guards for operations that require a dimensionless or common-scale source matrix.\n",
    1,
)
text = text.replace(
    "- Exact matrix linear systems and dimensional structural solve acceptance are now the active next task in the approved 0.9.0 plan.\n",
    "- Exact/common-scale guarded matrix analysis is now the active next task in the approved 0.9.0 plan.\n",
    1,
)
text = text.replace(
    "- `rank`, `rref`, `norm`, `eigenvals` and `eigenvects` remain later exact/common-scale guarded tasks after `solve(A,b)`.\n",
    "- Matrix rendering/presentation remains Task 8 after Task 7 analysis semantics and guard provenance are stable.\n",
    1,
)

validation = """\n### 0.9.0 Task 6 RED/GREEN evidence\n\n- The accepted Task 6 RED contract head is **`ac7c1f354f6e0b559f8e602471e9953f8779da06`**. Earlier RED attempts were not accepted as evidence because the mixed-DOF hand reference was corrected before the clean gate.\n- Clean RED Actions **`33326041862`**, job **`99296222756`**, CPython **3.13.15**: **6 failed, 2 passed in 1.77 s**. The six failures were precisely the missing matrix `solve(A,b)` overload/diagnostics; the two passes proved mixed-DOF heterogeneous numerical multiplication and historical scalar `solve(eq,x)` remained intact.\n- Clean RED artifact **`9736251229`**, digest **`sha256:ab69156dcb60063bdc4d0cdf4f1b9ada5082cc4c273d7e81931f84e0d5fea806`**.\n- Final GREEN Actions **`33326265185`**, job **`99296815169`**, CPython **3.13.15**: compile check + `git diff --check` GREEN; **23/23 focused GREEN in 4.12 s**; **665/665 full GREEN in 111.51 s**.\n- Product commit **`67b22d531955e8795e446afefc0ad0e698c9973d`** (`feat: solve exact linear matrix systems`) changed exactly two production files: `src/engcalc_colab/engine.py` (+7) and new `src/engcalc_colab/matrix_solve.py` (+35).\n- GREEN logs artifact **`9736336536`**, digest **`sha256:e576126b0b7b730935ddd8e8b4244b6b7deee5454abc94fdce58358e95912e33`**.\n- The first GREEN run stopped before pytest because a harness validation used `git diff --name-only` for an untracked new file; no product commit occurred. The validation was corrected to distinguish tracked modifications from the untracked new module, after which the final GREEN run passed.\n- Temporary Task 6 workflows and implementation/correction harnesses were removed after preserving evidence.\n- The runner's Node 20 deprecation/forced Node 24 warning is infrastructure-only and not an EngCalc product failure.\n\n"""
assert "\n## Roadmap / active plan\n" in text
text = text.replace("\n## Roadmap / active plan\n", validation + "## Roadmap / active plan\n", 1)

text = text.replace(
    "- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–5 COMPLETE, TASK 6 NEXT**.",
    "- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–6 COMPLETE, TASK 7 NEXT**.",
    1,
)
text = text.replace(
    "  - Task 6 exact `solve(A,b)` and dimensional structural solve acceptance: NEXT.",
    "  - Task 6 exact `solve(A,b)` and dimensional structural solve acceptance: COMPLETE, 23/23 focused + 665/665 full GREEN.\n  - Task 7 rank/RREF/norm/eigen analysis and common-scale numeric guards: NEXT.",
    1,
)

new_tail = """## Exact next step\n\n1. Add Task 7 RED tests in `tests/test_matrix_analysis.py` and `tests/test_matrix_analysis_units.py` for exact `rank`, `rref`, Frobenius `norm`, deterministic eigenvalue multiplicities/order and eigenvector result models.\n2. Add common-scale numerical acceptance for dimensionless and homogeneous matrices, including `numeric(norm(A))`, numerical RREF/eigen evaluation and homogeneous eigenvalue units where mathematically defined.\n3. Add heterogeneous rejection tests using the Task 5 beam stiffness matrix: numerical `rref`, `norm` and eigenanalysis must fail with operation-specific common-scale diagnostics rather than stripping units.\n4. Add guard-propagation RED tests so assigned guarded results and matrix-valued user functions retain provenance into later `numeric(...)`.\n5. Run Task 7 tests RED before production changes.\n6. Implement explicit analysis result models/functions and `MatrixNumericGuard` provenance without wrapping every SymPy expression in a second symbolic type.\n7. Validate common-scale source matrices through `QuantityMatrix`; accept dimensionless/common-unit sources and reject heterogeneous physical sources before guarded numerical results are accepted.\n8. Run focused GREEN and then the complete suite; persist product only after both gates pass.\n9. Update this file with Task 7 RED/GREEN SHAs and counts before Task 8 rendering.\n10. Do not invoke Codex and do not merge without explicit user authorization.\n\n## How to resume in a new conversation\n\nRead this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`. Tasks 0–6 are complete. Task 6 product commit `67b22d531955e8795e446afefc0ad0e698c9973d` adds exact `solve(A,b)` with square/column/matching-shape/unique-solution diagnostics while preserving scalar `solve(eq,x)`; final verification was 23/23 focused plus 665/665 complete. The exact next action is Task 7 RED for rank/RREF/Frobenius norm/eigen analysis and common-scale numerical guard provenance. Never invoke Codex and never merge without explicit user approval.\n"""
text, count = re.subn(
    r"## Exact next step\n\n.*?## How to resume in a new conversation\n\n.*?\Z",
    new_tail,
    text,
    flags=re.S,
)
assert count == 1

path.write_text(text, encoding="utf-8")
