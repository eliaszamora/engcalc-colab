# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.1 remains the canonical released baseline. A new 0.9.2 Audit Remediation & Reliability design has been written on `feature/v0.9.2-audit-reliability` in response to the independent Claude audit. No 0.9.2 product code has been changed yet; implementation is blocked on explicit user approval of the written spec._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**.
- 0.9.1 PR #33 merge commit: `25edd1e652081f31c16ffed05d24f4d00eaa8950`.
- Runtime/package version remains **0.9.1**.
- Real 0.9.1 wheel SHA-256: `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- 0.9.2 design spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-design.md`.
- Current spec commit: **`f21a4917da996d62a69477ecdad88305109a0078`**.
- No 0.9.2 implementation plan exists yet.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.

## Approved behavior

Released 0.9.1 public characteristic calls remain:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

- Characteristic solving remains exact-first, unit-aware, Piecewise-safe, scalar-only and provenance-preserving.
- Deterministic numeric fallback supplements exact solving when exact resolution is incomplete/unresolved.
- Whole matrices remain invalid scalar characteristic responses; indexed matrix scalars remain valid.
- Ordinary `plot(...)` retains a 201-point drawing grid with exact characteristic metadata independent of that grid.
- Positive structural moment remains plotted downward.
- Existing Numeric/Pint, Piecewise, tables, plots, envelopes, multi-argument functions and Matrix/CAS behavior remain regression requirements.
- `envelope(...)` remains sampled through 0.9.2.
- The proposed 0.9.2 design changes user-created SymPy engineering symbols to `real=True`, after an identity-sensitive source audit and RED tests.
- The proposed 0.9.2 design makes compatible direct unit literals valid in table/plot/roots/intersections/extrema bounds.
- The proposed Piecewise rule is: a continuous breakpoint emits one meaningful `at` value; real discontinuities retain side topology.

## Open issues / user feedback

Independent Claude audit of `main@698696bb` reported 846/846 existing tests green plus 38 adversarial probes and classified:

- **C-1 critical:** `roots()` / `intersections()` can silently return zero results for real roots when `sp.solve` returns exact objects such as `E`, `LambertW` or `CRootOf` that EngCalc cannot numerically validate, while the fallback is incorrectly suppressed.
- **H-1 high:** `extrema(abs(...))` fails because engine symbols have no `real=True` assumption.
- **M-1:** direct unit literals are inconsistent between table and plot/characteristic bounds.
- **M-2:** Piecewise extrema boundary `value_symbolic` can retain an unresolved outer Piecewise despite a numerically decidable branch.
- **M-3:** continuous Piecewise breakpoints can emit unnecessary `left/at/right`, with dimensional-zero inconsistency.
- **L-1…L-4:** renderer characteristic misuse crashes accidentally; matplotlib `semibold` warning; weaker Piecewise diagnostics; negative zero / exact-coordinate label polish.
- **I-1…I-3:** no permanent CI; IPython undeclared in project metadata; declared Python >=3.10 not continuously validated across 3.10–3.14.

These audit claims are **not yet EngCalc-confirmed defects**. The 0.9.2 spec requires independent RED reproduction before each product correction.

Audit potential risks without a confirmed reproduction remain investigation-only: residual equality tolerance, tri-state `is_real`, and unbounded `sp.simplify` cost.

Separate existing issues remain deferred: `no_vertical_scroll()`, multiline ordinary non-matrix function-call parsing, generalized structural eigenproblems.

## Validation evidence

### Canonical 0.9.1 release

- Final pre-PR run `33345708275`, job `99349296928`: 23/23 release contract PASS; 846/846 full source PASS in 111.56 s.
- Real wheel: `engcalc_colab-0.9.1-py3-none-any.whl`.
- External wheel smoke: PASS.
- Installed-wheel source-free suite: 846/846 PASS in 90.59 s.
- Post-wheel source suite: 846/846 PASS in 89.52 s.
- Post-merge run `33346335859`, job `99351086733`: 23/23 release contract PASS; 846/846 full source PASS in 133.55 s.

### External 0.9.1 audit input

- Audited commit: `698696bb`.
- Audit environment: Python 3.14.3.
- Existing suite observed by auditor: 846/846 GREEN.
- Independent adversarial probes: 38.
- External audit reported C-1/H-1/M-1/M-2/M-3/L-1…L-4 and infrastructure observations.
- The auditor’s verified-good behaviors included canonical beam characteristics, no false Piecewise jump root, correct discontinuous Piecewise topology, even-multiplicity roots, dimensional guards, indexed matrix scalar roots, deterministic fallback where activated, close roots, and exact off-grid plot coordinates.
- No 0.9.2 RED/GREEN product validation has run yet.

### 0.9.2 design state

- Branch created from `main@698696bb`.
- Written spec committed and self-reviewed at `f21a4917da996d62a69477ecdad88305109a0078`.
- No production source file has been modified for 0.9.2.
- No test has yet been added for 0.9.2.
- Version remains 0.9.1.

## Roadmap / active plan

- **0.9.0 Matrix/CAS:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.1 Exact Characteristics:** COMPLETE + RELEASE-VALIDATED + MERGED + POST-MERGE VALIDATED.
- **0.9.2 Audit Remediation & Reliability:** DESIGN WRITTEN — AWAITING USER SPEC APPROVAL.
- **0.9.3:** Exact Envelopes / Governing Intervals.
- **0.9.4:** Named Response Cases / Combinations.
- Later: **0.10.x engineering operations/verification → 1.0.0 stabilization**.

0.9.2 proposed sequence after spec approval:

1. write detailed implementation plan;
2. independently reproduce audit C/H/M findings in RED tests;
3. fix C-1 exact candidate evaluation + incomplete `solve` fallback/merge;
4. migrate engineering symbols to real assumptions with identity audit;
5. unify direct unit literals in bounds;
6. correct Piecewise symbolic/continuity topology;
7. close L-1…L-4;
8. investigate audit potential risks without speculative fixes;
9. split `characteristics.py` into the approved package layout without behavior change;
10. add permanent Python 3.10–3.14 CI and declared IPython dependency;
11. full acceptance + wheel/source-free release validation;
12. release PR, explicit merge approval, post-merge validation.

## Exact next step

1. **STOP before implementation.**
2. User reviews `docs/superpowers/specs/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-design.md`.
3. If the user approves the spec, invoke the Superpowers `writing-plans` workflow and write the detailed 0.9.2 implementation plan.
4. Ask for/confirm inline execution choice as required by the plan workflow.
5. Only after the plan is approved/selected, begin Task 1 RED reproduction.
6. Never invoke Codex unless separately authorized.

## How to resume in a new conversation

Read this file first. `main@698696bb8854fa197851cdbb2f5e4c08ef22178b` is the canonical EngCalc 0.9.1 baseline. The external Claude audit motivated a reliability release before exact envelopes. Active branch is `feature/v0.9.2-audit-reliability`; version is still 0.9.1; no product/test implementation has begun. The 0.9.2 design spec is committed at `f21a4917da996d62a69477ecdad88305109a0078` and awaits explicit user approval. After approval, write the implementation plan before touching product code. Exact envelopes are deferred to 0.9.3; named cases/combinations to 0.9.4. Never invoke Codex without explicit authorization.
