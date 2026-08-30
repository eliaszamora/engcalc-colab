# EngCalc Current Project Context

_Last updated: 2026-08-30 — dense characteristic-label task remains open; rejected bottom callout band is superseded by an approved compact summary-panel design. Written spec is persisted and self-reviewed; implementation planning waits for explicit user review of that written spec._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released branch: `main`; package/runtime version remains **0.7.2** during pre-release work.
- Active branch: **`feature/v0.8.0-characteristic-label-layout`**. Do not merge without explicit user approval.
- Current branch head after spec/context work is documentation-only; no production behavior has changed from the 482/482 machine-green bottom-band baseline.
- Dense-summary written spec: `docs/superpowers/specs/2026-08-30-engcalc-dense-characteristic-summary-design.md`.
- Retain existing feature/planning branches unless explicitly asked to delete them.
- Piecewise planning branch: `planning/v0.8.0-piecewise`; approved spec and implementation plan exist, production implementation has not started.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.

## Approved behavior

### Narrative text

- `%%eng` accepts presentation-only prose with `"""Texto"""` and multiline triple-double-quote blocks.
- Narrative is HTML-escaped, supports paragraph breaks, and never mutates symbolic/numeric state.
- Real-Colab QA validated narrative ordering with headings, equations, `numeric(...)`, and plots.

### Plot/envelope presentation metadata

- `plot(...)` and `envelope(...)` accept optional `title="..."`, `xlabel="..."`, `ylabel="..."`.
- Omitted options preserve automatic labels.
- Custom axis labels are stems; evaluated units remain automatic.
- Positive structural moment remains plotted downward.

### Roomier content transitions

- Level-2 heading margin: `0.60rem 0 0.34rem 0`.
- Level-3 heading margin: `0.46rem 0 0.24rem 0`.
- Narrative outer margin: `0.36rem 0 0.60rem 0`.

### Dense characteristic-point invariants

- Characteristic-point mathematics remains owned by the plotting layer; presentation must never change coordinates, values, colors, units, curves, legend, extrema detection, or sign convention.
- Multi-series annotations are clustered by nearby display-space x position using the existing clustering contract.
- Sparse clusters with fewer than **3** labels retain existing inline behavior.
- Dense clusters with **3 or more** labels are now designed to use a compact summary panel below the plot instead of per-point callouts.
- Dense curve markers remain visible; dense inline text is removed; no long leader lines are used.
- Dense summary groups are ordered by x. Rows retain stable `PlotResult.series` order, exact `series.display_label`, curve color, literal `max`/`min` role, value, and required unit information.
- The figure must never widen; the main engineering axes must preserve baseline physical width/height within ±1 px. Vertical growth is content-driven and must be materially smaller than the rejected +1.85 in bottom band for the canonical six-series fixture.
- No parser/model/API syntax change is part of this task.

## Open issues / user feedback

- User rejected the initial scattered in-axes labels.
- User rejected aligned in-axes rails because labels remained visually crowded/overlapping.
- User rejected the increased-clearance in-axes rail because curves and labels still competed for the same area.
- User approved moving dense labels outside the plot, but the first lateral external-callout screenshot was rejected because Colab scaled the widened 9.7-inch figure down.
- The bottom callout band preserved plot scale and passed machine geometry, but assistant-run PNG QA rejected it aesthetically because of excessive vertical whitespace and long leader lines.
- The replacement compact-summary direction is approved conceptually and now specified in writing; production implementation has not started.
- Multiline ordinary function-call parsing remains a later ergonomics item outside this task.
- `no_vertical_scroll()` Colab ergonomics remains explicitly outside this graphics correction.

## Validation evidence

### Narrative / presentation polish

- Narrative SHA `161bbaba36b93c3d7395790eb6e41284d36c231b`: **464/464 passed**, real-Colab visually validated.
- Presentation-polish SHA `d6fd873e21d5a415a2787bf06fdeceaa1f013e41`: **477/477 passed**, real-Colab visually validated.

### Characteristic-label history

- Child branch baseline: **477/477 passed**.
- Multiple in-axes iterations reached 479/479, 480/480 and 481/481 but failed real-Colab visual QA.
- Lateral external-callout implementation SHA `70c303d9c73d5027d0940778229fbdeb5a58a9fc` reached **482/482**, but real-Colab QA rejected visible shrink caused by widening the figure from 6.4 in to 9.7 in.

