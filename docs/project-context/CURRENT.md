# EngCalc Current Project Context

_Last updated: 2026-08-29 after the EngCalc 0.7.1 multi-argument/generalized-partial-evaluation design was clarified with the user, written, and self-reviewed on a dedicated planning branch._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` contains validated EngCalc **0.7.0**.
- PR #27 merged 0.7.0 as `03212e2c47f16492e87aadc451efe8bee6b3ee11`; the merge tree was verified identical to the inspected release head.
- `pyproject.toml` and `src/engcalc_colab/__init__.py` report **0.7.0** on `main`.
- Active design branch: `planning/v0.7.1-multiarg-partial-eval`, created from the post-merge documented 0.7.0 `main` baseline.
- 0.7.1 design spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-design.md`.
- Spec commits: initial `b04d52724cbe224ff0c81244c640d9ce8b80214c`, clarified/self-reviewed `349ff6f61670e15266c4788d5c27f9242ec9ea01`.
- No 0.7.1 production code or tests have been changed yet.

## Approved behavior

### Retained 0.7.0 behavior

- One-argument user functions remain unchanged.
- Numeric assignments use the separate Pint-backed `:=` context; symbolic formulas remain separate.
- `numeric(...)`, `result(...)`, plotting/envelopes, 201-point grids, dimensional-zero preservation and positive structural moment plotted downward remain unchanged.
- Scalar math `sqrt`, trig/inverse trig, `exp`, `log`, and `pi` retain all 0.7.0 unit/angle semantics.

### Approved 0.7.1 design direction

- 0.7.1 adds parametrization; it does **not** require users to put every variable in a function signature.
- Context-driven functions remain natural: `M(x) = ...` may continue to use `q`, `L`, etc. from the existing EngCalc context.
- Multi-argument reusable functions become valid: `M_base(x, q, L) = ...`, `qU(qD, qL) = ...`, `sigma(M, y, I) = M*y/I`.
- Partially parametrized functions are valid: `M(x, q) = ...` may still use context/global `L`.
- Parameters are ordered, positional, local to the function body and shadow same-named context values.
- Names not listed as parameters preserve existing EngCalc symbolic/numeric name-resolution behavior; 0.7.1 does not introduce new closure/dynamic-global semantics.
- A function has one active signature; 0.7.1 does not add overload dispatch by arity. Existing function redefinition behavior is retained: a later definition replaces the prior active definition.
- At least one parameter is required; parameters must be unique, valid, non-reserved identifiers. Defaults, keyword arguments and variadics remain unsupported.
- Unused parameters are legal mathematically, although documentation should avoid unnecessary ones.
- Multi-argument calls bind exactly by position and report exact arity/signature mismatches.
- Nested/composed functions are supported, enabling patterns such as `qU(qD,qL) -> M(x,q,L) -> M_U(x)`.
- Generalized partial evaluation follows one rule: substitute every numerically known value and preserve every unresolved dependency symbolically.
- Partial evaluation may leave one or many unresolved parameters/globals and must support non-polynomial scalar-math expressions such as `A*sin(pi*x/L)`.
- Partial results do not fabricate an overall Pint unit; target-unit conversion still requires a fully numeric result.
- Existing polynomial partial rendering may remain as a richer specialization; non-polynomial/general cases get a structural partial-expression fallback.
- Multi-argument functions must compose with `numeric`, `result`, `plot`, existing multi-series/envelope behavior and existing one-parameter sweeps.
- No recursion, function overloading, signature-level unit declarations or Cartesian multi-parameter sweeps are added in 0.7.1.

## Open issues / user feedback

- No known functional regression is open on merged 0.7.0.
- The user initially found the parameter/global distinction confusing. The approved mental model is now explicit: **put in the signature only the values you want to pass explicitly on each call; non-parameter symbols may continue to come from EngCalc context**.
- The user specifically noticed that `M(x, qD, qL) = 1.2*qD + 1.6*qL` unnecessarily included `x`; the design now explicitly allows unused parameters but recommends omitting them when they reduce clarity, e.g. `qU(qD, qL) = 1.2*qD + 1.6*qL`.
- **Do not invoke Codex, `@codex review`, Codex Cloud, or any action that may consume the user's Codex quota for EngCalc without explicit user authorization first.** Use direct inspection, repository tools, GitHub Actions and the existing test suite instead.
- The 0.7.1 written spec still requires explicit user review/approval before an implementation plan or production work begins.

## Validation evidence

- Definitive 0.7.0 distribution gate: GitHub Actions run `33232439088` on validated tree `0d9e2ae308f40f6cf7707a2de3970b985f7270a7`.
- 0.7.0 gate evidence: **123/123 focused**, **350/350 source**, clean wheel build/install/smoke, **350/350 installed-wheel**, **350/350 repeated source**.
- Final 0.7.0 wheel artifact: `9708946389`, digest `sha256:f88e98b7cdee221587caee56b34d0dfae779d2591be3b01609f6af4ff0115668`.
- PR #27 merge verification showed zero file differences between inspected PR head and merge commit.
- 0.7.1 currently has design-only commits; no implementation validation is claimed yet.

## Roadmap / active plan

- Master roadmap: `planning/engcalc-evolution-roadmap`.
- Completed milestone: **0.7.0 — scalar engineering mathematics**.
- Active milestone: **0.7.1 — multi-argument user functions and generalized partial evaluation**.
- Active design branch: `planning/v0.7.1-multiarg-partial-eval`.
- Written design: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-design.md`.
- After explicit spec approval, the next required artifact is a detailed implementation plan; implementation must then start RED → GREEN from current validated `main`.

## Exact next step

1. Ask the user to review/approve the written 0.7.1 spec.
2. If changes are requested, update the spec and self-review it again.
3. After explicit spec approval, write the 0.7.1 implementation plan using the approved spec.
4. Only after plan approval/transition, create the implementation feature branch from current `main` and start with RED tests.
5. Close 0.7.1 with focused tests, complete source suite, real wheel build, clean-environment smoke, source-free installed-wheel suite, repeated source suite, CI cleanup and a PR that is not merged without explicit user approval.

## How to resume in a new conversation

Read this file first. EngCalc 0.7.0 is merged and validated on `main`. 0.7.1 is in **design-only** state on `planning/v0.7.1-multiarg-partial-eval`; no production code has changed. The written spec is `docs/superpowers/specs/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-design.md`, latest spec commit `349ff6f61670e15266c4788d5c27f9242ec9ea01`. The approved mental model is that parameters are only the values the user wants to pass explicitly; non-parameter symbols may continue to use existing EngCalc context semantics. Generalized partial evaluation substitutes all known numeric values and preserves all unresolved symbols without fabricating units. Next step: user reviews/approves the written spec; then write the implementation plan. Do not use Codex for EngCalc without explicit user authorization.