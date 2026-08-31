# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.1 remains the canonical released baseline. The approved 0.9.2 Audit Remediation & Reliability plan is active on `feature/v0.9.2-audit-reliability`. Tasks 1–10 are complete and Task 11 is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**, re-verified unchanged after Task 10.
- Runtime/package version remains **0.9.1**; the 0.9.2 version bump is deferred to Task 14.
- `requires-python` remains **`>=3.10`**.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
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
11. **NEXT** — permanent Python 3.10–3.14 CI + declared IPython runtime dependency.
12. behavior-preserving characteristics package decomposition.
13. acceptance/docs/full regression.
14. 0.9.2 version/release validation/PR; STOP before merge.

## Product commits through Task 10

- Task 5: **`2b6be7d22817cee3c1267495e58635d3bb06fc9d`** — `fix: make engineering symbols explicitly real`.
- Task 6: **`c115bc9d810e8552a8d5138c88bfffcb3f55cb76`** — `fix: centralize direct unit literal bounds`.
- Task 7: **`d2ae961bf3be34c2b52b1afbc54b4963f7ceb156`** — `fix: normalize Piecewise extrema topology`.
- Task 8: **`833009fedcf257c18e84e8ea0992e4f613a5d52d`** — `fix: make characteristic diagnostics explicit`.
- Task 9: **`5363bfc54a5f4d27a2f1b79f309e6a383eb17a2e`** — `fix: polish exact characteristic presentation`.
- Task 10 has **no product commit**. Persistent evidence commit: **`87ee04cf13fd86993245a9f62f1e55c64a6d2f8b`** — `test: investigate characteristic audit risks`.

Tasks 1–4 are complete in branch history and remain covered by persistent audit/root/intersection regressions.

## Reliability contract now established

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
- Matplotlib plot-title weight uses numeric **600** rather than the environment-sensitive `semibold` string.
- Exact ordinary-plot characteristic requests retain `point.x_symbolic`; sampled/envelope requests retain `x_symbolic=None`.
- Non-integer exact SymPy rationals use compact `p/q` x labels while marker coordinates remain the exact physical numeric coordinate.
- Characteristic HTML near-zero normalization remains governed by `RenderSettings.zero_tolerance`.
- Ordinary plots retain 201 drawing samples and exact metadata; positive structural moment remains plotted downward.
- `envelope(...)` remains sampled in 0.9.2; exact envelopes are deferred to 0.9.3.
- No SciPy dependency.
- The three investigation-only audit concerns now have persistent evidence and did not justify speculative product changes.
- Permanent Python 3.10–3.14 CI and declared IPython dependency remain Task 11.

## Validation evidence — Task 5

- Product/idempotent gates: **7/7 + 122/122 + 69/69 + 862/862 PASS**.
- Product commit: `2b6be7d22817cee3c1267495e58635d3bb06fc9d`.

## Validation evidence — Task 6

- RED: run **`33352962308`**, job **`99369683201`**.
- GREEN: run **`33353557535`**, job **`99371326028`**.
- GREEN: **3/3 + 83/83 + 62/62 + 866/866 PASS**.
- Product: `c115bc9d810e8552a8d5138c88bfffcb3f55cb76`.
- Idempotence produced **`No Task 6 product or test patch to commit.`**

## Validation evidence — Task 7

- RED run **`33354710410`**, job **`99374541546`**: **2/2 new contracts FAILED** while **2/2 discontinuous representatives PASS**.
- GREEN run **`33354934109`**, job **`99375150144`**: **2/2 + 2/2 + 16/16 + 868/868 PASS**.
- Product: `d2ae961bf3be34c2b52b1afbc54b4963f7ceb156`.
- Idempotent run **`33355156480`**, job **`99375768821`** repeated the same counts and produced **`No Task 7 product or test patch to commit.`**

## Validation evidence — Task 8

- Initial RED run **`33355520272`**, job **`99376793403`**: **3 failed / 1 passed / 16 deselected**.
- Refined RED run **`33355576544`**, job **`99376959357`**: **4 failed / 1 passed / 16 deselected**.
- GREEN run **`33355653077`**, job **`99377170864`**: **5/5 + 45/45 + 873/873 PASS**.
- Product: `833009fedcf257c18e84e8ea0992e4f613a5d52d`.
- Idempotent run **`33355901981`**, job **`99377887051`** repeated **5/5 + 45/45 + 873/873** and produced **`No Task 8 product or test patch to commit.`**

## Validation evidence — Task 9

### RED discovery

- Initial RED commit **`5a8e78556b82dbad135ce47ba28d730540acd31c`**; run **`33356719340`**, job **`99380196396`**: **1 failed / 2 passed / 22 deselected**.
- Exact-rational label reproduced L-4: physical marker location was `x=1/3`, but text was `(0.33, 2)`.
- Warning capture and negative-zero cases were already GREEN and were not misreported as failures.
- Refined RED commit **`77f85faa427159f36ea535d30a6857b81077ba38`**; run **`33356828336`**, job **`99380499387`**: **2 failed / 2 passed / 22 deselected in 3.28 s**.
- Deterministic L-2 contract showed `axis.title.get_fontweight() == 'semibold'` rather than numeric `600`; exact rational annotation remained RED.

### Product GREEN / idempotence

