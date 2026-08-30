# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.8.0 Piecewise Tasks 1–8 are complete on `feature/v0.8.0-piecewise`. Acceptance is GREEN with 557/557 tests while package/runtime intentionally remain 0.7.2. Task 9 is next: version bump to 0.8.0, real wheel build, clean-environment/source-free distribution validation, final evidence, and a release PR to `main` without merging until explicit user approval._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated branch: `main`.
- Current implementation branch: **`feature/v0.8.0-piecewise`**.
- Feature branch base: **`main@79befeeb07364f4b6b78d2e6e55ad40258ef0da2`**.
- Latest accepted Piecewise product commit before harness cleanup: **`d0ff122b3f5f4681214fdbe6059c860c3bb11f54`**.
- Latest branch checkpoint before this context update: **`ce1f7c69c3497f97db8fe9474273ac67acf744b0`** (Task 8 harness cleanup only after the accepted product commit).
- Package/runtime version remains **0.7.2** until Task 9 release closure.
- Approved Piecewise spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- Approved Piecewise implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md`.
- Temporary branch validation CI: `.github/workflows/v080-piecewise-validation.yml`; Task-specific write-capable harnesses are removed after each completed task.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge the release PR to `main` without explicit user approval.

## Approved behavior

### Existing baseline that Piecewise preserves

- `%%eng` narrative and presentation polish remain integrated.
- `plot(...)` / `envelope(...)` retain approved `title`, `xlabel`, `ylabel` overrides.
- Dense characteristic clusters use the accepted compact summary; sparse clusters remain inline.
- Positive structural moment remains plotted downward.
- Multi-argument functions, partial numeric evaluation, scalar math and engineering tables remain compatible.

### 0.8.0 Piecewise contract

- Primary form: `piecewise(value_1, condition_1, ..., default_value)` with a mandatory default.
- Conditions are restricted to one direct interval-variable comparison using `<`, `<=`, `>`, or `>=` against a breakpoint expression that does not contain that interval variable.
- General boolean/chained Piecewise logic remains out of scope.
- SymPy `Piecewise`/relational objects are the symbolic source of truth; Pint remains the numeric/unit source of truth.
- Numeric comparisons convert compatible units; incompatible dimensions are rejected with Piecewise-specific diagnostics.
- Exact dimensionless zero may inherit a compatible dimensional response unit; nonzero dimensional mismatches remain invalid.
- Fully numeric Piecewise evaluation visits conditions in source order and evaluates only the governing branch.
- Partial `numeric(q(x))` retains the interval variable and exposes structured branch payload for native MathJax cases; `result(...)` uses the same final representation without the substitution stage.
- Tables preserve exactly the requested row count; breakpoints do not add table rows.
- Plot/envelope retains the 201-point base grid and augments it with exact numerically resolvable Piecewise breakpoints; multi-series/sweep/envelope use the union on one shared grid.
- Plot lines and fills split at actual Piecewise branch transitions. `<` and `<=` endpoint ownership are preserved and no fictitious jump connector is drawn.
- `diff(...)` is branchwise and does not expose `DiracDelta`; `numeric(...)` rejects evaluation exactly at every explicit Piecewise breakpoint of a derivative-origin function.
- Supported Piecewise integral outputs containing internal `Piecewise`, `Min` or `Max` remain numerically evaluable.
- Real `%%eng` acceptance preserves source order across equation groups, HTML tables and figures.

### Approved roadmap reprioritization

- After Piecewise, EngCalc will prioritize a **calculator/CAS-style vectors, matrices and linear-systems milestone** before exact-analysis milestones.
- That matrix milestone requires a dedicated design/spec gate and must not be mixed into the Piecewise branch.
- Working roadmap: `0.8.0 Piecewise` → `0.9.0 vectors/matrices/linear systems` → `0.9.1 exact-first extrema/roots/intersections` → `0.9.2 exact envelopes/governing intervals` → `0.9.3 named response cases/combinations` → `0.10.x engineering verification` → `1.0.0` stabilization.

## Open issues / user feedback

- Multiline ordinary function-call parsing remains a later ergonomics item.
- `no_vertical_scroll()` Colab ergonomics remains outside Piecewise.
- Matrix/CAS production work must not be mixed into this branch.
- Piecewise 0.8.0 intentionally excludes arbitrary boolean condition logic, endpoint glyphs, `solve(piecewise(...))`, exact Piecewise roots/intersections, exact governing-interval envelopes, arbitrary Python and automatic differentiability proofs.
- Task 9 still has to prove distribution integrity against the actual built wheel, not merely the source tree.

## Validation evidence

- Integrated `main` post-PR-#30 gate: **484/484 passed in 99.80 s** on Actions `33298959230`.
- Piecewise baseline on Python 3.13.15: **484/484 passed in 85.83 s** on Actions `33299317560`; package version 0.7.2.
- Task 1 restricted grammar + symbolic construction: product `a935dd7d9c2bb786caede1bb28274fde28bb77f8`; **506/506 GREEN**.
- Task 2 Pint-aware relations/numeric Piecewise/zero inheritance/restricted MinMax: product `3429f6d628a1ede348581e1d1d323680e5a50a39`; cleaned checkpoint `6410219e55f35bf119500d3ac760898a566a89d4`; **518/518 GREEN**.
- Task 3 structured partial numeric + native Piecewise renderer: RED **6 failed / 520 passed**; product **`04b9770e317578e157cd715e836efc4e1cc10f72`**; clean gate **526/526 GREEN**.
- Task 4 Piecewise tables: four new regression contracts fixed/persisted without redundant production changes; cleaned checkpoint **`c0beb86cac875d272a91de01371330bf79a82569`**; Actions `33301799234`: **530/530 GREEN in 107.09 s**.
- Task 5 enriched shared plot grids: corrected RED **5 failed / 1 passed**; focused GREEN **6/6**; product **`606e7ba`** (`feat: enrich piecewise plot sampling grids`); Actions `33301993902`: **536/536 GREEN in 91.31 s**. Exact non-grid breakpoints are added to the 201-point base and unioned across multi-series/sweeps/envelopes.
- Task 6 segmented plotting: first provisional patch intentionally not committed after focused failure. Corrected Actions `33314449433`, job `99265164117`: RED **6/6 failed as expected**, focused **6/6 GREEN**, full **542/542 GREEN in 94.43 s**. Product **`ebef3b9a4d78695bf29d4530cc06488a0ce49836`**.
- Task 7 Piecewise calculus: Actions `33314706148`, job `99265863908`: RED **2 failed / 3 passed** exactly at derivative breakpoints; focused **5/5 GREEN**; full **547/547 GREEN in 81.94 s**. Product **`34358fd94e27e99180cdd49074df4e5c473d202b`**.
- Task 8 acceptance/diagnostics/docs: initial RED exposed missing README documentation plus a swallowed Piecewise-specific comparison-unit error. Corrected Actions **`33315071844`**, job `99266867060`: RED **2 failed / 12 passed**, acceptance/diagnostics **14/14 GREEN**, complete Piecewise suite **66/66 GREEN**, full suite **557/557 GREEN in 113.99 s**. Product **`d0ff122b3f5f4681214fdbe6059c860c3bb11f54`**. Task 8 harnesses were then removed in cleanup commits ending at **`ce1f7c69c3497f97db8fe9474273ac67acf744b0`**.
- No Task 6/7/8 temporary write-capable harness remains after its corresponding cleanup.
- Package/runtime remains 0.7.2 by design; 0.8.0 is not yet claimed or distributed until Task 9 completes.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** RELEASE CLOSURE ACTIVE.
  - Task 0 baseline/branch setup: COMPLETE.
  - Task 1 restricted grammar + symbolic construction: COMPLETE, 506/506.
  - Task 2 Pint-aware numeric Piecewise: COMPLETE, 518/518.
  - Task 3 partial numeric + Piecewise renderer: COMPLETE, 526/526.
  - Task 4 Piecewise tables: COMPLETE, 530/530.
  - Task 5 exact breakpoint/shared enriched grids: COMPLETE, 536/536.
  - Task 6 segmented plots/fills at transitions: COMPLETE, 542/542.
  - Task 7 integral/diff + derivative breakpoint semantics: COMPLETE, 547/547.
  - Task 8 real `%%eng` acceptance, diagnostics and docs: COMPLETE, 557/557.
  - **Task 9 0.8.0 release closure/distribution validation: NEXT.**
- **0.9.0 vectors / matrices / linear systems:** NEXT MAJOR MILESTONE AFTER PIECEWISE; design/spec gate required.
- Later roadmap remains 0.9.1 exact-first analysis → 0.9.2 exact envelopes → 0.9.3 response cases → 0.10.x verification → 1.0.0.

## Exact next step

1. Start Task 9 with a **version RED contract first**: runtime/package metadata/README current version must expect 0.8.0 while production still reports 0.7.2.
2. Apply the minimal version bump only after verified RED: `pyproject.toml`, `src/engcalc_colab/__init__.py`, current-version tests and current README version references.
3. Run the complete source suite.
4. Build the actual `engcalc_colab-0.8.0` wheel and verify metadata.
5. Install that wheel into a fresh virtual environment from outside the repository with `PYTHONPATH` cleared and prove imports resolve from `site-packages`.
6. Run a release smoke covering Piecewise endpoint ownership, full/partial numeric, dimensional zero, exact-count table, non-grid breakpoint plot segmentation, Piecewise integral/diff, representative pre-0.8.0 multi-argument behavior and positive moment downward.
7. Run the complete test suite against the installed wheel from a source-free test tree, then repeat the source suite.
8. Record validation SHA, Python version, source and installed-wheel counts, wheel filename and SHA-256/artifact evidence.
9. Remove temporary release-validation harnesses, update this context with authoritative release evidence, and open a PR targeting `main` titled `release: EngCalc 0.8.0 piecewise expressions`.
10. Stop at the open PR. **Do not merge without explicit user approval.**

## How to resume in a new conversation

Read this file first. Active development is `feature/v0.8.0-piecewise`, based on `main@79befeeb...`. Piecewise Tasks 1–8 are complete and the accepted Task 8 product is `d0ff122b...`; the latest cleanup checkpoint before this context update is `ce1f7c69...`. The authoritative acceptance evidence is Actions `33315071844`: 14/14 acceptance/diagnostics, 66/66 Piecewise, 557/557 full GREEN. Runtime/package intentionally still report 0.7.2. The exact next action is Task 9 release TDD and wheel validation. Do not start matrix/CAS production work on this branch, do not invoke Codex, and do not merge the eventual release PR without explicit user approval.