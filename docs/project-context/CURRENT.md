# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.1 remains the canonical released baseline. The approved 0.9.2 Audit Remediation & Reliability plan is active on `feature/v0.9.2-audit-reliability`. Tasks 1–7 are complete and Task 8 is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**, re-verified unchanged after Task 7.
- Runtime/package version remains **0.9.1**; the 0.9.2 version bump is deferred to Task 14.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- Task 5 product commit: **`2b6be7d22817cee3c1267495e58635d3bb06fc9d`** — `fix: make engineering symbols explicitly real`.
- Task 6 product commit: **`c115bc9d810e8552a8d5138c88bfffcb3f55cb76`** — `fix: centralize direct unit literal bounds`.
- Task 7 product commit: **`d2ae961bf3be34c2b52b1afbc54b4963f7ceb156`** — `fix: normalize Piecewise extrema topology`.
- Task 7 idempotent verification trigger: **`8782fbdc0989840fd5d74465cbd5619afccb4cec`**.
- Task 7 temporary validation infrastructure fully removed; cleanup head before this context update: **`6e75380948e2ea40cea115be13e772e8e153262b`**.
- Approved spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-design.md`.
- Approved/refined plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-implementation.md`.
- Persistent natural audit regressions: `tests/test_v092_audit_regressions.py`.
- Never invoke Codex / Codex Cloud without explicit user authorization.

## Approved 0.9.2 behavior

Public characteristic syntax remains unchanged:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

Reliability contract:

- External audit findings receive EngCalc-owned RED reproduction before correction.
- Exact-first remains authoritative; deterministic fallback supplements incomplete exact discovery.
- Exact provenance wins when exact and numeric candidates represent the same physical location.
- Plausible exact-candidate evaluation failure must never silently become “no solution.”
- `roots()` and `intersections()` share one continuous zero-set discovery/validation/fallback/merge policy.
- Engine-created engineering symbols are `sp.Symbol(name, real=True)`.
- Identity-sensitive reconstruction reuses the exact matching free symbol when present; only otherwise creates a `real=True` fallback.
- Direct supported unit literals are consistent across roots/intersections/extrema/plot/table.
- Piecewise physical boundaries now preserve selected governing-branch symbolic values.
- Exact dimensionless zero at Piecewise side topology is normalized to an established physical response unit when available.
- Continuous Piecewise breakpoints collapse redundant `left/at/right` records to one `at`; discontinuous topology remains explicit.
- Renderer misuse and missing Piecewise-value diagnostics remain Task 8.
- Ordinary plots retain 201 drawing samples and exact metadata; positive structural moment remains plotted downward.
- `envelope(...)` remains sampled in 0.9.2; exact envelopes are deferred to 0.9.3.
- No SciPy dependency.
- Permanent Python 3.10–3.14 CI and declared IPython dependency remain Task 11.
- Release PR must stop before merge pending explicit user approval.

## Fixed through Task 7

### Tasks 2–4

- Natural `log(x)-1`, `exp(x)-3*x`, and quintic roots no longer return silent empty sets.
- `intersections(log(x), 1+0*x, x, 1, 10)` uses the same zero-set semantics as roots.
- Closed real finite SymPy numbers such as `E`, real `LambertW`, and real `CRootOf` can be physically evaluated while preserving exact symbolic objects.
- `oo`, `-oo`, `zoo`, `nan`, and non-real closed symbolic values are rejected.
- Incomplete exact discovery no longer suppresses deterministic fallback.
- Intersections preserve exact dimensional symbolic locations while supplementing incomplete discovery numerically.

### Task 5 — real symbols, identity-safe reconstruction, and `abs` extrema

- Canonical engine symbols are explicitly real.
- Identity-sensitive numeric/Piecewise/characteristic reconstruction reuses matching expression symbols before creating a `real=True` fallback.
- Dimensionless and dimensional scaled-`Abs` extrema preserve cusp/global minima.
- The closed-number path excludes `asin`, `acos`, and `atan`, preserving inverse-trig `radian` semantics.
- Final Task 5 product and idempotent gates both finished **7/7 + 122/122 + 69/69 + 862/862 PASS** with no second product patch.

### Task 6 — centralized direct unit-literal bounds