- GREEN run **`33356956199`**, job **`99380850593`**: **4/4 contracts in 3.08 s + 37/37 focused in 19.08 s + 877/877 full in 184.92 s**.
- Product: **`5363bfc54a5f4d27a2f1b79f309e6a383eb17a2e`**.
- Idempotent run **`33357240791`**, job **`99381630477`**: **4/4 in 3.04 s + 37/37 in 19.00 s + 877/877 in 187.18 s**.
- Final output: **`No Task 9 product or test patch to commit.`**
- Cleanup head after removing temporary Task 9 infrastructure: **`c9a6dfc0ea6aec939bdcdb9838f02cbb5538ff4b`**.

## Validation evidence — Task 10

### Investigation classification

Persistent probes in `tests/test_v092_risk_probes.py` cover:

1. **Residual / near-zero observation:** `x - sp.Float("1.000000000000000001")` over `[0,2]` still yields one validated root near `1.0`; no false rejection or near-zero promotion defect reproduced.
2. **Tri-state `is_real is None`:** an unresolved `solveset` plus an unevaluable `solve()` hint `u` still forces deterministic fallback and returns the real root at `x=1`; no complex result or confident false empty set reproduced.
3. **`sp.simplify` cost:** the approved expanded polynomial fixture finds the root near `1` and completes below the deliberately loose 15-second ceiling; no pathological delay reproduced.

Classification for all three: **not reproduced; no product change**.

### Authoritative gate

- Temporary workflow prep commit: **`553196db7a307885ae6944e22cfccad2e057d0f0`**.
- Persistent evidence commit: **`87ee04cf13fd86993245a9f62f1e55c64a6d2f8b`**.
- Run **`33358168465`**, job **`99384201915`**: SUCCESS.
- Risk probes + roots/fallback focused regression: **39/39 PASS in 10.73 s**.
- Full source suite: **880/880 PASS in 180.74 s**.
- Product-diff check: **`No Task 10 product patch exists.`**

### Idempotence / cleanup

- Same run re-executed idempotently on the same commit; job **`99384850174`**: SUCCESS.
- Focused regression: **39/39 PASS in 10.54 s**.
- Full suite: **880/880 PASS in 183.60 s**.
- Product-diff check again: **`No Task 10 product patch exists.`**
- Temporary workflow removed in cleanup commit **`4e9f73c94f426e11a3c0b81d9a3598c3d6163da3`**.
- Comparison `87ee04c...4e9f73c` contains only removal of `.github/workflows/v092-task10-probes.yml`; persistent tests remain and no `src/` file changed.
- `.github` is absent after cleanup.
- `main` remains **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**.
- Package metadata remains **0.9.1**, `requires-python = ">=3.10"`; IPython is still intentionally undeclared until Task 11.

## Exact next step — Task 11

Task 11 adds permanent infrastructure and the notebook runtime dependency. Unlike Task 10, `.github/workflows/ci.yml` is a **permanent repository file** and must remain after validation.

1. Create `tests/test_packaging_metadata.py` with the approved RED contract:
   - `project["requires-python"] == ">=3.10"`;
   - `"ipython>=8.18" in project["dependencies"]`.
2. Run only that metadata test first. Expected RED: IPython is currently undeclared.
3. Add `ipython>=8.18` to runtime dependencies in `pyproject.toml`; do not narrow Python support or add an upper bound solely for Python 3.10.
4. Create permanent `.github/workflows/ci.yml` with `pull_request` and push-to-`main` triggers and a Python matrix **3.10, 3.11, 3.12, 3.13, 3.14**.
5. Each matrix job must:
   - set up its declared Python version;
   - upgrade pip;
   - install `python -m pip install -e '.[dev]'` with **no ad-hoc IPython install**;
   - compile `src/engcalc_colab`;
   - run the complete test suite.
6. Validate all five matrix jobs on the feature branch using temporary validation triggering only as necessary, while keeping the final permanent workflow contract exactly scoped to PRs and pushes to `main`.
7. Record for each interpreter: job ID, resolved IPython version, conclusion and exact test count. Any advertised-version failure is a compatibility bug; do not narrow support without explicit approval.
8. Commit the Task 11 product/infrastructure only after all five jobs are GREEN, then perform the normal idempotent/cleanup/context gate. The permanent `ci.yml` stays in the repository.
9. Never invoke Codex unless separately authorized.

## Still deferred / open after Task 10

- Task 11: permanent Python 3.10–3.14 CI + declared IPython dependency.
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
- **0.9.2 Audit Remediation & Reliability:** **Tasks 1–10 COMPLETE; Task 11 NEXT**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`; runtime/package version remains 0.9.1 and `requires-python` remains `>=3.10`. Tasks 1–10 are complete. Task 9 product is `5363bfc54a5f4d27a2f1b79f309e6a383eb17a2e`. Task 10 made no product change; its persistent evidence is `tests/test_v092_risk_probes.py` at commit `87ee04cf13fd86993245a9f62f1e55c64a6d2f8b`. Authoritative Task 10 run `33358168465` / job `99384201915` passed 39/39 focused + 880/880 full and reported `No Task 10 product patch exists.` Idempotent job `99384850174` repeated 39/39 + 880/880 with the same no-product-diff result. Temporary Task 10 workflow was removed in `4e9f73c94f426e11a3c0b81d9a3598c3d6163da3`; `.github` is absent before Task 11. All three audit risks are classified `not reproduced; no product change`. Task 11 is next: metadata RED for undeclared IPython, add `ipython>=8.18`, add permanent Python 3.10–3.14 CI, validate all five jobs, and retain the permanent workflow. Never invoke Codex without explicit authorization.