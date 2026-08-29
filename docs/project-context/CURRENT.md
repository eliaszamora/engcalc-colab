# EngCalc Current Project Context

_Last updated: 2026-08-29 after EngCalc 0.7.2 design/plan approval and feature-branch setup._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical product branch: `main`.
- Canonical released baseline: **EngCalc 0.7.1**.
- `main` baseline SHA at 0.7.2 branch creation: `eab4f9a5dac6c6a0962419ba5273cd9fc212a86e`.
- Active implementation branch: `feature/v0.7.2-engineering-tables`.
- Planning branch retained: `planning/v0.7.2-engineering-tables`.
- Package/runtime version remains **0.7.1** until release closure.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`.
- Approved plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.2-engineering-tables-implementation.md`.
- The approved plan attachment commit is prepared as `2a492f07f91c79d07de48f86ea5402ee82ee2267`; feature branch ref must point to a descendant containing it before CI.
- No 0.7.2 production code or RED feature tests have been added.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume the user's Codex quota without explicit authorization.

## Approved behavior

### Existing 0.7.1 baseline

- Multi-argument user functions use exact positional arity.
- Generalized partial numeric evaluation preserves only genuinely unresolved caller symbols.
- Scalar engineering math, Pint numeric state, plotting and envelopes remain unchanged.
- Plot/envelope sampling remains 201 points; structural positive moment plots downward.

### EngCalc 0.7.2 engineering tables

- User explicitly approved the written 0.7.2 design.
- Primary form: `table(M(x), x, 0, L, 21)`.
- Exact dimensionless zero may inherit a compatible dimensional endpoint unit; nonzero dimensionless endpoints may not.
- Explicit point magnitudes may declare unit once: `table(M(x), x, [0, 1, 1.5, 2], m)`.
- Fully explicit compatible points remain valid: `table(M(x), x, [0*m, 50*cm, 1*m])`.
- Descending uniform ranges are valid.
- `count` is dimensionless integer >= 2 and includes both endpoints.
- Multiple responses preserve source order and must be dimensionally compatible in 0.7.2.
- Table evaluation must not mutate EngCalc state.
- Tables render natively as HTML inside `%%eng`, without pandas.
- Arbitrary lists remain invalid outside table-point and existing plot/envelope sweep whitelists.
- Export, interactive tables, Cartesian sweeps, cross-dimension tables, piecewise and derivation traces remain out of scope.

## Open issues / user feedback

- No known functional blocker remains for 0.7.1.
- 0.7.2 design and implementation plan are approved.
- Table-specific unit/grid mechanics are isolated from plot semantics.
- Feature-branch baseline source suite remains to be rerun before first RED feature test.

## Validation evidence

### Authoritative 0.7.1 release evidence

- Corrected distribution gate Actions `33259552699`: success.
- Validated SHA: `2332bd29e571a360cc47a29562e09b5828a3d2cb`.
- Focused: **77/77**; source: **386/386**; installed-wheel source-free: **386/386**; repeated source: **386/386**.
- Wheel artifact `9716898144`, digest `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`.

### 0.7.2 planning / execution evidence

- User approved design on 2026-08-29.
- Planning spec commit `d5ad296325157cceee088d704849f9073e3a0ec8`.
- Planning plan commit `31e2e09f65dd42b6a7343402d484a074da16c87e`.
- Feature branch created from `main` before production work.
- Feature spec commit `ed19f6013baa8c8ad78d652e45631d9dec98bb6d`.
- Plan blob `379a9cc62cd3972852205896311033141ba20f67`; attachment commit prepared as `2a492f07f91c79d07de48f86ea5402ee82ee2267`.
- No 0.7.2 test result is claimed yet.

## Roadmap / active plan

- **0.7.1 is complete and merged.**
- Active milestone: **0.7.2 — engineering tables / evaluation by points**.
- Execution: baseline validation → parser/models RED→GREEN → point normalization → engine evaluation → HTML/magic → acceptance/docs → release gate.
- Roadmap continues to 0.7.3 derivation traces afterward unless amended.

## Exact next step

- Ensure branch HEAD contains the approved spec and plan.
- Run complete baseline source suite and record exact result/SHA.
- Then add `tests/test_table_parser.py` first and observe expected RED before modifying production parser/models.
- Do not bump package version until release closure.

## How to resume in a new conversation

Read this file first. EngCalc 0.7.1 remains validated on `main` at `eab4f9a5dac6c6a0962419ba5273cd9fc212a86e`. User approved EngCalc 0.7.2 engineering tables. Active branch is `feature/v0.7.2-engineering-tables`. Governing spec/plan are the 0.7.2 files under `docs/superpowers/specs` and `docs/superpowers/plans`. Primary syntax is `table(M(x), x, 0, L, 21)` with unit-once explicit points. No production implementation or RED feature tests exist yet. Next: baseline CI, then Task 1 RED. Do not manually invoke Codex.