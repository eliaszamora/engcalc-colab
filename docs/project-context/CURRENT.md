# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 Piecewise is fully integrated into `main` through merged PR #31. The authoritative release product remains `7a3c4206002d26145ea3cd36a21d2dcfefe0914f`; the final pre-merge HEAD was freshly revalidated at 557/557 GREEN, and the merge commit tree was proven file-identical to that cleaned HEAD. The next milestone is the 0.9.0 vectors/matrices/linear-systems design/spec gate; no Matrix/CAS production work has started._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated branch: **`main`**.
- EngCalc runtime/package version on `main`: **0.8.0**.
- PR #31 — `release: EngCalc 0.8.0 piecewise expressions`: **MERGED**.
- Merge commit: **`eca248c376128da16ff9526751790aebe2089646`**.
- Final cleaned PR head merged into `main`: **`df11f1ecb7e8c1029f7ccdc0061722793b2a6b39`**.
- Authoritative distribution-validated 0.8.0 product commit: **`7a3c4206002d26145ea3cd36a21d2dcfefe0914f`**.
- Approved Piecewise spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- Approved Piecewise implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md`.
- No temporary Piecewise validation workflow remains in the integrated release tree.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.

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

## Open issues / user feedback

- Multiline ordinary function-call parsing remains a later ergonomics item.
- `no_vertical_scroll()` Colab ergonomics remains outside Piecewise.
- Piecewise 0.8.0 intentionally excludes arbitrary boolean conditions, endpoint glyphs/jump markers, `solve(piecewise(...))`, exact Piecewise roots/intersections, exact governing-interval envelopes, arbitrary Python and automatic differentiability proofs.
- Matrix/CAS production work remains pending its own design/spec gate.
- Auxiliary branch `noop` is non-product and contains no unique feature work; it may be removed manually from GitHub if desired.

## Validation evidence

- Integrated pre-Piecewise `main`: **484/484 GREEN** on Actions `33298959230`; isolated Piecewise baseline `33299317560`: **484/484 GREEN**.
- Task 1 through Task 7 progressed GREEN through 506, 518, 526, 530, 536, 542 and 547 tests respectively.
- Task 8 product `d0ff122b3f5f4681214fdbe6059c860c3bb11f54`; Actions `33315071844`: **14/14 acceptance**, **66/66 Piecewise**, **557/557 full GREEN in 113.99 s**.
- Authoritative Task 9 distribution gate: Actions **`33316141809`**, job `99269839966`, Python **3.13.15**:
  - release contracts: **23/23 GREEN**;
  - source before wheel: **557/557 GREEN in 77.13 s**;
  - wheel: **`engcalc_colab-0.8.0-py3-none-any.whl`**, metadata `Version: 0.8.0`;
  - clean venv installation and source-external `site-packages` smoke: GREEN;
  - installed-wheel/source-free suite: **557/557 GREEN in 75.40 s**;
  - source recheck: **557/557 GREEN in 74.75 s**;
  - wheel SHA-256: **`e200b45de358d8c2ee83f6a4fc945913cd0fc1709ce9ad5ffdfc1f727469055a`**;
  - artifact: **`engcalc-colab-0.8.0-release-v3`**, ID **`9733556162`**.
- Fresh pre-merge gate after all documentation/cleanup work: Actions **`33316786989`**, commit **`8628023f6654e9b5aeb9b1aaaf68dd43738fd353`**, Python 3.13.15: runtime version 0.8.0 GREEN and **557/557 GREEN in 116.63 s**.
- The only change from that freshly tested SHA to final PR head `df11f1ec...` was deletion of `.github/workflows/pr31-premerge-validation.yml`; no product/source/test/docs change occurred in that cleanup commit.
- Post-merge equality gate: compare `df11f1ec...` → merge commit `eca248c3...` reports **zero changed files**, proving the integrated merge tree is file-identical to the cleaned PR head.
- `main/src/engcalc_colab/__init__.py` reports **`__version__ = "0.8.0"`** after merge.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** **COMPLETE + MERGED to `main` via PR #31**.
- **0.9.0 vectors / matrices / linear systems:** NEXT MAJOR MILESTONE; design/spec gate required before production implementation.
- Later roadmap: 0.9.1 exact-first extrema/roots/intersections → 0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization.

## Exact next step

1. Treat EngCalc 0.8.0 Piecewise as closed and integrated.
2. Start a dedicated 0.9.0 vectors/matrices/linear-systems design exploration and written spec.
3. Do not begin Matrix/CAS production code until that spec is explicitly approved.
4. Keep later exact-analysis milestones separate from the 0.9.0 matrix/CAS scope.

## How to resume in a new conversation

Read this file first. EngCalc 0.8.0 Piecewise is integrated into `main` via merged PR #31 at merge commit `eca248c376128da16ff9526751790aebe2089646`; runtime/package version is 0.8.0. The distribution-validated release product is `7a3c4206002d26145ea3cd36a21d2dcfefe0914f`, with wheel SHA-256 `e200b45de358d8c2ee83f6a4fc945913cd0fc1709ce9ad5ffdfc1f727469055a`. Fresh pre-merge Actions `33316786989` passed 557/557 on the final product tree, and the merge-tree equality audit found zero file differences versus the cleaned PR head. The next work is 0.9.0 vectors/matrices/linear systems at design/spec stage only; no production implementation until explicit approval.