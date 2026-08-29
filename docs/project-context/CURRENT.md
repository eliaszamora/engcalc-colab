# EngCalc Current Project Context

_Last updated: 2026-08-29 after addressing the three findings raised by the repository-configured automatic review on PR #28; a fresh definitive 0.7.1 distribution gate is still required before the already-approved merge._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` remains on merged EngCalc **0.7.0**; 0.7.0 PR #27 merge commit: `03212e2c47f16492e87aadc451efe8bee6b3ee11`.
- Active release branch: `feature/v0.7.1-multiarg-partial-eval`.
- Open release PR: **#28 — `release: EngCalc 0.7.1 multi-argument functions`** against `main`.
- Release candidate version: **0.7.1** in both `pyproject.toml` and `src/engcalc_colab/__init__.py`.
- Current branch head before this context commit: `75e0d6454cb00fc080795bf7f23cefacc00cd552`.
- Latest product corrective: `4a46bbf7c48373a5d40c03edf99cfa8343d48573` — `fix: ignore unused unresolved numeric parameters`.
- Approved design is now persistent in the release tree:
  - `docs/superpowers/specs/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-design.md`;
  - `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md`.
- The user has explicitly approved merging PR #28. The merge is deliberately paused until the review findings are closed with a new authoritative distribution gate.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume the user's Codex quota without explicit authorization.

## Approved behavior

- User functions accept one or more ordered positional parameters. Existing one-argument syntax remains compatible.
- Calls require exact positional arity. Defaults, keyword calls, variadics, keyword-only parameters and overload-by-arity are not supported.
- Parameter substitution is simultaneous. Local parameters shadow same-named context symbols only inside their function body.
- `=` symbolic state and `:=` Pint-backed numeric state remain separate.
- Fully numeric multi-argument calls preserve Pint units, direct numeric expressions, nested user functions and dimensional zero in any argument position.
- Generalized partial evaluation substitutes every known numeric value and preserves only dependencies that remain symbolic **after substitution**.
- An unresolved caller argument whose corresponding parameter is unused by the function body does **not** make the result partial. Example: `f(x, y) = x`; `numeric(f(2*m, y), cm)` is a fully numeric result equal to `200 cm`.
- Only caller-supplied symbolic arguments may remain intentionally unresolved. Missing global/body numeric dependencies remain strict errors.
- Target-unit conversion is rejected only when symbols actually remain unresolved in the resulting expression.
- Non-polynomial partials preserve truthful symbolic structure and do not fabricate a final unit.
- Existing scalar-math semantics from 0.7.0 remain unchanged, including inverse-trig angle handling.
- Existing plot/envelope APIs remain unchanged: 201-point sampling and structural positive moment plotted downward are preserved. No Cartesian multi-parameter sweep was added.

## Open issues / user feedback

- Opening PR #28 triggered the repository-configured automatic Codex review. No manual `@codex review` or Codex Cloud review action was requested by this workflow.
- Review finding 1: `CURRENT.md` had lost the mandatory stable headings required by `AGENTS.md`. This file restores them.
- Review finding 2: the approved 0.7.1 spec/plan existed only on the planning branch. Both are now persisted in the release tree by commit `75e0d6454cb00fc080795bf7f23cefacc00cd552`.
- Review finding 3: an unresolved but unused function parameter could incorrectly force `numeric(...)` into a partial result. The defect was reproduced RED and fixed in `4a46bbf7c48373a5d40c03edf99cfa8343d48573`.
- Remaining release blocker: run a new definitive source/wheel distribution gate on the corrected tree, then update PR evidence, resolve the three review threads and execute the already-approved merge.

## Validation evidence

### Functional 0.7.1 implementation before PR review

- Task 0 baseline: **350/350**.
- Task 1 ordered signatures: **358/358**.
- Task 2 symbolic binding: **366/366**.
- Task 3 numeric multi-argument evaluation: **372/372**; final Actions `33237962065`.
- Task 4 generalized partial evaluation: **378/378**; final Actions `33238407627`.
- Task 5 rendering / real `%%eng`: **381/381**; Actions `33238752978`.
- Task 6 plot/envelope integration: focused **39/39**, full **384/384**; Actions `33238999984`; no plotting production change required.

### Original 0.7.1 distribution gate — historical after review corrective

