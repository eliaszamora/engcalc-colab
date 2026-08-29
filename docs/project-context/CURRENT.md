# EngCalc Current Project Context

_Last updated: 2026-08-29 after PR #26 merged EngCalc 0.6.2 into `main`, the merged tree was verified against the validated distribution-gate tree, and the release context was closed._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` now contains EngCalc **0.6.2**.
- PR **#26 — `release: EngCalc 0.6.2 numeric ergonomics`** merged successfully on 2026-08-29 after explicit user approval.
- Merge commit: `916290449d1d5f58d420f249e1db094c122701de`.
- Merged PR head: `bc9d93763932acf2421e42406982455af7915b65`.
- `pyproject.toml` and `src/engcalc_colab/__init__.py` both report version **0.6.2**.
- Canonical Colab installation returns to the normal dependency-resolving install from `main`:

```python
%pip install -q --upgrade --no-cache-dir git+https://github.com/eliaszamora/engcalc-colab.git
%load_ext engcalc_colab
```

## Approved behavior

### Presentation baseline retained from 0.6.1

- `numeric(...)` renders formula → explicit numerical substitution → final result.
- `result(...)` renders formula → final result using the same numerical engine.
- Semantic MathJax spacing remains 4 pt for wrapped continuation rows, 8 pt for a new stage/consecutive source result, and 16 pt after an explicit blank source line.
- Structural positive moment remains plotted downward.
- Compact plot/envelope characteristic annotations remain `(x, y)` with no boxes, duplicated units or leader lines.
- Real-Colab visual QA for the 0.6.1 presentation baseline is accepted.

### 0.6.2 numeric ergonomics and diagnostics

- Complete unit-bearing/numeric expressions may be passed directly to one-argument user functions in `numeric(...)` and `result(...)`.
- Supported acceptance cases include:
  - `numeric(M(2.5*m))`;
  - `numeric(V(L/2))` when `L` has a numerical value;
  - `numeric(R(4*tonf/m))`;
  - `numeric(M(0*m), kN*m)` without losing the dimensional meaning of the zero argument.
- A lone unassigned name remains intentionally symbolic, so `numeric(M(x))` / `result(M(x))` continue to produce partial numerical functions.
- The numeric bridge resolves complete function arguments from the restricted AST through the Pint-backed `NumericContext` before SymPy can erase unit information.
- `result(...)` reuses the `numeric(...)` evaluation path; only presentation differs.
- Corrective diagnostics distinguish unknown numeric names, unresolved numerical symbols and incompatible units in evaluated user functions while preserving the existing public exception hierarchy.
- Existing `solve(expr, unknown)` shorthand and explicit `eq(...)` behavior remain unchanged.

## Open issues / user feedback

- No known functional regression or release blocker is open for merged 0.6.2.
- A direct dimensional-zero call may display the mathematical argument as simplified `0` while retaining the correct Pint dimension internally; this is mathematically consistent and not a release blocker.
- No 0.7.0 production work has started yet. Start only from the merged-and-documented 0.6.2 `main` baseline.

## Validation evidence

### Final 0.6.2 distribution gate

GitHub Actions run **`33228562198`** on validated tree **`6343844965cce707d60dd523da282b70c6dcab78`** completed successfully:

- release metadata: PASS (`0.6.2` in package and `pyproject.toml`);
- focused 0.6.2 contracts: **30 passed in 2.13 s**;
- complete source suite: **262 passed in 55.82 s**;
- wheel `engcalc_colab-0.6.2-py3-none-any.whl`: built successfully;
- clean virtual-environment wheel installation: PASS;
- installed-wheel smoke from `/tmp` with empty `PYTHONPATH`: PASS;
- source-free complete suite against the installed wheel: **262 passed in 54.14 s**;
- repeated complete source suite: **262 passed in 54.47 s**;
- validated wheel artifact ID: **9707745104**;
- artifact ZIP digest: `sha256:50d4d465314aa3b5e1fa4076e24750ce484f7fc91047329dab8997fcded6bd75`.

### Post-gate and post-merge tree verification

- Temporary 0.6.2 validation workflow was removed after the gate.
- Comparing validated tree `6343844965cce707d60dd523da282b70c6dcab78` to merged `main` after PR #26 showed only:
  - removal of `.github/workflows/v062-numeric-ergonomics.yml`;
  - updates to `docs/project-context/CURRENT.md`.
- No `src/` or `tests/` file changed after the validated distribution gate.
- Therefore the merged product/test tree is the same validated 0.6.2 product/test tree and the distribution gate did not need to be rerun after merge.
- Post-merge verification confirmed PR #26 is closed/merged and records merge commit `916290449d1d5f58d420f249e1db094c122701de`.

## Roadmap / active plan

- The master roadmap remains on branch `planning/engcalc-evolution-roadmap`:
  - `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`;
  - `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`.
- Roadmap alignment was completed in commit `c46ec4047e1fbf35cde1ec1991d75f8809221f11`.
- The roadmap correctly records actual 0.6.1 as the visual/presentation release and numeric ergonomics as **0.6.2**.
- The next functional milestone is **0.7.0 — scalar engineering mathematics**.
- Planned 0.7.0 public scalar capabilities: `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `exp`, `log`, and constant `pi`, with explicit unit-aware numerical rules.
- 0.7.1 and later milestone numbering remains unchanged.

## Exact next step

1. Read this file, `AGENTS.md`, and the aligned 0.7.0 roadmap spec/plan before implementation.
2. Verify current `main` still points to the merged-and-documented 0.6.2 baseline.
3. Create a new feature branch for **0.7.0 scalar engineering mathematics** from current `main`.
4. Start with RED parser tests for the fixed scalar-function whitelist and reserved constant `pi`.
5. Do not modify production code until those RED tests fail for the expected unsupported/reserved-name behavior.
6. Continue Task 2 using RED → GREEN TDD and close 0.7.0 with the standard source + real wheel + clean-install + installed-wheel full-suite gate.

## How to resume in a new conversation

Read this file first. EngCalc 0.6.2 is merged and closed on `main`; PR #26 is finished. The authoritative release evidence is run `33228562198`, and merged-product identity was established without post-gate `src/` or `tests/` changes. The next work item is 0.7.0 scalar engineering mathematics, starting from current `main` with RED parser tests.