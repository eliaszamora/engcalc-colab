# EngCalc Current Project Context

_Last updated: 2026-08-31 — PR #35 (post-audit remediation of N-1…N-4) is MERGED into `main`. A follow-up independent audit of the merged result found two further defects, A-1 and A-2, both preexisting rather than PR #35 regressions. Their correction is COMPLETE on `fix/v0.9.2-audit-a1-a2` at 911/911 GREEN and awaits PR review and explicit merge approval._

## Canonical baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released `main`: **`e073320ba988b5956187932b4fb33fa4015a1e80`** — merge of PR #35.
- 0.9.2 release merge: PR #34, merge commit `a42b6bcd18c54794f02d032e8b376747c35bba87`.
- Post-audit remediation merge: PR #35, merge commit `e073320ba988b5956187932b4fb33fa4015a1e80`; suite at that commit: **901/901 GREEN**.
- Runtime/package version: **0.9.2**.
- `requires-python = ">=3.10"`.
- Runtime dependency includes `ipython>=8.18`.
- Permanent CI: Python 3.10–3.14.
- Released wheel before this corrective branch: `engcalc_colab-0.9.2-py3-none-any.whl`.
- Released-wheel SHA-256 before this corrective branch: `c493de3b527de4b6100830f00a038a137d1ec110a66aeef27b286e0874357de5`.
- Corrective requalification wheel: **`engcalc_colab-0.9.2-py3-none-any.whl`**.
- Corrective requalification wheel SHA-256: **`1d56169c8591bffd5c3086ced510c92defe53b8e25494604d9426255a03c1dfe`**.
- `0.9.3` Exact Envelopes / Governing Intervals remains deferred and is not part of this corrective branch.
- Never invoke Codex / Codex Cloud without explicit user authorization.

## Active corrective branch

- Branch: **`fix/v0.9.2-post-audit-remediation`**.
- Branch baseline: `main@a1dc97b40df64a1e351f1957bd910cde0232a38e`.
- Current work is isolated from `main`; do not merge without explicit user approval.
- Package version remains **0.9.2**.
- Corrective spec: `docs/superpowers/specs/2026-08-31-engcalc-v0.9.2-post-audit-remediation-design.md`.
- Corrective plan: `docs/superpowers/plans/2026-08-31-engcalc-v0.9.2-post-audit-remediation-implementation.md`.
- Persistent post-audit regressions: `tests/test_v092_post_audit_regressions.py` (**17 tests**).
- Temporary post-audit validation infrastructure has been removed.
- Cleanup commit: **`f92212ffbc3a62fa33108ce384e67574e93cbdae`** — `test: clean post-audit validation infrastructure`.
- Permanent `.github/workflows/ci.yml` remains intact and validates Python 3.10–3.14 on pull requests.

## Corrective task status

1. **COMPLETE** — baseline + N-1/N-2/N-3/N-4 persistent reproductions + N-1 supported-version diagnosis.
2. **COMPLETE** — N-1/N-2 exact-candidate residual validation unified with deterministic fallback contract.
3. **COMPLETE** — N-3 direct unit literals resolved once at characteristic solver boundaries and propagated consistently.
4. **COMPLETE** — N-4 extrema symbolic display simplifies decidable `Abs(...)` values using registered numeric context without changing numeric semantics.
5. **ACTIVE / FINAL GATE** — source/wheel/multi-Python requalification, idempotence and cleanup are COMPLETE. Next: open PR, require permanent Python 3.10–3.14 PR CI, then stop for explicit user merge approval.

## Task 1 — authoritative evidence

### Clean precondition

- Run: **`33401233875`**.
- Job: **`99517746481`**.
- Python 3.14.
- `python -m compileall -q src/engcalc_colab`: PASS.
- Complete released-baseline source suite: **884/884 GREEN in 184.47 s**.

### Initial RED contract

- Run: **`33401852319`**.
- Job: **`99519818274`**.
- N-1, N-2, N-3 and N-4 natural contracts RED as expected.
- Materially-wrong candidate control: GREEN.
- Lower-level fallback-with-resolved-unit-literal control: GREEN.

