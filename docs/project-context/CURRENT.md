# EngCalc Current Project Context

_Last updated: 2026-08-29 after EngCalc 0.7.1 Task 3 was verified GREEN and its temporary applicator was removed._

## Active milestone

- Repository: `eliaszamora/engcalc-colab`.
- Active branch: `feature/v0.7.1-multiarg-partial-eval`.
- Release baseline: merged EngCalc **0.7.0** on `main`.
- 0.7.0 merge commit: `03212e2c47f16492e87aadc451efe8bee6b3ee11` (PR #27).
- 0.7.1 target: **multi-argument user functions and generalized partial numeric evaluation**.
- Approved implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md` on `planning/v0.7.1-multiarg-partial-eval`.
- Do not bump the package version until release closure.
- Do not merge 0.7.1 without explicit user approval.
- **Do not invoke Codex, `@codex review`, Codex Cloud, or any action that consumes the user's Codex quota without explicit user authorization.**

## 0.7.1 execution state

### Task 0 — baseline

- Started from the verified merged 0.7.0 tree.
- Baseline suite: **350/350 GREEN**.
- The branch intentionally keeps package/runtime version `0.7.0` until release closure.
- Temporary baseline workflow: `.github/workflows/v071-baseline.yml` runs Python 3.13, installs `.[dev]` + IPython, checks runtime version `0.7.0`, then runs `pytest -q`.

### Task 1 — ordered multi-argument signatures

Status: **complete and GREEN**.

- RED contracts commit: `f92f21e23572e80632938c299d3099948481e6ef` — `test: define multi-argument parser contracts`.
- Product commit: `92e7df2aa1bcbb2ee29b025143a0ff8331679b86` — `feat: parse multi-argument function signatures`.
- Verified complete suite after Task 1: **358/358 GREEN**.
- `ParsedStatement.parameters` and `UserFunction.parameters` are ordered tuples.
- One-argument compatibility remains available through `.parameter`.
- Zero-argument, duplicate, invalid and reserved parameter names are rejected.

### Task 2 — symbolic multi-argument binding

Status: **complete and GREEN**.

- RED contracts commit: `cf49ab48c9171f0c701279430023ec637a960433` — `test: define multi-argument symbolic binding contracts`.
- Product commit: `b899eb26a21061fd63aafa91f97ae32da0c2925a` — `feat: bind multi-argument functions symbolically`.
- Temporary Task 2 applicator was removed by `05577d3052a5b11c4f38ce6c3a67b75dd8147040`.
- Verified complete suite after Task 2: **366/366 GREEN**.
- Calls use exact positional arity.
- Local parameters shadow same-named symbolic context values.
- Parameter substitutions are simultaneous rather than sequential.
- Function redefinition replaces the active signature; there is no overload-by-arity.
- Nested user functions compose symbolically.
- Inverse-trig preservation through substitution remains intact.

### Task 3 — fully numeric multi-argument evaluation with units

Status: **complete and GREEN**.

- RED contracts commit: `29a45f14a1e1b4575f40f84f66c96dc07a065664` — `test: define multi-argument numeric contracts`.
- RED evidence: **5 failed, 367 passed**. The five failures were the intended pre-implementation limitation where `numeric(...)` still required a single user-function argument. The local-parameter-vs-numeric-context shadowing contract already passed.
- Product commit: `eab52107558f98843162c4ce45cfa0b3f8108410` — `feat: evaluate multi-argument functions numerically`.
- Product behavior added:
  - tuple-based `display_arguments` with one-argument compatibility property;
  - independent AST-first/Pint resolution of every positional argument;
  - numeric arguments such as `1.2*qD + 1.6*qL`;
  - dimensional zero in any argument position;
  - nested numeric user-function arguments such as `qU(qD, qL)`;
  - local numeric parameter values passed as overrides without mixing Pint quantities into SymPy.
- Temporary Task 3 workflow removed by `d94b75391e56e0255ef95fb1a1006521ec77c66b`.
- Temporary Task 3 patch script removed by `6926682a80f6352be6229f0e221a90b23d5d515b`.
- Compare from RED `29a45f14...` to clean head `6926682a...` changes only `src/engcalc_colab/engine.py` and `src/engcalc_colab/models.py`; no test file changed after the RED contract was frozen.
- Definitive clean-HEAD baseline run: GitHub Actions `33237962065`, head `6926682a80f6352be6229f0e221a90b23d5d515b`, conclusion **success**; the full `pytest -q` step completed successfully.
- Because the frozen RED tree contained 372 tests and no test changed between RED and the verified clean head, Task 3 closes at **372/372 GREEN**.

## Approved behavior inherited from 0.7.0

- `numeric(...)` renders formula → explicit numerical substitution → final result.
- `result(...)` uses the same numerical engine with compact presentation.
- `=` symbolic state and `:=` Pint numeric state remain separate.
- Unit-bearing function arguments are supported, including dimensional zero.
- Existing native plot/envelope behavior remains unchanged, including 201-point sampling and structural positive moment plotted downward.
- Public fixed scalar functions: `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `exp`, `log`; public constant: `pi`.
- Scalar/reserved names cannot be redefined as user scalar assignments, numeric assignments or function parameters.
- `sqrt` propagates units through one-half power.
- `sin`, `cos`, `tan` accept unitless values or explicit angle quantities; degree quantities convert to radians for evaluation.
- `asin`, `acos`, `atan`, `exp`, `log` require truly unitless dimensionless inputs and reject explicit `deg`/`rad` quantities where required by the 0.7.0 contract.
- Inverse trig preserves explicit Pint angle units through numeric evaluation and user-function substitution.

## Active next task — Task 4: generalized partial numeric evaluation

Implement strictly RED → GREEN according to the approved plan.

Required behavior:

```text
M(x, q, L) = q*x*(L-x)/2
qD := 10*kN/m
L := 4*m
numeric(M(x, qD, L))
```

must substitute `qD` and `L` numerically while leaving `x` symbolic.

Task 4 contracts also require:

- any number of unresolved symbols, not just one;
- caller-side unresolved names replace local parameter names correctly (`numeric(f(x, q))` must retain `q`, not local `p`);
- known numeric context symbols referenced inside a function body are substituted too;
- non-polynomial partials such as `A*sin(pi*x/L)` are valid with `evaluated_terms=None`;
- target-unit conversion is rejected whenever the result remains partial.

Planned interfaces:

- `NumericContext.partial_substitutions(expression, allowed_unresolved=None, overrides=None)`;
- arbitrary-count unresolved-symbol tracking;
- hybrid local binding: known local parameters stay as body symbols with Pint overrides, unresolved local parameters are simultaneously replaced by caller-side symbolic expressions;
- `evaluate_partial_polynomial` remains an optional richer presentation only when exactly one unresolved polynomial variable remains.

Task 4 files:

- modify `src/engcalc_colab/numeric.py`;
- modify `src/engcalc_colab/engine.py`;
- create `tests/test_partial_numeric_general.py`;
- extend `tests/test_scalar_math_acceptance.py` where required by the approved regression contract.

Exact next execution sequence:

1. Add Task 4 RED contracts only; do not modify production code first.
2. Run `pytest tests/test_partial_numeric_general.py tests/test_scalar_math_acceptance.py -q` and confirm failures are caused by the current one-unresolved-symbol/single-parameter partial-evaluation limitation.
3. Implement the minimum generalized partial-substitution and hybrid binding changes.
4. Run focused GREEN: `pytest tests/test_partial_numeric_general.py tests/test_numeric_function_arguments.py tests/test_scalar_math_acceptance.py -q`.
5. Run the complete source suite and record the new all-green count.
6. Update this file and continue to Task 5 only after fresh verification.

## Release evidence retained from 0.7.0

- Definitive 0.7.0 distribution gate: Actions run `33232439088`.
- Focused scalar contracts: **123 passed**.
- Complete source suite: **350 passed**.
- Real wheel built and installed successfully into a clean virtual environment.
- Source-free installed-wheel full suite: **350 passed**.
- Repeated source suite: **350 passed**.
- Validated artifact ID: `9708946389`.
- 0.7.0 merged through PR #27 only after explicit approval.

## How to resume in a new conversation

Read this file first and inspect branch `feature/v0.7.1-multiarg-partial-eval`. Tasks 1–3 are complete. Task 3's clean verified head before this documentation commit was `6926682a80f6352be6229f0e221a90b23d5d515b`; the definitive clean-head Actions run is `33237962065`. The frozen Task 3 RED tree had 372 tests and no tests changed afterward, so Task 3 closes at 372/372 GREEN. Resume with **Task 4 RED — generalized partial numeric evaluation**. Do not invoke Codex for EngCalc without explicit user authorization, do not bump the version until release closure, and do not merge without explicit user approval.
