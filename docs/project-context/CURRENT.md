# EngCalc Current Project Context

_Last updated: 2026-08-28 after adding the user-approved compact `result(...)` command to the EngCalc 0.6.1 release candidate and completing its clean-wheel validation. PR #25 remains open and must not be merged without explicit user approval after the user reruns the updated candidate in Colab._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` still contains EngCalc **0.6.0**.
- Release candidate branch: `feature/v0.6.1-visual-polish-2`.
- Open PR: **#25 — `release: EngCalc 0.6.1 visual polish`**, targeting `main`.
- Release candidate version: **0.6.1** in both `pyproject.toml` and `src/engcalc_colab/__init__.py`.
- PR is intentionally **not merged** pending final user visual approval in Colab.
- Latest compact-label product code commit: `c41a9682d5d8223de37fa65c03d6a1f9062df38c`.
- `result(...)` parser implementation: `0ba84e376180fad90c3b472ecb4b13433a86e5f1`.
- `result(...)` compact-renderer implementation: `2892f245ee278cea2ef9bd1ac1eecf6c2e636701`.
- Corrected `result(...)` focused-test expectations: `0f8e4eba5390ab87a6dd635853195e736795aa16`.
- Final `result(...)` distribution gate was run from `9152a40ffd4bb8269a4bba6a3a38393966be9c80`.
- Temporary `result(...)` validation workflow removed in `280aec442234bbbd3a060c7f30a3537c757da38a`.
- Commits after the final `result(...)` gate are cleanup/documentation only.

## Approved behavior

EngCalc 0.6.1 remains presentation-focused. The structural calculations, unit engine, 201-point plot sampling grid, signed-envelope rules, magnitude-envelope rules and structural sign convention are unchanged.

### Numerical presentation commands

- `numeric(expr)` remains the detailed numerical presentation: **symbolic formula → explicit numerical substitution → final result**.
- `numeric(expr, target_unit)` preserves the same detailed presentation and converts the final quantity to the requested compatible unit.
- New `result(expr)` is the compact numerical presentation: **symbolic formula → final result**, omitting only the explicit substitution stage.
- New `result(expr, target_unit)` uses the same compact presentation while converting the final quantity to the requested compatible unit.
- `result(...)` deliberately reuses the existing `numeric(...)` evaluation path. It does not introduce a second numerical engine or alternative calculation method.
- For supported partially evaluated polynomial functions such as `M(x)`, `result(M(x))` shows the symbolic function followed directly by the evaluated numerical-coefficient function; `numeric(M(x))` continues to show the intermediate substitution stage.
- `result` is a reserved EngCalc command name.

Examples:

```text
numeric(M_A)
numeric(M_A, kN*m)
result(M_A)
result(M_A, kN*m)

numeric(M(x))
result(M(x))
```

### Plot presentation

- Positive structural moment plots **downward**.
- Multi-series plotting remains `plot(expr1, expr2, ..., x, start, end)`.
- Signed `envelope(...)` remains algebraic max/min.
- `abs(...)` and magnitude envelopes remain available; mixed signed/absolute sources in one envelope are rejected.
- Multi-series plots and envelopes do not use characteristic-value summary panels.
- Characteristic points use compact coordinate labels in the form **`(x, y)`**, for example `(2.5, 3.15)`.
- Characteristic labels contain no duplicated units, no `x =`, `M =`, `V =` prefixes, no boxes and no leader lines/arrows.
- Label text uses the corresponding series color.
- Placement treats axes boundaries, legend, previous labels and sampled curve points as collision constraints before ranking candidate positions.
- A label may be moved farther from a dense characteristic cluster when necessary rather than allow overlap or reintroduce a leader line.

### MathJax presentation

- Long symbolic and numerical MathJax output is split into semantic stages/rows under the notebook width budget; short expressions remain compact.
- The new `result(...)` command uses the same formula/final-result MathJax renderer and simply omits the numerical-substitution stage.

## Open issues / user feedback

- The user preferred a separate `result(...)` command rather than overloading `numeric(...)` with positional flags or changing the existing meaning of its second argument.
- Final real-Colab QA is still required for `result(...)`, especially scalar values, explicit target-unit conversion and partial functions such as `M(x)`.
- Final real-Colab QA is also still required for the compact `(x, y)` plot labels before PR #25 can be merged.
- README command-reference documentation for `result(...)` should be aligned before the release is merged; implementation and validation are complete, but public documentation has not yet been updated for this command.
- For partially evaluated non-polynomial functions where the existing polynomial coefficient evaluator cannot produce an evaluated compact function, `result(...)` inherits the same existing limitation rather than inventing a second evaluation path.

## Validation evidence

### Compact characteristic labels

User visual QA rejected the earlier boxed callouts with leader lines and requested a simpler technical-plot notation: show only `(x, y)` near each characteristic point, without units or leader lines, while preventing overlaps with labels and plotted curves.