### N-1 supported-version diagnosis

Diagnostic run:
- Run: **`33403078332`**.
- SymPy 1.13.3 job: **`99523886412`** — SUCCESS.
- SymPy 1.14.0 job: **`99523886487`** — SUCCESS.

Conclusion:
- `solveset` did **not** reproduce `EmptySet` on supported SymPy versions.
- Exact decimal candidates were discovered but rejected because tiny floating residuals were compared to literal zero.
- Deterministic fallback recovered the same physical roots.
- Six-case decimal family: `EMPTY_DISCOVERY_COUNT=0`, `RESIDUAL_REJECTION_COUNT=2` on both supported SymPy versions.
- N-1 and N-2 share the demonstrated residual-validation cause; no speculative `Float + EmptySet` behavior was added.

## Task 2 — N-1/N-2 residual correction

### Product commits

1. **`4278160bc789f48bdc9047cc8c6f5d2e7c813d71`** — `refactor: expose fallback residual contract`.
   - extracted `_fallback_response_profile(...)` and `_fallback_validated_residual(...)`;
   - preserved `_FALLBACK_REL_RESIDUAL_TOL = 1e-9` and 1025-sample response-scale semantics.

2. **`5d573faf833f9c44a47a5e6fb57339381c56324b`** — `fix: validate root candidates by relative residual`.
   - exact symbolic zero stays the fast path;
   - floating exact candidates reuse fallback response unit/scale/relative-residual semantics;
   - exact provenance remains authoritative.

### Authoritative Task 2 GREEN

- Run: **`33404788103`**.
- Job: **`99529556426`**.
- N-1/N-2: **11 passed, 5 deselected in 3.64 s**.
- characteristic focused: **41 passed in 14.52 s**.
- released baseline: **884/884 GREEN in 165.22 s**.
- N-3 and N-4 remained isolated intentional REDs.
- marker: `TASK2_GREEN_GATE=PASS`.

## Task 3 — N-3 unit-literal propagation correction

### RED + evaluation-boundary inventory

- Run: **`33405568505`**.
- Job: **`99532181077`**.
- **18** `evaluate_symbolic(...)` calls under `characteristics/`; **18/18** already supplied `overrides=`.
- `EVALUATE_SYMBOLIC_WITHOUT_OVERRIDES=0`.
- Public roots/extrema/intersections N-3 contracts RED; lower-level fallback with already-resolved unit overrides GREEN.

Conclusion: the propagated override dictionary entered solver trees incomplete; there was no missing `overrides=` call site.

### Product correction

- Product commit: **`e68a03de1467a88a68a92c7de7b045ac95fca048`** — `fix: propagate characteristic unit literals consistently`.
- Exact product diff: `roots.py`, `intersections.py`, `extrema.py` only.
- roots resolves one response-expression override dictionary;
- intersections resolves left then right into one merged dictionary;
- extrema resolves the response expression before continuous/Piecewise analysis;
- caller-owned dictionaries are not mutated.

### GREEN + idempotence

First GREEN / persistence:
- Run: **`33405927906`**.
- Job: **`99533390103`**.
- final boundary inventory: roots **1**, intersections **2**, extrema **1**.
- all **18/18** internal `evaluate_symbolic(...)` paths still receive `overrides=`.
- N-3: **4 passed, 12 deselected in 1.64 s**.
- characteristic integration: **69/69 GREEN in 17.09 s**.
- N-1/N-2: **11 passed, 5 deselected in 2.80 s**.
- baseline: **884/884 GREEN in 125.65 s**.

Idempotence:
- workflow-only trigger: **`da760a7c03390e495cb688c401d20c2782bad726`**.
- Run: **`33406513709`**.
- Job: **`99535327351`**.
- `TASK3_CHANGED=none`.
- **884/884 GREEN in 161.91 s**.
- exact final output: **`No Task 3 product patch to commit.`**

Task 3 context close:
- **`2c705bdf19675894a02dc310b3921ab328bd20db`** — `docs: record Task 3 completion`.

## Task 4 — N-4 symbolic extrema presentation

### Strengthened RED

