# EngCalc Current Project Context

_Last updated: 2026-08-29 — EngCalc 0.7.2 remains canonical; 0.8.0 Piecewise design is written and awaiting written-spec review before implementation planning._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical release branch: `main`.
- Canonical release: **EngCalc 0.7.2 — engineering tables / evaluation by points**.
- Current `main` checkpoint before 0.8.0 planning: `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`.
- Package/runtime version remains **0.7.2**; no 0.8.0 production code has been written.
- Active planning branch: **`planning/v0.8.0-piecewise`**, created from the current canonical `main` checkpoint.
- Formal 0.8.0 design spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- Latest Piecewise spec refinement commit: `9f0683d86dbb90210d0be5b93552876d9526cc59`.
- Canonical evolution roadmap: `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`.
- 0.7.3 derivation traces is retired as redundant; no 0.7.3 release is planned.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume the user's Codex quota without explicit authorization.
- Retain planning/feature branches unless the user explicitly requests deletion.

## Approved behavior

### Existing 0.7.2 regression baseline

- Preserve multi-argument functions, generalized partial evaluation, scalar math, numeric/result rendering, tables, plots/envelopes and structural positive-moment-down convention.
- `numeric(...)` remains the detailed calculation-memory presentation: formula → numerical substitution → result.
- `result(...)` remains the compact presentation: formula → result.
- Table uniform-count forms preserve exactly the requested count; explicit-point tables preserve exactly the supplied points.
- Plot/envelope base sampling remains 201 points unless a later feature explicitly enriches the grid without changing that base policy.

### Approved 0.8.0 Piecewise design

- Public syntax: `piecewise(value1, condition1, value2, condition2, ..., default)`.
- Mandatory final default; odd positional arity >= 3; no keywords.
- Branches evaluate in source order; the first true condition wins.
- Boundary ownership is controlled explicitly by `<`, `<=`, `>` and `>=`.
- Each Piecewise call uses one direct interval variable across all non-default conditions.
- Conditions are one binary comparison between that interval variable and a breakpoint expression that does not contain the same variable.
- No chained comparisons, `and/or/not`, public `==/!=`, Python conditionals, or conditions that require hidden root/intersection solving.
- Unit aliases remain numerical-context names; symbolic conditions use breakpoint variables such as `a := 3*m`, then `x < a`, not `x < 3*m`.
- SymPy `Piecewise`/relational nodes are the authoritative symbolic representation; Pint handles numeric comparisons and branch values.
- Exact dimensionless zero may inherit a compatible dimension in comparisons and Piecewise branch results; nonzero dimensionless/dimensional ambiguity is rejected.
- Branch-unit compatibility is lazy but strict at numerical operation boundaries; inactive branches are not blindly evaluated outside their domain.
- Fully numeric `numeric(piecewise_function(value))` selects the governing branch.
- Partial `numeric(piecewise_function(x))` preserves the free interval variable while substituting known branch values and breakpoints; `result(...)` remains compact.
- Tables do not add Piecewise breakpoints: uniform count and explicit points stay contractual.
- Plots retain the 201-point base grid and add numerically resolvable explicit Piecewise breakpoints inside the domain.
- Multi-series plots/envelopes and parameter sweeps use a shared union of relevant Piecewise breakpoints.
- Plot rendering splits polylines at Piecewise transitions so Matplotlib does not draw artificial connectors across jumps; no open/closed endpoint glyphs in 0.8.0.
- `integral(...)` continues to delegate symbolic Piecewise integration to SymPy; numeric support extends to the restricted Piecewise/relational/Min/Max constructs produced by that supported path.
- `diff(...)` is branchwise, introduces no automatic `DiracDelta`, and treats explicit Piecewise breakpoints conservatively as derivative-undefined unless simplification removed the transition before differentiation.
- `simplify`, `expand`, `factor`, `subs`, `integral` and `diff` compose with Piecewise when supported by SymPy/EngCalc restrictions.
- `solve(piecewise(...))` is not promoted as a new 0.8.0 contract; exact roots/intersections belong to 0.8.1.
- No new runtime dependency is planned.

## Open issues / user feedback