- RED test commit: `15cea62505249fc51d48f49af9c48f90baefd3fa`.
- RED focused result: **3 failed**.
- Production implementation: `cd05a0a00fc04be86712dca6e9781985fa3859b9`.
- Final visual gate: GitHub Actions run `33204609923` on `c41a9682d5d8223de37fa65c03d6a1f9062df38c`.
- Focused compact-label suite: **3 passed**.
- Complete source suite at that gate: **239 passed**.
- Four-figure compact-label visual acceptance: **PASS**.
- Visual artifact: `engcalc-v061-compact-label-visuals`, artifact ID `9699168071`, ZIP SHA256 `9f5caf08d2e5caa0f77225ddfeedf06e8d5ff7b0b1bcf120394d5802ca1b0b9d`.
- Compact-label distribution gate run `33205092470`: 21-station comparison against merged 0.6.0 **PASS**, worst absolute difference `0.000e+00`; source, clean-wheel and repeated-source suites were all **239 passed**.

### `result(...)` TDD cycle

The user approved `result(...)` as an additive compact presentation command while keeping `numeric(...)` unchanged.

- RED test commit: `659b71e095597862284c255ca8a2b012cb3cccc1`.
- RED GitHub Actions run `33209657979`: **5 failed, 1 passed**. The failures reproduced the absence of `result(...)` and the fact that `result` was not yet reserved; the existing `numeric(...)` compatibility test already passed.
- Parser implementation: `0ba84e376180fad90c3b472ecb4b13433a86e5f1`. `result(...)` is normalized to the existing `numeric(...)` evaluation call while the original statement source is preserved for presentation.
- Renderer implementation: `2892f245ee278cea2ef9bd1ac1eecf6c2e636701`. Formula and final result remain; the explicit substitution stage is suppressed only when the original command was `result(...)`.
- First GREEN attempt found one incorrect test expectation for the known partial polynomial; the implementation already omitted the substitution correctly. Test expectations were corrected in `0f8e4eba5390ab87a6dd635853195e736795aa16`.
- Focused GREEN: **6 passed**.

### Final `result(...)` 0.6.1 distribution gate

GitHub Actions run `33210052766` on `9152a40ffd4bb8269a4bba6a3a38393966be9c80`:

- branch diff check against `origin/main`: **PASS**;
- source version: **0.6.1 PASS**;
- focused `result(...)` suite: **6 passed in 1.40 s**;
- complete source suite: **245 passed in 56.58 s**;
- exact wheel `engcalc_colab-0.6.1-py3-none-any.whl`: **built successfully**;
- installation into a clean venv: **PASS**;
- installed-wheel smoke from `/tmp` with empty `PYTHONPATH`: **PASS**; it verified both compact `result(M_A, kN*m)` and unchanged detailed `numeric(M_A, kN*m)`;
- complete suite against the installed wheel with repository `src` removed: **245 passed in 55.96 s**;
- repeated source suite: **245 passed in 55.38 s**;
- temporary validation workflow was removed after the successful gate in `280aec442234bbbd3a060c7f30a3537c757da38a`.

The `result(...)` change does not modify `src/engcalc_colab/numeric.py`, the structural formulas, plotting sampling or envelope calculations. It changes command recognition and which already-computed rendering stage is displayed.

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

## Colab side-by-side browser extension

The vertical-scroll issue in the user's custom Colab side-by-side Chrome extension was investigated separately from EngCalc. Diagnostic evidence showed that the actual output lived in cross-origin `*-colab.googleusercontent.com/outputframe.html` iframes, including one frame fixed at 1000 px. Extension **v1.0.4** adds frame-height synchronization for those Colab output frames. The user subsequently reported that the vertical-output scrollbar problem appears solved.

This fix belongs to the browser extension, not EngCalc. Do not add Colab-specific output-height code to EngCalc unless new independent evidence requires it.

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

## Roadmap / active plan

Master roadmap remains on branch `planning/engcalc-evolution-roadmap`:

- `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`;
- `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`.

The original 0.6.1 visual-polish spec had deferred numeric ergonomics. The user explicitly reopened that narrow scope before merge and approved the additive `result(...)` command. This checkpoint records that approved amendment. Do not infer that any broader roadmap milestone has started.

## Exact next step

1. In a fresh/restarted Colab runtime, reinstall `feature/v0.6.1-visual-polish-2` and verify `engcalc_colab.__version__ == "0.6.1"`.
2. Run a compact comparison containing `numeric(M_A, kN*m)`, `result(M_A, kN*m)`, `numeric(M(x))` and `result(M(x))`.
3. Verify visually that `numeric(...)` still shows formula → substitution → result, while `result(...)` shows formula → result with the same numerical answer.
4. Rerun the complete propped-cantilever exercise and visually QA the four final plot families with compact `(x, y)` labels.
5. Confirm the long MathJax derivations remain correct and readable.
6. Align README command-reference documentation for `result(...)` before merge.
7. Inspect PR #25 if desired; **do not merge yet**.
8. Merge PR #25 only after the user gives explicit approval of this updated Colab visual QA.

## How to resume in a new conversation

Tell the new agent:

> Continue EngCalc from `docs/project-context/CURRENT.md`. Read root `AGENTS.md`, verify GitHub state, inspect PR #25 and continue the final Colab QA for `result(...)` plus compact plot labels. Do not merge without explicit approval.

The repository context file and Git history are authoritative for project continuity.
