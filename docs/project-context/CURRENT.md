# EngCalc Current Project Context

_Last updated: 2026-08-28 after implementing and distribution-validating the user-approved semantic **4 / 8 / 16 pt** MathJax spacing hierarchy, aligning public README documentation, and correcting the pre-merge Colab QA install protocol after a fresh runtime exposed that `--no-deps` leaves Pint unavailable._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` still contains EngCalc **0.6.0**.
- Release-candidate branch: `feature/v0.6.1-visual-polish-2`.
- Open PR: **#25 — `release: EngCalc 0.6.1 visual polish`**, targeting `main`.
- Release-candidate version: **0.6.1**.
- PR must remain unmerged until the user explicitly approves the final real-Colab QA.
- Compact plot labels `(x, y)` are already user-approved in real Colab.
- `result(...)` is implemented and distribution-tested; final real-Colab visual comparison with `numeric(...)` remains pending.
- Latest semantic-spacing renderer implementation: `1e14147b8edd48d621e9d8d5e07d3ec79a03ed1a`.
- Latest fully distribution-validated product/test head: `6069ba78a180669bc1377681a6a328c18d6809ca`.
- Temporary semantic-spacing workflow removed in `844001e255d162eb7b629eb99ef59d36b9468781`.
- README was aligned with `result(...)` and the final 4/8/16 spacing policy in `7de4c4ed73b29ae3b74da4de7138b3c3f4048967`.

## Approved behavior

EngCalc 0.6.1 remains presentation-focused. Structural calculations, Pint unit evaluation, the 201-point plotting grid, signed/magnitude envelope rules and the structural sign convention are unchanged.

### Numerical presentation

- `numeric(expr)` = symbolic formula → explicit numerical substitution → final result.
- `numeric(expr, target_unit)` keeps the same detailed stages and converts the final quantity.
- `result(expr)` = symbolic formula → final result, omitting only the explicit substitution stage.
- `result(expr, target_unit)` is the compact variant with target-unit conversion.
- `result(...)` reuses the existing `numeric(...)` evaluation path; it is a presentation alias, not a second calculation engine.

### Plot presentation

- Positive structural moment plots downward.
- Multi-series `plot(...)`, signed `envelope(...)`, `abs(...)` and magnitude envelopes remain available.
- Characteristic points use compact coordinate labels `(x, y)` with no duplicated units, prefixes, boxes or leader lines.
- Label color follows its series; placement avoids axes bounds, legend, prior labels and sampled curves.
- Real-Colab visual QA of the compact plot-label design is **approved by the user**.

### Semantic MathJax spacing — final 4 / 8 / 16 hierarchy

The renderer now distinguishes a **wrapped continuation of one mathematical stage** from a **new mathematical stage**.

- **4 pt** — continuation row of the same mathematical stage because an expression wrapped for width.
- **8 pt** — a new mathematical stage inside one operation, e.g. `solve`: equation → solved result; `numeric`: formula → substitution → result; `result`: formula → result.
- **8 pt** — consecutive source instructions/results with no blank source line.
- **16 pt** — the next source result is preceded by an explicit blank line in `%%eng`.
- The old blanket `2 pt` policy for every internal row is removed.

Examples of intended hierarchy:

```text
solve(...)
  equation being solved
      8 pt
  solved assignment

numeric(...)
  symbolic formula
      8 pt
  numerical substitution
      8 pt
  final result

long wrapped formula
  first part
      4 pt
  continuation of same formula