- The user approved the complete 0.8.0 Piecewise design globally and explicitly requested that routine technical micro-decisions be analyzed independently rather than requiring repeated approvals.
- The written spec has been created and self-reviewed, but it has not yet received the user's post-document review required by the architectural design workflow.
- No implementation plan exists yet for 0.8.0.
- No production/test/package version changes have been made for 0.8.0.
- One design correction made during self-review: a plot must both inject exact Piecewise breakpoints and split rendered line segments at transitions; breakpoint insertion alone would still allow Matplotlib to draw an artificial connector across a discontinuity.
- Another self-review clarification: one Piecewise call uses one interval variable, and dimensional validation is operation-scoped because free symbolic variables prevent general static unit inference.

## Validation evidence

### 0.7.2 release baseline

- Release PR #29 merged EngCalc 0.7.2 into `main`.
- Merge commit: `a7ba9521220743f3cb79814e13bd44b0e0f9ce5d`.
- Authoritative final distribution gate: Actions `33266879721`, validated SHA `08a58e77c1ebace0790ba1082290e3a291a47948`, Python 3.13.15.
- Release/version/packaging contracts: **11/11 passed**.
- Table feature subset: **80/80 passed**.
- Complete source suite: **454/454 passed**.
- Source-free installed-wheel suite: **454/454 passed**.
- Repeated source suite: **454/454 passed**.
- External installed-wheel smoke: **PASS** from outside repository source tree.
- Wheel: `engcalc_colab-0.7.2-py3-none-any.whl`.
- Wheel SHA-256: `bb7ece9ee102f3909cf78b53e99ff46f2229053372e7446bede2af321ae621cf`.
- Final PR head → merge commit had zero changed files, so the validated product tree remained applicable after merge.

### Roadmap correction

- User-side Google Colab verification confirmed existing `numeric(...)` already renders formula → substitution → result and `result(...)` renders formula → result.
- The formerly planned 0.7.3 derivation-traces milestone was therefore retired as duplicate scope.
- Corrected roadmap is persisted on `main` and promotes 0.8.0 Piecewise as the next real release milestone.

### 0.8.0 design evidence

- Planning branch `planning/v0.8.0-piecewise` was created from canonical `main` SHA `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`.
- Formal design spec was created, then self-reviewed and tightened.
- Current written design commit: `9f0683d86dbb90210d0be5b93552876d9526cc59`.
- No implementation code or RED tests have been added yet.

## Roadmap / active plan

- **0.7.2 — engineering tables:** COMPLETE and merged.
- **0.7.3 — derivation traces:** RETIRED / no release.
- **0.8.0 — Piecewise expressions:** DESIGN WRITTEN; awaiting written-spec review before implementation planning.
- **0.8.1 — exact-first extrema, roots and intersections:** planned after Piecewise.
- **0.8.2 — exact envelopes and governing intervals:** planned after exact characteristic solving.
- **0.8.3 — named response cases and combinations:** planned after exact envelope infrastructure.
- **0.9.0 — vectors, matrices and linear systems:** planned.
- **0.10.0 — engineering verification system (`check(...)`):** planned.
- **0.10.1 — verification collections and summaries (`summary()`):** planned.
- **1.0.0 — language/API stabilization and release engineering:** final roadmap stabilization milestone.

## Exact next step

- User reviews the written 0.8.0 spec at `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- If the user approves the written spec, invoke the Superpowers `writing-plans` skill and create a detailed implementation plan on `planning/v0.8.0-piecewise`.
- Do not implement production code before the written-spec review gate is passed.
- After implementation-plan approval, create/use a feature branch from the canonical baseline according to the approved plan and execute strict RED → GREEN TDD.
- Keep package/runtime version at 0.7.2 until formal 0.8.0 release closure.
- Do not invoke Codex without explicit authorization.

## How to resume in a new conversation

Read this file first, then read `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md` and the canonical evolution roadmap. EngCalc 0.7.2 remains the released baseline with authoritative 454-test distribution evidence. The redundant 0.7.3 milestone is retired. Active work is 0.8.0 Piecewise on `planning/v0.8.0-piecewise`; the complete design has been written and self-reviewed, but implementation has not begun and no implementation plan exists yet. The next gate is user review of the written spec; after approval, use `writing-plans`, then strict TDD. Do not invoke Codex.