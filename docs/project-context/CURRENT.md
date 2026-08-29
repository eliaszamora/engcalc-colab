# EngCalc Current Project Context

_Last updated: 2026-08-29 after the user explicitly approved the EngCalc 0.7.2 engineering-tables design and execution moved to the isolated feature branch._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical product branch: `main`.
- Canonical released baseline: **EngCalc 0.7.1**.
- `main` baseline SHA at 0.7.2 branch creation: `eab4f9a5dac6c6a0962419ba5273cd9fc212a86e`.
- Active implementation branch: `feature/v0.7.2-engineering-tables`, created from that `main` baseline.
- Planning branch retained: `planning/v0.7.2-engineering-tables`.
- Package/runtime version remains **0.7.1** until the release-closing task.
- Approved 0.7.2 spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`.
- Approved 0.7.2 implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.2-engineering-tables-implementation.md`.
- No 0.7.2 production code or tests have been implemented yet at this checkpoint.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume the user's Codex quota without explicit authorization.

## Approved behavior

### Existing 0.7.1 baseline

- User functions support one or more ordered positional parameters with exact arity.
- Generalized partial numeric evaluation substitutes known values while preserving only genuinely unresolved caller-side symbols.
- Scalar engineering math, Pint-backed numeric values, plotting and envelopes remain unchanged.
- Plot/envelope rendering remains 201-point with positive structural moment plotted downward.

### EngCalc 0.7.2 engineering tables

- The user explicitly approved the written 0.7.2 design.
- Primary/recommended form is automatic discretization: `table(M(x), x, 0, L, 21)`.
- If `L` is dimensional, exact dimensionless zero may inherit the compatible endpoint unit; users are not forced to write `0*m`.
- Nonzero dimensionless endpoints never silently inherit a dimensional unit.
- Explicit point magnitudes may declare their unit once: `table(M(x), x, [0, 1, 1.5, 2], m)`.
- Fully explicit compatible quantities remain supported: `table(M(x), x, [0*m, 50*cm, 1*m])`.
- Descending uniform ranges are valid and preserve requested order.
- Uniform `count` must be a dimensionless integer >= 2 and includes both endpoints.
- Multiple responses preserve source-column order and must be dimensionally compatible in 0.7.2.
- Table evaluation is local and must not mutate stored symbolic/numeric state, including a pre-existing value for the table variable.
- Table output renders natively as HTML inside `%%eng`; no pandas runtime dependency is added.
- Arbitrary list literals remain invalid outside the table-point whitelist and existing plot/envelope sweep whitelist.
- CSV/Excel export, interactive spreadsheets, Cartesian table sweeps, cross-dimension tables, piecewise expressions and derivation traces are out of scope for 0.7.2.

## Open issues / user feedback

- No known functional blocker remains for 0.7.1.
- 0.7.2 design is approved; implementation has begun only at branch/setup level.
- The implementation plan deliberately isolates table-specific unit/grid mechanics in `src/engcalc_colab/tables.py` so descending table ranges do not alter existing `plot(...)` bound semantics.
- Baseline source suite still needs to be rerun on the new feature branch before the first RED test is introduced.

## Validation evidence

### Authoritative 0.7.1 release evidence

- Corrected distribution gate: GitHub Actions `33259552699` — success.
- Validated SHA: `2332bd29e571a360cc47a29562e09b5828a3d2cb`.
- Focused corrected release contracts: **77/77 passed**.
- Complete source suite: **386/386 passed**.
- Complete source-free suite against installed wheel: **386/386 passed**.
- Repeated complete source suite: **386/386 passed**.
- Wheel artifact ID: `9716898144`.
- Wheel digest: `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`.

### 0.7.2 planning / execution evidence

- User explicitly approved the 0.7.2 design on 2026-08-29.
- Planning spec commit: `d5ad296325157cceee088d704849f9073e3a0ec8`.
- Planning implementation-plan commit: `31e2e09f65dd42b6a7343402d484a074da16c87e`.
- Feature branch `feature/v0.7.2-engineering-tables` was created from `main` before production work.
- Approved spec and plan are being persisted on the feature branch before baseline validation.
- No 0.7.2 production test result is claimed yet.

## Roadmap / active plan

- **0.7.1 is complete and merged.**
- Active milestone: **0.7.2 — engineering tables / evaluation by points**.
- Approved design and implementation plan are now the governing documents for the feature branch.
- Execution order: baseline validation → Task 1 parser/models RED→GREEN → Task 2 point normalization → Task 3 engine evaluation → Task 4 HTML/magic → Task 5 acceptance/docs → Task 6 release gate.
- Existing roadmap continues to 0.7.3 derivation traces after 0.7.2 unless later amended.

## Exact next step

- Finish persisting the approved plan on `feature/v0.7.2-engineering-tables`.
- Run the complete 0.7.1 source suite on the feature branch and record the actual green count/SHA.
- Only after that baseline is proven, create `tests/test_table_parser.py` as the first RED 0.7.2 production-contract test; do not modify parser/models production code until that RED failure is observed.
- Do not bump package version until the release-closing task.

## How to resume in a new conversation

Read this file first. EngCalc 0.7.1 remains the validated release baseline on `main` at `eab4f9a5dac6c6a0962419ba5273cd9fc212a86e`. The user explicitly approved EngCalc 0.7.2 engineering tables. Active implementation branch is `feature/v0.7.2-engineering-tables`; planning branch is retained. Governing documents are `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md` and `docs/superpowers/plans/2026-08-29-engcalc-v0.7.2-engineering-tables-implementation.md`. Primary syntax is `table(M(x), x, 0, L, 21)` with unit-once explicit points also supported. At this checkpoint, no production code or RED table tests have been added; the next mandatory step is feature-branch baseline validation before Task 1 RED. Do not manually invoke Codex without explicit authorization.