Original positive case used `a := 3*m`; a second persistent control used `a := -3*m` to prevent an invalid global-positive-symbol shortcut.

Persistent test commit:
- **`07864111b09cfdca052b807211e0403fbb885c9c`** — `test: strengthen Task 4 sign-aware extrema RED`.

Authoritative RED gate:
- Run: **`33407321959`**.
- Job: **`99538005203`**.
- positive N-4: expected RED (`Abs(a)` vs `a`).
- negative N-4: expected RED (`Abs(a)` vs `-a`).
- Tasks 1–3: **15 passed, 2 deselected in 4.90 s**.
- existing extrema/acceptance focused baseline: **7 passed, 4 deselected in 1.99 s**.

### Product correction

- Product commit: **`df290d561f5d29171ba87aaba53c973d33bc0c86`** — `fix: simplify decidable extrema display values`.
- Exact product diff: only `src/engcalc_colab/characteristics/extrema.py`.
- Context-aware presentation normalization evaluates only `Abs(argument)` sign decisions and preserves the symbolic argument as `g`, `-g`, or `0`.
- No global positivity assumption was added.
- `value_quantity`, extrema roles, Piecewise branch selection, topology/side and provenance remain on existing computation paths.

### GREEN + idempotence

First GREEN / persistence:
- Run: **`33407649126`**.
- Job: **`99539097505`**.
- N-4 focused: **2 passed, 15 deselected in 1.15 s**.
- extrema + acceptance: **11/11 GREEN in 5.21 s**.
- Tasks 1–3 post-audit: **15 passed, 2 deselected in 5.93 s**.
- complete source suite: **901/901 GREEN in 202.03 s**.

Idempotence:
- Run: **`33408181901`**.
- Job: **`99540890768`**.
- `TASK4_CHANGED=none`.
- complete source suite: **901/901 GREEN in 198.59 s**.
- exact final persistence output: **`No Task 4 product patch to commit.`**

Task 4 context close:
- **`83eb6fec04b04aed1207d6e546976d62653c598d`** — `docs: record Task 4 completion`.

## Task 5 — full requalification / wheel / cleanup

### Idempotence before requalification

Comparison `83eb6fec...` → `489c4c63...` contains exactly one changed file:
- `.github/workflows/v092-post-audit-validation.yml`

No Task 5 product or persistent-test patch was produced after Tasks 1–4 were materialized.

### Initial requalification run and harness diagnosis

Temporary workflow commit:
- **`148a2ebd85fbb6233e0d4ed9c4f75630e454849a`** — `test: run Task 5 final requalification`.

Run: **`33409252430`**.

All five Python-matrix jobs were GREEN. Qualification job **`99544413915`** passed:
- persistent post-audit regressions;
- focused characteristic regressions;
- full source suite **901/901**;
- scope audit;
- wheel build and metadata;
- import from external `site-packages`.

The first source-free suite reached **889/901 GREEN** and failed exactly 12 tests with `FileNotFoundError` because contract tests read repository support fixtures `README.md` and/or `pyproject.toml`. This was classified as a validation-harness fixture defect, not a package-source/runtime defect: the package import already resolved from the external installed wheel.

Harness-only correction:
- **`489c4c63b127823c89f11e3a63418bff69cf1911`** — `test: fix Task 5 source-free fixtures`.
- external test directory receives `tests/`, `README.md` and `pyproject.toml` only;
- it explicitly contains no `src/` tree and no local `engcalc_colab/` package;
- package import must resolve from venv `site-packages`.

### Authoritative corrected requalification

Run: **`33409999894`** — all six jobs SUCCESS.

Qualification job: **`99546888200`**.
- focused post-audit: **17 passed in 5.55 s**.
- focused characteristics: **69 passed in 21.47 s**.
- `compileall`: PASS.
- complete source suite: **901/901 GREEN in 165.31 s**.
- `TASK5_UNEXPECTED_FILES=` empty.
- `TASK5_VERSION=0.9.2`.
- `TASK5_SCOPE_AUDIT=PASS`.

