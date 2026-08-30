# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.0 Matrix/CAS remains canonical on `main`. EngCalc 0.9.1 exact characteristics is being implemented inline on `feature/v0.9.1-exact-characteristics`. Tasks 1–9 are complete and fully regression-tested. All temporary Task 9 validation infrastructure has been removed. The exact next step is Task 10 RED for authoritative exact characteristics in ordinary plots._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated release: **EngCalc 0.9.0 Matrix/CAS**.
- Canonical 0.9.1 base: **`main@cdc454db7ea43e57e334d523afded8b4ef498ded`**.
- Runtime/package version remains **0.9.0** until release-closing Task 12.
- Active branch: **`feature/v0.9.1-exact-characteristics`**.
- Approved design spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.1-exact-characteristics-implementation.md`.
- User selected **inline execution / executing-plans**.
- Task 7 product: **`44401cd2ab3d89d10b861a45f873342756af8d41`**.
- Task 8 product: **`0fe830723d12c4899e1e37cf8f3ec441cad708fe`**.
- Task 9 product: **`c9055a10fdeb2bae7d3d86f0740597567f142fcf`**.
- Task 9 cleanup head before this context update: **`2761ed83fca0eeed684bb7b6d873845aa9b889d8`**.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge 0.9.1 into `main` without explicit user approval.

## Approved behavior

### Existing released behavior preserved

- `%%eng` remains a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Numeric/Pint semantics, Piecewise, tables, plots, envelopes, multi-argument functions and Matrix/CAS behavior remain regression requirements.
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

- Characteristic calls are standalone-only in 0.9.1; assignment, nesting and composition are rejected.
- One reusable exact-first core lives in `src/engcalc_colab/characteristics.py`.
- Domains are finite closed real intervals with unit-compatible bounds and `lower < upper`.
- Exact symbolic results are authoritative whenever usable; deterministic numeric fallback runs only for unresolved continuous regions.
- Fallback uses 1025 internal physical-domain samples, residual tolerance 1e-9 and x de-duplication tolerance 1e-10; it never uses the public 201-point plot grid and adds no SciPy dependency.
- Roots, intersections and extrema preserve Piecewise topology, units, exact/numeric provenance, interval loci and explicit discontinuity semantics.
- Engine dispatch returns typed immutable `RootsResult`, `IntersectionsResult` and `ExtremaResult`, with operation-specific line-numbered diagnostics.
- Standalone characteristic rendering now uses a dedicated HTML/MathJax block: exact points show `=`, numeric fallback shows `≈`, units are compact, extrema roles/sides are explicit, root/coincident intervals are explicit, and unbounded extrema are stated rather than sampled.
- `%%eng` flushes pending aligned equations before each characteristic block and preserves source order across consecutive characteristic calls. Characteristic result classes are deliberately not part of `CalculationResult`.
- Task 10 will attach authoritative exact global extrema metadata to **ordinary `plot(...)` series** while retaining the 201-point grid only for drawing the curve.
- `envelope(...)` remains on its sampled characteristic path in 0.9.1; exact envelope crossovers/governing intervals remain deferred to **0.9.2**.

## Open issues / user feedback

- No blocking 0.9.1 design ambiguity remains.
- **Tasks 1–9 are complete. Task 10 is next.**
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
- Task 2 exact continuous roots: **772/772 full GREEN**.
- Task 3 Piecewise roots/topology: **783/783 full GREEN**.
- Task 4 intersections: **794/794 full GREEN**.
- Task 5 continuous extrema: **800/800 full GREEN**.
- Task 6 Piecewise extrema: run **`33338829227`**, job **`99330564446`** — **173/173 broad**, **808/808 complete in 152.40 s**.
- Task 7 deterministic fallback: product **`44401cd2ab3d89d10b861a45f873342756af8d41`**; run **`33339835753`**, job **`99333344632`** — **185/185 broad**, **820/820 complete in 157.77 s**.

### 0.9.1 Task 8 — engine dispatch + diagnostics

- RED run **`33340134611`**, job **`99334142882`**: **8 failed / 58 passed in 13.89 s**, all intended missing dispatch failures.
- Product: **`0fe830723d12c4899e1e37cf8f3ec441cad708fe`** (`feat: dispatch characteristic analysis from engine`).
- GREEN run **`33340266119`**, job **`99334498271`**: **85/85 PASS in 16.89 s**.
- Idempotent run **`33340328907`**, job **`99334670050`**: **85/85 PASS in 16.51 s**, patch skipped and no product commit.
- Authoritative full gate **`33340983117`**, job **`99336452342`**, SHA **`ecaf050503653c439ceb8b84f876938c293cc4c3`**: `compileall` PASS, diff hygiene PASS, **368/368 broad in 40.23 s**, **828/828 full in 104.51 s**.
- All Task 8 temporary harness files were removed.

### 0.9.1 Task 9 — rendering + `%%eng` routing

- RED run **`33341322976`**, job **`99337365358`**: **7 failed / 35 passed in 10.44 s**. Five failures were the intentionally missing `render_characteristic_result`; two were the intentionally missing magic routing (`RootsResult` incorrectly reached aligned rendering and had no `.value`). Existing renderer/magic regressions remained GREEN.
- Product: **`c9055a10fdeb2bae7d3d86f0740597567f142fcf`** (`feat: render characteristic analysis in eng magic`).
- First GREEN run **`33341431012`**, job **`99337657662`**: **42/42 PASS in 9.14 s**; `git diff --check` PASS.
- Idempotent run **`33341490338`**, job **`99337821337`**: **42/42 PASS in 8.43 s**; log explicitly states `Task 9 characteristic renderer already present; skipping patch.` and `No product patch to commit.`
- Authoritative full-gate SHA: **`98d2470f7d8ce92e541cd7c904daf69c5447810a`**.
- Full-gate run **`33341538689`**, job **`99337950723`**, Python **3.13.15**.
- `compileall`: PASS.
- `git diff --check origin/main...HEAD`: PASS.
- Characteristics + rendering/magic + Piecewise + matrix + scalar-math gate: **387/387 PASS in 49.23 s**.
- Complete source suite: **835/835 PASS in 117.02 s**.
- Three temporary Task 9 artifacts were removed: `.github/workflows/v091-task9-tdd.yml`, `.github/workflows/v091-task9-full-gate.yml`, `.github/scripts/v091_task9_green.py`.
- Cleanup head before this context update: **`2761ed83fca0eeed684bb7b6d873845aa9b889d8`**.
- Fresh compare against canonical `main` after cleanup contains no `.github` files; only approved docs, product and tests remain.
- No Codex review or Codex Cloud has been invoked.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 Matrix/CAS:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.1 Tasks 1–9:** **COMPLETE — latest full suite 835/835 GREEN**.
- **0.9.1 Task 10 exact characteristics in ordinary plots: NEXT**.
- Then Task 11 acceptance/docs and Task 12 release/real-wheel validation/PR.
- Later: **0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Create `tests/test_characteristics_plot_integration.py` before modifying plot product code.
2. The decisive RED must use `f(x) = -(x - 1/3)^2 + 2` on `[0,1]`: the authoritative global maximum must be exactly `x = 1/3` even though none of the 201 drawing samples lies at `1/3`.
3. Add RED coverage for independent multi-series extrema, parameter sweeps with overrides, Piecewise same-x side preservation, positive-moment inversion, dense characteristic summaries, and explicit envelope sampled-path preservation.
4. Extend `PlotSeries` with immutable `characteristics: tuple[CharacteristicPoint, ...] = ()` and preserve metadata through series normalization.
5. Generate exact global extrema metadata in the engine only for `plot(...)`, using the characteristic core and the same analysis domain but never the sampled `x_values`; parameter sweeps must pass their case override.
6. Make `plotting._characteristic_requests(...)` consume authoritative metadata first for ordinary plots; retain `_extreme_indices(...)` for envelopes/legacy fallback. No solver may be introduced in plotting or label-layout code.
7. Run focused plot/presentation regression gates and the complete suite before closing Task 10.
8. Keep version at 0.9.0 until Task 12. Do not merge without explicit user approval and do not invoke Codex unless explicitly authorized.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.0 remains canonical on `main@cdc454db7ea43e57e334d523afded8b4ef498ded`. Active work is `feature/v0.9.1-exact-characteristics`. Tasks 1–9 are complete. Task 9 product is `c9055a10fdeb2bae7d3d86f0740597567f142fcf`; authoritative run `33341538689`, job `99337950723`, with **387/387 broad tests** and **835/835 complete source tests in 117.02 s**. All Task 9 temporary harness files are removed; cleanup head before this context update is `2761ed83fca0eeed684bb7b6d873845aa9b889d8`. Resume with Task 10 RED for exact ordinary-plot characteristics. Never merge without explicit user approval; never invoke Codex without explicit authorization.
