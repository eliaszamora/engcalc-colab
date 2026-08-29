# EngCalc Current Project Context

_Last updated: 2026-08-29 — EngCalc 0.7.2 remains canonical on `main`; narrative text blocks are implementation-complete, validated and cleanup-complete on a retained feature branch; Piecewise is the next architectural milestone._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical branch: `main` at pre-feature checkpoint `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`.
- Released package/runtime version: **0.7.2**.
- 0.7.2 authoritative gate: Actions `33266879721`; source **454/454**, installed-wheel source-free **454/454**, repeated source **454/454**, external wheel smoke PASS.
- Completed bounded feature branch: **`feature/v0.8.0-narrative-text`**, retained for user review and not merged.
- Piecewise planning branch: **`planning/v0.8.0-piecewise`**.
- Piecewise spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- Piecewise implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md`.
- 0.7.3 derivation traces remains retired as redundant.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Retain branches unless explicitly asked to delete them; do not merge without explicit user approval.

## Approved behavior

### Narrative text in `%%eng`

- Single-line form: `"""Texto explicativo."""`.
- Multiline form: opening/closing triple double quotes around one or more prose lines.
- Consecutive non-empty lines are joined with spaces into one paragraph.
- A blank line inside the block creates a new paragraph.
- `#`, `##` and `###` inside narrative are literal text; outside the block existing comment/heading behavior is unchanged.
- Narrative is plain text, not Markdown or arbitrary HTML, and is HTML-escaped before display.
- Empty blocks are rejected.
- Unterminated blocks report the opening line.
- Content after closing `"""` on the same line is rejected.
- Narrative is a presentation boundary: pending MathJax equations flush first, prose renders as HTML, and later calculations continue in source order.
- Narrative never enters the symbolic/numeric engine and does not mutate calculation state.
- Feature reference: `docs/narrative-text.md`.

### Existing regression contract

- Preserve all EngCalc 0.7.2 behavior: multi-argument functions, generalized partial evaluation, scalar math, tables, plots/envelopes, source ordering, precision/zero tolerance and positive structural moment downward.
- Package/runtime version remains **0.7.2** during development; version bump occurs only during formal 0.8.0 release closure.

## Open issues / user feedback

- User requested narrative prose for calculation memories; `#>` was rejected and triple-double-quote syntax was selected and approved.
- User prefers routine technical micro-decisions to be analyzed independently rather than requiring repeated approvals.
- Narrative feature is complete but **not merged**.
- Piecewise implementation has **not started**; its design and implementation plan are complete.
- Canonical 0.7.2 README remains unchanged; narrative README integration belongs to the 0.8.0 integration/release path.

## Validation evidence

### Narrative baseline

- Feature branch created from canonical `main` SHA `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`.
- Initial temporary-CI failure was harness-only: existing tests require IPython but `.[dev]` does not install it. Temporary workflow was corrected to install `ipython`; no product code changed for this issue.
- Clean baseline Actions `33272374493`, job `99153080259`: **454/454 passed**, Python 3.13.15.

### Parser RED → GREEN

- RED commit `ee6017c66e0b8675e0f848d0ef3615c79e90b3a2`.
- RED Actions `33272464620`, job `99153315243`: **3 failed, 454 passed**, exactly because narrative parsing did not yet exist.
- Model commit `4d05e98050c5d78e680eea5d7774da0495e7c2c4` added `ParsedNarrative`.
- Parser commit `752361172f7b0794c6a5093260cf3c836e8d5314` added single/multiline narrative capture.
- GREEN Actions `33272662408`, job `99153837821`: **457/457 passed**.
- Diagnostic regression tests commit `34f0c825cf67a03522d2fbb9dba06685a6d93063` covers empty/unterminated/trailing-content and normal parsing resumption.

### Renderer RED → GREEN

- RED commit `66d796d909ed7278268004472b6bc7bdaf1cb83b`.
- RED Actions `33272911228`, job `99154513271`: **3 failed, 461 passed** because `ParsedNarrative` was still sent to the symbolic engine.
- Rendering commit `23e9cd338bff681a6ee0860e963fc8117abfbf92` adds the `%%eng` presentation boundary, paragraph HTML and escaping.
- GREEN Actions `33273056799`, job `99154906458`: **464/464 passed**.
- Documentation commit `7a10809847b8f6d2e71c6ed89e8bab9656feb728` added `docs/narrative-text.md`.

### Authoritative final feature gate and cleanup

- Validated feature SHA: **`161bbaba36b93c3d7395790eb6e41284d36c231b`**.
- Actions **`33273242772`**, job `99155402471`, Python 3.13.15: **464/464 passed**.
- Temporary workflow removed only after success in cleanup commit `47ed2b56fc6908f9a6f15c0aa2ba248ba1ebc7bc`.
- Post-gate compare from validated SHA `161bbaba...` through checkpoint `be47e1035e25ac2c3f5d2f29b6dc6c9eb863defe`: **2 commits; only `.github/workflows/narrative-text-validation.yml` removed and `docs/project-context/CURRENT.md` updated**. No production source, tests, package metadata or functional documentation changed after the 464/464 gate.
- `pyproject.toml` and runtime `__version__` remain **0.7.2**.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE and merged.
- **0.7.3 derivation traces:** RETIRED.
- **Narrative text blocks:** COMPLETE + VALIDATED on retained `feature/v0.8.0-narrative-text`; awaiting user integration decision.
- **0.8.0 Piecewise:** DESIGN + IMPLEMENTATION PLAN COMPLETE; implementation not started.
- **0.8.1:** exact-first extrema, roots and intersections.
- **0.8.2:** exact envelopes and governing intervals.
- **0.8.3:** named response cases/combinations.
- **0.9.0:** vectors, matrices and linear systems.
- **0.10.0:** engineering verification system.
- **0.10.1:** verification collections/summaries.
- **1.0.0:** language/API stabilization and release engineering.

## Exact next step

- Present the completed narrative feature to the user. Do **not** merge yet.
- If the user wants hands-on verification, install `feature/v0.8.0-narrative-text` directly in Colab and test the short and multiline forms.
- After explicit integration approval, integrate narrative text into the 0.8.0 baseline, update Piecewise Task 0 to inherit the 464-test narrative suite, and begin Piecewise implementation under its approved plan.
- Keep version `0.7.2` until formal 0.8.0 release closure.

## How to resume in a new conversation

Read this file first. Released `main` is EngCalc 0.7.2 at pre-feature checkpoint `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`. Narrative `"""..."""` blocks are fully implemented on retained branch `feature/v0.8.0-narrative-text` with parser and renderer RED→GREEN evidence and an authoritative **464/464** final gate at SHA `161bbaba36b93c3d7395790eb6e41284d36c231b`; only CI cleanup/context bookkeeping occurred afterward. The feature is not merged. Piecewise remains on `planning/v0.8.0-piecewise`, with approved spec and plan but no production implementation. Never invoke Codex without explicit authorization and never merge without explicit user approval.
