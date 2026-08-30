# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 Piecewise implementation and distribution validation are complete on `feature/v0.8.0-piecewise`. The authoritative release candidate is `7a3c4206002d26145ea3cd36a21d2dcfefe0914f`: source 557/557 GREEN, installed-wheel/source-free 557/557 GREEN, source recheck 557/557 GREEN, clean `site-packages` smoke GREEN. Temporary release harnesses have been removed. The exact next step is to open the release PR to `main` and stop before merge pending explicit user approval._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated branch: `main` at **`79befeeb07364f4b6b78d2e6e55ad40258ef0da2`**.
- Current implementation/release branch: **`feature/v0.8.0-piecewise`**.
- Feature branch base: **`main@79befeeb07364f4b6b78d2e6e55ad40258ef0da2`**.
- Authoritative validated 0.8.0 release product commit: **`7a3c4206002d26145ea3cd36a21d2dcfefe0914f`** (`release: bump EngCalc to 0.8.0`).
- Package/runtime version is now **0.8.0** on the feature branch.
- Approved Piecewise spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- Approved Piecewise implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md`.
- All temporary Piecewise release-validation workflows have been removed after successful validation.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge the release PR to `main` without explicit user approval.

## Approved behavior

### Existing behavior preserved

- `%%eng` narrative and presentation polish remain integrated.
- `plot(...)` / `envelope(...)` retain approved `title`, `xlabel`, `ylabel` overrides.
- Dense characteristic clusters use the accepted compact summary; sparse clusters remain inline.
- Positive structural moment remains plotted downward.
- Multi-argument functions, partial numeric evaluation, scalar math and engineering tables remain compatible.

### 0.8.0 Piecewise contract

- Public form: `piecewise(value_1, condition_1, ..., default_value)` with a mandatory default.
- Conditions use one direct interval-variable `<`, `<=`, `>` or `>=` comparison against a breakpoint expression that does not contain that interval variable.
- SymPy `Piecewise`/relational objects remain symbolic truth; Pint remains numerical/unit truth.
- Compatible condition units are normalized; incompatible dimensions raise Piecewise-specific engineering diagnostics.
- Fully numeric evaluation visits branches in source order and evaluates only the governing response branch.
- Exact dimensionless zero can inherit a compatible dimensional response unit.
- Partial `numeric(q(x))` retains the interval variable and renders native Piecewise cases; `result(...)` uses the same final representation without the substitution stage.
- Tables preserve exactly the requested row count and do not add hidden breakpoint rows.
- Plot/envelope retains the 201-point base grid and augments it with exact numerically resolvable breakpoints; multi-series/sweeps/envelopes share the union grid.
- Plot lines/fills split at actual Piecewise branch transitions, preserving endpoint ownership without fictitious jump connectors.
- `diff(...)` is branchwise with no public `DiracDelta`; derivative-origin functions are rejected exactly at explicit Piecewise breakpoints.
- Supported Piecewise integral outputs containing internal `Piecewise`, `Min` or `Max` remain numerically evaluable.
- Real `%%eng` acceptance preserves source order across equation groups, HTML tables and figures.

### Approved roadmap reprioritization

- After Piecewise, EngCalc prioritizes a **calculator/CAS-style vectors, matrices and linear-systems milestone**.
- Matrix/CAS requires a dedicated design/spec gate and must not be mixed into the Piecewise release branch before integration.
- Working roadmap: `0.8.0 Piecewise` → `0.9.0 vectors/matrices/linear systems` → `0.9.1 exact-first extrema/roots/intersections` → `0.9.2 exact envelopes/governing intervals` → `0.9.3 named response cases/combinations` → `0.10.x engineering verification` → `1.0.0` stabilization.

## Open issues / user feedback

- Multiline ordinary function-call parsing remains a later ergonomics item.
- `no_vertical_scroll()` Colab ergonomics remains outside Piecewise.
- Piecewise 0.8.0 intentionally excludes arbitrary boolean condition logic, endpoint glyphs/jump markers, `solve(piecewise(...))`, exact Piecewise roots/intersections, exact governing-interval envelopes, arbitrary Python and automatic differentiability proofs.
- Matrix/CAS production work remains pending its own design/spec after Piecewise is integrated.

## Validation evidence

- Integrated `main` pre-Piecewise baseline: **484/484 GREEN** on Actions `33298959230`; Piecewise isolated baseline `33299317560`: **484/484 GREEN** on Python 3.13.15.
- Task 1 symbolic construction: product `a935dd7d9c2bb786caede1bb28274fde28bb77f8`; **506/506 GREEN**.
- Task 2 numeric Piecewise/relations/zero inheritance/MinMax: product `3429f6d628a1ede348581e1d1d323680e5a50a39`; cleaned checkpoint `6410219e55f35bf119500d3ac760898a566a89d4`; **518/518 GREEN**.
- Task 3 partial numeric + native Piecewise rendering: product `04b9770e317578e157cd715e836efc4e1cc10f72`; **526/526 GREEN**.
- Task 4 Piecewise tables: cleaned checkpoint `c0beb86cac875d272a91de01371330bf79a82569`; **530/530 GREEN**.
- Task 5 enriched shared plot grids: product `606e7ba`; **536/536 GREEN**.
- Task 6 segmented plotting: product `ebef3b9a4d78695bf29d4530cc06488a0ce49836`; **542/542 GREEN**.
- Task 7 Piecewise calculus: product `34358fd94e27e99180cdd49074df4e5c473d202b`; **547/547 GREEN**.
- Task 8 acceptance/diagnostics/docs: product `d0ff122b3f5f4681214fdbe6059c860c3bb11f54`; Actions `33315071844`: **14/14 acceptance**, **66/66 Piecewise**, **557/557 full GREEN in 113.99 s**.
- Task 9 initial release gate `33315402367`: correctly exposed one stale `tests/test_parser.py` 0.7.2 version assertion; no wheel was accepted from that failed run.
- Task 9 v2 `33315620355`: product/distribution gates all passed but the runner push was rejected only because the temporary commit attempted to update a workflow without `workflows` permission. The candidate itself passed source, wheel and source-free validation.
- **Authoritative Task 9 gate:** Actions **`33316141809`**, job `99269839966`, Python **3.13.15**.
  - version RED before bump: **7 failed / 4 passed** as expected;
  - release contracts after bump: **23/23 GREEN**;
  - complete source suite before wheel: **557/557 GREEN in 77.13 s**;
  - wheel built: **`engcalc_colab-0.8.0-py3-none-any.whl`**, metadata `Version: 0.8.0`;
  - clean virtual environment installation: GREEN;
  - source-external smoke imported from `/tmp/engcalc-wheel-venv/lib/python3.13/site-packages/engcalc_colab/__init__.py`: GREEN;
  - complete source-free suite against installed wheel: **557/557 GREEN in 75.40 s**;
  - repeated complete source suite: **557/557 GREEN in 74.75 s**;
  - committed release product: **`7a3c4206002d26145ea3cd36a21d2dcfefe0914f`**;
  - committed-tree release contracts: **23/23 GREEN**;
  - wheel SHA-256: **`e200b45de358d8c2ee83f6a4fc945913cd0fc1709ce9ad5ffdfc1f727469055a`**;
  - Actions artifact: **`engcalc-colab-0.8.0-release-v3`**, artifact ID **`9733556162`**.
- Release harness cleanup after `7a3c420...` removed only the temporary workflow files. Product source/tests/README/version metadata remain identical to the validated release candidate.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** IMPLEMENTATION + RELEASE VALIDATION COMPLETE; PR GATE NEXT.
  - Tasks 0–8: COMPLETE.
  - Task 9 version/distribution validation: COMPLETE.
  - Release candidate: `7a3c4206002d26145ea3cd36a21d2dcfefe0914f`.
  - Release PR to `main`: NEXT.
  - Merge: BLOCKED pending explicit user approval.
- **0.9.0 vectors / matrices / linear systems:** NEXT MAJOR MILESTONE AFTER Piecewise integration; design/spec gate required.
- Later roadmap: 0.9.1 exact-first analysis → 0.9.2 exact envelopes → 0.9.3 response cases → 0.10.x verification → 1.0.0.

## Exact next step

1. Compare the validated release SHA `7a3c4206002d26145ea3cd36a21d2dcfefe0914f` with the current cleanup HEAD and verify that all post-validation changes are limited to temporary workflow deletion plus this `CURRENT.md` update.
2. Verify the feature branch remains based on `main@79befeeb07364f4b6b78d2e6e55ad40258ef0da2` and inspect the final feature-vs-main diff for unintended files.
3. Open a PR targeting `main` titled **`release: EngCalc 0.8.0 piecewise expressions`**, summarizing Piecewise scope and the authoritative wheel/source-free evidence.
4. Stop at the open PR. **Do not merge without explicit user approval.**

## How to resume in a new conversation

Read this file first. `feature/v0.8.0-piecewise` contains the validated EngCalc 0.8.0 release. The authoritative release product is `7a3c4206002d26145ea3cd36a21d2dcfefe0914f`, validated by Actions `33316141809`: 557/557 source, 557/557 installed-wheel/source-free, 557/557 source recheck, with clean `site-packages` smoke. Wheel: `engcalc_colab-0.8.0-py3-none-any.whl`, SHA-256 `e200b45de358d8c2ee83f6a4fc945913cd0fc1709ce9ad5ffdfc1f727469055a`, artifact ID `9733556162`. Temporary release workflows were removed after validation. The next action is final diff audit and opening the release PR to `main`; do not merge without explicit user approval and do not start matrix/CAS production work on this branch.