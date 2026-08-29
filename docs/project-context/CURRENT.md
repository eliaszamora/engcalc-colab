# EngCalc Current Project Context

_Last updated: 2026-08-29 after EngCalc 0.7.2 design/plan approval and isolated feature-branch setup._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released baseline: **EngCalc 0.7.1** on `main` at `eab4f9a5dac6c6a0962419ba5273cd9fc212a86e`.
- Active branch: `feature/v0.7.2-engineering-tables`; planning branch retained.
- Package/runtime remains **0.7.1** until release closure.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`.
- Approved plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.2-engineering-tables-implementation.md`.
- Approved plan blob: `379a9cc62cd3972852205896311033141ba20f67`; plan attachment commit prepared as `2a492f07f91c79d07de48f86ea5402ee82ee2267`.
- No 0.7.2 production code or RED feature tests have been added.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume Codex quota without explicit authorization.

## Approved behavior

- Existing 0.7.1 behavior remains backward compatible, including multi-argument functions, generalized partial evaluation, scalar math, 201-point plots/envelopes and positive-moment-down convention.
- 0.7.2 primary syntax: `table(M(x), x, 0, L, 21)`.
- Exact dimensionless zero may inherit a compatible dimensional peer endpoint; nonzero dimensionless endpoints may not.
- Unit-once explicit points: `table(M(x), x, [0, 1, 1.5, 2], m)`.
- Fully explicit compatible points: `table(M(x), x, [0*m, 50*cm, 1*m])`.
- Descending uniform ranges are valid; count is dimensionless integer >= 2 and includes both endpoints.
- Multiple table responses preserve source order and must be dimensionally compatible in 0.7.2.
- Table evaluation must not mutate state; HTML rendering is native to `%%eng`; no pandas dependency.
- Arbitrary list syntax remains rejected outside approved table-point and plot/envelope sweep positions.
- Export, interactive tables, Cartesian table sweeps, cross-dimension tables, piecewise and derivation traces are out of scope.

## Open issues / user feedback

- No known 0.7.1 functional blocker.
- User explicitly approved 0.7.2 design and implementation continuation.
- Feature-branch baseline source suite must be rerun before first RED feature test.

## Validation evidence

- 0.7.1 authoritative gate Actions `33259552699`: focused **77/77**, source **386/386**, installed-wheel source-free **386/386**, repeated source **386/386**.
- 0.7.1 artifact `9716898144`; digest `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`.
- Planning spec commit `d5ad296325157cceee088d704849f9073e3a0ec8`; plan commit `31e2e09f65dd42b6a7343402d484a074da16c87e`.
- Feature spec commit `ed19f6013baa8c8ad78d652e45631d9dec98bb6d`.
- No 0.7.2 RED/GREEN test evidence is claimed yet.

## Roadmap / active plan

- **0.7.1 complete and merged.**
- Active: **0.7.2 engineering tables**.
- Sequence: baseline → parser/models RED→GREEN → table point normalization → engine evaluation → HTML/magic → acceptance/docs → release gate.
- Next roadmap milestone remains 0.7.3 derivation traces unless amended.

## Exact next step

- Ensure feature HEAD contains approved plan.
- Run complete baseline source suite and record exact result/SHA.
- Add `tests/test_table_parser.py` and observe expected RED before production parser/models changes.
- Do not bump package version until release closure.

## How to resume in a new conversation

Read this file first. EngCalc 0.7.1 is the validated baseline; user approved 0.7.2 engineering tables. Active branch is `feature/v0.7.2-engineering-tables`. Approved spec/plan govern implementation. Primary syntax is `table(M(x), x, 0, L, 21)`. No 0.7.2 production code or RED feature tests have been added. Next: attach plan if needed, baseline CI, Task 1 RED. Do not manually invoke Codex.