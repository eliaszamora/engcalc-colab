# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.1 remains the canonical released baseline. The approved 0.9.2 Audit Remediation & Reliability plan is active on `feature/v0.9.2-audit-reliability`. Tasks 1–5 are complete and Task 6 is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**, re-verified unchanged after Task 5.
- Runtime/package version remains **0.9.1**; the 0.9.2 version bump is deferred to Task 14.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- Task 5 product commit: **`2b6be7d22817cee3c1267495e58635d3bb06fc9d`** — `fix: make engineering symbols explicitly real`.
- Task 5 idempotent verification trigger: **`c8f2b15d3cb806be7c07d5ab49e0e49ba11cdf58`**.
- Task 5 temporary validation infrastructure fully removed; final cleanup head before this context update: **`6a75cde5719cd740b7301efb25783c38206906ed`**.
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
- Renderer-only symbol construction remains display-only and is not rewritten solely for assumptions.
- Direct supported unit literals become consistent across roots/intersections/extrema/plot/table in Task 6.
- Piecewise boundary/topology normalization remains Task 7.
- Ordinary plots retain 201 drawing samples and exact metadata; positive structural moment remains plotted downward.
- `envelope(...)` remains sampled in 0.9.2; exact envelopes are deferred to 0.9.3.
- No SciPy dependency.
- Permanent Python 3.10–3.14 CI and declared IPython dependency remain Task 11.
- Release PR must stop before merge pending explicit user approval.

## Fixed through Task 5

### Tasks 2–4

- Natural `log(x)-1`, `exp(x)-3*x`, and quintic roots no longer return silent empty sets.
- `intersections(log(x), 1+0*x, x, 1, 10)` uses the same zero-set semantics as roots.
- Closed real finite SymPy numbers such as `E`, real `LambertW`, and real `CRootOf` can be physically evaluated while preserving exact symbolic objects.
- `oo`, `-oo`, `zoo`, `nan`, and non-real closed symbolic values are rejected.
- Incomplete `solveset` + partial `solve` output no longer suppresses deterministic fallback.
- Intersections preserve exact dimensional symbolic locations such as `P/(2*q)` while still supplementing incomplete exact discovery numerically.

### Task 5 — real symbols, identity-safe reconstruction, and `abs` extrema

- Canonical engine symbols are now explicitly real.
- Identity-sensitive symbol reconstruction in numeric helpers, Piecewise breakpoint extraction, and characteristic string adapters now reuses matching expression symbols before creating a `real=True` fallback.
- Renderer-only constructions were intentionally left unchanged.
- Dimensionless `extrema(abs(x-2), x, 0, 4)` now includes the cusp/global minimum.
- Dimensional scaled-`Abs` extrema now preserve units and the cusp minimum, including `L := 4*m`, `q := 2*kN/m`, `M(x)=q*(x-L/2)`, with global minimum at `x=2 m`, `0 kN`.
- The Task 2 closed-number path no longer intercepts `asin`, `acos`, or `atan`; inverse-trig physical angle evaluation therefore preserves `radian` semantics.
- Existing identity-sensitive tests were migrated to compare against `engine.resolve_symbol(...)`, rather than weakening exact SymPy equality.

## Task 5 validation evidence

### Pre-change audit

- Symbol audit run **`33351254275`**, job **`99364950249`**: SUCCESS.
- Identity-sensitive sites were classified before product modification: engine symbol creation, two numeric helpers, Piecewise breakpoint extraction, and four characteristic string adapters.
- Renderer constructions were classified as display-only.

### Authoritative RED

- RED run **`33351512415`**, job **`99365687086`**, CPython 3.13.15.
- Focused RED gate: **3 failed / 4 deselected**.
- The three intentional failures were exactly:
  1. existing dimensionless `abs` extrema cusp handling;
  2. `EngineeringEngine.resolve_symbol("x").is_real is True`;
  3. dimensional scaled-`Abs` extrema with units.

### Migration diagnostic before final GREEN

- Run **`33351895742`**, job **`99366762764`**.
- Task 5 contracts: **7/7 PASS**.
- Broad regression: **69/69 PASS**.
- Full suite: **820 PASS / 42 FAIL**.
- Failure classification: **40** stale tests constructing `sp.Symbol(...)` without `real=True`, plus **2** genuine inverse-trig `radian` regressions (`atan(1)` and equivalent user function).
- The inverse-trig cause was the generic closed-SymPy-number path preceding specialized scalar-function evaluation.

### Validated product GREEN

- Final product gate run **`33352336155`**, job **`99367974536`**: SUCCESS.
- Task 5 contracts: **7/7 PASS**.
- Focused identity/angle migration regression: **122/122 PASS**.
- Broad Task 5 regression: **69/69 PASS**.
- Full source suite: **862/862 PASS**.
- Product commit produced by that gate: **`2b6be7d22817cee3c1267495e58635d3bb06fc9d`**.
- Product commit touches source/tests only; no renderer behavior was changed for Task 5.

