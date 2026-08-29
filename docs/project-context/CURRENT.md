# EngCalc Current Project Context

_Last updated: 2026-08-29 after the EngCalc 0.7.0 scalar-engineering-math implementation and final distribution gate completed successfully and the temporary validation workflow was removed._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` remains merged-and-documented EngCalc **0.6.2** at `fff645936029f7348b2c080aa30eafab1116d532` before the 0.7.0 release is integrated.
- Active release branch: `feature/v0.7.0-scalar-engineering-math`.
- Candidate version: **0.7.0** in both `pyproject.toml` and `src/engcalc_colab/__init__.py`.
- Final validated distribution-gate tree: `331c9ff6b976a74f4b0fcc819018fe60fa2928f4`.
- Temporary 0.7.0 validation workflow was removed afterward in `1e938c5a2ec1ea71ddb737ce6902623cc346829e`; this cleanup changed no product or test file.
- A release PR still needs to be created and inspected. Do **not** merge without explicit user approval.

## Approved behavior retained from 0.6.x

- `numeric(...)` renders formula → explicit numerical substitution → final result.
- `result(...)` renders formula → final result through the same numerical engine.
- Semantic MathJax spacing remains 4 pt for wrapped continuation rows, 8 pt for a new mathematical stage/consecutive source result, and 16 pt after an explicit blank source line.
- Direct unit-bearing function arguments from 0.6.2 remain supported, including dimensional zero arguments.
- Structural positive moment remains plotted downward.
- Existing plot/envelope behavior, 201-point rendering grid, signed/magnitude envelope semantics and compact characteristic labels remain unchanged.

## EngCalc 0.7.0 — scalar engineering mathematics

### Public symbolic capabilities

The following names are now fixed public EngCalc language elements and are reserved from user assignment/function-parameter use:

- `sqrt(expression)`;
- `sin(expression)`, `cos(expression)`, `tan(expression)`;
- `asin(expression)`, `acos(expression)`, `atan(expression)`;
- `exp(expression)`;
- `log(expression)`;
- constant `pi`.

Symbolically, the nine functions map through a fixed explicit SymPy mapping; no dynamic arbitrary SymPy access was introduced. `pi` resolves to exact `sp.pi` in symbolic expressions.

### Unit-aware numeric rules

- `sqrt` propagates units through a power of one half, e.g. `sqrt(9*m^2) -> 3*m`.
- `sin`, `cos` and `tan` accept dimensionless values or angle quantities; degree quantities are converted to radians before evaluation.
- `asin`, `acos` and `atan` require dimensionless arguments and return Pint radian quantities.
- Inverse-trigonometric results may be target-converted, e.g. `numeric(atan(1), deg) -> 45 deg`.
- `exp` and `log` require dimensionless arguments.
- Incompatible dimensions raise EngCalc evaluation errors rather than silently stripping units.
- Numeric `pi` resolves consistently to the mathematical constant.

### User functions, plotting and current partial-evaluation boundary

- Scalar functions work inside user-defined functions, including `f(x) = A*sin(pi*x/L)`.
- The same function can be evaluated directly with units, e.g. `numeric(f(2*m), mm)`.
- Native `plot(f(x), x, 0, L)` samples the scalar-math response on the existing 201-point unit-aware grid.
- `numeric(f(x))` may continue to preserve `x` intentionally unresolved, but compact generalized coefficient evaluation of non-polynomial transcendental partial expressions is deliberately deferred to **0.7.1**.
- Multi-argument user functions are also deliberately deferred to 0.7.1.

## TDD evidence

### Parser RED → GREEN

- New parser contracts cover syntax for the nine scalar functions plus `pi`, and reserve all ten public names from scalar assignment, numeric assignment and function-parameter use.
- RED run `33229331526`: **10 passed, 30 failed** exactly because the new names were not yet reserved.
- Parser implementation persisted in `e19d41c7a2909a837a8d07a1d6c7206483540f77`.
- GREEN parser gate: **40/40 passed**.

### Symbolic-engine RED → GREEN

- New contracts cover the fixed SymPy mappings, exact `pi`, strict single-argument arity and composition inside user functions.
- RED run `33229446807`: parser remained **40/40 GREEN** while the **20 symbolic engine contracts failed** for the expected unsupported behavior.
- Symbolic implementation persisted in `49ae312b511b1c59db1c9cbc7db671ea3b4e0d2a`.

### Numeric RED → GREEN

- Numeric contracts cover degrees-to-radians trig, `sqrt` units, inverse-trig radian results, conversion to degrees, dimensionless `exp/log`, dimension errors and `sin(pi*x/L)` inside a user function.
- RED run `33229577297`: parser/symbolic contracts remained **60/60 GREEN** and all **11 numeric contracts failed** at the expected unsupported numeric boundaries.
- Unit-aware numerical implementation persisted in `90a6acd7818b0963185aeef81f4cb64e30b8d312`.

### Integrated acceptance and source regression

- Added actual plot/magic acceptance for `f(x) = A*sin(pi*x/L)` and the intentional pre-0.7.1 partial-evaluation boundary.
- Run `33229699540`: **74/74 focused scalar contracts passed** and the complete source suite passed **336/336**.
- Release metadata/documentation closure then passed **94/94 focused release/scalar contracts** and **336/336 complete source tests** before the 0.7.0 versioned state was persisted.

## Final 0.7.0 distribution gate

GitHub Actions run **`33229971355`** on validated tree **`331c9ff6b976a74f4b0fcc819018fe60fa2928f4`** completed successfully:

- release metadata: PASS (`0.7.0` in package and `pyproject.toml`);
- focused 0.7.0/release contracts: **94 passed in 6.79 s**;
- complete source suite: **336 passed in 56.71 s**;
- wheel `engcalc_colab-0.7.0-py3-none-any.whl`: built successfully with metadata version 0.7.0;
- clean virtual-environment wheel installation: PASS;
- installed-wheel smoke from `/tmp` with empty `PYTHONPATH`: PASS, importing from `site-packages` and exercising `sin(30*deg)`, `sqrt(9*m^2)`, `numeric(atan(1), deg)`, a unit-aware sine user function and its 201-point plot;
- source-free complete suite against the installed wheel: **336 passed in 55.04 s**;
- repeated complete source suite: **336 passed in 55.26 s**;
- validated wheel artifact: `engcalc-colab-0.7.0-wheel`;
- artifact ID: **9708206249**;
- artifact ZIP digest: `sha256:cab93c8df7d85bf678bb706a01d45508d0c8666aed20aa3d2fa74b2f5c48ce26`.

## Chain of custody after the gate

- The temporary workflow `.github/workflows/v070-scalar-math.yml` was removed after the successful gate in commit `1e938c5a2ec1ea71ddb737ce6902623cc346829e`.
- No product or test modification is authorized after validated tree `331c9ff6b976a74f4b0fcc819018fe60fa2928f4` without invalidating this chain of custody and requiring appropriate re-verification.
- The next verification step is to compare the validated tree against the release-branch head after workflow cleanup and this context update. Expected differences: only workflow removal plus `docs/project-context/CURRENT.md`.

## Roadmap / active plan

- The master roadmap remains on `planning/engcalc-evolution-roadmap` and already records **0.7.0 — scalar engineering mathematics** as the milestone following 0.6.2.
- The next milestone after 0.7.0 is **0.7.1 — multi-argument user functions and generalized partial evaluation**.
- 0.7.1 is intended to add multiple named function parameters and generalized partial substitution/rendering beyond the polynomial-only compact path, including transcendental expressions introduced in 0.7.0.

## Exact next step

1. Compare validated tree `331c9ff6b976a74f4b0fcc819018fe60fa2928f4` to the current release-branch head and confirm that only workflow cleanup and this context file changed.
2. Create the 0.7.0 release PR from `feature/v0.7.0-scalar-engineering-math` into `main`.
3. Inspect its changed-file set, code patches, mergeability and review threads; stop for any P1/P2 blocker.
4. Do **not** merge the PR without the user's explicit authorization after final inspection.
5. After an authorized merge, verify merged-product tree identity, update `CURRENT.md` on `main`, and only then begin 0.7.1 from merged-and-documented `main`.

## How to resume in a new conversation

Read this file first. EngCalc 0.7.0 has completed TDD implementation and the full distribution gate; the authoritative validated tree is `331c9ff6b976a74f4b0fcc819018fe60fa2928f4` and artifact evidence is run `33229971355`. The temporary workflow has been removed. Next: prove chain of custody, create/inspect the release PR, and wait for explicit user merge approval.