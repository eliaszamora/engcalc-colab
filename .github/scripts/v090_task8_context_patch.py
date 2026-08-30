from pathlib import Path

path = Path("docs/project-context/CURRENT.md")
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    assert count == 1, (old[:160], count)
    text = text.replace(old, new, 1)


replace_once(
    "_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–7 are complete with strict RED→GREEN evidence. Exact rank/RREF/Frobenius norm/eigen analysis now includes deterministic result models and provenance-aware common-scale numerical guards. Task 8 — native MathJax matrix rendering and numerical presentation — is the exact next step. Package/runtime version remains 0.8.0._",
    "_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–8 are complete with strict RED→GREEN evidence. Native MathJax now renders symbolic, partial and numerical matrices plus matrix-analysis result models through the existing EngCalc presentation path. Task 9 — Piecewise/table/plot integration and engineering diagnostics — is the exact next step. Package/runtime version remains 0.8.0._",
)

replace_once(
    "- Task 7 temporary RED/GREEN workflows, implementation harness, residual Task 6 context script and self-cleanup workflow were removed in **`fdf9f6fcb3acac7f8c66f2a69ad9fdcbf595612c`**.\n",
    "- Task 7 temporary RED/GREEN workflows, implementation harness, residual Task 6 context script and self-cleanup workflow were removed in **`fdf9f6fcb3acac7f8c66f2a69ad9fdcbf595612c`**.\n"
    "- Task 8 accepted corrected RED test head: **`a24b38d87cb5268f4088f89813da03d9242c6a0a`**.\n"
    "- Task 8 GREEN product commit: **`37c0cdb79b2ae4c0b2a039082a50260fda668700`** (`feat: render matrix calculations with MathJax`).\n"
    "- Task 8 temporary RED/GREEN workflows and apply/escape harnesses were removed in cleanup commits **`40c17e47c3eec775c991618b801f326a48e524c1`**, **`37cfc0b2e9577c2354edfc5e667eb440e782e93d`**, **`2b34fca73b2e2db8d44978c28bbd042c4a1428d2`** and **`04669837755ff276a6e0ccaa1722a0aa73ac1f47`**.\n",
)

replace_once(
    "### Implemented 0.9.0 behavior through Task 7",
    "### Implemented 0.9.0 behavior through Task 8",
)

replace_once(
    "- Heterogeneous physical source matrices are rejected for numerical `rank`, `rref`, `norm`, `eigenvals` and `eigenvects` with operation-specific common-scale diagnostics; units are never silently stripped.\n",
    "- Heterogeneous physical source matrices are rejected for numerical `rank`, `rref`, `norm`, `eigenvals` and `eigenvects` with operation-specific common-scale diagnostics; units are never silently stripped.\n"
    "- Symbolic row, column and general matrices render as native MathJax matrix structures through the existing engineering renderer; raw `Matrix([[...` representations are not exposed.\n"
    "- Homogeneous `QuantityMatrix` output factors one compatible common display unit outside the matrix while rendering per-cell magnitudes with active precision/zero tolerance; adaptable zeros remain neutral.\n"
    "- Heterogeneous numerical matrices retain the Pint unit of each cell and never fabricate one matrix-wide unit.\n"
    "- Matrix `numeric(...)` preserves formula → substitution → final numerical stages; `result(...)` omits the substitution stage; partial numerical matrices show formula/substitution only and never fabricate a final `QuantityMatrix`.\n"
    "- `MatrixShape`, eigenvalue multiplicities and eigenvector sets render deterministically; eigenvectors remain native matrices and homogeneous numerical eigenvalues retain physical units.\n"
    "- `%%eng` continues to use the same `render_aligned_results` source-order MathJax path for scalar and matrix results; no parallel matrix display system was introduced.\n",
)

old_open = """- Task 8 must add native MathJax rendering for symbolic, partial and numerical matrices plus deterministic rendering for shape/eigen result models.
- Matrix rendering/presentation is now the active next task; symbolic and numeric matrix truth is established through Task 7.
- Task 8 must extend the existing engineering renderer rather than introduce a parallel display system.
- Task 9 Piecewise/table/plot integration and end-to-end structural acceptance remains after Task 8 rendering.
"""
new_open = """- Task 9 must close Piecewise-in-matrix-cell integration, indexed scalar table/plot integration, whole-matrix scalar-API rejection and end-to-end structural worksheet acceptance.
- Task 9 must audit mandatory matrix diagnostics so backend SymPy/Pint exceptions do not leak through the EngCalc DSL.
- Whole-matrix `table`, `plot` and `envelope` remain deliberately out of scope; only indexed scalar matrix responses integrate with those scalar APIs.
- Task 10 release/version/wheel validation remains after Task 9 acceptance.
"""
replace_once(old_open, new_open)

