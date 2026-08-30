# EngCalc Dense Characteristic Summary — Design

_Date: 2026-08-30_
_Status: design direction approved in conversation; written specification pending user review before implementation planning_
_Active branch: `feature/v0.8.0-characteristic-label-layout`_

## 1. Purpose

Replace the visually rejected dense characteristic-point callout band with a compact summary panel that preserves the full-size engineering plot while keeping every dense characteristic value readable and traceable to its series.

This is a presentation-layer change only. It must not alter characteristic-point mathematics, curve sampling, units, extrema detection, response values, legend semantics, series colors, or the structural sign convention. Positive structural moment remains plotted downward.

## 2. Context and problem statement

EngCalc currently annotates maxima and minima directly on plots. Sparse cases are acceptable, but multi-series plots can create several characteristic labels at nearly the same display-space x coordinate.

Several strategies have already been tested and rejected visually:

1. scattered in-axes labels;
2. aligned in-axes rails;
3. increased-clearance in-axes rails;
4. lateral external callouts, which widened the figure and caused Google Colab to scale the complete plot down;
5. a bottom callout band with leader lines, which preserved plot scale and passed 482/482 tests but introduced excessive vertical whitespace and visually dominant long leaders.

The next design must solve the information-density problem without shrinking the plot or reconnecting every dense label to its point with long leader lines.

## 3. Design decision

Dense characteristic clusters will be represented in a compact summary panel below the unchanged-size main plot.

A cluster is dense when it contains **3 or more** characteristic requests whose display-space x positions fall within the existing clustering tolerance. Sparse clusters with fewer than 3 labels retain the existing inline annotation behavior.

For dense clusters:

- the characteristic markers already drawn on the curves remain visible;
- the dense inline text annotations are removed;
- no per-point leader lines are drawn;
- a compact summary panel is added below the main axes;
- summary content is grouped by characteristic x coordinate;
- each entry uses the same series color as the corresponding curve;
- each entry displays series identity, extremum role, and characteristic value;
- the panel uses the minimum vertical space required for its content;
- the complete figure width remains unchanged.

The summary is an engineering presentation element, not a spreadsheet-style table. It should be visually light: aligned text, restrained separators, no heavy cell grid, and no decorative elements that compete with the plot.

## 4. User-facing layout

For a dense six-series moment plot with two shared-x characteristic groups, the intended information hierarchy is:

```text
                 [ unchanged full-size plot ]
                 [ markers remain on curves ]

Characteristic points

x = 0.00 m                         x = 2.50 m
Series   Role   M [tonf·m]         Series   Role   M [tonf·m]
──────────────────────────         ──────────────────────────
● M_C1   min       -6.00           ● M_C1   max        3.38
● M_C2   min      -22.40           ● M_C2   max        8.85
● M_S1   min       -8.00           ● M_S1   max        4.50
● M_S2   min      -19.20           ● M_S2   max       10.80
● M_S3   min      -14.00           ● M_S3   max         ...
● M_S4   min      -16.00           ● M_S4   max         ...
```

This is conceptual layout, not a literal ASCII rendering contract.

### 4.1 Grouping

Each dense cluster becomes one summary group.

Groups are ordered left-to-right by characteristic x coordinate. When multiple dense groups fit comfortably in one row, they are laid out as columns. If future cases contain more groups than fit without crowding, layout may wrap to additional rows, but wrapping must preserve the figure width and avoid horizontal scrolling.

### 4.2 Entry ordering

Within each group, entries follow stable series order from `PlotResult.series`. If one series contributes both a maximum and minimum to the same dense x group, its entries preserve the order in which characteristic requests are produced by the plotting model.

This deliberately avoids sorting rows by numeric value because stable series order makes comparison against the legend and plotted curves easier.

### 4.3 Entry identity and content

Each dense summary entry contains:

- a compact color key using the corresponding plotted series color;
- the exact `series.display_label` used by the plotted series/legend as the row identity;
- the literal extremum role `max` or `min`;
- the characteristic y value.

The row identity must not substitute a different response symbol when doing so would differ from the legend identity. This keeps the summary-to-curve mapping deterministic.

The x coordinate is shown once in the group header rather than repeated on every row. The x header includes the evaluated x unit, for example `x = 2.50 m`.