- Added `NumericContext.unit_literal_overrides(expression, overrides=None)` with precedence **explicit override > stored numeric value > unit alias**.
- Characteristic bounds/candidates, plot bounds, and table symbolic fallback share the same unit-literal policy.
- Physical quantities can be resolved from the original AST before SymPy simplification, preserving the unit of zero-valued bounds such as `0*m`.
- Direct literals work consistently across roots/extrema/intersections/plot/table, including mixed `m/mm` domains.
- Incompatible domains such as `0*m ... 2*s` reach dimensional validation and raise an incompatible-domain error.
- Existing operation-specific characteristic diagnostics remain preserved.
- Authoritative Task 6 GREEN: **3/3 + 83/83 + 62/62 + 866/866 PASS**.
- Idempotent Task 6 rerun repeated the same counts and produced no second product/test patch.

### Task 7 — Piecewise branch values, dimensional zero, and topology

- Physical Piecewise domain endpoints select the actual governing branch with `_select_piecewise_branch()` before symbolic x substitution.
- `value_symbolic` at a physical boundary keeps parameters symbolic while representing the selected branch, e.g. `-a` rather than an unresolved Piecewise wrapper at the lower boundary and `2*(L-a)` at the upper boundary.
- Exact dimensionless zero side values adopt the physical response unit established by another side/at value before topology comparison and result construction.
- Breakpoint records are collapsed only when all three physical values are equivalent: `left == at == right -> at`.
- Meaningful discontinuities continue to preserve `left/at/right`; pairwise equality alone does not collapse a discontinuity.
- Continuous-extrema endpoint behavior was explicitly restored after a temporary patcher anchor initially targeted the wrong equivalent endpoint loop.

## Task 7 validation evidence

### Authoritative RED

- RED workflow commit: **`980812b23ed25e136a0e61f7f6db798d70c87ddf`**.
- RED run **`33354710410`**, job **`99374541546`**.
- New Task 7 contracts: **2/2 FAILED**, as intended.
- Existing discontinuous representative contracts: **2/2 PASS**.
- M-2 failure: lower physical boundary numeric value was correct (`-3 m`) but `value_symbolic` remained `Piecewise((-a, a > 0), (-2*a, True))` instead of selected-branch `-a`.
- M-3 failure: continuous `x=a` emitted `['left', 'at', 'right']` instead of one `['at']` record.

### GREEN development correction

- Initial GREEN run **`33354874445`**, job **`99374986290`**, stopped before regression/commit.
- Continuous-breakpoint topology contract passed, but the branch-symbolic boundary contract still failed.
- Cause was harness implementation scope, not the intended algorithm: a generic textual anchor replaced the first equivalent endpoint loop in `_solve_continuous_extrema_exact()` instead of the Piecewise endpoint loop.
- A scoped corrective restored `_solve_continuous_extrema_exact()` exactly and applied selected-branch endpoint handling only inside `_solve_piecewise_extrema_exact()`.

### Validated product GREEN

- Authoritative run **`33354934109`**, job **`99375150144`**: SUCCESS.
- Task 7 new contracts: **2/2 PASS in 1.08 s**.
- Discontinuous topology-preservation contracts: **2/2 PASS in 1.02 s**.
- Focused Piecewise/extrema regression: **16/16 PASS in 4.15 s**.
- Full source suite: **868/868 PASS in 178.62 s**.
- Product commit: **`d2ae961bf3be34c2b52b1afbc54b4963f7ceb156`**.
- Product commit touches exactly two persistent files: `src/engcalc_colab/characteristics.py` and `tests/test_characteristics_piecewise_extrema.py`.

### Idempotent re-verification

- Verification trigger: **`8782fbdc0989840fd5d74465cbd5619afccb4cec`**.
- Idempotent run **`33355156480`**, job **`99375768821`**: SUCCESS.
- Product-tree materialization/scoping check: PASS; Piecewise endpoint handling is present only in the Piecewise solver and absent from the continuous solver.
- Task 7 new contracts: **2/2 PASS in 1.03 s**.
- Discontinuous topology-preservation contracts: **2/2 PASS in 0.92 s**.
- Focused Piecewise/extrema regression: **16/16 PASS in 3.64 s**.
- Full source suite: **868/868 PASS in 160.09 s**.
- Final output: **`No Task 7 product or test patch to commit.`**
- Temporary Task 7 workflow and both temporary patcher scripts were then removed.
- Comparison `d2ae961...6e753809` contains only removal of those three `.github` files; no source/test modifications occurred after the validated product commit.
- `.github` is absent on the active branch after cleanup.

## Still open

