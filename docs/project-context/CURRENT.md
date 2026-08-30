# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.0 Matrix/CAS remains canonical on `main`. EngCalc 0.9.1 exact characteristics is being implemented inline on `feature/v0.9.1-exact-characteristics`. Tasks 1–6 are complete and fully regression-tested. All temporary Task 6 validation infrastructure has been removed. The exact next step is Task 7 RED for deterministic numerical fallback and explicit approximate provenance._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated release: **EngCalc 0.9.0 Matrix/CAS**.
- Canonical 0.9.1 base: **`main@cdc454db7ea43e57e334d523afded8b4ef498ded`**.
- Runtime/package version remains **0.9.0** until release-closing Task 12.
- Active branch: **`feature/v0.9.1-exact-characteristics`**.
- Approved design spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.1-exact-characteristics-implementation.md`.
- User selected **inline execution / executing-plans**.
- Task 6 product commit: **`84ca991d933c960137805db1980aa4d565d1cbed`**.
- Task 6 cleanup head before this context update: **`5b2528cf5c6aeaf94eaef341584abac4f1e477b7`**.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge 0.9.1 into `main` without explicit user approval.

## Approved behavior

### Existing released behavior preserved

- `%%eng` remains a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Numeric/Pint semantics, `numeric(...)`, `result(...)`, Piecewise, tables, plots, envelopes, multi-argument functions and Matrix/CAS behavior remain regression requirements.
- Whole matrices remain invalid scalar characteristic/plot/table/envelope responses; indexed scalar matrix expressions remain supported.
- Positive structural moment remains plotted **downward**.
- The 201-point plot grid remains a rendering policy, never an authoritative characteristic solver.

### Approved 0.9.1 characteristic contract

Public standalone calls:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

- Characteristic calls are standalone-only in 0.9.1: assignment, nesting and composition are rejected.
- Analysis variables are direct non-reserved symbolic identifiers.
- One reusable exact-first core lives in `src/engcalc_colab/characteristics.py`.
- Domains are finite closed real intervals with unit-compatible bounds and `lower < upper`.
- Exact symbolic results are authoritative whenever finite usable exact results exist.
- Numerical fallback is Task 7: it must run only after exact solving is unresolved, be deterministic, residual-validated, explicitly `provenance="numeric"`, independent of plot sampling and add no SciPy dependency.
- `roots(...)` preserves real in-domain roots, endpoints, exact symbolic locations, unit-aware evaluated coordinates, Piecewise topology and identically-zero interval loci.
- Root/coincident intervals preserve open/closed endpoint topology.
- `intersections(...)` requires compatible response dimensions, uses the union of both responses' Piecewise breakpoints, rejects jump-only crossings, preserves exact common values and represents coincident intervals explicitly.
- Continuous `extrema(...)` uses exact derivative roots plus domain endpoints, preserves local/global roles, constant whole-domain loci, physical units and explicit unbounded directions.
- Piecewise `extrema(...)` solves each continuous region independently, preserves open/closed ownership, keeps distinct finite `left` / `at` / `right` breakpoint records, recomputes global roles only after merge, supports constant governing subinterval loci, and does not create stationary extrema by differentiating through jumps.
- Standalone result models remain immutable/typed.
- Exact envelope crossover/governing-interval mathematics remains deferred to **0.9.2**.
- No SciPy/new runtime dependency.

## Open issues / user feedback

- No blocking 0.9.1 design ambiguity remains.
- **Tasks 1–6 are complete. Task 7 is next.**
- `no_vertical_scroll()` remains a separate ergonomics issue.
- Multiline ordinary non-matrix function-call parsing remains separate.
- Generalized structural eigenproblems remain deferred.

## Validation evidence

### Canonical 0.9.0 release

- Release Actions **`33332233490`**, job **`99312713507`**.
- Release contract **23/23 GREEN**.
- Source suite before wheel **721/721 GREEN in 142.99 s**.
- Wheel `engcalc_colab-0.9.0-py3-none-any.whl`; SHA-256 **`ea66fa231b5657695e2c38cefb324da220070a2f7c86557dddef19d2017a0719`**.
- Installed-wheel/source-free suite **721/721 GREEN in 141.38 s**.
- Final source revalidation **721/721 GREEN in 139.76 s**.

### 0.9.1 Tasks 1–5

- **Task 1 parser/API + typed models:** authoritative run **`33335640543`**, job **`99321927179`** — **758/758 PASS in 121.72 s**.
- **Task 2 finite unit-aware domain + exact continuous roots:** authoritative run **`33336114509`**, job **`99323194537`** — **772/772 PASS in 144.49 s**.
- **Task 3 Piecewise roots/discontinuities/infinite loci:** authoritative run **`33336900776`**, job **`99325325413`** — broad **128/128**, complete **783/783 PASS in 144.99 s**.
- **Task 4 exact intersections/unit compatibility/coincident intervals:** product **`335ea3978ec75ee6037856b8ec49a475016ff8a2`**; authoritative run **`33337417458`**, job **`99326713114`** — broad **158/158**, complete **794/794 PASS in 126.41 s**.
- **Task 5 continuous extrema/local-global roles/constants/unbounded:** product **`bf731e03163c60850a5f3532e750735a764f7e4d`**; authoritative run **`33338129266`**, job **`99328658714`** — broad **99/99**, complete **800/800 PASS in 119.62 s**.
- Temporary validation infrastructure for Tasks 1–5 was removed after each closure.

### 0.9.1 Task 6 — Piecewise extrema + distinct left / at / right values

- Initial RED run **`33338429958`**, job **`99329454985`**: **6 failed / 6 passed in 3.32 s**. Every new failure was the intended `EngEvaluationError("Piecewise extrema require region-aware extrema analysis")`; Task 5 continuous tests remained GREEN.
- A RED fixture was corrected before production changes: the originally chosen constant value `2` was actually globally governing against `(x-3)^2` on `[2,4]`; the non-governing fixture was changed to exact `1/2`.
- Corrected RED run **`33338579957`**, job **`99329863023`**: **6 failed / 6 passed in 3.42 s**, again only on the deliberate Piecewise gate.
- Product GREEN commit: **`84ca991d933c960137805db1980aa4d565d1cbed`** (`feat: preserve Piecewise one-sided extrema`).
- First focused GREEN run **`33338712802`**, job **`99330238095`**: **56/56 PASS in 10.03 s**; `git diff --check` PASS.
- Coverage was then strengthened with a dimensional Piecewise breakpoint and a continuous cusp where equal one-sided limits still require local-minimum classification.
- Reinforced idempotent run **`33338786652`**, job **`99330441531`**: **58/58 PASS in 12.42 s**; patch explicitly skipped and `No product patch to commit.`
- Authoritative full-gate SHA: **`e711d5ef3275f9a534b340e5273a234eb509d11e`**.
- Full-gate run **`33338829227`**, job **`99330564446`**, Python **3.13.15**.
- `compileall`: PASS.
- `git diff --check origin/main...HEAD`: PASS.
- Complete characteristics + Piecewise + scalar-math regression gate: **173/173 PASS in 26.84 s**.
- Complete source suite: **808/808 PASS in 152.40 s**.
- Task 6 preserves exact regional solving, explicit `left` / `at` / `right` values, actual breakpoint governing extrema, local cusp extrema, dimensional breakpoint quantities, constant global-max/min subinterval loci, post-merge global classification and jump-safe semantics.
- Four temporary Task 6 artifacts were removed after validation: `.github/workflows/v091-task6-tdd.yml`, `.github/workflows/v091-task6-full-gate.yml`, `.github/scripts/v091_task6_green.py`, and `.github/scripts/v091_task6_green_v2.py`.
- Cleanup head before this context update: **`5b2528cf5c6aeaf94eaef341584abac4f1e477b7`**.
- Fresh compare against canonical `main` after cleanup contains no `.github` files; only approved docs, product and tests remain.
- No Codex review or Codex Cloud has been invoked.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 Matrix/CAS:** **COMPLETE + RELEASE-VALIDATED + MERGED**.
- **0.9.1 Task 1:** **COMPLETE — 758/758 full GREEN**.
- **0.9.1 Task 2:** **COMPLETE — 772/772 full GREEN**.
- **0.9.1 Task 3:** **COMPLETE — 783/783 full GREEN**.
- **0.9.1 Task 4:** **COMPLETE — 794/794 full GREEN**.
- **0.9.1 Task 5:** **COMPLETE — 800/800 full GREEN**.
- **0.9.1 Task 6:** **COMPLETE — 808/808 full GREEN**.
- **0.9.1 Task 7 deterministic numerical fallback + approximate provenance: NEXT**.
- Then Tasks 8–12 per the approved implementation plan.
- Later: **0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Create `tests/test_characteristics_fallback.py` before modifying production code.
2. RED must force `_exact_real_solution_set(...)` to report unresolved and prove that roots fall back numerically with `provenance="numeric"` rather than returning unresolved/no answer.
3. Add RED coverage for deterministic repeated results, residual rejection, even-multiplicity roots, duplicate collapse, no bracketing across Piecewise jumps, coexistence of exact and numeric results across separate Piecewise regions, extrema derivative fallback, and independence from `NumericContext.build_plot_sample_points`.
4. Implement `_fallback_roots(...)` with exactly `_FALLBACK_SCAN_COUNT = 1025`, `_FALLBACK_REL_RESIDUAL_TOL = 1e-9`, `_FALLBACK_X_DEDUP_REL_TOL = 1e-10`.
5. Build fallback samples directly from `AnalysisDomain`; never use the public 201-point plot grid and never pass Pint quantities directly to mpmath.
6. Validate every candidate by real/finite/domain/residual checks and de-duplicate in physical x, preferring exact provenance when exact and numeric candidates coincide.
7. Wire fallback only for continuous regions whose exact solver reports unresolved. If fallback cannot validate a solution set, raise `EngEvaluationError("characteristic numerical fallback could not validate a solution set")` rather than returning sampled guesses.
8. Run focused fallback + roots/extrema regressions, then the broad characteristic gate and complete source suite before closing Task 7.
9. Keep version at 0.9.0 until Task 12.
10. Do not merge without explicit user approval and do not invoke Codex unless explicitly authorized.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.0 remains canonical on `main@cdc454db7ea43e57e334d523afded8b4ef498ded`. Active work is `feature/v0.9.1-exact-characteristics`. Tasks 1–6 are complete. Task 6 product is `84ca991d933c960137805db1980aa4d565d1cbed`; authoritative run `33338829227`, job `99330564446`, with **173/173 characteristic+Piecewise+scalar tests** and **808/808 complete source tests in 152.40 s**. All four Task 6 temporary harness files are removed; cleanup head before this context update is `5b2528cf5c6aeaf94eaef341584abac4f1e477b7`. Resume with Task 7 RED for deterministic numerical fallback and explicit numeric provenance. Never merge without explicit user approval; never invoke Codex without explicit authorization.