Actions `33239360930` on SHA `5a02014df0dcf6a2e4e4b99207597611bd271187` passed:

- focused release contracts: **39/39**;
- complete source suite: **384/384**;
- real `engcalc_colab-0.7.1-py3-none-any.whl` built and metadata verified;
- clean-venv smoke from `/tmp` with `PYTHONPATH=''` importing from `site-packages`;
- source-free installed-wheel suite: **384/384**;
- repeated source suite: **384/384**;
- artifact ID `9710919105`, digest `sha256:90e0cec9932f1a3b1d82fe85d34a6d6227f2dfd46782a65f972d0cd14d1b82cd`.

This gate is no longer authoritative for merge because the review corrective changed production code and added two tests afterward.

### Review corrective RED → GREEN

- Regression tests added in `e2ee4d4e3e31f0d446741779bca16a71277c08a8` for unused unresolved parameters, with and without target-unit conversion.
- RED Actions `33259267930`: **2 failed, 6 passed**, reproducing exactly the reported defect.
- Product corrective: `4a46bbf7c48373a5d40c03edf99cfa8343d48573`.
- GREEN Actions `33259332512`:
  - focused numeric/partial regression: **19/19 passed**;
  - complete source suite: **386/386 passed**.
- Temporary corrective workflow and applicator were removed in the product corrective commit.
- Approved spec and plan persistence workflow succeeded as Actions `33259426881`; its temporary workflow self-removed in commit `75e0d6454cb00fc080795bf7f23cefacc00cd552`.

## Roadmap / active plan

- Active milestone: **EngCalc 0.7.1 — multi-argument user functions and generalized partial numeric evaluation**.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-design.md`.
- Approved implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md`.
- Tasks 0–7 are functionally implemented. The remaining work is release-control closure after review corrective.
- Current source test count is **386**.
- Release closure still requires: fresh source suite → real wheel → clean install → smoke outside source tree → source-free installed-wheel full suite → repeated source suite → workflow cleanup → chain-of-custody proof.
- User merge approval is already recorded; no second approval is required if the corrected release passes these gates without a new material issue.

## Exact next step

1. Run a new definitive 0.7.1 distribution gate on the corrected tree.
2. Require release metadata 0.7.1, focused multi-argument/release contracts, and **386/386** complete source tests.
3. Build `engcalc_colab-0.7.1-py3-none-any.whl`, verify wheel metadata, and install it into a clean virtual environment.
4. From outside the checkout with `PYTHONPATH=''`, verify import from `site-packages` and smoke fully numeric multi-argument evaluation, generalized partials, non-polynomial partials, nested composition/plotting, dimensional zero, exact arity, and the corrected unused-parameter case `numeric(f(2*m, y), cm) == 200 cm`.
5. Run the complete **386-test** suite against the installed wheel with `src/` excluded, then repeat the complete source suite.
6. Upload the validated wheel artifact, remove the temporary distribution workflow, and update this file with the new authoritative run/SHA/artifact/digest.
7. Prove chain of custody from the validated SHA to the final PR head.
8. Update PR #28 validation text, reply to and resolve the three review threads, and verify the PR remains clean/mergeable.
9. Merge PR #28 using the already-recorded user approval and an expected-head-SHA guard.
10. Verify the merge on `main` and update this context on `main` with the final 0.7.1 release state.

## How to resume in a new conversation

Read this file, then read the persisted 0.7.1 spec and plan above. PR #28 is open and the user has explicitly approved merging it, but the merge is paused for post-review revalidation. The automatic PR review raised three findings: mandatory CURRENT headings, missing persisted approved plan/spec, and an unused unresolved parameter incorrectly forcing partial numeric evaluation. The functional defect was reproduced by RED Actions `33259267930` (2 failed, 6 passed), fixed by `4a46bbf7c48373a5d40c03edf99cfa8343d48573`, and GREEN Actions `33259332512` passed 19 focused and 386 full tests. The spec/plan were persisted by `75e0d6454cb00fc080795bf7f23cefacc00cd552`. CURRENT's mandatory headings are restored by the commit containing this snapshot. Next: run a fresh definitive 0.7.1 distribution gate with 386 tests and the unused-parameter installed-wheel smoke, then clean up, resolve PR review threads and merge PR #28 with the existing approval. Do not manually invoke Codex without explicit authorization.