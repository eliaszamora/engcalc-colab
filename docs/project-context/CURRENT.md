# EngCalc Current Project Context

_Last updated: 2026-08-30 — compact dense-characteristic summary implementation is complete, machine-green, assistant-QA approved, and explicitly visually accepted by the user. Pre-integration review is complete and Pull Request #30 is open against `main`, ready for review. The branch remains unmerged._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released branch: `main`; package/runtime version remains **0.7.2** during pre-release work.
- Active branch: **`feature/v0.8.0-characteristic-label-layout`**. Do not merge without explicit user approval.
- Open integration PR: **#30 — `feat: integrate EngCalc narrative and plot presentation polish`**, base `main`, ready for review, mergeable.
- Pre-PR housekeeping checkpoint: `954025da22e3976b2f502b92fbbcd88b27a9e2fd`.
- Product tree checkpoint: `a11b0946aad322cb30145a178eda4261f8f1e1de`.
- Post-QA-cleanup checkpoint: `236760a8e35f9a60978e6197f28c468ef8709464`.
- GitHub compare confirmed `a11b0946...` and `236760a8...` have **zero file differences**; QA cleanup returned the branch exactly to the validated product tree.
- Before opening PR #30, the feature-only validation workflow was removed; compare from fresh-green SHA `f945a408...` to `954025da...` changed only `.github/workflows/characteristic-label-validation.yml`.
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

### Dense characteristic summary — implemented and accepted

- Characteristic-point mathematics is owned by `plotting.py`; presentation no longer independently recomputes extrema.
- A private `_CharacteristicRequest` / `_characteristic_requests(result)` sequence is the authoritative source consumed by both plotting and presentation.
- Multi-series clustering uses the existing display-space x tolerance and dense threshold of **3** labels.
- Sparse clusters with fewer than 3 labels remain inline and retain baseline figure size.
- Dense clusters move to a compact secondary summary axes below the main plot.
- Dense curve markers remain on the engineering curves; dense inline text is removed; dense leader lines are eliminated.
- Summary groups are ordered by x. Rows preserve stable `PlotResult.series` order, exact `PlotSeries.display_label`, exact plotted-line color, literal `max`/`min` role, and characteristic value.
- x unit is shown once per group. A homogeneous y unit is shown once in the value heading; heterogeneous-unit fallback may include units per row.
- Figure width does not grow. `figure.axes[0]` remains the main engineering axes and retains baseline physical width/height under Agg.
- Canonical six-series summary adds **1.34 in** vertically, materially below the rejected **1.85 in** bottom-callout band.
- No parser/model/public API change is included by the dense-summary correction itself.

## Historical visual decisions

- Earlier in-axes dense-label strategies were rejected because labels competed with curves.
- Lateral external callouts were rejected because widening to 9.7 in caused Colab to scale the whole graphic down.
- Bottom callout band preserved plot size and passed machine geometry, but visual QA rejected the excessive lower whitespace and long leader lines.
- Compact color-keyed summary below the unchanged-size engineering axes was accepted by the user on **2026-08-30**.
- Multiline ordinary function-call parsing remains a later ergonomics item.
- `no_vertical_scroll()` Colab ergonomics remains explicitly outside this graphics correction.

## Validation evidence

### Retained baseline

- Narrative SHA `161bbaba36b93c3d7395790eb6e41284d36c231b`: **464/464 passed**, real-Colab visually validated.
- Presentation-polish SHA `d6fd873e21d5a415a2787bf06fdeceaa1f013e41`: **477/477 passed**, real-Colab visually validated.
- Bottom-band implementation SHA `34b807ab24c3071b91f1a710f8152fbaeaa3b3ae`; GREEN Actions `33283236424`: **482/482 passed**.
- Fresh bottom-band checkpoint gate at `ac3cd1db4c5f75fe4e3533fcc49f703b63ad010f`: **482/482 passed**.
- Bottom-band QA Actions `33285562569`: baseline figure **6.4 × 4.8 in**, rejected figure **6.4 × 6.65 in**, baseline axes **548.924 × 379.608 px**, presented axes **549.942 × 379.608 px**, 12 labels, zero overlaps. Visual presentation rejected despite machine PASS.

### Dense-summary implementation — RED→GREEN evidence

- Pre-implementation baseline on branch: **482 passed**.
- Task 1 RED SHA `3117b80f...`: expected collection failure because `_characteristic_requests` did not exist.
- Task 1 GREEN SHA `1c226298...`: **483 passed**.
- Task 2 RED Actions `33297360032`, job `99219218711`: expected collection failure because `_build_dense_summary_groups` did not exist.
- Task 2 GREEN SHA `6a4a9947...`: **484 passed**.
- Visual-contract RED SHA `9559bd25...`: **3 failed, 480 passed**, exactly for retained callouts, rejected 1.85 in expansion, and missing summary axes.
- Product GREEN SHA `a11b0946aad322cb30145a178eda4261f8f1e1de`: **484 passed**.

