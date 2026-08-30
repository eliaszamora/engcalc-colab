from pathlib import Path
import re

path = Path("docs/project-context/CURRENT.md")
text = path.read_text(encoding="utf-8")

text, count = re.subn(
    r"_Last updated: 2026-08-30 — .*?_\n",
    "_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–5 are complete with strict RED→GREEN evidence. Pint-backed numerical matrices now preserve per-entry dimensionality, homogeneous target-unit conversion, exact-zero adaptability and partial matrix evaluation. Task 6 — exact `solve(A,b)` plus dimensional structural solve acceptance — is the exact next step. Package/runtime version remains 0.8.0._\n",
    text,
    count=1,
)
assert count == 1

baseline_marker = "- Task 4 temporary RED workflow removed in `a3d5b311e42de417b091784a3688799249f92903`; final GREEN workflow removed in `ca85d897e0983c6746a2e8c0d435062b0d35f220`; implementation harness removed in `bd28e033bdf3a1ba6dbcc628886db1950d3dff6e`.\n"
assert baseline_marker in text
text = text.replace(
    baseline_marker,
    baseline_marker
    + "- Task 5 RED test commits: **`fb0339b59fe42e14f1a4e6914a290cd1d596df06`** and **`b6c424273e922bd3434eb0108df9f55b5e9acb62`**.\n"
    + "- Task 5 RED workflow commit: **`7a595e9a0a3c2367b70e1ee169513d48ded749b2`**; RED workflow removed in **`dbb3e6f751426c76c7a15441370a96de0a3b9dff`**.\n"
    + "- Task 5 GREEN product commit: **`68f8a23`** (`feat: evaluate matrices with Pint units`).\n"
    + "- Task 5 final GREEN workflow removed in **`c104a6a29a7e533eee01d4261a88f551dfa2715d`**; implementation harness removed in **`d17c28fd87ae58567c75b92116389de2e713b431`**.\n",
    1,
)

text = text.replace(
    "### Implemented 0.9.0 behavior through Task 4\n",
    "### Implemented 0.9.0 behavior through Task 5\n",
    1,
)
implemented_marker = "- `map_matrix_entries(...)` is the single immutable entrywise CAS mapping primitive; `substitute_symbolic_value(...)` centralizes scalar/matrix function substitution while preserving existing scalar behavior.\n"
assert implemented_marker in text
text = text.replace(
    implemented_marker,
    implemented_marker
    + "- `QuantityMatrix` is now the immutable Pint-valued numerical output boundary; it deliberately exposes no public matrix arithmetic parallel to SymPy.\n"
    + "- `numeric(A)` evaluates immutable symbolic matrices cell by cell through the existing `NumericContext`, preserving Pint dimensionality per entry.\n"
    + "- Homogeneous numerical matrices accept a single compatible target unit through `numeric(A, unit)`; heterogeneous matrices reject a single incompatible matrix-wide target unit with a coordinate-aware diagnostic.\n"
    + "- Exact symbolic zeros are tracked as adaptable zero cells and inherit a target unit only when the requested homogeneous conversion makes that inheritance unambiguous.\n"
    + "- Matrix numeric failures identify the one-based failing coordinate, e.g. `[2,1]`, while `QuantityMatrix.entry(row,col)` remains internal zero-based storage.\n"
    + "- Partial numerical matrices return `PartialMatrixNumericEvaluationResult` with deterministic unresolved-symbol ordering and known Pint substitutions; target-unit conversion remains blocked until fully numeric.\n"
    + "- Matrix-valued user functions use the existing argument-binding/shadowing rules during `numeric(...)`; `result(A)` follows the same full/partial matrix evaluation route.\n",
    1,
)

text = text.replace(
    "- Task 5 must introduce immutable `QuantityMatrix` numerical outputs with per-entry Pint dimensionality, homogeneous target-unit conversion, exact-zero adaptability, coordinate-aware diagnostics and partial numeric matrix evaluation.\n",
    "- Task 6 must add exact `solve(A,b)` for square linear systems while preserving existing scalar `solve(eq,x)` behavior and translating shape/singularity failures to EngCalc diagnostics.\n",
    1,
)
text = text.replace(
    "- Numerical/unit-aware matrices (`QuantityMatrix`) are now the active next task in the approved 0.9.0 plan.\n",
    "- Exact matrix linear systems and dimensional structural solve acceptance are now the active next task in the approved 0.9.0 plan.\n",
    1,
)
text = text.replace(
    "- `rank`, `rref`, `norm`, `eigenvals`, `eigenvects` and `solve(A,b)` are later exact tasks in the plan.\n",
    "- `rank`, `rref`, `norm`, `eigenvals` and `eigenvects` remain later exact/common-scale guarded tasks after `solve(A,b)`.\n",
    1,
)

