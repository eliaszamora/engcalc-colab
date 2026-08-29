# EngCalc Current Project Context

_Last updated: 2026-08-29 — presentation polish is test-validated and real-Colab visually validated; characteristic-point label deconfliction is the next bounded graphics task._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released branch: `main`; package/runtime version remains **0.7.2** during pre-release work.
- EngCalc 0.7.2 distribution gate: source **454/454**, installed-wheel source-free **454/454**, repeated source **454/454**, external wheel smoke PASS.
- Retained feature branches include `feature/v0.8.0-narrative-text` and `feature/v0.8.0-presentation-polish`; neither is merged.
- Piecewise planning branch: `planning/v0.8.0-piecewise` with approved spec and implementation plan.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Retain branches unless explicitly asked to delete them; do not merge without explicit user approval.

## Approved behavior

### Narrative text

- `%%eng` accepts presentation-only narrative prose using `"""Texto"""` or multiline triple-double-quote blocks.
- Blank lines inside narrative create paragraphs; ordinary line breaks within a paragraph are joined naturally.
- Narrative is HTML-escaped and never mutates the symbolic/numeric engine.
- Real Colab screenshots visually validated narrative ordering with headings, equations, `numeric(...)`, and plots.

### Plot/envelope presentation metadata

- `plot(...)` and `envelope(...)` accept optional `title="..."`, `xlabel="..."`, `ylabel="..."`.
- Omitted options preserve the existing automatic title/axis labels exactly.
- Custom labels are stems; EngCalc/Pint appends evaluated units automatically.
- Presentation keywords are removed before mathematical evaluation, so display strings never enter the symbolic/numeric engine.
- Existing 201-point sampling, envelope mathematics, characteristic-point detection, sign conventions, and positive structural moment plotted downward are unchanged.
- Ordinary `%%eng` statements remain line-oriented; long `plot(...)` / `envelope(...)` calls currently must remain on one physical line.

### Roomier content transitions

- Level-2 heading margin: `0.60rem 0 0.34rem 0`.
- Level-3 heading margin: `0.46rem 0 0.24rem 0`.
- Narrative outer margin: `0.36rem 0 0.60rem 0`.
- MathJax equation-row spacing remains unchanged.

## Open issues / user feedback

- User prefers routine technical micro-decisions to be analyzed independently rather than requiring repeated approvals.
- A real multi-curve moment plot supplied by the user shows characteristic-point labels becoming crowded at shared/nearby x-locations, notably endpoints and interior extrema.
- **Next bounded task:** automatic characteristic-point label deconfliction/placement for plots and envelopes. Preserve every detected point, its series color/association, mathematical values, and sign conventions. Do not solve by merely applying one larger fixed offset.
- Multiline ordinary function-call parsing is a possible later ergonomics improvement, but is not part of the characteristic-label task.
- Piecewise implementation has not started.

## Validation evidence

### Narrative

- Authoritative narrative SHA: `161bbaba36b93c3d7395790eb6e41284d36c231b`.
- Actions `33273242772`, Python 3.13.15: **464/464 passed**.
- Real Google Colab screenshots subsequently validated the rendered narrative behavior.

### Presentation polish

- Branch baseline: **464/464 passed**.
- Optional graph metadata RED: **9 failed, 465 passed**; failures were exactly the old keyword-as-sweep behavior.
- Graph metadata GREEN: Actions `33275488306`: **474/474 passed**.
- Spacing RED: **3 failed, 474 passed**; failures were exactly the old CSS margins.
- Combined graph + spacing GREEN: Actions `33275854386`: **477/477 passed**.
- Final authoritative presentation-polish gate SHA: **`d6fd873e21d5a415a2787bf06fdeceaa1f013e41`**.
- Final Actions **`33278758205`**, job `99170178155`, Python 3.13.15: **477/477 passed**.
- Real Colab screenshots then confirmed:
  - the roomier title/text/equation spacing;
  - custom plot title `Diagrama de momento flector`;
  - custom ylabel with automatic unit `Momento [kN·m]`;
  - optional presentation metadata parsing;
  - automatic fallback plot retaining `M(x)`, `M(x) [kN·m]`, and `x [m]`;
  - positive structural moment remains plotted downward.
- Temporary presentation-polish workflow removed after the final gate in cleanup commit **`cd200abaf8c88013c92201997ff2bd57b33d4871`**.
- Package metadata/runtime version remains **0.7.2**.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE, distribution-validated, merged.
- **0.7.3 derivation traces:** RETIRED.
- **Narrative text:** IMPLEMENTED + TEST-VALIDATED + REAL-COLAB VISUALLY VALIDATED.
- **Presentation polish:** IMPLEMENTED + 477/477 FINAL GATE + REAL-COLAB VISUALLY VALIDATED; retained and not merged.
- **Next bounded graphics task:** characteristic-point label deconfliction / automatic placement.
- **0.8.0 Piecewise:** DESIGN + SPEC + IMPLEMENTATION PLAN COMPLETE; implementation not started.
- **0.8.1:** exact-first extrema, roots and intersections.
- **0.8.2:** exact envelopes and governing intervals.
- **0.8.3:** named response cases/combinations.
- **0.9.0:** vectors, matrices and linear systems.
- **0.10.0:** engineering verification system.
- **0.10.1:** verification collections/summaries.
- **1.0.0:** language/API stabilization and release engineering.

## Exact next step

1. Compare validated presentation SHA `d6fd873e...` to cleanup/checkpoint HEAD and confirm post-gate changes are administrative only.
2. Create a retained child feature branch for characteristic-point label deconfliction from the completed presentation-polish baseline.
3. Inspect current characteristic annotation placement and write focused RED tests that reproduce shared-endpoint and shared-extrema crowding.
4. Implement a deterministic automatic placement strategy without changing characteristic-point detection or engineering values.
5. Run focused tests, then the complete inherited suite.
6. Request real-Colab visual evidence on a dense multi-curve case before considering the graphics task complete.
7. Do not merge without explicit user approval.

## How to resume in a new conversation

Read this file first. Released `main` remains EngCalc 0.7.2. Narrative and presentation-polish features are retained, not merged, and the latter has an authoritative **477/477** final gate at `d6fd873e21d5a415a2787bf06fdeceaa1f013e41` plus real-Colab visual validation. Its temporary workflow was removed in `cd200abaf8c88013c92201997ff2bd57b33d4871`. The next task is bounded graphics work: automatically deconflict characteristic-point labels in multi-curve plots/envelopes while preserving the detected points, values, colors, units, and moment sign convention. Piecewise remains planned but unimplemented. Never invoke Codex without explicit authorization and never merge without explicit user approval.