### Bottom callout band RED → GREEN

- RED commit `8fc9e516abf9d87b9d7ce4a901a10bbee8431504`: expected **2 failed, 480 passed** on Actions `33283117813`.
- Bottom-band implementation commit `34b807ab24c3071b91f1a710f8152fbaeaa3b3ae`.
- GREEN Actions `33283236424`: **482/482 passed**.
- Fresh checkpoint gate at `ac3cd1db4c5f75fe4e3533fcc49f703b63ad010f`: **482/482 passed**.

### Assistant-run bottom-band visual evidence

- Evidence Actions `33285562569`, artifact `engcalc-bottom-band-qa`.
- Baseline figure: **6.4 × 4.8 in**; rejected bottom-band figure: **6.4 × 6.65 in**.
- Baseline axes: **548.924 × 379.608 px**; bottom-band axes: **549.942 × 379.608 px**.
- Characteristic annotations: **12**; pairwise text overlap: **0**; all dense labels below axes: **true**.
- Machine geometry was correct, but visual inspection rejected the presentation because the lower band was oversized and leader lines were visually dominant.

### Dense summary design checkpoint

- Conceptual dense-summary direction was explicitly approved by the user on 2026-08-30.
- Initial written-spec commit: `b7e1c6306c14a16e04f247bf21112eecf0e1031f`.
- Self-review clarified deterministic row identity and unit presentation in commit `8a40d005d80e33fd3bbc1ffc10b9882ba39a7830`.
- No production source or tests were changed by these documentation commits; the previous 482/482 product evidence therefore remains the current machine baseline, not evidence for the unimplemented summary design.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE, distribution-validated, merged.
- **0.7.3 derivation traces:** RETIRED.
- **Narrative text:** IMPLEMENTED + MACHINE GREEN + REAL-COLAB VISUALLY VALIDATED.
- **Presentation polish:** IMPLEMENTED + REAL-COLAB VISUALLY VALIDATED; retained and not merged.
- **Characteristic-point label deconfliction:** OPEN. Compact dense-summary design is approved conceptually, written and self-reviewed; implementation plan and RED→GREEN work are still pending.
- **0.8.0 Piecewise:** DESIGN + SPEC + IMPLEMENTATION PLAN COMPLETE; implementation not started.
- **0.8.1:** exact-first extrema, roots and intersections.
- **0.8.2:** exact envelopes and governing intervals.
- **0.8.3:** named response cases/combinations.
- **0.9.0:** vectors, matrices and linear systems.
- **0.10.0:** engineering verification system.
- **0.10.1:** verification collections/summaries.
- **1.0.0:** language/API stabilization and release engineering.

## Exact next step

1. User reviews the written spec `docs/superpowers/specs/2026-08-30-engcalc-dense-characteristic-summary-design.md` and either approves it or requests changes.
2. After explicit written-spec approval, create the dedicated implementation plan with the Superpowers planning workflow.
3. Implementation plan must start by replacing rejected bottom-band tests with RED dense-summary contracts, then GREEN implementation, focused tests, full suite, automated PNG + metrics QA, visual self-review, temporary QA cleanup, and explicit user acceptance.
4. Do not begin production implementation before the written-spec review gate is satisfied.
5. Do not merge without explicit user approval.

## How to resume in a new conversation

Read this file first. Released `main` remains EngCalc 0.7.2. Narrative and plot presentation polish are visually validated. Dense-label attempts inside the axes, on lateral rails, and in a bottom callout band were machine-green at different stages but visually rejected. The latest rejected band preserved the full plot but added excessive lower whitespace and long leaders. The user approved replacing dense callouts with a compact color-keyed summary panel below the unchanged-size plot while sparse clusters remain inline. The written design is `docs/superpowers/specs/2026-08-30-engcalc-dense-characteristic-summary-design.md`, self-reviewed at commit `8a40d005d80e33fd3bbc1ffc10b9882ba39a7830`. Production implementation has not started. Next gate is explicit user review of the written spec, then implementation planning. Never invoke Codex without explicit authorization and never merge without explicit user approval.
