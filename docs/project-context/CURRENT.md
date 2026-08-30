# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 Piecewise Task 1 is complete on the isolated feature branch. Restricted Piecewise grammar and symbolic SymPy construction are GREEN with 506/506 tests. Task 2 now begins with Pint-aware comparisons, numeric branch selection and dimensional-zero inheritance. The user also approved moving the matrix/CAS milestone immediately after Piecewise._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated branch: `main`.
- Current implementation branch: **`feature/v0.8.0-piecewise`**.
- Feature branch base: **`main@79befeeb07364f4b6b78d2e6e55ad40258ef0da2`**.
- Package/runtime version remains **0.7.2** during Piecewise development.
- Approved Piecewise spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- Approved Piecewise implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md`.
- The old `planning/v0.8.0-piecewise` branch is retained, but it is 84 commits behind the integrated `main`; it must not be merged into the implementation branch. Only its approved spec/plan blobs were copied.
- Temporary branch CI: `.github/workflows/v080-piecewise-validation.yml`; remove before release closure unless intentionally retained.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.

## Approved behavior

### Existing baseline that Piecewise must preserve

- `%%eng` narrative and presentation polish are merged.
- `plot(...)` / `envelope(...)` support approved `title`, `xlabel`, `ylabel` overrides.
- Dense characteristic clusters use the accepted compact summary; sparse clusters remain inline.
- Positive structural moment remains plotted downward.
- Multi-argument functions, partial numeric evaluation, scalar math and engineering tables remain unchanged unless the approved Piecewise spec explicitly composes with them.

### 0.8.0 Piecewise contract

- Primary form: `piecewise(value_1, condition_1, ..., default_value)` with a mandatory default.
- Conditions are restricted to one direct interval variable compared with `<`, `<=`, `>`, or `>=` against a breakpoint expression that does not contain that variable.
- General comparisons/booleans remain unavailable outside Piecewise condition positions.
- SymPy `Piecewise`/relational objects are the symbolic source of truth; Pint remains the numeric/unit source of truth.
- Exact dimensionless zero may inherit a compatible dimensional unit; nonzero dimensionless values may not silently mix with dimensional quantities.
- Tables keep exactly the requested row count; Piecewise breakpoints do not add table rows.
- Plot/envelope keeps the 201-point base grid and augments it with resolvable explicit Piecewise breakpoints.
- Plot polylines split at Piecewise transitions; no fictitious connector across a jump.
- `diff(...)` is branchwise with no automatic `DiracDelta`; explicit transitions are conservatively derivative-undefined for numeric evaluation.
- Piecewise rendering should use native MathJax cases.

### Approved roadmap reprioritization

- After Piecewise, EngCalc will prioritize a **calculator/CAS-style vectors, matrices and linear-systems milestone** before the exact-analysis milestones.
- That matrix milestone must have a dedicated design/spec before production work and must cover exact symbolic matrices, numerical/unit-aware matrices, rendering, matrix algebra and linear systems.
- To keep version ordering coherent, the working roadmap is now: `0.8.0 Piecewise` → `0.9.0 vectors/matrices/linear systems` → `0.9.1 exact-first extrema/roots/intersections` → `0.9.2 exact envelopes/governing intervals` → `0.9.3 named response cases/combinations` → `0.10.x engineering verification` → `1.0.0` stabilization.
- References to old `0.8.1`/`0.8.2` labels inside the already-approved Piecewise spec describe deferred functional scope; the functional boundary is unchanged even though roadmap numbering is reprioritized.

## Open issues / user feedback

- Multiline ordinary function-call parsing remains a later ergonomics item.
- `no_vertical_scroll()` Colab ergonomics remains outside Piecewise.
- Matrix/CAS production work must not be mixed into the Piecewise branch.
- Matrix support is intended to approach a TI-Nspire CX CAS workflow while adding engineering-specific unit safety, including a later explicit design decision for heterogeneous-unit structural matrices.

## Validation evidence

- Integrated `main` post-PR-#30 gate: **484/484 passed in 99.80 s** on Actions `33298959230`.
- Piecewise execution branch created exactly from `main@79befeeb07364f4b6b78d2e6e55ad40258ef0da2`.
- Approved planning docs imported in commit `e0a677e95a2d5352fe2bbce8898573eb70f1d6fa` without merging planning history.
- Baseline CI commit: `2ad58c9d20910894f13701a2e2207f0301488a4d`.
- Baseline Actions run `33299317560`, job `99224326960`: package version check **0.7.2 PASS** and complete suite **484/484 passed in 85.83 s** on Python 3.13.15.
- Parser RED: commit `483ccc6a6b633cf7fda07567bad313aafeed1d5a` with symbolic tests added later produced the expected missing-feature failures; parser-only RED earlier was **8 failed, 493 passed**.
- Parser GREEN: restricted Piecewise grammar, reserved `piecewise`, and contextual comparison whitelist passed **501/501**.
- Symbolic RED: Actions run `33299843672`, job `99225774691`: **4 failed, 502 passed**; all four failures were the expected `unsupported syntax 'Compare'` at Piecewise symbolic construction.
- Symbolic implementation: `src/engcalc_colab/piecewise.py` plus minimal `_Evaluator` Piecewise dispatch/construction in `engine.py`; temporary patch workflow was removed immediately after applying the exact engine edit.
- Task 1 authoritative GREEN: commit `a935dd7d9c2bb786caede1bb28274fde28bb77f8`, Actions run `33300087110`, job `99226465958`: package version check **0.7.2 PASS** and complete suite **506/506 passed in 68.84 s** on Python 3.13.15.
- The implementation plan's old expected baseline of 454 tests is superseded by 484 because narrative/presentation/dense-summary tests were merged before Piecewise execution; this is an explained baseline update, not a regression.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary work:** COMPLETE + merged + 484-test baseline retained.
- **0.8.0 Piecewise:** ACTIVE.
  - Task 0 baseline/branch setup: COMPLETE.
  - Task 1 restricted grammar + symbolic construction: COMPLETE, **506/506 GREEN**.
  - Task 2 Pint-aware relations + numeric Piecewise evaluation + dimensional-zero inheritance: ACTIVE NEXT.
  - Tasks 3+ partial numeric rendering, tables, plots/envelopes, calculus and acceptance: pending.
- **0.9.0 vectors / matrices / linear systems:** NEXT MAJOR MILESTONE AFTER PIECEWISE; design/spec gate required.
- **0.9.1 exact-first extrema / roots / intersections:** planned after matrix/CAS core.
- **0.9.2 exact envelopes / governing intervals:** planned.
- **0.9.3 named response cases / combinations:** planned.
- **0.10.0 / 0.10.1 engineering verification:** planned.
- **1.0.0 API stabilization / release engineering:** planned.

## Exact next step

1. Create **tests only** in `tests/test_piecewise_numeric.py` for compatible dimensional comparisons, dimensional-zero comparisons, invalid incompatible comparisons, branch selection, target-unit conversion and branch-unit compatibility.
2. Run the full feature workflow and confirm RED specifically because `NumericContext` does not yet evaluate SymPy relational/Piecewise nodes.
3. Only after verified RED, minimally extend `numeric.py` with Pint-aware relational normalization, Piecewise branch evaluation, exact-zero inheritance and the restricted Min/Max support required by the approved plan.
4. Run focused-equivalent/full-suite GREEN through the branch workflow before moving to Task 3.
5. Do not write matrix production code on this branch and do not merge to `main` without explicit user approval.

## How to resume in a new conversation

Read this file first. `main` remains integrated and machine-green at the presentation baseline. Active development is `feature/v0.8.0-piecewise`, based exactly on `main@79befeeb...`. Piecewise Task 1 is complete: restricted grammar and symbolic `sympy.Piecewise` construction are implemented; Actions `33300087110` verified **506/506 tests** with package version 0.7.2. The exact next action is Task 2 numeric RED tests in `tests/test_piecewise_numeric.py`, followed by Pint-aware relation/Piecewise evaluation only after the RED is observed. The user also approved reprioritizing matrices/CAS immediately after Piecewise, with roadmap numbering updated to 0.9.0 matrices, then 0.9.1–0.9.3 exact-analysis/cases milestones. Never invoke Codex without explicit authorization.