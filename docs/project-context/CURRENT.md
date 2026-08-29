# EngCalc Current Project Context

_Last updated: 2026-08-29 — presentation polish is closed and visually validated; characteristic-point label deconfliction is implementation-complete and machine-validated, with real-Colab visual QA still pending._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released branch: `main`; package/runtime version remains **0.7.2** throughout pre-release feature work.
- EngCalc 0.7.2 distribution gate: source **454/454**, installed-wheel source-free **454/454**, repeated source **454/454**, external wheel smoke PASS.
- Retained branches include `feature/v0.8.0-narrative-text`, `feature/v0.8.0-presentation-polish`, and active child branch **`feature/v0.8.0-characteristic-label-layout`**. None is merged.
- Piecewise planning branch: `planning/v0.8.0-piecewise` with approved spec and implementation plan; Piecewise production implementation has not started.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Retain branches unless explicitly asked to delete them; do not merge without explicit user approval.

## Approved behavior

### Narrative text

- `%%eng` accepts presentation-only prose using `"""Texto"""` or multiline triple-double-quote blocks.
- Blank lines inside narrative create paragraphs; ordinary line breaks within a paragraph join naturally.
- Narrative is HTML-escaped and never mutates symbolic/numeric state.
- Real Colab screenshots visually validated narrative ordering with headings, equations, `numeric(...)`, and plots.

### Plot/envelope presentation metadata

- `plot(...)` and `envelope(...)` accept optional `title="..."`, `xlabel="..."`, `ylabel="..."`.
- Omitted options preserve the existing automatic title/axis labels exactly.
- Custom labels are stems; EngCalc/Pint appends evaluated units automatically.
- Presentation strings are removed before mathematical evaluation.
- Existing 201-point sampling, envelope mathematics, characteristic-point detection, units, sign conventions, and positive structural moment plotted downward are unchanged.
- Ordinary `%%eng` statements remain line-oriented; long `plot(...)` / `envelope(...)` calls currently must remain on one physical line.

### Roomier content transitions

- Level-2 heading margin: `0.60rem 0 0.34rem 0`.
- Level-3 heading margin: `0.46rem 0 0.24rem 0`.
- Narrative outer margin: `0.36rem 0 0.60rem 0`.
- MathJax equation-row spacing remains unchanged.

### Dense characteristic-point label layout

- Multi-series `plot(...)` characteristic-point detection remains authoritative in the existing plotting layer; no characteristic point is added, removed, or numerically changed by the layout feature.
- A user-facing presentation pass reflows characteristic labels only for multi-series plots.
- Characteristic annotations are clustered by nearby display-space x position and handled as spatial groups.
- The existing collision-aware placement engine remains responsible for finding safe annotation slots around curves, axes, legend, and other labels.
- Within a dense x-cluster, those already-safe slots are reassigned deterministically so the vertical order of the labels matches the vertical order of their point anchors. This removes the previous visual zig-zag caused by series-order placement.
- Reflow preserves each label text, characteristic coordinate, series color association, units, plotted curves, legend, engineering values, and moment sign convention.
- The feature does not solve crowding by applying one larger fixed offset.
- Machine tests require dense labels to remain inside the axes and have zero pairwise label-box overlap after reflow.
- Envelope characteristic rendering is not mathematically changed by this bounded task; the new reflow currently targets multi-series `plot` annotations, which are the crowding case demonstrated by the user's real plot.

## Open issues / user feedback

- User prefers routine technical micro-decisions to be analyzed independently rather than requiring repeated approval prompts.
- Real multi-curve moment screenshot supplied by the user showed characteristic-point labels visually disordered at shared/nearby x-locations, notably around `x=0` and interior extrema near `x=2.5 m`.
- The characteristic-label implementation is machine-green but **real-Colab visual QA is still required** before considering the graphics task complete.
- If real-Colab output is still too dense despite being non-overlapping and spatially ordered, the next iteration should refine group spacing/column composition rather than change characteristic-point mathematics.
- Multiline ordinary function-call parsing remains a possible later ergonomics improvement, outside this label-layout task.
- Piecewise implementation has not started.

## Validation evidence

### Narrative

- Authoritative narrative SHA: `161bbaba36b93c3d7395790eb6e41284d36c231b`.
- Actions `33273242772`, Python 3.13.15: **464/464 passed**.
- Real Google Colab screenshots subsequently validated narrative rendering.

### Presentation polish

- Optional graph metadata RED: **9 failed, 465 passed**; graph metadata GREEN: **474/474 passed**.
- Spacing RED: **3 failed, 474 passed**; combined graph + spacing GREEN: **477/477 passed**.
- Authoritative presentation-polish gate SHA: `d6fd873e21d5a415a2787bf06fdeceaa1f013e41`.
- Actions `33278758205`, job `99170178155`, Python 3.13.15: **477/477 passed**.
- Real Colab screenshots confirmed custom graph title, custom axis text with automatic Pint units, automatic fallback labels, improved content spacing, and positive structural moment downward.
- Temporary presentation workflow removed only after validation; compare to cleanup/checkpoint showed administrative changes only.

