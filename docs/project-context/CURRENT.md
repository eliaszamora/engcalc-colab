# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 Piecewise Task 2 is complete on the isolated feature branch. Pint-aware relations, lazy numeric Piecewise branch selection, dimensional-zero inheritance and restricted unit-aware Min/Max are GREEN with 518/518 tests. Task 3 is next: structured partial `numeric(...)` / `result(...)` support and native Piecewise rendering. The user also approved moving the matrix/CAS milestone immediately after Piecewise._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated branch: `main`.
- Current implementation branch: **`feature/v0.8.0-piecewise`**.
- Feature branch base: **`main@79befeeb07364f4b6b78d2e6e55ad40258ef0da2`**.
- Latest machine-validated product tree before this documentation-only update: **`6410219e55f35bf119500d3ac760898a566a89d4`**.
- Package/runtime version remains **0.7.2** during Piecewise development.
- Approved Piecewise spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- Approved Piecewise implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md`.
- The old `planning/v0.8.0-piecewise` branch is retained, but it is 84 commits behind the integrated `main`; it must not be merged into the implementation branch. Only its approved spec/plan blobs were copied.
- Temporary branch validation CI: `.github/workflows/v080-piecewise-validation.yml`; remove before release closure unless intentionally retained.
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
- Numeric comparisons convert compatible units before comparison; incompatible dimensions are rejected.
- A dimensional quantity may be compared with exact dimensionless zero, but not with a nonzero dimensionless value.
- Fully numeric Piecewise evaluation visits conditions in source order and evaluates only the governing response branch.
- Exact dimensionless zero may inherit a compatible dimensional response unit from safely resolvable branches; incompatible branch dimensions and dimensional/nonzero-dimensionless mixtures are rejected when that inference operation encounters them.
- Restricted internal `SymPy Min/Max` evaluation normalizes compatible quantities and dimensional zeros; this exists for supported downstream calculus paths and does not expose general `min(...)` / `max(...)` syntax.
- Tables keep exactly the requested row count; Piecewise breakpoints do not add table rows.
- Plot/envelope keeps the 201-point base grid and augments it with resolvable explicit Piecewise breakpoints.
- Plot polylines split at Piecewise transitions; no fictitious connector across a jump.
- `diff(...)` is branchwise with no automatic `DiracDelta`; explicit transitions are conservatively derivative-undefined for numeric evaluation.
- Piecewise rendering should use native MathJax cases.

### Approved roadmap reprioritization

- After Piecewise, EngCalc will prioritize a **calculator/CAS-style vectors, matrices and linear-systems milestone** before the exact-analysis milestones.
- That matrix milestone must have a dedicated design/spec before production work and must cover exact symbolic matrices, numerical/unit-aware matrices, rendering, matrix algebra and linear systems.
- Working roadmap: `0.8.0 Piecewise` → `0.9.0 vectors/matrices/linear systems` → `0.9.1 exact-first extrema/roots/intersections` → `0.9.2 exact envelopes/governing intervals` → `0.9.3 named response cases/combinations` → `0.10.x engineering verification` → `1.0.0` stabilization.
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
- Baseline Actions run `33299317560`, job `99224326960`: package version **0.7.2 PASS** and **484/484 passed in 85.83 s** on Python 3.13.15.
- Task 1 symbolic RED: Actions `33299843672`, job `99225774691`: **4 failed, 502 passed**, all expected missing Piecewise symbolic construction failures.
- Task 1 authoritative GREEN: commit `a935dd7d9c2bb786caede1bb28274fde28bb77f8`, Actions `33300087110`, job `99226465958`: **506/506 passed in 68.84 s** and package version **0.7.2 PASS**.
- Task 2 initial RED: commit `707c34eb9039298e1f9e2598f751647bf93a6d34`, Actions `33300354762`, job `99227202494`: **10 failed, 506 passed**; all new public numeric contracts failed because `_evaluate_sympy()` did not support symbolic `Piecewise`.
- Task 2 complete RED after adding the plan-required restricted Min/Max contracts: commit `94aea450d838915d1d2c60d530c615bb1d089952`, Actions `33300495144`, job `99227608288`: **12 failed, 506 passed in 104.13 s**; Piecewise tests failed on unsupported `Piecewise`, Min/Max tests failed on unsupported `Min`.
- Task 2 implementation commit: **`3429f6d628a1ede348581e1d1d323680e5a50a39`** (`feat: evaluate piecewise expressions with units`). Compare from its parent confirms the commit changed **only `src/engcalc_colab/numeric.py`**, adding the Pint-aware relation/Piecewise/zero-inference/MinMax implementation.
- Task 2 focused GREEN inside the exact patch workflow: Actions `33300649475`, job `99228028049`: **12/12 passed in 2.65 s** before the implementation commit was pushed.
- The temporary write-capable patch workflow was then deleted. Compare `3429f6d...` → `6410219...` confirms the cleanup commit removed **only `.github/workflows/apply-piecewise-numeric-green.yml`**.
- Task 2 authoritative full GREEN on the cleaned product tree: **`6410219e55f35bf119500d3ac760898a566a89d4`**, Actions `33300696739`, job `99228158667`: package version **0.7.2 PASS** and **518/518 passed in 51.66 s** on Python 3.13.15.
- The implementation plan's old expected baseline of 454 tests is superseded by the integrated baseline because narrative/presentation/dense-summary work was merged before Piecewise execution; this is an explained baseline update, not a regression.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary work:** COMPLETE + merged.
- **0.8.0 Piecewise:** ACTIVE.
  - Task 0 baseline/branch setup: COMPLETE.
  - Task 1 restricted grammar + symbolic construction: COMPLETE, **506/506 GREEN**.
  - Task 2 Pint-aware relations + numeric Piecewise evaluation + dimensional-zero inheritance + restricted Min/Max: COMPLETE, **518/518 GREEN**.
  - Task 3 partial `numeric(...)` / `result(...)` Piecewise metadata and MathJax rendering: NEXT.
  - Task 4 Piecewise engineering tables: pending.
  - Task 5 exact breakpoint extraction/shared enriched plot grids: pending.
  - Later approved plot/envelope/calculus/acceptance tasks: pending.
- **0.9.0 vectors / matrices / linear systems:** NEXT MAJOR MILESTONE AFTER PIECEWISE; design/spec gate required.
- **0.9.1 exact-first extrema / roots / intersections:** planned after matrix/CAS core.
- **0.9.2 exact envelopes / governing intervals:** planned.
- **0.9.3 named response cases / combinations:** planned.
- **0.10.0 / 0.10.1 engineering verification:** planned.
- **1.0.0 API stabilization / release engineering:** planned.

## Exact next step

1. Begin Task 3 with **tests only** in `tests/test_piecewise_partial_numeric.py` and `tests/test_piecewise_renderer.py`.
2. Specify `numeric(q(x))` with known branch values/breakpoints but unresolved interval variable `x`: unresolved symbols must contain only `x`; known branch quantities and breakpoints must be represented structurally; default zero must normalize to the common branch unit when known; target-unit conversion with unresolved `x` remains rejected.
3. Specify renderer RED for formula → substitution → evaluated Piecewise MathJax cases; `result(q(x))` must omit the substitution stage while retaining the compact final Piecewise representation and active precision/zero-tolerance rules.
4. Run RED before modifying `models.py`, `engine.py`, `numeric.py` or `renderer.py`.
5. After verified RED, introduce the smallest optional immutable Piecewise-specific field on `PartialNumericEvaluationResult` and branchwise partial-substitution payload needed by the renderer; keep all existing non-Piecewise paths unchanged.
6. Do not write matrix production code on this branch and do not merge to `main` without explicit user approval.

## How to resume in a new conversation

Read this file first. `main` remains integrated and machine-green at the presentation baseline. Active development is `feature/v0.8.0-piecewise`, based exactly on `main@79befeeb...`. Piecewise Tasks 1 and 2 are complete. The latest machine-validated cleaned product tree is `6410219e...`; Actions `33300696739` verified package version 0.7.2 and **518/518 tests**. Numeric Piecewise now supports Pint-aware `<`, `<=`, `>`, `>=`, lazy governing-branch evaluation, compatible unit conversion, exact-zero dimensional inheritance, explicit incompatible-unit diagnostics and restricted internal Min/Max. The exact next action is Task 3 RED tests for partial `numeric(q(x))` / `result(q(x))` and native Piecewise rendering. The user approved matrices/CAS immediately after Piecewise. Never invoke Codex without explicit authorization.