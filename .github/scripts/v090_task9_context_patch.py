from pathlib import Path

path = Path("docs/project-context/CURRENT.md")
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    assert count == 1, (old[:160], count)
    text = text.replace(old, new, 1)


replace_once(
    "_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–8 are complete with strict RED→GREEN evidence. Native MathJax now renders symbolic, partial and numerical matrices plus matrix-analysis result models through the existing EngCalc presentation path. Task 9 — Piecewise/table/plot integration and engineering diagnostics — is the exact next step. Package/runtime version remains 0.8.0._",
    "_Last updated: 2026-08-30 — EngCalc 0.8.0 remains integrated in `main`. The approved 0.9.0 Matrix/CAS plan is executing inline on `feature/v0.9.0-matrix-cas`. Tasks 0–9 are complete with strict RED→GREEN evidence. Matrix Piecewise cells, indexed scalar table/plot/envelope integration, engineering diagnostics and the canonical structural worksheet are now accepted end to end. Task 10 — release/version/wheel validation for 0.9.0 — is the exact next step. Package/runtime version remains 0.8.0 until that release-closing task._",
)

replace_once(
    "- Task 8 temporary RED/GREEN workflows and apply/escape harnesses were removed in cleanup commits **`40c17e47c3eec775c991618b801f326a48e524c1`**, **`37cfc0b2e9577c2354edfc5e667eb440e782e93d`**, **`2b34fca73b2e2db8d44978c28bbd042c4a1428d2`** and **`04669837755ff276a6e0ccaa1722a0aa73ac1f47`**.\n",
    "- Task 8 temporary RED/GREEN workflows and apply/escape harnesses were removed in cleanup commits **`40c17e47c3eec775c991618b801f326a48e524c1`**, **`37cfc0b2e9577c2354edfc5e667eb440e782e93d`**, **`2b34fca73b2e2db8d44978c28bbd042c4a1428d2`** and **`04669837755ff276a6e0ccaa1722a0aa73ac1f47`**.\n"
    "- Task 9 accepted RED test head: **`5ea9caa9caa38710e0f380ee842569c8a85f650f`**; RED workflow commit: **`15e82fbab9f9a7fd84d3ec1074941689821734c7`**.\n"
    "- Task 9 GREEN product commit: **`6bd29dbb8fb417667f1fb1e264d9cbd146a2bbe0`** (`feat: integrate EngCalc matrix CAS workflows`).\n"
    "- Task 9 temporary RED/GREEN workflows and implementation harness were removed in **`83240acde126ffad3ce547bf3205b157ee3bf3cf`**, **`7c6f1cd1c18faeb6ec8780f26712d51174f9ab1e`** and **`70adb774b70807d146cebc173ef946da43f3ca73`**.\n",
)

replace_once(
    "### Implemented 0.9.0 behavior through Task 8",
    "### Implemented 0.9.0 behavior through Task 9",
)

replace_once(
    "- `%%eng` continues to use the same `render_aligned_results` source-order MathJax path for scalar and matrix results; no parallel matrix display system was introduced.\n",
    "- `%%eng` continues to use the same `render_aligned_results` source-order MathJax path for scalar and matrix results; no parallel matrix display system was introduced.\n"
    "- Piecewise scalar expressions inside matrix cells evaluate entrywise through matrix-valued user functions, including exact breakpoint ownership and dimensional-zero semantics.\n"
    "- Indexed scalar matrix responses such as `K(x)[1,1]` flow through the existing scalar `table`, `plot` and `envelope` APIs without broadening those APIs to whole matrices.\n"
    "- Whole-matrix `table`, `plot` and `envelope` inputs are rejected before scalar numeric sampling with concise operation-specific `response must be scalar` diagnostics.\n"
    "- The canonical structural worksheet runs in one `%%eng` cell with numerical material data, multiline stiffness/load matrices, exact `solve(K,F)`, `numeric(K)` and `numeric(u)` in source-order MathJax without traceback.\n"
    "- README now documents the 0.9.0 Matrix/CAS development syntax, one-based indexing, exact `solve(A,b)`, `numeric(A)`, per-entry dimensional semantics and whole-matrix table/plot limitation while runtime remains 0.8.0.\n",
)

old_open = """- Task 9 must close Piecewise-in-matrix-cell integration, indexed scalar table/plot integration, whole-matrix scalar-API rejection and end-to-end structural worksheet acceptance.
- Task 9 must audit mandatory matrix diagnostics so backend SymPy/Pint exceptions do not leak through the EngCalc DSL.
- Whole-matrix `table`, `plot` and `envelope` remain deliberately out of scope; only indexed scalar matrix responses integrate with those scalar APIs.
- Task 10 release/version/wheel validation remains after Task 9 acceptance.
"""
new_open = """- Task 10 must bump package/runtime/documentation contracts from 0.8.0 to 0.9.0 only after a version RED is observed.
- Task 10 must build the real wheel, validate wheel metadata and SHA-256, then verify from a clean external environment with `src/` excluded.
- The installed-wheel/source-free suite must pass before a release PR is opened.
- Whole-matrix `table`, `plot` and `envelope` remain deliberately out of scope; only indexed scalar matrix responses integrate with those scalar APIs.
"""
replace_once(old_open, new_open)

