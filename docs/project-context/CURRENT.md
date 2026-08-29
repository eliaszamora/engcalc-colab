# EngCalc Current Project Context

_Last updated: 2026-08-29 after EngCalc 0.7.1 Task 5 was verified GREEN and its temporary verifier was removed._

## Active milestone

- Repository: `eliaszamora/engcalc-colab`.
- Active branch: `feature/v0.7.1-multiarg-partial-eval`.
- Release baseline: merged EngCalc **0.7.0** on `main`.
- 0.7.0 merge commit: `03212e2c47f16492e87aadc451efe8bee6b3ee11` (PR #27).
- 0.7.1 target: **multi-argument user functions and generalized partial numeric evaluation**.
- Approved plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md` on `planning/v0.7.1-multiarg-partial-eval`.
- Do not bump package/runtime version until Task 7 release closure.
- Do not merge 0.7.1 without explicit user approval.
- **Do not invoke Codex, `@codex review`, Codex Cloud, or anything that consumes the user's Codex quota without explicit user authorization.**

## 0.7.1 execution state

### Task 0 — baseline

Status: **complete and GREEN**.

- Started from merged 0.7.0.
- Baseline suite: **350/350 GREEN**.
- `.github/workflows/v071-baseline.yml` intentionally checks runtime version `0.7.0` until Task 7.

### Task 1 — ordered multi-argument signatures

Status: **complete and GREEN**.

- RED: `f92f21e23572e80632938c299d3099948481e6ef`.
- Product: `92e7df2aa1bcbb2ee29b025143a0ff8331679b86`.
- Verified suite: **358/358 GREEN**.
- Function parameters are ordered tuples; `.parameter` keeps one-argument compatibility.

### Task 2 — symbolic multi-argument binding

Status: **complete and GREEN**.

- RED: `cf49ab48c9171f0c701279430023ec637a960433`.
- Product: `b899eb26a21061fd63aafa91f97ae32da0c2925a`.
- Temporary applicator removed by `05577d3052a5b11c4f38ce6c3a67b75dd8147040`.
- Verified suite: **366/366 GREEN**.
- Exact positional arity, local shadowing, simultaneous substitution, function redefinition, nested user functions, and inverse-trig preservation are covered.

### Task 3 — fully numeric multi-argument evaluation with units

Status: **complete and GREEN**.

- RED: `29a45f14a1e1b4575f40f84f66c96dc07a065664`.
- RED evidence: **5 failed, 367 passed**; failures were exactly the previous single-argument `numeric(...)` limitation.
- Product: `eab52107558f98843162c4ce45cfa0b3f8108410`.
- Clean Task 3 head after temporary tooling removal: `6926682a80f6352be6229f0e221a90b23d5d515b`.
- Definitive run: Actions `33237962065`, success.
- Frozen test count: **372/372 GREEN**.
- Added tuple-based `display_arguments`, independent Pint resolution of positional args, numeric argument expressions, dimensional zero in any position, nested user-function args, and local numeric overrides without Pint leakage into SymPy.

### Task 4 — generalized partial numeric evaluation

Status: **complete and GREEN**.

Required form works semantically:

```text
M(x, q, L) = q*x*(L-x)/2
qD := 10*kN/m
L := 4*m
numeric(M(x, qD, L))
```

`qD` and `L` resolve numerically while `x` remains symbolic.

Evidence:

- RED contracts: `33163951d8ea969e0b65b1397e390ecdb5c10189`.
- RED Actions `33238112694`: **6 failed, 3 passed** as expected.
- First product: `eb20fedae7c56bd0939a6a62fdd220529ab57ee0`.
- First GREEN attempt: focused **14 passed**; full suite **1 failed, 377 passed** due a backward-compatibility regression that allowed missing global body dependencies to remain symbolic.
- Corrective product: `17581bf51c7307146c88edca42b56470be6d2b56` — only caller-side symbolic arguments may define allowed unresolved names; missing body globals remain errors.
- Clean product/test head after tooling removal: `870c9a18fc4221da64ada95873f0318dead7297f`.
- Clean baseline Actions `33238401875`: success.
- Final focused + full Actions `33238407627`: success.
- Frozen suite: **378/378 GREEN**.

Task 4 behavior includes arbitrary unresolved caller symbols, caller-name retention, known body-context substitutions, optional one-variable polynomial presentation, valid non-polynomial partials, and rejection of target-unit conversion while a result remains partial.

### Task 5 — multi-argument rendering and real `%%eng` acceptance

Status: **complete and GREEN**.

RED acceptance contracts:

- Added `tests/test_multiarg_acceptance.py` in `ae152b3993b37e9ba87312e7abfa2619fd1c5e32`.
- Contracts cover:
  - fully numeric and partial `M(x, q, L)` inside real `%%eng`;
  - non-polynomial `v(x, A, L) = A*sin(pi*x/L)` partial rendering;
  - compact `result(M(2*m, qD, L), kN*m)` without explicit substitution stage.
- RED Actions `33238578261`: **3 failed, 15 passed**.
- All three failures were exactly the renderer's use of one-argument compatibility properties: definitions/calls rendered as bare `M` or `v` instead of preserving ordered argument tuples. Numeric semantics were already correct.

Product implementation:

- Product commit: `0329063e2a01ceff5b8ffa10d677520c81dce38c` — `feat: render multi-argument evaluations`.
- Only `src/engcalc_colab/renderer.py` required a product change; `models.py` already contained tuple-based `parameters` and `display_arguments`.
- Renderer now consumes `statement.parameters` and `result.display_arguments` directly.
- `_render_function_call_lhs` joins arbitrary positive positional argument tuples in order.
- `_render_lhs` joins arbitrary ordered parameter tuples while preserving one-argument compatibility and special `Sigma_...` naming.
- Existing structural partial fallback already rendered known substitutions and remaining symbolic structure without fabricating a final quantity, so no new numerical behavior was added.
- Two early applicator attempts stopped before product mutation because deterministic staging guards were too strict/miscounted references; the tests and product design were not relaxed. The third applicator run succeeded.
- Temporary applicator workflow removed by `a3e6b2c76d2645f3e747a911cba8ce794f45fc2d`.
- Temporary patch script removed by `bfe29b817135f8eaad62fca5a2a0d5e62fdda130`.

Verification:

- Final Task 5 Actions `33238752978`:
  - focused `test_multiarg_acceptance.py + test_magic.py + test_adaptive_mathjax_wrapping.py + test_numeric_function_magic_acceptance.py`: success;
  - complete source suite: success.
- Temporary final verifier removed by `919833205f14ab0af7bb4bcd066411e070278245`.
- Task 5 added exactly three tests to the 378-test Task 4 suite, therefore Task 5 closes at **381/381 GREEN**.

## Approved behavior inherited from 0.7.0

- `numeric(...)`: formula → explicit numerical substitution → final result.
- `result(...)`: same numerical engine with compact presentation.
- `=` symbolic state and `:=` Pint numeric state remain separate.
- Existing plot/envelope semantics remain unchanged, including 201-point sampling and structural positive moment plotted downward.
- Public scalar functions: `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `exp`, `log`; public constant: `pi`.
- Existing scalar-math unit semantics and inverse-trig preservation remain compatibility requirements.

## Active next task — Task 6: plot, envelope, and backward-compatibility integration gate

Task 6 is an integration gate. Add the approved tests first. If they are already GREEN, **do not modify plotting/envelope production code**.

Required integration contracts:

1. Direct multi-argument response plotting:

```text
M(x, q, L) = q*x*(L-x)/2
qD := 4*kN/m
L := 5*m
plot(M(x, qD, L), x, 0*m, L)
```

must produce 201 samples and midpoint `12.5 kN*m`.

2. Specialized one-variable wrapper built from a multi-argument function:

```text
M_D(x) = M(x, qD, L)
plot(M_D(x), x, 0*m, L)
```

must behave identically at the midpoint.

3. Envelope integration:

```text
M_D(x) = M(x, qD, L)
M_U(x) = M(x, 1.2*qD + 1.6*qL, L)
envelope(M_D(x), M_U(x), x, 0*m, L)
```

must use the existing envelope machinery and 201-point grid.

No Cartesian multi-parameter sweep is added.

Task 6 files per approved plan:

- extend `tests/test_plot_engine.py`;
- extend `tests/test_envelope_engine.py`;
- extend `tests/test_multiarg_acceptance.py` only where real magic acceptance adds useful coverage;
- modify `src/engcalc_colab/engine.py` only if the integration tests reveal a real defect;
- update this file after verification.

Exact next sequence:

1. Add direct + specialized multi-argument plot tests and specialized envelope integration test.
2. Run `pytest tests/test_plot_engine.py tests/test_envelope_engine.py tests/test_multiarg_acceptance.py -q`.
3. If GREEN immediately, make no production plot/envelope change. If RED, diagnose before modifying product.
4. Run `pytest -q`.
5. Record functional-completion SHA/counts here and proceed to Task 7 only after fresh verification.

## Remaining approved release path

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

Read this file first and inspect `feature/v0.7.1-multiarg-partial-eval`. Tasks 0–5 are complete. Task 5 closes at **381/381 GREEN**, product commit `0329063e2a01ceff5b8ffa10d677520c81dce38c`, final focused/full run `33238752978`, verifier cleanup `919833205f14ab0af7bb4bcd066411e070278245`. Resume with **Task 6 integration gate — plot/envelope compatibility**. Do not invoke Codex without explicit user authorization, do not bump the version before Task 7, and do not merge without explicit user approval.
