# EngCalc Current Project Context

_Last updated: 2026-08-29 — EngCalc 0.7.2 remains canonical; 0.8.0 Piecewise design is approved and the implementation plan is written. Production implementation has not started._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical release branch: `main`.
- Canonical release: **EngCalc 0.7.2 — engineering tables / evaluation by points**.
- Current `main` checkpoint before 0.8.0 execution: `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`.
- Package/runtime version remains **0.7.2**; no 0.8.0 production code has been written.
- Active planning branch: **`planning/v0.8.0-piecewise`**, created from canonical `main`.
- Approved 0.8.0 design spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.8.0-piecewise-design.md`.
- Current Piecewise spec commit: `9f0683d86dbb90210d0be5b93552876d9526cc59`.
- Implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md`.
- Implementation-plan commit: `2dbb367b96f2fe7760fa188e4e58c66bb9f61ce7`.
- Canonical evolution roadmap: `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`.
- 0.7.3 derivation traces is retired as redundant; no 0.7.3 release is planned.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume the user's Codex quota without explicit authorization.
- Retain planning/feature branches unless explicitly requested otherwise.

## Approved behavior

### Existing 0.7.2 regression baseline

- Preserve multi-argument functions, generalized partial evaluation, scalar math, `numeric`/`result` rendering, tables, plots/envelopes and structural positive-moment-down convention.
- `numeric(...)` remains formula → numerical substitution → result.
- `result(...)` remains formula → result.
- Uniform-count tables preserve exactly the requested count; explicit-point tables preserve exactly the supplied points.
- Plot/envelope base sampling remains 201 points.

### Approved 0.8.0 Piecewise design

- Public syntax: `piecewise(value1, condition1, value2, condition2, ..., default)`.
- Mandatory final default; odd positional arity >= 3; no keywords.
- Branches evaluate in source order; first true condition wins.
- Boundary ownership is explicitly controlled with `<`, `<=`, `>` and `>=`.
- Each Piecewise call uses one direct interval variable across all non-default conditions.
- Each condition compares that interval variable directly against a breakpoint expression that does not contain the same variable.
- No chained comparisons, `and/or/not`, public `==/!=`, Python conditionals, or conditions that require hidden root/intersection solving.
- Unit aliases remain numerical-context names; use breakpoint values such as `a := 3*m`, then symbolic conditions such as `x < a`, rather than unit literals inside symbolic conditions.
- SymPy `Piecewise`/relational nodes are the symbolic authority; Pint handles numerical comparisons and branch values.
- Exact dimensionless zero may inherit a compatible dimension; nonzero dimensionless/dimensional ambiguity is rejected.
- Branch-unit validation is lazy but strict at numerical operation boundaries; inactive branches are not blindly evaluated outside their domain.
- Fully numeric `numeric(piecewise_function(value))` selects the governing branch.
- Partial `numeric(piecewise_function(x))` preserves the free interval variable while substituting known branch values and breakpoints; `result(...)` stays compact.
- Tables do not add breakpoints; table count/explicit-point contracts remain unchanged.
- Plots retain the 201-point base grid and add exact numerically resolvable Piecewise breakpoints inside the requested domain.
- Multi-series plots/envelopes and sweeps use the union of relevant breakpoints so all series remain aligned.
- Plot rendering splits polylines/fills at Piecewise transitions so Matplotlib does not draw artificial connectors across jumps.
- No open/closed endpoint glyphs in 0.8.0.
- `integral(...)` continues to delegate Piecewise integration to SymPy; numeric support extends only to restricted Piecewise/relational/Min/Max forms produced by supported calculus.
- `diff(...)` is branchwise, introduces no automatic `DiracDelta`, and treats explicit Piecewise breakpoints conservatively as derivative-undefined unless simplification removed the transition first.
- `solve(piecewise(...))` is not promoted as a new 0.8.0 contract; exact roots/intersections remain 0.8.1 scope.
- No new runtime dependency.

## Open issues / user feedback

