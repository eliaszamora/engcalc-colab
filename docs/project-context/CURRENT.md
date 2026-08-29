# EngCalc Current Project Context

_Last updated: 2026-08-29 — narrative/presentation polish are visually validated; three in-axes dense-label iterations were rejected by real-Colab QA; dense clusters now use external callout rails with leader lines and 482/482 machine-green coverage, pending new visual QA._

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

### Dense characteristic-point callout layout

- Mathematical characteristic-point detection remains authoritative in the plotting layer; presentation layout never changes coordinates, values, colors, units, curves, legend, or sign convention.
- Multi-series characteristic annotations are clustered by nearby display-space x position.
- Real-Colab QA rejected three variants that attempted to keep dense labels inside the axes: initial collision avoidance produced scattered zig-zags, aligned in-axes rails still looked disordered, and increasing vertical clearance still left labels colliding visually with curves/other labels.
- **Current strategy:** clusters with fewer than 3 labels retain the existing inline annotation layout exactly; clusters with **3 or more** labels move to external callout rails.
- Each dense cluster chooses the nearest horizontal side of the data axes (left for anchors in the left half, right for anchors in the right half).
- The figure reserves `1.65 in` of external side space on each side actually used while preserving the axes' original physical width/height.
- Dense labels are placed on one aligned external rail per used side and ordered by the display-space y coordinate of their anchors.
- Consecutive dense callout text boxes retain a 12 px internal vertical gap; tests require at least 10 px free clearance.
- Every external dense callout has a thin same-color leader line back to its original characteristic point.
- External callout text remains inside the figure canvas and outside the data axes; sparse 1–2 label clusters remain inline and do not enlarge the figure.
- This layout is presentation-only and does not alter engineering values or extrema detection.

## Open issues / user feedback

- User explicitly rejected all prior in-axes dense-label outputs as visually unsatisfactory; do not describe those as approved.
- Latest rejected screenshot showed that even a 12 px in-axes rail gap did not solve the fundamental competition between six labels and the curves around `x≈2.5`.
- User approved changing strategy rather than continuing pixel-offset tuning: dense clusters should use reserved external callout space with leader lines.
- Real-Colab visual QA of the new external-callout strategy is still required before closing this graphics task.
- Multiline ordinary function-call parsing remains a possible later ergonomics improvement, outside this label-layout task.
- Piecewise implementation has not started.

## Validation evidence

### Narrative / presentation polish

- Narrative authoritative SHA `161bbaba36b93c3d7395790eb6e41284d36c231b`: **464/464 passed** and real-Colab visually validated.
- Presentation-polish authoritative SHA `d6fd873e21d5a415a2787bf06fdeceaa1f013e41`: **477/477 passed** and real-Colab visually validated for spacing, custom `title/xlabel/ylabel`, automatic units/fallback labels, and positive moment downward.

### Characteristic-label history

- Child branch baseline: **477/477 passed**.
- Initial ordering/collision iterations reached **479/479**, **480/480**, then **481/481**, but each corresponding real-Colab output remained visually unacceptable for dense clusters.
- Robust-clearance in-axes implementation SHA `af3c4eb9b3eac086924cbbbaf8c14ed17e1738d7`: **481/481 passed**, but real-Colab screenshot still showed overlap/curve competition; this strategy is superseded.

### External callout rail RED → GREEN

- New callout-contract test commit `8ba571885a78b6f9bc4695529bfa24e59a52b166`; refined text-box measurement commit `61f3544f52e773d34ab02f75566eb35f04a3ce3f`.
- Refined RED Actions `33281581420`, job `99177529004`, Python 3.13.15: **2 failed, 480 passed**. The two expected failures were: no leader arrows existed and the figure still remained at the default 6.4 in width instead of reserving external side space.
- External-callout implementation commit **`70c303d9c73d5027d0940778229fbdeb5a58a9fc`**.
- GREEN Actions **`33281734799`**, job **`99177923324`**, Python 3.13.15: **482/482 passed** in 97.09 s.
- Coverage now verifies: dense anchor-y order, aligned external rails, leader-line presence, dense text outside axes but inside the figure, robust vertical clearance, no pairwise text overlap, figure side-space reservation, and preservation of the existing inline layout for sparse two-label clusters.
- Temporary characteristic-label workflow remains active until real-Colab visual QA is accepted.
- Package/runtime version remains **0.7.2**.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE, distribution-validated, merged.
- **0.7.3 derivation traces:** RETIRED.
- **Narrative text:** IMPLEMENTED + MACHINE GREEN + REAL-COLAB VISUALLY VALIDATED.
- **Presentation polish:** IMPLEMENTED + 477/477 + REAL-COLAB VISUALLY VALIDATED; retained and not merged.
- **Characteristic-point label deconfliction:** external callout rails **482/482 MACHINE GREEN**; real-Colab visual QA pending.
- **0.8.0 Piecewise:** DESIGN + SPEC + IMPLEMENTATION PLAN COMPLETE; implementation not started.
- **0.8.1:** exact-first extrema, roots and intersections.
- **0.8.2:** exact envelopes and governing intervals.
- **0.8.3:** named response cases/combinations.
- **0.9.0:** vectors, matrices and linear systems.
- **0.10.0:** engineering verification system.
- **0.10.1:** verification collections/summaries.
- **1.0.0:** language/API stabilization and release engineering.

## Exact next step

1. Run one fresh complete 482-test gate on the checkpointed HEAD containing production, tests and this context file.
2. Pin that validated SHA in a one-shot Colab installer which clears stale EngCalc modules and re-registers the fresh `%%eng` magic.
3. Render the same six-series dense moment fixture used in every prior visual comparison.
4. Require visually: dense labels outside the data axes, no text overlap, readable leader lines, clear point-to-label association, no interference with title/axes/legend, and preservation of positive-moment-down convention.
5. If accepted, remove the temporary workflow, verify administrative-only cleanup, and await explicit integration/merge decision.
6. If still visually unsatisfactory, refine only the external callout presentation and rerun focused + complete tests before another screenshot.
7. Do not merge without explicit user approval.

## How to resume in a new conversation

Read this file first. Released `main` remains EngCalc 0.7.2. Narrative and presentation polish are retained and visually validated. Multiple in-axes dense-label approaches were machine-green but rejected by real-Colab QA. The user approved a structural change: clusters of 3+ characteristic labels now move outside the data axes to aligned side rails with same-color leader lines and reserved figure space; clusters of 1–2 labels remain inline. Production SHA `70c303d9c73d5027d0940778229fbdeb5a58a9fc` is GREEN **482/482**. A fresh gate on the checkpointed HEAD and real-Colab screenshot are the immediate next actions. Piecewise remains planned but unimplemented. Never invoke Codex without explicit authorization and never merge without explicit user approval.