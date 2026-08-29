# EngCalc Current Project Context

_Last updated: 2026-08-29 — presentation polish is visually validated; first and second characteristic-label layouts were rejected by real-Colab visual QA; robust-clearance aligned rails are now 481/481 machine green and await a new screenshot._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released branch: `main`; package/runtime version remains **0.7.2** during pre-release work.
- EngCalc 0.7.2 release/distribution baseline remains fully validated.
- Retained feature branches include `feature/v0.8.0-narrative-text`, `feature/v0.8.0-presentation-polish`, and active child branch **`feature/v0.8.0-characteristic-label-layout`**. None is merged.
- Piecewise planning branch: `planning/v0.8.0-piecewise`, with approved spec and implementation plan; Piecewise production implementation has not started.
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
- Omitted options preserve automatic title/axis labels exactly.
- Custom labels are stems; EngCalc/Pint appends evaluated units automatically.
- Existing sampling, envelope mathematics, characteristic-point detection, units, sign conventions, and positive structural moment plotted downward remain unchanged.
- Ordinary `%%eng` statements remain line-oriented; long calls currently must stay on one physical line.

### Roomier content transitions

- Level-2 heading margin: `0.60rem 0 0.34rem 0`.
- Level-3 heading margin: `0.46rem 0 0.24rem 0`.
- Narrative outer margin: `0.36rem 0 0.60rem 0`.
- MathJax equation-row spacing remains unchanged.

### Dense characteristic-point label layout

- Mathematical characteristic-point detection remains authoritative in the plotting layer; layout never changes coordinates, values, colors, units, curves, legend, or sign convention.
- Multi-series characteristic annotations are clustered by nearby display-space x position.
- Real-Colab QA proved that merely avoiding overlap and preserving anchor-y order is **not sufficient**: the first output formed alternating/scattered left-right clouds.
- A second real-Colab pass with aligned rails improved horizontal order but still showed labels visually touching/overlapping vertically, especially around `x≈2.5`.
- Required presentation contract: each dense shared-x group uses **one aligned label rail/column**, with one common left or right text edge chosen automatically from available axes space.
- Within the rail, vertical label order follows vertical anchor order.
- Consecutive label boxes in a dense rail must retain a robust visual clearance, not merely zero geometric overlap.
- Current implementation uses a 12 px internal vertical rail gap; machine tests require at least 10 px free clearance between adjacent label boxes.
- Labels must remain inside the axes and pairwise non-overlapping.
- The feature must not change characteristic-point mathematics or solve crowding with one generic fixed offset applied to every point.

## Open issues / user feedback

- User explicitly rejected the first real-Colab characteristic-label result as visually unordered. Do not describe that output as approved.
- User also rejected the second aligned-rail screenshot as still needing improvement because labels visibly overlapped/touched in the dense interior cluster.
- A third real-Colab visual QA pass is required for the robust-clearance refinement before closing this graphics task.
- Multiline ordinary function-call parsing remains a possible later ergonomics improvement, outside this label-layout task.
- Piecewise implementation has not started.

## Validation evidence

### Narrative / presentation polish

- Narrative authoritative SHA `161bbaba36b93c3d7395790eb6e41284d36c231b`: **464/464 passed** and real-Colab visually validated.
- Presentation-polish authoritative SHA `d6fd873e21d5a415a2787bf06fdeceaa1f013e41`: **477/477 passed** and real-Colab visually validated for spacing, custom `title/xlabel/ylabel`, automatic units/fallback labels, and positive moment downward.

### Characteristic-label work

- Child branch baseline: **477/477 passed**.
- Initial ordering RED: **1 failed, 477 passed**.
- Intermediate implementation reached **479/479 passed**, including tests for vertical anchor order, axes containment, and zero pairwise label-box overlap.
- First real-Colab screenshot **failed visual QA**: non-overlapping labels were still visibly scattered into multiple horizontal positions.
- Aligned-rail RED commit `a6e18667e9d0ebb451b42b98f6f169ccda331546`: **1 failed, 479 passed**; failure measured ~81–95 px horizontal edge spread.
- Aligned-rail implementation commit `15bf024fd03dbd29fc1f96f0c6bc98c72965f435`: Actions `33280670988`, job `99175192258`, Python 3.13.15: **480/480 passed**.
- Second real-Colab screenshot improved horizontal ordering but **failed visual QA** because adjacent rail labels were still too close and visibly overlapped/touched.
- Robust-clearance RED commit **`60d83b2737eb0058404e5f04f079dfee6ac9a60e`**: Actions `33280875717`, job `99175714568`: **1 failed, 480 passed**. The new test measured only 5 px clearance between most adjacent rail boxes versus a required 10 px.
- Robust-clearance implementation commit **`af3c4eb9b3eac086924cbbbaf8c14ed17e1738d7`** increases the internal rail gap to 12 px.
- Actions **`33281000238`**, job **`99176037827`**, Python 3.13.15: **481/481 passed**.
- Temporary characteristic-label workflow remains active until the new real-Colab visual QA is accepted.
- Package/runtime version remains **0.7.2**.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE, distribution-validated, merged.
- **0.7.3 derivation traces:** RETIRED.
- **Narrative text:** IMPLEMENTED + MACHINE GREEN + REAL-COLAB VISUALLY VALIDATED.
- **Presentation polish:** IMPLEMENTED + 477/477 + REAL-COLAB VISUALLY VALIDATED; retained and not merged.
- **Characteristic-point label deconfliction:** robust-clearance aligned-rail refinement **481/481 MACHINE GREEN**; third real-Colab visual QA pending.
- **0.8.0 Piecewise:** DESIGN + SPEC + IMPLEMENTATION PLAN COMPLETE; implementation not started.
- **0.8.1:** exact-first extrema, roots and intersections.
- **0.8.2:** exact envelopes and governing intervals.
- **0.8.3:** named response cases/combinations.
- **0.9.0:** vectors, matrices and linear systems.
- **0.10.0:** engineering verification system.
- **0.10.1:** verification collections/summaries.
- **1.0.0:** language/API stabilization and release engineering.

## Exact next step

1. Use SHA `af3c4eb9b3eac086924cbbbaf8c14ed17e1738d7` for a one-shot Colab installation/reload.
2. Render the same dense six-series moment fixture used in the prior screenshots.
3. Require visually that each shared-x group remains one aligned column/rail and that adjacent labels have clearly visible whitespace between them.
4. Also verify axes containment, color association, legend, axes/title, and positive-moment-down convention.
5. If visually accepted, run one fresh final full gate on the checkpointed HEAD, remove the temporary workflow, and verify cleanup changes are administrative only.
6. If still visually unsatisfactory, refine presentation only and rerun focused + complete tests before another screenshot.
7. Do not merge without explicit user approval.

## How to resume in a new conversation

Read this file first. Released `main` remains EngCalc 0.7.2. Narrative and presentation polish are retained and visually validated. The first characteristic-label attempt was rejected for scattered labels; the second aligned-rail attempt was rejected because labels were still too tightly packed in Colab. The active branch now contains robust-clearance rails at SHA `af3c4eb9b3eac086924cbbbaf8c14ed17e1738d7`, machine-green **481/481**. The immediate next action is a third real-Colab visual QA using the same dense six-series fixture. Piecewise remains planned but unimplemented. Never invoke Codex without explicit authorization and never merge without explicit user approval.