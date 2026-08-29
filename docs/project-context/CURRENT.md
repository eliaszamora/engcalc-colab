# EngCalc Current Project Context

_Last updated: 2026-08-29 after PR #27 review identified inverse-trigonometric angle-unit and continuity-documentation blockers, both code defects were corrected with RED → GREEN TDD, and a fresh corrected 0.7.0 distribution gate passed._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` remains EngCalc **0.6.2** at `fff645936029f7348b2c080aa30eafab1116d532` until 0.7.0 is explicitly approved and merged.
- Active release branch: `feature/v0.7.0-scalar-engineering-math`.
- Open release PR: **#27 — `release: EngCalc 0.7.0 scalar engineering mathematics`**.
- Candidate package/runtime version: **0.7.0**.
- Corrected product commit for inverse-trig angle handling: `ed7716fb5d965661934bd2309d6ccfee2b417cf3`.
- Authoritative corrected distribution-gate tree: `adb28861fbb274f0e60b223057c10e29bab72e9f`.
- The temporary corrected-gate workflow was removed after the successful gate in `8e6c13c02fe898152c81093997ad856b0c75564d`.
- Do **not** merge PR #27 without explicit user approval after final inspection.

## Approved behavior

### Retained 0.6.x behavior

- `numeric(...)` renders formula → explicit numerical substitution → final result.
- `result(...)` renders formula → final result through the same numerical engine.
- Semantic MathJax spacing remains 4 pt for wrapped continuation rows, 8 pt for a new mathematical stage/consecutive source result, and 16 pt after an explicit blank source line.
- Direct unit-bearing function arguments from 0.6.2 remain supported, including dimensional zero arguments.
- Structural positive moment remains plotted downward.
- Existing plot/envelope behavior, 201-point rendering grid, signed/magnitude envelope semantics and compact characteristic labels remain unchanged.

### EngCalc 0.7.0 scalar engineering mathematics

