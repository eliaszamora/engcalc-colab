# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.1 remains the canonical released baseline. The approved 0.9.2 Audit Remediation & Reliability plan is active on `feature/v0.9.2-audit-reliability`. Tasks 1–12 are complete; Task 13 is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**, re-verified unchanged through Task 12.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- Runtime/package version remains **0.9.1**; the 0.9.2 version bump is deferred to Task 14.
- `requires-python` remains **`>=3.10`**.
- Runtime dependencies include **`ipython>=8.18`**.
- Dev/test compatibility includes **`tomli>=2.0; python_version < '3.11'`**.
- Permanent CI: `.github/workflows/ci.yml`, PR + push-to-`main`, Python **3.10–3.14** matrix.
- Approved spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-design.md`.
- Approved plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-implementation.md`.
- Persistent audit regressions: `tests/test_v092_audit_regressions.py`.
- Persistent audit-risk evidence: `tests/test_v092_risk_probes.py`.
- Never invoke Codex / Codex Cloud without explicit user authorization.
- Never merge the release PR without explicit user approval.

## 0.9.2 task status

1. **COMPLETE** — independent C-1/H-1 natural RED.
2. **COMPLETE** — closed real finite SymPy evaluation.
3. **COMPLETE** — complete/non-silent roots + exact/numeric merge.
4. **COMPLETE** — intersections share zero-set semantics.
5. **COMPLETE** — explicit-real engineering symbols, identity-safe reconstruction, scaled-`Abs` extrema, inverse-trig unit preservation.
6. **COMPLETE** — centralized direct unit-literal bounds and dimensional-zero preservation.
7. **COMPLETE** — selected Piecewise boundary branches, dimensional-zero normalization, continuous/discontinuous topology.
8. **COMPLETE** — explicit characteristic renderer misuse diagnostics + actionable unresolved Piecewise-symbol guidance.
9. **COMPLETE** — numeric Matplotlib title weight, exact rational x-coordinate labels, negative-zero presentation regression.
10. **COMPLETE** — residual, tri-state-realness and simplify-cost audit risks investigated; all **not reproduced; no product change**.
11. **COMPLETE** — permanent Python 3.10–3.14 CI + declared IPython runtime dependency + Python 3.10 TOML-test compatibility.
12. **COMPLETE** — behavior-preserving `characteristics.py` package decomposition behind stable public imports.
13. **NEXT** — broaden natural-input acceptance, rename v0.9.3 envelope acceptance, README reliability documentation, complete regression + hygiene.
14. 0.9.2 version/release validation/PR; **STOP before merge**.

## Product/evidence commits

- Task 5: **`2b6be7d22817cee3c1267495e58635d3bb06fc9d`** — `fix: make engineering symbols explicitly real`.
- Task 6: **`c115bc9d810e8552a8d5138c88bfffcb3f55cb76`** — `fix: centralize direct unit literal bounds`.
- Task 7: **`d2ae961bf3be34c2b52b1afbc54b4963f7ceb156`** — `fix: normalize Piecewise extrema topology`.
- Task 8: **`833009fedcf257c18e84e8ea0992e4f613a5d52d`** — `fix: make characteristic diagnostics explicit`.
- Task 9: **`5363bfc54a5f4d27a2f1b79f309e6a383eb17a2e`** — `fix: polish exact characteristic presentation`.
- Task 10: no product commit; persistent evidence **`87ee04cf13fd86993245a9f62f1e55c64a6d2f8b`** — `test: investigate characteristic audit risks`.
- Task 11 product/infrastructure: **`c8c2dd9be63df5c3b7925bbfafe32d607c2372a7`** — `ci: validate EngCalc across Python 3.10 to 3.14`.
- Task 11 cleanup: **`93c271d47b087d6b1a9dfe59b7253f3d7b920ebe`**, **`4473788e4d3bffdbd2f917357e09fc19bf44ff56`**.
- Task 12 product: **`cee4b39e19d2f6f2c49595d8a46efcdd6f1d58ce`** — `refactor: split characteristic solver by responsibility`.
- Task 12 cleanup: **`6ccf182cef34fc3874793e2b8c5bf0816b13a92d`** — `test: clean task12 validation infrastructure`.

Tasks 1–4 remain complete in branch history and covered by persistent audit/root/intersection regressions.

## Reliability contract established through Task 12

