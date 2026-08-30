# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.0 Matrix/CAS remains the canonical integrated release on `main`. The user approved the conversational design for 0.9.1 exact-first extrema/roots/intersections. A dedicated 0.9.1 branch and written design spec now exist; production implementation has not started and the written spec is pending user review before implementation planning._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated release: **EngCalc 0.9.0 Matrix/CAS**.
- Canonical `main`: **`cdc454db7ea43e57e334d523afded8b4ef498ded`** (`docs: close EngCalc 0.9.0 Matrix CAS integration`).
- 0.9.0 merge commit: **`d22d5e0a62ce13800de8476c28d86a6d9415f1bd`**; PR #32 is merged/closed.
- Runtime/package version on `main`: **0.9.0**.
- Active 0.9.1 branch: **`feature/v0.9.1-exact-characteristics`**, created exactly from `main@cdc454db7ea43e57e334d523afded8b4ef498ded`.
- 0.9.1 design spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
- Design-spec commit: **`6872eaf8f0f21c93f03976092db4cc305b066994`** (`docs: specify EngCalc 0.9.1 exact characteristics`).
- 0.9.1 production code: **NOT STARTED**.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.

## Approved behavior

### Existing released behavior preserved

- `%%eng` remains a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Numeric/Pint semantics, `numeric(...)`, `result(...)`, Piecewise, tables, plots, envelopes, multi-argument functions and Matrix/CAS behavior remain regression requirements.
- Whole matrices remain invalid scalar plot/table/envelope responses; indexed scalar matrix expressions remain supported.
- Positive structural moment is plotted **downward**.
- The 201-point plotting grid remains a rendering policy, not an authoritative mathematical solver.

### Approved 0.9.1 design direction

Public standalone analysis calls:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

Approved semantics:

- Introduce one reusable exact-first characteristic-analysis core, expected in `src/engcalc_colab/characteristics.py`.
- Exact symbolic solving is authoritative whenever a finite usable exact result exists.
- Deterministic numerical fallback is allowed only after unresolved exact solving; fallback results are residual-validated, visibly approximate and independent of the plot 201-point grid.
- Analysis domains are finite closed real intervals with unit-compatible bounds; exact dimensional zero may inherit endpoint unit context when unambiguous.
- Whole matrices are rejected; indexed scalar matrix responses such as `K(x)[1,1]` are valid.
- `roots(...)` returns only real in-domain roots, respects endpoints, de-duplicates repeated roots and represents identically-zero intervals as infinite root loci rather than arbitrary samples.
- `intersections(...)` solves equality of dimensionally compatible scalar responses, respects Piecewise discontinuities and represents coincident intervals explicitly.
- `extrema(...)` considers stationary points, endpoints, Piecewise breakpoints and finite one-sided limiting values. Constant extremum loci and unbounded directions are represented explicitly.
- Piecewise regions are solved independently. A sign change/crossing across a jump is not a root/intersection unless equality actually holds at a defined point.
- Characteristic points carry exact/numeric provenance and `at`/`left`/`right` side semantics where required.
- Typed immutable point/interval/result models are used internally; standalone renderers never expose raw SymPy sets or Python dataclass reprs.
- Ordinary and multi-series `plot(...)` characteristic extrema migrate from sampled `_extreme_indices(...)` coordinates to the exact-first characteristic core while curve sampling itself remains unchanged.
- Exact envelope crossovers/governing intervals remain deferred to 0.9.2; 0.9.1 must not partially implement that release.
- Assignment/nesting of `extrema(...)`, `roots(...)` and `intersections(...)` is intentionally unsupported in 0.9.1; they are standalone analysis statements.
- No SciPy/new runtime dependency.

## Open issues / user feedback

- Written 0.9.1 spec is pending explicit user review/approval before implementation planning.
- `no_vertical_scroll()` remains a separate ergonomics issue.
- Multiline ordinary non-matrix function-call parsing remains separate.
- Generalized structural eigenproblems remain deferred to a dedicated future design.
- Auxiliary branch `noop` is non-product and contains no unique feature work.

## Validation evidence

### Canonical 0.9.0 release evidence

- Task 9 integrated Matrix/CAS acceptance: **29/29 focused**, **164/164 Matrix/CAS acceptance**, **721/721 complete GREEN** on `6bd29dbb8fb417667f1fb1e264d9cbd146a2bbe0`.
- Authoritative 0.9.0 release Actions: **`33332233490`**, job **`99312713507`**.
- Release contract: **23/23 GREEN**.
- Source suite before wheel: **721/721 GREEN in 142.99 s**.
- Wheel: `engcalc_colab-0.9.0-py3-none-any.whl`, SHA-256 **`ea66fa231b5657695e2c38cefb324da220070a2f7c86557dddef19d2017a0719`**.
- Installed-wheel/source-free suite: **721/721 GREEN in 141.38 s**.
- Final source revalidation: **721/721 GREEN in 139.76 s**.
- Authoritative validated release commit: **`fb1be9e2e854f66f95414b9597dabceabaeb6470`**.
- Post-merge Actions **`33333566096`**, job **`99316363602`**, verified the exact merge SHA `d22d5e0a62ce13800de8476c28d86a6d9415f1bd` with installation, `compileall`, `git diff --check` and complete `pytest -q`: **success**.

### 0.9.1 design evidence

- `main` was rechecked immediately before branching and remained **`cdc454db7ea43e57e334d523afded8b4ef498ded`**.
- Branch **`feature/v0.9.1-exact-characteristics`** was created from that exact SHA.
- User explicitly approved the in-conversation architectural design before the written spec was created.
- Written spec committed at **`6872eaf8f0f21c93f03976092db4cc305b066994`**.
- Spec self-review found no `TODO`/`TBD` placeholders; exact-first/fallback, units, Piecewise discontinuities, matrices/indexed scalars, plots, envelope boundary, diagnostics, TDD and release scope are explicitly defined.
- No production files or tests have been changed for 0.9.1 yet.
- No Codex review or Codex Cloud has been invoked.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **COMPLETE + RELEASE-VALIDATED + MERGED**.
- **0.9.1 exact-first extrema / roots / intersections:** **DESIGN APPROVED IN CONVERSATION; WRITTEN SPEC PENDING USER REVIEW**.
- Later: **0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. User reviews `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
2. If changes are requested, revise the spec and repeat the spec self-review.
3. After explicit written-spec approval, invoke the Superpowers `writing-plans` workflow and create the detailed RED → GREEN 0.9.1 implementation plan.
4. Do not change production code before that plan exists.
5. During implementation, run focused RED/GREEN tests before the complete suite and close the release with the same real-wheel/source-free validation discipline.
6. Do not merge without explicit user approval and do not invoke Codex unless explicitly authorized.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.0 is the validated canonical baseline on `main@cdc454db7ea43e57e334d523afded8b4ef498ded`. Work for 0.9.1 is on `feature/v0.9.1-exact-characteristics`, created from that exact baseline. The conversational architecture has user approval and the written design spec exists at `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md` (spec commit `6872eaf8f0f21c93f03976092db4cc305b066994`). Production implementation has not started. The next gate is explicit user review/approval of the written spec; only then create the implementation plan with `writing-plans`.
