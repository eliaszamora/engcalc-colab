# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.1 remains the canonical released baseline. The 0.9.2 Audit Remediation & Reliability spec and 14-task implementation plan are approved. Task 1 is now complete at the RED stage: EngCalc independently reproduced all five natural C-1/H-1 audit contracts on Python 3.13.15. No 0.9.2 product source code has been modified yet._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**.
- 0.9.1 PR #33 merge commit: `25edd1e652081f31c16ffed05d24f4d00eaa8950`.
- Runtime/package version remains **0.9.1** until 0.9.2 release Task 14.
- Real 0.9.1 wheel SHA-256: `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- Approved 0.9.2 spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-design.md`.
- Spec approval/status commit: **`e32a6d9b86fe6e248a4974d1bcf4ffd53ae172ee`**.
- 0.9.2 implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-implementation.md`.
- Refined/self-reviewed plan commit: **`75fbace4326ba866a728677924d02295629327fe`**.
- Persistent Task 1 regression tests: `tests/test_v092_audit_regressions.py`, created at **`507857cce52292b22a44fed4ba23b3f56ff40cb5`**.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.

## Approved behavior

Released public characteristic calls remain unchanged:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

0.9.2 approved contract:

- External audit findings are inputs to investigate; each confirmed defect first receives an EngCalc-owned RED reproduction.
- No plausible exact-candidate evaluation failure may silently become “no solution.”
- Exact-first remains authoritative; deterministic fallback supplements incomplete exact discovery; exact provenance wins on deduplication.
- User engineering symbols become `sp.Symbol(name, real=True)` only after an identity-sensitive source audit.
- Direct supported unit literals become valid consistently in bounds for `roots`, `intersections`, `extrema`, `plot`, and `table`.
- Piecewise boundary `value_symbolic` reflects the selected governing branch when decidable.
- Continuous Piecewise breakpoints emit one meaningful `side="at"`; true discontinuities retain meaningful side topology; physical zero units are consistent.
- `render_result()` remains the LaTeX calculation renderer and explicitly rejects characteristic results with guidance to `render_characteristic_result()` rather than merging return contracts.
- Matplotlib title weight uses a supported value; negative zero is normalized; exact compact plot coordinates such as `1/3` are exposed in labels without moving the exact marker.
- Permanent CI validates Python 3.10–3.14; IPython becomes a declared dependency; `requires-python >=3.10` remains unchanged unless separately approved.
- Audit potential risks (residual equality, tri-state realness, simplify cost) are investigation-only until deterministic reproduction.
- `characteristics.py` is split by responsibility only after corrected behavior and the complete source suite are GREEN.
- Ordinary plots retain the 201-point drawing grid and exact metadata; positive structural moment remains plotted downward.
- `envelope(...)` remains sampled in 0.9.2; exact envelopes are deferred to **0.9.3**.
- Named cases/combinations are deferred to **0.9.4**; `figure(...)` and `check(...)` are out of 0.9.2 scope.

## Open issues / user feedback

The independent audit findings are now split into EngCalc-confirmed versus still-unconfirmed items.

### EngCalc-confirmed by Task 1 RED

- **C-1 critical:** `roots(log(x)-1, x, 1, 10)`, `roots(exp(x)-3*x, x, 0, 3)` and `roots(x^5-x-1, x, 0, 2)` each returned **zero points** instead of their real roots.
- **C-1 intersections:** `intersections(log(x), 1+0*x, x, 1, 10)` returned **zero points** instead of the real intersection at `x=e`.
- **H-1 high:** `extrema(abs(x-2), x, 0, 4)` failed with `EngEvaluationError: line 2: unsupported piecewise relation` rather than returning the cusp minimum at `x=2`.

### Still awaiting their own focused RED tasks

- **M-1:** direct unit-literal bounds are inconsistent between table and plot/characteristic APIs.
- **M-2:** Piecewise extrema boundary `value_symbolic` can retain a resolvable outer Piecewise.
- **M-3:** continuous Piecewise breakpoints can emit unnecessary side triples with zero-unit inconsistency.
- **L-1…L-4:** renderer misuse crash, matplotlib `semibold` warning, weaker Piecewise diagnostics, negative-zero/exact-coordinate label polish.
- **I-1…I-3:** no permanent CI, IPython undeclared, advertised Python 3.10–3.14 range not continuously tested.
- Potential risks (residual equality, tri-state `is_real`, simplify cost) remain investigation-only until Task 10.
- Separate deferred issues remain `no_vertical_scroll()`, multiline ordinary non-matrix call parsing and generalized structural eigenproblems.

## Validation evidence

### Canonical 0.9.1 release

- Final pre-PR run `33345708275`, job `99349296928`: 23/23 release contract PASS; 846/846 full source PASS in 111.56 s.
- Real wheel: `engcalc_colab-0.9.1-py3-none-any.whl`; SHA-256 `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`.
- External wheel smoke: PASS.
- Installed-wheel source-free suite: 846/846 PASS in 90.59 s.
- Post-wheel source suite: 846/846 PASS in 89.52 s.
- Post-merge run `33346335859`, job `99351086733`: 23/23 release contract PASS; 846/846 full source PASS in 133.55 s.

### 0.9.2 design/planning evidence

- Branch created from `main@698696bb`.
- External audit source: `main@698696bb`, Python 3.14.3, 846/846 existing tests plus 38 independent adversarial probes.
- Spec written, self-reviewed and explicitly approved by the user; approved status commit `e32a6d9b86fe6e248a4974d1bcf4ffd53ae172ee`.
- Detailed implementation plan has **14 tasks**, was self-reviewed for scope/placeholders/type/interface consistency, and refined at `75fbace4326ba866a728677924d02295629327fe`.
- Version remains 0.9.1.

### 0.9.2 Task 1 — authoritative RED

- Temporary runner-only RED workflow commit: `2c9e44b26ab0b027f0a16a803f9c43d5e5b0dbfd`.
- GitHub Actions run **`33349614143`**, job **`99360260965`**.
- Environment: Ubuntu 24.04, CPython **3.13.15**, SymPy 1.14.0, Pint 0.25.3.
- Command: `python -m pytest tests/test_v092_audit_regressions.py -q`.
- Result: **5 failed / 0 passed in 2.41 s**.
- `roots(log(x)-1, x, 1, 10)`: expected one root near `e`; actual `points=()`.
- `roots(exp(x)-3*x, x, 0, 3)`: expected two real roots; actual `points=()`.
- `roots(x^5-x-1, x, 0, 2)`: expected one real root; actual `points=()`.
- `intersections(log(x), 1+0*x, x, 1, 10)`: expected one point; actual `points=()`.
- `extrema(abs(x-2), x, 0, 4)`: raised `EngEvaluationError: line 2: unsupported piecewise relation`.
- The workflow materialized the tests only inside the runner before the RED, so no product/test implementation preceded the observed failure.
- Temporary workflow removed at `f2806962a8a06af5b11ebff60549963cbbe88152`.
- The exact RED tests were then persisted at `507857cce52292b22a44fed4ba23b3f56ff40cb5`.
- **No product source file has been modified yet.**

## Roadmap / active plan

- **0.9.0 Matrix/CAS:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.1 Exact Characteristics:** COMPLETE + RELEASE-VALIDATED + MERGED + POST-MERGE VALIDATED.
- **0.9.2 Audit Remediation & Reliability:** **Task 1 RED COMPLETE; Task 2 NEXT**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.
- Later: **0.10.x engineering operations/verification → 1.0.0 stabilization**.

0.9.2 implementation plan:

1. **COMPLETE — independent C-1/H-1 natural RED reproduction: 5/5 confirmed failing**;
2. **NEXT — closed real finite SymPy number evaluation**;
3. complete/non-silent root discovery and exact/numeric merge;
4. intersections reuse shared zero-set semantics;
5. safe `real=True` symbol migration + identity audit;
6. centralized direct unit-literal bounds;
7. Piecewise branch/continuity/zero-unit normalization;
8. renderer misuse + actionable Piecewise diagnostics;
9. plot warning/negative-zero/exact-label polish;
10. investigation-only audit risk probes;
11. permanent Python 3.10–3.14 CI + IPython metadata;
12. behavior-preserving `characteristics` package decomposition;
13. acceptance/docs/full regression;
14. version RED/bump, wheel, external smoke, source-free suite, repeated source suite, release PR, STOP before merge.

## Exact next step

1. Execute **Task 2** with TDD.
2. Add focused RED tests in `tests/test_numeric_context.py` for closed real finite SymPy values (`E`, real `LambertW`, real `CRootOf`) plus rejection of non-real/non-finite values.
3. Observe the focused RED before touching `src/engcalc_colab/numeric.py`.
4. Implement only the narrow closed-number fallback in `_evaluate_sympy()`.
5. Re-run `tests/test_numeric_context.py` plus `tests/test_v092_audit_regressions.py`; closed-number tests must be GREEN while C-1/H-1 may legitimately remain RED until Tasks 3/5.
6. Never invoke Codex unless separately authorized.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`; version remains 0.9.1. The 0.9.2 spec is approved and the 14-task plan is active. Task 1 is complete at RED: run `33349614143`, job `99360260965`, Python 3.13.15, **5/5 failed in 2.41 s** exactly as documented above. Persistent tests are `tests/test_v092_audit_regressions.py` from commit `507857cce52292b22a44fed4ba23b3f56ff40cb5`. No product source code has been modified yet. Next action is Task 2 closed real finite SymPy numeric evaluation with test-first RED. Exact envelopes remain deferred to 0.9.3; named cases/combinations to 0.9.4. Never invoke Codex without explicit authorization.
