# EngCalc Current Project Context

_Last updated: 2026-08-30 — compact dense-characteristic summary design is approved; written spec, planning clarification, and detailed TDD implementation plan are complete. Production implementation has not started._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released branch: `main`; package/runtime version remains **0.7.2** during pre-release work.
- Active branch: **`feature/v0.8.0-characteristic-label-layout`**. Do not merge without explicit user approval.
- Latest state-changing work is documentation/planning only; `src/` and tests still match the previously validated bottom-band product tree.
- Dense-summary design: `docs/superpowers/specs/2026-08-30-engcalc-dense-characteristic-summary-design.md`.
- Planning clarification: `docs/superpowers/specs/2026-08-30-engcalc-dense-characteristic-summary-planning-clarification.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-dense-characteristic-summary-implementation.md`.
- Retain existing feature/planning branches unless explicitly asked to delete them.
- Piecewise planning branch: `planning/v0.8.0-piecewise`; Piecewise production implementation has not started.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.

## Approved behavior

### Existing retained presentation behavior

- `%%eng` narrative text remains visually validated and presentation-only.
- `plot(...)` / `envelope(...)` optional `title`, `xlabel`, and `ylabel` behavior remains unchanged.
- Positive structural moment remains plotted downward.
- Roomier heading/narrative spacing remains unchanged.

### Dense characteristic summary

- Characteristic-point mathematics is owned by `plotting.py`; presentation must not independently recompute extrema.
- Planning inspection found current `label_layout.py` still duplicated extrema/request extraction. The approved-intent clarification therefore permits a **private, behavior-preserving** `_CharacteristicRequest` / `_characteristic_requests(result)` refactor in `plotting.py`, consumed by both plotting and presentation.
- Multi-series clustering continues to use the existing display-space x tolerance and dense threshold of **3** labels.
- Sparse clusters with fewer than 3 labels remain inline and retain baseline figure size.
- Dense clusters move to a compact secondary summary axes below the main plot.
- Dense curve markers remain on the engineering curves; dense inline text is removed; dense leader lines are eliminated.
- Summary groups are ordered by x. Rows use stable `PlotResult.series` order, exact `PlotSeries.display_label`, exact plotted-line color, literal `max`/`min` role, and characteristic value.
- x unit is shown once per group. A homogeneous y unit is shown once in the value heading; heterogeneous-unit fallback may include units per row.
- Figure width must not grow. `figure.axes[0]` remains the main engineering axes and must retain baseline physical width/height within ±1 px under Agg.
- Canonical six-series summary must add less than the rejected **1.85 in** vertical band.
- No parser/model/public API change is included.

## Open issues / user feedback

- Earlier in-axes dense-label strategies were visually rejected because labels competed with curves.
- Lateral external callouts were rejected because widening to 9.7 in caused Colab to scale the whole graphic down.
- Bottom callout band preserved plot size and passed machine geometry, but visual QA rejected the excessive lower whitespace and long leader lines.
- Compact summary design is approved and planned, but remains **unimplemented**.
- Multiline ordinary function-call parsing remains a later ergonomics item.
- `no_vertical_scroll()` Colab ergonomics remains explicitly outside this graphics correction.

## Validation evidence

### Retained baseline

- Narrative SHA `161bbaba36b93c3d7395790eb6e41284d36c231b`: **464/464 passed**, real-Colab visually validated.
- Presentation-polish SHA `d6fd873e21d5a415a2787bf06fdeceaa1f013e41`: **477/477 passed**, real-Colab visually validated.
- Bottom-band implementation SHA `34b807ab24c3071b91f1a710f8152fbaeaa3b3ae`; GREEN Actions `33283236424`: **482/482 passed**.
- Fresh bottom-band checkpoint gate at `ac3cd1db4c5f75fe4e3533fcc49f703b63ad010f`: **482/482 passed**.
- Bottom-band QA Actions `33285562569`: baseline figure **6.4 × 4.8 in**, rejected figure **6.4 × 6.65 in**, baseline axes **548.924 × 379.608 px**, presented axes **549.942 × 379.608 px**, 12 labels, zero overlaps. Visual presentation rejected despite machine PASS.

### Dense-summary planning checkpoint

- User approved the compact-summary conceptual design and then explicitly approved the written spec on 2026-08-30.
- Written design initial commit: `b7e1c6306c14a16e04f247bf21112eecf0e1031f`.
- Spec self-review refinement: `8a40d005d80e33fd3bbc1ffc10b9882ba39a7830`.
- Detailed implementation plan finalized in commit `08e38b5751c54fa87129249532a62fd20cdfca7e`.
- Planning clarification eliminating presentation-layer extrema duplication: `d3d9fb5402a271b1bb0fc5a4ef49b5d0347734cc`.
- No new product validation applies to the summary because production implementation has not started; the 482/482 evidence remains the previous product baseline only.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE, distribution-validated, merged.
- **0.7.3 derivation traces:** RETIRED.
- **Narrative text:** IMPLEMENTED + MACHINE GREEN + REAL-COLAB VISUALLY VALIDATED.
- **Presentation polish:** IMPLEMENTED + REAL-COLAB VISUALLY VALIDATED; retained and not merged.
- **Characteristic-point label deconfliction:** OPEN; compact-summary spec + implementation plan COMPLETE; implementation pending.
- Dense-summary implementation plan tasks:
  1. centralize authoritative characteristic requests in `plotting.py` with RED→GREEN regression;
  2. build immutable dense-summary groups and remove presentation extrema duplication;
  3. replace rejected callout tests with compact-summary RED contracts;
  4. implement compact summary GREEN and run focused/full tests;
  5. generate GitHub Actions PNG + JSON metrics and perform assistant visual QA;
  6. after explicit user visual acceptance, remove temporary QA harness/workflow and stop at merge gate.
- **0.8.0 Piecewise:** design/spec/plan complete; production implementation not started.
- Later roadmap remains 0.8.1 exact-first extrema/roots/intersections, 0.8.2 exact envelopes/governing intervals, 0.8.3 named response cases/combinations, 0.9.0 vectors/matrices/linear systems, 0.10.x verification, 1.0 stabilization.

## Exact next step

1. Choose an execution mode for `docs/superpowers/plans/2026-08-30-engcalc-dense-characteristic-summary-implementation.md`.
2. Recommended mode: **Subagent-Driven Development** with a fresh agent/review gate per task; alternative: **Inline Execution** in the current session using `executing-plans` with checkpoints.
3. On execution, begin Task 1 with a failing `tests/test_characteristic_requests.py`; do not modify production before confirming RED.
4. Do not invoke Codex.
5. Do not merge without explicit user approval.

## How to resume in a new conversation

Read this file first. Released `main` remains EngCalc 0.7.2. Narrative and plot presentation polish are visually validated. Dense-label attempts inside the axes, on lateral rails, and in a bottom callout band were rejected visually; the bottom band was nevertheless 482/482 machine-green. The user approved a replacement compact color-keyed summary below the unchanged-size plot while sparse clusters remain inline. The written design, planning clarification, and detailed implementation plan are complete on `feature/v0.8.0-characteristic-label-layout`; production implementation has not started. Planning also corrected an existing architectural flaw: `label_layout.py` currently recomputes extrema, so Task 1 centralizes a private authoritative request sequence in `plotting.py` with no public behavior change. Next action is to execute the implementation plan via Subagent-Driven Development (recommended) or Inline Execution. Never invoke Codex without explicit authorization and never merge without explicit user approval.
