# EngCalc Current Project Context

_Last updated: 2026-08-29 after PR #26 was created and inspected, the EngCalc 0.6.2 distribution gate passed, temporary validation workflows were removed, and the master roadmap was aligned to the actual 0.6.2 numbering._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` remains EngCalc **0.6.1** at `1543e6ca5b0d631d5dea6922c6d4a2d817371448`.
- Active release branch: `feature/v0.6.2-numeric-ergonomics`.
- Candidate version: **0.6.2** in both `pyproject.toml` and `src/engcalc_colab/__init__.py`.
- Release metadata commit: `05ad676d70eeca2e36a27beade741fcc017f3cb2`.
- Final validated distribution-gate tree: `6343844965cce707d60dd523da282b70c6dcab78`.
- Temporary 0.6.2 validation workflow was removed afterward in `03049db2d70a97b07392a39fb32f3d5a13808020`; this cleanup changed no product or test file.
- PR **#26 — `release: EngCalc 0.6.2 numeric ergonomics`** is open from `feature/v0.6.2-numeric-ergonomics` into `main`.
- PR #26 is non-draft, not merged and GitHub reports it mergeable.
- The PR changed-file set was inspected: 13 expected product/docs/test files and no temporary workflow remain.
- Do **not** merge PR #26 without explicit user approval.

## Approved behavior

### 0.6.1 presentation baseline

- `numeric(...)` renders formula → explicit numerical substitution → final result.
- `result(...)` renders formula → final result using the same numerical engine.
- Semantic MathJax spacing remains 4 pt for wrapped continuation rows, 8 pt for a new stage/consecutive source result, and 16 pt after an explicit blank source line.
- Structural positive moment remains plotted downward.
- Compact plot/envelope characteristic annotations remain `(x, y)` with no boxes, duplicated units or leader lines.
- User-provided real-Colab visual evidence on 2026-08-29 confirmed the intended `numeric(...)`/`result(...)` hierarchy and spacing; that visual QA is accepted.

### 0.6.2 numeric ergonomics and diagnostics

- A complete unit-bearing/numeric expression may be passed directly to a one-argument user function in `numeric(...)` and `result(...)`.
- Required examples now supported include:
  - `numeric(M(2.5*m))`;
  - `numeric(V(L/2))` when `L` has a numerical value;
  - `numeric(R(4*tonf/m))`;
  - `numeric(M(0*m), kN*m)` without losing the length dimension of the zero argument.
- A lone unassigned name intentionally remains symbolic, so `numeric(M(x))` / `result(M(x))` continue to produce partial numerical functions.
- The bridge is AST-level: complete function arguments are evaluated in the restricted Pint-backed `NumericContext` before SymPy can erase units; intentionally free names remain symbolic.
- `result(...)` reuses the `numeric(...)` evaluation path; only presentation differs.
- Corrective diagnostics now distinguish unknown numeric names, unresolved numerical symbols and incompatible units in evaluated user functions while preserving the existing public exception hierarchy.
- Existing `solve(expr, unknown)` / explicit `eq(...)` behavior is preserved.

## Open issues / user feedback

- No known functional regression or P1/P2 review blocker is open for the 0.6.2 candidate.
- The final PR code/diff inspection found no reason to invalidate the completed distribution gate.
- The direct dimensional-zero call may render the mathematical call at the simplified coordinate `M(0)` while retaining the correct dimensional Pint value internally; this is mathematically consistent and is not a release blocker. The authoritative 0.6.2 requirement is preservation of numeric dimensions/evaluation, which is covered by tests and the installed-wheel smoke.

## Validation evidence

### TDD and persisted implementation

- RED contract stage reproduced the expected symbolic/numeric crossing failures before production changes.
- The dimensional-zero acceptance exposed the important `0*m -> 0` SymPy simplification boundary; the implementation was corrected to resolve complete arguments from their AST before symbolic simplification.
- Persisted implementation verification on the release branch passed **10 focused tests** and **262/262 complete source tests** before release metadata closure.
- Release-metadata closure then passed **30/30 focused tests** and **262/262 complete source tests** before committing version 0.6.2.

### Final 0.6.2 distribution gate

GitHub Actions run **`33228562198`** on head **`6343844965cce707d60dd523da282b70c6dcab78`** completed successfully:

