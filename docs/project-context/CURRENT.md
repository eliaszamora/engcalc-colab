# EngCalc Current Project Context

_Last updated: 2026-08-29 after the 0.7.2 engineering-table design was written on the planning branch._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical product branch: `main`.
- Canonical released baseline: **EngCalc 0.7.1**.
- Current planning branch: `planning/v0.7.2-engineering-tables`, created from `main` at `eab4f9a5dac6c6a0962419ba5273cd9fc212a86e`.
- 0.7.1 release PR #28 is merged; merge commit `f142a85ae90b657b8f85216f0510e686709ee602`.
- Package/runtime version remains **0.7.1** during planning. No 0.7.2 production code or version bump has been made.
- 0.7.2 design spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`.
- Spec creation commit: `d5ad296325157cceee088d704849f9073e3a0ec8`.
- Retain existing release/planning branches unless the user explicitly requests cleanup.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume the user's Codex quota without explicit authorization.

## Approved behavior

### Existing 0.7.1 baseline

- User functions support one or more ordered positional parameters with exact arity.
- Generalized partial numeric evaluation substitutes known values while preserving only genuinely unresolved caller-side symbols.
- Scalar engineering math, Pint-backed numeric values, plotting and envelopes remain unchanged.
- Plot/envelope rendering remains 201-point with positive structural moment plotted downward.

### 0.7.2 conceptual decisions already approved in chat

- Next milestone is **engineering tables / evaluation by points**.
- Automatic discretization is the primary/recommended workflow:
  `table(M(x), x, 0, L, 21)`.
- When `L` carries units, exact dimensionless zero may inherit the compatible endpoint unit; users should not be forced to write `0*m`.
- Explicit point magnitudes can declare the unit once:
  `table(M(x), x, [0, 1, 1.5, 2, 3, 4], m)`.
- Fully explicit quantities remain supported for mixed compatible point units:
  `table(M(x), x, [0*m, 50*cm, 1*m, 150*cm, 2*m])`.
- EngCalc must never infer metres merely from the variable name. A dimensionless domain remains dimensionless unless unit information is supplied.
- Table output is intended to render natively inside `%%eng`, not require pandas.

## Open issues / user feedback

- No known functional blocker remains for 0.7.1.
- The written 0.7.2 spec is **pending explicit user review/approval** before an implementation plan or production code may begin.
- The current spec deliberately keeps the original roadmap constraint that multiple response expressions in one 0.7.2 table are dimensionally compatible. Cross-dimension tables (for example moment + shear + displacement together) are deferred unless the user explicitly expands scope.
- No CSV/Excel export, interactive spreadsheet behavior, Cartesian multi-parameter sweep, arbitrary list syntax or pandas runtime dependency is included in 0.7.2.

## Validation evidence

### Authoritative 0.7.1 release evidence

- Corrected distribution gate: GitHub Actions `33259552699` — success.
- Validated SHA: `2332bd29e571a360cc47a29562e09b5828a3d2cb`.
- Focused corrected release contracts: **77/77 passed**.
- Complete source suite: **386/386 passed**.
- Complete source-free suite against installed wheel: **386/386 passed**.
- Repeated complete source suite: **386/386 passed**.
- Wheel artifact ID: `9716898144`.
- Wheel digest: `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`.
- Final PR head → merge commit had zero changed files.

### 0.7.2 planning evidence

- `AGENTS.md`, `CURRENT.md`, roadmap design, parser, models, engine and renderer were inspected before writing the new design.
- Current parser deliberately rejects arbitrary list literals, confirming that `table(...)` needs a narrow table-specific whitelist rather than general list support.
- Current public result types are immutable dataclasses, supporting a dedicated `TableResult` rather than overloading `PlotResult`.
- 0.7.2 spec was written and self-reviewed for placeholders, internal contradictions, scope and ambiguous requirements.
- No production code has been modified and no tests have been claimed for 0.7.2 yet.

## Roadmap / active plan

- **0.7.1 is complete and merged.**
- Active milestone candidate: **0.7.2 — engineering tables / evaluation by points**.
- Written design exists on `planning/v0.7.2-engineering-tables`.
- Core user-facing design is automatic discretization first, explicit points second.
- After written-spec approval, invoke the writing-plans workflow and create a detailed RED → GREEN implementation plan.
- The existing roadmap continues to 0.7.3 derivation traces after 0.7.2 unless later amended.

## Exact next step

- User reviews `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`.
- If approved, create the 0.7.2 implementation plan before touching production code.
- Then implement from the 0.7.1 `main` baseline with strict RED → GREEN TDD, focused tests first and full-suite verification after each coherent block.
- Do not bump the package version until the release-closing task.

## How to resume in a new conversation

Read this file first. EngCalc 0.7.1 is the validated canonical baseline on `main`. Planning for 0.7.2 is on `planning/v0.7.2-engineering-tables`; design spec `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`, creation commit `d5ad296325157cceee088d704849f9073e3a0ec8`. The approved conceptual syntax prioritizes `table(M(x), x, 0, L, 21)` and also supports a one-unit explicit-point form such as `table(M(x), x, [0, 1, 2], m)`. The written spec is awaiting explicit user review before an implementation plan or production code. Do not manually invoke Codex without explicit authorization.