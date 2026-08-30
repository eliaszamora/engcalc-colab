# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 Piecewise is implemented, distribution-validated, cleaned, and proposed to `main` in PR #31. The authoritative release product is `7a3c4206002d26145ea3cd36a21d2dcfefe0914f`: 557/557 source GREEN, 557/557 installed-wheel/source-free GREEN, 557/557 source recheck GREEN, and clean `site-packages` smoke GREEN. The release PR is open and intentionally unmerged pending explicit user approval._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated branch: `main` at **`79befeeb07364f4b6b78d2e6e55ad40258ef0da2`**.
- Release branch: **`feature/v0.8.0-piecewise`**.
- Validated 0.8.0 product commit: **`7a3c4206002d26145ea3cd36a21d2dcfefe0914f`** (`release: bump EngCalc to 0.8.0`).
- Package/runtime version on the release branch: **0.8.0**.
- Release PR: **#31 — `release: EngCalc 0.8.0 piecewise expressions`**, head `feature/v0.8.0-piecewise`, base `main`, open and not merged.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- Approved implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md`.
- All temporary Piecewise release-validation workflows were removed after successful validation.
- An accidentally-created auxiliary branch `noop` was immediately neutralized to point exactly at `main@79befeeb...`; it contains no unique commits. The available GitHub connector does not expose branch-ref deletion.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge PR #31 without explicit user approval.

## Approved behavior

### Existing behavior preserved

- `%%eng` narrative and presentation polish remain integrated.
- `plot(...)` / `envelope(...)` retain approved `title`, `xlabel`, `ylabel` overrides.
- Dense characteristic clusters use the accepted compact summary; sparse clusters remain inline.
- Positive structural moment remains plotted downward.
- Multi-argument functions, partial numeric evaluation, scalar math and engineering tables remain compatible.

### 0.8.0 Piecewise contract

- Public form: `piecewise(value_1, condition_1, ..., default_value)` with a mandatory default.
- Conditions use one direct interval-variable `<`, `<=`, `>` or `>=` comparison against a breakpoint expression that does not contain that variable.
- SymPy `Piecewise`/relational objects are symbolic truth; Pint is numerical/unit truth.
- Compatible comparison units normalize; incompatible dimensions produce Piecewise-specific diagnostics.
- Fully numeric evaluation visits branches in source order and evaluates only the governing branch.
- Exact dimensionless zero can inherit a compatible dimensional response unit.
- Partial `numeric(q(x))` retains the interval variable and renders native Piecewise cases; `result(...)` uses the same final representation without the substitution stage.
- Tables preserve exactly the requested row count and do not add hidden breakpoint rows.
- Plot/envelope keeps the 201-point base grid and augments it with exact numerically resolvable breakpoints; multi-series/sweeps/envelopes use a shared union grid.
- Lines/fills split at actual Piecewise branch transitions, preserving endpoint ownership and avoiding fictitious jump connectors.
- `diff(...)` remains branchwise without public `DiracDelta`; derivative-origin functions reject numeric evaluation exactly at explicit Piecewise breakpoints.
- Supported Piecewise integral outputs containing internal `Piecewise`, `Min` or `Max` remain numerically evaluable.
- Real `%%eng` acceptance preserves source order across MathJax groups, HTML tables and figures.

### Approved roadmap reprioritization

- After Piecewise integration, EngCalc prioritizes a calculator/CAS-style **vectors, matrices and linear-systems** milestone.
- Matrix/CAS requires its own design/spec gate and must not be mixed into PR #31.
- Roadmap: `0.8.0 Piecewise` → `0.9.0 vectors/matrices/linear systems` → `0.9.1 exact-first extrema/roots/intersections` → `0.9.2 exact envelopes/governing intervals` → `0.9.3 named response cases/combinations` → `0.10.x engineering verification` → `1.0.0` stabilization.

## Open issues / user feedback

- Multiline ordinary function-call parsing remains a later ergonomics item.
- `no_vertical_scroll()` Colab ergonomics remains outside Piecewise.
- Piecewise 0.8.0 intentionally excludes arbitrary boolean conditions, endpoint glyphs/jump markers, `solve(piecewise(...))`, exact Piecewise roots/intersections, exact governing-interval envelopes, arbitrary Python and automatic differentiability proofs.
- Matrix/CAS production work remains pending its own design/spec after Piecewise integration.
- Auxiliary branch `noop` is harmless and has no unique history but may be deleted manually in GitHub UI if desired.

## Validation evidence

