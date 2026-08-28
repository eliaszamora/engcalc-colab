# EngCalc Current Project Context

_Last updated: 2026-08-28 after completing the EngCalc 0.6.1 visual-polish release gate on `feature/v0.6.1-visual-polish-2`; PR to `main` is the next step and must not be merged without explicit user approval after Colab visual QA._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` still contains EngCalc **0.6.0**. `main`'s `pyproject.toml` reports `version = "0.6.0"`.
- Release candidate branch: `feature/v0.6.1-visual-polish-2`.
- Release candidate version: **0.6.1** in both `pyproject.toml` and `src/engcalc_colab/__init__.py`.
- Final product/release-gate head: `18a51c78edf231639a42a39fa92716179e862af8`.
- Final callout geometry correction: `da4524469108af25c9de7828abe99e50b74251b9`.
- Version bump: `ceb03223383f23db24d878f82a8e128bf283f24d`.
- README 0.6.1 documentation: `ea536cf2126cd437f0b8e17d384e6860b2d88639`.
- Legacy version assertions aligned to 0.6.1: `d1438bbb6083be4acb95879cd34b817480c18b5e`.
- Temporary release workflow removed in `9ff5d7a2ef5200e3709fd24ac885c53a6a580c4e`.
- Temporary visual-validation workflow removed in `6ecae51f8459aa17ba69442083d6536c3d7f5b8a`.

## 0.6.1 approved behavior

EngCalc 0.6.1 is presentation-focused. It does not change the engineering calculations, unit engine, 201-point sampling grid, signed-envelope rules, magnitude-envelope rules, or the structural sign convention.

- Symbolic definitions use `=`; Pint-backed numerical assignments use `:=`.
- Symbolic and numerical namespaces remain separate.
- Positive structural moment plots **downward**.
- Multi-series plotting remains `plot(expr1, expr2, ..., x, start, end)`.
- Signed `envelope(...)` remains algebraic max/min.
- `abs(...)` and magnitude envelopes remain available; mixed signed/absolute sources in one envelope are rejected.
- Multi-series plots and envelopes no longer use characteristic-value summary panels.
- Characteristic values are attached to their exact sampled data points with `x` and response ordinate shown in the callout.
- Callout placement is collision-aware and treats the axes boundary, legend and prior callouts as hard constraints before ranking valid candidates.
- Matplotlib annotation geometry is explicitly refreshed before scoring so the bounding box used for collision selection matches final rendering.
- Long symbolic and numerical MathJax output is split into semantic stages/rows under the notebook width budget; short expressions remain compact.

## Professor Excel comparison

Use like-for-like chart families:

- stage moment chart: unfactored `M_C`, `M_D`, `M_L`;
- stage shear chart: unfactored `V_C`, `V_D`, `V_L`;
- design moment envelope: `M_UC` versus `M_UU`;
- design shear envelope: maximum magnitude of `V_UC` versus `V_UU`.

Compact commands:

```text
plot(M_C(x), M_D(x), M_L(x), x, 0, L)
plot(V_C(x), V_D(x), V_L(x), x, 0, L)
envelope(M_UC(x), M_UU(x), x, 0, L)
envelope(abs(V_UC(x)), abs(V_UU(x)), x, 0, L)
```

Do not unnecessarily split short function calls across multiple source lines.

## 0.6.1 validation evidence

### Version TDD

- RED commit: `7ee08e9e20d6f35a3d6c981c6283252afd292232`.
- Expected RED result: **2 failed, 234 passed** because package and `pyproject.toml` were still 0.6.0.
- After the version bump, three older tests still hard-coded 0.6.0; this produced **3 failed, 233 passed** and was corrected in `d1438bbb6083be4acb95879cd34b817480c18b5e`.

### Final visual and numerical gate

GitHub Actions run `33199663483` on `18a51c78edf231639a42a39fa92716179e862af8`:

- focused MathJax renderer suite: **11 passed in 1.96 s**;
- complete source suite: **236 passed in 38.54 s**;
- visual acceptance: **PASS** for four figures with point annotations and axes-safe callouts;
- moment diagrams preserved positive-down convention;
- 21-station numerical comparison with merged 0.6.0: **PASS**, worst absolute difference `0.000e+00`;
- visual artifact: `engcalc-v061-visual-acceptance`, artifact ID `9697252147`;
- visual artifact ZIP SHA256: `66aa85babc89ef1741f596f5c4b37ea7baedf6ae9d5694b3fd7add0bedd9792b`.

### Final 0.6.1 release gate

GitHub Actions run `33199663520` on `18a51c78edf231639a42a39fa92716179e862af8`:

- source version: **0.6.1 PASS**;
- source suite: **236 passed in 48.79 s**;
- wheel `engcalc_colab-0.6.1-py3-none-any.whl`: **built successfully**, approximately 26 KiB;
- installation into a fresh venv: **PASS**;
- installed-wheel smoke from `/tmp` with empty `PYTHONPATH`: **PASS 0.6.1**;
- complete suite against installed wheel with repository `src` removed: **236 passed in 47.85 s**;
- repeated source suite: **236 passed in 47.52 s**;
- wheel artifact: `engcalc-colab-0.6.1-wheel`, artifact ID `9697303713`;
- wheel artifact ZIP SHA256: `e62b7240aed0b22a2a6358bd6333b97cbe5e34a4897a0ac94a8a723257812a8d`.

## Colab output-pane scrollbar finding

The independent vertical scrollbar visible in Colab's right-side output pane is a **Google Colab host behavior**, not a scrollbar created by EngCalc or Matplotlib. EngCalc's `magic.py` emits `Math`, HTML headings and Matplotlib figures through IPython `display(...)`; it does not configure a Colab output-height container or call `google.colab.output`.

Google Colab has a host API `google.colab.output.no_vertical_scroll()` for disabling the per-cell vertical output scrollbar. Because an `%%eng` cell owns the whole cell body, a clean automatic solution would require a guarded Colab-specific integration inside the EngCalc cell magic. This is **not part of the frozen 0.6.1 release candidate** and should be treated as a separate follow-up unless the user explicitly decides to reopen 0.6.1 scope.

## Installation before merge

Until 0.6.1 is merged, test the release candidate in a fresh/restarted Colab runtime with:

```python
%pip install -q --upgrade --no-cache-dir git+https://github.com/eliaszamora/engcalc-colab.git@feature/v0.6.1-visual-polish-2
%load_ext engcalc_colab
```

Verification target:

```python
import engcalc_colab
print(engcalc_colab.__version__)  # 0.6.1
```

After an approved merge, normal installation from `main` becomes the canonical command.

## Roadmap

Master roadmap remains on branch `planning/engcalc-evolution-roadmap`:

- `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`;
- `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`.

Do not infer that a later roadmap milestone has started merely because 0.6.1 visual polish is release-ready.

## Exact next step

1. Review the final branch diff against `main` after temporary workflow cleanup.
2. Open PR `feature/v0.6.1-visual-polish-2` -> `main` with the exact validation evidence above.
3. Do **not** merge the PR yet.
4. In a fresh/restarted Colab runtime, install the feature branch and rerun the complete propped-cantilever exercise.
5. Visually QA the long MathJax derivations, multi-series stage plots, signed/magnitude envelopes, point callouts and positive-down moment convention.
6. Merge only after the user gives explicit approval.
7. Treat automatic removal of Colab's per-cell output scrollbar as a separate host-integration follow-up unless the user explicitly asks to include it before merge.

## How to resume in a new conversation

Tell the new agent:

> Continue EngCalc from `docs/project-context/CURRENT.md`. Read root `AGENTS.md`, verify GitHub state, inspect the open 0.6.1 PR and continue the exact next step. Do not merge without explicit approval.

The repository context file and Git history are authoritative for project continuity.
