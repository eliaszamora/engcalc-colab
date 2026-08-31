# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.1 remains the canonical released baseline. The approved 0.9.2 Audit Remediation & Reliability plan is active on `feature/v0.9.2-audit-reliability`. Tasks 1–6 are complete and Task 7 is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**, re-verified unchanged after Task 6.
- Runtime/package version remains **0.9.1**; the 0.9.2 version bump is deferred to Task 14.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- Task 5 product commit: **`2b6be7d22817cee3c1267495e58635d3bb06fc9d`** — `fix: make engineering symbols explicitly real`.
- Task 6 product commit: **`c115bc9d810e8552a8d5138c88bfffcb3f55cb76`** — `fix: centralize direct unit literal bounds`.
- Task 6 idempotent verification trigger: **`743967f538b5806e4ab01729ae0b4c9666c9abbb`**.
- Task 6 temporary validation infrastructure fully removed; cleanup head before this context update: **`06d2e66155f6b8ce55c6501dd4a50458455a3742`**.
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
- Direct supported unit literals are now consistent across roots/intersections/extrema/plot/table.
- Piecewise boundary/topology normalization remains Task 7.
- Ordinary plots retain 201 drawing samples and exact metadata; positive structural moment remains plotted downward.
- `envelope(...)` remains sampled in 0.9.2; exact envelopes are deferred to 0.9.3.
- No SciPy dependency.
- Permanent Python 3.10–3.14 CI and declared IPython dependency remain Task 11.
- Release PR must stop before merge pending explicit user approval.

## Fixed through Task 6

### Tasks 2–4

- Natural `log(x)-1`, `exp(x)-3*x`, and quintic roots no longer return silent empty sets.
- `intersections(log(x), 1+0*x, x, 1, 10)` uses the same zero-set semantics as roots.
- Closed real finite SymPy numbers such as `E`, real `LambertW`, and real `CRootOf` can be physically evaluated while preserving exact symbolic objects.
- `oo`, `-oo`, `zoo`, `nan`, and non-real closed symbolic values are rejected.
- Incomplete `solveset` + partial `solve` output no longer suppresses deterministic fallback.
- Intersections preserve exact dimensional symbolic locations such as `P/(2*q)` while still supplementing incomplete exact discovery numerically.

### Task 5 — real symbols, identity-safe reconstruction, and `abs` extrema

- Canonical engine symbols are explicitly real.
- Identity-sensitive numeric/Piecewise/characteristic reconstruction reuses matching expression symbols before creating a `real=True` fallback.
- Dimensionless and dimensional scaled-`Abs` extrema preserve cusp/global minima.
- The Task 2 closed-number path excludes `asin`, `acos`, and `atan`, preserving inverse-trig `radian` semantics.
- Existing identity-sensitive tests compare against `engine.resolve_symbol(...)` rather than weakening exact SymPy equality.
- Final Task 5 product gate: **7/7 + 122/122 + 69/69 + 862/862 PASS**.
- Idempotent Task 5 rerun: **7/7 + 122/122 + 69/69 + 862/862 PASS**, with no second product/test patch.

### Task 6 — centralized direct unit-literal bounds

- Added `NumericContext.unit_literal_overrides(expression, overrides=None)`.
- Precedence contract is **explicit override > stored numeric value > unit alias**.
- Characteristic-domain bounds, exact/boundary candidates, plot bounds, and table symbolic fallback share the same unit-literal policy.
- Domain quantities can be resolved directly from the original AST before SymPy simplification; this preserves the physical unit of zero-valued bounds such as `0*m` instead of allowing `0*m -> 0` to erase dimensionality.
- Direct literals now work consistently for:
  - `roots(V(x), x, 0*m, 6*m)`;
  - `extrema(M(x), x, 0*m, 6000*mm)`;
  - `intersections(M(x), M2(x), x, 0*m, 6*m)`;
  - `plot(M(x), x, 0*m, 6*m)` and mixed `0*m ... 6000*mm`;
  - `table(M(x), x, 0*m, 6*m, 5)`.
- Incompatible domains such as `roots(V(x), x, 0*m, 2*s)` now reach dimensional validation and raise an incompatible-domain error rather than failing earlier on an unresolved unit symbol.
- Existing operation-specific characteristic diagnostics such as `roots domain bound must be numerically resolvable` remain preserved.
- Table’s already-correct ordinary numeric AST route was retained; the shared resolver is used without redesigning table semantics.

## Task 6 validation evidence

### Authoritative RED

- RED run **`33352962308`**, job **`99369683201`**.
- Public RED contracts: **2/2 failed**, as intended.
- Probe classification before product changes:
  - `roots`: unresolved direct unit literal;
  - `extrema`: unresolved direct unit literal;
  - `intersections`: unresolved direct unit literal;
  - `plot`: unresolved direct unit literal;
  - `table`: already accepted `0*m ... 6*m`;
  - incompatible `0*m ... 2*s`: failed too early on unresolved `s`, before dimensional compatibility validation.

### Corrective diagnostics during GREEN development

- First GREEN contract run exposed two real edge conditions:
  1. SymPy could simplify `0*m` to dimensionless zero before characteristic normalization;
  2. exact/boundary candidates containing unit literals needed the shared alias policy as well.
- A later focused regression found one diagnostic-only regression: unresolved characteristic bounds still failed correctly, but the generic numeric message escaped instead of the existing operation-specific `roots domain bound must be numerically resolvable` contract. That diagnostic mapping was restored.
- One subsequent gate failure was harness-only: it referenced nonexistent `tests/test_engineering_tables.py`. No product change was made; the gate was corrected to the actual table suites.