- release metadata: PASS (`0.6.2` in package and `pyproject.toml`);
- focused 0.6.2 contracts: **30 passed in 2.13 s**;
- complete source suite: **262 passed in 55.82 s**;
- wheel `engcalc_colab-0.6.2-py3-none-any.whl`: built successfully with metadata version 0.6.2;
- clean virtual-environment wheel installation: PASS;
- smoke from `/tmp` with empty `PYTHONPATH`: PASS, importing from `site-packages` and exercising direct `0*m`, partial `M(x)` and `result(M(2.5*m), kN*m)` behavior;
- source-free complete suite against the installed wheel: **262 passed in 54.14 s**;
- repeated complete source suite: **262 passed in 54.47 s**;
- validated wheel artifact: `engcalc-colab-0.6.2-wheel`, artifact ID **9707745104**, ZIP digest `sha256:50d4d465314aa3b5e1fa4076e24750ce484f7fc91047329dab8997fcded6bd75`.

### Chain of custody after the gate

- Comparing validated tree `6343844965cce707d60dd523da282b70c6dcab78` to the pre-final-context PR head showed only:
  - removal of `.github/workflows/v062-numeric-ergonomics.yml`;
  - update of `docs/project-context/CURRENT.md`.
- No `src/` or `tests/` file changed after the validated distribution gate.
- Subsequent updates to `CURRENT.md` are documentation-only and do not alter the validated product/test tree.

## Roadmap / active plan

- The master roadmap remains on branch `planning/engcalc-evolution-roadmap`:
  - `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`
  - `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`
- Roadmap alignment was completed on 2026-08-29 in commit `c46ec4047e1fbf35cde1ec1991d75f8809221f11`.
- The spec now explicitly records that actual 0.6.1 was the visual/presentation release and the unchanged numeric-ergonomics milestone is **0.6.2**.
- The implementation plan now uses Task 1 = **0.6.2**, branch `feature/v0.6.2-numeric-ergonomics`, version bump/commit text 0.6.2, and dependency graph `0.6.2 → 0.7.0`.
- Milestone **0.7.0 — scalar engineering mathematics** remains next (`sqrt`, trig/inverse trig, `exp`, `log`, `pi` with explicit unit-aware rules).
- The temporary roadmap-alignment workflow was removed after the documentation commit.

## PR #26 inspection

- Base: `main` at `1543e6ca5b0d631d5dea6922c6d4a2d817371448` at inspection time.
- Head branch: `feature/v0.6.2-numeric-ergonomics`.
- GitHub reports `mergeable: true`.
- PR is open, non-draft and not merged.
- Changed files are the expected 13 files:
  - `README.md`;
  - `docs/project-context/CURRENT.md`;
  - `pyproject.toml`;
  - `src/engcalc_colab/__init__.py`;
  - `src/engcalc_colab/engine.py`;
  - `src/engcalc_colab/errors.py`;
  - `src/engcalc_colab/numeric.py`;
  - `tests/test_diagnostics.py`;
  - `tests/test_numeric_function_arguments.py`;
  - `tests/test_numeric_function_magic_acceptance.py`;
  - `tests/test_packaging.py`;
  - `tests/test_parser.py`;
  - `tests/test_release_version_v062.py` (renamed from the 0.6.1 release contract).
- No temporary `.github/workflows/v062-numeric-ergonomics.yml` file is present in the PR diff.
- Key implementation, diagnostics and acceptance patches were inspected after the gate; no release-blocking defect was identified.

## Exact next step

1. Re-read PR #26 immediately before any integration action and confirm its head/base/mergeability have not moved.
2. Wait for the user's **explicit authorization to merge PR #26**. Do not infer authorization from general instructions to continue work.
3. Once explicitly authorized, merge using the repository's established release strategy with an expected-head guard where available.
4. Verify merged `main` tree/state; if tree identity with the validated product cannot be established, rerun the appropriate release verification.
5. Update `docs/project-context/CURRENT.md` on merged `main` to record 0.6.2 closure.
6. Begin **0.7.0** only from the merged-and-documented `main` baseline.

## How to resume in a new conversation

Read this file first, then fetch PR #26 and verify current head/base/mergeability. The 0.6.2 product/test tree is already fully distribution-tested; changes after the gate are workflow cleanup and context documentation only. The roadmap numbering is already aligned. Do not merge PR #26 without explicit user approval. After merge, update `main` context and start 0.7.0 from merged `main`.
