# EngCalc Current Project Context

_Last updated: 2026-08-29 after the final PR #25 inspection, resolution of two P2 review blockers, and a fresh full distribution gate. The user explicitly authorized closing EngCalc 0.6.1 and moving to the next roadmap milestone._

## Current release state

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` still contains EngCalc **0.6.0** until PR #25 is merged.
- Release branch: `feature/v0.6.1-visual-polish-2`.
- PR #25: **`release: EngCalc 0.6.1 visual polish`** targeting `main`.
- Candidate/package version: **0.6.1**.
- User authorization to close/merge 0.6.1: **given explicitly on 2026-08-29** after successful real-Colab spacing QA.
- Compact plot labels `(x, y)` are user-approved in real Colab.
- Semantic MathJax spacing is user-approved in real Colab.
- `result(...)` is included as the compact formula → result presentation command; `numeric(...)` remains formula → substitution → result.

## Final approved presentation behavior

### MathJax spacing

- **4 pt**: continuation row of the same mathematical stage caused by width wrapping.
- **8 pt**: new mathematical stage inside one operation (`solve`, `numeric`, `result`).
- **8 pt**: consecutive source results with no blank source line.
- **16 pt**: next source result after an explicit blank source line.

### Plotting

- Positive structural moment is plotted downward.
- Multi-series `plot(...)`, signed `envelope(...)`, `abs(...)` and magnitude envelopes remain supported.
- Characteristic labels are compact `(x, y)` text with no boxes, duplicated units or leader lines.
- Label placement avoids axes, legend, prior labels and sampled curves.

## Final PR inspection blockers and fixes

The final inspection of PR #25 found two unresolved P2 review threads. Merge was deliberately stopped until both were reproduced, fixed with TDD and distribution-validated.

### P2 — overwide single multiplicative term

Problem: `_bounded_expression_rows()` could return a product/fraction wider than the MathJax visual budget when additive packing and `expand()` could not improve it.

- RED coverage added for one long product and one long fraction.
- RED focused run `33226282597`: the two wrapping regressions failed as expected, along with the coincident-envelope regression.
- Production renderer fix: `9d145958753bdfdb8d9ab94dd2a49807b73924d0`.
- Overwide multiplicative terms now split only at safe factor boundaries; continuation rows retain the 4 pt wrapping hierarchy.

### P2 — coincident signed-envelope extrema

Problem: when signed upper and lower envelopes had the same global point/value, the renderer emitted duplicate extrema markers/annotations.

- RED constant-envelope regression added.
- Production plotting fix: `7b6686d06a907a1fa5b78043b3cb7d557c96d9ca`.
- Coincident global extrema now render one characteristic marker/annotation rather than two duplicates.

Both review threads were replied to with test evidence and resolved after the final gate.

## Final 0.6.1 distribution gate

Temporary workflow: `.github/workflows/v061-final-review-blockers.yml`.

- Focused GREEN before full gate: run `33226413469` — **18 passed**.
- Final full distribution gate: run **`33226471869`** on repository head **`b512e89204ad2726bea3aaefe5320a315a4d5313`**.
- Focused final-review suite: **18 passed in 9.50 s**.
- Complete source suite: **252 passed in 63.44 s**.
- Wheel `engcalc_colab-0.6.1-py3-none-any.whl`: **built successfully**.
- Clean-venv installation: **PASS**.
- Installed-wheel smoke from `/tmp` with empty `PYTHONPATH`: **PASS**. It explicitly checked:
  - long product splitting;
  - long fraction splitting;
  - coincident signed-envelope annotation deduplication;
  - 8 pt consecutive-result spacing;
  - 16 pt explicit-blank spacing.
- Complete suite against installed wheel with repository source removed: **252 passed in 61.90 s**.
- Repeated source suite: **252 passed in 60.93 s**.
- Temporary final-review workflow removed in `4100cef48e74d285653ce70e215114d528b300fd`.

No production source or test changes were made after the validated gate; only validation-workflow cleanup and release-context documentation follow it.

## Earlier retained 0.6.1 evidence

- Compact-label visual gate `33204609923`: visual acceptance PASS; subsequent real-Colab appearance approved by user.
- 21-station comparison against merged 0.6.0 in `33205092470`: worst absolute numerical difference `0.000e+00`.
- `result(...)` distribution gate `33210052766`: source/wheel/repeated-source suites all passed.
- Semantic 4/8/16 distribution gate `33220438965`: source/wheel/repeated-source suites all passed before the two final review blockers were discovered and then independently closed by the newer gate above.

## Installation

After PR #25 is merged, canonical Colab installation returns to the normal dependency-resolving command from `main`:

```python
%pip install -q --upgrade --no-cache-dir git+https://github.com/eliaszamora/engcalc-colab.git
%load_ext engcalc_colab
```

The prior Pint + exact-commit two-step command was specifically for pre-merge QA while multiple candidate revisions shared package version `0.6.1`.

## Merge gate

The user has explicitly authorized closing 0.6.1. Before merging PR #25, verify all of the following against GitHub:

1. PR is open, non-draft and mergeable.
2. No unresolved review threads remain.
3. The temporary final-review workflow is absent from changed files.
4. Since validated head `b512e89204ad2726bea3aaefe5320a315a4d5313`, only workflow cleanup and documentation changed; no `src/` or test files changed.
5. Merge using the exact current PR head SHA as a guard.

After merge, verify `main` contains version 0.6.1 and update this file on `main` with the merge SHA and next roadmap milestone.

## Roadmap

The evolution roadmap remains on branch `planning/engcalc-evolution-roadmap`:

- `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`
- `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`

After 0.6.1 is merged, read those files and use them—not an inferred version number—to select the next milestone.