```

## Semantic-spacing TDD and validation

User feedback from a real `solve(...)` output showed that equation and solution were incorrectly separated by the same old 2 pt used for mere wrapping. The approved correction was the general 4/8/16 hierarchy above rather than a `solve`-specific patch.

### RED

- Regression-test commit: `e2c48917b5c68022aa037cb57151011cf2fb6d75`.
- GitHub Actions RED run: `33219994765`.
- Result: **3 failed**.
- Failures demonstrated that `solve`, `numeric` stages and true wrapping all still used `2 pt`.

### GREEN implementation

- Final repaired renderer commit: `1e14147b8edd48d621e9d8d5e07d3ec79a03ed1a`.
- Focused GREEN run: `33220209199`.
- Result: **3 passed**.
- The implementation classifies internal rows semantically: same-stage wrapping receives 4 pt; stage boundaries receive 8 pt.
- A first automated patch attempt produced invalid indentation and was discarded/repaired before validation; no successful gate relies on that malformed intermediate tree.

### Full distribution gate

The first complete-suite attempt correctly found six legacy tests still asserting the retired 2 pt contract. Those tests were updated to the approved hierarchy. Final gate:

- GitHub Actions run: **`33220438965`**.
- Validated head: **`6069ba78a180669bc1377681a6a328c18d6809ca`**.
- Focused semantic/magic/renderer suite: **23 passed in 5.44 s**.
- Complete source suite: **249 passed in 52.00 s**.
- Wheel `engcalc_colab-0.6.1-py3-none-any.whl`: **built successfully**.
- Clean-venv wheel installation: **PASS**.
- Installed-wheel smoke from `/tmp` with empty `PYTHONPATH`: **PASS**, explicitly checking solve=8 pt, wrapping=4 pt, consecutive=8 pt, blank-line=16 pt and numeric stage boundaries=8 pt.
- Complete suite against the installed wheel with repository `src` removed: **249 passed in 51.35 s**.
- Repeated source suite: **249 passed in 51.39 s**.
- Temporary workflow removed after the successful gate in `844001e255d162eb7b629eb99ef59d36b9468781`.

## Earlier 0.6.1 validation already retained

### Compact characteristic labels

- Compact-label visual gate run `33204609923`: focused 3 passed; source 239 passed; four-figure visual acceptance PASS.
- 21-station comparison against merged 0.6.0 in run `33205092470`: worst absolute numerical difference `0.000e+00`.
- User subsequently approved the compact graph appearance in real Colab after exact-commit installation.

### `result(...)`

- RED run `33209657979`: 5 failed, 1 passed.
- Focused GREEN: 6 passed.
- Parser implementation: `0ba84e376180fad90c3b472ecb4b13433a86e5f1`.
- Renderer implementation: `2892f245ee278cea2ef9bd1ac1eecf6c2e636701`.
- Distribution run `33210052766`: source 245 passed; wheel build/install PASS; installed-wheel 245 passed; repeated source 245 passed.

## Real-Colab installation rule before merge

Because successive QA revisions all report package version `0.6.1`, installing a moving branch with only `--upgrade` previously left an older submodule in `site-packages` while `__version__` still read `0.6.1`.

A fresh Colab runtime then exposed a second installation detail: using the exact VCS commit together with `--force-reinstall --no-deps` can leave EngCalc installed while required dependency **Pint** is absent. The wheel builds successfully, but `%load_ext engcalc_colab` then fails at `from pint.errors import DimensionalityError` with `ModuleNotFoundError: No module named 'pint'`.

For pre-merge real-Colab QA, use this two-step protocol so the validated EngCalc source is force-reinstalled without unnecessarily force-reinstalling Colab's whole scientific stack:

```python
%pip install -q "pint>=0.24"
%pip install -q --force-reinstall --no-deps --no-cache-dir "git+https://github.com/eliaszamora/engcalc-colab.git@6069ba78a180669bc1377681a6a328c18d6809ca"
```

Then **restart the Colab runtime** before loading/running EngCalc. The validated QA commit is `6069ba78a180669bc1377681a6a328c18d6809ca`; do not substitute an unrelated/moving SHA when performing the final visual comparison.

After merge, the normal installation command should install declared dependencies conventionally; this two-step command is specifically for exact-commit pre-merge QA under the unchanged package version `0.6.1`.

## Colab side-by-side browser extension

The separate vertical-output scrollbar issue was traced to cross-origin Colab `outputframe.html` iframes. Browser-extension v1.0.4 synchronizes those frame heights, and the user reported the issue solved. This is extension behavior, not EngCalc code.

## Documentation alignment

README now documents:

- `result(expr[, target_unit])` alongside `numeric(...)`;
- formula → result versus formula → substitution → result behavior;
- the final **4 / 8 / 16 pt** semantic spacing hierarchy;
- the updated 0.6.1 version note.

No documentation-only commit after the distribution gate modifies the validated package source or tests.

## Roadmap / active plan

Master roadmap remains on branch `planning/engcalc-evolution-roadmap`:

- `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`;
- `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`.

The original 0.6.1 visual-polish scope was explicitly amended by user-approved pre-merge refinements: compact coordinate plot labels, `result(...)`, and the final semantic 4/8/16 MathJax spacing hierarchy.

## Exact next step

1. In Colab, install Pint and then force-install exact commit `6069ba78a180669bc1377681a6a328c18d6809ca` with the two commands above.
2. Restart the Colab runtime.
3. Load EngCalc and rerun the same calculation that visually exposed the problem, especially a `solve(...)` output.
4. Confirm visually:
   - wrapped continuation of one equation: 4 pt;
   - equation → solve result: 8 pt;
   - formula → substitution → result in `numeric(...)`: 8 pt between stages;
   - consecutive source results: 8 pt;
   - explicit source blank line: 16 pt.
5. In the same pass, visually compare `numeric(...)` and `result(...)`.
6. If approved, inspect PR #25 one final time and request explicit user authorization before merge.
7. **Do not merge PR #25 without explicit user approval.**

## How to resume in a new conversation

Tell the new agent:

> Continue EngCalc from `docs/project-context/CURRENT.md`. Read root `AGENTS.md`, verify GitHub/PR #25 state, and continue the final real-Colab QA for the semantic 4/8/16 MathJax spacing plus `result(...)`. Compact plot labels are already user-approved. Use the corrected Pint + exact-commit QA install protocol. Do not merge without explicit approval.

The repository context file and Git history are authoritative for continuity.