### Characteristic-label branch baseline

- Child branch `feature/v0.8.0-characteristic-label-layout` created from cleaned presentation-polish checkpoint `4cfe13eec2162696d42dc4f88908a7b0dbd954c5`.
- Temporary CI baseline commit `1ccc28af317a4100715fe6893d4548b4a07ec776`.
- Baseline Actions `33279362172`, job `99171763044`, Python 3.13.15: **477/477 passed**.

### Characteristic-label RED → GREEN

- Dense six-series regression fixture reproduces two shared-x annotation clusters analogous to the user screenshot: six endpoint labels around `x=0` and six interior-extremum labels around `x≈2.5`.
- Initial RED commit `7c6163a45a08ff0e8f9ced5b9176edaf86943562`: Actions `33279455264`, job `99172009106`: **1 failed, 477 passed**. Only the new visual-order contract failed.
- User-facing-route RED commit `03471aa8adcd72a321e171794d8f2ec55bf36012`: Actions `33279680988`, job `99172601135`: **1 failed, 477 passed**.
- Initial reflow integration exposed a renderer-boundary regression: Actions `33279782244`, job `99172870570`: **2 failed, 476 passed** due `FigureCanvasBase` lacking `get_renderer()`. It was fixed by mounting a temporary `FigureCanvasAgg` only during reflow and restoring the original canvas.
- Renderer-boundary fix commit `cc8d8759c5e4f08447b159160582cacef8e0de54`: Actions `33279893520`, job `99173174035`: **1 failed, 477 passed**. All inherited behavior was green; only the new ordering contract still failed, proving sorted insertion order alone was insufficient.
- Deterministic safe-slot reassignment implemented in commit **`6acd86a3f55b317023daaef2f0e63e081ca7aa93`**. Existing safe slots are sorted spatially and reassigned to anchor-y-ordered labels within each dense x-cluster.
- Actions `33280004612`, job `99173461780`, Python 3.13.15: **478/478 passed**.
- Additional geometry-safety test commit **`6fb6df530a7c89a89433fc77f3d65d84838d928c`** requires every dense label to stay inside the axes and every pair of annotation boxes to have zero overlap.
- Actions **`33280104391`**, job **`99173717130`**, Python 3.13.15: **479/479 passed**.
- Temporary characteristic-label workflow remains active until real-Colab visual QA is complete so any visual refinement can be revalidated immediately.
- Package metadata/runtime version remains **0.7.2**.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE, distribution-validated, merged.
- **0.7.3 derivation traces:** RETIRED.
- **Narrative text:** IMPLEMENTED + TEST-VALIDATED + REAL-COLAB VISUALLY VALIDATED.
- **Presentation polish:** IMPLEMENTED + 477/477 FINAL GATE + REAL-COLAB VISUALLY VALIDATED; retained and not merged.
- **Characteristic-point label deconfliction:** IMPLEMENTED + 479/479 MACHINE GREEN; real-Colab visual QA pending.
- **0.8.0 Piecewise:** DESIGN + SPEC + IMPLEMENTATION PLAN COMPLETE; implementation not started.
- **0.8.1:** exact-first extrema, roots and intersections.
- **0.8.2:** exact envelopes and governing intervals.
- **0.8.3:** named response cases/combinations.
- **0.9.0:** vectors, matrices and linear systems.
- **0.10.0:** engineering verification system.
- **0.10.1:** verification collections/summaries.
- **1.0.0:** language/API stabilization and release engineering.

## Exact next step

1. Run one fresh complete validation on the current characteristic-label HEAD containing production, tests and this checkpoint; require **479/479** green.
2. Pin that validated SHA in a one-shot Colab installer that clears stale EngCalc modules and explicitly re-registers the fresh `%%eng` magic.
3. Ask the user to render the dense six-series moment fixture and send a screenshot.
4. Inspect spatial order at both shared-x groups, label-label overlap, axes containment, color/series association, title/axes, and positive-moment-down convention.
5. If visually satisfactory, close the bounded graphics task, remove the temporary workflow, verify post-gate administrative-only changes, and await explicit integration/merge decision.
6. If still visually too dense, refine presentation only and rerun focused + complete tests before another screenshot.
7. Do not merge without explicit user approval.

## How to resume in a new conversation

Read this file first. Released `main` remains EngCalc 0.7.2. Narrative and presentation polish are retained and real-Colab visually validated. The active branch `feature/v0.8.0-characteristic-label-layout` addresses the real six-curve annotation-order problem by reusing collision-safe slots and deterministically matching them to the vertical order of characteristic anchors. The implementation is machine-green at **479/479** on SHA `6fb6df530a7c89a89433fc77f3d65d84838d928c`, including explicit no-overlap and axes-containment tests; a fresh gate after this checkpoint and real-Colab screenshot are still required. The temporary CI workflow remains active until visual QA is complete. Piecewise remains planned but unimplemented. Never invoke Codex without explicit authorization and never merge without explicit user approval.
