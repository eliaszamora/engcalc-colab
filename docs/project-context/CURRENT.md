# EngCalc Current Project Context

_Last updated: 2026-08-28 after incorporating final Colab visual-QA feedback into EngCalc 0.6.1. PR #25 remains open and must not be merged without explicit user approval after the user reruns the updated release candidate in Colab._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` still contains EngCalc **0.6.0**.
- Release candidate branch: `feature/v0.6.1-visual-polish-2`.
- Open PR: **#25 — `release: EngCalc 0.6.1 visual polish`**, targeting `main`.
- Release candidate version: **0.6.1** in both `pyproject.toml` and `src/engcalc_colab/__init__.py`.
- PR is intentionally **not merged** pending final user visual approval in Colab.
- Latest compact-label product code commit: `c41a9682d5d8223de37fa65c03d6a1f9062df38c`.
- Final compact-label distribution gate was run from `c73f25bbf91b67d1d7f82565a1cc0d227da50e67`; commits after that gate only remove temporary workflows and update documentation.
- Temporary compact-label visual workflow removed in `c0a4f101fed9a9587527aaf8a76b0669450dc501`.
- Temporary compact-label release workflow removed in `36556234d4632f683304d648d76ff3251e289dbf`.

## 0.6.1 approved behavior

EngCalc 0.6.1 is presentation-focused. It does not change the engineering calculations, unit engine, 201-point sampling grid, signed-envelope rules, magnitude-envelope rules, or the structural sign convention.

- Symbolic definitions use `=`; Pint-backed numerical assignments use `:=`.
- Symbolic and numerical namespaces remain separate.
- Positive structural moment plots **downward**.
- Multi-series plotting remains `plot(expr1, expr2, ..., x, start, end)`.
- Signed `envelope(...)` remains algebraic max/min.
- `abs(...)` and magnitude envelopes remain available; mixed signed/absolute sources in one envelope are rejected.
- Multi-series plots and envelopes do not use characteristic-value summary panels.
- Characteristic points use compact coordinate labels in the form **`(x, y)`**, for example `(2.5, 3.15)`.
- Characteristic labels contain **no duplicated units**, because units already appear on the axes.
- Characteristic labels contain **no `x =`, `M =`, `V =` prefixes**, no boxes and no leader lines/arrows.
- Label text uses the corresponding series color to preserve series association.
- Placement treats axes boundaries, legend, previous labels and sampled curve points as collision constraints before ranking candidate positions.
- A label may be moved farther from a dense characteristic cluster when necessary to keep the graphic readable; no leader line is reintroduced.
- Long symbolic and numerical MathJax output is split into semantic stages/rows under the notebook width budget; short expressions remain compact.

## Compact characteristic labels — final TDD cycle

User visual QA rejected the earlier boxed callouts with leader lines and requested a simpler technical-plot notation: show only `(x, y)` near each characteristic point, without units or leader lines, while preventing overlaps with labels and plotted curves.

- RED test commit: `15cea62505249fc51d48f49af9c48f90baefd3fa`.
- RED focused result: **3 failed**, reproducing the old long text/box/leader behavior and curve/label collision cases.
- Production implementation: `cd05a0a00fc04be86712dca6e9781985fa3859b9`.
- Legacy plotting contracts updated in `0e6f0ab7a23dc5e7a9611a013eda9023f3ae0b98`, `ca83905327c380e54e21e305e12f644a50eb7ae0`, `dae54bb4c0fbecb928f9bbf486b2916345a0dea0`, `e877a00a9afff18856e87908ea375b8ce0b40ced` and `c41a9682d5d8223de37fa65c03d6a1f9062df38c`.

### Final compact-label visual gate

GitHub Actions run `33204609923` on `c41a9682d5d8223de37fa65c03d6a1f9062df38c`:

- focused compact-label suite: **3 passed**;
- complete source suite: **239 passed**;
- four-figure compact-label visual acceptance: **PASS**;
- automated checks covered label-to-label collision, label-to-curve collision, axes boundaries, legend clearance, coordinate-only text, absence of boxes and absence of leader lines;
- visual artifact: `engcalc-v061-compact-label-visuals`, artifact ID `9699168071`;
- visual artifact ZIP SHA256: `9f5caf08d2e5caa0f77225ddfeedf06e8d5ff7b0b1bcf120394d5802ca1b0b9d`.

Manual inspection of all four generated PNGs also passed. The stage-shear plot has a dense cluster near `x=0`; one label is deliberately displaced farther horizontally to avoid both other labels and the curves. This is accepted behavior and is preferable to overlap or a leader line.

### Final compact-label 0.6.1 distribution gate

GitHub Actions run `33205092470` on `c73f25bbf91b67d1d7f82565a1cc0d227da50e67`:

- branch diff check against `origin/main`: **PASS**;
- source version: **0.6.1 PASS**;
- source suite: **239 passed in 49.17 s**;
- 21-station numerical comparison with merged 0.6.0: **PASS**, worst absolute difference `0.000e+00`;
- exact wheel `engcalc_colab-0.6.1-py3-none-any.whl`: **built successfully**;
- clean-venv wheel installation: **PASS**;
- installed-wheel smoke from `/tmp` with empty `PYTHONPATH`: **PASS 0.6.1**;
- complete suite against installed wheel with repository `src` removed: **239 passed in 48.56 s**;
- repeated source suite: **239 passed in 48.44 s**;
- wheel artifact: `engcalc-colab-0.6.1-compact-label-wheel`, artifact ID `9699418713`;
- wheel artifact ZIP SHA256: `63e3a4f4daba4c61004e093360c7e3535544d490159bceba83324ca480f5766f`.

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

## Colab side-by-side browser extension

The vertical-scroll issue in the user's custom Colab side-by-side Chrome extension was investigated separately from EngCalc. Diagnostic evidence showed that the actual output lived in cross-origin `*-colab.googleusercontent.com/outputframe.html` iframes, including one frame fixed at 1000 px. Extension **v1.0.4** adds frame-height synchronization for those Colab output frames. The user subsequently reported that the vertical-output scrollbar problem appears solved.

This fix belongs to the browser extension, not EngCalc. Do not add Colab-specific output-height code to EngCalc unless a new independent problem demonstrates that it is required.

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

Do not infer that a later roadmap milestone has started merely because 0.6.1 is release-ready.

## Exact next step

1. In a fresh/restarted Colab runtime, reinstall `feature/v0.6.1-visual-polish-2` and verify `engcalc_colab.__version__ == "0.6.1"`.
2. Rerun the complete propped-cantilever exercise.
3. Visually QA the four final plot families with compact `(x, y)` labels: stage moments, stage shears, signed moment envelope and magnitude shear envelope.
4. Confirm specifically that labels have no boxes/leader lines/units and that no unacceptable overlap remains in the real Colab renderer.
5. Also confirm the long MathJax derivations still look correct.
6. Inspect PR #25 if desired; **do not merge yet**.
7. Merge PR #25 only after the user gives explicit approval of this updated Colab visual QA.

## How to resume in a new conversation

Tell the new agent:

> Continue EngCalc from `docs/project-context/CURRENT.md`. Read root `AGENTS.md`, verify GitHub state, inspect PR #25 and continue the exact updated Colab visual-QA step. Do not merge without explicit approval.

The repository context file and Git history are authoritative for project continuity.
