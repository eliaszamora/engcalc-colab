# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.1 exact characteristics is release-validated on `feature/v0.9.1-exact-characteristics`. Tasks 1–12, real-wheel validation, source-free validation, and the final clean pre-PR gate are complete. All temporary validation workflows/scripts are removed. The exact next step is to verify the final compare, open the 0.9.1 PR, and STOP before merge for explicit user approval._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated release on `main`: **EngCalc 0.9.0 Matrix/CAS**.
- Canonical 0.9.1 base: **`main@cdc454db7ea43e57e334d523afded8b4ef498ded`**.
- Active branch: **`feature/v0.9.1-exact-characteristics`**.
- Runtime/package version: **0.9.1**.
- Verified release metadata commit: **`e997d93a69d1ba3589dc48a9ce945b1037476967`**.
- Authoritative wheel-validation SHA: **`2628186afd409cf2a1ec898a39a6e8c5ed5f6f2b`**.
- Final pre-PR gate SHA: **`50581b6ab8fdf46b072577bd1b2e189711761a73`**.
- Final gate cleanup commit: **`03c56a89d1e42a107d34fe078e80ba63da4adf0a`**.
- Approved design spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
- Approved implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.1-exact-characteristics-implementation.md`.
- User selected **inline execution / executing-plans**.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge 0.9.1 into `main` without explicit user approval.

## Approved behavior

- `%%eng` remains a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Numeric/Pint semantics, Piecewise, tables, plots, envelopes, multi-argument functions and Matrix/CAS behavior remain regression requirements.
- Whole matrices remain invalid scalar characteristic/plot/table/envelope responses; indexed scalar matrix expressions remain supported.
- Positive structural moment remains plotted **downward**.
- Ordinary plots retain the 201-point drawing grid; that grid is not the authoritative characteristic solver.
- Public standalone 0.9.1 calls are:
  `extrema(response, variable, lower, upper)`,
  `roots(response, variable, lower, upper)`,
  `intersections(response_1, response_2, variable, lower, upper)`.
- Characteristic calls are standalone-only in 0.9.1; assignment/nesting/composition are rejected.
- The characteristic core is exact-first, unit-aware, Piecewise-safe, deterministic on numeric fallback, scalar-only, and preserves exact/numeric provenance and interval topology.
- Standalone rendering shows exact `=` versus numeric fallback `≈`.
- Ordinary `plot(...)` carries exact characteristic metadata independently of its drawing grid.
- `envelope(...)` remains sampled in 0.9.1; exact crossovers/governing intervals are deferred to **0.9.2**.

## Open issues / user feedback

- No blocking 0.9.1 product, packaging, wheel, source-free, or pre-PR validation issue remains.
- **Tasks 1–12 and final pre-PR validation are complete.**
- Remaining release administration: verify final compare, open the release PR, then STOP before merge.
- `no_vertical_scroll()` remains a separate ergonomics issue.
- Multiline ordinary non-matrix function-call parsing remains separate.
- Generalized structural eigenproblems remain deferred.

## Validation evidence

### Canonical 0.9.0 release

- Release run **`33332233490`**, job **`99312713507`**.
- Release contract **23/23 GREEN**.
- Source before wheel **721/721 GREEN in 142.99 s**.
- Wheel `engcalc_colab-0.9.0-py3-none-any.whl`; SHA-256 **`ea66fa231b5657695e2c38cefb324da220070a2f7c86557dddef19d2017a0719`**.
- Source-free installed-wheel suite **721/721 GREEN in 141.38 s**.
- Final source revalidation **721/721 GREEN in 139.76 s**.

### 0.9.1 Tasks 1–10

- Task 1: **758/758 full GREEN**.
- Task 2: **772/772 full GREEN**.
- Task 3: **783/783 full GREEN**.
- Task 4: **794/794 full GREEN**.
- Task 5: **800/800 full GREEN**.
- Task 6: **808/808 full GREEN**.
- Task 7: **820/820 full GREEN**.
- Task 8 run **`33340983117`**, job **`99336452342`** — **828/828 full GREEN in 104.51 s**.
- Task 9 run **`33341538689`**, job **`99337950723`** — **835/835 full GREEN in 117.02 s**.
- Task 10 run **`33342633493`**, job **`99340916954`** — `compileall` PASS, diff hygiene PASS, **844/844 full GREEN in 142.78 s**.

### 0.9.1 Task 11

- Unit-literal correction: **`10e40c6b598f6005a26de1e52b75c512c8f87d50`**.
- README product: **`3d4eb51651c8011895c2e6b715e9d66a52fd1c29`**.
- Authoritative gate SHA **`ae9cd3270edfb5b9b55e651cc3757f56c0369c80`**.
- Run **`33343511326`**, job **`99343282200`**.
- `compileall`: PASS; diff hygiene: PASS; acceptance **2/2 PASS in 1.23 s**; full source **846/846 PASS in 98.43 s**.
- All Task 11 temporary validation files were removed.

### 0.9.1 Task 12 release validation

- Intentional version RED: **6 failed / 5 passed in 0.08 s**, exclusively the expected 0.9.0 → 0.9.1 mismatch.
- First GREEN attempt run **`33343868704`**, job **`99344237909`**: release contract and `compileall` passed; full suite exposed one stale parser version assertion — **845 passed / 1 failed in 175.29 s**. No release bump was committed from that failed run.
- Effective stale-version test correction: **`a358ed15910b6393399d86f3c9ce8383d0e82040`**; product behavior unchanged.
- Successful metadata GREEN run **`33344172956`**, job **`99345049612`**: focused release contract **11/11 PASS in 0.05 s**, source **846/846 PASS in 172.60 s**.
- Verified release metadata commit: **`e997d93a69d1ba3589dc48a9ce945b1037476967`**.
- Authoritative wheel-validation SHA **`2628186afd409cf2a1ec898a39a6e8c5ed5f6f2b`**, run **`33344486134`**, job **`99345919150`**: SUCCESS.
- Committed release contract including parser: **23/23 PASS in 0.05 s**.
- Real wheel: **`engcalc_colab-0.9.1-py3-none-any.whl`**.
- Wheel metadata version: **0.9.1**.
- Wheel SHA-256: **`f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`**.
- External clean-venv/site-packages smoke: **PASS**.
- Installed-wheel source-free suite: **846/846 PASS in 90.59 s**.
- Post-wheel source suite: **846/846 PASS in 89.52 s**.
- Evidence artifact: `engcalc-0.9.1-release-validation`, artifact ID **`9741591634`**, artifact ZIP SHA-256 **`39453d375a3148fb27b3944d398f48381665f17edb0a17f4c9c09fa8fee9b4c0`**.
- All Task 12 release-validation workflows/scripts were removed before the final pre-PR gate.

### Final clean pre-PR gate

- Gate SHA: **`50581b6ab8fdf46b072577bd1b2e189711761a73`**.
- Run **`33345708275`**, job **`99349296928`**: SUCCESS.
- Python **3.13.15**.
- Explicit checks confirmed all prior Task 12 harness files absent and version metadata/README at 0.9.1.
- `python -m compileall -q src/engcalc_colab`: PASS.
- `git diff --check origin/main...HEAD`: PASS.
- Committed release contract: **23/23 PASS in 0.07 s**.
- Complete source suite: **846/846 PASS in 111.56 s**.
- Temporary final-gate workflow removed immediately afterward in cleanup commit **`03c56a89d1e42a107d34fe078e80ba63da4adf0a`**.
- `.github/workflows` and `.github/scripts` are absent after cleanup.
- No Codex review or Codex Cloud has been invoked.

## Roadmap / active plan

- **0.9.0 Matrix/CAS:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.1 Tasks 1–12:** COMPLETE.
- **0.9.1 wheel/source-free/final pre-PR validation:** COMPLETE.
- **0.9.1 PR creation and merge approval checkpoint:** ACTIVE.
- Later: **0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Verify the final branch HEAD and compare against `main`.
2. Confirm no temporary `.github` validation file is present in the final compare.
3. Confirm no existing open PR already uses `feature/v0.9.1-exact-characteristics` as head.
4. Open PR **`release: EngCalc 0.9.1 exact characteristics`** targeting `main`.
5. **STOP before merge** and request explicit user approval.
6. Never invoke Codex unless separately authorized.

## How to resume in a new conversation

Read this file first. `main@cdc454db7ea43e57e334d523afded8b4ef498ded` remains the released 0.9.0 baseline. Active branch is `feature/v0.9.1-exact-characteristics`, runtime/package version is 0.9.1, and all Tasks 1–12 plus wheel/source-free/final pre-PR validation are complete. Final clean gate is run `33345708275`, job `99349296928`, with `compileall` PASS, diff hygiene PASS, **23/23 release contract PASS**, and **846/846 complete source tests PASS in 111.56 s**. The final gate workflow is removed at cleanup commit `03c56a89d1e42a107d34fe078e80ba63da4adf0a`; no validation workflow/script should remain. Resume by verifying the final compare, creating the 0.9.1 release PR, and STOP before merge. Never merge without explicit user approval; never invoke Codex without explicit authorization.
