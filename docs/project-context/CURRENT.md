# EngCalc Current Project Context

_Last updated: 2026-08-29 — EngCalc 0.7.2 approved; isolated feature-branch baseline validation is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Released baseline: **0.7.1**, canonical `main` baseline `eab4f9a5dac6c6a0962419ba5273cd9fc212a86e`.
- Active branch: `feature/v0.7.2-engineering-tables`; planning branch retained.
- Version remains 0.7.1 until release closure.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`.
- Approved plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.2-engineering-tables-implementation.md`.
- No 0.7.2 production code or feature tests have been introduced.
- Do not manually invoke Codex / `@codex review` / Codex Cloud without explicit authorization.

## Approved behavior

- Preserve 0.7.1 behavior.
- Primary syntax: `table(M(x), x, 0, L, 21)`.
- Exact dimensionless zero may inherit a compatible dimensional peer endpoint; nonzero dimensionless values may not.
- Unit-once explicit points: `table(M(x), x, [0, 1, 1.5, 2], m)`.
- Fully explicit compatible points: `table(M(x), x, [0*m, 50*cm, 1*m])`.
- Descending ranges valid; count dimensionless integer >=2; endpoints included.
- Multiple responses remain dimensionally compatible in 0.7.2 and preserve source order.
- Tables do not mutate state and render as native HTML in `%%eng`, with no pandas.
- General Python list syntax remains rejected.

## Open issues / user feedback

- No known 0.7.1 blocker.
- User explicitly approved 0.7.2.
- Feature baseline source suite has not yet been rerun in this execution branch.

## Validation evidence

- 0.7.1 authoritative Actions `33259552699`: 77 focused / 386 source / 386 installed-wheel / 386 repeated.
- Artifact `9716898144`, digest `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`.
- Planning spec commit `d5ad296325157cceee088d704849f9073e3a0ec8`; planning plan commit `31e2e09f65dd42b6a7343402d484a074da16c87e`.
- Feature spec commit `ed19f6013baa8c8ad78d652e45631d9dec98bb6d`.
- Plan content blob is `379a9cc62cd3972852205896311033141ba20f67`; prepared attachment commits exist but feature HEAD must be verified to contain the path before CI.
- No 0.7.2 RED/GREEN evidence yet.

## Roadmap / active plan

- 0.7.1 complete and merged.
- Active: 0.7.2 engineering tables.
- Sequence: baseline → parser/models RED→GREEN → normalization → engine → HTML/magic → acceptance/docs → release gate.

## Exact next step

- Verify/persist approved plan path on feature HEAD.
- Run full baseline source suite and record exact SHA/count.
- Add `tests/test_table_parser.py` and observe RED before modifying parser/models.

## How to resume in a new conversation

Read this file first. 0.7.1 is the validated baseline; 0.7.2 is approved and isolated on `feature/v0.7.2-engineering-tables`. Governing spec/plan paths are above. No production/table-test implementation has begun. Next: verify plan on HEAD, baseline CI, then Task 1 RED. Do not invoke Codex without explicit authorization.