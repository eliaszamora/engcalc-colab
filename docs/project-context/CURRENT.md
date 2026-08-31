# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.1 remains the canonical released baseline. The approved 0.9.2 Audit Remediation & Reliability plan is active on `feature/v0.9.2-audit-reliability`. Tasks 1–9 are complete and Task 10 is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**, re-verified unchanged after Task 9.
- Runtime/package version remains **0.9.1**; the 0.9.2 version bump is deferred to Task 14.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- Approved spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-design.md`.
- Approved/refined plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-implementation.md`.
- Persistent audit regressions: `tests/test_v092_audit_regressions.py`.
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
10. **NEXT** — investigation-only audit risk probes; no speculative product fixes.
11. permanent Python 3.10–3.14 CI + declared IPython dependency.
12. behavior-preserving characteristics package decomposition.
13. acceptance/docs/full regression.
14. 0.9.2 version/release validation/PR; STOP before merge.

## Product commits through Task 9

- Task 5: **`2b6be7d22817cee3c1267495e58635d3bb06fc9d`** — `fix: make engineering symbols explicitly real`.
- Task 6: **`c115bc9d810e8552a8d5138c88bfffcb3f55cb76`** — `fix: centralize direct unit literal bounds`.
- Task 7: **`d2ae961bf3be34c2b52b1afbc54b4963f7ceb156`** — `fix: normalize Piecewise extrema topology`.
- Task 8: **`833009fedcf257c18e84e8ea0992e4f613a5d52d`** — `fix: make characteristic diagnostics explicit`.
- Task 9: **`5363bfc54a5f4d27a2f1b79f309e6a383eb17a2e`** — `fix: polish exact characteristic presentation`.

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
- Non-integer exact SymPy rationals use compact `p/q` x labels while marker coordinates remain the exact physical numeric coordinate. Integer and ordinary-decimal labels retain compact numeric formatting.
- Characteristic HTML near-zero normalization remains governed by `RenderSettings.zero_tolerance`; the Task 9 negative-zero audit case was already GREEN and is now protected by a persistent regression.
- Ordinary plots retain 201 drawing samples and exact metadata; positive structural moment remains plotted downward.
- `envelope(...)` remains sampled in 0.9.2; exact envelopes are deferred to 0.9.3.
- No SciPy dependency.
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

- Initial RED run **`33355520272`**, job **`99376793403`**: **3 failed / 1 passed / 16 deselected**; all L-1 renderer variants leaked `AttributeError`, while one proposed diagnostic case was already GREEN.
- Refined RED run **`33355576544`**, job **`99376959357`**: **4 failed / 1 passed / 16 deselected**, including the genuine `_piecewise_substitutions()` missing-hint path.
- GREEN run **`33355653077`**, job **`99377170864`**: **5/5 contracts + 45/45 focused + 873/873 full PASS**.
- Product: `833009fedcf257c18e84e8ea0992e4f613a5d52d`.
- Idempotent run **`33355901981`**, job **`99377887051`** repeated **5/5 + 45/45 + 873/873** and produced **`No Task 8 product or test patch to commit.`**
- Temporary infrastructure was removed; `.github` was absent before Task 9.

## Validation evidence — Task 9

### RED discovery

- Initial RED workflow commit: **`5a8e78556b82dbad135ce47ba28d730540acd31c`**.
- Initial run **`33356719340`**, job **`99380196396`**: **1 failed / 2 passed / 22 deselected**.
- Exact rational label reproduced L-4: the characteristic marker was at the correct physical `x=1/3`, but text was **`(0.33, 2)`** rather than carrying exact `1/3`.
- The warning-capture probe did **not** reproduce under the runner's Matplotlib 3.11.1, and the negative-zero case was already GREEN because renderer zero-tolerance normalization already existed. Neither was falsely reported as RED.

### Refined authoritative RED

- Refined RED commit: **`77f85faa427159f36ea535d30a6857b81077ba38`**.
- Run **`33356828336`**, job **`99380499387`**: **2 failed / 2 passed / 22 deselected in 3.28 s**.
- Deterministic L-2 compatibility contract failed because `axis.title.get_fontweight()` returned **`'semibold'`** rather than numeric **`600`**.
- Exact-rational annotation remained RED because text was **`(0.33, 2)`** instead of containing `1/3`.
- Warning-capture and negative-zero regressions remained GREEN.

### Product GREEN

