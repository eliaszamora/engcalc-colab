# EngCalc Current Project Context

_Last updated: 2026-08-29 — 0.7.2 approved; feature branch setup is being finalized before baseline validation._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Released baseline: **EngCalc 0.7.1** on `main` at `eab4f9a5dac6c6a0962419ba5273cd9fc212a86e`.
- Active branch: `feature/v0.7.2-engineering-tables`.
- Planning branch retained: `planning/v0.7.2-engineering-tables`.
- Version remains **0.7.1** until release closure.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`.
- Approved plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.2-engineering-tables-implementation.md`.
- Plan content exists in repository blob `379a9cc62cd3972852205896311033141ba20f67`; attachment commit `2a492f07f91c79d07de48f86ea5402ee82ee2267` was prepared.
- No 0.7.2 production code or feature tests exist yet.
- Do not invoke Codex or consume Codex quota without explicit authorization.

## Approved behavior

- Preserve all 0.7.1 semantics.
- Primary table form: `table(M(x), x, 0, L, 21)`.
- Exact zero can inherit a compatible dimensional peer endpoint; nonzero dimensionless values cannot.
- Unit-once points: `table(M(x), x, [0, 1, 1.5, 2], m)`.
- Fully explicit compatible points: `table(M(x), x, [0*m, 50*cm, 1*m])`.
- Descending ranges valid; count dimensionless integer >=2 including endpoints.
- Multiple responses preserve source order and are dimensionally compatible in 0.7.2.
- Evaluation does not mutate state. HTML rendering is native in `%%eng`; no pandas.
- Arbitrary lists remain rejected outside approved positions.

## Open issues / user feedback

- No known 0.7.1 blocker.
- User approved 0.7.2.
- Baseline suite must run before first RED test.

## Validation evidence

- 0.7.1 authoritative Actions `33259552699`: 77 focused, 386 source, 386 installed-wheel, 386 repeated.
- Artifact `9716898144`; digest `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`.
- Planning spec `d5ad296325157cceee088d704849f9073e3a0ec8`; plan `31e2e09f65dd42b6a7343402d484a074da16c87e`.
- Feature spec `ed19f6013baa8c8ad78d652e45631d9dec98bb6d`.
- No 0.7.2 test evidence yet.

## Roadmap / active plan

- 0.7.1 complete.
- Active: 0.7.2 engineering tables.
- Sequence: baseline → parser/models RED/GREEN → normalization → engine → HTML/magic → acceptance/docs → release gate.

## Exact next step

- Finalize feature HEAD with approved plan.
- Run full baseline suite.
- Add first parser test RED before any production change.

## How to resume in a new conversation

EngCalc 0.7.1 is baseline. User approved 0.7.2. Active branch `feature/v0.7.2-engineering-tables`; governing spec/plan are documented above. No production/table tests yet. Next: finalize plan attachment, baseline CI, then Task 1 RED. Do not invoke Codex without explicit authorization.