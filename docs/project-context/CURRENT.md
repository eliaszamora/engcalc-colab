# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.1 remains the canonical released baseline. The approved 0.9.2 Audit Remediation & Reliability plan is active on `feature/v0.9.2-audit-reliability`. Tasks 1–8 are complete and Task 9 is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**, re-verified unchanged after Task 8.
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
9. **NEXT** — plot warning, negative-zero, and exact rational coordinate-label polish.
10. investigation-only risk probes.
11. permanent Python 3.10–3.14 CI + declared IPython dependency.
12. behavior-preserving characteristics package decomposition.
13. acceptance/docs/full regression.
14. 0.9.2 version/release validation/PR; STOP before merge.

## Product commits through Task 8

- Task 5: **`2b6be7d22817cee3c1267495e58635d3bb06fc9d`** — `fix: make engineering symbols explicitly real`.
- Task 6: **`c115bc9d810e8552a8d5138c88bfffcb3f55cb76`** — `fix: centralize direct unit literal bounds`.
- Task 7: **`d2ae961bf3be34c2b52b1afbc54b4963f7ceb156`** — `fix: normalize Piecewise extrema topology`.
- Task 8: **`833009fedcf257c18e84e8ea0992e4f613a5d52d`** — `fix: make characteristic diagnostics explicit`.

Tasks 1–4 are already complete in the branch history and remain covered by the persistent audit/root/intersection regression suites.

## Reliability contract now established

- External audit findings receive EngCalc-owned RED reproduction before correction.
- Exact-first remains authoritative; deterministic fallback supplements incomplete exact discovery.
- Exact provenance wins when exact and numeric candidates represent the same physical location.
- Plausible exact-candidate evaluation failure never silently becomes “no solution.”
- `roots()` and `intersections()` share one continuous zero-set discovery/validation/fallback/merge policy.
- Engine-created engineering symbols are `sp.Symbol(name, real=True)`.
- Identity-sensitive reconstruction reuses the exact matching free symbol when present; only otherwise creates a `real=True` fallback.
- Supported unit literals work consistently across roots/intersections/extrema/plot/table.
- Original AST numeric-bound evaluation preserves dimensional zero bounds such as `0*m` before SymPy simplification.
- Piecewise physical boundaries preserve the selected governing branch symbolically.
- Exact dimensionless zero at Piecewise topology adopts an established physical response unit when available.
- Continuous Piecewise breakpoints collapse redundant `left/at/right` records only when all physical values are equivalent; discontinuities remain explicit.
- `render_result()` explicitly rejects characteristic results and directs callers to `render_characteristic_result()` instead of leaking `AttributeError`.
- Missing numeric values encountered in Piecewise characteristic branch substitution reuse the stable unresolved-symbol diagnostic hint.
- Ordinary plots retain 201 drawing samples and exact metadata; positive structural moment remains plotted downward.
- `envelope(...)` remains sampled in 0.9.2; exact envelopes are deferred to 0.9.3.
- No SciPy dependency.
- Permanent Python 3.10–3.14 CI and declared IPython dependency remain Task 11.

## Validation evidence — Task 5

- Authoritative product/idempotent gates: **7/7 + 122/122 + 69/69 + 862/862 PASS**.
- Product commit: `2b6be7d22817cee3c1267495e58635d3bb06fc9d`.
- Temporary validation infrastructure was removed before Task 6.

## Validation evidence — Task 6

- Authoritative RED: run **`33352962308`**, job **`99369683201`**.
- Authoritative GREEN: run **`33353557535`**, job **`99371326028`**.
- GREEN: **3/3 public contracts + 83/83 focused + 62/62 table + 866/866 full PASS**.
- Product commit: `c115bc9d810e8552a8d5138c88bfffcb3f55cb76`.
- Idempotent rerun repeated the same counts and produced **`No Task 6 product or test patch to commit.`**
- Temporary Task 6 infrastructure was removed before Task 7.

## Validation evidence — Task 7

### RED

- RED workflow commit: **`980812b23ed25e136a0e61f7f6db798d70c87ddf`**.
- RED run **`33354710410`**, job **`99374541546`**.
- New Task 7 contracts: **2/2 FAILED**, as intended.
- Existing discontinuous representative contracts: **2/2 PASS**.
- Failure M-2: physical boundary value was numerically correct but `value_symbolic` kept an unresolved Piecewise wrapper instead of the selected branch.
- Failure M-3: continuous breakpoint emitted `left/at/right` instead of one `at` record.