- The user approved the complete 0.8.0 Piecewise design globally and then approved proceeding after the written spec review gate.
- The user explicitly requested that routine technical micro-decisions be analyzed independently rather than requiring repeated approvals.
- The complete implementation plan is now written and self-reviewed. No production implementation has started yet.
- New user request: allow explanatory prose inside `%%eng`, not only headings/subheadings, so calculation memories can explain what each calculation is doing.
- This narrative-text request is intentionally kept separate from the Piecewise implementation plan because it is an independent presentation capability.
- Proposed bounded design for narrative text: preserve `#` as hidden comments and `##`/`###` as headings; introduce a visible-paragraph marker such as `#> Texto...`, with consecutive `#>` lines merged into one normal paragraph and blank lines separating paragraphs. This proposal is not implemented yet and should receive one global design approval before coding.

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
- External installed-wheel smoke: **PASS**.
- Wheel: `engcalc_colab-0.7.2-py3-none-any.whl`.
- Wheel SHA-256: `bb7ece9ee102f3909cf78b53e99ff46f2229053372e7446bede2af321ae621cf`.

### Roadmap correction

- User-side Colab verification confirmed `numeric(...)` already provides formula → substitution → result and `result(...)` formula → result.
- The old 0.7.3 derivation-traces milestone was retired as duplicate scope.
- Corrected roadmap on `main` promotes 0.8.0 Piecewise as the next major release milestone.

### 0.8.0 planning evidence

- Planning branch `planning/v0.8.0-piecewise` created from `main` SHA `72b0b1b872c57f379abe16ceaa686bec0e5ef10b`.
- Formal design spec created and self-reviewed; latest design commit `9f0683d86dbb90210d0be5b93552876d9526cc59`.
- User passed the post-written-spec approval gate with `procede`.
- Implementation plan created at `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md`, commit `2dbb367b96f2fe7760fa188e4e58c66bb9f61ce7`.
- Plan contains Tasks 0–9: baseline/feature branch; parser/symbolic grammar; Pint numeric evaluation; partial numeric rendering; tables; breakpoint-aware plot grids; discontinuity-safe plotting; calculus; acceptance/docs; release/distribution closure.
- No production code, tests or version metadata have been changed yet for 0.8.0.

## Roadmap / active plan

- **0.7.2 — engineering tables:** COMPLETE and merged.
- **0.7.3 — derivation traces:** RETIRED / no release.
- **0.8.0 — Piecewise expressions:** DESIGN APPROVED; IMPLEMENTATION PLAN WRITTEN; execution not started.
- **0.8.1 — exact-first extrema, roots and intersections:** planned.
- **0.8.2 — exact envelopes and governing intervals:** planned.
- **0.8.3 — named response cases and combinations:** planned.
- **0.9.0 — vectors, matrices and linear systems:** planned.
- **0.10.0 — engineering verification system (`check(...)`):** planned.
- **0.10.1 — verification collections and summaries (`summary()`):** planned.
- **1.0.0 — language/API stabilization and release engineering:** planned final stabilization milestone.
- **Narrative text inside `%%eng`:** newly requested presentation capability; keep as a separate bounded work item rather than mixing it into the Piecewise core plan.

## Exact next step

- For Piecewise, execute `docs/superpowers/plans/2026-08-29-engcalc-v0.8.0-piecewise-implementation.md` using the approved strict RED → GREEN process.
- At execution start, create `feature/v0.8.0-piecewise` from the exact current canonical `main` SHA and rerun the complete 0.7.2 baseline before writing RED tests.
- Keep package/runtime version at 0.7.2 until Task 9 release closure.
- Do not merge the future release PR without explicit user approval.
- For the separate narrative-text request, present one concise bounded design (recommended `#>` visible-paragraph syntax) and obtain one global approval before implementation; do not ask for micro-approvals after that.
- Do not invoke Codex without explicit authorization.

## How to resume in a new conversation

Read this file first, then the Piecewise spec and implementation plan. EngCalc 0.7.2 remains the released baseline with authoritative 454-test distribution evidence. 0.7.3 is retired. Active major work is 0.8.0 Piecewise: design approved, plan written, production execution not started. The exact next Piecewise action is Task 0 of the implementation plan. A separate new user request asks for visible explanatory prose inside `%%eng`; recommended bounded syntax is `#> ...`, preserving `#` comments and `##`/`###` headings. Do not mix that independent presentation feature into the Piecewise core unless explicitly decided. Do not invoke Codex.