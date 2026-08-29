# EngCalc Current Project Context

_Last updated: 2026-08-29 — EngCalc 0.7.2 remains canonical on `main`; narrative text has been visually validated in real Colab; optional plot/envelope labels and roomier content spacing are implemented on a retained presentation-polish branch; characteristic-point label deconfliction is the next bounded graphics task after visual verification._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical branch: `main` at pre-feature checkpoint `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`.
- Released package/runtime version: **0.7.2**; keep that version throughout pre-release development.
- 0.7.2 authoritative distribution gate: Actions `33266879721`; source **454/454**, installed-wheel source-free **454/454**, repeated source **454/454**, external wheel smoke PASS.
- Retained narrative branch: **`feature/v0.8.0-narrative-text`**, not merged.
- Active bounded presentation branch: **`feature/v0.8.0-presentation-polish`**, created from the narrative branch, not merged.
- Piecewise planning branch: **`planning/v0.8.0-piecewise`**.
- Piecewise formal spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- Piecewise implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md`.
- 0.7.3 derivation traces remains retired as redundant.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Retain branches unless explicitly asked to delete them; do not merge without explicit user approval.

## Approved behavior

### Narrative text in `%%eng`

- Narrative prose uses triple double quotes: `"""Texto explicativo."""` or a multiline `""" ... """` block.
- Consecutive non-empty lines form one paragraph; a blank line creates a new paragraph.
- `#`, `##`, `###` inside narrative are literal text; outside narrative existing comment/heading semantics remain unchanged.
- Narrative is plain text, HTML-escaped, presentation-only and never mutates symbolic/numeric state.
- Empty, unterminated and trailing-content-invalid blocks produce explicit syntax errors.
- Narrative is a source-order display boundary among headings, MathJax calculations, tables and plots.
- Real Google Colab screenshots supplied by the user visually confirmed correct headings, narrative placement, `numeric(...)` formula → substitution → result, narrative after calculations, and plot ordering.
- Feature reference: `docs/narrative-text.md`.

### Optional `plot` / `envelope` title and axis labels

- `plot(...)` and `envelope(...)` accept optional `title="..."`, `xlabel="..."`, `ylabel="..."` presentation keywords.
- Every option is independent. Omitted options retain the **existing automatic presentation exactly as before**.
- Custom x/y labels are text stems only; EngCalc/Pint appends the evaluated unit automatically.
- Example: `xlabel="Longitud"` with metre x values renders `Longitud [m]`.
- Example: `ylabel="Momento"` with kN·m response values renders `Momento [kN·m]`.
- One existing parameter sweep may coexist with the presentation keywords; presentation metadata does not count as a sweep.
- At most one actual sweep remains allowed.
- Presentation keywords must be non-empty strings.
- No arbitrary Matplotlib keyword surface is exposed.
- Presentation metadata is removed from the AST call before mathematical evaluation and stored on `ParsedStatement`; the symbolic/numeric engine therefore never receives display strings.
- A dedicated presentation layer applies optional overrides after the existing `render_plot(...)` path. With no overrides it returns the original figure unchanged.
- Existing 201-point sampling, envelope mathematics, characteristic points, units, sign conventions and positive structural moment downward are unchanged.
- Feature reference: `docs/presentation-polish.md`.

### Roomier content transitions

- User-side Colab screenshots showed that equation-internal spacing was good but transitions among headings, prose, equations and plots were slightly compressed.
- Level-2 heading margin is now `0.60rem 0 0.34rem 0`.
- Level-3 heading margin is now `0.46rem 0 0.24rem 0`.
- Narrative outer margin is now `0.36rem 0 0.60rem 0`.
- Narrative paragraph spacing itself remains unchanged.
- MathJax calculation spacing is deliberately unchanged: normal equation-row separation and explicit blank-line separation remain governed by the existing renderer contract.

## Open issues / user feedback

- User prefers routine technical micro-decisions to be analyzed independently rather than requiring repeated approval prompts.
- User approved the optional graph-title/axis-label contract for both `plot` and `envelope`.
- User requested slightly more spacing between prose/titles and equations after inspecting real Colab output.
- Current `%%eng` parsing is line-oriented for ordinary statements, so long calls such as `plot(...)` / `envelope(...)` must currently remain on one physical line; multiline call support is a possible later ergonomics improvement.
- User provided a real multi-curve plot showing characteristic-point labels becoming crowded/overlapping around shared x-locations (notably many labels near the same endpoints/interior extrema). After title/axis and spacing verification is complete, the **next bounded graphics task is automatic characteristic-label deconfliction / placement**, preserving clear association with each series and avoiding naive fixed offsets.
- The current presentation-polish feature is implementation-complete and test-green but **not merged**.
- Final real-Colab visual verification of the new spacing and custom graph text is still pending.
- Piecewise implementation has **not started**; its design, spec and implementation plan are complete.

## Validation evidence

### Narrative feature inherited baseline

- Narrative authoritative validated SHA: `161bbaba36b93c3d7395790eb6e41284d36c231b`.
- Narrative Actions `33273242772`, job `99155402471`, Python 3.13.15: **464/464 passed**.
- Temporary narrative workflow was subsequently removed; only administrative cleanup/context changes followed the validated SHA.
- Real user Colab screenshots then confirmed narrative rendering visually. An initial user-side stale-module issue was diagnosed: Colab had loaded the old main parser, not the feature parser. Installing the validated SHA and clearing/reloading modules resolved it without a product-code fix.