### GREEN

- Authoritative run **`33354934109`**, job **`99375150144`**: SUCCESS.
- New contracts: **2/2 PASS**.
- Discontinuous topology preservation: **2/2 PASS**.
- Focused Piecewise/extrema regression: **16/16 PASS**.
- Full suite: **868/868 PASS**.
- Product commit: **`d2ae961bf3be34c2b52b1afbc54b4963f7ceb156`**.

### Idempotence / cleanup

- Verification trigger: **`8782fbdc0989840fd5d74465cbd5619afccb4cec`**.
- Idempotent run **`33355156480`**, job **`99375768821`**: SUCCESS.
- Repeated **2/2 + 2/2 + 16/16 + 868/868 PASS**.
- Final output: **`No Task 7 product or test patch to commit.`**
- Temporary Task 7 workflow/scripts were removed; `.github` was absent before Task 8.

## Validation evidence — Task 8

### RED discovery

- Initial RED workflow commit: **`6ab5a51b401fcec6af022ebaeea56efd84a5c471`**.
- Initial run **`33355520272`**, job **`99376793403`**: **3 failed / 1 passed / 16 deselected**.
- All three L-1 variants reproduced the real defect: direct `render_result()` on `RootsResult`, `IntersectionsResult`, or `ExtremaResult` leaked `AttributeError` because those result types have no `.value`.
- The originally proposed unresolved Piecewise condition-symbol example `a` was already actionable on the current tree through an earlier diagnostic path, so it correctly passed rather than being misreported as RED.

### Refined authoritative RED

- Refined RED commit: **`7b8eacbcf81226d3fd7fd7574ce4d544e31c70ec`**.
- Run **`33355576544`**, job **`99376959357`**: **4 failed / 1 passed / 16 deselected**.
- L-1 remained RED in all three renderer variants.
- Direct `_piecewise_substitutions()` path was isolated with an unresolved branch symbol `q`; its error contained `q` but omitted the actionable `q := <value>*<unit>` hint, giving a legitimate L-3 RED.
- The existing `a` condition-symbol case remained GREEN and was retained as a regression contract.

### Product GREEN

- Authoritative GREEN trigger: **`ed5f4eecd884a0ec966b8cd875bb8d74c81731e4`**.
- Run **`33355653077`**, job **`99377170864`**: SUCCESS.
- Task 8 contracts: **5/5 PASS in 1.76 s**.
- Focused renderer/magic/Piecewise regression: **45/45 PASS in 10.11 s**.
- Full source suite: **873/873 PASS in 182.65 s**.
- Product commit: **`833009fedcf257c18e84e8ea0992e4f613a5d52d`** — `fix: make characteristic diagnostics explicit`.
- Persistent product change is narrow:
  - `render_result()` has a characteristic-result guard that raises targeted `TypeError` and directs callers to `render_characteristic_result()`.
  - `_piecewise_substitutions()` reuses `diagnostic_hint("unresolved_numeric_symbols", names=(name,))`.
  - Both approved/isolated regressions are persisted in tests.

### Idempotent re-verification and cleanup

- Idempotent trigger: **`198a3067f9337806d95f6c0396ef7a5167a9956e`**.
- Idempotent run **`33355901981`**, job **`99377887051`**: SUCCESS.
- Product-tree materialization check: PASS.
- Task 8 contracts: **5/5 PASS in 1.39 s**.
- Focused regression: **45/45 PASS in 8.31 s**.
- Full suite: **873/873 PASS in 151.47 s**.
- Final output: **`No Task 8 product or test patch to commit.`**
- Temporary files removed:
  - `.github/workflows/v092-task8-red.yml`
  - `.github/scripts/v092_task8_green.py`
- Cleanup commits: **`bf40a06aeb1944c11a2498970bb54f911e51d52b`**, then **`0bd92fc559a6d396cfbaf8a7b6637b0cb7801157`**.
- Comparison `833009f...0bd92fc` contains only removal of those two `.github` files; no `src/` or test change occurred after the validated product commit.
- `.github` is absent on the active branch after cleanup.
- `main` remains `698696bb8854fa197851cdbb2f5e4c08ef22178b` and package metadata remains **0.9.1**.

