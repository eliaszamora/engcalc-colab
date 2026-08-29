# EngCalc Current Project Context

_Last updated: 2026-08-29 after the definitive EngCalc 0.7.1 distribution gate._

## Release state

- Repository: `eliaszamora/engcalc-colab`.
- Release branch: `feature/v0.7.1-multiarg-partial-eval`.
- Base release on `main`: EngCalc **0.7.0**, merge commit `03212e2c47f16492e87aadc451efe8bee6b3ee11` (PR #27).
- Current candidate: EngCalc **0.7.1 — multi-argument user functions and generalized partial numeric evaluation**.
- Approved implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md` on `planning/v0.7.1-multiarg-partial-eval`.
- Tasks 0–7 are implemented and distribution-validated.
- **Do not merge without explicit user approval.**
- **Do not invoke Codex, `@codex review`, Codex Cloud, or anything that consumes the user's Codex quota without explicit user authorization.**

## Functional implementation history

### Task 0 — 0.7.0 baseline

- Started from merged 0.7.0.
- Baseline: **350/350 GREEN**.

### Task 1 — ordered multi-argument signatures

- RED: `f92f21e23572e80632938c299d3099948481e6ef`.
- Product: `92e7df2aa1bcbb2ee29b025143a0ff8331679b86`.
- Verified: **358/358 GREEN**.
- Function parameters are ordered tuples; `.parameter` preserves one-argument compatibility.
- Zero-argument, duplicate, invalid and reserved parameter names are rejected.

### Task 2 — symbolic multi-argument binding

- RED: `cf49ab48c9171f0c701279430023ec637a960433`.
- Product: `b899eb26a21061fd63aafa91f97ae32da0c2925a`.
- Verified: **366/366 GREEN**.
- Exact positional arity, simultaneous substitution, local shadowing, redefinition without overload-by-arity, nested user functions and inverse-trig preservation are covered.

### Task 3 — fully numeric multi-argument evaluation

- RED: `29a45f14a1e1b4575f40f84f66c96dc07a065664`.
- RED evidence: **5 failed, 367 passed**; all failures were the previous single-argument `numeric(...)` restriction.
- Product: `eab52107558f98843162c4ce45cfa0b3f8108410`.
- Clean verification: Actions `33237962065`.
- Closed at **372/372 GREEN**.
- Supports independent Pint resolution for each argument, argument expressions such as `1.2*qD + 1.6*qL`, dimensional zero in any argument position and nested user-function arguments.

### Task 4 — generalized partial numeric evaluation

- RED tests: `33163951d8ea969e0b65b1397e390ecdb5c10189`.
- RED Actions `33238112694`: **6 failed, 3 passed**.
- First product: `eb20fedae7c56bd0939a6a62fdd220529ab57ee0`.
- First GREEN attempt found one real backward-compatibility regression: focused **14 passed**, full **1 failed, 377 passed** because a missing global body dependency could remain unresolved.
- Corrective product: `17581bf51c7307146c88edca42b56470be6d2b56`.
- Correct rule: only caller-supplied symbolic argument names may remain unresolved; missing global dependencies inside the body remain errors.
- Final Actions `33238407627` plus clean baseline `33238401875`.
- Closed at **378/378 GREEN**.
- Supports multiple unresolved caller symbols, caller-name retention, known numeric context substitutions, one-variable polynomial enhancement and non-polynomial structural partials with `evaluated_terms=None`.

### Task 5 — multi-argument rendering and real `%%eng`

- RED tests: `ae152b3993b37e9ba87312e7abfa2619fd1c5e32`.
- RED Actions `33238578261`: **3 failed, 15 passed**; all failures were renderer LHS loss from singular compatibility properties.
- Product: `0329063e2a01ceff5b8ffa10d677520c81dce38c`.
- Renderer now consumes tuple-based `statement.parameters` and `result.display_arguments`, preserving ordered forms such as `M(x, q, L)`.
- Final Actions `33238752978`.
- Closed at **381/381 GREEN**.

### Task 6 — plot/envelope integration

- Integration tests: `a5e13c7f9b67b4cbe4998fe4ab9f3a1ed896915c`.
- Covers direct `plot(M(x, qD, L), ...)`, a specialized one-variable wrapper built from a multi-argument function, and an envelope using `M_D(x)` / `M_U(x)`.
- Actions `33238999984`: focused **39/39 GREEN**, full **384/384 GREEN**.
- The new integration contracts passed immediately, so **no plotting/envelope production change was made and `engine.py` remained unchanged in Task 6**.

## Task 7 — 0.7.1 release closure

Status: **distribution-validated; branch ready for PR review, not merge**.

### TDD release-version gate

- Version contracts were changed before production metadata:
  - `tests/test_packaging.py` -> requires 0.7.1: `287f0b1a0039df50f9d826a916d40dda0e36affb`.
  - `tests/test_parser.py` -> runtime 0.7.1: `62d0686ac9dc6bff93cc6d0bcdd619505a49508f`.
  - new `tests/test_release_version_v071.py`: `038e6e2272a82e13f111b14804cb30b6dbfc1374`.
  - old `tests/test_release_version_v070.py` removed in `445ecc13854a455c3b598d3738a4ab4e65b1d805`.
- RED Actions `33239153967`: **5 failed, 379 passed**.
- The five failures were exclusively expected 0.7.1-vs-0.7.0 metadata/runtime assertions; no functional regression appeared.

### Release metadata and documentation

- Release product/docs commit: `7daab3a1d6e3aa27148397d2278c53abac0f285d` — `release: prepare EngCalc 0.7.1 metadata and docs`.
- `pyproject.toml`: `version = "0.7.1"`.
- `src/engcalc_colab/__init__.py`: `__version__ = "0.7.1"`.
- README current version is 0.7.1 and documents executable forms:

```text
M(x) = q*x*(L-x)/2
M_param(x, q) = q*x*(L-x)/2
M_base(x, q, L) = q*x*(L-x)/2
qU(qD, qL) = 1.2*qD + 1.6*qL
M_U(x) = M_base(x, qU(qD, qL), L)
v(x, A, L) = A*sin(pi*x/L)
```

- README also documents generalized partials, nested functions, exact positional arity, integration with plot/envelope and the intentionally unsupported defaults, keyword arguments, variadics, overload-by-arity and Cartesian multi-parameter sweeps.

### Definitive distribution gate

- Validated SHA: `5a02014df0dcf6a2e4e4b99207597611bd271187`.
- GitHub Actions run: `33239360930` — **success**.
- Python: 3.13.
- Release metadata: **0.7.1 verified**.
- Focused release contracts: **39/39 passed**.
- Complete source suite: **384/384 passed**.
- Real wheel built: `engcalc_colab-0.7.1-py3-none-any.whl` with `Version: 0.7.1` verified inside wheel METADATA.
- Wheel installed into a clean virtual environment.
- Outside-checkout smoke ran with `PYTHONPATH=''` and imported from:
  `/tmp/engcalc-v071-final-wheel-venv/lib/python3.13/site-packages/engcalc_colab/__init__.py`.
- Installed-wheel smoke verified:
  - fully numeric multi-argument evaluation (`20 kN*m` case);
  - generalized partial evaluation preserving `x`;
  - non-polynomial partial evaluation;
  - nested `qU(qD,qL)` -> `M_U(x)` composition;
  - native 201-point plotting and midpoint result;
  - dimensional zero preserving units;
  - exact arity rejection.
- Complete suite against installed wheel with `src/` excluded and `PYTHONPATH=''`: **384/384 passed**.
- Repeated complete source suite: **384/384 passed**.
- Validated artifact:
  - ID: `9710919105`;
  - name: `engcalc-colab-0.7.1-final-wheel`;
  - size: `29228` bytes;
  - digest: `sha256:90e0cec9932f1a3b1d82fe85d34a6d6227f2dfd46782a65f972d0cd14d1b82cd`;
  - expires: 2026-11-27.
- Temporary distribution workflow removed by `65d51f8d822f9a5be847ad9c2173ae22a389353a`.

## Release behavior summary

EngCalc 0.7.1 now supports user functions with any positive number of ordered positional parameters while retaining the existing one-argument form. Symbolic binding is simultaneous; local parameters shadow context only locally; redefinition replaces a signature rather than creating overloads. Fully numeric calls support Pint quantities, direct unit expressions, numeric combinations, dimensional zero and nested user functions.

`numeric(...)` can also partially evaluate a multi-argument function by substituting all known values while preserving one or more caller-supplied symbolic names. One-variable polynomial partials retain evaluated-coefficient presentation; non-polynomial partials retain substituted symbolic structure. Target-unit conversion is still restricted to fully numeric results.

The existing native plot/envelope API remains unchanged. Direct multi-argument response expressions and specialized one-variable wrappers use the existing 201-point sampling and structural sign conventions. No Cartesian multi-parameter sweep was added.

## Release-control boundary

The release candidate has passed the definitive distribution gate. The only permitted changes after validated SHA `5a02014d...` before opening the PR are removal of the temporary distribution workflow and this context update. A later comparison must confirm no `src/`, tests, README or release metadata changed after validation.

Next steps:

1. Verify chain of custody from validated SHA `5a02014d...` to current branch head.
2. Inspect the full `main...feature/v0.7.1-multiarg-partial-eval` diff.
3. Open the 0.7.1 PR if the diff is clean.
4. **Stop before merge and wait for explicit user approval.**

## How to resume in a new conversation

Read this file first. Functional work through Task 6 closed at **384/384 GREEN**. Task 7 definitive distribution evidence is Actions `33239360930`, validated SHA `5a02014df0dcf6a2e4e4b99207597611bd271187`, artifact `9710919105`, with source 384/384, source-free installed-wheel 384/384 and repeated source 384/384. Verify chain of custody, inspect/open the PR, but do not merge without explicit user approval and do not use Codex without explicit authorization.
