# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.2 is released on `main`. PR #35 is merged and independently re-audited. Two further preexisting defects (A-1/A-2) are corrected on `fix/v0.9.2-audit-a1-a2`; an independent review found and corrected one over-broad completeness assumption in the first A-1 patch. PR #36 is OPEN. Final permanent Python 3.10–3.14 PR CI on the final head is the remaining technical gate. Do not merge without explicit user approval._

## Canonical released state

- Repository: `eliaszamora/engcalc-colab`.
- Runtime/package version: **0.9.2**.
- Canonical released `main` before this follow-up: **`e073320ba988b5956187932b4fb33fa4015a1e80`** — merge of PR #35.
- PR #35: `fix: remediate EngCalc 0.9.2 post-audit correctness defects` — **MERGED**.
- Post-merge CI on `main@e073320...`: run **`33418339062`** — Python 3.10–3.14 **SUCCESS**.
- Complete suite at that released point: **901/901 GREEN**.
- `requires-python = ">=3.10"`.
- Runtime dependency includes `ipython>=8.18`.
- Permanent CI: `.github/workflows/ci.yml`, Python 3.10–3.14 on PRs and pushes to `main`.
- `0.9.3` Exact Envelopes / Governing Intervals remains deferred. It is **not** part of this follow-up.
- Never invoke Codex / Codex Cloud without explicit user authorization.

## PR #35 requalification evidence retained

Authoritative pre-merge requalification:

- run **`33409999894`**;
- focused post-audit: **17/17 GREEN**;
- focused characteristics: **69/69 GREEN**;
- complete source suite: **901/901 GREEN**;
- source-free installed-wheel suite: **901/901 GREEN**;
- Python 3.10, 3.11, 3.12, 3.13 and 3.14: **901/901 GREEN on each**;
- scope audit: no unexpected files.

Corrective wheel:

- `engcalc_colab-0.9.2-py3-none-any.whl`;
- SHA-256: **`1d56169c8591bffd5c3086ced510c92defe53b8e25494604d9426255a03c1dfe`**;
- metadata: `Version: 0.9.2`, `Requires-Python: >=3.10`, runtime `ipython>=8.18`.

Permanent PR #35 CI:

- run **`33411287211`** on head `18d98f7ee0d151c3fa2e53eef9c89f12a9d70120`;
- Python 3.10–3.14: **SUCCESS**.

Post-merge `main` CI:

- run **`33418339062`** on merge commit `e073320ba988b5956187932b4fb33fa4015a1e80`;
- Python 3.10–3.14: **SUCCESS**.

Detailed N-1…N-4 remediation history remains in:

- `docs/superpowers/specs/2026-08-31-engcalc-v0.9.2-post-audit-remediation-design.md`;
- `docs/superpowers/plans/2026-08-31-engcalc-v0.9.2-post-audit-remediation-implementation.md`;
- Git history of PR #35.

## Independent audit after PR #35

An independent adversarial audit of `main@e073320...` re-ran the original N-1…N-4 reproductions and attempted to falsify the remediation.

Audit conclusion:

- N-1…N-4: **resolved**;
- no regression attributable to PR #35 was demonstrated;
- two additional defects were demonstrated, both also reproducing on the pre-PR#35 tree `a1dc97b...`, therefore both are **preexisting**.

### A-1 — HIGH — parameterized complex exact candidates

Reproduction:

```text
a := 1
f(x) = x^2 + a
roots(f(x), x, -2, 2)
```

Released behavior at `e073320...`:

```text
EngEvaluationError: symbolic evaluation failed:
float() argument must be a string or a real number, not 'complex'
```

Correct behavior: **no real roots**.

Cause:

- symbolic candidates such as `±sqrt(-a)` have `is_real = None` before registered numeric values are substituted;
- they passed the three-valued symbolic filter;
- after `a := 1`, the physical candidate becomes complex;
- converting its magnitude with `float()` surfaced an internal Python `TypeError`.

### A-2 — MEDIUM-HIGH — Piecewise open upper edge

Reproduction:

```text
a := 3*m
s(x) = piecewise(x, x < a, x - a)
extrema(s(x), x, 0, a)
```

Released behavior at `e073320...` incorrectly labeled attained endpoint value `0` as `global_max`, even though values approach `3 m` as `x -> a-`.

Correct behavior:

- emit the one-sided point at `x=a`, `side="left"`, value `a`;
- do not assign `global_max` to an attained value below that non-attained supremum.

## Active follow-up branch

- Branch: **`fix/v0.9.2-audit-a1-a2`**.
- Base: **`main@e073320ba988b5956187932b4fb33fa4015a1e80`**.
- PR: **#36 — `fix: correct complex root candidates and open-edge Piecewise extrema`**.
- Package version remains **0.9.2**.
- No 0.9.3 work.
- No dependency changes.
- No temporary validation workflow was added; permanent CI is used directly.

## Claude Code A-1/A-2 implementation

Initial implementation commit:

- **`7f4a2c5eae755ab37aabb81f2d188ac7fb38b8b9`** — `fix: handle complex candidates and open-edge Piecewise extrema`.

Persistent A-1/A-2 regression file:

- `tests/test_v092_audit_a1_a2_regressions.py` — **10 tests**;
- six defect contracts;
- four controls against over-correction.

