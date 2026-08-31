# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.2 post-audit remediation is ACTIVE on `fix/v0.9.2-post-audit-remediation`. Tasks 1–4 are COMPLETE. Task 5 (full requalification / wheel / cleanup / PR approval gate) is NEXT. Released `main` remains untouched._

## Canonical baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released `main`: **`a1dc97b40df64a1e351f1957bd910cde0232a38e`** — `docs: close EngCalc 0.9.2 integration`.
- 0.9.2 release merge: PR #34, merge commit `a42b6bcd18c54794f02d032e8b376747c35bba87`.
- Runtime/package version: **0.9.2**.
- `requires-python = ">=3.10"`.
- Runtime dependency includes `ipython>=8.18`.
- Permanent CI: Python 3.10–3.14.
- Definitive released wheel before this corrective branch: `engcalc_colab-0.9.2-py3-none-any.whl`.
- Released-wheel SHA-256 before this corrective branch: `c493de3b527de4b6100830f00a038a137d1ec110a66aeef27b286e0874357de5`.
- `0.9.3` Exact Envelopes / Governing Intervals remains deferred and is not part of this corrective branch.
- Never invoke Codex / Codex Cloud without explicit user authorization.

## Active corrective branch

- Branch: **`fix/v0.9.2-post-audit-remediation`**.
- Branch baseline: `main@a1dc97b40df64a1e351f1957bd910cde0232a38e`.
- Current work is isolated from `main`; do not merge without explicit user approval.
- Package version stays **0.9.2** during remediation.
- Corrective spec: `docs/superpowers/specs/2026-08-31-engcalc-v0.9.2-post-audit-remediation-design.md`.
- Corrective plan: `docs/superpowers/plans/2026-08-31-engcalc-v0.9.2-post-audit-remediation-implementation.md`.
- Persistent post-audit regressions: `tests/test_v092_post_audit_regressions.py`.
- Persistent post-audit regression file now contributes **17 test items**.
- Temporary validation infrastructure currently present:
  - `.github/workflows/v092-post-audit-validation.yml`
  - `.github/scripts/v092_post_audit_n1_diagnostic.py`
  - `.github/scripts/v092_post_audit_n3_inventory.py`
  - `.github/scripts/v092_post_audit_task3_apply.py`
  - `.github/scripts/v092_post_audit_task4_apply.py`
  These must be removed during Task 5 cleanup.

## Corrective task status

1. **COMPLETE** — baseline + N-1/N-2/N-3/N-4 persistent reproductions + N-1 supported-version diagnosis.
2. **COMPLETE** — N-1/N-2 exact-candidate residual validation unified with deterministic fallback contract.
3. **COMPLETE** — N-3 direct unit literals resolved once at characteristic solver boundaries and propagated consistently.
4. **COMPLETE** — N-4 extrema symbolic display now simplifies decidable `Abs(...)` values using registered numeric context without changing numeric semantics.
5. **NEXT** — full source/wheel/multi-Python requalification, temporary-infrastructure cleanup, documentation, PR, explicit merge approval gate.

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
- N-1 and N-2 therefore share the demonstrated residual-validation cause; no speculative `Float + EmptySet` behavior was added.

## Task 2 — N-1/N-2 residual correction

### Product commits

1. **`4278160bc789f48bdc9047cc8c6f5d2e7c813d71`** — `refactor: expose fallback residual contract`.
   - extracted `_fallback_response_profile(...)` and `_fallback_validated_residual(...)`;
   - preserved `_FALLBACK_REL_RESIDUAL_TOL = 1e-9` and 1025-sample response-scale semantics.

2. **`5d573faf833f9c44a47a5e6fb57339381c56324b`** — `fix: validate root candidates by relative residual`.
   - exact symbolic zero stays the fast path;
   - floating exact candidates reuse the fallback response unit/scale/relative-residual contract;
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
- Exact product diff: **3 files, 24 insertions, 15 deletions**:
  - `roots.py`
  - `intersections.py`
  - `extrema.py`
- roots resolves one response-expression override dictionary;
- intersections resolves left then right into one merged dictionary;
- extrema resolves the response expression before continuous/Piecewise analysis;
- caller-owned dictionaries are not mutated.

### GREEN + idempotence

First GREEN / persistence:
- Run: **`33405927906`**.
- Job: **`99533390103`**.
- boundary inventory: roots **1**, intersections **2**, extrema **1**.
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

Original public case:

```text
a := 3*m
L := 6*m
s(x) = piecewise(x-a, x < a, 2*(x-a))
extrema(abs(s(x)), x, 0, L)
```

Numeric extrema were already correct (`3 m`, `6 m`) but symbolic values retained undecided `Abs(a)` / related forms.

A negative-sign persistent control was added before product change:

```text
a := -3*m
L := 6*m
f(x) = abs(a) + x
extrema(f(x), x, 0, L)
```

This requires `-a` / `L-a`, preventing an invalid global-positive-symbol shortcut.

Persistent test commit:
- **`07864111b09cfdca052b807211e0403fbb885c9c`** — `test: strengthen Task 4 sign-aware extrema RED`.

