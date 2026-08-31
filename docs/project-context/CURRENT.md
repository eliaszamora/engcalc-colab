# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.1 remains the canonical released baseline. The approved 0.9.2 Audit Remediation & Reliability plan is active on `feature/v0.9.2-audit-reliability`. Tasks 1–11 are complete and Task 12 is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**, re-verified unchanged after Task 11.
- Runtime/package version remains **0.9.1**; the 0.9.2 version bump is deferred to Task 14.
- `requires-python` remains **`>=3.10`**.
- Runtime dependencies now include **`ipython>=8.18`**.
- Test/dev metadata includes **`tomli>=2.0; python_version < '3.11'`** so the test suite itself remains valid on advertised Python 3.10.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- Permanent CI: `.github/workflows/ci.yml`, PR + push-to-`main`, Python **3.10–3.14** matrix.
- Approved spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-design.md`.
- Approved/refined plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-implementation.md`.
- Persistent audit regressions: `tests/test_v092_audit_regressions.py`.
- Persistent audit-risk evidence: `tests/test_v092_risk_probes.py`.
- Never invoke Codex / Codex Cloud without explicit user authorization.
- Never merge the release PR without explicit user approval.

## 0.9.2 task status

1. **COMPLETE** — independent C-1/H-1 natural RED.
2. **COMPLETE** — closed real finite SymPy evaluation.
3. **COMPLETE** — complete/non-silent roots + exact/numeric merge.
4. **COMPLETE** — intersections share zero-set semantics.
5. **COMPLETE** — explicit real engineering symbols, identity-safe reconstruction, scaled-`Abs` extrema, inverse-trig unit preservation.
6. **COMPLETE** — centralized unit-literal bounds and zero-bound physical-unit preservation.
7. **COMPLETE** — selected Piecewise boundary branches, dimensional zero normalization, continuous/discontinuous topology.
8. **COMPLETE** — explicit characteristic renderer misuse diagnostics + actionable unresolved Piecewise-symbol guidance.
9. **COMPLETE** — numeric Matplotlib title weight, exact rational x-coordinate labels, negative-zero presentation regression.
10. **COMPLETE** — residual, tri-state-realness and simplify-cost audit risks investigated; all **not reproduced; no product change**.
11. **COMPLETE** — permanent Python 3.10–3.14 CI + declared IPython runtime dependency + Python 3.10 TOML-test compatibility.
12. **NEXT** — behavior-preserving `characteristics.py` package decomposition behind stable public imports.
13. acceptance/docs/full regression.
14. 0.9.2 version/release validation/PR; STOP before merge.

## Product/evidence commits

- Task 5: **`2b6be7d22817cee3c1267495e58635d3bb06fc9d`** — `fix: make engineering symbols explicitly real`.
- Task 6: **`c115bc9d810e8552a8d5138c88bfffcb3f55cb76`** — `fix: centralize direct unit literal bounds`.
- Task 7: **`d2ae961bf3be34c2b52b1afbc54b4963f7ceb156`** — `fix: normalize Piecewise extrema topology`.
- Task 8: **`833009fedcf257c18e84e8ea0992e4f613a5d52d`** — `fix: make characteristic diagnostics explicit`.
- Task 9: **`5363bfc54a5f4d27a2f1b79f309e6a383eb17a2e`** — `fix: polish exact characteristic presentation`.
- Task 10: no product commit; persistent evidence **`87ee04cf13fd86993245a9f62f1e55c64a6d2f8b`** — `test: investigate characteristic audit risks`.
- Task 11 product/infrastructure: **`c8c2dd9be63df5c3b7925bbfafe32d607c2372a7`** — `ci: validate EngCalc across Python 3.10 to 3.14`.
- Task 11 cleanup: **`93c271d47b087d6b1a9dfe59b7253f3d7b920ebe`** and **`4473788e4d3bffdbd2f917357e09fc19bf44ff56`** remove only the temporary patcher/workflow.

Tasks 1–4 are complete in branch history and remain covered by persistent audit/root/intersection regressions.

## Reliability contract established through Task 11

- External audit findings receive EngCalc-owned RED reproduction before correction.
- Exact-first remains authoritative; deterministic fallback supplements incomplete exact discovery.
- Exact provenance wins when exact and numeric candidates represent the same physical location.
- Plausible exact-candidate evaluation failure never silently becomes “no solution.”
- `roots()` and `intersections()` share one continuous zero-set discovery/validation/fallback/merge policy.
- Engine-created engineering symbols are `sp.Symbol(name, real=True)`.
- Identity-sensitive reconstruction reuses matching free-symbol identity whenever available.
- Supported unit literals work consistently across roots/intersections/extrema/plot/table.
- Original AST numeric-bound evaluation preserves dimensional zero bounds such as `0*m` before SymPy simplification.
- Piecewise physical boundaries preserve the selected governing branch symbolically.
- Continuous Piecewise breakpoints collapse redundant `left/at/right` records only when physically equivalent; discontinuities remain explicit.
- `render_result()` explicitly rejects characteristic results and directs callers to `render_characteristic_result()`.
- Missing Piecewise characteristic numeric values reuse stable actionable unresolved-symbol hints.
- Matplotlib plot-title weight uses numeric **600**.
- Exact ordinary-plot characteristic requests retain `point.x_symbolic`; sampled/envelope requests retain `x_symbolic=None`.
- Non-integer exact SymPy rationals use compact `p/q` x labels while marker coordinates remain physical numeric coordinates.
- Characteristic HTML near-zero normalization remains governed by `RenderSettings.zero_tolerance`.
- Ordinary plots retain 201 drawing samples and exact metadata; positive structural moment remains plotted downward.
- `envelope(...)` remains sampled in 0.9.2; exact envelopes are deferred to 0.9.3.
- No SciPy dependency.
- Investigation-only audit concerns from Task 10 did not justify speculative product changes.
- IPython is a declared runtime dependency rather than an assumed notebook-host dependency.
- Advertised Python support remains 3.10+ and is permanently CI-validated through 3.14.

