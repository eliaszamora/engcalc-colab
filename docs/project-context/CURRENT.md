# EngCalc Current Project Context

_Last updated: 2026-08-29 after PR #25 merged EngCalc 0.6.1 into `main` and the evolution roadmap was reviewed against the actual merged capability set._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` now contains EngCalc **0.6.1**.
- PR #25 — `release: EngCalc 0.6.1 visual polish` — merged successfully on 2026-08-29.
- Merge commit: `0db200a2fe691ec8fc54eb2bd0374cc9289eff2b`.
- `pyproject.toml` and `src/engcalc_colab/__init__.py` both report version **0.6.1**.
- Canonical Colab installation is again the normal dependency-resolving install from `main`:

```python
%pip install -q --upgrade --no-cache-dir git+https://github.com/eliaszamora/engcalc-colab.git
%load_ext engcalc_colab
```

## 0.6.1 closed behavior

### MathJax presentation

- **4 pt**: continuation row of one mathematical stage after width wrapping.
- **8 pt**: new mathematical stage inside `solve`, `numeric` or `result`.
- **8 pt**: consecutive source results without a blank source line.
- **16 pt**: next source result after an explicit blank source line.
- `numeric(...)` remains formula → substitution → result.
- `result(...)` is formula → result.

### Plotting and envelopes

- Structural positive moment plots downward.
- Multi-series `plot(...)`, signed `envelope(...)`, `abs(...)` and magnitude envelopes remain supported.
- Characteristic annotations are compact `(x, y)` labels with no boxes, duplicated units or leader lines.
- Coincident signed-envelope extrema render one characteristic marker/annotation rather than duplicates.

## Final 0.6.1 verification evidence

The final PR inspection found and closed two P2 review blockers before merge:

1. overwide single products/fractions could escape the MathJax visual-width budget;
2. coincident signed-envelope upper/lower extrema could create duplicate annotations.

Both were reproduced with RED tests, fixed, and revalidated.

Final distribution gate: GitHub Actions run **`33226471869`** on validated head `b512e89204ad2726bea3aaefe5320a315a4d5313`:

- focused final-review regressions: **18 passed in 9.50 s**;
- complete source suite: **252 passed in 63.44 s**;
- wheel `engcalc_colab-0.6.1-py3-none-any.whl`: built successfully;
- clean-venv installation: PASS;
- installed-wheel smoke from `/tmp` with empty `PYTHONPATH`: PASS;
- installed-wheel complete suite: **252 passed in 61.90 s**;
- repeated source suite: **252 passed in 60.93 s**.

After that gate, only the temporary validation workflow was removed and release-context documentation changed before the exact-head merge. No product or test file changed after the validated gate.

Earlier retained evidence includes the compact-label visual approval in real Colab and the 21-station comparison against 0.6.0 with worst absolute numerical difference `0.000e+00`.

## Roadmap reconciliation after 0.6.1

The master evolution roadmap predates the final scope of 0.6.1. It originally assigned version `0.6.1` to **symbolic/numeric ergonomics and diagnostic quality**, while the version that actually shipped as 0.6.1 became the visual/presentation release plus `result(...)` and final renderer corrections.

A capability review of merged `main` shows the original roadmap block is **not fully implemented**:

- the `numeric(...)` user-function path still resolves a call argument through the symbolic visitor before numerical evaluation, so the dedicated bridge intended for direct unit-bearing arguments such as `numeric(M(2.5*m))`, `numeric(V(L/2))` and `numeric(R(4*tonf/m))` is still pending;
- `errors.py` still contains only the base exception hierarchy and does not yet provide the roadmap's centralized corrective diagnostic hints.

Therefore the roadmap's original numeric-ergonomics release is renumbered to **EngCalc 0.6.2** without expanding its functional scope. Version **0.7.0 — scalar engineering mathematics** remains the milestone after 0.6.2.

## Next milestone — EngCalc 0.6.2 numeric ergonomics and diagnostics

Planned branch: `feature/v0.6.2-numeric-ergonomics`, created from the merged-and-documented `main` baseline.

Required behavior carried forward from the roadmap:

- `numeric(M(2.5*m))` works directly;
- `numeric(V(L/2))` works when `L` has a numeric value;
- `numeric(R(4*tonf/m))` works directly;
- intentionally unresolved `numeric(M(x))` remains a valid partial evaluation;
- `solve(expression, unknown)` remains the normal `expression = 0` shorthand and explicit `eq(...)` remains supported;
- diagnostics distinguish unknown numeric names, incompatible units, unresolved symbols and unsupported symbolic/numeric crossings, with corrective hints when EngCalc can safely provide one.

The roadmap documents the intended internal bridge as a restricted numeric function-argument resolver: a lone unassigned name may remain symbolic, while a complete expression containing numeric values/units is evaluated by `NumericContext`.

## Roadmap after 0.6.2

- **0.7.0** — scalar engineering mathematics: `sqrt`, trig/inverse trig, `exp`, `log`, `pi` with unit-aware rules.
- **0.7.1** — multi-argument user functions and generalized partial evaluation.
- **0.7.2** — engineering tables/evaluation by points.
- **0.7.3** — derivation traces.
- Later 0.8.x/0.9/0.10/1.0 milestones remain as defined in the master roadmap.

Master roadmap files remain on branch `planning/engcalc-evolution-roadmap`:

- `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`
- `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`

## Exact next step

1. Amend the roadmap documents so the original numeric-ergonomics Task 1 is versioned **0.6.2**, with 0.7.0 and later versions unchanged.
2. Create `feature/v0.6.2-numeric-ergonomics` from current `main`.
3. Start TDD with RED tests for direct unit-bearing user-function arguments and diagnostic quality.
4. Do not modify production code until those RED tests fail for the expected current behavior.
5. Close 0.6.2 with the standard source + real wheel + clean install + installed-wheel full-suite gate before merge.
