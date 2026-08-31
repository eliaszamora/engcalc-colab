# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.1 exact characteristics has completed Tasks 1–12 product/release validation on `feature/v0.9.1-exact-characteristics`. The real wheel and source-free installation are validated. All Task 12 release harness files have been removed. The only remaining work is the final clean pre-PR gate, PR creation, and an explicit STOP before merge._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated release on `main`: **EngCalc 0.9.0 Matrix/CAS**.
- Canonical 0.9.1 base: **`main@cdc454db7ea43e57e334d523afded8b4ef498ded`**.
- Active branch: **`feature/v0.9.1-exact-characteristics`**.
- Runtime/package version: **0.9.1**.
- Verified release metadata commit: **`e997d93a69d1ba3589dc48a9ce945b1037476967`** (`release: bump EngCalc to 0.9.1`).
- Authoritative wheel-validation SHA: **`2628186afd409cf2a1ec898a39a6e8c5ed5f6f2b`**.
- Clean Task 12 harness-removal head before this context update: **`db569ff37b6ee0fc21c45f0f87975eba1a56a291`**.
- Approved design spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
- Approved implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.1-exact-characteristics-implementation.md`.
- User selected **inline execution / executing-plans**.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge 0.9.1 into `main` without explicit user approval.

## Approved behavior

### Existing released behavior preserved

- `%%eng` remains a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Numeric/Pint semantics, Piecewise, tables, plots, envelopes, multi-argument functions and Matrix/CAS behavior remain regression requirements.
- Whole matrices remain invalid scalar characteristic/plot/table/envelope responses; indexed scalar matrix expressions remain supported.
- Positive structural moment remains plotted **downward**.
- Ordinary plot curves retain the 201-point sampling policy; the plot grid is never an authoritative characteristic solver.

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
- Fallback is deterministic, residual-validated, Piecewise-safe and independent of the public plotting grid; no SciPy runtime dependency was added.
- Roots, intersections and extrema preserve Piecewise topology, units, exact/numeric provenance, interval loci and explicit discontinuity semantics.
- Engine dispatch returns typed immutable `RootsResult`, `IntersectionsResult` and `ExtremaResult`, with operation-specific line-numbered diagnostics.
- Standalone characteristic rendering uses dedicated HTML/MathJax: exact points show `=`, numeric fallback shows `≈`.
- `PlotSeries` carries immutable exact characteristic metadata.
- Ordinary `plot(...)` keeps its 201-point drawing grid while exact global extrema are generated independently by the characteristic core.
- Plot presentation preserves the historical maximum one max / one min callout per series even when mathematical metadata contains several equivalent global points.
- Constant global-extremum intervals are not expanded into repeated plot markers.
- `envelope(...)` deliberately remains sampled in 0.9.1; exact crossover/governing-interval mathematics is deferred to **0.9.2**.

## Open issues / user feedback

- No blocking 0.9.1 product or release-validation issue remains.
- **Tasks 1–12 product/release validation are complete.**
- Remaining release administration: final clean pre-PR gate, PR creation, then STOP before merge.
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

### 0.9.1 Tasks 1–10

- Task 1: **758/758 full GREEN**.
- Task 2: **772/772 full GREEN**.
- Task 3: **783/783 full GREEN**.
- Task 4: **794/794 full GREEN**.
- Task 5: **800/800 full GREEN**.
- Task 6: **808/808 full GREEN**.
- Task 7: **820/820 full GREEN**.
- Task 8 authoritative run **`33340983117`**, job **`99336452342`** — **368/368 broad**, **828/828 full in 104.51 s**.
- Task 9 authoritative run **`33341538689`**, job **`99337950723`** — **387/387 broad in 49.23 s**, **835/835 full in 117.02 s**.
- Task 10 authoritative run **`33342633493`**, job **`99340916954`** — `compileall` PASS, diff hygiene PASS, **235/235 broad PASS in 62.91 s**, **844/844 full PASS in 142.78 s**.

### 0.9.1 Task 11 — acceptance/docs/pre-release regression

- Unit-literal correction: **`10e40c6b598f6005a26de1e52b75c512c8f87d50`**.
- README product: **`3d4eb51651c8011895c2e6b715e9d66a52fd1c29`**.
- Authoritative full-gate SHA: **`ae9cd3270edfb5b9b55e651cc3757f56c0369c80`**.
- Full-gate run **`33343511326`**, job **`99343282200`**.
- `compileall`: PASS.
- `git diff --check origin/main...HEAD`: PASS.
- Acceptance: **2/2 PASS in 1.23 s**.
- Complete source suite: **846/846 PASS in 98.43 s**.
- All Task 11 temporary validation artifacts were removed before Task 12.

### 0.9.1 Task 12 — release/version/wheel/source-free validation

- Intentional version RED: **6 failed / 5 passed in 0.08 s**, exclusively because tests expected 0.9.1 while runtime/package/README still reported 0.9.0.
- First release-GREEN attempt: run **`33343868704`**, job **`99344237909`**. Release contract and `compileall` passed, but full source gate exposed one stale historical assertion in `tests/test_parser.py`: **845 passed / 1 failed in 175.29 s**. No release bump was committed from that failed run.
- The stale parser expectation was corrected without product behavior changes. A temporary accidental partial-file edit was immediately superseded by restoring the full test file; the effective correction commit is **`a358ed15910b6393399d86f3c9ce8383d0e82040`**, with exactly one line changed relative to the pre-correction tree.
- Successful metadata GREEN: run **`33344172956`**, job **`99345049612`**.
- Focused release contract in that bump run: **11/11 PASS in 0.05 s**.
- Complete source suite before release commit: **846/846 PASS in 172.60 s**.
- Verified release metadata committed as **`e997d93a69d1ba3589dc48a9ce945b1037476967`**.
- Authoritative wheel-validation SHA: **`2628186afd409cf2a1ec898a39a6e8c5ed5f6f2b`**.
- Authoritative wheel-validation run **`33344486134`**, job **`99345919150`**: SUCCESS.
- Committed release contract including parser: **23/23 PASS in 0.05 s**.
- Built wheel: **`engcalc_colab-0.9.1-py3-none-any.whl`**.
- Wheel `METADATA` version: **0.9.1**.
- Wheel SHA-256: **`f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`**.
- External clean-venv import resolved from `/tmp/engcalc-v091-wheel-venv/lib/python3.13/site-packages/engcalc_colab/__init__.py`.
- External installed-wheel smoke: **PASS**. It exercised exact/unit-aware roots, extrema, intersections, Piecewise no-false-root behavior, indexed matrix scalar analysis, deterministic numeric fallback provenance, and the exact ordinary-plot peak at `x = 1/3` while retaining 201 drawing samples.
- Complete installed-wheel/source-free suite: **846/846 PASS in 90.59 s**.
- Complete source suite repeated after wheel validation: **846/846 PASS in 89.52 s**.
- Evidence artifact: `engcalc-0.9.1-release-validation`, artifact ID **`9741591634`**.
- Artifact zip SHA-256: **`39453d375a3148fb27b3944d398f48381665f17edb0a17f4c9c09fa8fee9b4c0`**.
- Task 12 release-validation workflow and all three temporary release scripts have been removed.
- Clean harness-removal head before this context update: **`db569ff37b6ee0fc21c45f0f87975eba1a56a291`**.
- No Codex review or Codex Cloud has been invoked.

## Roadmap / active plan

- **0.9.0 Matrix/CAS:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.1 Tasks 1–11:** COMPLETE.
- **0.9.1 Task 12 product/release/wheel/source-free validation:** COMPLETE.
- **0.9.1 final pre-PR clean gate + PR creation:** ACTIVE.
- Later: **0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Verify again that no prior Task 12 temporary workflow/script exists.
2. Run one fresh final pre-PR gate against the cleaned 0.9.1 release tree: `compileall`, `git diff --check origin/main...HEAD`, release contract, and complete source suite.
3. Remove the temporary final-gate workflow immediately after success and record its run/job/count/time here.
4. Verify the final compare against `main` contains no temporary `.github` validation infrastructure.
5. Open PR **`release: EngCalc 0.9.1 exact characteristics`** targeting `main`.
6. **STOP before merge** and request explicit user approval.
7. Never invoke Codex unless separately authorized.

## How to resume in a new conversation

Read this file first. `main@cdc454db7ea43e57e334d523afded8b4ef498ded` still carries released EngCalc 0.9.0. Active branch is `feature/v0.9.1-exact-characteristics`, runtime/package version is 0.9.1, release metadata commit is `e997d93a69d1ba3589dc48a9ce945b1037476967`, and Task 12 wheel/source-free validation is complete. Authoritative wheel run is `33344486134`, job `99345919150`; wheel SHA-256 is `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`; source-free and post-wheel source suites are both 846/846 GREEN. All release harness files are removed. Resume with the final clean pre-PR gate, remove that temporary gate, update this file, open the 0.9.1 PR, and STOP before merge. Never merge without explicit user approval; never invoke Codex without explicit authorization.