## Validation evidence — Task 10

- Persistent probes cover residual/near-zero behavior, tri-state `is_real is None`, and simplify-cost regression.
- Classification for all three: **not reproduced; no product change**.
- Run **`33358168465`**, job **`99384201915`**: **39/39 focused + 880/880 full PASS**; `No Task 10 product patch exists.`
- Idempotent job **`99384850174`** repeated **39/39 + 880/880** with the same no-product-diff result.
- Temporary Task 10 workflow removed in **`4e9f73c94f426e11a3c0b81d9a3598c3d6163da3`**.

## Validation evidence — Task 11

### RED and compatibility finding

- Initial metadata RED established that `requires-python >=3.10` was already correct but IPython was undeclared.
- The first Python matrix exposed a real **test-infrastructure compatibility defect on Python 3.10**: `tests/test_packaging.py` and `tests/test_version.py` imported stdlib `tomllib`, unavailable on 3.10, and the packaging test still asserted the superseded contract that IPython must not be runtime-managed.
- Corrective scope stayed outside `src/`: add conditional dev `tomli`, use `tomllib`/`tomli` fallback in those tests, and update the runtime-dependency contract.

### Authoritative five-version GREEN

Run **`33358958365`** validated the candidate before persistence. Every job installed only `.[dev]`, with **no ad-hoc IPython install**, compiled the package, passed `tests/test_packaging_metadata.py`, and passed the complete suite **881/881**:

- Python **3.10** — job **`99386459903`** — resolved **IPython 8.39.0** — SUCCESS — **881/881**.
- Python **3.11** — job **`99386460066`** — resolved **IPython 9.17.0** — SUCCESS — **881/881**.
- Python **3.12** — job **`99386460051`** — resolved **IPython 9.17.0** — SUCCESS — **881/881**.
- Python **3.13** — job **`99386460059`** — resolved **IPython 9.17.0** — SUCCESS — **881/881**.
- Python **3.14** — job **`99386460063`** — resolved **IPython 9.17.0** — SUCCESS — **881/881**.

The run’s attempted push was rejected only because the Actions token cannot create/update workflow files without workflow permission; the already-validated five-file tree was persisted through the authorized GitHub connection as product commit **`c8c2dd9be63df5c3b7925bbfafe32d607c2372a7`**.

### Idempotence / cleanup

- Idempotent run **`33359297689`** repeated all five Python **3.10–3.14** jobs successfully with the full **881/881** suite.
- Idempotent commit job **`99388058367`** ended with exact output: **`No Task 11 product or test patch to commit.`**
- Comparison `c8c2dd9...4473788` contains only removal of `.github/scripts/v092_task11_green.py` and `.github/workflows/v092-task11-validation.yml`.
- Permanent `.github/workflows/ci.yml` remains. It runs on pull requests and pushes to `main` using Python 3.10–3.14.
- `main` remains **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**.
- Package/runtime version remains **0.9.1**.

## Exact next step — Task 12

Task 12 is a **behavior-preserving architecture refactor**. No intentional output or solver-semantic change is allowed.

1. Establish pre-refactor GREEN with `compileall` and the full test suite.
2. Replace monolithic `src/engcalc_colab/characteristics.py` with package `src/engcalc_colab/characteristics/`:
   - `__init__.py`
   - `domain.py`
   - `candidates.py`
   - `fallback.py`
   - `roots.py`
   - `intersections.py`
   - `extrema.py`
   - `piecewise_analysis.py`
3. Move domain/Piecewise infrastructure first; keep formulas/tolerances equivalent.
4. Move deterministic fallback and exact-candidate discovery/validation/merge infrastructure.
5. Move roots/intersections/extrema operation solvers.
6. Preserve stable public imports through an explicit `characteristics/__init__.py` facade.
7. Update only tests that monkeypatch private implementation details so they target the responsible submodule; do not expose private compatibility aliases merely for old test paths.
8. Run the stable-import gate, complete suite, then focused characteristic/plot/magic/matrix suites. No output change is permitted.
9. Commit the refactor alone as `refactor: split characteristic solver by responsibility`, then perform idempotence/cleanup/context closure before Task 13.

## Still deferred / open

- Task 12: behavior-preserving characteristics package decomposition.
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
- **0.9.2 Audit Remediation & Reliability:** **Tasks 1–11 COMPLETE; Task 12 NEXT**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`; runtime/package version remains 0.9.1 and `requires-python` remains `>=3.10`. Tasks 1–11 are complete. Task 11 product is `c8c2dd9be63df5c3b7925bbfafe32d607c2372a7`; idempotent run `33359297689` passed the full 881-test suite on Python 3.10–3.14 and commit job `99388058367` reported `No Task 11 product or test patch to commit.` Only the temporary Task 11 patcher/workflow were removed afterward; permanent `ci.yml` remains. Task 12 is next and must preserve behavior while splitting `characteristics.py` behind stable public imports. Never invoke Codex without explicit authorization.