- Integrated pre-Piecewise `main`: **484/484 GREEN** on Actions `33298959230`; isolated Piecewise baseline `33299317560`: **484/484 GREEN**.
- Task 1: `a935dd7d9c2bb786caede1bb28274fde28bb77f8`, **506/506 GREEN**.
- Task 2: `3429f6d628a1ede348581e1d1d323680e5a50a39`, cleaned `6410219e55f35bf119500d3ac760898a566a89d4`, **518/518 GREEN**.
- Task 3: `04b9770e317578e157cd715e836efc4e1cc10f72`, **526/526 GREEN**.
- Task 4: `c0beb86cac875d272a91de01371330bf79a82569`, **530/530 GREEN**.
- Task 5: `606e7ba`, **536/536 GREEN**.
- Task 6: `ebef3b9a4d78695bf29d4530cc06488a0ce49836`, **542/542 GREEN**.
- Task 7: `34358fd94e27e99180cdd49074df4e5c473d202b`, **547/547 GREEN**.
- Task 8: `d0ff122b3f5f4681214fdbe6059c860c3bb11f54`; Actions `33315071844`: **14/14 acceptance**, **66/66 Piecewise**, **557/557 full GREEN in 113.99 s**.
- Task 9 initial run `33315402367` correctly found one stale 0.7.2 parser-version assertion; no wheel was accepted from that failed run.
- Task 9 v2 `33315620355` passed the product/distribution gates; its push failed only because the temporary commit attempted to modify a workflow without `workflows` permission.
- **Authoritative Task 9 release gate:** Actions **`33316141809`**, job `99269839966`, Python **3.13.15**:
  - version RED: **7 failed / 4 passed** as expected;
  - release contracts: **23/23 GREEN**;
  - source before wheel: **557/557 GREEN in 77.13 s**;
  - wheel: **`engcalc_colab-0.8.0-py3-none-any.whl`**, metadata `Version: 0.8.0`;
  - clean venv installation: GREEN;
  - source-external `site-packages` smoke: GREEN;
  - installed-wheel/source-free suite: **557/557 GREEN in 75.40 s**;
  - source recheck: **557/557 GREEN in 74.75 s**;
  - validated product SHA: **`7a3c4206002d26145ea3cd36a21d2dcfefe0914f`**;
  - committed-tree release contracts: **23/23 GREEN**;
  - wheel SHA-256: **`e200b45de358d8c2ee83f6a4fc945913cd0fc1709ce9ad5ffdfc1f727469055a`**;
  - artifact: **`engcalc-colab-0.8.0-release-v3`**, ID **`9733556162`**.
- Post-validation compare from `7a3c420...` confirmed that cleanup changed only three temporary workflow files plus `CURRENT.md`; no `src/`, product-test, README or package-metadata changes occurred after validation.
- Final feature-vs-main audit reports 28 changed files, all within approved Piecewise implementation/tests/docs/version scope and no Matrix/CAS production files or temporary workflows.
- PR #31 was opened against the exact expected base `main@79befeeb...`; it remains unmerged.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** IMPLEMENTATION + RELEASE VALIDATION COMPLETE; **PR #31 OPEN**.
  - Tasks 0–9: COMPLETE.
  - Validated release product: `7a3c4206002d26145ea3cd36a21d2dcfefe0914f`.
  - Release PR: #31.
  - Merge: **BLOCKED pending explicit user approval**.
- **0.9.0 vectors / matrices / linear systems:** next major milestone after Piecewise integration; design/spec gate required.
- Later roadmap: 0.9.1 exact-first analysis → 0.9.2 exact envelopes → 0.9.3 response cases → 0.10.x verification → 1.0.0.

## Exact next step

1. Stop at open PR #31.
2. Await explicit user decision on whether to merge PR #31 into `main`.
3. If merge is explicitly approved, verify PR head/base/check state immediately before merging, merge only the approved PR, then run/inspect the post-merge `main` validation before declaring 0.8.0 integrated.
4. Only after Piecewise integration is closed may the 0.9.0 Matrix/CAS design/spec workflow begin.

## How to resume in a new conversation

Read this file first. EngCalc 0.8.0 Piecewise is fully implemented and distribution-validated on `feature/v0.8.0-piecewise`. Authoritative product: `7a3c4206002d26145ea3cd36a21d2dcfefe0914f`; Actions `33316141809` verified 557/557 source, 557/557 installed-wheel/source-free, 557/557 source recheck, and clean `site-packages` smoke. Wheel SHA-256: `e200b45de358d8c2ee83f6a4fc945913cd0fc1709ce9ad5ffdfc1f727469055a`; artifact ID `9733556162`. Temporary workflows are removed. PR #31 is open against `main` and must not be merged without explicit user approval. The auxiliary `noop` branch points exactly to `main` and has no unique commits.