### Presentation-polish baseline

- Branch `feature/v0.8.0-presentation-polish` created from retained narrative branch.
- Temporary CI baseline commit `f4df65267ac6962ae920035ecb5dee26cc2434a0`.
- Baseline Actions `33274953866`, job `99159934641`, Python 3.13.15: **464/464 passed**.

### Optional graph metadata RED → GREEN

- RED tests commit `721c930698c32502afb3854ecad57950340eb6fe`.
- RED Actions `33275115922`, job `99160359686`: **9 failed, 465 passed**. Failures were exactly the old parser treating all `plot/envelope` keywords as sweep parameters.
- Model metadata commit: `678dcecb167e021e989fe723b4eb396f8874e996`.
- Parser metadata extraction/validation commit: `4e22ca3d6e00c96538291aa167f0007e37f04f1d`.
- Dedicated plot-presentation renderer commit: `49d429f6def0b7789222d277922c6dcd065b769e`.
- `%%eng` integration commit: `ca86f6119394e0cd6ada64f5c015d0f989099563`.
- One intermediate run had one failing test because its fixture incorrectly put units (`kN`, `m`) inside a symbolic definition; the fixture was corrected to use the numerical Pint context. No production change was required for that issue.
- Corrected graph-contract SHA: `61ad61744c170de8c93ffa6ce85507748786543c`.
- Graph GREEN Actions `33275488306`, job `99161335289`: **474/474 passed**.

### Content spacing RED → GREEN

- Spacing RED tests commit `6232b4c64dbf948b87d6790726e29f740d043ada`.
- RED Actions `33275614985`, job `99161678398`: **3 failed, 474 passed**; failures were exactly the three old CSS margins observed as too tight in Colab.
- Spacing implementation commit `4ec0651bb06839a672328b721679e576b1fa29fc` changed only the heading/narrative margin constants in `magic.py`.
- First spacing GREEN attempt Actions `33275748939`, job `99162030623`: new spacing tests were green and **476 tests passed**, with one remaining failure in historical `test_visual_layout.py` because it still asserted the old literal heading margins.
- Historical visual contract updated in `3f83ffbb3478fdab9ca08d84e44e31735e44c7f1`; no product code changed in that corrective commit.
- Combined graph + spacing GREEN Actions `33275854386`, job `99162312312`, Python 3.13.15: **477/477 passed**.
- `test_visual_layout.py` continues to verify 8-point normal equation spacing and 16-point explicit blank-line spacing, confirming MathJax spacing was not altered.

### Documentation / final gate preparation

- Presentation reference added in commit `2f00d3955bb304c6345ac94ef30c3706c593b0c9`: `docs/presentation-polish.md`.
- This checkpoint records all feature behavior/evidence before the authoritative final full-suite gate.
- Package metadata and runtime version remain **0.7.2**.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE, distribution-validated, merged.
- **0.7.3 derivation traces:** RETIRED.
- **Narrative text blocks:** IMPLEMENTED + TEST-VALIDATED + REAL-COLAB VISUALLY VALIDATED on retained branch.
- **Presentation polish:** IMPLEMENTED; optional graph text + roomier content spacing are green on `feature/v0.8.0-presentation-polish`; final gate/cleanup and user visual check remain.
- **Next bounded graphics task after visual verification:** characteristic-point label deconfliction / automatic placement for multi-curve plots and envelopes.
- **0.8.0 Piecewise:** DESIGN + SPEC + IMPLEMENTATION PLAN COMPLETE; implementation not started.
- **0.8.1:** exact-first extrema, roots and intersections.
- **0.8.2:** exact envelopes and governing intervals.
- **0.8.3:** named response cases/combinations.
- **0.9.0:** vectors, matrices and linear systems.
- **0.10.0:** engineering verification system.
- **0.10.1:** verification collections/summaries.
- **1.0.0:** language/API stabilization and release engineering.

## Exact next step

1. Complete real-Colab visual verification of optional graph title/axis labels and roomier heading/narrative spacing using single-line `plot(...)` / `envelope(...)` calls.
2. Then address characteristic-point label deconfliction / automatic placement as the next bounded graphics task.
3. Run one fresh complete validation on the presentation-polish HEAD containing production, tests, documentation and checkpoint; require all **477 tests** green before cleanup/integration.
4. Only after that gate succeeds, remove `.github/workflows/presentation-polish-validation.yml` and compare validated SHA to cleanup HEAD.
5. Do not merge unless explicitly approved.
6. After integration approval, make the resulting presentation baseline the inherited baseline for Piecewise and start the approved 0.8.0 implementation plan.

## How to resume in a new conversation

Read this file first. Released `main` remains EngCalc 0.7.2 at checkpoint `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`. Narrative `"""..."""` blocks are implemented and real-Colab visually validated. The active retained branch `feature/v0.8.0-presentation-polish` adds optional `title/xlabel/ylabel` to `plot/envelope` while preserving automatic defaults and Pint units, plus modestly roomier heading/narrative margins; the combined suite is **477/477 GREEN** at `3f83ffbb3478fdab9ca08d84e44e31735e44c7f1`, with documentation/checkpoint commits following. Real-Colab title/spacing verification is pending; after that, characteristic-point label deconfliction is the next bounded graphics task. Piecewise remains planned but unimplemented. Never invoke Codex without explicit authorization and never merge without explicit user approval.
