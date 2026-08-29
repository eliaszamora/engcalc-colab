# EngCalc Current Project Context

_Last updated: 2026-08-29 after EngCalc 0.7.1 Task 4 was verified GREEN and temporary Task 4 tooling was removed._

## Active milestone

- Repository: `eliaszamora/engcalc-colab`.
- Active branch: `feature/v0.7.1-multiarg-partial-eval`.
- Release baseline: merged EngCalc **0.7.0** on `main`.
- 0.7.0 merge commit: `03212e2c47f16492e87aadc451efe8bee6b3ee11` (PR #27).
- 0.7.1 target: **multi-argument user functions and generalized partial numeric evaluation**.
- Approved plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md` on `planning/v0.7.1-multiarg-partial-eval`.
- Do not bump the package/runtime version until release closure.
- Do not merge 0.7.1 without explicit user approval.
- **Do not invoke Codex, `@codex review`, Codex Cloud, or anything that consumes the user's Codex quota without explicit user authorization.**

## 0.7.1 execution state

### Task 0 — baseline

Status: **complete and GREEN**.

- Started from merged 0.7.0.
- Baseline suite: **350/350 GREEN**.
- `.github/workflows/v071-baseline.yml` intentionally checks runtime version `0.7.0` until Task 7 release closure.

### Task 1 — ordered multi-argument signatures

Status: **complete and GREEN**.

- RED: `f92f21e23572e80632938c299d3099948481e6ef` — `test: define multi-argument parser contracts`.
- Product: `92e7df2aa1bcbb2ee29b025143a0ff8331679b86` — `feat: parse multi-argument function signatures`.
- Verified suite: **358/358 GREEN**.
- Function parameters are ordered tuples; `.parameter` keeps one-argument compatibility.
- Zero-argument, duplicate, invalid and reserved parameter names are rejected.

### Task 2 — symbolic multi-argument binding

Status: **complete and GREEN**.

- RED: `cf49ab48c9171f0c701279430023ec637a960433` — `test: define multi-argument symbolic binding contracts`.
- Product: `b899eb26a21061fd63aafa91f97ae32da0c2925a` — `feat: bind multi-argument functions symbolically`.
- Temporary applicator removed by `05577d3052a5b11c4f38ce6c3a67b75dd8147040`.
- Verified suite: **366/366 GREEN**.
- Exact positional arity; local parameters shadow same-named context values; simultaneous substitutions; no overload-by-arity; nested user functions compose symbolically; inverse-trig preservation remains intact.

### Task 3 — fully numeric multi-argument evaluation with units

Status: **complete and GREEN**.

- RED: `29a45f14a1e1b4575f40f84f66c96dc07a065664` — `test: define multi-argument numeric contracts`.
- RED evidence: **5 failed, 367 passed**; failures were exactly the previous single-argument `numeric(...)` limitation.
- Product: `eab52107558f98843162c4ce45cfa0b3f8108410` — `feat: evaluate multi-argument functions numerically`.
- Clean Task 3 head: `6926682a80f6352be6229f0e221a90b23d5d515b` after temporary workflow/script removal.
- Definitive Task 3 run: Actions `33237962065`, success.
- Frozen test count gives **372/372 GREEN**.
- Added tuple-based `display_arguments`, independent Pint resolution of positional arguments, numeric expressions such as `1.2*qD + 1.6*qL`, dimensional zero in any position, nested user-function arguments, and numeric parameter overrides that do not leak Pint quantities into SymPy.

### Task 4 — generalized partial numeric evaluation

Status: **complete and GREEN**.

Required form now works semantically:

```text
M(x, q, L) = q*x*(L-x)/2
qD := 10*kN/m
L := 4*m
numeric(M(x, qD, L))
```

`qD` and `L` are resolved numerically while `x` remains symbolic.

Evidence and commits:

- RED contracts: `33163951d8ea969e0b65b1397e390ecdb5c10189` — created `tests/test_partial_numeric_general.py` with six generalized-partial contracts.
- RED Actions run: `33238112694`; evidence **6 failed, 3 passed**. All six failures were the expected pre-Task-4 inability to preserve unresolved caller symbols.
- First product implementation: `eb20fedae7c56bd0939a6a62fdd220529ab57ee0` — `feat: generalize partial numeric evaluation`.
- First GREEN attempt showed the new contracts themselves were healthy: focused set **14 passed**; full suite exposed one backward-compatibility regression: **1 failed, 377 passed** in `test_numeric_partial_function_requires_all_non_parameter_values`.
- Root cause: the first implementation passed `allowed_unresolved=None`, which accidentally permitted missing global body dependencies as partial symbols.
- Corrective product commit: `17581bf51c7307146c88edca42b56470be6d2b56` — `fix: preserve strict global dependencies in partial evaluation`.
- Corrective rule: only free symbols originating from explicitly symbolic caller-side arguments are allowed to remain unresolved. Missing global symbols referenced only inside a function body still raise the historical numeric-dependency error.
- Clean product/test head after corrective tooling removal: `870c9a18fc4221da64ada95873f0318dead7297f`.
- Clean-head baseline run: Actions `33238401875`; complete baseline suite success.
- Final focused + full verification run: Actions `33238407627`; both `Focused Task 4 contracts` and `Full source suite` completed successfully.
- Temporary final verifier removed by `0d2cfbc9825733c3703967f238503bdf893e7c2a`.
- Frozen suite size after adding the six Task 4 tests is **378 tests**, therefore Task 4 closes at **378/378 GREEN**.

Task 4 behavior:

- `NumericContext.partial_substitutions(expression, allowed_unresolved=None, overrides=None)` supports arbitrary unresolved-symbol counts while retaining strict dependency checking when an allow-set is supplied.
- Known local parameters remain body symbols backed by Pint overrides.
- Unresolved local parameters are replaced simultaneously by the caller-side symbolic expressions.
- Caller names are retained (`numeric(f(x, q))` keeps `q`, not local parameter `p`).
- Known numeric context symbols referenced inside the function body are included in substitutions.
- `evaluate_partial_polynomial(..., overrides=...)` remains an optional richer presentation when exactly one unresolved polynomial variable remains.
- Non-polynomial partials are valid with `evaluated_terms=None`.
- Target-unit conversion remains forbidden whenever the result is partial.
- One-argument historical boundary is preserved: missing global/non-parameter numeric dependencies still error rather than silently becoming partial variables.

## Approved behavior inherited from 0.7.0

- `numeric(...)` renders formula → explicit numerical substitution → final result.
- `result(...)` uses the same numerical engine with compact presentation.
- `=` symbolic state and `:=` Pint numeric state remain separate.
- Existing plot/envelope behavior remains unchanged, including 201-point sampling and structural positive moment plotted downward.
- Public scalar functions: `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `exp`, `log`; public constant: `pi`.
- Existing scalar-math unit semantics and inverse-trig preservation remain compatibility requirements.

## Active next task — Task 5: multi-argument rendering and real `%%eng` acceptance

Execute strictly RED → GREEN according to the approved plan.

Task 5 files:

- modify `src/engcalc_colab/renderer.py`;
- modify `src/engcalc_colab/models.py` only if needed by the frozen contracts;
- create `tests/test_multiarg_acceptance.py`;
- modify `tests/test_magic.py` for compact `result(...)` regression coverage where appropriate.

Required rendering behavior:

- tuple-based display arguments render calls with any positive number of positional arguments;
- function-definition LHS renders ordered parameter tuples, e.g. `M(x, q, L)`;
- real `%%eng` renders fully numeric multi-argument calls and generalized partial calls in one Math display;
- non-polynomial partial fallback renders known substitutions plus remaining symbolic structure without inventing a final quantity;
- one-variable polynomial partial enhancement remains intact;
- compact `result(...)` remains compact and omits the explicit substitution stage.

Exact next execution sequence:

1. Add Task 5 RED acceptance/rendering tests only.
2. Run `pytest tests/test_multiarg_acceptance.py tests/test_magic.py -q` and record the rendering failures before production changes.
3. Generalize function-call LHS and function-definition LHS rendering.
4. Implement structural partial fallback using existing substitution-aware row rendering.
5. Run focused GREEN:
   `pytest tests/test_multiarg_acceptance.py tests/test_magic.py tests/test_adaptive_mathjax_wrapping.py tests/test_numeric_function_magic_acceptance.py -q`.
6. Run the complete suite and record the new count.
7. Update this file and proceed to Task 6 only after fresh verification.

## Remaining approved release path

- **Task 6:** plot, envelope and full backward-compatibility integration gate. Direct multi-argument response calls and specialized one-argument wrappers must use the existing plot/envelope APIs; no Cartesian parameter sweep is added.
- **Task 7:** README/docs, version bump to 0.7.1, packaging/version tests, real wheel/source-free installation gate, final artifact, branch ready for PR inspection. No automatic merge.

## Release evidence retained from 0.7.0

- Definitive 0.7.0 distribution gate: Actions `33232439088`.
- Focused scalar contracts: **123 passed**.
- Complete source suite: **350 passed**.
- Real wheel built and installed into a clean virtual environment.
- Source-free installed-wheel full suite: **350 passed**.
- Repeated source suite: **350 passed**.
- Validated artifact ID: `9708946389`.
- 0.7.0 merged through PR #27 only after explicit user approval.

## How to resume in a new conversation

Read this file first and inspect `feature/v0.7.1-multiarg-partial-eval`. Tasks 0–4 are complete; Task 4 closes at **378/378 GREEN** with corrective product commit `17581bf51c7307146c88edca42b56470be6d2b56`, clean baseline run `33238401875`, and final focused/full run `33238407627`. Resume with **Task 5 RED — multi-argument rendering and real `%%eng` acceptance**. Do not invoke Codex without explicit user authorization, do not bump the version before Task 7, and do not merge without explicit user approval.