- External audit findings receive EngCalc-owned RED reproduction before correction.
- Exact-first remains authoritative; deterministic fallback supplements incomplete exact discovery.
- Exact provenance wins when exact and numeric candidates represent the same physical location.
- Plausible exact-candidate evaluation failure never silently becomes “no solution.”
- `roots()` and `intersections()` share one continuous zero-set discovery/validation/fallback/merge policy.
- Engine-created engineering symbols are explicitly real.
- Identity-sensitive reconstruction reuses matching free-symbol identity whenever available.
- Supported unit literals work consistently across roots/intersections/extrema/plot/table.
- Original AST numeric-bound evaluation preserves dimensional-zero bounds such as `0*m` before SymPy simplification.
- Piecewise physical boundaries preserve the selected governing branch symbolically.
- Continuous Piecewise breakpoints collapse redundant `left/at/right` records only when physically equivalent; discontinuities remain explicit.
- `render_result()` explicitly rejects characteristic results and routes to `render_characteristic_result()`.
- Missing Piecewise characteristic numeric values reuse stable actionable unresolved-symbol hints.
- Matplotlib plot-title weight uses numeric **600**.
- Exact ordinary-plot characteristic requests retain `point.x_symbolic`; sampled/envelope requests retain `x_symbolic=None`.
- Non-integer exact SymPy rationals use compact `p/q` x labels while marker coordinates remain physical numeric coordinates.
- Characteristic HTML near-zero normalization remains governed by `RenderSettings.zero_tolerance`.
- Ordinary plots retain 201 drawing samples and exact metadata; positive structural moment remains plotted downward.
- `envelope(...)` remains sampled in 0.9.2; exact envelopes are deferred to 0.9.3.
- No SciPy dependency.
- IPython is a declared runtime dependency rather than an assumed notebook-host dependency.
- Advertised Python support is permanently CI-validated from 3.10 through 3.14.
- Characteristic solver internals are now decomposed by responsibility under `src/engcalc_colab/characteristics/`; stable public imports are preserved by `characteristics/__init__.py`.

## Validation evidence — Task 10

- Persistent probes cover residual/near-zero behavior, tri-state `is_real is None`, and simplify-cost regression.
- Classification for all three: **not reproduced; no product change**.
- Run **`33358168465`**, job **`99384201915`**: **39/39 focused + 880/880 full PASS**.
- Idempotent job **`99384850174`** repeated **39/39 + 880/880** with no product diff.
- Temporary Task 10 workflow removed in **`4e9f73c94f426e11a3c0b81d9a3598c3d6163da3`**.

## Validation evidence — Task 11

- Initial RED confirmed advertised Python support was already `>=3.10` but IPython was undeclared.
- First matrix exposed test-infrastructure incompatibility on Python 3.10 (`tomllib`); corrected with conditional `tomli` and test fallback, without changing product semantics.
- Authoritative run **`33358958365`**: Python 3.10, 3.11, 3.12, 3.13 and 3.14 each passed **881/881** after installing only `.[dev]`.
- Jobs: **`99386459903`**, **`99386460066`**, **`99386460051`**, **`99386460059`**, **`99386460063`**.
- Idempotent run **`33359297689`** repeated all five versions GREEN; commit job **`99388058367`** reported **`No Task 11 product or test patch to commit.`**
- Permanent `.github/workflows/ci.yml` remains; only Task 11 temporary infrastructure was removed.

## Validation evidence — Task 12

### Pre-refactor baseline

- Baseline commit **`e249cfc7c3180e08a434cf5cab3a0fc0b1fb041c`**.
- Run **`33359923576`**, job **`99389160145`**.
- `compileall` PASS and monolithic full suite **881/881 PASS in 200.90 s**.

### Mechanical candidate failures — no product persisted

1. Run **`33360284005`**, job **`99390172266`**: **13 failed / 868 passed**. Generated `intersections.py` omitted the `_fallback_roots` import. Classified as splitter wiring defect; no product commit.
2. Run **`33360499583`**, job **`99390769603`**: generated `candidates.py` used `_FALLBACK_X_DEDUP_REL_TOL` without importing it from `fallback.py`. Classified as splitter dependency-wiring defect; no product commit.
3. Run **`33361479616`**, job **`99393547819`**: `tests/test_characteristics_acceptance.py` still monkeypatched the old monolithic private target `characteristics._exact_real_solution_set`. Per plan, the test was retargeted to `characteristics.candidates`; no private facade alias was added and no product candidate was persisted from the failing run.

### Authoritative GREEN and product persistence

- Successful candidate run **`33361626996`** on the corrected splitter/private-test wiring.
- Stable public imports PASS.
- `compileall` PASS.
- Full suite **881/881 PASS in 206.46 s**.
- Focused characteristic/plot/magic/matrix regression **347/347 PASS in 80.68 s**.
- Decomposition shape/private-target gate PASS.
- Product commit **`cee4b39e19d2f6f2c49595d8a46efcdd6f1d58ce`** contains exactly:
  - removal of monolithic `src/engcalc_colab/characteristics.py`;
  - package modules `__init__.py`, `domain.py`, `candidates.py`, `fallback.py`, `roots.py`, `intersections.py`, `extrema.py`, `piecewise_analysis.py`;
  - private monkeypatch retargets in `tests/test_characteristics_acceptance.py` and `tests/test_characteristics_fallback.py`.
