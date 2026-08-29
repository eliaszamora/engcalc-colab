# EngCalc Current Project Context

_Last updated: 2026-08-29 after the corrected EngCalc 0.7.1 distribution gate passed and its temporary workflow was removed._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` remains on merged EngCalc **0.7.0** until PR #28 is merged.
- Active release branch: `feature/v0.7.1-multiarg-partial-eval`.
- Open release PR: **#28 — `release: EngCalc 0.7.1 multi-argument functions`** against `main`.
- Release candidate version: **0.7.1** in both `pyproject.toml` and `src/engcalc_colab/__init__.py`.
- Latest product corrective: `4a46bbf7c48373a5d40c03edf99cfa8343d48573` — `fix: ignore unused unresolved numeric parameters`.
- Approved design is persistent in the release tree:
  - `docs/superpowers/specs/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-design.md`;
  - `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md`.
- Definitive corrected validation SHA: `2332bd29e571a360cc47a29562e09b5828a3d2cb`.
- Temporary corrected distribution workflow removed by `8de00a35912a3a9f5c820cd3c4d035b4a2c2c08d`.
- The user explicitly approved merging PR #28. Merge may proceed after PR evidence/review threads and chain-of-custody checks are finalized.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume the user's Codex quota without explicit authorization.

## Approved behavior

- User functions accept one or more ordered positional parameters; the existing one-argument form remains compatible.
- Calls require exact positional arity. Defaults, keyword calls, variadics, keyword-only parameters and overload-by-arity are unsupported.
- Parameter substitution is simultaneous. Local parameters shadow same-named context values only inside their function body.
- `=` symbolic state and `:=` Pint-backed numeric state remain separate.
- Fully numeric multi-argument calls preserve Pint units, direct numeric expressions, nested user functions and dimensional zero in any argument position.
- Generalized partial evaluation substitutes every known value and preserves only dependencies that remain symbolic **after substitution**.
- An unresolved caller argument whose parameter is unused by the body does **not** make the result partial. `f(x, y) = x`; `numeric(f(2*m, y), cm)` returns a fully numeric `200 cm` result.
- Only caller-supplied symbolic arguments may remain intentionally unresolved. Missing global/body numeric dependencies remain strict errors.
- Target-unit conversion is rejected only when symbols actually remain unresolved in the resulting expression.
- Non-polynomial partials preserve truthful symbolic structure and do not fabricate a final quantity.
- Scalar-math behavior inherited from 0.7.0 remains unchanged.
- Plot/envelope behavior remains unchanged: 201-point sampling and structural positive moment downward. No Cartesian multi-parameter sweep was added.

## Open issues / user feedback

- Opening PR #28 triggered the repository-configured automatic Codex review. No manual `@codex review` or Codex Cloud review action was initiated by this workflow.
- Review finding 1 (mandatory `CURRENT.md` headings): corrected; the required stable headings are restored and are explicitly checked by the definitive gate.
- Review finding 2 (approved spec/plan absent from release tree): corrected; both files were persisted by `75e0d6454cb00fc080795bf7f23cefacc00cd552` and their presence is checked by the definitive gate.
- Review finding 3 (unused unresolved parameter incorrectly forcing a partial result): reproduced RED and fixed in `4a46bbf7c48373a5d40c03edf99cfa8343d48573`; the installed-wheel smoke now exercises the corrected case.
- No known functional blocker remains. Administrative closure still required: chain-of-custody comparison, PR body update, replies/resolution of the three review threads, mergeability check, then the already-approved merge.

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
- Spec/plan persistence: Actions `33259426881`; persistent docs commit `75e0d6454cb00fc080795bf7f23cefacc00cd552`.

### Definitive corrected 0.7.1 distribution gate

- GitHub Actions: `33259552699` — **success**.
- Validated SHA: `2332bd29e571a360cc47a29562e09b5828a3d2cb`.
- Persistent release-context/design checks: **passed**.
- Release metadata: **0.7.1 passed**.
- Focused corrected release contracts: **77/77 passed**.
- Complete source suite: **386/386 passed**.
- Real wheel built: `engcalc_colab-0.7.1-py3-none-any.whl`; wheel METADATA contains `Version: 0.7.1`.
- Wheel installed into a clean virtual environment.
- Outside-checkout smoke with `PYTHONPATH=''` imported from `/tmp/engcalc-v071-corrected-wheel-venv/lib/python3.13/site-packages/engcalc_colab/__init__.py`.
- Installed-wheel smoke passed fully numeric multi-argument evaluation, generalized partials, non-polynomial partials, nested composition/201-point plot, dimensional zero, exact arity, and `numeric(f_unused(2*m, y), cm) == 200 cm`.
- Complete source-free suite against installed wheel: **386/386 passed**.
- Repeated complete source suite: **386/386 passed**.
- Validated wheel artifact:
  - ID: `9716898144`;
  - name: `engcalc-colab-0.7.1-corrected-final-wheel`;
  - size: `29225` bytes;
  - digest: `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`;
  - expires: `2026-11-27`.
- Temporary corrected distribution workflow removed by `8de00a35912a3a9f5c820cd3c4d035b4a2c2c08d`.

## Roadmap / active plan

- Active milestone: **EngCalc 0.7.1 — multi-argument user functions and generalized partial numeric evaluation**.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-design.md`.
- Approved plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.1-multiarg-partial-eval-final.md`.
- Tasks 0–7 plus all three PR review correctives are implemented and distribution-validated.
- Current source suite: **386 tests**.
- Remaining steps are release administration only: chain of custody, PR evidence/review closure, merge, and post-merge context verification.

## Exact next step

1. Compare validated SHA `2332bd29...` to final feature head and require that post-validation git changes are limited to removal of the temporary distribution workflow and this context update.
2. Update PR #28 validation text with Actions `33259552699`, 77 focused tests, 386 source/wheel tests, artifact `9716898144` and the automatic-review clarification.
3. Reply to and resolve all three automatic-review threads with their RED/GREEN evidence.
4. Re-fetch PR #28 and require open, clean and mergeable state.
5. Merge PR #28 using merge commit semantics and an expected-head-SHA guard; user approval is already recorded.
6. Verify the merged `main` tree corresponds to the finalized PR tree, then update `CURRENT.md` on `main` to record EngCalc 0.7.1 as merged.

## How to resume in a new conversation

Read this file and the persisted 0.7.1 spec/plan. PR #28 is open and already has explicit user approval to merge. The repository-configured automatic review raised three findings; all three are corrected. The functional finding was reproduced by RED Actions `33259267930` and fixed in `4a46bbf7c48373a5d40c03edf99cfa8343d48573`; GREEN Actions `33259332512` passed 19 focused and 386 full tests. The definitive corrected distribution gate is Actions `33259552699` on SHA `2332bd29e571a360cc47a29562e09b5828a3d2cb`: 77 focused, 386 source, 386 installed-wheel source-free, 386 repeated source, corrected installed-wheel smoke passed, artifact `9716898144` digest `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`. The temporary gate is removed. Next: prove chain of custody, update/resolve PR review evidence, verify mergeability, merge PR #28 using existing approval, and verify/update `main`. Do not manually invoke Codex without explicit authorization.