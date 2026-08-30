# EngCalc Current Project Context

_Last updated: 2026-08-29 — narrative/presentation polish are visually validated; all in-axes and lateral dense-label variants were rejected by real-Colab QA; dense clusters now use a bottom callout band that preserves the original plot width/axes size. Machine gate: 482/482; new Colab visual QA pending._

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

### Dense characteristic-point layout

- Characteristic-point mathematics remains owned by the plotting layer; presentation never changes coordinates, values, colors, units, curves, legend, extrema detection, or sign convention.
- Multi-series annotations are clustered by nearby display-space x position.
- Clusters with fewer than **3** labels keep the existing inline annotations exactly.
- Clusters with **3 or more** labels use a dedicated **bottom callout band**.
- The figure width remains the original Matplotlib width; only figure height grows to make room for dense labels.
- The data `Axes` preserves its original physical width and height and is shifted upward into the taller figure. This is required because Colab scales oversized-width figures to the notebook cell and visually shrinks the graph.
- Each dense shared-x group is one aligned vertical rail/column within the bottom band, horizontally centered near its characteristic x location while clamped inside the figure.
- Dense labels preserve anchor visual-y ordering and use 12 px internal vertical clearance; tests require at least 10 px free clearance.
- Each dense label retains a thin same-color leader line to the characteristic point.
- Dense callout text must remain below the data axes, inside the figure canvas, and pairwise non-overlapping.
- Bottom-band height scales with the largest dense cluster; sparse plots do not enlarge the figure.

## Open issues / user feedback

- User rejected the initial scattered in-axes labels.
- User rejected aligned in-axes rails because labels remained visually crowded/overlapping.
- User rejected the increased-clearance in-axes rail because curves and labels still competed for the same area.
- User approved moving dense labels outside the plot, but the first **lateral** external-callout screenshot was also rejected because Colab scaled the 9.7-inch-wide figure down and the graph visibly became smaller.
- Root cause: preserving the Matplotlib axes' physical size was insufficient when the whole raster exceeded Colab's display width; notebook scaling shrank the entire visual.
- Current corrective strategy is therefore **vertical expansion only** via the bottom callout band.
- New real-Colab visual QA is required before this graphics task can be closed.
- Multiline ordinary function-call parsing remains a later ergonomics item outside this task.

## Validation evidence

### Narrative / presentation polish

- Narrative SHA `161bbaba36b93c3d7395790eb6e41284d36c231b`: **464/464 passed**, real-Colab visually validated.
- Presentation-polish SHA `d6fd873e21d5a415a2787bf06fdeceaa1f013e41`: **477/477 passed**, real-Colab visually validated.

### Characteristic-label history

- Child branch baseline: **477/477 passed**.
- Multiple in-axes iterations reached 479/479, 480/480 and 481/481 but failed real-Colab visual QA.
- Lateral external-callout implementation SHA `70c303d9c73d5027d0940778229fbdeb5a58a9fc` reached **482/482**, but the real-Colab screenshot showed the graph visually shrinking because the figure widened from 6.4 in to 9.7 in.

### Bottom callout band RED → GREEN

- RED commit **`8fc9e516abf9d87b9d7ce4a901a10bbee8431504`** changed the contract to require a bottom band, original figure width, increased height, and preservation of baseline axes pixel width/height.
- RED Actions `33283117813`, job `99181543314`, Python 3.13.15: **2 failed, 480 passed**. Expected failures: labels were not below the axes and figure width was still 9.7 in instead of 6.4 in.
- Bottom-band implementation commit **`34b807ab24c3071b91f1a710f8152fbaeaa3b3ae`**.
- GREEN Actions **`33283236424`**, job **`99181850054`**, Python 3.13.15: **482/482 passed** in 59.94 s.
- Coverage verifies: dense anchor-y order, aligned rails, leader-line presence, robust vertical clearance, bottom-of-axes placement, figure containment, pairwise text non-overlap, unchanged figure width, increased figure height, preservation of baseline `Axes` width/height, and unchanged sparse inline behavior.
- Temporary characteristic-label workflow remains active until real-Colab QA is accepted.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE, distribution-validated, merged.
- **0.7.3 derivation traces:** RETIRED.
- **Narrative text:** IMPLEMENTED + MACHINE GREEN + REAL-COLAB VISUALLY VALIDATED.
- **Presentation polish:** IMPLEMENTED + REAL-COLAB VISUALLY VALIDATED; retained and not merged.
- **Characteristic-point label deconfliction:** bottom callout band **482/482 MACHINE GREEN**; real-Colab visual QA pending.
- **0.8.0 Piecewise:** DESIGN + SPEC + IMPLEMENTATION PLAN COMPLETE; implementation not started.
- **0.8.1:** exact-first extrema, roots and intersections.
- **0.8.2:** exact envelopes and governing intervals.
- **0.8.3:** named response cases/combinations.
- **0.9.0:** vectors, matrices and linear systems.
- **0.10.0:** engineering verification system.
- **0.10.1:** verification collections/summaries.
- **1.0.0:** language/API stabilization and release engineering.

## Exact next step

1. Run a fresh complete gate on the checkpointed HEAD containing production, tests and this context update.
2. Pin that validated SHA in a one-shot Colab installer that clears stale EngCalc modules and re-registers `%%eng`.
3. Render the same six-series dense moment fixture.
4. Require visually: graph retains its former width/scale, dense labels live in the added bottom band, labels do not overlap, leader lines are readable without excessive clutter, title/axes/legend remain clean, and positive moment remains downward.
5. If accepted, remove the temporary workflow and verify cleanup before requesting an explicit integration/merge decision.
6. If not accepted, refine presentation only and rerun focused + full tests.

## How to resume in a new conversation

Read this file first. Released `main` remains EngCalc 0.7.2. Narrative and plot presentation polish are visually validated. Several in-axes dense-label approaches and then a lateral external-callout approach were machine-green but rejected by real-Colab QA. The lateral approach was rejected specifically because widening the figure caused Colab to scale the whole graphic down. The active strategy keeps the original figure width and original physical `Axes` size, adds height only, and places dense clusters in aligned bottom-band callouts with same-color leader lines. Production SHA `34b807ab24c3071b91f1a710f8152fbaeaa3b3ae` is **482/482 GREEN**; run one fresh checkpoint gate after this context commit, then perform real-Colab visual QA. Piecewise remains planned but unimplemented. Never invoke Codex without explicit authorization and never merge without explicit user approval.