### Validated product GREEN

- Authoritative run **`33353557535`**, job **`99371326028`**: SUCCESS.
- Task 6 public contracts: **3/3 PASS in 1.60 s**.
- Focused Task 6 regression: **83/83 PASS in 27.79 s**.
- Table regression: **62/62 PASS in 9.59 s**.
- Full source suite: **866/866 PASS in 181.58 s**.
- Product commit produced by that gate: **`c115bc9d810e8552a8d5138c88bfffcb3f55cb76`**.
- Product commit changed six source/test files only: `numeric.py`, `characteristics.py`, `engine.py`, and three persistent test modules.

### Idempotent re-verification

- Explicit verification trigger: **`743967f538b5806e4ab01729ae0b4c9666c9abbb`**.
- Idempotent run **`33353821187`**, job **`99372068989`**: SUCCESS.
- Product-tree materialization check: PASS.
- Task 6 public contracts: **3/3 PASS in 1.56 s**.
- Focused Task 6 regression: **83/83 PASS in 27.42 s**.
- Table regression: **62/62 PASS in 9.38 s**.
- Full source suite: **866/866 PASS in 181.88 s**.
- Final output: **`No Task 6 product or test patch to commit.`**
- Therefore Task 6 is reproducibly idempotent on the validated product tree.
- After evidence capture, the workflow plus all four Task 6 patcher/corrective scripts were deleted.
- Comparison `c115bc9...06d2e661` contains only removal of those five `.github` files; no source/test modifications occurred after the validated product commit.
- `.github` is absent on the active branch after cleanup.

## Still open

- **M-2/M-3:** Piecewise boundary value/topology/zero-unit normalization — **Task 7, next**.
- **L-1…L-4:** renderer misuse diagnostics and plot presentation polish — Tasks 8–9.
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
- **0.9.2 Audit Remediation & Reliability:** **Tasks 1–6 COMPLETE; Task 7 NEXT**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.

0.9.2 task status:

1. COMPLETE — independent C-1/H-1 natural RED;
2. COMPLETE — closed real finite SymPy evaluation;
3. COMPLETE — complete/non-silent roots + exact/numeric merge;
4. COMPLETE — intersections share zero-set semantics;
5. COMPLETE — explicit real engineering symbols, identity-safe reconstruction, scaled-`Abs` extrema, inverse-trig unit preservation, full/idempotent GREEN;
6. **COMPLETE — centralized unit-literal bounds, zero-bound physical-unit preservation, incompatible-domain validation, full/idempotent GREEN**;
7. **NEXT — Piecewise branch/continuity/zero-unit normalization**;
8. renderer misuse + actionable Piecewise diagnostics;
9. plot warning/negative-zero/exact-label polish;
10. investigation-only risk probes;
11. permanent Python 3.10–3.14 CI + IPython metadata;
12. behavior-preserving characteristics package decomposition;
13. acceptance/docs/full regression;
14. 0.9.2 version/release validation/PR, STOP before merge.

## Exact next step — Task 7

Follow the approved Task 7 order; do not skip the RED:

1. Add M-2 RED: Piecewise physical domain boundaries must store `value_symbolic` from the **selected governing branch**, not from substituting the whole Piecewise expression in a way that loses the intended branch semantics.
2. Add M-3 RED: for a continuous breakpoint such as `Piecewise((x-a, x<a), (2*(x-a), True))`, `x=a` must emit only one `side="at"` record with a dimensional zero response.
3. Preserve existing discontinuous tests: meaningful `left/at/right` records must remain.
4. After observing RED, select the actual Piecewise branch at physical boundary quantities via `_select_piecewise_branch()`, then substitute only the symbolic x location into that branch while keeping parameters symbolic.
5. Normalize exact dimensionless zero to the established physical response unit before side-value topology comparisons and result construction.
6. Collapse only mathematically redundant side records:
   - `left == at == right` -> one `at` record;
   - `left != right` -> retain meaningful `left/right`, plus `at` if distinct/defined;
   - distinct `at` -> retain `at` plus each distinct side value.
7. Focused gate:
   `python -m pytest tests/test_characteristics_piecewise_extrema.py tests/test_characteristics_extrema.py -q`
8. Then run `python -m pytest -q`.
9. Commit only if all gates are GREEN; remove temporary Task 7 validation infrastructure and verify `.github` clean before Task 8.
10. Never invoke Codex unless separately authorized.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`; runtime/package version remains 0.9.1. Tasks 1–6 are complete. Task 6 product is `c115bc9d810e8552a8d5138c88bfffcb3f55cb76`. Its authoritative GREEN run `33353557535` / job `99371326028` finished 3/3 + 83/83 + 62/62 + 866/866 PASS. Its idempotent run `33353821187` / job `99372068989` repeated 3/3 + 83/83 + 62/62 + 866/866 PASS and produced no second product/test patch. All five temporary Task 6 harness files were removed; cleanup head before this context update is `06d2e66155f6b8ce55c6501dd4a50458455a3742`, and `.github` is absent. Task 7 is the next authorized plan step: RED first for Piecewise governing branch boundary values and continuous-breakpoint topology, then narrow Piecewise normalization, focused/full GREEN, idempotence, cleanup, and context update. Exact envelopes remain deferred to 0.9.3; named cases/combinations to 0.9.4. Never invoke Codex without explicit authorization.