Claude Code local result before independent review:

- Python 3.14.3;
- **911/911 GREEN** (901 existing + 10 new).

### A-2 correction retained

`characteristics/extrema.py` now:

- emits one-sided limits when the first/last Piecewise region has an open edge coincident with an analysis-domain bound;
- suppresses `global_max` / `global_min` when a non-attained one-sided limit lies strictly beyond every attained value;
- preserves controls for interior breakpoints, non-strict `<=`, lower-bound breakpoints and interior extrema.

No independent over-correction was demonstrated in A-2 during review.

## Independent review of the A-1 implementation

The first A-1 implementation correctly rejected complex candidate locations, but also introduced this broader rule in `_exact_real_solution_set(...)`:

```text
expression.is_polynomial(variable) => solve() discovery is complete
```

That implication is **not valid** for symbolic-parameter polynomials. `solveset()` can return a `Union` containing both a finite solved factor and a `ConditionSet`; `solve()` may then expose only the finite factor. Marking that partial result complete suppresses deterministic fallback and silently loses real roots.

### RED guard

Reviewer guard commit:

- **`cef0a0fa27e333edd2e52de1bf8dfb3070345f92`** — `test: guard incomplete symbolic polynomial discovery`.

New persistent guard:

- `tests/test_v092_audit_completion_guard.py`.

Reproduction:

```text
a := 0
b := -1
f(x) = (x - a)*(x^5 + b*x + 1)
roots(f(x), x, -2, 2)
```

Expected real roots:

- approximately `-1.1673039782614187`;
- `0`.

Authoritative RED CI:

- PR #36 run **`33424746960`**;
- Python 3.10 job **`99595491670`**: `compileall` PASS, suite **1 failed / 911 passed**;
- observed result: only `[0.0]`;
- missing root: approximately `-1.1673039782614187`;
- Python 3.12 independently failed on the same guard.

This proves the over-broad polynomial-completeness rule was a real regression in the first A-1 patch, not a theoretical objection.

### GREEN correction

Correction commit:

- **`527ced09980f19079a6ec0df344a32406162dfa0`** — `fix: preserve incomplete symbolic polynomial discovery`.

The rule is now deliberately narrow:

- `EmptySet`, `FiniteSet` and `Reals` from `solveset(..., domain=Reals)` remain complete;
- `Intersection(FiniteSet, Reals)` is treated as an exhaustive finite candidate family whose real membership is decided after registered values are substituted;
- any result containing unresolved structure such as `ConditionSet` remains incomplete;
- fallback `solve()` candidates remain hints with `complete=False`;
- deterministic numerical fallback therefore still runs when exact discovery is incomplete;
- `_candidate_in_domain(...)` still rejects candidate locations that become complex after registered-value substitution.

This preserves the intended A-1 fix while retaining the existing safety contract that an unresolved numerical scan may not silently become an empty solution set.

## Validation status

Permanent PR CI on the corrected code head is running as:

- run **`33425292081`**;
- code head **`527ced09980f19079a6ec0df344a32406162dfa0`**;
- matrix: Python 3.10–3.14;
- each job runs installation, `compileall`, and the complete `pytest -q` suite.

Because this `CURRENT.md` update itself creates the final documentation commit, a fresh permanent PR CI run on the resulting final PR head is required before merge approval.

Expected complete-suite count on the final branch: **912 tests** (901 released + 10 A-1/A-2 regressions + 1 independent completion guard).

## Invariants that must remain true

- Exact-first remains authoritative; deterministic numerical fallback supplements incomplete exact discovery.
- Exact provenance wins when exact and numeric candidates deduplicate to one physical point.
- A plausible unresolved candidate/region must not silently become an empty solution set.
- Complex candidate locations are rejected as outside a real analysis domain rather than surfacing Python conversion errors.
- Piecewise open edges at analysis-domain bounds retain their one-sided limiting values.
- Non-attained suprema/infima must not be labeled as attained `global_max` / `global_min`.
- Dimensional zero semantics remain preserved.
- Positive structural moment plots downward.
- `envelope(...)` remains sampled in 0.9.2.
- No SciPy dependency.
- IPython remains declared.
- Python 3.10–3.14 remains the advertised range.

## Exact next action

1. Obtain permanent PR #36 CI on the **final branch head** after this documentation update.
2. Require Python **3.10, 3.11, 3.12, 3.13 and 3.14** all to complete GREEN with the full **912-test** suite.
3. Re-check PR scope against `main@e073320...`; no unrelated product, dependency, version or 0.9.3 changes are allowed.
4. Update the PR description with the RED→GREEN reviewer evidence.
5. **Stop for explicit user approval before merge.**

## How to resume

Read this file first. PR #35 is already merged and independently validated. Current work is PR #36 on `fix/v0.9.2-audit-a1-a2`. A-1 and A-2 were both real preexisting defects. Claude Code's initial fixes passed 911/911 locally, but independent review caught a genuine over-broad A-1 completeness rule and proved it RED in permanent CI. The rule has been narrowed at `527ced09980f19079a6ec0df344a32406162dfa0`. The remaining gate is permanent Python 3.10–3.14 CI on the final PR head, followed by explicit user merge approval. Never merge automatically and never invoke Codex without explicit authorization.