- GREEN trigger: **`e58d57585e2e37343ecbd5cabeadb96019c98b74`**.
- Authoritative run **`33356956199`**, job **`99380850593`**: SUCCESS.
- Task 9 contracts: **4/4 PASS in 3.08 s**.
- Focused plotting/integration/rendering/request regression: **37/37 PASS in 19.08 s**.
- Full suite: **877/877 PASS in 184.92 s**.
- Product commit: **`5363bfc54a5f4d27a2f1b79f309e6a383eb17a2e`** — `fix: polish exact characteristic presentation`.
- Product change is narrow:
  - Matplotlib title weights in presentation/plotting use numeric `600`.
  - `_CharacteristicRequest` carries optional `x_symbolic` only for exact ordinary-plot characteristic metadata.
  - `_compact_exact_x_label()` displays non-integer exact `sp.Rational` x values as `p/q` while preserving existing numeric formatting otherwise.
  - negative-zero behavior required no product change; its already-GREEN audit case is persisted as regression coverage.

### Idempotent re-verification / cleanup

- Idempotent trigger: **`23316ae1beb899d5b2d7772f5156dd8381c19ada`**.
- Run **`33357240791`**, job **`99381630477`**: SUCCESS.
- Product-tree materialization check: PASS.
- Contracts: **4/4 PASS in 3.04 s**.
- Focused regression: **37/37 PASS in 19.00 s**.
- Full suite: **877/877 PASS in 187.18 s**.
- Final output: **`No Task 9 product or test patch to commit.`**
- Temporary files removed:
  - `.github/workflows/v092-task9-red.yml`
  - `.github/scripts/v092_task9_green.py`
- Cleanup commits: **`b3ecc94fb1455c05a854468b8f0d9a4c240ff12f`**, then **`c9a6dfc0ea6aec939bdcdb9838f02cbb5538ff4b`**.
- Comparison `5363bfc...c9a6dfc` contains only removal of those two `.github` files; no `src/` or test change occurred after the validated product commit.
- `.github` is absent on the active branch after cleanup.
- `main` remains **`698696bb8854fa197851cdbb2f5e4c08ef22178b`** and package metadata remains **0.9.1**.

## Exact next step — Task 10

Task 10 is **investigation-only** unless a deterministic new defect is first reproduced. Product files remain unchanged by default.

1. Create `tests/test_v092_risk_probes.py`.
2. Add the approved near-zero-vs-exact-root residual probe using `x - sp.Float("1.000000000000000001")` over `[0,2]`. Do **not** loosen residual validation; if an exact-root false rejection appears, preserve it as RED and stop for a separate corrective task.
3. Add the approved tri-state-realness/incomplete-evaluation probe: monkeypatch `solveset` to a `ConditionSet`, `solve` to return an `is_real is None` hint, and require fallback to produce a real root rather than a complex result or confident empty set.
4. Add the approved generous simplify-cost probe using `expand((x-1) * sum((x+i)**2 for i in range(1,35)))`; require the root near `1` and elapsed time `<15 s`.
5. Run:
   `python -m pytest tests/test_v092_risk_probes.py tests/test_characteristics_roots.py tests/test_characteristics_fallback.py -q`
6. If all probes pass, record **“not reproduced; no product change”** for those audit risks and commit evidence only: `tests/test_v092_risk_probes.py` + `CURRENT.md`, message `test: investigate characteristic audit risks`.
7. If a deterministic defect appears, stop; commit the RED reproduction and insert a numbered corrective task before Task 11. Do not make a speculative fix.
8. Never invoke Codex unless separately authorized.

## Still deferred / open after Task 9

- Task 10: residual, tri-state-realness and simplify-cost investigation probes.
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
- **0.9.2 Audit Remediation & Reliability:** **Tasks 1–9 COMPLETE; Task 10 NEXT**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`; package/runtime version remains 0.9.1. Tasks 1–9 are complete. Task 9 product is `5363bfc54a5f4d27a2f1b79f309e6a383eb17a2e`. Its authoritative GREEN run `33356956199` / job `99380850593` finished 4/4 contracts + 37/37 focused + 877/877 full PASS. Its idempotent run `33357240791` / job `99381630477` repeated 4/4 + 37/37 + 877/877 and produced `No Task 9 product or test patch to commit.` Temporary Task 9 workflow/patcher were removed; cleanup head before this context update is `c9a6dfc0ea6aec939bdcdb9838f02cbb5538ff4b`, and `.github` is absent. Task 10 is next and is investigation-only: create the three approved residual/tri-state/simplify-cost probes; if they pass, record “not reproduced; no product change”; if a deterministic defect appears, stop with RED and insert a corrective task before Task 11. Never invoke Codex without explicit authorization.