- **L-1/L-3:** renderer misuse diagnostic and actionable Piecewise missing-symbol guidance — **Task 8, next**.
- **L-2/L-4:** plot warning, negative-zero, and exact-label presentation polish — Task 9.
- Investigation-only audit risks remain Task 10.
- **I-1…I-3:** permanent CI/Python matrix/IPython metadata — Task 11.
- Separate deferred issues remain `no_vertical_scroll()`, multiline ordinary non-matrix call parsing, and generalized structural eigenproblems.

## Canonical 0.9.1 evidence

- `main@698696bb8854fa197851cdbb2f5e4c08ef22178b` remains unchanged.
- Runtime/package metadata on the active branch remains **0.9.1**.
- 0.9.1 final pre-PR: **23/23 release contract; 846/846 full source**.
- Real wheel SHA-256: `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`.
- Post-merge source validation: **846/846 PASS**.

## Roadmap / active plan

- **0.9.0 Matrix/CAS:** COMPLETE + MERGED.
- **0.9.1 Exact Characteristics:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.2 Audit Remediation & Reliability:** **Tasks 1–7 COMPLETE; Task 8 NEXT**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.

0.9.2 task status:

1. COMPLETE — independent C-1/H-1 natural RED;
2. COMPLETE — closed real finite SymPy evaluation;
3. COMPLETE — complete/non-silent roots + exact/numeric merge;
4. COMPLETE — intersections share zero-set semantics;
5. COMPLETE — explicit real engineering symbols, identity-safe reconstruction, scaled-`Abs` extrema, inverse-trig unit preservation;
6. COMPLETE — centralized unit-literal bounds and zero-bound physical-unit preservation;
7. **COMPLETE — selected Piecewise boundary branches, dimensional zero normalization, continuous/discontinuous topology, full/idempotent GREEN**;
8. **NEXT — renderer misuse + actionable Piecewise diagnostics**;
9. plot warning/negative-zero/exact-label polish;
10. investigation-only risk probes;
11. permanent Python 3.10–3.14 CI + IPython metadata;
12. behavior-preserving characteristics package decomposition;
13. acceptance/docs/full regression;
14. 0.9.2 version/release validation/PR, STOP before merge.

## Exact next step — Task 8

Follow the approved Task 8 order; do not skip RED:

1. Add L-1 RED to `tests/test_renderer.py`: `render_result()` called directly with `RootsResult`, `IntersectionsResult`, or `ExtremaResult` must raise targeted `TypeError` containing `render_result does not support characteristic results; use render_characteristic_result`.
2. Add L-3 RED to `tests/test_characteristics_piecewise_extrema.py`: an unresolved Piecewise condition symbol such as `a` must produce a characteristic error containing both `a` and the actionable hint `a := <value>*<unit>`.
3. Observe both RED behaviors before touching product code.
4. Add an explicit characteristic-result guard at the start of `render_result()`; do not merge the renderer HTML and LaTeX return contracts.
5. In `_piecewise_substitutions()`, reuse `diagnostic_hint("unresolved_numeric_symbols", names=(name,))` and include that hint in the characteristic-specific error.
6. Focused gate:
   `python -m pytest tests/test_renderer.py tests/test_characteristics_rendering.py tests/test_characteristics_magic.py tests/test_magic.py tests/test_characteristics_piecewise_extrema.py -q`
7. Then run `python -m pytest -q`.
8. Commit only if all gates are GREEN; then run an idempotent re-verification, remove Task 8 temporary validation infrastructure, verify `.github` clean, and update this file before Task 9.
9. Never invoke Codex unless separately authorized.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`; runtime/package version remains 0.9.1. Tasks 1–7 are complete. Task 7 product is `d2ae961bf3be34c2b52b1afbc54b4963f7ceb156`. Its authoritative GREEN run `33354934109` / job `99375150144` finished 2/2 + 2/2 + 16/16 + 868/868 PASS. Its idempotent run `33355156480` / job `99375768821` repeated 2/2 + 2/2 + 16/16 + 868/868 PASS, verified the product scope, and produced no second product/test patch. All three temporary Task 7 harness files were removed; cleanup head before this context update is `6e75380948e2ea40cea115be13e772e8e153262b`, and `.github` is absent. Task 8 is next: RED first for renderer misuse and actionable unresolved Piecewise-symbol diagnostics, then narrow renderer/diagnostic fixes, focused/full GREEN, idempotence, cleanup, and context update. Exact envelopes remain deferred to 0.9.3; named cases/combinations to 0.9.4. Never invoke Codex without explicit authorization.