- Public fixed scalar functions: `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `exp`, `log`; public constant: `pi`.
- These names are reserved from user scalar assignment, numeric assignment and function-parameter use.
- The symbolic layer uses a fixed explicit SymPy mapping; arbitrary SymPy access was not opened.
- `sqrt` propagates units through a one-half power.
- `sin`, `cos` and `tan` accept dimensionless values or angle quantities and convert degree quantities to radians before evaluation.
- `asin`, `acos` and `atan` require dimensionless inputs and numerically return explicit Pint radian quantities.
- Exact inverse-trig expressions are kept unevaluated symbolically until the numeric layer can attach the required angle unit; e.g. `numeric(atan(1))` returns a radian quantity instead of a plain dimensionless `pi/4` result.
- Explicit angle units are preserved in notebook rendering even though Pint classifies angles as dimensionless; therefore `a := atan(1)` visibly includes `rad`, and `numeric(atan(1), deg)` visibly includes `deg`.
- `exp` and `log` require dimensionless arguments.
- Scalar math works inside user functions and native plots, including `f(x) = A*sin(pi*x/L)` and the existing 201-point plot grid.
- `numeric(f(x))` may intentionally retain `x` unresolved; generalized non-polynomial partial evaluation remains deferred to 0.7.1.
- Multi-argument user functions remain deferred to 0.7.1.

## Open issues / user feedback

- No known functional regression remains open in the corrected 0.7.0 product/test tree.
- PR #27 review originally reported three release blockers: missing mandatory continuity headings, hidden inverse-trig `rad/deg` rendering, and loss of radian units for exact inverse-trig expressions. The two code defects are corrected and covered by regression tests; this file restores the required continuity headings.
- The PR review threads still need to be replied to/resolved and the final PR changed-file/code inspection must be repeated after this cleanup.
- PR #27 must remain unmerged until that inspection is clean and the user explicitly authorizes merge.

## Validation evidence

### Original 0.7.0 implementation TDD

- Parser RED run `33229331526`: 10 syntax tests passed and 30 reserved-name contracts failed as expected; parser then reached 40/40 GREEN.
- Symbolic-engine RED run `33229446807`: parser remained 40/40 GREEN while 20 new symbolic contracts failed as expected before implementation.
- Numeric RED run `33229577297`: existing parser/symbolic contracts remained 60/60 GREEN while all 11 new numeric contracts failed at the intended unsupported boundaries.
- Integrated acceptance run `33229699540`: 74/74 focused scalar contracts and 336/336 complete source tests passed.
- The earlier distribution gate `33229971355` was valid for its then-current tree but is **superseded as final release evidence** because review subsequently required product corrections.

### Review corrective RED → GREEN

- Added `tests/test_scalar_math_angle_units.py` with three regression contracts:
  - `numeric(atan(1))` must retain `radian`;
  - `a := atan(1)` must render `rad`;
  - `numeric(atan(1), deg)` must render `deg`.
- RED run `33231160212`: **3/3 failed** for exactly those three pre-corrective defects.
- Corrective implementation commit: `ed7716fb5d965661934bd2309d6ccfee2b417cf3`.
- Corrective GREEN run `33231261259`: **32/32 focused tests passed** and complete source suite **339/339 passed**.

### Authoritative corrected 0.7.0 distribution gate

GitHub Actions run **`33231382966`** on tree **`adb28861fbb274f0e60b223057c10e29bab72e9f`** completed successfully:

- release metadata: PASS (`0.7.0` in package and `pyproject.toml`);
- focused corrected 0.7.0 contracts: **112 passed in 11.75 s**;
- complete source suite: **339 passed in 66.74 s**;
- real wheel `engcalc_colab-0.7.0-py3-none-any.whl`: built successfully;
- clean virtual-environment wheel installation: PASS;
- installed-wheel smoke from `/tmp` with empty `PYTHONPATH`: PASS;
- installed-wheel smoke explicitly verified exact `atan(1)` retains radians and `_quantity_latex` renders `rad`, target conversion to degrees renders `deg`, plus `sin(30*deg)`, `sqrt(9*m^2)`, unit-aware sine user-function evaluation and its 201-point plot;
- source-free complete suite against installed wheel: **339 passed in 65.57 s**;
- repeated complete source suite: **339 passed in 65.50 s**;
- validated artifact: `engcalc-colab-0.7.0-corrected-wheel`;
- artifact ID: **9708639018**;
- artifact ZIP digest: `sha256:0f00e5c5d9c4bc2d1a7a7fd617b000d8b4ac14552e4ac41ddf24094f238af5d4`.

### Chain of custody after corrected gate

- The temporary workflow `.github/workflows/v070-angle-unit-corrective.yml` was removed after the successful corrected gate.
- After the authoritative tree `adb28861fbb274f0e60b223057c10e29bab72e9f`, no further `src/` or `tests/` change is authorized without invalidating this gate.
- The next check must compare that validated tree to the final release-branch head and confirm that only workflow removal plus this `CURRENT.md` update occurred after validation.

## Roadmap / active plan

- The master roadmap remains on `planning/engcalc-evolution-roadmap`.
- Current release milestone: **0.7.0 — scalar engineering mathematics**.
- The next milestone after an approved/merged 0.7.0 is **0.7.1 — multi-argument user functions and generalized partial evaluation**.
- Do not start 0.7.1 until 0.7.0 is merged and the merged `main` tree is verified/documented.

## Exact next step

1. Compare corrected validated tree `adb28861fbb274f0e60b223057c10e29bab72e9f` against the current release-branch head; require post-gate differences to be only temporary-workflow removal and `docs/project-context/CURRENT.md`.
2. Reply to and resolve the three PR #27 review threads using the corrective commits/tests and restored continuity structure as evidence.
3. Re-fetch PR #27 review state, mergeability, head SHA and changed-file set; inspect the final product patches and stop if any P1/P2 issue remains.
4. Do **not** merge PR #27 without explicit user authorization.
5. After authorized merge, verify merged-product identity against the corrected validated product/test tree, update `CURRENT.md` on `main`, and only then begin 0.7.1.

## How to resume in a new conversation

Read this file first. EngCalc 0.7.0 is implemented on `feature/v0.7.0-scalar-engineering-math`; PR #27 is open and unmerged. A code review exposed inverse-trig angle-unit defects, which were reproduced RED, fixed in `ed7716fb5d965661934bd2309d6ccfee2b417cf3`, and revalidated with authoritative corrected gate `33231382966` on tree `adb28861fbb274f0e60b223057c10e29bab72e9f` (339/339 source, 339/339 installed wheel, 339/339 repeated source; artifact 9708639018). The temporary workflow has been removed and this continuity file repaired. Next: prove post-gate tree identity, resolve review threads, repeat final PR inspection, and wait for explicit user merge approval.