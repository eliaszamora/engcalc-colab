# EngCalc Current Project Context

_Last updated: 2026-08-29 — EngCalc 0.7.2 Tasks 1–3 are GREEN; Task 4 HTML rendering and real `%%eng` integration is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Released baseline: **EngCalc 0.7.1** on canonical `main` at `eab4f9a5dac6c6a0962419ba5273cd9fc212a86e`.
- Active implementation branch: `feature/v0.7.2-engineering-tables`; planning branch retained.
- Package/runtime version remains **0.7.1** until release closure.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`.
- Approved plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.2-engineering-tables-implementation.md`.
- Implemented 0.7.2 scope so far: restricted table grammar/models, table-specific point normalization, and end-to-end engine evaluation returning `TableResult`.
- `main` has not been modified.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume Codex quota without explicit authorization.

## Approved behavior

- Preserve all 0.7.1 behavior, including multi-argument functions, generalized partial evaluation, scalar math, 201-point plot/envelope sampling and positive-moment-down convention.
- Primary 0.7.2 syntax: `table(M(x), x, 0, L, 21)`.
- Exact dimensionless zero may inherit a compatible dimensional peer endpoint; nonzero dimensionless endpoints may not.
- Unit-once explicit points: `table(M(x), x, [0, 1, 1.5, 2], m)`.
- Fully explicit compatible points: `table(M(x), x, [0*m, 50*cm, 1*m])`.
- Descending uniform ranges are valid; count is a dimensionless integer >= 2 and both endpoints are included.
- Multiple response columns preserve source order and must be dimensionally compatible in 0.7.2.
- Table evaluation uses the table variable as a local numeric override and does not mutate stored symbolic/numeric state.
- Constant responses, nested user functions, multi-argument user functions and supported scalar math work inside tables.
- Table output will render as native HTML inside `%%eng`; no pandas runtime dependency.
- Arbitrary list literals remain rejected outside the table-point whitelist and existing plot/envelope sweep whitelist.

## Open issues / user feedback

- No known 0.7.1 functional blocker.
- User explicitly approved 0.7.2 design and execution.
- No known functional blocker in Tasks 1–3 after the complete Task 3 source gate.
- Table HTML rendering and `%%eng` source-order integration are not implemented yet; that is Task 4.
- Initial 0.7.2 baseline CI run `33261787307` failed during collection only because the temporary workflow omitted IPython; corrected baseline `33261841291` established this was an environment issue, not a product regression.

## Validation evidence

### 0.7.1 release baseline

- Authoritative corrected release gate Actions `33259552699`: focused **77/77**, source **386/386**, installed-wheel source-free **386/386**, repeated source **386/386**.
- Artifact `9716898144`; digest `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`.

### 0.7.2 execution baseline

- Corrected baseline Actions `33261841291` on SHA `c3b979f22f47d7aecdc7e5fd49541530508eccf5`: **386/386 passed** in Python 3.13.15; runtime version verified as 0.7.1.

### Task 1 — restricted parser grammar and result models

- RED test commit: `102b91b0e93f1cf47670fe873944fc08d7ec19ec`.
- RED Actions `33261976864`: **12 failed, 28 passed**.
- Model product commit: `01788b38fdd06a0054d0c0d116882d5c0631cfb9`.
- Parser product commit: `cb1ccf0417ae20b31e7bbf59110f3e004bdc3c20`.
- Focused GREEN Actions `33262102226`: **40/40 passed**.
- Complete Task 1 gate Actions `33262151576`: focused **40/40**, complete source **402/402 passed**.

### Task 2 — table point/range normalization

- RED tests commit: `2a9ff3aaca0138d1fcf039ea9e540c1f96826b2f`.
- RED Actions `33262313647`: **21 failed, 34 passed**; all new failures were the intentionally missing `engcalc_colab.tables` implementation.
- Product commit: `7fe7528b701448aaf05991105191078ebe1a8621` (`src/engcalc_colab/tables.py`).
- Focused GREEN Actions `33262406298`: **55/55 passed**.
- Complete Task 2 gate Actions `33262681298` on SHA `a1a9a96acbe5b362c28c577b408b1c537c728dbb`: focused **55/55**, complete source **423/423 passed**.
- Task 2 temporary workflow was removed after validation.

### Task 3 — end-to-end engine table evaluation

- RED tests commit: `e5759ed21bd7573d1e1976a08c9797f5fd9623e2` (`tests/test_table_engine.py`).
- RED Actions `33262826998`: **12 failed, 39 passed**; failures were exactly missing engine dispatch/evaluation for `table(...)` while parser-only invalid-shape contracts remained green.
- Product commit: `0625a97656a6a7ffe2a4cfa692eda979c679fc1a` (`feat: evaluate engineering tables`). Compare against its parent shows the product commit modified only `src/engcalc_colab/engine.py` (+132 lines).
- Focused GREEN Actions `33262981704`: **51/51 passed**.
- Complete Task 3 gate Actions `33263067183` on SHA `326117a2190b5fe69ffce072686291f623652fbc`: focused **51/51**, complete source **436/436 passed**.
- Verified central engineering contract: with `M(x,q,L)=q*x*(L-x)/2`, `q=4*kN/m`, `L=5*m`, `table(...,21)` includes midpoint `x=2.5 m` with `M=12.5 kN*m`.
- Verified explicit points, unit-once syntax, mixed `m/cm`, compatible multi-response source order, constants, nested functions, scalar math, targeted unresolved-symbol errors, incompatible response rejection and local override/restoration of a pre-existing numeric `x`.
- Task 3 patch applicator/workflow and validation workflow were removed after validation; no product source change was made after the authoritative gate.

## Roadmap / active plan

- **0.7.1 complete and merged.**
- Active milestone: **0.7.2 engineering tables**.
- Task 0 baseline: complete.
- Task 1 parser/models: complete and fully regressed.
- Task 2 point/range normalization: complete and fully regressed.
- Task 3 engine evaluation: complete and fully regressed.
- Next: **Task 4 native HTML renderer + real `%%eng` integration** → Task 5 acceptance/docs → Task 6 release gate.
- Next roadmap milestone remains 0.7.3 derivation traces unless amended.

## Exact next step

- Start Task 4 with RED tests in `tests/test_table_render.py` and real-magic tests covering native HTML output, unit-bearing headers, row/source order, and coexistence with headings/equations/plots in one `%%eng` cell.
- Implement table rendering through the existing renderer/magic architecture without pandas and without changing plot rendering semantics.
- Run focused Task 4 tests, then the complete source suite before moving to acceptance/docs.
- Do not bump package version until release closure.

## How to resume in a new conversation

Read this file first. EngCalc 0.7.1 remains canonical `main`; 0.7.2 is isolated on `feature/v0.7.2-engineering-tables`. Tasks 1–3 are complete. Key gates: baseline `33261841291` = 386/386; Task 1 `33262151576` = 402/402; Task 2 `33262681298` = 423/423; Task 3 `33263067183` = focused 51/51 and complete source 436/436. Task 3 product commit is `0625a97656a6a7ffe2a4cfa692eda979c679fc1a`. Exact next work is Task 4 RED for native HTML table rendering and real `%%eng` source-order integration. Do not manually invoke Codex.
