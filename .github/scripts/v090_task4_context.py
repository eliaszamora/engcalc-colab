from pathlib import Path


path = Path("docs/project-context/CURRENT.md")
text = path.read_text(encoding="utf-8")

old = "_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–3 are complete with strict RED→GREEN evidence. Exact matrix constructors and core functions are implemented and fully regression-tested. Task 4 — matrix-valued user functions and matrix-aware existing CAS transforms — is the exact next step. Package/runtime version remains 0.8.0._"
new = "_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–4 are complete with strict RED→GREEN evidence. Matrix-valued user functions and entrywise CAS transforms are implemented and fully regression-tested. Task 5 — Pint-backed numerical matrices with per-entry dimensionality — is the exact next step. Package/runtime version remains 0.8.0._"
assert old in text
text = text.replace(old, new, 1)

anchor = "- Task 3 temporary GREEN workflow removed in `4c573b0637e639f29ac3e24e8b617ffd7051a160`; temporary implementation harness removed in `bf32b52da8bc752c22506c6d14f811ad260be5c8`.\n"
addition = anchor + "- Task 4 RED test commits: **`6ce1cdf4e9d7c140747308240a3efd3fc733438b`** and **`02b7369ad6403c560555a72223feca79e72313a7`**.\n- Task 4 GREEN product commit: **`501b6af2ef9eb228f7e69fb560479caa05f9dfb7`** (`feat: support matrix-valued CAS functions`).\n- Task 4 temporary RED workflow removed in `a3d5b311e42de417b091784a3688799249f92903`; final GREEN workflow removed in `ca85d897e0983c6746a2e8c0d435062b0d35f220`; implementation harness removed in `bd28e033bdf3a1ba6dbcc628886db1950d3dff6e`.\n"
assert anchor in text
text = text.replace(anchor, addition, 1)

text = text.replace("### Implemented 0.9.0 behavior through Task 3", "### Implemented 0.9.0 behavior through Task 4", 1)
anchor = "- Existing scalar behavior remains routed through the same engine and passes the complete regression suite.\n"
addition = anchor + "- Matrix-valued user functions preserve exact positional arity, simultaneous substitution, local-parameter shadowing and inverse-trig node semantics.\n- `simplify`, `expand`, `factor`, `subs`, `diff` and definite `integral` explicitly map entrywise over immutable matrices.\n- Matrix Piecewise differentiation remains entrywise and stores the union of explicit breakpoint metadata for later numeric evaluation.\n- Scalar symbolic functions such as `sin`, `cos`, `tan`, inverse trig, `sqrt`, `exp` and `log` reject whole-matrix arguments instead of silently introducing unintended matrix-function semantics.\n- `map_matrix_entries(...)` is the single immutable entrywise CAS mapping primitive; `substitute_symbolic_value(...)` centralizes scalar/matrix function substitution while preserving existing scalar behavior.\n"
assert anchor in text
text = text.replace(anchor, addition, 1)

old = "- Task 4 must add matrix-valued user functions and entrywise matrix-aware `simplify`, `expand`, `factor`, `subs`, `diff`, and definite `integral` while keeping scalar trig calls matrix-invalid.\n- Piecewise scalar cells inside matrices must remain differentiable entrywise; derivative breakpoint metadata must not be lost for matrix-valued user functions.\n- Matrix rendering/presentation has not yet been implemented; current work establishes symbolic truth before presentation.\n- Numerical/unit-aware matrices (`QuantityMatrix`) remain a later task in this same approved 0.9.0 plan.\n"
new = "- Task 5 must introduce immutable `QuantityMatrix` numerical outputs with per-entry Pint dimensionality, homogeneous target-unit conversion, exact-zero adaptability, coordinate-aware diagnostics and partial numeric matrix evaluation.\n- Matrix rendering/presentation has not yet been implemented; current work establishes symbolic and numeric truth before final presentation.\n- Numerical/unit-aware matrices (`QuantityMatrix`) are now the active next task in the approved 0.9.0 plan.\n"
assert old in text
text = text.replace(old, new, 1)