When all summary rows share one compatible evaluated y unit, that unit is shown once in the value-column heading, for example `M [tonf·m]`, rather than repeated on every row. If a future supported plot legitimately contains non-common y display units, the implementation falls back to displaying the evaluated unit in each affected row instead of dropping unit information.

The panel must not silently drop or merge characteristic requests. Every request removed from dense inline annotation must appear exactly once in the summary.

## 5. Architectural boundaries

### 5.1 Plotting layer remains authoritative

`src/engcalc_colab/plotting.py` remains authoritative for:

- series rendering;
- sampling;
- extrema selection;
- characteristic marker positions;
- units and response symbols;
- moment-axis inversion;
- legend content;
- inline characteristic annotation creation before presentation reflow.

The new design must not reimplement engineering extrema mathematics independently.

### 5.2 Presentation layer owns dense reflow

`src/engcalc_colab/presentation.py` continues to call presentation-only reflow after `render_plot(result)`.

`src/engcalc_colab/label_layout.py` remains the isolated implementation boundary for dense characteristic presentation. It may be refactored internally from callout-band logic to summary-panel logic, but its responsibility remains presentation-only.

The main plot axes must remain `figure.axes[0]` so existing consumers and tests continue to address the engineering plot consistently. Any summary axes are secondary axes added after the main one and are presentation-only.

### 5.3 No parser or model API change

The user does not write new syntax to request this behavior. Dense summary activation is automatic based on characteristic clustering.

No changes are planned to parser grammar, `PlotResult` public API, `plot(...)`, or `envelope(...)` call signatures for this task.

## 6. Dense-cluster detection

Retain the existing display-space clustering approach and current threshold:

- x clustering tolerance: existing `_CLUSTER_X_TOLERANCE_PX` contract;
- dense threshold: `_DENSE_CLUSTER_SIZE = 3`.

Changing the clustering algorithm is outside this design unless implementation proves the current grouping cannot represent the approved fixture correctly. If such a problem is found, implementation must stop and upgrade the design rather than silently changing semantics.

## 7. Figure geometry requirements

The previous failures establish strict geometry constraints.

### 7.1 Width

The figure width must remain equal to the ordinary Matplotlib/EngCalc baseline width. For the current fixture this is 6.4 in.

The dense summary must never widen the figure. This prevents Google Colab from scaling the entire image down.

### 7.2 Main axes physical size

The primary plot axes must preserve their baseline physical width and height within a tolerance of ±1 px under the Agg renderer used by tests.

Adding the summary may shift the primary axes upward, but it must not reduce the visible data area.

### 7.3 Vertical growth

Vertical growth is allowed only for the summary itself and must be content-driven.

For the six-series two-group QA fixture, the new design must use materially less additional height than the rejected bottom-callout variant, which added 1.85 in and produced a 6.4 × 6.65 in figure.

The implementation should target a compact panel around 0.9–1.1 in for that fixture, but those numbers are design targets rather than brittle fixed constants. The acceptance contract is that the rendered result is substantially more compact than the rejected 1.85 in band while remaining readable and collision-free.

## 8. Visual styling requirements

The summary panel should match EngCalc's existing plotting typography and restraint.

Required characteristics:

- font size visually compatible with the existing 8.5 pt characteristic annotations;
- clear group headers;
- aligned values;
- light or minimal separators only;
- same series colors as the plotted curves;
- no long leader lines;
- no heavy table grid;
- no legend duplication beyond what is necessary for row identity;
- no clipping against the figure boundary;
- no overlap with axis labels, title, legend, or other summary groups.

The panel should read as part of the engineering figure, not as an unrelated dataframe rendered underneath it.

## 9. Sparse behavior preservation

If no dense cluster exists:

- no summary panel is created;
- no secondary summary axes are created;
- existing inline characteristic labels remain unchanged;
- figure size remains exactly the ordinary baseline size;
- existing sparse visual behavior remains a regression contract.

A two-series fixture that currently yields four sparse annotations remains the canonical sparse regression case.

## 10. TDD contracts

Implementation must follow RED → GREEN. The existing dense-layout tests describe the rejected bottom-band presentation and therefore must be replaced rather than merely extended.

### 10.1 RED contracts for the dense six-series fixture

