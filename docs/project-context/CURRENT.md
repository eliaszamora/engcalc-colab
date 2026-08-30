# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.0 Matrix/CAS remains the canonical integrated release on `main`. The user has now explicitly approved the written 0.9.1 exact-characteristics spec. The detailed 12-task RED → GREEN implementation plan has been written and self-reviewed on the dedicated 0.9.1 branch. Production implementation has not started._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical integrated release: **EngCalc 0.9.0 Matrix/CAS**.
- Canonical baseline used for 0.9.1: **`main@cdc454db7ea43e57e334d523afded8b4ef498ded`** (`docs: close EngCalc 0.9.0 Matrix CAS integration`).
- 0.9.0 merge commit: **`d22d5e0a62ce13800de8476c28d86a6d9415f1bd`**; PR #32 is merged/closed.
- Runtime/package version remains **0.9.0** until the 0.9.1 release-closing task.
- Active branch: **`feature/v0.9.1-exact-characteristics`**, created exactly from `main@cdc454db7ea43e57e334d523afded8b4ef498ded`.
- Approved design spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
- Design-spec commit: **`6872eaf8f0f21c93f03976092db4cc305b066994`**.
- Implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.1-exact-characteristics-implementation.md`.
- Initial plan commit: **`aacf133221725b8ee7f8d9b852c5a6fa83dafbc2`**.
- Plan self-review/correction commit: **`eb9b5344d20dab950462c63e742ff8f17be8916d`**.
- 0.9.1 production code/tests: **NOT STARTED**.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.

## Approved behavior

### Existing released behavior preserved

- `%%eng` remains a restricted EngCalc DSL; ordinary notebook cells remain Python.
- Numeric/Pint semantics, `numeric(...)`, `result(...)`, Piecewise, tables, plots, envelopes, multi-argument functions and Matrix/CAS behavior remain regression requirements.
- Whole matrices remain invalid scalar analysis/plot/table/envelope responses; indexed scalar matrix expressions remain supported.
- Positive structural moment remains plotted **downward**.
- The 201-point plot grid remains a rendering policy, not an authoritative mathematical solver.

### Approved 0.9.1 contract

Public standalone calls:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

- Introduce one reusable exact-first characteristic-analysis core in `src/engcalc_colab/characteristics.py`.
- Exact symbolic results are authoritative whenever a finite usable exact result exists.
- Deterministic numerical fallback runs only after unresolved exact solving, is residual-validated, visibly approximate and independent of the public 201-point plotting grid.
- Domains are finite closed real intervals with unit-compatible bounds and `lower < upper`; dimensional zero inheritance follows existing EngCalc semantics.
- Whole matrices are rejected; indexed scalar matrix responses such as `K(x)[1,1]` are valid.
- `roots(...)` keeps real in-domain roots, endpoints and repeated-root de-duplication; identically-zero regions are represented as interval loci.
- `intersections(...)` requires dimensionally compatible responses, respects Piecewise discontinuities and represents coincident intervals explicitly.
- `extrema(...)` considers stationary points, endpoints, Piecewise breakpoints and finite one-sided values; local/global roles, constant loci and unbounded directions are explicit.
- Piecewise regions are solved independently; a sign change/crossing through a jump is not a root/intersection unless equality holds at a defined point.
- Characteristic points preserve exact/numeric provenance and `at`/`left`/`right` topology.
- Standalone result models are immutable/typed and render as engineering output, never raw SymPy set/dataclass reprs.
- Ordinary/multi-series `plot(...)` migrates characteristic extrema to the exact-first core while retaining its existing 201-point curve sampling and visual conventions.
- Exact envelope crossover/governing-interval mathematics remains deferred to **0.9.2**.
- Characteristic calls remain standalone in 0.9.1; assignment/nesting/composition is intentionally unsupported.
- No SciPy/new runtime dependency.

## Open issues / user feedback

- No blocking 0.9.1 design ambiguity remains after written-spec approval and plan self-review.
- Implementation execution has not started; the next choice is execution workflow (subagent-driven vs inline/executing-plans).
- `no_vertical_scroll()` remains a separate ergonomics issue.
- Multiline ordinary non-matrix function-call parsing remains separate.
- Generalized structural eigenproblems remain deferred to a dedicated future design.

## Validation evidence

### Canonical 0.9.0 release evidence

- Matrix/CAS integration: **721/721 complete GREEN** before release closure.
- Authoritative release Actions: **`33332233490`**, job **`99312713507`**.
- Release contract: **23/23 GREEN**.
- Source suite before wheel: **721/721 GREEN in 142.99 s**.
- Wheel: `engcalc_colab-0.9.0-py3-none-any.whl`; SHA-256 **`ea66fa231b5657695e2c38cefb324da220070a2f7c86557dddef19d2017a0719`**.
- Installed-wheel/source-free suite: **721/721 GREEN in 141.38 s**.
- Final source revalidation: **721/721 GREEN in 139.76 s**.
- Validated release commit: **`fb1be9e2e854f66f95414b9597dabceabaeb6470`**.
- Post-merge Actions **`33333566096`**, job **`99316363602`**, verified exact merge SHA `d22d5e0a62ce13800de8476c28d86a6d9415f1bd`: installation, `compileall`, `git diff --check`, complete `pytest -q` all succeeded.

### 0.9.1 design/planning evidence

- `main` was verified at **`cdc454db7ea43e57e334d523afded8b4ef498ded`** immediately before creating the 0.9.1 branch.
- User approved the conversational architecture, then explicitly approved the written spec.
- Written spec commit: **`6872eaf8f0f21c93f03976092db4cc305b066994`**.
- Detailed implementation plan created at **`aacf133221725b8ee7f8d9b852c5a6fa83dafbc2`** and refined at **`eb9b5344d20dab950462c63e742ff8f17be8916d`**.
- Plan is organized into **12 RED → GREEN tasks**: parser/models; exact roots/domain; Piecewise roots; intersections; continuous extrema; Piecewise one-sided extrema; deterministic fallback; engine/diagnostics; renderer/magic; exact plot extrema; acceptance/docs/full regression; real-wheel release/PR gate.
- Self-review corrected the `NumericContext.assign` fixture to use a real AST, aligned the Piecewise fixture with public comparator syntax, and made fallback refinement explicitly Pint-aware via an mpmath callback.
- Placeholder scan on the refined plan: **0 `TBD`, 0 `TODO`, 0 `placeholder`, 0 `similar to Task`, 0 `appropriate error` matches**.
- No production source, tests, package metadata or version files have been changed for 0.9.1 yet.
- No product tests were run in this planning-only phase because the branch changes are documentation/state only; product verification begins with Task 1 RED.
- No Codex review or Codex Cloud has been invoked.

## Roadmap / active plan

- **0.7.2 engineering tables:** COMPLETE + merged.
- **Narrative / presentation / characteristic-summary:** COMPLETE + merged.
- **0.8.0 Piecewise:** COMPLETE + merged.
- **0.9.0 vectors / matrices / linear systems:** **COMPLETE + RELEASE-VALIDATED + MERGED**.
- **0.9.1 exact-first extrema / roots / intersections:** **WRITTEN SPEC APPROVED + IMPLEMENTATION PLAN READY; IMPLEMENTATION NOT STARTED**.
- Later: **0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Select the execution workflow for the approved plan: **Subagent-Driven Development** (recommended by the planning skill) or **Inline Execution / executing-plans**.
2. Before Task 1, re-read this file, the approved spec and the implementation plan and verify the active branch/head against GitHub.
3. Execute Task 1 parser/models strictly RED → GREEN; update `CURRENT.md` with the actual focused evidence and commit before moving to Task 2.
4. Continue task-by-task with focused tests before complete-suite gates; never skip the exact-first/fallback/Piecewise/unit regression contracts.
5. Close 0.9.1 only with the real-wheel/source-free release discipline defined in Task 12.
6. Open the release PR only after fresh pre-PR verification, and stop for explicit user approval before merge.
7. Do not invoke Codex unless explicitly authorized.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.0 is the validated canonical baseline used for the 0.9.1 branch (`main@cdc454db7ea43e57e334d523afded8b4ef498ded`). Active work is `feature/v0.9.1-exact-characteristics`. The user explicitly approved `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`; the detailed execution artifact is `docs/superpowers/plans/2026-08-30-engcalc-v0.9.1-exact-characteristics-implementation.md`, refined at `eb9b5344d20dab950462c63e742ff8f17be8916d`. No production implementation has started. Resume by verifying branch state, then execute Task 1 RED → GREEN under the selected execution workflow. Never merge without explicit user approval and never invoke Codex without explicit authorization.
