# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.2 post-audit remediation is ACTIVE on `fix/v0.9.2-post-audit-remediation`. The released 0.9.2 baseline remains untouched on `main`; Task 1 (reproduction + N-1 diagnosis) is complete and Task 2 (shared residual-validation fix for N-1/N-2) is NEXT._

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
2. **NEXT** — fix N-1/N-2 by unifying exact-candidate and fallback relative-residual validation.
3. **PENDING** — fix N-3 by centralizing unit-literal overrides at characteristic solver boundaries.
4. **PENDING** — fix N-4 symbolic extrema presentation without changing numeric semantics.
5. **PENDING** — full source/wheel/multi-Python requalification, cleanup, PR, explicit merge approval gate.

## Task 1 — authoritative evidence

### Clean precondition

- Run: **`33401233875`**.
- Job: **`99517746481`**.
- Python 3.14.
- `python -m compileall -q src/engcalc_colab`: PASS.
- Complete source suite: **884/884 GREEN in 184.47 s**.

This proves the released baseline was internally green before the new post-audit contracts were materialized.

### Initial RED contract

- Run: **`33401852319`**.
- Job: **`99519818274`**.
- Result: N-1, N-2, N-3 and N-4 natural contracts RED as expected.
- Negative/materially-wrong candidate control: GREEN.
- Lower-level fallback-with-resolved-unit-literal control: GREEN.
- No `src/` product patch existed at this point.

### N-1 causal diagnosis

Independent audit symptom is confirmed:

```text
f(x) = 2.87*x^2 - 12.50459*x + 6.4876637
roots(f(x), x, 0, 5)
```

Expected roots: approximately `0.602` and `3.755`.

However, the proposed `solveset -> EmptySet` mechanism was **not reproduced** on the supported SymPy range.

Supported-version diagnostic run:
- Run: **`33403078332`**.
- SymPy 1.13.3 job: **`99523886412`** — SUCCESS.
- SymPy 1.14.0 job: **`99523886487`** — SUCCESS.

Both versions show:
- `solveset` returns `{0.602, 3.755}`;
- `_exact_real_solution_set()` returns both candidates with `complete=True`;
- candidate `0.602` leaves residual about `-8.88178419700125e-16` and is rejected;
- candidate `3.755` leaves residual about `-7.10542735760100e-15` and is rejected;
- direct `_fallback_roots()` recovers both physical roots.

### Decimal family diagnostic

Six deterministic expanded decimal quadratics were tested on both SymPy 1.13.3 and 1.14.0.

Result on **both** versions:
- `EMPTY_DISCOVERY_COUNT=0`.
- `RESIDUAL_REJECTION_COUNT=2`.
- Case `a=2.87, r1=0.602, r2=3.755`: both roots lost by residual rejection.
- Case `a=0.83, r1=1.125, r2=7.375`: one root lost by residual rejection while the other is accepted because its residual simplifies to exact zero.
- Remaining four cases survive because their candidate residuals simplify to literal zero.

Conclusion:
- N-1 and N-2 share the same demonstrated root cause on the supported runtime matrix: **exact candidates are validated with literal numeric zero instead of the fallback relative-residual contract**.
- Do **not** add speculative `Float + EmptySet => incomplete` behavior unless a supported-version reproduction is later demonstrated.

### Task 1 plan/spec correction

The original N-1 `EmptySet` assumption was removed from the authoritative corrective spec and plan.

Persistent N-1 lower-level regression now requires:
- exact discovery returns the two decimal candidates;
- both candidates survive roundoff-aware validation after the fix.

The public N-1 example and six-case family remain persistent tests.

## Exact next step — Task 2

1. Re-run the aligned RED gate after the corrected N-1 test/node ID.
2. Read the current fallback residual implementation in `src/engcalc_colab/characteristics/fallback.py` and the exact-candidate validation in `candidates.py`.
3. Extract/reuse the smallest dimensionally meaningful relative-residual predicate already represented by `_FALLBACK_REL_RESIDUAL_TOL`; do not create a second independent tolerance policy.
4. Apply it to `_evaluate_root_candidate()` while retaining symbolic exact-zero as the fast path and preserving exact provenance.
5. Verify:
   - N-1 public example;
   - six-case decimal family;
   - N-1 lower-level candidate validation;
   - N-2 `1e-6` and `1e-12`;
   - materially wrong candidate remains rejected;
   - existing fallback/root/acceptance suites;
   - `compileall` + complete source suite.
6. Only after all gates are GREEN, update this file and commit the product change as `fix: validate root candidates by relative residual`.
7. Do not start N-3 until Task 2 is fully closed.

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

Read this file first. Work from `fix/v0.9.2-post-audit-remediation`, never directly from `main`. Task 1 is complete. The next operation is the aligned RED rerun and then the Task 2 relative-residual implementation for the shared N-1/N-2 cause. Do not implement speculative EmptySet behavior. Do not begin N-3 until Task 2 passes focused and complete regression gates. Never invoke Codex without explicit authorization.