marker = "## Roadmap / active plan\n"
assert marker in text
before, after = text.split(marker, 1)
validation = """### 0.9.0 Task 4 RED/GREEN evidence

- Task 4 user-function tests were committed at **`6ce1cdf4e9d7c140747308240a3efd3fc733438b`** and matrix-calculus tests at **`02b7369ad6403c560555a72223feca79e72313a7`**, before Task 4 production code.
- RED Actions **`33324597889`**, job **`99292391302`**, CPython **3.13.15**: **2 failed, 13 passed in 3.64 s**.
- RED established two genuine missing contracts: `factor(A)` was not entrywise and scalar `sin(A)` was incorrectly accepted. The other 13 approved behaviors already happened to work through SymPy and were retained rather than artificially broken.
- RED artifact **`9735856775`**, digest **`sha256:33dbf248cab35c24c2051e77943d1e413fa8ca00f17bcada5772fe984f60d871`**.
- Final GREEN Actions **`33324742050`**, job **`99292774054`**, CPython **3.13.15**: compile check + `git diff --check` GREEN; **15/15 focused GREEN in 3.35 s**; **642/642 full GREEN in 126.22 s**.
- Product commit **`501b6af2ef9eb228f7e69fb560479caa05f9dfb7`** changed exactly `src/engcalc_colab/engine.py` and `src/engcalc_colab/matrix_core.py`: 70 additions, 10 deletions; no unrelated product files changed.
- GREEN logs artifact **`9735923490`**, digest **`sha256:d4afefbff29b0344d3f2fe1529bbd9c3450d3640a7ec8b3701c89e7ed3b19da9`**.
- Temporary Task 4 RED/GREEN workflows and implementation harness were removed after evidence was preserved.
- The only runner warning was GitHub Actions' Node 20 deprecation/forced Node 24 compatibility warning; it is not an EngCalc product failure.

"""
assert "### 0.9.0 Task 4 RED/GREEN evidence" not in before
text = before + validation + marker + after

text = text.replace("**IMPLEMENTATION ACTIVE — TASKS 0–3 COMPLETE, TASK 4 NEXT**", "**IMPLEMENTATION ACTIVE — TASKS 0–4 COMPLETE, TASK 5 NEXT**", 1)
text = text.replace("  - Task 4 matrix-valued user functions and matrix-aware existing CAS transforms: NEXT.\n", "  - Task 4 matrix-valued user functions and matrix-aware existing CAS transforms: COMPLETE, 15/15 focused + 642/642 full GREEN.\n  - Task 5 Pint-backed numerical matrices and partial numeric matrices: NEXT.\n", 1)

start = text.index("## Exact next step\n")
resume = text.index("## How to resume in a new conversation\n")
new_next = """## Exact next step

1. Add Task 5 RED tests in `tests/test_matrix_numeric.py` for homogeneous matrices, explicit common target-unit conversion, heterogeneous engineering stiffness matrices and per-cell dimensionality.
2. Add exact-zero adaptability and one-based coordinate diagnostic tests, including an incompatible dimensional sum that identifies the failing matrix cell.
3. Add Task 5 RED partial-evaluation tests in `tests/test_matrix_partial_numeric.py` for deterministic unresolved-symbol reporting, known Pint substitutions, `result(A)` parity and rejection of target-unit conversion while unresolved symbols remain.
4. Run only the new Task 5 tests and verify failures are due to the missing `QuantityMatrix`/matrix numeric route rather than malformed tests.
5. Only after observed RED, create immutable `QuantityMatrix`, `NumericMatrixEvaluationResult`, `PartialMatrixNumericEvaluationResult` and `NumericContext.evaluate_matrix(...)` without adding public arithmetic to `QuantityMatrix`.
6. Evaluate symbolic matrices cell-by-cell through existing scalar Pint logic, preserve per-entry dimensions and exact-zero adaptability, and annotate failures with one-based coordinates.
7. Integrate matrix handling into `numeric(...)` / `result(...)` without altering scalar numeric behavior.
8. Run focused GREEN (`test_matrix_numeric`, `test_matrix_partial_numeric`, `test_numeric_context`) and then the complete suite; persist production only after both pass.
9. Update this file with Task 5 RED/GREEN SHAs and counts before Task 6 exact `solve(A,b)`.
10. Do not invoke Codex and do not merge without explicit user authorization.

"""
new_resume = """## How to resume in a new conversation

Read this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`. Tasks 0–4 are complete. Task 4 product commit `501b6af2ef9eb228f7e69fb560479caa05f9dfb7` makes matrix-valued functions and approved CAS transforms explicitly matrix-aware; final verification was 15/15 focused plus 642/642 complete. The exact next action is Task 5 RED for Pint-backed `QuantityMatrix`, heterogeneous per-entry units, exact-zero adaptability, coordinate diagnostics and partial numeric matrices. Never invoke Codex and never merge without explicit user approval.
"""
text = text[:start] + new_next + new_resume

path.write_text(text, encoding="utf-8")