roadmap_anchor = "## Roadmap / active plan\n"
assert text.count(roadmap_anchor) == 1
validation = """### 0.9.0 Task 9 RED/GREEN evidence

- Task 9 acceptance/integration contracts were persisted before production in `tests/test_matrix_acceptance.py`, `tests/test_matrix_integration.py` and the extended `tests/test_matrix_diagnostics.py`; accepted test head **`5ea9caa9caa38710e0f380ee842569c8a85f650f`**.
- RED Actions **`33330893770`**, job **`99309133015`**, CPython **3.13.15**: **4 failed, 25 passed in 4.65 s**. The 25 passes established that Piecewise matrix cells, indexed scalar table/plot/envelope behavior, canonical structural worksheet and mandatory historical diagnostics were already correct. The four genuine gaps were README Matrix/CAS documentation plus concise whole-matrix rejection messages for `table`, `plot` and `envelope`.
- RED artifact **`9737606835`**, digest **`sha256:6c062c92d15fb2de3c3df43362c2c361951714f4a48e30cd79ab10a9d4da2d2c`**.
- Final GREEN Actions **`33331638868`**, job **`99311093809`**, CPython **3.13.15**, with `set -o pipefail`: compile check + `git diff --check` + exact two-file patch audit GREEN; **29/29 Task 9 focused GREEN in 6.24 s**; **164/164 Matrix/CAS acceptance GREEN in 27.38 s**; **721/721 complete suite GREEN in 139.26 s**.
- Product commit **`6bd29dbb8fb417667f1fb1e264d9cbd146a2bbe0`** (`feat: integrate EngCalc matrix CAS workflows`) changed exactly `README.md` (+16) and `src/engcalc_colab/engine.py` (+12), with no deletions and no unrelated product files.
- GREEN logs artifact **`9737847921`**, digest **`sha256:539dddd248c7f9f2c5e2a138adeb9838d2a1f7d37b1de55d6c125b0055d5bd9a`**.
- Post-validation compare `6bd29dbb...` → `70adb774...` contains only deletion of the Task 9 RED/GREEN workflows and implementation harness; no `src/`, README or product-test changes occurred after the validated product tree.
- The runner's Node 20 deprecation/forced Node 24 warning remains infrastructure-only and is not an EngCalc product failure.

"""
text = text.replace(roadmap_anchor, validation + roadmap_anchor, 1)

replace_once(
    "- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–8 COMPLETE, TASK 9 NEXT**.",
    "- **0.9.0 vectors / matrices / linear systems:** **IMPLEMENTATION ACTIVE — TASKS 0–9 COMPLETE, TASK 10 RELEASE VALIDATION NEXT**.",
)
replace_once(
    "  - Task 9 Piecewise/table/plot integration, diagnostics and end-to-end structural acceptance: NEXT.\n  - Package/runtime version remains 0.8.0 until the release-closing task.\n",
    "  - Task 9 Piecewise/table/plot integration, diagnostics and end-to-end structural acceptance: COMPLETE, 29/29 focused + 164/164 Matrix/CAS acceptance + 721/721 full GREEN.\n"
    "  - Task 10 release 0.9.0, installed-wheel/source-free validation and release PR: NEXT.\n"
    "  - Package/runtime version remains 0.8.0 until Task 10's version GREEN.\n",
)

start = text.index("## Exact next step\n")
end = text.index("## How to resume in a new conversation\n")
new_next = """## Exact next step

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

"""
text = text[:start] + new_next + text[end:]

resume_start = text.index("Read this file first.", text.index("## How to resume in a new conversation"))
text = text[:resume_start] + (
    "Read this file first. EngCalc 0.8.0 remains integrated on `main@9b90014fa59014eb9e831c71c7f7f2a35dfeb86d`. "
    "Matrix/CAS implementation is active on `feature/v0.9.0-matrix-cas`. Tasks 0–9 are complete. "
    "Task 9 product commit `6bd29dbb8fb417667f1fb1e264d9cbd146a2bbe0` closes Piecewise-cell, indexed scalar table/plot/envelope, whole-matrix diagnostics, README Matrix/CAS documentation and the canonical structural worksheet; final verification was 29/29 focused, 164/164 Matrix/CAS acceptance and 721/721 complete. "
    "The exact next action is Task 10 version RED for the 0.9.0 package/release contract, followed by wheel and source-free validation. "
    "Never invoke Codex and never merge without explicit user approval.\n"
)

path.write_text(text, encoding="utf-8")
