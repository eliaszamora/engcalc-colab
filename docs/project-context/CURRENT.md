# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.1 remains the canonical released baseline. The approved 0.9.2 Audit Remediation & Reliability plan is active on `feature/v0.9.2-audit-reliability`. Tasks 1–4 are complete; Task 5 (safe `real=True` symbol migration + H-1 `abs` extrema) is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`** (re-verified unchanged after Task 4 cleanup).
- Runtime/package version remains **0.9.1** through Tasks 1–13.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- Task 4 cleanup head before this context update: **`f268245decb4564254e0127f32916504e145f49f`**.
- Approved spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-design.md`.
- Approved/refined plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-implementation.md`.
- Persistent natural audit regressions: `tests/test_v092_audit_regressions.py`.
- No temporary `.github` validation infrastructure remains after Task 4 cleanup.
- Never invoke Codex / Codex Cloud without explicit user authorization.

## Approved behavior

Public characteristic syntax remains unchanged:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

0.9.2 reliability contract:

- External audit findings must first receive EngCalc-owned RED reproduction.
- Exact-first remains authoritative; deterministic fallback supplements incomplete exact discovery.
- Exact provenance wins when an exact and numeric candidate represent the same physical location.
- Plausible exact-candidate evaluation failure must never silently become “no solution.”
- `roots()` and `intersections()` share one continuous zero-set discovery/validation/fallback/merge policy.
- User engineering symbols migrate to `sp.Symbol(name, real=True)` only after identity-sensitive symbol construction is audited.
- Direct supported unit literals must become consistent across bounds for roots/intersections/extrema/plot/table in Task 6.
- Piecewise boundary/topology normalization remains Task 7.
- Ordinary plots retain 201 drawing samples and exact metadata; positive structural moment remains plotted downward.
- `envelope(...)` remains sampled in 0.9.2; exact envelopes are deferred to 0.9.3.
- No SciPy dependency.
- Permanent Python 3.10–3.14 CI and declared IPython dependency remain Task 11.
- Version bump to 0.9.2 occurs only in Task 14.
- Release PR must stop before merge pending explicit user approval.

## Open issues / user feedback

### Fixed in Tasks 2–4

- **C-1 roots:** natural `log(x)-1`, `exp(x)-3*x`, and quintic cases no longer return silent empty sets.
- **C-1 intersections:** `intersections(log(x), 1+0*x, x, 1, 10)` now resolves via the same zero-set semantics as roots.
- Closed real finite SymPy numbers such as `E`, real `LambertW`, and real `CRootOf` can now be physically evaluated without discarding exact symbolic objects.
- `oo`, `-oo`, `zoo`, `nan`, and non-real closed symbolic values are rejected.
- Incomplete `solveset` + partial `solve` output no longer suppresses deterministic fallback.
- Intersections preserve exact dimensional symbolic locations such as `P/(2*q)` while still supplementing incomplete exact discovery numerically.

### Still open

- **H-1:** `extrema(abs(x-2), x, 0, 4)` still raises `unsupported piecewise relation`; this is the focused Task 5 defect.
- **M-1:** direct unit-literal bound inconsistency — Task 6.
- **M-2/M-3:** Piecewise boundary value/topology/zero-unit normalization — Task 7.
- **L-1…L-4:** renderer misuse diagnostics and plot presentation polish — Tasks 8–9.
- **I-1…I-3:** permanent CI/IPython metadata — Task 11.
- Audit potential risks remain investigation-only until Task 10.
- Separate deferred issues remain `no_vertical_scroll()`, multiline ordinary non-matrix call parsing, and generalized structural eigenproblems.

## Validation evidence

### Canonical 0.9.1

- `main@698696bb8854fa197851cdbb2f5e4c08ef22178b` remains unchanged.
- 0.9.1 final pre-PR: 23/23 release contract; 846/846 full source.
- Real wheel SHA-256: `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`.
- Post-merge source validation: 846/846 PASS.

### Task 1 — natural RED reproduction

- Run `33349614143`, job `99360260965`, CPython 3.13.15.
- `tests/test_v092_audit_regressions.py`: **5 failed / 0 passed in 2.41 s**.
- All three roots cases, the log intersection, and H-1 `abs` extrema were independently confirmed before product correction.

### Task 2 — closed real finite SymPy numbers

- Persistent focused tests added to `tests/test_numeric_context.py`.
- Product commit: **`e3befd1256bb5ec2ac6ab0c9679814051a530a34`**.
- Focused gate: **21/21 PASS**.
- Idempotent rerun: **21/21 PASS**, no second product patch.
- After Task 2, three of the original characteristic failures naturally became solvable; the second `exp(x)-3*x` root and H-1 remained isolated for later tasks.

