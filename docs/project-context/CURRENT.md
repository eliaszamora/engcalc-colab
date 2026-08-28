# EngCalc Current Project Context

_Last updated: 2026-08-28 after doubling inter-result MathJax spacing to the user-approved 8 pt / 16 pt policy and completing a fresh source/wheel distribution gate. PR #25 remains open and must not be merged without explicit user approval after the remaining real-Colab QA._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` still contains EngCalc **0.6.0**.
- Release candidate branch: `feature/v0.6.1-visual-polish-2`.
- Open PR: **#25 — `release: EngCalc 0.6.1 visual polish`**, targeting `main`.
- Release candidate version: **0.6.1** in both `pyproject.toml` and `src/engcalc_colab/__init__.py`.
- PR is intentionally **not merged** pending explicit final user approval.
- Compact plot-label implementation is already user-approved in real Colab.
- `result(...)` implementation is complete and distribution-tested; final real-Colab visual comparison remains pending.
- Latest output-spacing production commit: `8ea386500b106a3f01a2494176b51e795c60467a`.
- Latest fully validated spacing/product-test head: `f2c1ce5d1c5acffe0b6423087ee5dd3c65afd2ff`.
- Temporary spacing validation workflow removed in `600de43f7e8973c15631de8172a01ea3a60c5e96`.

## Approved behavior

EngCalc 0.6.1 remains presentation-focused. Structural calculations, the unit engine, the 201-point plot sampling grid, signed-envelope rules, magnitude-envelope rules and structural sign convention are unchanged.

### Numerical presentation commands

- `numeric(expr)` remains the detailed numerical presentation: **symbolic formula → explicit numerical substitution → final result**.
- `numeric(expr, target_unit)` preserves that detailed presentation and converts the final quantity to the requested compatible unit.
- `result(expr)` is the compact numerical presentation: **symbolic formula → final result**, omitting only the explicit substitution stage.
- `result(expr, target_unit)` uses the same compact presentation with final-unit conversion.
- `result(...)` deliberately reuses the existing `numeric(...)` evaluation path; it does not introduce a second calculation engine.
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
- **Real-Colab visual QA passed:** after installing the exact validated revision, the user confirmed the modified graphs rendered correctly and approved their appearance.

### MathJax presentation and vertical spacing

- Long symbolic and numerical MathJax output is split into semantic stages/rows under the notebook width budget; short expressions remain compact.
- `result(...)` uses the same formula/final-result MathJax renderer and simply omits the numerical-substitution stage.
- User-approved inter-result vertical spacing is now:
  - **8 pt** between consecutive source results, e.g. `A = 1` immediately followed by `B = 2`;
  - **16 pt** before a result preceded by a source blank line.
- Internal continuation rows that belong to one wrapped/staged mathematical result remain at **2 pt**. The 8/16 pt change does not alter wrapping or the internal formula → substitution → result hierarchy.

## Real-Colab installation lesson for pre-merge QA

During QA, the user observed `engcalc_colab.__version__ == "0.6.1"` while the installed `plotting.py` was still an older 0.6.1 revision. Diagnostics showed:

- package version: `0.6.1`;
- `magic.render_plot is plotting.render_plot`: `True`;
- compact renderer symbol `_coordinate_label`: absent in the installed package.

The branch itself did contain the new renderer. The practical issue was repeatedly installing a **moving branch under the same package version 0.6.1**. For all remaining pre-merge QA, do **not** rely on `--upgrade` plus the branch name alone.

Use an exact commit SHA and force reinstall. The latest fully validated product/test head for the spacing change is:

```text
f2c1ce5d1c5acffe0b6423087ee5dd3c65afd2ff
```

Recommended QA install command:

```python
%pip install -q --force-reinstall --no-deps --no-cache-dir "git+https://github.com/eliaszamora/engcalc-colab.git@f2c1ce5d1c5acffe0b6423087ee5dd3c65afd2ff"
```

Then restart the Colab session before loading/running EngCalc. After an approved merge, installation from `main` becomes canonical again.

## Validation evidence

### Compact characteristic labels

User visual QA rejected the earlier boxed callouts with leader lines and requested a simpler technical-plot notation: show only `(x, y)` near each characteristic point, without units or leader lines, while preventing overlaps with labels and plotted curves.

- RED test commit: `15cea62505249fc51d48f49af9c48f90baefd3fa`.
- RED focused result: **3 failed**.
- Production implementation: `cd05a0a00fc04be86712dca6e9781985fa3859b9`.
- Final visual gate: GitHub Actions run `33204609923`.
- Focused compact-label suite: **3 passed**.
- Complete source suite at that gate: **239 passed**.
- Four-figure compact-label visual acceptance: **PASS**.
- Visual artifact: `engcalc-v061-compact-label-visuals`, artifact ID `9699168071`, ZIP SHA256 `9f5caf08d2e5caa0f77225ddfeedf06e8d5ff7b0b1bcf120394d5802ca1b0b9d`.
- Compact-label distribution gate run `33205092470`: 21-station comparison against merged 0.6.0 **PASS**, worst absolute difference `0.000e+00`; source, clean-wheel and repeated-source suites were all **239 passed**.
- Subsequent **real-Colab visual QA is approved by the user** after exact-commit forced installation exposed the correct renderer.

