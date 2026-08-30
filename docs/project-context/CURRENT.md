# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.0 Matrix/CAS remains the canonical integrated release on `main`. EngCalc 0.9.1 exact characteristics is being implemented inline on its dedicated feature branch. Task 1 (public grammar + typed result models) is complete, fully regression-tested, and its temporary validation harness has been removed. The exact next step is Task 2 RED for finite unit-aware domains and exact continuous roots._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated release: **EngCalc 0.9.0 Matrix/CAS**.
- Canonical 0.9.1 base: **`main@cdc454db7ea43e57e334d523afded8b4ef498ded`**.
- Runtime/package version remains **0.9.0** until the release-closing Task 12.
- Active branch: **`feature/v0.9.1-exact-characteristics`**.
- Approved design spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.1-exact-characteristics-implementation.md`.
- Plan refinement commit: **`eb9b5344d20dab950462c63e742ff8f17be8916d`**.
- User selected **inline execution / executing-plans** for implementation.
- Task 1 cleanup head before this context update: **`0e0f698490a024963d31bea2736ffde2886e8ad1`**.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge 0.9.1 into `main` without explicit user approval.

## Approved behavior

### Existing released behavior preserved

- `%%eng` remains a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Numeric/Pint semantics, `numeric(...)`, `result(...)`, Piecewise, tables, plots, envelopes, multi-argument functions and Matrix/CAS behavior remain regression requirements.
- Whole matrices remain invalid scalar analysis/plot/table/envelope responses; indexed scalar matrix expressions remain supported.
- Positive structural moment remains plotted **downward**.
- The 201-point plot grid remains a rendering policy, not an authoritative mathematical solver.

### Approved 0.9.1 contract

Public standalone calls:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

- Characteristic calls are standalone-only in 0.9.1: assignment, nesting and composition are rejected.
- Their analysis variable must be a direct non-reserved symbolic identifier.
- Introduce one reusable exact-first characteristic-analysis core in `src/engcalc_colab/characteristics.py`.
- Exact symbolic results are authoritative whenever a finite usable exact result exists.
- Deterministic numerical fallback runs only after unresolved exact solving, is residual-validated, visibly approximate and independent of the public 201-point plotting grid.
- Domains are finite closed real intervals with unit-compatible bounds and `lower < upper`; dimensional-zero inheritance follows existing EngCalc semantics.
- Whole matrices are rejected; indexed scalar matrix responses such as `K(x)[1,1]` are valid.
- `roots(...)` keeps real in-domain roots, endpoints and repeated-root de-duplication; identically-zero regions are interval loci.
- `intersections(...)` requires dimensionally compatible responses, respects Piecewise discontinuities and represents coincident intervals explicitly.
- `extrema(...)` considers stationary points, endpoints, Piecewise breakpoints and finite one-sided values; local/global roles, constant loci and unbounded directions are explicit.
- Piecewise regions are solved independently; a sign change/crossing through a jump is not a root/intersection unless equality holds at a defined point.
- Characteristic points preserve exact/numeric provenance and `at`/`left`/`right` topology.
- Standalone result models are immutable/typed and render as engineering output, never raw SymPy set/dataclass reprs.
- Ordinary/multi-series `plot(...)` migrates characteristic extrema to the exact-first core while retaining existing 201-point curve sampling and visual conventions.
- Exact envelope crossover/governing-interval mathematics remains deferred to **0.9.2**.
- No SciPy/new runtime dependency.

## Open issues / user feedback

- No blocking 0.9.1 design ambiguity remains.
- **Task 1 is complete.** Task 2 has not started yet.
- `no_vertical_scroll()` remains a separate ergonomics issue.
- Multiline ordinary non-matrix function-call parsing remains separate.
- Generalized structural eigenproblems remain deferred to a dedicated future design.

## Validation evidence

### Canonical 0.9.0 release evidence

- Authoritative 0.9.0 release Actions: **`33332233490`**, job **`99312713507`**.
- Release contract: **23/23 GREEN**.
- Source suite before wheel: **721/721 GREEN in 142.99 s**.
- Wheel: `engcalc_colab-0.9.0-py3-none-any.whl`; SHA-256 **`ea66fa231b5657695e2c38cefb324da220070a2f7c86557dddef19d2017a0719`**.
- Installed-wheel/source-free suite: **721/721 GREEN in 141.38 s**.
- Final source revalidation: **721/721 GREEN in 139.76 s**.
- Post-merge Actions **`33333566096`**, job **`99316363602`**, verified exact merge SHA `d22d5e0a62ce13800de8476c28d86a6d9415f1bd` successfully.

### 0.9.1 Task 1 — parser/API RED → GREEN

- Parser RED SHA: **`512b9fc856fda338601f360ad7cde72481ad699f`**.
- RED Actions: run **`33335156057`**, job **`99320642585`**.
- RED result: **20 failed / 4 passed in 0.09 s**.
- All 20 failures were the intended missing-contract failures: wrong arity, invalid/direct-variable rules, standalone-only rules, reserved characteristic names, `:=` assignment and matrix-literal nesting were still being accepted.
- Parser GREEN Actions: run **`33335340109`**, job **`99321122672`**.
- Focused parser GREEN: **65/65 PASS in 0.15 s**, plus `git diff --check` PASS.
- Parser product commit: **`e7e92069d0858edef6684286c1c6f414d132e881`** (`feat: validate characteristic analysis syntax`).
- Independent parser-only recheck: run **`33335404256`**, job **`99321295095`**: **24/24 PASS in 0.07 s**.

### 0.9.1 Task 1 — typed result models RED → GREEN

- Models RED SHA: **`7ac31fcb50cc51116df522b387d31d46046c495e`**.
- RED Actions: run **`33335416627`**, job **`99321328462`**.
- RED result: collection failed exactly because `CharacteristicInterval` and the new characteristic result types did not yet exist; **1 intended collection error in 0.20 s**.
- Models GREEN Actions: run **`33335470514`**, job **`99321471976`**.
- Focused models/parser GREEN: **78/78 PASS in 0.22 s**, plus `git diff --check` PASS.
- Models product commit: **`b12a573c51f6dc6856f6d3b3652d674ffa4e8846`** (`feat: add typed characteristic result models`).
- Added immutable `CharacteristicPoint`, `CharacteristicInterval`, `RootsResult`, `IntersectionsResult`, `ExtremaResult`; provenance is restricted to `exact|numeric`, side to `at|left|right`, result collections normalize to tuples, and extrema carry explicit unbounded-above/below flags.

### 0.9.1 Task 1 — complete regression gate

- First full-gate attempt reached `compileall` and `git diff --check` successfully but stopped during pytest collection with **14 `ModuleNotFoundError: IPython` errors** because the temporary Actions environment installed `.[dev]` without IPython. This was a harness dependency omission, not a product regression; no source correction was made for it.
- Harness-only dependency fix commit: **`c5d8309923cb80922645064a80596a9a546d8259`**.
- Authoritative Task 1 full gate: run **`33335640543`**, job **`99321927179`**, Python **3.13.15**.
- `compileall`: PASS.
- `git diff --check`: PASS.
- Complete suite: **758/758 PASS in 121.72 s**.
- All temporary Task 1 workflows/scripts were removed afterward. Cleanup head before this context update: **`0e0f698490a024963d31bea2736ffde2886e8ad1`**.
- Comparison from canonical `main` to the clean Task 1 tree contains only the approved spec/plan/context plus `parser.py`, `models.py`, `tests/test_characteristics_parser.py` and `tests/test_characteristics_models.py`; no temporary `.github` harness remains.
- No Codex review or Codex Cloud has been invoked.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **COMPLETE + RELEASE-VALIDATED + MERGED**.
- **0.9.1 Task 1 parser/API + typed result models:** **COMPLETE — 758/758 full GREEN**.
- **0.9.1 Task 2 finite unit-aware domain + exact continuous roots:** **NEXT**.
- Then Tasks 3–12 per the approved implementation plan.
- Later releases: **0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Start Task 2 by writing `tests/test_characteristics_roots.py` before creating the characteristic solver implementation.
2. RED must cover exact rational/polynomial roots, repeated-root de-duplication, endpoint roots, no-real-root case, finite/reversed/zero-width domains, incompatible domain units, non-finite bounds, dimensional bounds with adaptable zero, and dimensional response roots.
3. Confirm the RED on the exact branch SHA in GitHub Actions.
4. Create `src/engcalc_colab/characteristics.py` with `AnalysisDomain`, `normalize_analysis_domain(...)`, and exact continuous `solve_roots_exact(...)` only; Piecewise partitioning remains Task 3.
5. Run focused GREEN roots/domain tests, relevant numeric-context regressions, then a complete suite gate before Task 2 closure.
6. Keep version at 0.9.0 until Task 12.
7. Do not merge without explicit user approval and do not invoke Codex unless explicitly authorized.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.0 remains canonical on `main@cdc454db7ea43e57e334d523afded8b4ef498ded`. Active 0.9.1 work is on `feature/v0.9.1-exact-characteristics`; the user approved the written design and selected inline execution. Task 1 is complete: parser RED **20 failed / 4 passed**, parser GREEN **65/65**, typed-model RED was the intended missing-import failure, typed-model GREEN **78/78**, and the authoritative complete Task 1 regression gate was **758/758 PASS in 121.72 s** (Actions `33335640543`, job `99321927179`). Temporary Task 1 harness files have been removed. Resume with Task 2 RED for finite unit-aware domains and exact continuous roots. Never merge without explicit user approval and never invoke Codex without explicit authorization.
