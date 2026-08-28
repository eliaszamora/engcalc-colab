# EngCalc Current Project Context

_Last updated: 2026-08-28 after the EngCalc 0.6.0 symbolic-wrapping correction and final release gate._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` is still EngCalc **0.5.0**.
- Release-candidate branch: `feature/v0.6.0-abs-envelope-panel`.
- Open PR: **#24**, `release: EngCalc 0.6.0 magnitude envelopes and in-plot panels`.
- Runtime product correction for long symbolic MathJax output is commit `138e35cafa7d4427ac9831bbf57f894dd8fb3080`.
- Final 0.6.0 release gate passed on commit `17da5c949885bf6c875c1c76a3e6a7c5644d8102`; commits after that gate only remove the temporary workflow and update project-context documentation.
- Temporary validation workflow has been removed in cleanup commit `9872bf1dc6dbd253b073419bac8082edb960e3e9`.

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
- Characteristic-value panels belong **inside the axes** and choose a low-occupancy corner while avoiding the legend corner. No right-side figure margin is reserved.

### MathJax wrapping

- Existing adaptive wrapping for numeric/partial results remains.
- Long ordinary symbolic `EvaluationResult` expressions now use adaptive rows too.
- Long direct expressions split on additive terms where possible.
- Long staged operations such as `integral(...) -> evaluated result` separate the operation and result when they do not fit.
- Long solve equalities can split their additive equation across rows and place the solved assignment on its own row.
- Short symbolic expressions remain one row.

## Open issues / user feedback

### 1. User Colab currently installs 0.5.0 from `main`

The normal bootstrap:

```python
%pip install -q --upgrade git+https://github.com/eliaszamora/engcalc-colab.git
```

still installs 0.5.0 until PR #24 is merged. This explains the user's screenshots showing:

- `unsupported function 'abs'`;
- characteristic-value panels outside the plot.

For pre-merge visual QA use:

```python
%pip install -q --upgrade "git+https://github.com/eliaszamora/engcalc-colab.git@feature/v0.6.0-abs-envelope-panel"
```

Restart the Colab runtime after changing installed EngCalc code, then `%load_ext engcalc_colab` and verify `engcalc_colab.__version__ == "0.6.0"`.

### 2. User visual QA still required for symbolic wrapping

Automated tests prove row splitting structurally, but the user should rerun the propped-cantilever example in Colab from the feature branch and confirm the long `delta_B` / `R_B(q)` output is visually satisfactory at their notebook width.

### 3. Excel chart comparison must be like-for-like

The professor workbook contains different chart families:

- stage moment chart: unfactored construction dead `M_C`, use dead `M_D`, use live `M_L`;
- stage shear chart: unfactored construction dead `V_C`, use dead `V_D`, use live `V_L`;
- design moment envelope: ultimate `M_UC` versus `M_UU` -> algebraic max/min;
- design shear envelope: ultimate `V_UC` versus `V_UU` -> maximum absolute magnitude.

The earlier EngCalc plots `plot(M_UC, M_UU)` / `plot(V_UC, V_UU)` were ultimate-combination comparison plots, not replicas of the Excel stage-component charts. For like-for-like stage plotting use:

```text
plot(M_C(x), M_D(x), M_L(x), x, 0, L)
plot(V_C(x), V_D(x), V_L(x), x, 0, L)
```

and for design envelopes use:

```text
envelope(M_UC(x), M_UU(x), x, 0, L)
envelope(abs(V_UC(x)), abs(V_UU(x)), x, 0, L)
```

## Validation evidence

### Symbolic-wrapping TDD

RED: new wrapping tests produced **2 failed, 227 passed** because long ordinary symbolic results remained one row.

GREEN after commit `138e35c...`:

- focused wrapping suite: **7 passed**;
- full source suite: **229 passed**.

### Final 0.6.0 release gate

GitHub Actions run `33191115724`, gate commit `17da5c949885bf6c875c1c76a3e6a7c5644d8102`:

- source version: `0.6.0` PASS;
- source full suite: **229 passed in 38.44 s**;
- wheel built: `engcalc_colab-0.6.0-py3-none-any.whl`;
- clean venv install: PASS;
- installed-wheel smoke from `/tmp`: PASS, including magnitude envelope, in-axes panel and symbolic wrapping;
- full suite against installed wheel: **229 passed in 37.94 s**;
- repeated source suite: **229 passed in 38.50 s**;
- temporary validation workflow cleanup: PASS.

Only a nonfunctional Matplotlib font fallback message appeared during smoke (`semibold` -> weight 700).

### Professor Excel numerical validation

A from-scratch EngCalc solution derived the propped-cantilever reactions through equilibrium/compatibility and matched all 21 Excel stations for `Mu max`, `Mu min`, and `|Vu| max` at numerical tolerance `1e-9`. The Excel envelope columns were used only for final validation, not to construct the solution.

## Roadmap / active plan

Master roadmap is persisted separately on branch `planning/engcalc-evolution-roadmap`:

- design: `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`;
- implementation plan: `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`.

Planned progression after closing 0.6.0:

`0.6.1 numeric ergonomics -> 0.7.0 scalar math -> 0.7.1 multi-arg/general partial -> 0.7.2 tables -> 0.7.3 derivation traces -> 0.8.0 piecewise -> 0.8.1 exact characteristics -> 0.8.2 exact envelopes -> 0.8.3 named cases -> 0.9.0 matrices -> 0.10.0 checks -> 0.10.1 summaries -> 1.0 stabilization`.

## Exact next step

1. User installs the feature branch in a restarted Colab runtime and confirms version 0.6.0.
2. User reruns the structural example to visually QA: in-axes characteristic panels, `abs` magnitude envelope and long symbolic wrapping.
3. Use the corrected like-for-like stage plots (`M_C/M_D/M_L`, `V_C/V_D/V_L`) when comparing with the professor Excel.
4. If visual QA passes, update PR #24 evidence/body as needed and merge 0.6.0 to `main` when authorized.
5. Then begin roadmap Task 1 / EngCalc 0.6.1 from merged `main`.

## How to resume in a new conversation

Tell the new agent:

> Continue EngCalc from `docs/project-context/CURRENT.md`. Read root `AGENTS.md`, verify GitHub state, then continue the exact next step. Do not assume `main` contains 0.6.0 until PR #24 is actually merged.

The repository context file and its Git history are authoritative for project continuity; do not ask the user to reconstruct earlier technical decisions unless repository evidence is genuinely incomplete.
