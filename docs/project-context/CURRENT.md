# EngCalc Current Project Context

_Last updated: 2026-08-28 during EngCalc 0.6.0 release-candidate validation._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` is still EngCalc **0.5.0**.
- Release-candidate branch: `feature/v0.6.0-abs-envelope-panel`.
- Open PR: **#24**, `release: EngCalc 0.6.0 magnitude envelopes and in-plot panels`.
- 0.6.0 was previously release-gated at 226 tests, but a newly reported symbolic MathJax wrapping regression is being corrected before merge. Do not reuse the old release-gate claim as final evidence after product code changes; rerun the gate.
- Temporary validation workflow currently used for the wrapping correction: `.github/workflows/v060-symbolic-wrap-validation.yml`. Remove before release closure.

## Approved behavior

### Existing language / numeric model

- Symbolic definitions use `=`; numeric Pint-backed assignments use `:=`.
- Symbolic and numeric namespaces remain deliberately separate.
- `solve(expr, x)` may solve the implicit equation `expr = 0`; `eq(left, right)` remains available for explicit equalities.
- Positive structural moment is plotted downward.

### Plotting and envelopes

- Multi-series plotting: `plot(expr1, expr2, ..., x, start, end)`.
- One-parameter sweep remains supported for `plot`/`envelope`.
- Signed envelope: `envelope(M1(x), M2(x), x, 0, L)` returns algebraic max/min.
- 0.6.0 adds safe `abs(...)` and magnitude envelopes such as `envelope(abs(V1(x)), abs(V2(x)), x, 0, L)`.
- Magnitude envelopes show one nonnegative governing magnitude curve while preserving signed source responses and the signed governing value internally.
- Mixed absolute/signed sources in one envelope are rejected.
- In 0.6.0 characteristic-value panels belong **inside the axes** and choose a low-occupancy corner while avoiding the legend corner. No right-side figure margin should be reserved for those panels.

## Open issues / user feedback

### 1. User Colab is currently running 0.5.0, not 0.6.0

The normal bootstrap installs the default branch:

```python
%pip install -q --upgrade git+https://github.com/eliaszamora/engcalc-colab.git
```

Because `main` is still 0.5.0, this explains both observed symptoms:

- `engcalc: ... unsupported function 'abs'`;
- characteristic-value panels still appearing outside the plot.

Do not diagnose these as failures of the validated 0.6.0 branch unless reproduced after installing the feature branch or after merging 0.6.0.

### 2. Symbolic long-expression wrapping gap

User screenshot shows long symbolic outputs for the propped-cantilever derivation overflowing horizontally. Root cause: adaptive additive MathJax wrapping currently applies to `NumericEvaluationResult` and `PartialNumericEvaluationResult`, but ordinary symbolic `EvaluationResult` goes through `_standard_result_row()` as one row.

Required correction before 0.6.0 merge:

- extend adaptive row splitting to long symbolic assignments/functions;
- break long multi-stage `display_input -> evaluated value` chains across rows when necessary;
- preserve alignment and existing short-expression output.

### 3. Excel chart comparison was initially framed incorrectly

The professor workbook contains different chart families:

- moment stage chart uses **unfactored components**: construction dead (`Mpp construction`), use dead (`Mpp use`), use live (`Msc use`);
- shear stage chart analogously uses `Vpp construction`, `Vpp use`, `Vsc use`;
- design moment envelope uses `Mu max` / `Mu min`;
- design shear envelope is based on `|Vu| max`.

The previous EngCalc demonstration `plot(M_UC(x), M_UU(x), ...)` and `plot(V_UC(x), V_UU(x), ...)` compared **factored ultimate combinations**, so those plots were not intended to reproduce the Excel's stage-component charts even though the envelope values matched the Excel numerically.

For a like-for-like validation, generate stage plots from construction dead + use dead + use live separately, then generate design envelopes from ultimate combinations.

## Validation evidence

### 0.6.0 before current wrapping correction

Prior validated feature branch evidence:

- source suite: 226 passed;
- wheel: `engcalc_colab-0.6.0-py3-none-any.whl` built;
- clean installed-wheel smoke from `/tmp`: PASS;
- full suite against installed wheel: 226 passed with only a cache-permission warning;
- repeated source suite: 226 passed.

This evidence predates the new symbolic-wrapping product correction and must be rerun after that correction.

### Professor Excel numerical validation

A from-scratch EngCalc solution derived the propped-cantilever reactions through equilibrium/compatibility and matched all 21 Excel stations for:

- `Mu max`;
- `Mu min`;
- `|Vu| max`;

at numerical tolerance `1e-9`.

The reference source used only problem data for solving; the Excel envelope columns were used only as final validation data.

## Roadmap / active plan

Master roadmap is persisted separately on branch `planning/engcalc-evolution-roadmap`:

- design: `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`;
- implementation plan: `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`.

Planned progression after closing 0.6.0:

`0.6.1 numeric ergonomics -> 0.7.0 scalar math -> 0.7.1 multi-arg/general partial -> 0.7.2 tables -> 0.7.3 derivation traces -> 0.8.0 piecewise -> 0.8.1 exact characteristics -> 0.8.2 exact envelopes -> 0.8.3 named cases -> 0.9.0 matrices -> 0.10.0 checks -> 0.10.1 summaries -> 1.0 stabilization`.

## Exact next step

1. Establish green baseline with the temporary wrapping workflow on `feature/v0.6.0-abs-envelope-panel`.
2. Add failing tests reproducing long symbolic wrapping for the propped-cantilever expressions (`delta_B`, `R_B(q)` or equivalent).
3. Implement minimal symbolic adaptive wrapping in `renderer.py`.
4. Run focused tests + full source suite.
5. Reproduce the structural example and visually/structurally verify the generated MathJax rows.
6. Rerun the complete 0.6.0 release gate, remove temporary workflow, update this file with final SHAs/counts.
7. Only then merge PR #24 when explicitly authorized.

## How to resume in a new conversation

Tell the new agent:

> Continue EngCalc from `docs/project-context/CURRENT.md`. Read root `AGENTS.md`, verify GitHub state, then continue the exact next step. Do not assume `main` contains 0.6.0 until PR #24 is actually merged.

The repository context file and its Git history are authoritative for project continuity; do not ask the user to reconstruct earlier technical decisions unless repository evidence is genuinely incomplete.