validation = """\n### 0.9.0 Task 5 RED/GREEN evidence\n\n- Task 5 numerical-matrix tests were committed before production code at **`fb0339b59fe42e14f1a4e6914a290cd1d596df06`** and **`b6c424273e922bd3434eb0108df9f55b5e9acb62`**.\n- RED Actions **`33325205662`**, job **`99293997738`**, CPython **3.13.15**: **15 failed in 3.58 s**, with no collection errors. Full numeric cases failed because `numeric(...)` rejected `ImmutableDenseMatrix`; partial cases still entered the scalar missing-value path, exactly establishing the missing Task 5 boundary.\n- RED artifact **`9736021588`**, digest **`sha256:c7cf07b50c8d8398e4fdf943375a0ee1bbc7dbad5646b27af9b32c420b4f466d`**.\n- Final GREEN Actions **`33325415322`**, job **`99294564132`**, CPython **3.13.15**: compile check + `git diff --check` GREEN; **27/27 focused GREEN in 5.52 s**; **657/657 full GREEN in 129.46 s**.\n- Product commit **`68f8a23`** (`feat: evaluate matrices with Pint units`) changed exactly four production files: `src/engcalc_colab/engine.py`, new `src/engcalc_colab/matrix_numeric.py`, `src/engcalc_colab/models.py`, and `src/engcalc_colab/numeric.py`; audit from `c4aee7b...` shows 301 additions and 23 deletions with no unrelated product files.\n- GREEN logs artifact **`9736111856`**, digest **`sha256:660b95eaadf0f5d74ab54b7a9b6ced43858f69b7cde377f297348bb7ca914a49`**.\n- Temporary Task 5 RED/GREEN workflows and implementation harness were removed after evidence was preserved.\n- The only runner warning was GitHub Actions' Node 20 deprecation/forced Node 24 compatibility warning; it is not an EngCalc product failure.\n\n"""
assert "\n## Roadmap / active plan\n" in text
text = text.replace("\n## Roadmap / active plan\n", validation + "## Roadmap / active plan\n", 1)

text = text.replace(
    "- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–4 COMPLETE, TASK 5 NEXT**.",
    "- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–5 COMPLETE, TASK 6 NEXT**.",
    1,
)
text = text.replace(
    "  - Task 5 Pint-backed numerical matrices and partial numeric matrices: NEXT.",
    "  - Task 5 Pint-backed numerical matrices and partial numeric matrices: COMPLETE, 27/27 focused + 657/657 full GREEN.\n  - Task 6 exact `solve(A,b)` and dimensional structural solve acceptance: NEXT.",
    1,
)

new_next = """## Exact next step\n\n1. Add Task 6 RED tests in `tests/test_matrix_solve.py` for exact `solve(A,b)` using the two-DOF stiffness system from the approved plan.\n2. Verify `K*u-F` simplifies to the exact zero matrix and preserve existing scalar `solve(eq,x)` behavior.\n3. Add explicit EngCalc diagnostics for nonsquare `A`, row-vector RHS, wrong RHS length and singular/non-unique systems.\n4. Add dimensional acceptance: with `k1 := 20*kN/mm`, `k2 := 15*kN/mm`, `P := 30*kN`, `numeric(u)` must return a `2 x 1` `QuantityMatrix` whose entries have length dimensionality.\n5. Add a mixed translational/rotational DOF case whose symbolic stiffness multiplication evaluates numerically to heterogeneous force/moment result cells without imposing one matrix-wide unit.\n6. Run the new Task 6 tests RED before production.\n7. Implement `matrix_solve.py` and overload `solve` by evaluated first-argument type; keep the scalar `solve(eq,x)` route unchanged where possible.\n8. Run focused GREEN (`test_matrix_solve` + scalar solve regression) and then the complete suite; persist production only after both pass.\n9. Update this file with Task 6 RED/GREEN SHAs and counts before Task 7 matrix analysis.\n10. Do not invoke Codex and do not merge without explicit user authorization.\n\n## How to resume in a new conversation\n\nRead this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`. Tasks 0–5 are complete. Task 5 product commit `68f8a23` implements Pint-backed `QuantityMatrix`, per-entry dimensionality, homogeneous target-unit conversion, exact-zero adaptability, coordinate diagnostics, partial numerical matrices and `result(A)` parity; final verification was 27/27 focused plus 657/657 complete. The exact next action is Task 6 RED for exact `solve(A,b)`, shape/singularity diagnostics and dimensional structural solve acceptance. Never invoke Codex and never merge without explicit user approval.\n"""
text, count = re.subn(
    r"## Exact next step\n\n.*?## How to resume in a new conversation\n\n.*?\Z",
    new_next,
    text,
    flags=re.S,
)
assert count == 1

path.write_text(text, encoding="utf-8")
