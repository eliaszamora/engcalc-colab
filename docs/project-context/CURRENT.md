# EngCalc Current Project Context

_Last updated: 2026-08-29 after the EngCalc 0.6.2 distribution gate passed and the temporary validation workflow was removed._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default branch `main` remains EngCalc **0.6.1** at `1543e6ca5b0d631d5dea6922c6d4a2d817371448`.
- Active release branch: `feature/v0.6.2-numeric-ergonomics`.
- Branch was created from current `main` and is not behind it.
- Candidate version: **0.6.2** in both `pyproject.toml` and `src/engcalc_colab/__init__.py`.
- Release metadata commit: `05ad676d70eeca2e36a27beade741fcc017f3cb2`.
- Final validated distribution-gate tree: `6343844965cce707d60dd523da282b70c6dcab78`.
- Temporary validation workflow was removed afterward in `03049db2d70a97b07392a39fb32f3d5a13808020`; this cleanup changed no product or test file.
- A PR for 0.6.2 still needs to be created/inspected. Do not merge without explicit user approval.

## Approved behavior

### 0.6.1 presentation baseline

- `numeric(...)` renders formula → explicit numerical substitution → final result.
- `result(...)` renders formula → final result using the same numerical engine.
- Semantic MathJax spacing remains 4 pt for wrapped continuation rows, 8 pt for a new stage/consecutive source result, and 16 pt after an explicit blank source line.
- Structural positive moment remains plotted downward.
- Compact plot/envelope characteristic annotations remain `(x, y)` with no boxes, duplicated units or leader lines.
- User-provided real-Colab visual evidence on 2026-08-29 confirmed the intended `numeric(...)`/`result(...)` hierarchy and spacing; that visual QA is accepted.

### 0.6.2 numeric ergonomics and diagnostics

- A complete unit-bearing/numeric expression may be passed directly to a one-argument user function in `numeric(...)` and `result(...)`.
- Required examples now supported include:
  - `numeric(M(2.5*m))`;
  - `numeric(V(L/2))` when `L` has a numerical value;
  - `numeric(R(4*tonf/m))`;
  - `numeric(M(0*m), kN*m)` without losing the length dimension of the zero argument.
- A lone unassigned name intentionally remains symbolic, so `numeric(M(x))` / `result(M(x))` continue to produce partial numerical functions.
- The bridge is AST-level: complete function arguments are evaluated in the restricted Pint-backed `NumericContext` before SymPy can erase units; intentionally free names remain symbolic.
- `result(...)` reuses the `numeric(...)` evaluation path; only presentation differs.
- Corrective diagnostics now distinguish unknown numeric names, unresolved numerical symbols and incompatible units in evaluated user functions while preserving the existing public exception hierarchy.
- Existing `solve(expr, unknown)` / explicit `eq(...)` behavior is preserved.

## Open issues / user feedback

- No known functional regression is open for the 0.6.2 candidate.
- The master roadmap files on `planning/engcalc-evolution-roadmap` still use the original `0.6.1` label for the numeric-ergonomics Task 1. The shipped visual release consumed 0.6.1, so those roadmap documents should be amended to call this completed milestone **0.6.2** before starting 0.7.0. This is documentation/planning alignment only and is not a blocker to validating the 0.6.2 product tree.

## Validation evidence

### TDD and persisted implementation

- RED contract stage reproduced the expected symbolic/numeric crossing failures before production changes.
- The dimensional-zero acceptance exposed the important `0*m -> 0` SymPy simplification boundary; the implementation was corrected to resolve complete arguments from their AST before symbolic simplification.
- Persisted implementation verification on the release branch passed **10 focused tests** and **262/262 complete source tests** before release metadata closure.
- Release-metadata closure then passed **30/30 focused tests** and **262/262 complete source tests** before committing version 0.6.2.

### Final 0.6.2 distribution gate

GitHub Actions run **`33228562198`** on head **`6343844965cce707d60dd523da282b70c6dcab78`** completed successfully:

- release metadata: PASS (`0.6.2` in package and `pyproject.toml`);
- focused 0.6.2 contracts: **30 passed in 2.13 s**;
- complete source suite: **262 passed in 55.82 s**;
- wheel `engcalc_colab-0.6.2-py3-none-any.whl`: built successfully with metadata version 0.6.2;
- clean virtual-environment wheel installation: PASS;
- smoke from `/tmp` with empty `PYTHONPATH`: PASS, importing from `site-packages` and exercising direct `0*m`, partial `M(x)` and `result(M(2.5*m), kN*m)` behavior;
- source-free complete suite against the installed wheel: **262 passed in 54.14 s**;
- repeated complete source suite: **262 passed in 54.47 s**;
- validated wheel artifact: `engcalc-colab-0.6.2-wheel`, artifact ID **9707745104**, ZIP digest `sha256:50d4d465314aa3b5e1fa4076e24750ce484f7fc91047329dab8997fcded6bd75`.

After this gate the temporary workflow was removed. No product or test file changed after the validated gate; only workflow cleanup and project-context documentation changed.

## Roadmap / active plan

- The active roadmap is still maintained on branch `planning/engcalc-evolution-roadmap`:
  - `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md`
  - `docs/superpowers/plans/2026-08-28-engcalc-evolution-roadmap-implementation.md`
- Numeric ergonomics/diagnostics is the milestone that must be labeled **0.6.2** after the actual 0.6.1 visual release.
- Next functional milestone after 0.6.2 remains **0.7.0 — scalar engineering mathematics** (`sqrt`, trig/inverse trig, `exp`, `log`, `pi` with explicit unit-aware rules).

## Exact next step

1. Create the 0.6.2 pull request from `feature/v0.6.2-numeric-ergonomics` into `main`.
2. Inspect its full changed-file set, head SHA, mergeability and CI/release-gate evidence; confirm the temporary workflow is absent.
3. Do **not** merge the PR until the user explicitly authorizes the merge.
4. Amend the roadmap documents on `planning/engcalc-evolution-roadmap` so Task 1 is labeled 0.6.2, while keeping 0.7.0 and later milestone numbering unchanged.
5. After 0.6.2 merges, update `main` project context and begin 0.7.0 only from the merged baseline.

## How to resume in a new conversation

Read this file first, then verify the active branch/PR against GitHub. The 0.6.2 product candidate is already fully distribution-tested. If the PR has not yet been created, create and inspect it; if it exists, inspect current head/mergeability and changed files. Never merge 0.6.2 without explicit user approval. After merge, align the roadmap labels and start 0.7.0 from merged `main`.
