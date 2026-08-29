# EngCalc Current Project Context

_Last updated: 2026-08-29 after EngCalc 0.7.1 Task 6 was verified GREEN and its temporary verifier was removed._

## Active milestone

- Repository: `eliaszamora/engcalc-colab`.
- Active branch: `feature/v0.7.1-multiarg-partial-eval`.
- Release baseline: merged EngCalc **0.7.0** on `main`.
- 0.7.0 merge commit: `03212e2c47f16492e87aadc451efe8bee6b3ee11` (PR #27).
- 0.7.1 target: **multi-argument user functions and generalized partial numeric evaluation**.
- Approved plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md` on `planning/v0.7.1-multiarg-partial-eval`.
- Functional implementation is complete through Task 6.
- Do not merge 0.7.1 without explicit user approval.
- **Do not invoke Codex, `@codex review`, Codex Cloud, or anything that consumes the user's Codex quota without explicit user authorization.**

## 0.7.1 execution state

### Task 0 — baseline

Status: **complete and GREEN**.

- Started from merged 0.7.0.
- Baseline suite: **350/350 GREEN**.

### Task 1 — ordered multi-argument signatures

Status: **complete and GREEN**.

- RED: `f92f21e23572e80632938c299d3099948481e6ef`.
- Product: `92e7df2aa1bcbb2ee29b025143a0ff8331679b86`.
- Verified suite: **358/358 GREEN**.
- Function parameters are ordered tuples; `.parameter` preserves one-argument compatibility.
- Zero-argument, duplicate, invalid and reserved parameter names are rejected.

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
- RED evidence: **5 failed, 367 passed**; failures were exactly the historical single-argument `numeric(...)` limitation.
- Product: `eab52107558f98843162c4ce45cfa0b3f8108410`.
- Clean Task 3 head: `6926682a80f6352be6229f0e221a90b23d5d515b`.
- Definitive Actions run: `33237962065`, success.
- Frozen test count: **372/372 GREEN**.
- Added tuple-based `display_arguments`, independent Pint resolution of positional arguments, numeric expressions such as `1.2*qD + 1.6*qL`, dimensional zero in any position, nested user-function arguments, and local numeric overrides without Pint leakage into SymPy.

### Task 4 — generalized partial numeric evaluation

Status: **complete and GREEN**.

Required form works:

```text
M(x, q, L) = q*x*(L-x)/2
qD := 10*kN/m
L := 4*m
numeric(M(x, qD, L))
```

`qD` and `L` resolve numerically while `x` remains symbolic.

- RED contracts: `33163951d8ea969e0b65b1397e390ecdb5c10189`.
- RED Actions `33238112694`: **6 failed, 3 passed** as expected.
- First product: `eb20fedae7c56bd0939a6a62fdd220529ab57ee0`.
- First GREEN attempt: focused **14 passed**; full suite **1 failed, 377 passed** because missing global body dependencies were accidentally allowed to remain symbolic.
- Corrective product: `17581bf51c7307146c88edca42b56470be6d2b56` — only caller-side symbolic arguments can define allowed unresolved names; missing body globals remain errors.
- Clean product/test head: `870c9a18fc4221da64ada95873f0318dead7297f`.
- Clean baseline Actions `33238401875`: success.
- Final focused + full Actions `33238407627`: success.
- Frozen suite: **378/378 GREEN**.
- Supports arbitrary unresolved caller symbols, caller-name retention, known body-context substitutions, optional one-variable polynomial presentation, valid non-polynomial partials, and rejection of target-unit conversion while partial.

### Task 5 — multi-argument rendering and real `%%eng` acceptance

Status: **complete and GREEN**.

- RED acceptance tests added in `ae152b3993b37e9ba87312e7abfa2619fd1c5e32`.
- RED Actions `33238578261`: **3 failed, 15 passed**.
- Failures were isolated to one-argument renderer compatibility properties; semantics were already correct.
- Product: `0329063e2a01ceff5b8ffa10d677520c81dce38c` — `feat: render multi-argument evaluations`.
- Renderer consumes `statement.parameters` and `result.display_arguments` directly and renders arbitrary ordered tuples.
- Existing non-polynomial partial fallback remains structural and never invents a final quantity.
- Temporary applicator removed by `a3e6b2c76d2645f3e747a911cba8ce794f45fc2d`; patch script removed by `bfe29b817135f8eaad62fca5a2a0d5e62fdda130`.
- Final Actions `33238752978`: focused and complete source suite success.
- Task 5 closes at **381/381 GREEN**.

### Task 6 — plot, envelope, and backward-compatibility integration gate

Status: **complete and GREEN**.

Frozen integration tests:

- Test commit: `a5e13c7f9b67b4cbe4998fe4ab9f3a1ed896915c` — `test: cover multi-argument plotting integration`.
- Added two plot contracts:
  - direct `plot(M(x, qD, L), x, 0*m, L)`;
  - specialized `M_D(x) = M(x, qD, L)` followed by `plot(M_D(x), ...)`.
- Added one envelope contract using `M_D(x)` and `M_U(x) = M(x, 1.2*qD + 1.6*qL, L)`.
- Required 201 samples and midpoint values `12.5 kN*m` for the base response and `25.0 kN*m` for the factored envelope source.

Verification:

- Temporary test applicator workflow removed by `9c4497a875de39d6976fb693faa76f4f11452c14`.
- Temporary test script removed by `c64dd96f4c4e6d7a412e71c215c9553360452d81`.
- Dedicated Task 6 verification run: Actions `33238999984`, validated head `b50e744912752cb159dd01a406b90570455e4a78`.
- Focused gate `tests/test_plot_engine.py tests/test_envelope_engine.py tests/test_multiarg_acceptance.py`: **39/39 passed**.
- Complete source suite: **384/384 passed**.
- The focused tests were GREEN immediately; therefore **no production plotting/envelope code was modified and `engine.py` was left unchanged**.
- Temporary Task 6 verifier removed by `e2579c6a9177246cb06c8c3163098e3eb638e09e`.

Functional completion through Tasks 1–6 is therefore established at **384/384 GREEN**.

## Approved behavior inherited from 0.7.0

- `numeric(...)`: formula → explicit numerical substitution → final result.
- `result(...)`: same numerical engine with compact presentation.
- `=` symbolic state and `:=` Pint numeric state remain separate.
- Plot/envelope semantics remain unchanged, including 201-point sampling and structural positive moment plotted downward.
- Public scalar functions: `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `exp`, `log`; public constant: `pi`.
- Existing scalar-math unit semantics and inverse-trig preservation remain compatibility requirements.

## Active next task — Task 7: documentation, version 0.7.1, and definitive distribution gate

Task 7 is the release closure. It may now bump the package/runtime version because functional completion is established.

Required steps:

1. Update README with executable 0.7.1 forms:

```text
M(x) = q*x*(L-x)/2
M_param(x, q) = q*x*(L-x)/2
M_base(x, q, L) = q*x*(L-x)/2
qU(qD, qL) = 1.2*qD + 1.6*qL
M_U(x) = M_base(x, qU(qD, qL), L)
v(x, A, L) = A*sin(pi*x/L)
```

Document unsupported defaults, keyword arguments, variadics, overloads, and Cartesian multi-parameter sweeps.

2. Bump `pyproject.toml` and `src/engcalc_colab/__init__.py` to `0.7.1`.
3. Rename/update `tests/test_release_version_v070.py` to `tests/test_release_version_v071.py` and update all required version assertions.
4. Run focused release contracts and complete source suite.
5. Build a real `engcalc_colab-0.7.1-py3-none-any.whl`.
6. Install it into a clean venv.
7. From outside the checkout with empty `PYTHONPATH`, prove import from `site-packages` and smoke fully numeric, partial, non-polynomial, nested combination, plot, dimensional-zero and exact-arity behavior.
8. Run the complete suite against the installed wheel with source excluded.
9. Repeat the complete source suite.
10. Record run ID, validated SHA, all counts, wheel artifact ID/digest and clean import path here.
11. Remove the temporary distribution workflow and prove chain of custody: validated SHA → final branch head may differ only by workflow removal and this context file.
12. Prepare/open the PR only after the distribution gate is authoritative. Do not request Codex review.
13. Stop before merge and wait for explicit user approval.

## Release evidence retained from 0.7.0

- Definitive 0.7.0 distribution gate: Actions `33232439088`.
- Focused scalar contracts: **123 passed**.
- Complete source suite: **350 passed**.
- Real wheel built and installed into a clean virtual environment.
- Source-free installed-wheel full suite: **350 passed**.
- Repeated source suite: **350 passed**.
- Validated artifact ID: `9708946389`.
- 0.7.0 merged through PR #27 only after explicit approval.

## How to resume in a new conversation

Read this file first and inspect `feature/v0.7.1-multiarg-partial-eval`. Tasks 0–6 are complete. Functional completion is **384/384 GREEN**. Task 6 integration evidence is Actions `33238999984`; no plot/envelope production changes were needed. Resume with **Task 7 release closure**. Do not invoke Codex without explicit user authorization and do not merge without explicit user approval.