### Idempotent re-verification

- Explicit rerun commit: **`c8f2b15d3cb806be7c07d5ab49e0e49ba11cdf58`**; the only difference from the product commit was a one-line workflow comment used to trigger the gate.
- Idempotent run **`33352587955`**, job **`99368675579`**: SUCCESS.
- Task 5 contracts: **7/7 PASS in 2.62 s**.
- Focused migration regression: **122/122 PASS in 22.47 s**.
- Broad Task 5 regression: **69/69 PASS in 16.67 s**.
- Full source suite: **862/862 PASS in 175.82 s**.
- Final workflow output: **`No Task 5 product or test patch to commit.`**
- Therefore the Task 5 product patch is idempotent on its validated product tree.
- Temporary Task 5 workflow and both temporary patcher scripts were removed after this evidence was captured. The `.github` directory is absent on the branch after cleanup, so no Task 5 harness remains.

## Still open

- **M-1:** direct unit-literal bound inconsistency — **Task 6, next**.
- **M-2/M-3:** Piecewise boundary value/topology/zero-unit normalization — Task 7.
- **L-1…L-4:** renderer misuse diagnostics and plot presentation polish — Tasks 8–9.
- Investigation-only audit risks remain Task 10.
- **I-1…I-3:** permanent CI/Python matrix/IPython metadata — Task 11.
- Separate deferred issues remain `no_vertical_scroll()`, multiline ordinary non-matrix call parsing, and generalized structural eigenproblems.

## Canonical 0.9.1 evidence

- `main@698696bb8854fa197851cdbb2f5e4c08ef22178b` remains unchanged.
- 0.9.1 final pre-PR: **23/23 release contract; 846/846 full source**.
- Real wheel SHA-256: `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`.
- Post-merge source validation: **846/846 PASS**.

## Roadmap / active plan

- **0.9.0 Matrix/CAS:** COMPLETE + MERGED.
- **0.9.1 Exact Characteristics:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.2 Audit Remediation & Reliability:** **Tasks 1–5 COMPLETE; Task 6 NEXT**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.

0.9.2 task status:

1. COMPLETE — independent C-1/H-1 natural RED;
2. COMPLETE — closed real finite SymPy evaluation;
3. COMPLETE — complete/non-silent roots + exact/numeric merge;
4. COMPLETE — intersections share zero-set semantics;
5. **COMPLETE — explicit real engineering symbols, identity-safe reconstruction, scaled-`Abs` extrema, inverse-trig unit preservation, full/idempotent GREEN**;
6. **NEXT — centralized direct unit-literal bounds**;
7. Piecewise branch/continuity/zero-unit normalization;
8. renderer misuse + actionable Piecewise diagnostics;
9. plot warning/negative-zero/exact-label polish;
10. investigation-only risk probes;
11. permanent Python 3.10–3.14 CI + IPython metadata;
12. behavior-preserving characteristics package decomposition;
13. acceptance/docs/full regression;
14. 0.9.2 version/release validation/PR, STOP before merge.

## Exact next step — Task 6

Follow the approved Task 6 order; do not skip the RED:

1. Add a public engine-level RED matrix covering direct unit-literal bounds across all five domain-bearing APIs:
   - `roots(V(x), x, 0*m, 6*m)`;
   - `extrema(M(x), x, 0*m, 6000*mm)`;
   - `intersections(M(x), M2(x), x, 0*m, 6*m)`;
   - `plot(M(x), x, 0*m, 6*m)`;
   - `table(M(x), x, 0*m, 6*m, 5)`.
2. Add an incompatible-domain contract such as `roots(V(x), x, 0*m, 2*s)` and require an incompatible-domain error.
3. Observe the RED before touching product code.
4. Add `NumericContext.unit_literal_overrides(expression, overrides=None)` with precedence **explicit override > stored numeric value > unit alias**.
5. Replace characteristic-only literal-unit handling with the shared helper.
6. Wire the same helper into plot/table lower and upper bound evaluation.
7. Run the focused Task 6 gate from the approved plan, then `python -m pytest -q`.
8. Do not begin Task 7 until Task 6 is fully GREEN and its temporary validation infrastructure has been removed.
9. Never invoke Codex unless separately authorized.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`, version remains 0.9.1. Tasks 1–5 are complete. Task 5 product is `2b6be7d22817cee3c1267495e58635d3bb06fc9d`; its explicit idempotent run `33352587955` / job `99368675579` finished 7/7 + 122/122 + 69/69 + 862/862 GREEN and produced no second product/test patch. All three temporary Task 5 harness files were removed; cleanup head before this context update is `6a75cde5719cd740b7301efb25783c38206906ed`. Task 6 is the next authorized plan step: RED first for direct unit literals across roots/intersections/extrema/plot/table, then centralized `NumericContext.unit_literal_overrides(...)`, focused/full GREEN, cleanup, and context update. Exact envelopes remain deferred to 0.9.3; named cases/combinations to 0.9.4. Never invoke Codex without explicit authorization.