Authoritative RED gate:
- Run: **`33407321959`**.
- Job: **`99538005203`**.
- positive N-4: expected RED (`Abs(a)` vs `a`).
- negative N-4: expected RED (`Abs(a)` vs `-a`).
- Tasks 1–3: **15 passed, 2 deselected in 4.90 s**.
- existing extrema/acceptance focused baseline: **7 passed, 4 deselected in 1.99 s**.
- `git diff --check`: PASS.

### Product correction

- Product commit: **`df290d561f5d29171ba87aaba53c973d33bc0c86`** — `fix: simplify decidable extrema display values`.
- Exact product diff from its parent: **only `src/engcalc_colab/characteristics/extrema.py`**, **46 insertions / 4 deletions**.
- Introduced presentation-only `_simplify_decidable_abs(...)` behavior:
  - inspect each symbolic `Abs(argument)`;
  - use registered numeric context only to decide the sign of `argument`;
  - preserve the symbolic argument itself (`g`, `-g`, or `0`) rather than substituting numeric values;
  - leave unresolved/nonfinite `Abs(...)` untouched;
  - apply to extrema candidate/interval/one-sided symbolic display production.
- `value_quantity`, extrema roles, Piecewise branch selection, topology/side and provenance remain on their existing computation paths.

### First authoritative GREEN / persistence

- Run: **`33407649126`**.
- Job: **`99539097505`**.
- `compileall`: PASS.
- N-4 focused: **2 passed, 15 deselected in 1.15 s**.
- extrema + acceptance: **11/11 GREEN in 5.21 s**.
- Tasks 1–3 post-audit: **15 passed, 2 deselected in 5.93 s**.
- scope gate: `TASK4_WORKTREE_FILES=src/engcalc_colab/characteristics/extrema.py`.
- complete source suite: **901/901 GREEN in 202.03 s**.
- product persisted as `df290d561f5d29171ba87aaba53c973d33bc0c86`.

### Idempotence confirmation

Workflow-only trigger:
- **`05bd8854dbdbe04fbdfdbeba399a22b9e44347ab`** — `test: rerun Task 4 idempotence gate`.

Idempotent run:
- Run: **`33408181901`**.
- Job: **`99540890768`**.
- apply script: **`TASK4_CHANGED=none`**.
- N-4 focused: **2 passed, 15 deselected in 1.17 s**.
- extrema + acceptance: **11/11 GREEN in 5.33 s**.
- Tasks 1–3: **15 passed, 2 deselected in 5.90 s**.
- `TASK4_IDEMPOTENT_WORKTREE=` (empty).
- complete source suite: **901/901 GREEN in 198.59 s**.
- exact final persistence output: **`No Task 4 product patch to commit.`**

Task 4 is closed.

## Exact next step — Task 5

Execute the approved full requalification sequence; do not change product behavior unless a requalification failure exposes a real defect.

1. Focused post-audit regression:
   - `python -m pytest -q tests/test_v092_post_audit_regressions.py`
   - focused characteristic suites using their actual repository paths.
2. Compile + complete source suite:
   - `python -m compileall -q src/engcalc_colab`
   - `python -m pytest -q`
3. Hygiene/scope audit:
   - `git diff --check main...HEAD`
   - clean worktree expectation after validation materialization;
   - no exact-envelope work, unrelated refactor, temporary harness, or version bump.
4. Build the real **`engcalc_colab-0.9.2-py3-none-any.whl`** and record SHA-256.
5. Inspect wheel metadata and require:
   - `Version: 0.9.2`;
   - `Requires-Python: >=3.10`;
   - IPython runtime dependency.
6. Install the real wheel in an external/source-free environment, confirm `engcalc_colab.__file__` resolves under `site-packages`, copy tests outside the repository, and run the complete source-free suite.
7. Re-run after materialization for idempotence.
8. Remove all temporary `.github/` post-audit validation infrastructure and prove cleanup only deletes temporary files.
9. Update this file with run/job IDs, commits, test counts, wheel filename/SHA, source-free evidence and final action.
10. Open a PR approximately titled `fix: remediate EngCalc 0.9.2 post-audit correctness defects`.
11. Require permanent Python 3.10–3.14 PR CI and **stop before merge**. Merge requires explicit user approval.

## Released 0.9.2 invariants that must remain intact

- Exact-first remains authoritative; deterministic numeric fallback supplements incomplete exact discovery.
- Exact provenance wins when exact and numeric candidates deduplicate to one physical point.
- Plausible candidate evaluation failure must not silently become an empty solution set.
- Roots/intersections share continuous zero-set discovery/validation/fallback/merge semantics.
- Engineering symbols are explicitly real.
- Dimensional zero bounds are preserved.
- Piecewise boundaries/topology rules remain as accepted in 0.9.2.
- Positive structural moment plots downward.
- Plot title weight remains supported (700) with no clean-environment font warning.
- `envelope(...)` remains sampled in 0.9.2.
- No SciPy dependency.
- IPython remains declared.
- Python 3.10–3.14 remains the advertised and CI-validated range.

## How to resume

Read this file first. Work from `fix/v0.9.2-post-audit-remediation`, never directly from `main`. Tasks 1–4 are complete. Task 5 is next: full source/wheel/multi-Python requalification, source-free wheel validation, idempotence, cleanup and PR. Stop before merge and request explicit user approval. Never invoke Codex without explicit authorization.
