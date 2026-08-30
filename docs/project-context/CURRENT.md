# EngCalc Current Project Context

_Last updated: 2026-08-30 — Pull Request #30 has been merged into `main`. Narrative text, plot presentation polish, and the compact dense-characteristic summary are now integrated. A fresh post-merge full-suite gate passed, temporary CI was removed, and the project is ready to move to the next roadmap milestone._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical branch: **`main`**.
- Package/runtime version remains **0.7.2** while the next pre-release milestone is developed.
- PR #30 — `feat: integrate EngCalc narrative and plot presentation polish` — merged on 2026-08-30.
- Merge commit: **`1bb1f63606c669605dcccaf011bcf6f20764b2cc`**.
- Post-merge validation commit: `701bf6957754e1c0fd720082958c39508cd9956b`.
- Post-merge validation run: **GitHub Actions `33298959230`, job `99223386831`: 484/484 passed in 99.80 s**.
- Temporary post-merge workflow removed in `4dba31ce0ff0b2f6ce665539a28c3f50bd92207f`.
- Compare between approved feature head `c3af207f...` and merge commit `1bb1f636...` showed **zero file differences**, so the merge itself did not alter the approved tree.
- Retain existing feature/planning branches unless explicitly asked to delete them.
- Piecewise planning branch: `planning/v0.8.0-piecewise`; approved Piecewise design/spec/implementation plan already exist, but production implementation has not started.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.

## Approved behavior

### Narrative and presentation

- `%%eng` supports visually validated narrative text blocks integrated with headings/equations/plots.
- `plot(...)` / `envelope(...)` support optional `title`, `xlabel`, and `ylabel` presentation overrides.
- Roomier heading/narrative spacing remains approved.
- Positive structural moment remains plotted downward.

### Dense characteristic summary

- Characteristic-point mathematics is owned by `plotting.py`; presentation does not independently recompute extrema.
- A private `_CharacteristicRequest` / `_characteristic_requests(result)` sequence is the authoritative source consumed by plotting and presentation.
- Multi-series clustering uses display-space x tolerance and dense threshold of **3** labels.
- Sparse clusters with fewer than 3 labels remain inline and retain baseline figure size.
- Dense clusters move to a compact secondary summary axes below the main plot.
- Dense curve markers remain on the curves; dense inline text and leader lines are removed.
- Summary groups are ordered by x. Rows preserve stable series order, exact display label, plotted color, `max`/`min`, and characteristic value.
- x unit is shown once per group; homogeneous y unit is shown once in the value heading.
- Figure width does not grow and the main axes retains its physical size under Agg.
- Canonical six-series summary adds **1.34 in** vertically versus the rejected **1.85 in** bottom-callout band.

## Open issues / user feedback

- Multiline ordinary function-call parsing remains a later ergonomics item.
- `no_vertical_scroll()` Colab ergonomics remains outside the completed characteristic-label correction.
- Piecewise syntax/evaluation is the next approved production milestone.
- Vector/matrix/linear-system support is planned for **0.9.0**. The intended direction is calculator/CAS-style exact symbolic matrices plus numerical matrices, including engineering-aware unit handling; detailed matrix design has not yet been approved or implemented.

## Validation evidence

### Retained release baseline

- EngCalc 0.7.2 engineering tables: distribution-validated and merged before this presentation work.
- Narrative SHA `161bbaba36b93c3d7395790eb6e41284d36c231b`: **464/464 passed**, real-Colab visually validated.
- Presentation-polish SHA `d6fd873e21d5a415a2787bf06fdeceaa1f013e41`: **477/477 passed**, real-Colab visually validated.

### Dense-summary RED→GREEN

- Pre-implementation baseline: **482 passed**.
- Task 1 RED SHA `3117b80f...`: expected collection failure because `_characteristic_requests` did not exist.
- Task 1 GREEN SHA `1c226298...`: **483 passed**.
- Task 2 RED Actions `33297360032`, job `99219218711`: expected collection failure because `_build_dense_summary_groups` did not exist.
- Task 2 GREEN SHA `6a4a9947...`: **484 passed**.
- Visual-contract RED SHA `9559bd25...`: **3 failed, 480 passed**, exactly for retained callouts, rejected 1.85 in expansion, and missing summary axes.
- Product GREEN SHA `a11b0946aad322cb30145a178eda4261f8f1e1de`: **484 passed**.