The first RED commit must establish all of the following:

1. The fixture still identifies 12 characteristic requests at the same engineering coordinates and extrema roles.
2. The same fixture contains two dense shared-x groups, six entries per group, around `x = 0` and `x = 2.5` for the established test data.
3. Dense characteristic text no longer remains as 12 main-axis `Annotation` objects after presentation reflow.
4. Dense characteristic entries have no `arrow_patch`/leader-line dependency.
5. A dedicated summary presentation surface exists only when dense clusters exist.
6. The summary contains exactly one entry for every dense request: no omission and no duplication.
7. Dense groups are ordered by x coordinate.
8. Rows inside each group follow stable `PlotResult.series` order.
9. Each row preserves the plotted series color, exact `series.display_label`, literal role, characteristic value, and required unit information.
10. Summary text boxes are contained in the figure and do not overlap each other.
11. The figure width equals baseline width.
12. The primary axes width and height remain within ±1 px of the baseline rendering.
13. The six-series summary uses materially less added height than the rejected 1.85 in callout band.

### 10.2 Sparse regression contracts

The sparse two-series fixture must continue to verify:

- four inline annotations remain;
- no dense summary panel is created;
- no leader lines are introduced;
- annotations remain in the ordinary plot region according to current behavior;
- figure width and height equal the baseline 6.4 × 4.8 in under default test configuration.

### 10.3 Engineering invariants

Focused tests must also prove that presentation reflow does not change:

- x or y quantities of characteristic points;
- maximum/minimum classification;
- series ordering;
- units;
- plotted curve data;
- moment-axis inversion;
- legend labels/colors.

## 11. Automated visual QA

Machine geometry tests are necessary but not sufficient because multiple previous variants passed geometric checks and still failed visual inspection.

After GREEN:

1. run the focused dense/sparse presentation tests;
2. run the complete source suite;
3. generate the exact six-series QA fixture automatically through GitHub Actions or an equivalent reproducible harness;
4. export a PNG plus geometry metrics;
5. inspect the PNG before presenting it to the user;
6. report both machine evidence and visual assessment;
7. do not close or merge the graphics task without explicit user acceptance.

The QA metrics should include at minimum:

- figure width/height;
- primary axes pixel width/height;
- number of dense groups;
- number of summary entries;
- overlap count;
- containment status;
- absence of dense leader lines.

## 12. Files expected to change during implementation

Primary expected files:

- `src/engcalc_colab/label_layout.py` — replace bottom-callout layout with compact dense-summary layout;
- `src/engcalc_colab/presentation.py` — only if needed to integrate the secondary presentation surface cleanly;
- `tests/test_dense_characteristic_label_layout.py` — replace rejected bottom-band contracts with dense-summary contracts;
- optional focused presentation tests if separation improves readability;
- `docs/project-context/CURRENT.md` — maintain continuity state.

`src/engcalc_colab/plotting.py`, parser, engine, models, numeric system, and tables are not expected to change. Any need to modify those files should be treated as scope expansion and reviewed before implementation.

## 13. Explicit non-goals

This task does not include:

- piecewise-expression implementation;
- multiline ordinary function-call parsing;
- `no_vertical_scroll()` Colab ergonomics;
- new plot syntax or user configuration flags;
- changing extrema mathematics;
- exact-first extrema/root/intersection work planned for later roadmap milestones;
- merging retained presentation branches into `main`;
- release/version bump work.

## 14. Acceptance criteria

The design is considered successfully implemented only when all of the following are true:

- dense labels no longer overlap or require long callout leaders;
- the main plot remains visually the same size as the baseline;
- the summary is noticeably more compact than the rejected bottom band;
- every dense characteristic value remains visible and correctly associated with its series;
- sparse cases remain unchanged;
- focused and complete automated tests pass;
- reproducible PNG QA passes assistant inspection;
- the user explicitly accepts the rendered result before integration/merge.

## 15. Implementation sequence after spec approval

After this written specification is reviewed and approved, create a dedicated implementation plan using the established Superpowers planning workflow. The plan must begin with replacement RED contracts, then implementation GREEN, focused/full validation, automated PNG QA, cleanup of temporary QA instrumentation, and an explicit merge/integration gate.

Do not begin production implementation directly from this document without that implementation plan.
