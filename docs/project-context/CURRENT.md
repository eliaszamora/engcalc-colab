# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.1 remains the canonical released baseline. The approved 0.9.2 Audit Remediation & Reliability plan is active on `feature/v0.9.2-audit-reliability`. Tasks 1–4 are complete. Task 5 symbol-identity audit is complete and recorded before product modification; Task 5 RED is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`** (re-verified unchanged after Task 4 cleanup).
- Runtime/package version remains **0.9.1** through Tasks 1–13.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- Task 4 cleanup head: **`f268245decb4564254e0127f32916504e145f49f`**.
- Tasks 2–4 context checkpoint: `b37a042a22c6111700d45fc3c9d1c3fa320395fa`.
- Task 5 audit workflow commit: **`0de2a1c37424c72da1d38dba2499f608c6d063c5`**.
- Approved spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-design.md`.
- Approved/refined plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-implementation.md`.
- Persistent natural audit regressions: `tests/test_v092_audit_regressions.py`.
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
- Identity-sensitive reconstruction must reuse the exact free symbol with matching `.name` when available; only otherwise create `sp.Symbol(name, real=True)`.
- Renderer-only symbol construction is display-only and must not be rewritten solely for assumptions.
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

### Task 5 identity audit — completed before product change

Authoritative grep run `33351254275`, job `99364950249`, executed exactly:

```bash
grep -R "sp\.Symbol\|sp\.symbols" -n src/engcalc_colab
```

The grep includes type annotations as well as constructions. The actual construction sites are classified as follows:

- **Identity-sensitive — engine creation:** `src/engcalc_colab/engine.py:210`, `self.symbols[name] = sp.Symbol(name)`. This is the canonical engine symbol factory and must become `real=True`.
- **Identity-sensitive — polynomial helper:** `src/engcalc_colab/numeric.py:437`, `evaluate_partial_polynomial()` reconstructs `sp.Symbol(variable)` for `sp.Poly`; it must reuse the matching symbol from `expr.free_symbols` or create a real fallback.
- **Identity-sensitive — Piecewise partial helper:** `src/engcalc_colab/numeric.py:753`, `build_partial_piecewise_evaluation()` reconstructs the interval symbol for free-symbol/condition matching; it must reuse the matching expression symbol or create a real fallback.
- **Identity-sensitive — Piecewise breakpoint extraction:** `src/engcalc_colab/piecewise.py:74`, `extract_symbolic_breakpoints()` reconstructs the comparison variable; it must reuse a matching expression free symbol or create a real fallback.
- **Identity-sensitive — characteristic solver string adapters:** `src/engcalc_colab/characteristics.py:981`, `1548`, `2012`, `2616` construct a symbol when `variable` is passed as `str` in roots/intersections/continuous-extrema/extrema paths. They must prefer the actual matching free symbol from the relevant expression(s) before a `real=True` fallback, so direct API calls with pre-existing symbols do not acquire mismatched assumptions.
- **Display-only — leave unchanged:** `src/engcalc_colab/renderer.py:284`, `311`, `1044`, `1282`, `1295`, `1297`, `1303`. These symbols exist only to form LaTeX/HTML labels, function names, targets, parameters or coordinates and are not used for polynomial/substitution/derivative/solve/Piecewise identity.
- Type annotations/checks such as `variable: sp.Symbol`, `isinstance(..., sp.Symbol)`, and `dict[str, sp.Symbol]` are not symbol constructions and require no migration.

This audit is complete before any Task 5 product source modification, satisfying Step 5.1 of the approved plan.

### Still open

- **H-1:** `extrema(abs(x-2), x, 0, 4)` still raises `unsupported piecewise relation`; this is the focused Task 5 defect.
- **Task 5 contract:** engine-created engineering symbols are not yet explicitly real; RED must be observed before correction.
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

### Task 3 — complete/non-silent root discovery

- Product commit: **`36305161768b2df568479511b916f0cf01341d94`**.
- Initial GREEN run `33350369203`, job `99362410880`: roots + fallback **36/36 PASS in 9.94 s**; natural C-1 excluding H-1 **4/4 PASS in 2.34 s**.
- Idempotent rerun `33350437106`, job `99362607491`: **36/36 PASS in 10.09 s**; C-1 **4/4 PASS in 2.37 s**; no second product commit.
- Temporary Task 3 workflow/script removed.

### Task 4 — intersections reuse shared zero-set semantics

- Product commit: **`36ae6a7b4bb1c7adc59300679e967db02521944f`**.
- Initial GREEN run `33350705926`, job `99363373533`: shared gate **56/56 PASS in 14.63 s**; natural C-1 excluding H-1 **4/4 PASS in 2.36 s**.
- Idempotent rerun `33350776880`, job `99363578401`: shared gate **56/56 PASS in 14.12 s**; natural C-1 **4/4 PASS in 2.33 s**; H-1 exactly one expected failure; no second product patch.
- Task 4 workflow removed at `7e536587e71098e6f734b88330d63b3b709b7fa3`; script removed at **`f268245decb4564254e0127f32916504e145f49f`**.

### Task 5 — pre-change symbol identity audit

- Temporary audit workflow commit: **`0de2a1c37424c72da1d38dba2499f608c6d063c5`**.
- Run **`33351254275`**, job **`99364950249`**: SUCCESS.
- Exact grep recorded all source occurrences and the identity/display classification above.
- No Task 5 product source modification had occurred when this audit was recorded.

## Roadmap / active plan

- **0.9.0 Matrix/CAS:** COMPLETE + MERGED.
- **0.9.1 Exact Characteristics:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.2 Audit Remediation & Reliability:** **Tasks 1–4 COMPLETE; Task 5 audit COMPLETE; Task 5 RED NEXT**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.

0.9.2 task status:

1. COMPLETE — independent C-1/H-1 natural RED;
2. COMPLETE — closed real finite SymPy evaluation;
3. COMPLETE — complete/non-silent roots + exact/numeric merge;
4. COMPLETE — intersections share zero-set semantics;
5. **IN PROGRESS — symbol audit complete; RED→GREEN migration next**;
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

1. Remove the temporary Task 5 audit workflow after its evidence has been captured.
2. Add runner-only RED contracts for `EngineeringEngine.resolve_symbol("x").is_real is True` and dimensional `abs` extrema:
   `L := 4*m`, `q := 2*kN/m`, `M(x)=q*(x-L/2)`, `extrema(abs(M(x)),x,0,L)` with global minimum at `x=2 m`, `0 kN`.
3. Include the existing dimensionless H-1 case in the RED gate.
4. Observe the RED before touching product code, then persist the tests.
5. Migrate engine symbol creation to `real=True` and repair every identity-sensitive reconstruction according to the audit; leave renderer-only symbols unchanged.
6. Run the Task 5 broad regression set and then `python -m pytest -q`; do not start Task 6 unless the full source suite is GREEN.
7. Remove temporary Task 5 validation infrastructure and update this file.
8. Never invoke Codex unless separately authorized.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`, version remains 0.9.1. Tasks 1–4 are complete. Task 5 is in progress: the mandatory pre-change symbol audit is complete and recorded from run `33351254275`, job `99364950249`; no Task 5 product source had been modified when the audit was persisted. Identity-sensitive sites are engine symbol creation, two numeric helpers, Piecewise breakpoint extraction, and four characteristic string adapters; renderer constructions are display-only. Next action is runner-only Task 5 RED for the real-symbol contract plus dimensional and dimensionless `abs` extrema, then the narrow identity-safe migration. Exact envelopes remain deferred to 0.9.3; named cases/combinations to 0.9.4. Never invoke Codex without explicit authorization.
