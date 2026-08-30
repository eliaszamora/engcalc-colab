# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.0 Matrix/CAS remains the canonical integrated release on `main`. EngCalc 0.9.1 exact characteristics is being implemented inline on its dedicated feature branch. Tasks 1 and 2 are complete and fully regression-tested. Task 2 temporary validation workflows have been removed. The exact next step is Task 3 RED for Piecewise roots, discontinuities, and infinite root intervals._

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
- Task 2 cleanup head before this context update: **`2e90014e2c1a5902e005e843f465c2cefb513f7d`**.
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
- One reusable exact-first characteristic-analysis core lives in `src/engcalc_colab/characteristics.py`.
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
- **Tasks 1 and 2 are complete. Task 3 is next.**
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

### 0.9.1 Task 1 — parser/API + typed models

- Parser RED: **20 failed / 4 passed** on run **`33335156057`**, job **`99320642585`**.
- Parser GREEN: **65/65 PASS** on run **`33335340109`**, job **`99321122672`**; product commit **`e7e92069d0858edef6684286c1c6f414d132e881`**.
- Typed-model RED: intended missing-type collection error on run **`33335416627`**, job **`99321328462`**.
- Typed-model GREEN: **78/78 PASS** on run **`33335470514`**, job **`99321471976`**; product commit **`b12a573c51f6dc6856f6d3b3652d674ffa4e8846`**.
- Authoritative Task 1 full gate: run **`33335640543`**, job **`99321927179`**, Python **3.13.15**; `compileall` PASS, `git diff --check` PASS, **758/758 PASS in 121.72 s**.
- All Task 1 temporary validation harness files were removed.

### 0.9.1 Task 2 — finite unit-aware domain + exact continuous roots

- Task 2 RED SHA: **`1a32d448d19969fda1f3b031826baa5e1adc73e6`**.
- RED run **`33335920700`**, job **`99322671165`**: intended collection failure, `ModuleNotFoundError: engcalc_colab.characteristics`, **1 error in 0.49 s**.
- Product implementation commit: **`e038b63332f2708c89faf85e5f099616747a529d`** (`feat: add exact continuous root analysis core`).
- First GREEN run **`33335992284`**, job **`99322863102`**: **13 passed / 1 failed**. The sole failure was a test-fixture issue: `ConditionSet(x, True, Reals)` simplifies to `Reals`, so it did not represent an unresolved symbolic solve. No product change was needed.
- Fixture-only correction commit: **`e0efefca06ea11a74ce52fd424b02fd78e4a9fa1`**.
- Focused recheck run **`33336075965`**, job **`99323088081`**: **14/14 PASS in 3.36 s**.
- Authoritative Task 2 full-gate SHA: **`fe0d0c8b591956ba32029bb216421eca628e1d09`**.
- Full-gate run **`33336114509`**, job **`99323194537`**, Python **3.13.15**.
- `compileall`: PASS.
- `git diff --check`: PASS.
- Focused roots + `NumericContext` + numeric-units regression gate: **30/30 PASS in 6.27 s**.
- Complete source suite: **772/772 PASS in 144.49 s**.
- Task 2 introduced `AnalysisDomain`, finite/unit-compatible closed-domain normalization, exact continuous root solving, exact symbolic coordinate preservation with evaluated Pint quantities, endpoint inclusion, repeated-root de-duplication, no-real-root handling, exact-domain filtering, dimensional response-zero preservation, and explicit unresolved signalling without inventing sampled answers.
- Both temporary Task 2 workflows were removed after validation; cleanup head before this context update: **`2e90014e2c1a5902e005e843f465c2cefb513f7d`**.
- No Codex review or Codex Cloud has been invoked.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **COMPLETE + RELEASE-VALIDATED + MERGED**.
- **0.9.1 Task 1 parser/API + typed result models:** **COMPLETE — 758/758 full GREEN**.
- **0.9.1 Task 2 finite unit-aware domain + exact continuous roots:** **COMPLETE — 772/772 full GREEN**.
- **0.9.1 Task 3 Piecewise roots, discontinuities + infinite root intervals:** **NEXT**.
- Then Tasks 4–12 per the approved implementation plan.
- Later releases: **0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Start Task 3 by writing Piecewise-root tests before changing `characteristics.py`.
2. RED must cover independent branch solving, branch open/closed endpoint topology, exact root at a defined breakpoint, no false root caused only by a jump sign-change, identically-zero Piecewise regions represented as `CharacteristicInterval` loci, interval clipping to the requested closed domain, de-duplication where branch endpoints coincide, and unresolved branch propagation without fabricated sampled roots.
3. Reuse `extract_symbolic_breakpoints(...)` / existing Piecewise primitives rather than duplicating breakpoint discovery.
4. Confirm Task 3 RED on an exact branch SHA in GitHub Actions.
5. Implement the minimum Piecewise partition/root extension in `characteristics.py`; do not start intersections/extrema early.
6. Run focused Task 3 GREEN + existing Piecewise regressions, then the full source suite before closing Task 3.
7. Keep version at 0.9.0 until Task 12.
8. Do not merge without explicit user approval and do not invoke Codex unless explicitly authorized.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.0 remains canonical on `main@cdc454db7ea43e57e334d523afded8b4ef498ded`. Active 0.9.1 work is on `feature/v0.9.1-exact-characteristics`; the user approved the written design and selected inline execution. Task 1 is complete with authoritative **758/758 PASS**. Task 2 is complete: RED was the intended missing `characteristics` module, focused GREEN **14/14**, expanded focused gate **30/30**, and authoritative full suite **772/772 PASS in 144.49 s** on Actions run `33336114509`, job `99323194537`; temporary Task 2 workflows were removed. Resume with Task 3 RED for Piecewise roots/discontinuities/infinite root intervals. Never merge without explicit user approval and never invoke Codex without explicit authorization.
