# EngCalc Current Project Context

_Last updated: 2026-08-29 after the user explicitly approved the EngCalc 0.7.1 design and the implementation plan was written, self-reviewed, and finalized on the dedicated planning branch._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` contains validated EngCalc **0.7.0**; current verified `main` head at planning time: `4fc6104f7a3b45dcd66a22b698bb684c21a7004a`.
- PR #27 merged 0.7.0 as `03212e2c47f16492e87aadc451efe8bee6b3ee11`; merge verification found zero file differences from the inspected release head.
- Active planning branch: `planning/v0.7.1-multiarg-partial-eval`.
- Approved design spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-design.md`.
- Latest spec clarification/self-review commit: `349ff6f61670e15266c4788d5c27f9242ec9ea01`.
- Final implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md`.
- Final plan commit: `47df41a99a51465bf84b6773d3cb33d7aeb71dcd`.
- Superseded plan draft was removed in `93c7096fa9c3b200cdf681a0e1510adca2d8fc55`.
- No 0.7.1 production source or tests have been modified yet.

## Approved behavior

- 0.7.1 adds optional multi-argument parametrization without making normal context-driven `M(x)` calculations more verbose.
- `M(x) = ...`, `M(x, q) = ...`, and `M_base(x, q, L) = ...` are valid styles according to how much the author wants to pass explicitly per call.
- Symbols omitted from the signature retain existing EngCalc name-resolution behavior; `=` symbolic state and Pint-backed `:=` numeric state remain separate.
- Function parameters are ordered, positional, local, unique, non-reserved identifiers and shadow same-named context values while bound locally.
- At least one parameter is required; unused parameters remain legal. Defaults, keyword calls, variadics, keyword-only arguments and overload-by-arity remain unsupported.
- One active definition exists per function name; redefining a function replaces its previous active signature rather than creating an overload.
- Symbolic argument binding must be simultaneous, not sequential.
- Nested composition is supported, including `qU(qD,qL) -> M(x,q,L) -> M_U(x)`.
- Fully numeric positional arguments are resolved with Pint while preserving units and dimensional zero in every argument position.
- Generalized partial evaluation substitutes every numerically known value and preserves one or many unresolved caller-side symbols.
- Partial evaluation supports non-polynomial scalar math such as `A*sin(pi*x/L)`; the existing one-variable polynomial rendering remains an optional richer specialization.
- Partial results do not fabricate a final Pint unit; target-unit conversion still requires a fully numeric result.
- Existing 0.7.0 scalar-math rules, `numeric`, `result`, plotting/envelopes, 201-point sampling and positive-moment-down convention remain authoritative.
- Multi-argument functions reuse the existing plot/envelope language; Cartesian multi-parameter sweeps are not added.

## Open issues / user feedback

- No known functional regression is open on merged 0.7.0.
- The parameter/global mental model has been clarified and approved: put in a function signature only the values that should be passed explicitly on each call; non-parameter symbols may continue to come from EngCalc context.
- The 0.7.1 design and implementation plan are approved/planned, but implementation has **not** begun.
- **Do not invoke Codex, `@codex review`, Codex Cloud, or any action that may consume the user's Codex quota for EngCalc without explicit user authorization first.** Use direct inspection, repository tools, GitHub Actions and the existing test suite instead.

## Validation evidence

- Definitive 0.7.0 distribution gate: GitHub Actions run `33232439088` on tree `0d9e2ae308f40f6cf7707a2de3970b985f7270a7`.
- Gate results: **123/123 focused**, **350/350 source**, successful real-wheel build/clean install/smoke, **350/350 installed-wheel**, **350/350 repeated source**.
- Final 0.7.0 wheel artifact: `9708946389`; digest `sha256:f88e98b7cdee221587caee56b34d0dfae779d2591be3b01609f6af4ff0115668`.
- 0.7.1 currently has design/plan documentation only. No implementation test result or release validation is claimed yet.

## Roadmap / active plan

- Master roadmap: `planning/engcalc-evolution-roadmap`.
- Completed milestone: **0.7.0 — scalar engineering mathematics**.
- Active milestone: **0.7.1 — multi-argument user functions and generalized partial evaluation**.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-design.md`.
- Final implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md`.
- Planned execution sequence: baseline → parser/models → symbolic simultaneous binding → fully numeric multi-argument evaluation → generalized partial evaluation → renderer/real `%%eng` acceptance → plot/envelope/full regression → 0.7.1 release/wheel gate.

## Exact next step

1. Use inline execution with the approved implementation plan unless the user requests another available execution workflow.
2. Re-read this file, `AGENTS.md`, the approved spec and final plan immediately before implementation.
3. Re-verify current `main` still points to the intended merged 0.7.0 baseline.
4. Create `feature/v0.7.1-multiarg-partial-eval` from current `main`.
5. Run the complete baseline source suite; expected count at plan time is **350 passing tests**. If `main` legitimately changed, record the fresh all-green count.
6. Update `CURRENT.md` on the feature branch, then start Task 1 with RED parser/model tests. Do not modify production code until those new tests fail for the intended one-parameter limitation.
7. Execute Tasks 1–7 RED → GREEN. Close 0.7.1 with a real wheel/clean-install/installed-wheel/full-suite gate, remove temporary validation workflows, prove post-gate tree identity, open/inspect the PR manually, and stop for explicit merge approval.

## How to resume in a new conversation

Read this file first. EngCalc **0.7.0 is merged and validated on `main`**. The user explicitly approved the 0.7.1 design. The final design is `docs/superpowers/specs/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-design.md`; the executable plan is `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md`. No 0.7.1 product/test implementation has started. Next: re-verify `main`, create `feature/v0.7.1-multiarg-partial-eval`, run the full 0.7.0 baseline (350 tests at plan time), then begin Task 1 with RED parser/model contracts. Never use Codex for EngCalc without explicit user authorization.