### Task 3 — complete/non-silent root discovery

- Product commit: **`36305161768b2df568479511b916f0cf01341d94`**.
- Initial GREEN run `33350369203`, job `99362410880`:
  - roots + fallback: **36/36 PASS in 9.94 s**;
  - natural C-1 excluding H-1: **4/4 PASS in 2.34 s**;
  - H-1 deliberately remained **1 failing**.
- Idempotent rerun `33350437106`, job `99362607491`:
  - roots + fallback: **36/36 PASS in 10.09 s**;
  - natural C-1: **4/4 PASS in 2.37 s**;
  - no second product commit.
- Temporary Task 3 workflow/script removed.

### Task 4 — intersections reuse shared zero-set semantics

- Focused RED detected two issues: incomplete-discovery provenance loss plus a transient dimensional exactness regression (`P/(2*q)` falling to numeric `1.0`).
- Product commit: **`36ae6a7b4bb1c7adc59300679e967db02521944f`**.
- Initial GREEN run `33350705926`, job `99363373533`:
  - roots/intersections/fallback/engine shared gate: **56/56 PASS in 14.63 s**;
  - natural C-1 excluding H-1: **4/4 PASS in 2.36 s**;
  - H-1 remained the sole expected RED.
- Idempotent rerun `33350776880`, job `99363578401`:
  - shared zero-set gate: **56/56 PASS in 14.12 s**;
  - natural C-1 excluding H-1: **4/4 PASS in 2.33 s**;
  - H-1 remained exactly **1 failing**;
  - product step reported `No Task 4 product patch to commit.`
- Task 4 validation workflow removed at `7e536587e71098e6f734b88330d63b3b709b7fa3`.
- Task 4 validation script removed at **`f268245decb4564254e0127f32916504e145f49f`**.
- `.github` is absent again on the feature branch.

## Roadmap / active plan

- **0.9.0 Matrix/CAS:** COMPLETE + MERGED.
- **0.9.1 Exact Characteristics:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.2 Audit Remediation & Reliability:** **Tasks 1–4 COMPLETE; Task 5 NEXT**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.

0.9.2 task status:

1. COMPLETE — independent C-1/H-1 natural RED;
2. COMPLETE — closed real finite SymPy evaluation;
3. COMPLETE — complete/non-silent roots + exact/numeric merge;
4. COMPLETE — intersections share zero-set semantics;
5. **NEXT — safe `real=True` symbol migration + H-1 `abs` extrema**;
6. centralized direct unit-literal bounds;
7. Piecewise branch/continuity/zero-unit normalization;
8. renderer misuse + actionable Piecewise diagnostics;
9. plot warning/negative-zero/exact-label polish;
10. investigation-only risk probes;
11. permanent Python 3.10–3.14 CI + IPython metadata;
12. behavior-preserving characteristics package decomposition;
13. acceptance/docs/full regression;
14. 0.9.2 version/release validation/PR, STOP before merge.

## Exact next step

1. Execute Task 5 with strict RED→GREEN.
2. Audit all `sp.Symbol` / `sp.symbols` creation in `src/engcalc_colab`; classify identity-sensitive vs display-only reconstruction.
3. Persist the identity audit in this file before changing the engine symbol assumptions.
4. Add RED contracts that `EngineeringEngine.resolve_symbol("x").is_real is True` and that dimensional `abs` extrema preserve units and identify the cusp minimum.
5. Observe RED before touching product code.
6. Migrate engine-created engineering symbols to `real=True` and repair every identity-sensitive reconstruction found by the audit.
7. Run the Task 5 focused regressions plus matrix partial numeric, multiarg numeric, Piecewise extrema, characteristic engine, plot integration, magic, and natural audit regressions.
8. H-1 must become GREEN without regressing Tasks 2–4.
9. Remove temporary validation infrastructure and update `CURRENT.md`.
10. Never invoke Codex unless separately authorized.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`, version remains 0.9.1. Tasks 1–4 of the approved 14-task 0.9.2 plan are complete. Task 4 product commit is `36ae6a7b4bb1c7adc59300679e967db02521944f`; authoritative idempotent run is `33350776880`, job `99363578401`, with 56/56 shared zero-set tests and 4/4 natural C-1 tests GREEN while H-1 remains the one expected RED. All Task 4 temporary `.github` files are removed; cleanup head before this context update is `f268245decb4564254e0127f32916504e145f49f`. The exact next action is Task 5: audit symbol construction, add RED `real=True` and dimensional-`abs` extrema contracts, then make the narrow identity-safe migration. Exact envelopes remain deferred to 0.9.3; named cases/combinations to 0.9.4. Never invoke Codex without explicit authorization.
