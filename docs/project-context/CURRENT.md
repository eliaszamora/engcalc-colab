# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.0 Matrix/CAS remains canonical on `main`. EngCalc 0.9.1 exact characteristics is being implemented inline on `feature/v0.9.1-exact-characteristics`. Tasks 1–8 are complete and fully regression-tested. All temporary Task 8 validation infrastructure has been removed. The exact next step is Task 9 RED for standalone characteristic rendering and `%%eng` display routing._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated release: **EngCalc 0.9.0 Matrix/CAS**.
- Canonical 0.9.1 base: **`main@cdc454db7ea43e57e334d523afded8b4ef498ded`**.
- Runtime/package version remains **0.9.0** until release-closing Task 12.
- Active branch: **`feature/v0.9.1-exact-characteristics`**.
- Approved design spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.1-exact-characteristics-implementation.md`.
- User selected **inline execution / executing-plans**.
- Task 7 product commit: **`44401cd2ab3d89d10b861a45f873342756af8d41`**.
- Task 8 product commit: **`0fe830723d12c4899e1e37cf8f3ec441cad708fe`**.
- Task 8 cleanup head before this context update: **`89ed4404feb6daf8cb8f726dccdfcc88791cfb49`**.
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
- Deterministic numerical fallback runs only for unresolved continuous regions, uses **1025** internal physical-domain samples, residual tolerance **1e-9**, x de-duplication tolerance **1e-10**, never uses the public plot grid, carries `provenance="numeric"`, and adds no SciPy dependency.
- Numerical fallback is shared by roots, intersections and extrema derivative solving. Exact and numeric results may coexist across independent Piecewise regions.
- If numerical fallback cannot validate a finite solution set, EngCalc raises an explicit `EngEvaluationError`; it never promotes sampled guesses to authoritative results.
- `roots(...)` preserves real in-domain roots, endpoints, exact symbolic locations, unit-aware evaluated coordinates, Piecewise topology and identically-zero interval loci.
- `intersections(...)` requires compatible response dimensions, respects both responses' Piecewise topology, rejects jump-only crossings, preserves common values, supports fallback and represents coincident intervals explicitly.
- `extrema(...)` preserves local/global roles, endpoint/boundary candidates, Piecewise `left` / `at` / `right` values, constant governing intervals, physical units and explicit unbounded directions.
- Engine dispatch now returns immutable typed `RootsResult`, `IntersectionsResult` and `ExtremaResult` through parsed DSL calls.
- Engine response resolution reuses the existing function/substitution/`abs`/matrix-index machinery; whole matrices are rejected with actionable scalar-index diagnostics.
- Characteristic domain/core errors are operation-specific and line-numbered at the engine boundary.
- Standalone engineering rendering is **Task 9**; characteristic results are not yet routed as presentation blocks in `%%eng`.
- Exact envelope crossover/governing-interval mathematics remains deferred to **0.9.2**.

## Open issues / user feedback

- No blocking 0.9.1 design ambiguity remains.
- **Tasks 1–8 are complete. Task 9 is next.**
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

### 0.9.1 Tasks 1–7

- Task 1 parser/API + typed models: **758/758 full GREEN**.
- Task 2 finite unit-aware domain + exact continuous roots: **772/772 full GREEN**.
- Task 3 Piecewise roots/discontinuities/infinite loci: **783/783 full GREEN**.
- Task 4 exact intersections/unit compatibility/coincident intervals: **794/794 full GREEN**.
- Task 5 continuous extrema/local-global roles/constants/unbounded: **800/800 full GREEN**.
- Task 6 Piecewise extrema + `left` / `at` / `right`: authoritative run **`33338829227`**, job **`99330564446`** — **173/173 broad**, **808/808 complete in 152.40 s**.
- Task 7 deterministic fallback: product **`44401cd2ab3d89d10b861a45f873342756af8d41`**; authoritative run **`33339835753`**, job **`99333344632`** — **185/185 broad**, **820/820 complete in 157.77 s**.
- Temporary validation infrastructure for Tasks 1–7 was removed after closure.

### 0.9.1 Task 8 — engine dispatch + diagnostics

- RED run **`33340134611`**, job **`99334142882`**: **8 failed / 58 passed in 13.89 s**. All eight failures were the intended missing engine dispatch (`unsupported function 'roots'/'intersections'/'extrema'`); direct characteristic-core regressions remained GREEN.
- Product GREEN commit: **`0fe830723d12c4899e1e37cf8f3ec441cad708fe`** (`feat: dispatch characteristic analysis from engine`).
- First GREEN run **`33340266119`**, job **`99334498271`**: **85/85 PASS in 16.89 s**; `git diff --check` PASS.
- Idempotent recheck run **`33340328907`**, job **`99334670050`**: **85/85 PASS in 16.51 s**; log explicitly states `Task 8 engine dispatch already present; skipping patch.` and `No product patch to commit.`
- Authoritative full-gate SHA: **`ecaf050503653c439ceb8b84f876938c293cc4c3`**.
- Full-gate run **`33340983117`**, job **`99336452342`**, Python **3.13.15**.
- `compileall`: PASS.
- `git diff --check origin/main...HEAD`: PASS.
- Characteristics + engine/diagnostics + Piecewise + matrix + scalar-math gate: **368/368 PASS in 40.23 s**.
- Complete source suite: **828/828 PASS in 104.51 s**.
- Engine behavior validated: typed roots/intersections/extrema results, dimensional domains/results, indexed matrix scalar responses, whole-matrix rejection, incompatible intersection dimensions, unresolved/reversed-domain diagnostics and preserved line numbers.
- Three temporary Task 8 artifacts were removed after validation: `.github/workflows/v091-task8-tdd.yml`, `.github/workflows/v091-task8-full-gate.yml`, `.github/scripts/v091_task8_green.py`.
- Cleanup head before this context update: **`89ed4404feb6daf8cb8f726dccdfcc88791cfb49`**.
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
- **0.9.1 Task 7:** **COMPLETE — 820/820 full GREEN**.
- **0.9.1 Task 8:** **COMPLETE — 828/828 full GREEN**.
- **0.9.1 Task 9 standalone engineering rendering + `%%eng` display routing: NEXT**.
- Then Tasks 10–12 per the approved implementation plan.
- Later: **0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Create `tests/test_characteristics_rendering.py` and `tests/test_characteristics_magic.py` before modifying renderer/magic product code.
2. RED rendering coverage must prove exact `=` versus fallback `≈`, units, global/local roles, Piecewise side labels, root interval loci, coincident-intersection intervals, unbounded extrema and absence of raw dataclass reprs.
3. RED magic coverage must prove pending equation groups are flushed before a standalone characteristic HTML block.
4. Implement `render_characteristic_result(result, settings=None) -> str` in `renderer.py`, reusing `_latex`, `_quantity_latex`, `RenderSettings` and HTML escaping.
5. Route `RootsResult`, `IntersectionsResult` and `ExtremaResult` in `magic.py` as standalone `HTML(...)` blocks after flushing pending equation rows. Do not add these results to `CalculationResult`.
6. Run focused rendering/magic regressions, then a complete source-suite gate before Task 9 closure.
7. Keep version at 0.9.0 until Task 12. Do not merge without explicit user approval and do not invoke Codex unless explicitly authorized.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.0 remains canonical on `main@cdc454db7ea43e57e334d523afded8b4ef498ded`. Active work is `feature/v0.9.1-exact-characteristics`. Tasks 1–8 are complete. Task 8 product is `0fe830723d12c4899e1e37cf8f3ec441cad708fe`; authoritative run `33340983117`, job `99336452342`, with **368/368 broad characteristic/engine/matrix tests** and **828/828 complete source tests in 104.51 s**. All Task 8 temporary harness files are removed; cleanup head before this context update is `89ed4404feb6daf8cb8f726dccdfcc88791cfb49`. Resume with Task 9 RED for standalone characteristic rendering and `%%eng` display routing. Never merge without explicit user approval; never invoke Codex without explicit authorization.
