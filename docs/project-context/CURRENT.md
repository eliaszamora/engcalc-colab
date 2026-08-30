# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.0 Matrix/CAS remains canonical on `main`. EngCalc 0.9.1 exact characteristics is being implemented inline on `feature/v0.9.1-exact-characteristics`. Tasks 1–5 are complete and fully regression-tested. Task 5 temporary validation infrastructure has been removed. The exact next step is Task 6 RED for Piecewise extrema, one-sided breakpoint values and constant extremum loci by subinterval._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated release: **EngCalc 0.9.0 Matrix/CAS**.
- Canonical 0.9.1 base: **`main@cdc454db7ea43e57e334d523afded8b4ef498ded`**.
- Runtime/package version remains **0.9.0** until release-closing Task 12.
- Active branch: **`feature/v0.9.1-exact-characteristics`**.
- Approved design spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.1-exact-characteristics-implementation.md`.
- User selected **inline execution / executing-plans**.
- Task 5 product commit: **`bf731e03163c60850a5f3532e750735a764f7e4d`**.
- Task 5 temporary-workflow/script cleanup head before this context update: **`0d02a8dcc1e906f8932cbc316337a63d0f312021`**.
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
- Numerical fallback, when later enabled by the approved plan, must be deterministic, residual-validated, explicitly approximate and independent of the 201-point plotting grid.
- `roots(...)` preserves real in-domain roots, endpoints, exact symbolic locations, unit-aware evaluated coordinates, Piecewise topology and identically-zero interval loci.
- Root/coincident intervals preserve open/closed endpoint topology.
- `intersections(...)` requires compatible response dimensions, uses the union of both responses' Piecewise breakpoints, rejects jump-only crossings, preserves exact common values and represents coincident intervals explicitly.
- Continuous `extrema(...)` now uses exact derivative roots plus domain endpoints, preserves local/global roles, constant whole-domain loci, physical units and explicit unbounded-above/below directions.
- For a symbolic stationary point whose second-derivative sign is unresolved, local classification uses deterministic same-region neighboring evaluation rather than plot sampling.
- Piecewise extrema must solve continuous regions independently and preserve distinct finite `left` / `at` / `right` values at breakpoints; this is Task 6.
- Standalone result models remain immutable/typed.
- Exact envelope crossover/governing-interval mathematics remains deferred to **0.9.2**.
- No SciPy/new runtime dependency.

## Open issues / user feedback

- No blocking 0.9.1 design ambiguity remains.
- **Tasks 1–5 are complete. Task 6 is next.**
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

### 0.9.1 Tasks 1–4

- **Task 1 parser/API + typed models:** authoritative run **`33335640543`**, job **`99321927179`** — `compileall`/hygiene PASS, **758/758 PASS in 121.72 s**.
- **Task 2 finite unit-aware domain + exact continuous roots:** authoritative run **`33336114509`**, job **`99323194537`** — focused **30/30**, complete **772/772 PASS in 144.49 s**.
- **Task 3 Piecewise roots/discontinuities/infinite root loci:** product **`324e4990be3c95c19422b6a58804e1b104653d79`** plus dimensional contract; authoritative run **`33336900776`**, job **`99325325413`** — characteristics+Piecewise **128/128**, complete **783/783 PASS in 144.99 s**.
- **Task 4 exact intersections/unit compatibility/coincident intervals:** product **`335ea3978ec75ee6037856b8ec49a475016ff8a2`**; authoritative run **`33337417458`**, job **`99326713114`** — broad gate **158/158**, complete **794/794 PASS in 126.41 s**.
- Temporary validation infrastructure for Tasks 1–4 was removed after each closure.

### 0.9.1 Task 5 — continuous extrema, local/global roles, constants + unbounded detection

- RED test commit: **`e7f2b35fc8ced87ee87e48a00df2438a8ff92633`**; RED harness SHA **`0248e9fc088037b7be40c47d59198bf10f616b12`**.
- RED run **`33337842652`**, job **`99327896512`**: intended collection failure, `ImportError: cannot import name 'solve_extrema_exact'`, **1 error in 0.69 s**.
- First GREEN attempt run **`33337937283`**, job **`99328156883`**: **58 passed / 1 failed in 7.25 s**. The only failure was missing `local_max` on a dimensional quadratic; exact `L/2`, `qL^2/4`, 40 kN·m and `global_max` were already correct. No product commit was allowed.
- Root cause: symbolic second derivative `-2*q` has unknown SymPy sign, so fallback neighboring comparison was used. With a required `1e-6` spatial offset, the quadratic value difference is order `1e-12`, equal to the original local-role comparison tolerance. The local-classification tolerance was narrowed only for that fallback; global comparison tolerance remained unchanged.
- Product GREEN run **`33338015312`**, job **`99328361908`**: **59/59 PASS in 7.87 s**; `git diff --check` PASS; product commit **`bf731e03163c60850a5f3532e750735a764f7e4d`** (`feat: add exact continuous extrema analysis`).
- Idempotent recheck run **`33338081632`**, job **`99328536729`**: patch explicitly skipped, **59/59 PASS in 12.21 s**, `No product patch to commit.`
- Authoritative full-gate SHA: **`6d15e6a1183f5991bf46590f201d8fda01bb6158`**.
- Full-gate run **`33338129266`**, job **`99328658714`**, Python **3.13.15**.
- `compileall`: PASS.
- `git diff --check origin/main...HEAD`: PASS.
- Complete `test_characteristics_*` + scalar-math regression gate: **99/99 PASS in 10.17 s**.
- Complete source suite: **800/800 PASS in 119.62 s**.
- Task 5 added exact continuous stationary-point analysis, endpoint boundary candidates, local/global role classification, dimensional exact locations/values, constant `CharacteristicInterval(role="global_max_min")` loci, finite-domain singularity inspection and explicit unbounded-above/below flags without creating finite points at undefined poles.
- All Task 5 temporary workflows and guarded patch script were removed; cleanup head **`0d02a8dcc1e906f8932cbc316337a63d0f312021`**.
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
- **0.9.1 Task 5 continuous extrema:** **COMPLETE — 800/800 full GREEN**.
- **0.9.1 Task 6 Piecewise extrema + `left/at/right`: NEXT**.
- Then Tasks 7–12 per the approved implementation plan.
- Later: **0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Create Task 6 RED tests before modifying `characteristics.py`.
2. RED must cover a discontinuous Piecewise breakpoint with distinct finite `left`, `at`, `right` records, a breakpoint governing a global maximum/minimum, a constant Piecewise subinterval that is a global extremum locus, and a jump that must not become a fake stationary point.
3. Reuse `_partition_piecewise_regions(...)` and the continuous extrema machinery from Task 5; never differentiate the full Piecewise expression through a jump.
4. Solve each continuous region independently, preserving its open/closed boundary ownership.
5. Add explicit finite one-sided breakpoint values and the actual defined breakpoint value.
6. Recompute global roles only after merging all regional points, one-sided values and constant loci.
7. Run focused Piecewise-extrema + existing continuous-extrema + Piecewise calculus/plotting regressions, then the complete source suite before closing Task 6.
8. Keep version at 0.9.0 until Task 12.
9. Do not merge without explicit user approval and do not invoke Codex unless explicitly authorized.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.0 remains canonical on `main@cdc454db7ea43e57e334d523afded8b4ef498ded`. Active work is `feature/v0.9.1-exact-characteristics`. Tasks 1–5 are complete; Task 5 product is `bf731e03163c60850a5f3532e750735a764f7e4d`, authoritative run `33338129266`, job `99328658714`, with **99/99 characteristic+scalar regression tests** and **800/800 complete source tests in 119.62 s**. Task 5 temporary infrastructure is removed. Resume with Task 6 RED for Piecewise extrema and distinct finite `left/at/right` breakpoint values. Never merge without explicit user approval; never invoke Codex without explicit authorization.