### `result(...)` TDD cycle

The user approved `result(...)` as an additive compact presentation command while keeping `numeric(...)` unchanged.

- RED test commit: `659b71e095597862284c255ca8a2b012cb3cccc1`.
- RED GitHub Actions run `33209657979`: **5 failed, 1 passed**.
- Parser implementation: `0ba84e376180fad90c3b472ecb4b13433a86e5f1`.
- Renderer implementation: `2892f245ee278cea2ef9bd1ac1eecf6c2e636701`.
- Focused GREEN: **6 passed**.
- Final `result(...)` distribution gate run `33210052766` on `9152a40ffd4bb8269a4bba6a3a38393966be9c80`:
  - focused suite: **6 passed**;
  - complete source suite: **245 passed**;
  - exact wheel `engcalc_colab-0.6.1-py3-none-any.whl`: built successfully;
  - clean-venv installation and smoke: **PASS**;
  - complete suite against installed wheel: **245 passed**;
  - repeated source suite: **245 passed**.

The `result(...)` change does not modify `src/engcalc_colab/numeric.py`, structural formulas, plotting sampling or envelope calculations. It changes command recognition and which already-computed rendering stage is displayed.

### 8 pt / 16 pt spacing TDD cycle

The user explicitly approved doubling the existing source-result spacing from 4/8 pt to **8/16 pt**.

- RED contract commit: `1b4b73590d67db2ee5c93ef5c7f5ce25ba533c6d`.
- Valid RED GitHub Actions run `33214577611`: **2 failed, 13 passed**; the failures showed the old `4 pt` consecutive and `8 pt` blank-line behavior.
- Production implementation: `8ea386500b106a3f01a2494176b51e795c60467a`.
- Focused GREEN run `33214784059`: **15 passed** in `tests/test_magic.py`.
- The first full-suite attempt correctly exposed three legacy tests still asserting the old 4/8 pt contract; those test expectations were aligned with the approved behavior in `e4b3da15bbddd8a7ef85ac13259c9f6a0c829a60` and `f2c1ce5d1c5acffe0b6423087ee5dd3c65afd2ff`.
- Final spacing distribution gate: GitHub Actions run `33215053282` on `f2c1ce5d1c5acffe0b6423087ee5dd3c65afd2ff`:
  - focused spacing/magic suite: **15 passed in 4.61 s**;
  - complete source suite: **246 passed in 59.94 s**;
  - exact wheel `engcalc_colab-0.6.1-py3-none-any.whl`: **built successfully**;
  - clean venv install: **PASS**;
  - installed-wheel smoke from `/tmp`: **PASS**, explicitly asserting consecutive `8 pt` and blank-line `16 pt` spacing;
  - complete suite against installed wheel with repository `src` removed: **246 passed in 59.37 s**;
  - repeated source suite: **246 passed in 58.61 s**.
- Temporary spacing workflow removed in `600de43f7e8973c15631de8172a01ea3a60c5e96`.

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

## Documentation still to align before merge

- README command-reference documentation for `result(...)` still needs to be added/aligned.
- README's old 4 pt / 8 pt spacing sentence must be changed to the approved 8 pt / 16 pt policy.
- These are documentation-only release-closure items; implementation and distribution validation are complete.

## Roadmap / active plan

Master roadmap remains on branch `planning/engcalc-evolution-roadmap`:

- `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`;
- `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`.

The original 0.6.1 visual-polish spec had deferred numeric ergonomics. The user explicitly reopened that narrow scope before merge and approved the additive `result(...)` command. The later 8/16 pt spacing adjustment is also an explicitly approved pre-merge presentation refinement. Do not infer that a broader roadmap milestone has started.

## Exact next step

1. In Colab, force-install exact commit `f2c1ce5d1c5acffe0b6423087ee5dd3c65afd2ff`, then restart the session.
2. Rerun a representative `%%eng` block and visually confirm the new hierarchy:
   - consecutive equations: 8 pt;
   - a source blank line: 16 pt;
   - continuation rows inside one long calculation remain compact.
3. In the same final visual pass, compare `numeric(M_A, kN*m)` vs `result(M_A, kN*m)` and `numeric(M(x))` vs `result(M(x))`.
4. If the spacing and `result(...)` presentation are approved, align README for `result(...)` and 8/16 pt spacing.
5. Inspect PR #25 one final time; **do not merge yet**.
6. Merge PR #25 only after the user gives explicit approval to merge the final 0.6.1 candidate.

## How to resume in a new conversation

Tell the new agent:

> Continue EngCalc from `docs/project-context/CURRENT.md`. Read root `AGENTS.md`, verify GitHub state, inspect PR #25 and continue the final real-Colab QA for 8/16 pt MathJax spacing plus `result(...)`. Compact plot labels are already user-approved. Do not merge without explicit approval.

The repository context file and Git history are authoritative for project continuity.