### Dense-summary final QA

- QA evidence SHA: `44d48065db4b6bad1b5ffbf0fa701478b93d6075`.
- GitHub Actions run `33297891785`, job `99220581598`: **484 passed in 80.05 s**.
- QA artifact ID `9728003251`, digest `sha256:17d512b5c6cf15ade0c5a9fe526c93d4e12f95486e8089684f53fc37401e9ee1`.
- Baseline figure **6.4 × 4.8 in**; presented figure **6.4 × 6.14 in**.
- Main axes unchanged at **548.924 × 379.608 px**.
- 2 dense groups / 12 entries / 41 summary texts.
- **0** text overlaps, **0** out-of-figure texts, **0** dense plot annotations, **0** leader lines.
- Assistant visual QA: PASS.
- User visual acceptance: APPROVED on 2026-08-30.

### Integration and post-merge gate

- Fresh pre-integration rerun on feature SHA `f945a408...`: **484 passed in 66.74 s**.
- PR #30 final feature head before merge: `c3af207ff69067e944a3e5d1634525fb60b6869c`.
- PR #30 merged with the repository's established merge-commit workflow into `main`: merge commit **`1bb1f63606c669605dcccaf011bcf6f20764b2cc`**.
- GitHub compare `c3af207f...1bb1f636`: **zero changed files**.
- A temporary main-only post-merge workflow was added solely for final verification.
- Post-merge Actions `33298959230`, job `99223386831`: **484 passed in 99.80 s** on `main`.
- Temporary post-merge workflow removed in `4dba31ce0ff0b2f6ce665539a28c3f50bd92207f`.
- No product source or product test changes occurred after the post-merge validation tree; only CI cleanup and this context update follow it.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + DISTRIBUTION VALIDATED + MERGED.
- **Narrative text:** COMPLETE + MACHINE GREEN + REAL-COLAB VISUALLY VALIDATED + MERGED.
- **Presentation polish:** COMPLETE + REAL-COLAB VISUALLY VALIDATED + MERGED.
- **Characteristic-point label deconfliction:** COMPLETE + 484/484 GREEN + AUTOMATED QA PASS + USER VISUALLY APPROVED + MERGED.
- **0.8.0 Piecewise:** design/spec/implementation plan COMPLETE; production implementation NOT STARTED.
- **0.8.1 exact-first extrema / roots / intersections:** planned after Piecewise.
- **0.8.2 exact envelopes / governing intervals:** planned.
- **0.8.3 named response cases / combinations:** planned.
- **0.9.0 vectors / matrices / linear systems:** planned. This is the milestone for symbolic and numerical matrix capability approaching a TI-Nspire-CX-CAS-style workflow, subject to a dedicated design/spec gate.
- **0.10.0 engineering verification** and **0.10.1 verification collections:** planned.
- **1.0.0 API stabilization / release engineering:** planned.

## Exact next step

1. Treat `main` as the new authoritative integrated baseline.
2. Start the **0.8.0 Piecewise implementation workflow** from the already approved Piecewise design/spec/plan, but first refresh/create the implementation branch from current `main` so it contains the newly merged presentation work.
3. Execute Piecewise using RED→GREEN TDD with focused tests first, then complete suite and user-facing validation.
4. Do not start matrix production implementation inside Piecewise; matrices remain a separate 0.9.0 milestone unless the user explicitly approves roadmap reprioritization.
5. When matrix work begins, create a dedicated design/spec covering exact symbolic matrices, numerical/unit-aware matrices, rendering, matrix algebra, and linear-system APIs before production changes.
6. Do not invoke Codex unless explicitly authorized.

## How to resume in a new conversation

Read this file first. `main` now contains the previously separate narrative, presentation-polish, and dense characteristic-summary work. PR #30 merged on 2026-08-30 at `1bb1f636...`; the merge tree exactly matched the approved feature head. A fresh main-only post-merge validation then passed **484/484 in 99.80 s** on Actions run `33298959230`, after which the temporary workflow was removed. The next production milestone is **0.8.0 Piecewise**, whose design/spec/implementation plan already exist but whose production implementation has not started. After Piecewise come exact-first analysis (0.8.1), exact envelope intervals (0.8.2), named cases/combinations (0.8.3), then **0.9.0 vectors/matrices/linear systems**, where EngCalc is intended to gain exact symbolic and numerical matrix workflows. Never invoke Codex without explicit authorization.
