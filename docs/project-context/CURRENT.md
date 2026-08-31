# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.2 post-audit remediation is ACTIVE on `fix/v0.9.2-post-audit-remediation`. Tasks 1–3 are COMPLETE. Task 4 (N-4 symbolic extrema presentation) is NEXT. Released `main` remains untouched._

## Canonical baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released `main`: **`a1dc97b40df64a1e351f1957bd910cde0232a38e`** — `docs: close EngCalc 0.9.2 integration`.
- 0.9.2 release merge: PR #34, merge commit `a42b6bcd18c54794f02d032e8b376747c35bba87`.
- Runtime/package version: **0.9.2**.
- `requires-python = ">=3.10"`.
- Runtime dependency includes `ipython>=8.18`.
- Permanent CI: Python 3.10–3.14.
- Definitive released wheel: `engcalc_colab-0.9.2-py3-none-any.whl`.
- Definitive released-wheel SHA-256: `c493de3b527de4b6100830f00a038a137d1ec110a66aeef27b286e0874357de5`.
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
- Temporary validation infrastructure currently present:
  - `.github/workflows/v092-post-audit-validation.yml`
  - `.github/scripts/v092_post_audit_n1_diagnostic.py`
  - `.github/scripts/v092_post_audit_n3_inventory.py`
  - `.github/scripts/v092_post_audit_task3_apply.py`
  These must be removed before final PR closure.

## Corrective task status

1. **COMPLETE** — baseline + N-1/N-2/N-3/N-4 persistent reproductions + N-1 supported-version diagnosis.
2. **COMPLETE** — N-1/N-2 exact-candidate residual validation unified with deterministic fallback contract.
3. **COMPLETE** — N-3 direct unit literals resolved once at characteristic solver boundaries and propagated consistently.
4. **NEXT** — fix N-4 symbolic extrema presentation without changing numeric semantics.
5. **PENDING** — full source/wheel/multi-Python requalification, cleanup, PR, explicit merge approval gate.

## Task 1 — authoritative evidence

### Clean precondition

- Run: **`33401233875`**.
- Job: **`99517746481`**.
- Python 3.14.
- `python -m compileall -q src/engcalc_colab`: PASS.
- Complete source suite: **884/884 GREEN in 184.47 s**.

### Initial RED contract

- Run: **`33401852319`**.
- Job: **`99519818274`**.
- N-1, N-2, N-3 and N-4 natural contracts RED as expected.
- Materially-wrong candidate control: GREEN.
- Lower-level fallback-with-resolved-unit-literal control: GREEN.
- No `src/` product patch existed at this point.

### N-1 causal diagnosis

Natural symptom:

```text
f(x) = 2.87*x^2 - 12.50459*x + 6.4876637
roots(f(x), x, 0, 5)
```

Expected roots: approximately `0.602` and `3.755`.

Supported-version diagnostic run:
- Run: **`33403078332`**.
- SymPy 1.13.3 job: **`99523886412`** — SUCCESS.
- SymPy 1.14.0 job: **`99523886487`** — SUCCESS.

Both versions show:
- `solveset` returns `{0.602, 3.755}`;
- `_exact_real_solution_set()` returns both candidates with `complete=True`;
- candidate `0.602` leaves residual about `-8.88178419700125e-16` and is rejected by the released implementation;
- candidate `3.755` leaves residual about `-7.10542735760100e-15` and is rejected;
- direct `_fallback_roots()` recovers both physical roots.

Six-case deterministic decimal family on both supported SymPy versions:
- `EMPTY_DISCOVERY_COUNT=0`.
- `RESIDUAL_REJECTION_COUNT=2`.
- `a=2.87, r1=0.602, r2=3.755`: both roots lost by residual rejection.
- `a=0.83, r1=1.125, r2=7.375`: one root lost while one residual simplifies to literal zero.

Conclusion: N-1 and N-2 share the demonstrated root cause. Do **not** add speculative `Float + EmptySet => incomplete` behavior unless a supported-version reproduction appears later.

## Task 2 — N-1/N-2 residual correction

### Product commits

1. **`4278160bc789f48bdc9047cc8c6f5d2e7c813d71`** — `refactor: expose fallback residual contract`
   - extracted `_fallback_response_profile(...)`;
   - extracted `_fallback_validated_residual(...)`;
   - preserved `_FALLBACK_REL_RESIDUAL_TOL = 1e-9` and the existing 1025-sample response-scale semantics;
   - routed fallback root validation through the extracted shared predicate.

2. **`5d573faf833f9c44a47a5e6fb57339381c56324b`** — `fix: validate root candidates by relative residual`
   - symbolic exact zero remains the fast path;
   - non-literal-zero exact candidates now reuse the same response unit, scale and relative-residual contract as deterministic fallback;
   - exact provenance remains `exact`;
   - no change to `_exact_real_solution_set()` completeness semantics;
   - one response profile is reused per continuous zero-set rather than recomputed per candidate.

### Authoritative Task 2 GREEN

Run: **`33404788103`**.
Job: **`99529556426`**.
Conclusion: **SUCCESS**.

Results:
- compileall: PASS.
- N-1/N-2 focused: **11 passed, 5 deselected in 3.64 s**.
- characteristic focused (`fallback`, `roots`, `acceptance`): **41 passed in 14.52 s**.
- released baseline suite excluding the intentionally still-RED post-audit file: **884/884 GREEN in 165.22 s**.
- N-3 isolation: expected three public REDs with lower-level resolved-override control GREEN.
- N-4 isolation: expected `Abs(a)` symbolic presentation RED.
- final marker: **`TASK2_GREEN_GATE=PASS`**.

