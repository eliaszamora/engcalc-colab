# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.2 post-audit remediation is ACTIVE on `fix/v0.9.2-post-audit-remediation`. Tasks 1–2 are COMPLETE. Task 3 (N-3 unit-literal propagation) is NEXT. Released `main` remains untouched._

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
  These must be removed before final PR closure.

## Corrective task status

1. **COMPLETE** — baseline + N-1/N-2/N-3/N-4 persistent reproductions + N-1 supported-version diagnosis.
2. **COMPLETE** — N-1/N-2 exact-candidate residual validation unified with deterministic fallback contract.
3. **NEXT** — fix N-3 by centralizing unit-literal overrides at characteristic solver boundaries.
4. **PENDING** — fix N-4 symbolic extrema presentation without changing numeric semantics.
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

Scope audit of the product step showed only `fallback.py` and `candidates.py` plus the temporary validation workflow; no unrelated product files changed.

### Harness-only correction

Initial Task 2 GREEN run:
- Run: **`33404574761`**.
- Job: **`99528833618`**.
- N-1/N-2 focused already passed **11/11**.
- Job then failed only because the temporary workflow referenced nonexistent `tests/test_roots.py`.
- No product failure was involved.

Harness fix:
- **`d196cb9e2f21db6c57e2c6eb8edefe6a72cabd3e`** — `test: fix Task 2 characteristic gate path`
- Correct path: `tests/test_characteristics_roots.py`.

### Authoritative Task 2 GREEN

Run: **`33404788103`**.
Job: **`99529556426`**.
Conclusion: **SUCCESS**.

Results:
- compileall: PASS.
- N-1/N-2 focused: **11 passed, 5 deselected in 3.64 s**.
- characteristic focused (`fallback`, `roots`, `acceptance`): **41 passed in 14.52 s**.
- released baseline suite excluding the intentionally still-RED post-audit file: **884/884 GREEN in 165.22 s**.
- N-3 isolation gate: **3 failed, 1 passed, 12 deselected in 1.59 s** — exactly the three expected public failures; the already-resolved lower-level fallback control remains GREEN.
- N-4 isolation gate: **1 failed, 15 deselected in 0.85 s** — expected symbolic `Abs(a)` display failure.
- `git diff --check`: PASS.
- final marker: **`TASK2_GREEN_GATE=PASS`**.

Task 2 is therefore closed. N-3/N-4 remain intentionally RED and are handled independently in Tasks 3/4.

## N-3 current RED signatures

Using:

```text
L := 6*m
q := 12*kN/m
V(x) = q*(L/2-x)
M(x) = q*x*(L-x)/2
```

Current public failures:
1. `roots(V(x) - 6*kN, x, 0, L)` -> `EngEvaluationError: characteristic numerical fallback could not validate a solution set`.
2. `extrema(M(x) - 20*kN*m, x, 0, L)` -> returns zero points instead of three.
3. `intersections(M(x), 20*kN*m + 0*x, x, 0, L)` -> `EngEvaluationError: intersections responses could not be evaluated on the requested domain`.
4. Lower-level fallback given an already-resolved unit-literal override dictionary remains GREEN.

This isolates N-3 to propagation/resolution of direct unit literals, not the fallback root algorithm itself.

## Exact next step — Task 3

1. Inventory every `evaluate_symbolic(...)` call under `src/engcalc_colab/characteristics/` and classify how its overrides are obtained.
2. Confirm the focused N-3 public RED boundary on the Task-2-closed tree.
3. Resolve direct unit literals exactly once at each public solver boundary:
   - roots: response expression;
   - intersections: left then right response merged into one dictionary;
   - extrema: response expression before continuous/Piecewise derivative analysis.
4. Preserve caller-provided overrides and never mutate caller-owned dictionaries.
5. Propagate the resolved override dictionary through all subordinate candidate/fallback/Piecewise/evaluation paths.
6. Re-run the inventory and leave no response-evaluation path unclassified.
7. Verify N-3 focused GREEN, characteristic integration suites, compileall, and the released 884-test baseline. N-4 must remain the only intentional future RED.
8. Update this file and close Task 3 before starting N-4.

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

Read this file first. Work from `fix/v0.9.2-post-audit-remediation`, never directly from `main`. Tasks 1–2 are complete. The next operation is Task 3: inventory characteristic `evaluate_symbolic()` boundaries, confirm N-3 RED, then centralize and propagate unit-literal overrides. Do not begin N-4 until Task 3 is fully GREEN. Never invoke Codex without explicit authorization.
