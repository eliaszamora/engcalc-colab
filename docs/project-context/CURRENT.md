# EngCalc Current Project Context

_Last updated: 2026-08-28 after merging EngCalc 0.6.0 to `main`._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` now contains EngCalc **0.6.0**.
- PR **#24**, `release: EngCalc 0.6.0 magnitude envelopes and in-plot panels`, was squash-merged to `main`.
- Merge commit: `8b13ede8a6993de734c2b49de429125265210e56`.
- Runtime product correction for long symbolic MathJax output: `138e35cafa7d4427ac9831bbf57f894dd8fb3080` on the former feature history.
- Final release gate passed on `17da5c949885bf6c875c1c76a3e6a7c5644d8102`; later feature-branch changes only removed the temporary workflow and updated documentation.

## Approved behavior

- Symbolic definitions use `=`; numeric Pint-backed assignments use `:=`.
- Symbolic and numeric namespaces remain separate.
- Positive structural moment plots downward.
- Multi-series plotting: `plot(expr1, expr2, ..., x, start, end)`.
- Signed envelope: `envelope(M1(x), M2(x), x, 0, L)` gives algebraic max/min.
- Safe `abs(...)` and magnitude envelopes are available, e.g. `envelope(abs(V1(x)), abs(V2(x)), x, 0, L)`.
- Magnitude envelopes keep signed source responses and the signed governing value internally.
- Mixed signed/absolute sources in one envelope are rejected.
- Characteristic-value panels render **inside the axes** with low-occupancy corner placement and no reserved right margin.
- Long symbolic `EvaluationResult` expressions now use adaptive MathJax wrapping; short expressions remain one row.

## Installation

Normal Colab installation from `main` is now correct:

```python
%pip install -q --upgrade git+https://github.com/eliaszamora/engcalc-colab.git
%load_ext engcalc_colab
```

After upgrading EngCalc in an already-running runtime, restart the runtime or reload the extension as appropriate. Verification target: `engcalc_colab.__version__ == "0.6.0"`.

## Professor Excel comparison

Use like-for-like chart families:

- stage moment chart: unfactored `M_C`, `M_D`, `M_L`;
- stage shear chart: unfactored `V_C`, `V_D`, `V_L`;
- design moment envelope: `M_UC` versus `M_UU`;
- design shear envelope: maximum magnitude of `V_UC` versus `V_UU`.

Compact commands preferred by the user:

```text
plot(M_C(x), M_D(x), M_L(x), x, 0, L)
plot(V_C(x), V_D(x), V_L(x), x, 0, L)
envelope(M_UC(x), M_UU(x), x, 0, L)
envelope(abs(V_UC(x)), abs(V_UU(x)), x, 0, L)
```

Do not unnecessarily split short function calls across multiple source lines.

## Validation evidence

### Symbolic-wrapping TDD

- RED: **2 failed, 227 passed**.
- GREEN focused suite: **7 passed**.
- GREEN full source suite: **229 passed**.

### Final 0.6.0 release gate

GitHub Actions run `33191115724` on `17da5c949885bf6c875c1c76a3e6a7c5644d8102`:

- source version 0.6.0: PASS;
- source suite: **229 passed in 38.44 s**;
- wheel `engcalc_colab-0.6.0-py3-none-any.whl`: built;
- clean venv install: PASS;
- installed-wheel smoke from `/tmp`: PASS;
- full suite against installed wheel: **229 passed in 37.94 s**;
- repeated source suite: **229 passed in 38.50 s**.

### Professor Excel numerical validation

A from-scratch EngCalc solution for the 4 m propped cantilever matched all 21 Excel stations for `Mu max`, `Mu min`, and `|Vu| max` at tolerance `1e-9`. Inputs were `qC=2 tonf/m`, `qD=4 tonf/m`, `qL=3 tonf/m`; Excel envelope ordinates were used only for final validation.

## Roadmap

Master roadmap remains on branch `planning/engcalc-evolution-roadmap`:

- `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`;
- `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`.

Progression: `0.6.1 numeric ergonomics -> 0.7.0 scalar math -> 0.7.1 multi-arg/general partial -> 0.7.2 tables -> 0.7.3 derivation traces -> 0.8.0 piecewise -> 0.8.1 exact characteristics -> 0.8.2 exact envelopes -> 0.8.3 named cases -> 0.9.0 matrices -> 0.10.0 checks -> 0.10.1 summaries -> 1.0 stabilization`.

## Exact next step

1. Install normal `main` in a fresh/restarted Colab runtime and verify EngCalc 0.6.0.
2. Rerun the complete propped-cantilever exercise.
3. Visually QA: `abs(...)`, magnitude envelope, in-axes characteristic panels, symbolic wrapping, and like-for-like Excel stage plots.
4. If QA passes, begin EngCalc 0.6.1 from merged `main`.

## How to resume in a new conversation

Tell the new agent:

> Continue EngCalc from `docs/project-context/CURRENT.md`. Read root `AGENTS.md`, verify GitHub state, then continue the exact next step.

The repository context file and Git history are authoritative for project continuity.