Real wheel:
- filename: **`engcalc_colab-0.9.2-py3-none-any.whl`**.
- SHA-256: **`1d56169c8591bffd5c3086ced510c92defe53b8e25494604d9426255a03c1dfe`**.
- `Version: 0.9.2`: PASS.
- `Requires-Python: >=3.10`: PASS.
- runtime `ipython>=8.18`: PASS.

Source-free installed-wheel verification:
- import path: `/tmp/engcalc-wheel-venv/lib/python3.14/site-packages/engcalc_colab/__init__.py`.
- no copied `src/` tree.
- no copied local `engcalc_colab/` package.
- support fixtures only: `README.md`, `pyproject.toml`.
- `SOURCE_FREE_IMPORT=PASS`.
- complete external wheel suite: **901/901 GREEN in 166.59 s**.

Uploaded validation artifact:
- artifact name: `engcalc-colab-0.9.2-post-audit-wheel`.
- artifact ID: **`9764966340`**.
- artifact ZIP SHA-256: `2e67a4cee4722e2a0009ec1181d43da8868e4b348ba773a5c9fff2650540ee99`.
- the authoritative **wheel** SHA is the separate `1d56169...` value above.

### Python 3.10–3.14 authoritative matrix

All jobs ran `compileall` and the complete **901-test** suite:

- Python **3.10.21** — job **`99546887894`** — **901/901 GREEN in 238.35 s**; IPython 8.39.0.
- Python **3.11.16** — job **`99546888155`** — **901/901 GREEN in 179.18 s**.
- Python **3.12.14** — job **`99546888045`** — **901/901 GREEN in 143.70 s**.
- Python **3.13.15** — job **`99546888137`** — **901/901 GREEN in 195.68 s**.
- Python **3.14.7** — job **`99546888074`** — **901/901 GREEN in 197.03 s**.

This confirms the advertised Python 3.10–3.14 range after all post-audit corrections.

### Cleanup audit

Cleanup commit:
- **`f92212ffbc3a62fa33108ce384e67574e93cbdae`** — `test: clean post-audit validation infrastructure`.

Comparison `489c4c63...` → `f92212ff...` contains exactly five removals:
- `.github/workflows/v092-post-audit-validation.yml`;
- `.github/scripts/v092_post_audit_n1_diagnostic.py`;
- `.github/scripts/v092_post_audit_n3_inventory.py`;
- `.github/scripts/v092_post_audit_task3_apply.py`;
- `.github/scripts/v092_post_audit_task4_apply.py`.

No product/test/document file changed in cleanup. Permanent `.github/workflows/ci.yml` remains intact.

### Final PR scope before this context update

Comparison `main@a1dc97b...` → cleanup head `f92212ff...` contains exactly the permanent remediation scope:
- `docs/project-context/CURRENT.md`;
- corrective plan/spec;
- `src/engcalc_colab/characteristics/{candidates,fallback,roots,intersections,extrema}.py`;
- `tests/test_v092_post_audit_regressions.py`.

No temporary harness, version bump, exact-envelope work, or unrelated refactor remains.

## Released 0.9.2 invariants preserved

- Exact-first remains authoritative; deterministic numeric fallback supplements incomplete exact discovery.
- Exact provenance wins when exact and numeric candidates deduplicate to one physical point.
- Plausible candidate evaluation failure must not silently become an empty solution set.
- Roots/intersections share continuous zero-set discovery/validation/fallback/merge semantics.
- Engineering symbols remain explicitly real.
- Dimensional zero bounds are preserved.
- Piecewise boundaries/topology rules remain as accepted in 0.9.2.
- Positive structural moment plots downward.
- Plot title weight remains supported (700) with no clean-environment font warning.
- `envelope(...)` remains sampled in 0.9.2.
- No SciPy dependency.
- IPython remains declared.
- Python 3.10–3.14 remains the advertised and requalified range.

## Follow-up audit of merged PR #35 — findings A-1 and A-2

An independent adversarial audit of `e073320` confirmed that N-1…N-4 are genuinely
resolved and that PR #35 introduced no regressions. It then demonstrated two further
defects. Both were verified against the pre-PR#35 tree `a1dc97b` and reproduce there
identically, so **both are preexisting, not PR #35 regressions**.