roadmap_anchor = "## Roadmap / active plan\n"
assert text.count(roadmap_anchor) == 1
validation = """### 0.9.0 Task 8 RED/GREEN evidence

- Task 8 renderer/magic tests were written before accepted production code. The corrected clean RED head was **`a24b38d87cb5268f4088f89813da03d9242c6a0a`**.
- Corrected RED Actions **`33330073653`**, job **`99306945957`**, CPython **3.13.15**: **13 failed, 3 passed in 4.36 s**. The three passes were pre-existing SymPy matrix-printing capability; the 13 failures were the missing matrix numeric/partial/shape/eigen/`%%eng` presentation paths.
- Corrected RED artifact **`9737377959`**, digest **`sha256:a7c0508b5c17717c2d5b7cc87f8ba889f99e3a703920f671a309b128e481f9c5`**.
- A prior candidate run (`33329742934`) exposed a CI harness defect: `pytest | tee` lacked `pipefail`, so pytest failures were swallowed and candidate commit `08f4906da33557ef66c66407cb411b90d80179f3` was created prematurely. That commit was explicitly invalidated and reverted in **`1b9aedebcdde0c598244178014e6d4fe799ce533`** before re-running RED/GREEN. Four assertions were then corrected where they overconstrained string substrings, canonical heterogeneous units, or a nonexistent partial-final numeric stage; test intent remained aligned with the approved spec.
- Final GREEN Actions **`33330195507`**, job **`99307284768`**, CPython **3.13.15**, with `set -o pipefail`: compile check + `git diff --check` + exact renderer-only patch audit GREEN; **65/65 focused GREEN in 11.59 s**; **700/700 full GREEN in 117.35 s**.
- Product commit **`37c0cdb79b2ae4c0b2a039082a50260fda668700`** (`feat: render matrix calculations with MathJax`) changed exactly one production file: `src/engcalc_colab/renderer.py` (**251 additions, 4 deletions**).
- GREEN logs artifact **`9737440675`**, digest **`sha256:c0531c7c1bb334aeaa8264b82af11d6351bd64fa23b4a808ae6f4bac1cfe0d5d`**.
- Task 8 RED/GREEN workflows and apply/escape harnesses were removed after evidence preservation; no product source changed during cleanup.
- The runner's Node 20 deprecation/forced Node 24 warning remains infrastructure-only and is not an EngCalc product failure.

"""
text = text.replace(roadmap_anchor, validation + roadmap_anchor, 1)

replace_once(
    "- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–7 COMPLETE, TASK 8 NEXT**.",
    "- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–8 COMPLETE, TASK 9 NEXT**.",
)
replace_once(
    "  - Task 8 native MathJax rendering for symbolic/partial/numerical matrices and analysis models: NEXT.\n",
    "  - Task 8 native MathJax rendering for symbolic/partial/numerical matrices and analysis models: COMPLETE, 65/65 focused + 700/700 full GREEN.\n"
    "  - Task 9 Piecewise/table/plot integration, diagnostics and end-to-end structural acceptance: NEXT.\n",
)

start = text.index("## Exact next step\n")
end = text.index("## How to resume in a new conversation\n")
new_next = """## Exact next step

1. Add Task 9 RED tests in `tests/test_matrix_acceptance.py`, `tests/test_matrix_integration.py` and `tests/test_matrix_diagnostics.py` before changing production.
2. Verify Piecewise scalar expressions inside matrix cells evaluate entrywise, including dimensional-zero semantics.
3. Verify indexed scalar matrix responses such as `K(x)[1,1]` flow through existing scalar `table(...)` and `plot(...)`; whole matrices passed to `table`, `plot` or `envelope` must fail with a concise scalar-response diagnostic.
4. Add one canonical end-to-end structural `%%eng` worksheet with numerical material data, multiline stiffness matrix, load vector, `u = solve(K,F)`, `numeric(K)` and `numeric(u)`, preserving source-order MathJax and no traceback.
5. Cover every mandatory diagnostic category: unclosed/inconsistent/nested literals, shape mismatch, invalid exponent/index, singular inverse, numeric coordinate incompatibility, heterogeneous target unit, non-unique solve and heterogeneous guarded analysis.
6. Run the Task 9 tests RED before production changes, then implement only missing integration/diagnostic glue; do not broaden scalar table/plot/envelope APIs to whole matrices.
7. Update README with approved Matrix/CAS syntax/current limitations while runtime version remains 0.8.0.
8. Run the full 0.9.0 focused acceptance set from the implementation plan, then the complete suite; persist production only after both gates pass.
9. Update this file with exact Task 9 RED/GREEN evidence before Task 10 release/version/wheel validation.
10. Do not invoke Codex and do not merge without explicit user authorization.

"""
text = text[:start] + new_next + text[end:]

resume_start = text.index("Read this file first.", text.index("## How to resume in a new conversation"))
text = text[:resume_start] + (
    "Read this file first. EngCalc 0.8.0 is integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. "
    "Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`. Tasks 0–8 are complete. "
    "Task 8 product commit `37c0cdb79b2ae4c0b2a039082a50260fda668700` adds native MathJax rendering for symbolic, partial and numerical matrices plus deterministic shape/eigen presentation; final verification was 65/65 focused and 700/700 complete. "
    "The exact next action is Task 9 RED for Piecewise-cell integration, indexed scalar table/plot integration, whole-matrix scalar-API diagnostics and canonical structural worksheet acceptance. "
    "Never invoke Codex and never merge without explicit user approval.\n"
)

path.write_text(text, encoding="utf-8")
