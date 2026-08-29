# EngCalc Current Project Context

_Last updated: 2026-08-29 — EngCalc 0.7.2 remains canonical on `main`; narrative text blocks are implemented and validated on a separate pre-0.8.0 feature branch; Piecewise remains the next architectural milestone._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical branch: `main`.
- Canonical `main` checkpoint before current feature work: `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`.
- Released package/runtime version: **0.7.2**.
- 0.7.2 authoritative final distribution gate: Actions `33266879721`; source **454/454**, installed-wheel source-free **454/454**, repeated source **454/454**, external wheel smoke PASS.
- Active bounded feature branch: **`feature/v0.8.0-narrative-text`**, created directly from canonical `main`.
- Active architectural planning branch: **`planning/v0.8.0-piecewise`**.
- Formal Piecewise spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- Piecewise implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md`.
- 0.7.3 derivation traces remains retired as redundant because `numeric(...)` already provides formula → substitution → result and `result(...)` provides formula → result.
- Do not invoke Codex, `@codex review`, Codex Cloud or anything that may consume Codex quota without explicit user authorization.
- Retain branches unless the user explicitly requests deletion.
- Do not merge feature/planning work without explicit user approval.

## Approved behavior

### Existing 0.7.2 regression baseline

- Preserve multi-argument functions, generalized partial numerical evaluation, scalar math, native tables, sampled plots/envelopes, source-order rendering, precision/zero tolerance and positive structural moment plotted downward.
- Package/runtime version stays `0.7.2` during pre-release development; version changes only during formal release closure.

### Narrative text in `%%eng`

- Narrative prose is delimited by triple double quotes.
- Single-line form is valid: `"""Texto explicativo."""`.
- Multiline form is valid with delimiters on their own lines.
- Consecutive non-empty lines inside one block are joined with spaces into one paragraph.
- A blank line inside a block starts a new paragraph.
- `#`, `##` and `###` inside a narrative block are literal text, not comments/headings.
- Outside narrative blocks, existing `#` comments and `##` / `###` headings retain their existing behavior.
- Narrative text is plain text, not Markdown and not arbitrary HTML.
- User narrative content is HTML-escaped before rendering.
- Empty narrative blocks are rejected.
- Unterminated blocks report the line where the narrative block started.
- Non-whitespace content after a closing `"""` on the same line is rejected.
- Narrative blocks are presentation boundaries: pending equations render before the prose, then later calculations continue in source order.
- Narrative blocks do not enter the symbolic/numeric engine and do not mutate calculation state.
- User-facing feature reference on this branch: `docs/narrative-text.md`.

### Piecewise direction after narrative integration

- 0.8.0 Piecewise design is globally approved and formally planned.
- Narrative text is intentionally a separate bounded presentation feature and does not alter Piecewise grammar or numeric semantics.
- Once narrative text is accepted/integrated, the Piecewise execution baseline should include these narrative tests as part of the inherited regression suite.

## Open issues / user feedback

- User explicitly requested explanatory prose in calculation memories, not only headings/subheadings.
- Initial `#>` syntax was rejected as visually unnatural; triple-double-quote syntax was selected and approved.
- User wants routine technical micro-decisions analyzed independently rather than requiring repeated approvals.
- Narrative feature is implemented on its feature branch but **not merged** to `main`.
- Piecewise implementation has **not started**; only its design/spec/implementation plan exist.
- README on canonical 0.7.2 is intentionally not changed by this pre-release feature. Public release documentation should be integrated when the feature becomes part of the 0.8.0 baseline.

## Validation evidence

### 0.7.2 release baseline

- Release PR #29 merged successfully.
- Canonical package/runtime version: `0.7.2`.
- Authoritative Actions `33266879721`, Python 3.13.15: source **454/454**, installed-wheel source-free **454/454**, repeated source **454/454**, external smoke PASS.
- Wheel SHA-256: `bb7ece9ee102f3909cf78b53e99ff46f2229053372e7446bede2af321ae621cf`.

