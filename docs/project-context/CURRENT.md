# EngCalc Current Project Context

_Last updated: 2026-08-29 — EngCalc 0.7.2 Tasks 1–4 are GREEN; Task 5 acceptance and documentation is next._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Released baseline: **EngCalc 0.7.1** on canonical `main` at `eab4f9a5dac6c6a0962419ba5273cd9fc212a86e`.
- Active implementation branch: `feature/v0.7.2-engineering-tables`; planning branch retained.
- Package/runtime version remains **0.7.1** until release closure.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`.
- Approved plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.2-engineering-tables-implementation.md`.
- Implemented 0.7.2 scope so far: restricted table grammar/models, table-specific point normalization, end-to-end engine evaluation returning `TableResult`, native HTML rendering, and real `%%eng` source-order integration.
- Table rendering has no pandas runtime dependency and uses scoped `.engcalc-table` HTML/CSS.
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
- Table output renders as native HTML inside `%%eng`; variable is the first column and responses follow source order.
- Units appear once in table headers, not in every body cell; dimensionless headers omit a unit suffix.
- Table numeric cells obey the same `RenderSettings.precision` and `RenderSettings.zero_tolerance` configuration used elsewhere in `%%eng`.
- User-derived table labels are HTML-escaped before display.
- A table is a display boundary in `%%eng`: pending equations flush before it, the table displays as `HTML`, and later equations resume in a new MathJax group. Headings keep source order around tables.
- Arbitrary list literals remain rejected outside the table-point whitelist and existing plot/envelope sweep whitelist.

## Open issues / user feedback

- No known 0.7.1 functional blocker.
- User explicitly approved 0.7.2 design and execution.
- No known functional blocker in Tasks 1–4 after the complete Task 4 source gate.
- Task 5 acceptance/documentation and Task 6 release closure remain pending.
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

### Task 4 — native HTML rendering and real `%%eng` integration

- Table renderer tests were introduced in `tests/test_table_rendering.py`; real-magic source-order contracts were added to `tests/test_magic.py`.
- Final RED head before validation workflow: `ec95f7446038bd1080f2fa8a832fd6b65308e1ee`.
- RED Actions `33263389497`: **7 failed, 37 passed**. Five failures were the deliberately missing `render_table`; two failures showed `TableResult` incorrectly falling through to MathJax rendering.
- Product commit: `55fffe0dbcc280fb2a5685b48921e062be923f9f` (`feat: render engineering tables in eng magic`). Production changes are limited to `src/engcalc_colab/renderer.py` and `src/engcalc_colab/magic.py`.
- Focused GREEN Actions `33263532658`: **44/44 passed**.
- Authoritative complete Task 4 gate Actions `33263583872` on SHA `34be4158147e16633dc5f263c29d5df3df84f576`: focused **44/44**, complete source **443/443 passed** in Python 3.13.15.
- Verified headers carry units once (`x [m]`, response `[kN·m]`), body cells contain magnitudes only, dimensionless headers omit suffixes, precision/zero-tolerance settings are respected, labels are HTML-escaped, and row/response source order is preserved.
- Verified `%%eng` display ordering as equation → table → equation = `[Math, HTML, Math]`; heading/equation/table/heading/equation order is also preserved.
- Task 4 product applicator/apply workflow were removed before the authoritative gate. The remaining Task 4 validation workflow was removed immediately after the successful gate; no product source or test changed after the authoritative gate.

## Roadmap / active plan

- **0.7.1 complete and merged.**
- Active milestone: **0.7.2 engineering tables**.
- Task 0 baseline: complete.
- Task 1 parser/models: complete and fully regressed.
- Task 2 point/range normalization: complete and fully regressed.
- Task 3 engine evaluation: complete and fully regressed.
- Task 4 native HTML renderer + real `%%eng` integration: complete and fully regressed.
- Next: **Task 5 acceptance + documentation** → Task 6 release gate.
- Next roadmap milestone remains 0.7.3 derivation traces unless amended.

## Exact next step

- Start Task 5 by adding acceptance coverage for complete engineer-facing examples, including primary uniform syntax, unit-once explicit syntax, fully explicit mixed-unit points, descending ranges, multi-response output and coexistence with existing equations/plots.
- Update README/user documentation only after the acceptance examples are executable and GREEN.
- Run Task 5 focused acceptance/docs checks and the complete source suite before release closure.
- Do not bump package/runtime version until Task 6 release closure.

## How to resume in a new conversation

Read this file first. EngCalc 0.7.1 remains canonical `main`; 0.7.2 is isolated on `feature/v0.7.2-engineering-tables`. Tasks 1–4 are complete. Key gates: baseline `33261841291` = 386/386; Task 1 `33262151576` = 402/402; Task 2 `33262681298` = 423/423; Task 3 `33263067183` = 436/436; Task 4 `33263583872` = focused 44/44 and complete source 443/443. Task 4 product commit is `55fffe0dbcc280fb2a5685b48921e062be923f9f`; authoritative Task 4 validated SHA is `34be4158147e16633dc5f263c29d5df3df84f576`. Exact next work is Task 5 acceptance and documentation. Do not manually invoke Codex.
