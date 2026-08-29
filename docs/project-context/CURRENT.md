# EngCalc Current Project Context

_Last updated: 2026-08-29 after EngCalc 0.7.1 was merged through PR #28 and the merged tree was verified against the finalized release branch._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default/canonical branch: `main`.
- Current release: **EngCalc 0.7.1 — multi-argument user functions and generalized partial numeric evaluation**.
- Release PR: **#28 — `release: EngCalc 0.7.1 multi-argument functions`**, merged into `main`.
- Merge commit: `f142a85ae90b657b8f85216f0510e686709ee602`.
- Final PR head: `b6e7effa6aca8a5bb228e02bb02f78b643aec780`.
- Comparison final PR head → merge commit contained **zero changed files**, proving the merge introduced no tree changes beyond merge history.
- Package/runtime version: **0.7.1** in `pyproject.toml` and `src/engcalc_colab/__init__.py`.
- Latest functional corrective included in the release: `4a46bbf7c48373a5d40c03edf99cfa8343d48573` — `fix: ignore unused unresolved numeric parameters`.
- Approved release design is persistent on `main`:
  - `docs/superpowers/specs/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-design.md`;
  - `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md`.
- Release branch `feature/v0.7.1-multiarg-partial-eval` is retained; it has not been deleted.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume the user's Codex quota without explicit authorization.

## Approved behavior

- User functions accept one or more ordered positional parameters; the one-argument form remains compatible.
- Calls require exact positional arity. Defaults, keyword calls, variadics, keyword-only parameters and overload-by-arity are unsupported.
- Parameter substitution is simultaneous. Local parameters shadow same-named context values only inside their function body.
- `=` symbolic state and `:=` Pint-backed numeric state remain separate.
- Fully numeric multi-argument calls preserve Pint units, direct numeric expressions, nested user functions and dimensional zero in any argument position.
- Generalized partial evaluation substitutes every known value and preserves only dependencies that remain symbolic after substitution.
- An unresolved caller argument whose parameter is unused by the function body does not force a partial result. `f(x, y) = x`; `numeric(f(2*m, y), cm)` returns `200 cm`.
- Only caller-supplied symbolic arguments may remain intentionally unresolved. Missing global/body numeric dependencies remain strict errors.
- Target-unit conversion is rejected only when symbols actually remain unresolved in the resulting expression.
- Non-polynomial partials preserve truthful symbolic structure and do not fabricate a final quantity.
- Scalar-math behavior inherited from 0.7.0 remains unchanged.
- Plot/envelope behavior remains unchanged: 201-point sampling and structural positive moment downward. No Cartesian multi-parameter sweep was added.

## Open issues / user feedback

- No known functional blocker remains for 0.7.1.
- Opening PR #28 triggered the repository-configured automatic Codex review; no manual `@codex review` or Codex Cloud review action was initiated as part of the release workflow.
- All three automatic-review findings were addressed before merge:
  1. mandatory stable `CURRENT.md` headings restored and verified by the final gate;
  2. approved spec and plan persisted in the release tree;
  3. unused unresolved parameter partial-evaluation defect reproduced RED, fixed and revalidated through the installed wheel.
- All three PR review threads were replied to and marked resolved before merge.
- Future work should start from this merged 0.7.1 baseline; no 0.7.2 behavior has been approved yet.

## Validation evidence

### Implementation history

- Task 0 baseline: **350/350**.
- Task 1 ordered signatures: **358/358**.
- Task 2 symbolic binding: **366/366**.
- Task 3 numeric multi-argument evaluation: **372/372**, Actions `33237962065`.
- Task 4 generalized partial evaluation: **378/378**, Actions `33238407627`.
- Task 5 renderer / real `%%eng`: **381/381**, Actions `33238752978`.
- Task 6 plot/envelope integration: focused **39/39**, full **384/384**, Actions `33238999984`.

### Review corrective RED → GREEN

- Regression tests: `e2ee4d4e3e31f0d446741779bca16a71277c08a8`.
- RED Actions `33259267930`: **2 failed, 6 passed**, reproducing both unused-parameter symptoms.
- Product corrective: `4a46bbf7c48373a5d40c03edf99cfa8343d48573`.
- GREEN Actions `33259332512`: focused **19/19 passed**, complete source **386/386 passed**.
- Persistent approved spec/plan: commit `75e0d6454cb00fc080795bf7f23cefacc00cd552`; Actions `33259426881`.

### Definitive corrected 0.7.1 distribution gate

- GitHub Actions: `33259552699` — **success**.
- Validated SHA: `2332bd29e571a360cc47a29562e09b5828a3d2cb`.
- Persistent release-context/design checks: **passed**.
- Release metadata: **0.7.1 verified**.
- Focused corrected release contracts: **77/77 passed**.
- Complete source suite: **386/386 passed**.
- Real wheel: `engcalc_colab-0.7.1-py3-none-any.whl`; METADATA verified as `Version: 0.7.1`.
- Wheel installed into a clean virtual environment.
- Outside-checkout smoke with `PYTHONPATH=''` imported from `/tmp/engcalc-v071-corrected-wheel-venv/lib/python3.13/site-packages/engcalc_colab/__init__.py`.
- Installed-wheel smoke covered fully numeric multi-argument evaluation, generalized partials, non-polynomial partials, nested composition/201-point plotting, dimensional zero, exact arity and `numeric(f_unused(2*m, y), cm) == 200 cm`.
- Complete source-free suite against installed wheel: **386/386 passed**.
- Repeated complete source suite: **386/386 passed**.
- Validated wheel artifact:
  - ID: `9716898144`;
  - name: `engcalc-colab-0.7.1-corrected-final-wheel`;
  - size: `29225` bytes;
  - digest: `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`;
  - expires: `2026-11-27`.
- Validated SHA → final PR head changed only by temporary workflow removal and release-context update.
- Final PR head `b6e7effa6aca8a5bb228e02bb02f78b643aec780` → merge commit `f142a85ae90b657b8f85216f0510e686709ee602`: **zero changed files**.

## Roadmap / active plan

- **0.7.1 is complete and merged.**
- Approved 0.7.1 spec and plan are retained as release-history documents on `main`.
- No next feature/release scope has been approved in this context.
- New work should begin by defining the next milestone/spec from the 0.7.1 baseline rather than reopening closed 0.7.1 tasks unless a regression is found.

## Exact next step

- Treat `main` at EngCalc **0.7.1** as the new development baseline.
- If the user requests another feature or release, first inspect this file and the relevant existing architecture/tests, then create/approve the next spec/plan before implementation.
- If a 0.7.1 regression is reported, reproduce it with a RED test against `main` before modifying production code.
- Do not delete the retained release branch unless the user explicitly requests repository cleanup.

## How to resume in a new conversation

Read this file first. EngCalc **0.7.1 is merged on `main` through PR #28**, merge commit `f142a85ae90b657b8f85216f0510e686709ee602`. The finalized release branch head was `b6e7effa6aca8a5bb228e02bb02f78b643aec780`, and comparison to the merge commit had zero changed files. The authoritative corrected distribution gate is Actions `33259552699` on SHA `2332bd29e571a360cc47a29562e09b5828a3d2cb`: 77 focused, 386 source, 386 installed-wheel source-free, 386 repeated source; corrected installed-wheel smoke passed; artifact `9716898144`, digest `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`. The automatic PR review's three findings were corrected and all review threads resolved before merge. Start any future work from the 0.7.1 `main` baseline. Do not manually invoke Codex without explicit authorization.