### Dense-summary final QA

- QA evidence SHA: `44d48065db4b6bad1b5ffbf0fa701478b93d6075`.
- GitHub Actions run: `33297891785`; job: `99220581598`.
- Fresh full suite on exact QA SHA: **484 passed in 80.05 s**.
- QA artifact: `engcalc-characteristic-summary-qa`, artifact ID `9728003251`.
- Artifact digest: `sha256:17d512b5c6cf15ade0c5a9fe526c93d4e12f95486e8089684f53fc37401e9ee1`.
- Baseline figure: **6.4 × 4.8 in**.
- Presented figure: **6.4 × 6.14 in**.
- Vertical expansion: **1.34 in**.
- Baseline main axes: **548.924 × 379.608 px**.
- Presented main axes: **548.924 × 379.608 px**.
- Dense groups: **2**.
- Dense entries: **12**.
- Summary texts checked: **41**.
- Text overlaps: **0**.
- Texts outside figure: **0**.
- Dense plot annotations: **0**.
- Leader lines: **0**.
- Assistant visual QA: PASS.
- User visual acceptance: **APPROVED on 2026-08-30**.

### QA cleanup and pre-integration gate

- Temporary workflow artifact steps removed in commit `acd52d4589df71c160a3d9d56782f5891d32673c`.
- Temporary `tools/render_dense_characteristic_summary_qa.py` removed in commit `236760a8e35f9a60978e6197f28c468ef8709464`.
- Compare `a11b0946aad322cb30145a178eda4261f8f1e1de...236760a8e35f9a60978e6197f28c468ef8709464`: **zero changed files**. Therefore QA cleanup changed no product source or product test tree.
- Fresh pre-integration rerun on SHA `f945a408bde8bd88511396609abb3f5e91c37937`: **484 passed in 66.74 s**.
- Complete branch audit against `main` found the accumulated, previously validated narrative/presentation work plus dense-summary source/tests/docs; no dependency/build changes or unrelated product modules.
- `main` is the merge base and direct ancestor of the feature branch: **0 commits behind**; no historical divergence/conflict is present.
- Feature-only workflow `.github/workflows/characteristic-label-validation.yml` removed in commit `954025da22e3976b2f502b92fbbcd88b27a9e2fd` before PR creation.
- Pull Request **#30** opened against `main` on 2026-08-30; GitHub recalculated it as **mergeable=true**, non-draft, still unmerged.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE, distribution-validated, merged.
- **0.7.3 derivation traces:** RETIRED.
- **Narrative text:** IMPLEMENTED + MACHINE GREEN + REAL-COLAB VISUALLY VALIDATED; included in PR #30.
- **Presentation polish:** IMPLEMENTED + REAL-COLAB VISUALLY VALIDATED; included in PR #30.
- **Characteristic-point label deconfliction:** **IMPLEMENTED + 484/484 GREEN + AUTOMATED QA PASS + USER VISUALLY APPROVED**; included in PR #30.
- Dense-summary implementation plan tasks 1–6: COMPLETE.
- **Integration:** PR #30 OPEN + MERGEABLE; merge not yet authorized/executed.
- **0.8.0 Piecewise:** design/spec/plan complete; production implementation not started.
- Later roadmap remains 0.8.1 exact-first extrema/roots/intersections, 0.8.2 exact envelopes/governing intervals, 0.8.3 named response cases/combinations, 0.9.0 vectors/matrices/linear systems, 0.10.x verification, 1.0 stabilization.

## Exact next step

1. Review Pull Request **#30** against `main`.
2. Do not merge PR #30 without a new explicit user instruction to merge it.
3. If merge is approved, verify the PR head has not moved unexpectedly, merge using the selected repository method, then verify the resulting `main` state with a fresh full test run/equivalent gate.
4. Keep the feature branch available for PR feedback until the integration is complete.
5. Do not begin Piecewise production implementation as part of this PR gate.
6. Do not invoke Codex unless explicitly authorized.

## How to resume in a new conversation

Read this file first. Released `main` remains EngCalc 0.7.2 at `72b0b1b...`. The accumulated narrative, presentation-polish, and dense characteristic-label work is now proposed for integration in Pull Request #30 from `feature/v0.8.0-characteristic-label-layout`. The compact color-keyed summary is implemented with a centralized characteristic-request source, preserved sparse inline behavior, no dense leader lines, unchanged main axes geometry, and 1.34 in vertical expansion in the canonical six-series case. Product SHA `a11b0946...` passed 484/484; exact QA SHA `44d48065...` passed 484/484 and generated artifact `9728003251`; assistant visual QA passed and the user explicitly approved the image. A fresh pre-integration rerun on `f945a408...` passed 484/484 in 66.74 s. The feature-only CI workflow was then removed, and PR #30 was opened against `main`; GitHub reports it mergeable. The PR remains unmerged and requires explicit user authorization before merge. Never invoke Codex without explicit authorization.