- No unrelated product file changed.

### Idempotence and cleanup

- A first post-product rerun (`33362037335`) had GREEN product tests but its auxiliary commit job failed only because the temporary harness tried to `git add` the already-deleted monolith path. The splitter correctly reported `Task 12 decomposition already materialized.` This was harness-only and caused no product patch.
- Final path-safe idempotent run **`33362287774`**:
  - test job **`99395831492`** SUCCESS;
  - full suite **881/881 PASS in 172.04 s**;
  - focused regression **347/347 PASS in 67.15 s**;
  - public-import, `compileall`, package-shape and private-target gates PASS;
  - commit job **`99396580569`** SUCCESS with exact output **`No Task 12 product or test patch to commit.`**
- Cleanup commit **`6ccf182cef34fc3874793e2b8c5bf0816b13a92d`** removes only `.github/scripts/v092_task12_split.py` and `.github/workflows/v092-task12-validation.yml`.
- Compact compare `cee4b39...6ccf182` confirms no product changes after the authoritative refactor commit other than deletion of temporary Task 12 infrastructure.
- Permanent `.github/workflows/ci.yml` remains intact.
- `main` remains **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**.
- Runtime/package version remains **0.9.1**.

## Exact next step — Task 13

Task 13 is **acceptance/docs/full regression** and must not change solver product behavior.

1. Extend `tests/test_characteristics_acceptance.py` with natural-input acceptance for:
   - real engineering symbol + inverse trig (`asin(delta/L)`),
   - unit-literal root domains (`domain=(0*m, 3*m)`),
   - Piecewise extrema with units,
   - transcendental roots and ordinary plot roots over `(0.0, 15.0)` with expected `2*pi` and `4*pi`.
2. Rename `tests/test_v092_acceptance.py` to `tests/test_v093_envelope_acceptance.py` and rename only the envelope-deferment test to `...until_v093`; assertions stay unchanged.
3. Add a concise README reliability note covering exact-first + deterministic fallback, explicit-real symbols, natural unit domains, Piecewise boundary selection, exact coordinate display validity, exact annotation identity, Python 3.10–3.14 CI, declared IPython dependency, the `characteristics` package split, and sampled-envelope deferment to 0.9.3. Use natural EngCalc syntax, not dependency-qualified syntax.
4. Required gates:
   - `python -m compileall -q src/engcalc_colab`
   - `pytest -q tests/test_characteristics_acceptance.py tests/test_v093_envelope_acceptance.py`
   - `pytest -q`
   - `git diff --check`
   - README hygiene grep for accidental `expression.`, `expression[`, `matplotlib.`, `plt.`, `sp.`, `sympy.`, `np.` syntax.
5. Refresh this file with exact Task 13 pass counts and handoff commands.
6. Commit only README/context/acceptance changes as **`docs: complete 0.9.2 reliability acceptance`** after GREEN.
7. Do not start Task 14 until Task 13 is fully closed. Task 14 performs the 0.9.2 version/release validation/PR and must STOP before merge.

## Still deferred / open

- Task 13: acceptance/docs/full regression.
- Task 14: 0.9.2 version/release validation/PR; STOP before merge.
- Separate deferred issues: `no_vertical_scroll()`, multiline ordinary non-matrix call parsing, generalized structural eigenproblems.
- 0.9.3: Exact Envelopes / Governing Intervals.
- 0.9.4: Named Response Cases / Combinations.

## Canonical 0.9.1 evidence

- `main@698696bb8854fa197851cdbb2f5e4c08ef22178b` remains unchanged.
- Runtime/package metadata on the active branch remains **0.9.1**.
- 0.9.1 final pre-PR: **23/23 release contract; 846/846 full source**.
- Real wheel SHA-256: `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`.
- Post-merge source validation: **846/846 PASS**.

## Roadmap

- **0.9.0 Matrix/CAS:** COMPLETE + MERGED.
- **0.9.1 Exact Characteristics:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.2 Audit Remediation & Reliability:** **Tasks 1–12 COMPLETE; Task 13 NEXT**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`; runtime/package version is still 0.9.1. Tasks 1–12 are complete. Task 12 product commit is `cee4b39e19d2f6f2c49595d8a46efcdd6f1d58ce`; final idempotent run `33362287774` passed 881/881 full + 347/347 focused and commit job `99396580569` reported `No Task 12 product or test patch to commit.` Cleanup `6ccf182cef34fc3874793e2b8c5bf0816b13a92d` removed only temporary Task 12 infrastructure; permanent CI remains. Task 13 is next: acceptance tests + v0.9.3 envelope-test rename + README reliability note + full regression/hygiene, then commit `docs: complete 0.9.2 reliability acceptance`. Never invoke Codex without explicit authorization.