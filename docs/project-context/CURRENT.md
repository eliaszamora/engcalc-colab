# EngCalc Current Project Context

_Last updated: 2026-08-29 — EngCalc 0.7.2 Task 1 parser/result-model contracts are GREEN and Task 2 point normalization is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Released baseline: **EngCalc 0.7.1** on canonical `main` at `eab4f9a5dac6c6a0962419ba5273cd9fc212a86e`.
- Active implementation branch: `feature/v0.7.2-engineering-tables`; planning branch retained.
- Package/runtime version remains **0.7.1** until release closure.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`.
- Approved plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.2-engineering-tables-implementation.md`.
- Task 1 production changes are limited to restricted table grammar in `parser.py` and immutable `TableColumn` / `TableResult` in `models.py`.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume Codex quota without explicit authorization.

## Approved behavior

- Preserve all 0.7.1 behavior, including multi-argument functions, generalized partial evaluation, scalar math, 201-point plot/envelope sampling and positive-moment-down convention.
- Primary 0.7.2 syntax: `table(M(x), x, 0, L, 21)`.
- Exact dimensionless zero may inherit a compatible dimensional peer endpoint; nonzero dimensionless endpoints may not.
- Unit-once explicit points: `table(M(x), x, [0, 1, 1.5, 2], m)`.
- Fully explicit compatible points: `table(M(x), x, [0*m, 50*cm, 1*m])`.
- Descending uniform ranges are valid; count is dimensionless integer >= 2 and both endpoints are included.
- Multiple response columns preserve source order and must be dimensionally compatible in 0.7.2.
- Table evaluation must not mutate stored symbolic/numeric state.
- Table output will render as native HTML inside `%%eng`; no pandas runtime dependency.
- Arbitrary list literals remain rejected outside the table-point whitelist and existing plot/envelope sweep whitelist.

## Open issues / user feedback

- No known 0.7.1 functional blocker.
- User explicitly approved 0.7.2 design and execution.
- Initial 0.7.2 baseline CI run `33261787307` failed during test collection only because the temporary workflow omitted IPython; this was an environment error, not a product regression. The corrected workflow matched the validated 0.7.1 environment and passed.
- Task 2 point/range normalization has not yet been implemented.

## Validation evidence

### 0.7.1 release baseline

- Authoritative corrected release gate Actions `33259552699`: focused **77/77**, source **386/386**, installed-wheel source-free **386/386**, repeated source **386/386**.
- Artifact `9716898144`; digest `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`.

### 0.7.2 execution baseline

- Corrected baseline Actions `33261841291` on SHA `c3b979f22f47d7aecdc7e5fd49541530508eccf5`: **386/386 passed** in Python 3.13.15; runtime version verified as 0.7.1.
- Temporary baseline workflow was removed after validation.

### Task 1 — restricted parser grammar and result models

- RED test commit: `102b91b0e93f1cf47670fe873944fc08d7ec19ec`.
- RED Actions `33261976864`: **12 failed, 28 passed**; failures exactly covered missing table list whitelist, reserved name/shape validation and missing table models.
- Model product commit: `01788b38fdd06a0054d0c0d116882d5c0631cfb9`.
- Parser product commit: `cb1ccf0417ae20b31e7bbf59110f3e004bdc3c20`.
- Focused GREEN Actions `33262102226`: **40/40 passed**.
- Complete Task 1 gate Actions `33262151576` on SHA `0cd9009daf8bdee0552e82c45186550bc82f5cfa`: focused **40/40**, complete source **402/402 passed**.

## Roadmap / active plan

- **0.7.1 complete and merged.**
- Active milestone: **0.7.2 engineering tables**.
- Task 0 baseline: complete.
- Task 1 parser/models: complete and fully regressed.
- Next: Task 2 point/range normalization → Task 3 engine evaluation → Task 4 HTML/magic → Task 5 acceptance/docs → Task 6 release gate.
- Next roadmap milestone remains 0.7.3 derivation traces unless amended.

## Exact next step

- Remove/replace the temporary Task 1 workflow so it does not rerun unnecessarily.
- Add `tests/test_table_points.py` first and observe RED for table-specific point/range normalization before creating `src/engcalc_colab/tables.py`.
- Preserve existing `NumericContext.normalize_plot_bounds` semantics; descending-table support belongs only in the new table helper.
- Do not bump package version until release closure.

## How to resume in a new conversation

Read this file first. EngCalc 0.7.1 is the validated baseline. User approved 0.7.2. Active branch is `feature/v0.7.2-engineering-tables`; approved spec/plan are persisted. Baseline Actions `33261841291` passed 386/386. Task 1 is complete: RED `33261976864` (12 failed/28 passed), focused GREEN `33262102226` (40/40), full gate `33262151576` (402/402). Next mandatory step is Task 2 RED in `tests/test_table_points.py`, then minimal `tables.py` implementation. Do not manually invoke Codex.