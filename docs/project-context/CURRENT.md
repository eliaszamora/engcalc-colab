# EngCalc Current Project Context

_Last updated: 2026-08-29 — narrative/presentation polish are visually validated; all in-axes, lateral, and current bottom-band dense-label variants have now been visually reviewed. The bottom band fixes plot shrink but is not aesthetically accepted because it adds excessive vertical whitespace and long leader lines. Machine baseline remains 482/482._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released branch: `main`; package/runtime version remains **0.7.2** during pre-release work.
- Active branch: **`feature/v0.8.0-characteristic-label-layout`**. Do not merge without explicit user approval.
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
- Multi-series annotations are clustered by nearby display-space x position.
- Sparse clusters with fewer than **3** labels retain the existing inline behavior unless a later approved design changes this explicitly.
- Any future dense-layout strategy must preserve the original visible plot width/scale in notebook rendering; widening the whole figure is prohibited because Colab scales it down.

## Open issues / visual QA history

- User rejected the initial scattered in-axes labels.
- User rejected aligned in-axes rails because labels remained visually crowded/overlapping.
- User rejected the increased-clearance in-axes rail because curves and labels still competed for the same area.
- User approved moving dense labels outside the plot, but the first **lateral** external-callout screenshot was rejected because Colab scaled the 9.7-inch-wide figure down and the graph visibly became smaller.
- Root cause of lateral shrink: preserving the Matplotlib axes' physical size was insufficient when the whole raster exceeded Colab's display width; notebook scaling shrank the whole visual.
- A **bottom callout band** was then implemented to keep figure width at 6.4 in and preserve the axes size. Machine geometry is correct, but assistant-run visual QA shows the band is too tall and the leader lines are long/visually dominant. Therefore this bottom-band presentation is **not accepted as the final dense-label design**.
- Recommended next design direction: keep the full-size plot and replace dense per-point callout leaders with a compact characteristic-point summary/table below the plot, grouped by series or shared x and keyed by the same series colors. Sparse points can remain inline. This should preserve information while avoiding overlap, long leaders, and horizontal shrink.
- Multiline ordinary function-call parsing remains a later ergonomics item outside this task.

## Validation evidence

### Narrative / presentation polish

- Narrative SHA `161bbaba36b93c3d7395790eb6e41284d36c231b`: **464/464 passed**, real-Colab visually validated.
- Presentation-polish SHA `d6fd873e21d5a415a2787bf06fdeceaa1f013e41`: **477/477 passed**, real-Colab visually validated.

### Characteristic-label history

- Child branch baseline: **477/477 passed**.
- Multiple in-axes iterations reached 479/479, 480/480 and 481/481 but failed real-Colab visual QA.
- Lateral external-callout implementation SHA `70c303d9c73d5027d0940778229fbdeb5a58a9fc` reached **482/482**, but real-Colab QA rejected the visible shrink caused by widening the figure from 6.4 in to 9.7 in.

### Bottom callout band RED → GREEN

- RED commit **`8fc9e516abf9d87b9d7ce4a901a10bbee8431504`** required a bottom band, original figure width, increased height, and preservation of baseline axes pixel width/height.
- RED Actions `33283117813`, job `99181543314`, Python 3.13.15: **2 failed, 480 passed**. Expected failures: labels were not below the axes and figure width was still 9.7 in instead of 6.4 in.
- Bottom-band implementation commit **`34b807ab24c3071b91f1a710f8152fbaeaa3b3ae`**.
- GREEN Actions **`33283236424`**, job **`99181850054`**, Python 3.13.15: **482/482 passed**.
- Fresh checkpoint gate at `ac3cd1db4c5f75fe4e3533fcc49f703b63ad010f`: **482/482 passed**.

### Assistant-run visual evidence

- To remove dependence on the user's computer, a temporary Actions QA harness rendered the exact six-series dense fixture and exported both PNG and metrics. The instrumentation was removed after capture; no production behavior was changed by the QA harness.
- Evidence run: Actions **`33285562569`**, artifact `engcalc-bottom-band-qa`.
- Metrics from the exact renderer:
  - baseline figure: **6.4 × 4.8 in**;
  - bottom-band figure: **6.4 × 6.65 in**;
  - baseline axes: **548.924 × 379.608 px**;
  - current axes: **549.942 × 379.608 px** — not smaller;
  - characteristic annotations: **12**;
  - pairwise text-box overlaps: **0**;
  - all dense labels below axes: **true**.
- Visual inspection of the exported PNG: the plot itself retains its scale/width, so the user's shrink complaint is solved. However, the added lower band is visually oversized and the leader lines are long and cluttered. This variant is therefore **machine-correct but visually rejected** as the final presentation.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE, distribution-validated, merged.
- **0.7.3 derivation traces:** RETIRED.
- **Narrative text:** IMPLEMENTED + MACHINE GREEN + REAL-COLAB VISUALLY VALIDATED.
- **Presentation polish:** IMPLEMENTED + REAL-COLAB VISUALLY VALIDATED; retained and not merged.
- **Characteristic-point label deconfliction:** still OPEN. Existing bottom-band implementation is machine-green but visually rejected; next design should be a compact dense characteristic summary/table while preserving sparse inline labels and full plot size.
- **0.8.0 Piecewise:** DESIGN + SPEC + IMPLEMENTATION PLAN COMPLETE; implementation not started.
- **0.8.1:** exact-first extrema, roots and intersections.
- **0.8.2:** exact envelopes and governing intervals.
- **0.8.3:** named response cases/combinations.
- **0.9.0:** vectors, matrices and linear systems.
- **0.10.0:** engineering verification system.
- **0.10.1:** verification collections/summaries.
- **1.0.0:** language/API stabilization and release engineering.

## Exact next step

1. Show the assistant-generated PNG and metrics to the user as evidence.
2. Do **not** close the dense-label task based solely on the 482/482 machine gate.
3. Recommended next iteration: TDD a compact characteristic-point summary/table below the unchanged-size plot for dense clusters, using series labels/colors for association and eliminating long leader lines; retain inline annotation for sparse clusters.
4. After implementation, rerun focused + complete tests and generate the QA PNG automatically again before asking the user to inspect anything.
5. Do not merge without explicit user approval.

## How to resume in a new conversation

Read this file first. Released `main` remains EngCalc 0.7.2. Narrative and plot presentation polish are visually validated. Several dense-label strategies were attempted: scattered/aligned/increased-clearance in-axes layouts failed visual QA; lateral external callouts solved overlaps but caused Colab to shrink the whole plot; a bottom callout band preserved plot size and passed 482/482 tests, but assistant-run PNG QA shows excessive lower whitespace and long leader-line clutter. The dense-label task remains open. The recommended next architecture is a compact color-keyed characteristic-point summary/table below the full-size graph for dense cases, while sparse points remain inline. Never invoke Codex without explicit authorization and never merge without explicit user approval.
