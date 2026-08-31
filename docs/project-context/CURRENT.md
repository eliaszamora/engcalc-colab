# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.1 remains the canonical released baseline. The user approved the 0.9.2 Audit Remediation & Reliability spec, and the detailed 14-task implementation plan is written/self-reviewed on `feature/v0.9.2-audit-reliability`. No 0.9.2 product code or RED tests have been implemented yet._

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

Independent Claude audit of `main@698696bb` reported 846/846 existing tests green plus 38 adversarial probes and identified:

- **C-1 critical:** roots/intersections can silently miss valid real roots when exact candidates (`E`, `LambertW`, `CRootOf`) cannot be physically evaluated and incomplete `sp.solve` suppresses fallback.
- **H-1 high:** `extrema(abs(...))` fails because engine symbols are not explicitly real.
- **M-1:** direct unit-literal bounds are inconsistent between table and plot/characteristic APIs.
- **M-2:** Piecewise extrema boundary `value_symbolic` can retain a resolvable outer Piecewise.
- **M-3:** continuous Piecewise breakpoints can emit unnecessary side triples with zero-unit inconsistency.
- **L-1…L-4:** renderer misuse crash, matplotlib `semibold` warning, weaker Piecewise diagnostics, negative-zero/exact-coordinate label polish.
- **I-1…I-3:** no permanent CI, IPython undeclared, advertised Python 3.10–3.14 range not continuously tested.

These remain external findings until Task 1 and subsequent focused RED tests independently reproduce them. Separate deferred issues remain `no_vertical_scroll()`, multiline ordinary non-matrix call parsing and generalized structural eigenproblems.

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
- The plan uses RED→GREEN for confirmed audit defects, full source gates after cross-cutting changes, permanent Python 3.10–3.14 CI, behavior-preserving characteristic decomposition, and full wheel/source-free release validation.
- No 0.9.2 product source file has been modified yet.
- No 0.9.2 RED test has run yet.
- Version remains 0.9.1.

## Roadmap / active plan

- **0.9.0 Matrix/CAS:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.1 Exact Characteristics:** COMPLETE + RELEASE-VALIDATED + MERGED + POST-MERGE VALIDATED.
- **0.9.2 Audit Remediation & Reliability:** **SPEC APPROVED + IMPLEMENTATION PLAN COMPLETE — READY FOR EXECUTION CHOICE**.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.
- Later: **0.10.x engineering operations/verification → 1.0.0 stabilization**.

0.9.2 implementation plan:

1. independent C-1/H-1 natural RED reproduction;
2. closed real finite SymPy number evaluation;
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

1. Select execution mode for the approved plan.
2. Preferred/current project mode is **Inline Execution** with `superpowers:executing-plans`; no Codex.
3. After execution mode is confirmed, read the approved spec and plan, then execute **Task 1 only far enough to obtain authoritative RED evidence** before any product patch.
4. Update this file with exact RED run/count/failure evidence in the same branch.
5. Continue tasks in plan order with focused GREEN then required broad/full gates.
6. Do not merge a future 0.9.2 PR without explicit user approval.

## How to resume in a new conversation

Read this file first. Canonical released baseline is `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`; version remains 0.9.1. The user approved the 0.9.2 Audit Remediation & Reliability spec, now marked approved at commit `e32a6d9b86fe6e248a4974d1bcf4ffd53ae172ee`. The detailed 14-task plan is `docs/superpowers/plans/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-implementation.md`, refined at `75fbace4326ba866a728677924d02295629327fe`. No product patch or RED test has begun. Next action is execution-mode confirmation, then Task 1 independent C-1/H-1 RED reproduction. Exact envelopes are deferred to 0.9.3; named cases/combinations to 0.9.4. Never invoke Codex without explicit authorization.