### A-1 — complex exact candidates surfaced an internal `TypeError`

- Reproduction: `a := 1` / `f(x) = x^2 + a` / `roots(f(x), x, -2, 2)`.
- Was: `EngEvaluationError: symbolic evaluation failed: float() argument must be a string or a real number, not 'complex'`.
- Now: `n = 0`, the correct answer. The literal control `x^2 + 1` already returned `n = 0`, so the two forms now agree.
- Cause: `sp.solve(x**2 + a, x)` yields `±sqrt(-a)`, whose `is_real` is `None` rather
  than `False`, so the three-valued filter in `_exact_real_solution_set` let them
  through; `_candidate_in_domain` then called `float()` on a complex magnitude.
- Correction, in `characteristics/candidates.py`:
  - `_candidate_in_domain` treats a complex location as outside a real domain.
    This is the shared chokepoint for roots, extrema, intersections and the
    Piecewise analysis, so one guard covers every caller.
  - `_exact_real_solution_set` marks a discovery `complete` when the response is a
    polynomial in the variable, because `solve()` is a complete solver there. A
    polynomial whose candidates are all complex is a proven absence of real roots,
    not an unresolved case needing numeric confirmation.
- The numeric-fallback contract was deliberately left untouched:
  `test_unresolved_region_without_validated_root_raises_instead_of_guessing` still
  passes. Relaxing it was tried and rejected — a 1025-point scan can miss a narrow
  root, so an empty scan on a non-polynomial response must stay an error.

### A-2 — false `global_max` when the upper bound coincides with a strict breakpoint

- Reproduction: `a := 3*m` / `s(x) = piecewise(x, x < a, x - a)` / `extrema(s(x), x, 0, a)`.
- Was: both endpoints reported `global_max` with value `0`, contradicted by `s(2*m) = 2 m`.
- Now: the left-sided limit at `a` is reported with value `a`, and no attained point
  claims `global_max`, because the supremum is approached and never reached.
- Cause: one-sided limits were emitted only at junctions between consecutive
  regions. A region whose open edge coincides with an analysis-domain bound has no
  neighbour, so its limit was never emitted and global roles were computed as if the
  region's supremum were its endpoint value.
- Correction, in `characteristics/extrema.py`:
  - `_solve_piecewise_extrema_exact` emits the one-sided limit for the first region's
    open lower edge and the last region's open upper edge.
  - `_piecewise_global_roles` suppresses `global_max` / `global_min` when a one-sided
    limit lies strictly beyond every attained value, mirroring how `unbounded_above`
    and `unbounded_below` already suppress them.
- Interior breakpoints, non-strict (`<=`) conditions, a breakpoint on the lower bound,
  and interior extrema inside the open region are all unchanged; each has a control test.

### Validation

- New contract file: `tests/test_v092_audit_a1_a2_regressions.py`, 10 tests, written
  RED before the corrections. Six encoded the defects; four are controls against
  over-correction (real roots still found, interior breakpoint unchanged, `<=`
  still attains its maximum, interior extremum preserved).
- Full suite on `fix/v0.9.2-audit-a1-a2`: **911/911 GREEN** (901 + 10), Python 3.14.3.
- No production behaviour outside these two paths was modified.

## Exact next action

1. Review PR from `fix/v0.9.2-audit-a1-a2` to `main`, titled `fix: correct complex root candidates and open-edge Piecewise extrema`.
2. Require the permanent `.github/workflows/ci.yml` pull-request matrix for Python 3.10–3.14 to complete GREEN.
3. Do **not** merge automatically.
4. Stop and request explicit user approval before merge.

## How to resume

Read this file first. `main` is at `e073320` with PR #35 merged and 901/901 GREEN. The
follow-up audit findings A-1 and A-2 are corrected on `fix/v0.9.2-audit-a1-a2` at
911/911 GREEN, with ten RED-first regression contracts. The next operation is PR review
plus the permanent CI matrix. Never merge without explicit user approval and never
invoke Codex without explicit authorization.