### Narrative feature baseline

- Feature branch created from `main` SHA `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`.
- Temporary validation harness initially exposed only a harness dependency issue: existing tests import IPython but `.[dev]` does not install it. The temporary workflow was corrected to install `ipython`; no product code was changed for that issue.
- Clean feature baseline Actions `33272374493`, job `99153080259`: **454/454 passed** on Python 3.13.15.

### Narrative parser TDD

- RED tests commit: `ee6017c66e0b8675e0f848d0ef3615c79e90b3a2`.
- RED Actions `33272464620`, job `99153315243`: **3 failed, 454 passed**. Failures were exactly the missing narrative parser capability.
- Model commit: `4d05e98050c5d78e680eea5d7774da0495e7c2c4` adds `ParsedNarrative`.
- Parser implementation commit: `752361172f7b0794c6a5093260cf3c836e8d5314`.
- GREEN Actions `33272662408`, job `99153837821`: **457/457 passed**.
- Parser diagnostic regression tests commit: `34f0c825cf67a03522d2fbb9dba06685a6d93063`; workflow succeeded with the complete suite.

### Narrative renderer TDD

- Rendering RED tests commit: `66d796d909ed7278268004472b6bc7bdaf1cb83b`.
- RED Actions `33272911228`, job `99154513271`: **3 failed, 461 passed**. Failures showed `ParsedNarrative` was still being sent to the symbolic engine.
- Rendering implementation commit: `23e9cd338bff681a6ee0860e963fc8117abfbf92`.
- GREEN Actions `33273056799`, job `99154906458`: **464/464 passed**.
- The GREEN suite covers source order, HTML escaping, paragraph rendering, parser forms/diagnostics and all inherited 0.7.2 tests.
- Feature reference documentation commit: `7a10809847b8f6d2e71c6ed89e8bab9656feb728`.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE, distribution-validated and merged.
- **0.7.3 derivation traces:** RETIRED / no release.
- **Narrative text blocks:** IMPLEMENTED on `feature/v0.8.0-narrative-text`; final branch validation/cleanup pending, then user review before any integration.
- **0.8.0 Piecewise:** DESIGN + IMPLEMENTATION PLAN COMPLETE; implementation not started.
- **0.8.1:** exact-first extrema, roots and intersections.
- **0.8.2:** exact envelopes and governing intervals.
- **0.8.3:** named response cases/combinations.
- **0.9.0:** vectors, matrices and linear systems.
- **0.10.0:** engineering verification system.
- **0.10.1:** verification collections/summaries.
- **1.0.0:** language/API stabilization and release engineering.

## Exact next step

1. Run a fresh complete narrative-feature validation after this checkpoint/documentation state.
2. If green, remove the temporary `.github/workflows/narrative-text-validation.yml` harness in a cleanup-only commit.
3. Compare the validated product/docs SHA to cleanup HEAD and prove no product/test behavior changed after the gate.
4. Present the retained feature branch to the user for review; do not merge without explicit approval.
5. After user approves integration, make narrative text part of the inherited 0.8.0 baseline and then start Piecewise Task 0 under its approved implementation plan.
6. Keep package/runtime version at `0.7.2` until formal 0.8.0 release closure.

## How to resume in a new conversation

Read this file first. The released baseline is EngCalc 0.7.2 on `main` at the pre-feature checkpoint `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`, with authoritative 454-test wheel validation. The user requested narrative prose inside `%%eng` and approved triple-double-quote blocks. That bounded feature is implemented on `feature/v0.8.0-narrative-text`; parser and renderer both have explicit RED→GREEN evidence and the latest product GREEN gate is 464/464. Final branch validation/temporary-workflow cleanup remain before user review. Piecewise remains separate on `planning/v0.8.0-piecewise`; its spec and implementation plan are complete but no Piecewise production work has started. Never invoke Codex without explicit authorization and never merge without explicit user approval.