## Task 3 — N-3 unit-literal propagation correction

### RED + evaluation-boundary inventory

Authoritative RED/inventory run:
- Run: **`33405568505`**.
- Job: **`99532181077`**.
- Conclusion: **SUCCESS as a RED gate**.

Inventory findings before product modification:
- **18** calls to `evaluate_symbolic(...)` under `src/engcalc_colab/characteristics/`.
- **18/18** already supplied an `overrides=` keyword.
- `EVALUATE_SYMBOLIC_WITHOUT_OVERRIDES=0`.
- Therefore N-3 was not caused by a forgotten evaluation call; the propagated dictionary itself entered the solver tree without direct unit literals resolved.

Focused RED behavior on the Task-2-closed tree:
- roots public N-3: RED.
- extrema public N-3: RED.
- intersections public N-3: RED.
- lower-level fallback with boundary-resolved unit literals: GREEN.
- N-1/N-2 remained **11 passed, 5 deselected**.

### Product correction

Product commit:
- **`e68a03de1467a88a68a92c7de7b045ac95fca048`** — `fix: propagate characteristic unit literals consistently`.
- Exact product diff: **3 files, 24 insertions, 15 deletions**:
  - `src/engcalc_colab/characteristics/roots.py`
  - `src/engcalc_colab/characteristics/intersections.py`
  - `src/engcalc_colab/characteristics/extrema.py`
- No unrelated product file changed.

Implemented boundary contract:
- `solve_roots_exact(...)`: resolve response-expression unit literals once through `context.unit_literal_overrides(expression, overrides)`.
- `solve_intersections_exact(...)`: resolve left response then right response into one merged override dictionary.
- `solve_extrema_exact(...)`: resolve response-expression unit literals before continuous/Piecewise derivative analysis.
- Caller dictionaries remain unmutated; the resolved dictionary is propagated through subordinate candidate/fallback/Piecewise/evaluation paths.

### First authoritative GREEN / persistence run

Run: **`33405927906`**.
Job: **`99533390103`**.
Conclusion: **SUCCESS**.

Results:
- `compileall`: PASS.
- solver-boundary inventory: roots **1**, intersections **2**, extrema **1**, all as planned.
- all **18/18** internal `evaluate_symbolic(...)` calls continue to receive `overrides=`.
- N-3 focused: **4 passed, 12 deselected in 1.64 s**.
- characteristic integration: **69/69 GREEN in 17.09 s**.
- N-1/N-2: **11 passed, 5 deselected in 2.80 s**.
- released baseline suite: **884/884 GREEN in 125.65 s**.
- N-4 remains the sole intentional future RED: **1 failed, 15 deselected** with `Abs(a)` symbolic presentation mismatch.
- product persisted as `e68a03de1467a88a68a92c7de7b045ac95fca048`.

### Idempotence confirmation

Workflow-only trigger commit:
- **`da760a7c03390e495cb688c401d20c2782bad726`** — `test: rerun Task 3 idempotence gate`.
- Relative to the product commit it only adds an explanatory comment to the temporary workflow; no product change.

Idempotent run:
- Run: **`33406513709`**.
- Job: **`99535327351`**.
- Conclusion: **SUCCESS**.

Results:
- apply script: `UNCHANGED roots.py`, `UNCHANGED intersections.py`, `UNCHANGED extrema.py`, `TASK3_CHANGED=none`.
- solver-boundary inventory again PASS at **1 / 2 / 1**.
- N-3 focused: **4 passed, 12 deselected in 2.01 s**.
- characteristic integration: **69/69 GREEN in 21.76 s**.
- N-1/N-2: **11 passed, 5 deselected in 3.54 s**.
- released baseline suite: **884/884 GREEN in 161.91 s**.
- N-4 remains the expected sole RED.
- exact final persistence output: **`No Task 3 product patch to commit.`**

Task 3 is therefore closed.

## N-4 current RED signature

Current natural case:

```text
a := 3*m
L := 6*m
s(x) = piecewise(x-a, x < a, 2*(x-a))
extrema(abs(s(x)), x, 0, L)
```

Numeric extrema semantics are already correct:
- lower boundary value quantity = `3 m`;
- upper boundary value quantity = `6 m`.

Presentation defect:
- lower `value_symbolic` is `Abs(a)` instead of the decidable `a`;
- the failing assertion is `simplify(Abs(a) - a) != 0` because the engineering symbol itself carries no positivity assumption even though the registered scalar context knows `a := 3*m`.

Task 4 must change **symbolic presentation only**. It must not change `value_quantity`, extrema roles, Piecewise branch selection, side/topology, or provenance.

## Exact next step — Task 4

1. Confirm focused N-4 RED on the Task-3-closed tree.
2. Inspect existing known-scalar/sign-aware symbolic simplification machinery and reuse it if available.
3. Normalize extrema `value_symbolic` only when registered scalar context makes the simplification decidable; do not globally assume positivity for engineering symbols.
4. Verify numeric quantities, roles, Piecewise topology, side and provenance remain unchanged.
5. Run N-4 focused GREEN, Piecewise/extrema suites, `compileall`, and complete source regression.
6. Commit product as `fix: simplify decidable extrema display values`.
7. Confirm idempotence, update this file, then proceed to Task 5 requalification only after Task 4 is fully closed.

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

Read this file first. Work from `fix/v0.9.2-post-audit-remediation`, never directly from `main`. Tasks 1–3 are complete. The next operation is Task 4: confirm the N-4 RED, inspect existing sign-aware/known-scalar simplification support, and implement presentation-only normalization in extrema. Never invoke Codex without explicit authorization.