## Still open

- **L-2/L-4:** plot warning, negative-zero, exact rational annotation presentation — **Task 9, next**.
- Investigation-only audit risks remain Task 10.
- **I-1…I-3:** permanent CI/Python matrix/IPython metadata — Task 11.
- Separate deferred issues remain `no_vertical_scroll()`, multiline ordinary non-matrix call parsing, and generalized structural eigenproblems.

## Exact next step — Task 9

Follow the approved Task 9 order; RED first and do not change product until the failure signatures are observed.

1. In `tests/test_plotting.py`, add L-2 RED for a titled plot rendered through `render_presented_plot()`. Assert stderr does not contain either `font weight semibold` or `Failed to find font weight semibold`.
2. Add exact-rational annotation RED: `f(x)=-(x-1/3)^2+2`, then `plot(f(x), x, 0, 1)`. The characteristic annotation at `x=1/3` must contain literal `1/3` and be positioned at the same exact numeric coordinate.
3. In `tests/test_characteristics_rendering.py`, add negative-zero regression using `roots((x-1)*(x-1.0000001), x, 0, 2)` with `RenderSettings(zero_tolerance=1e-10)` and assert characteristic HTML contains no `-0.00`, `-0.0`, or `-0\,` token.
4. Observe the Task 9 RED behavior before touching product code. If any proposed contract is already GREEN, record that fact and isolate the actual failing path rather than manufacturing a false RED.
5. In `src/engcalc_colab/presentation.py`, replace unsupported title weight with `axis.set_title(result.title, pad=10, fontweight=600)`.
6. In `src/engcalc_colab/plotting.py`, extend `_CharacteristicRequest` with `x_symbolic: Any | None = None`. Exact ordinary-plot characteristic metadata carries `point.x_symbolic`; sampled envelope/legacy requests keep `None`.
7. Add `_compact_exact_x_label(symbolic, numeric)` so only non-integer `sp.Rational` values render as `p/q`; all integer/ordinary-decimal x labels retain existing compact numeric formatting. Pass `request.x_symbolic` into coordinate-label creation.
8. Normalize characteristic rendered near-zero output so configured zero tolerance never emits negative zero.
9. Focused gate:
   `python -m pytest tests/test_plotting.py tests/test_characteristics_plot_integration.py tests/test_characteristics_rendering.py tests/test_characteristic_requests.py -q`
10. Then run `python -m pytest -q`.
11. Commit only if all gates are GREEN. Then perform an idempotent re-verification, remove all temporary Task 9 validation infrastructure, verify `.github` clean/absent, update this file, and only then proceed to Task 10.
12. Never invoke Codex unless separately authorized.

## Canonical 0.9.1 evidence

- `main@698696bb8854fa197851cdbb2f5e4c08ef22178b` remains unchanged.
- Runtime/package metadata on the active branch remains **0.9.1**.
- 0.9.1 final pre-PR: **23/23 release contract; 846/846 full source**.
- Real wheel SHA-256: `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`.
- Post-merge source validation: **846/846 PASS**.

## Roadmap

- **0.9.0 Matrix/CAS:** COMPLETE + MERGED.
- **0.9.1 Exact Characteristics:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.2 Audit Remediation & Reliability:** **Tasks 1–8 COMPLETE; Task 9 NEXT**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`; package/runtime version remains 0.9.1. Tasks 1–8 are complete. Task 8 product is `833009fedcf257c18e84e8ea0992e4f613a5d52d`. Its authoritative GREEN run `33355653077` / job `99377170864` finished 5/5 contracts + 45/45 focused + 873/873 full PASS. Its idempotent run `33355901981` / job `99377887051` repeated 5/5 + 45/45 + 873/873 and produced `No Task 8 product or test patch to commit.` Temporary Task 8 workflow/patcher were removed; cleanup head before this context update is `0bd92fc559a6d396cfbaf8a7b6637b0cb7801157`, and `.github` is absent. Task 9 is next: RED first for matplotlib title-weight warning, exact rational x annotations, and negative-zero presentation; then narrow presentation/plotting fixes, focused/full GREEN, idempotence, cleanup, and context update. Exact envelopes remain deferred to 0.9.3; named cases/combinations to 0.9.4. Never invoke Codex without explicit authorization.
