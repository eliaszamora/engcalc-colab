# EngCalc Current Project Context

_Last updated: 2026-09-01 — EngCalc 0.9.2 is released and closed on `main`. The **Permanent Quality Gate** is audited, merged and qualified on `main`: PR #37 is integrated at `38b28d5`, post-merge CI is green on Python 3.10–3.14 and Deep qualification is green on 3.10 and 3.14 against the merge commit, which discharges the QG-2 bootstrap exception. No production source changed. One evidentiary residual, QG-3, is open. P-1/P-2/P-3 presentation defects remain open and are deliberately not corrected here. **Engineering Presentation is unblocked and not started.**_

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical `main`: **`38b28d5ab3abce389fff5cdf74552bf7728c8437`** — merge of PR #37, the Permanent Quality Gate. The gate was developed on `c3f4b14`; branch `qa/permanent-quality-gate` is deleted, local and remote.
- Runtime/package version: **0.9.2**. No version bump for QA infrastructure.
- `requires-python = ">=3.10"`; runtime dependency includes `ipython>=8.18`.
- Permanent CI: `.github/workflows/ci.yml`, Python 3.10–3.14 on PRs and pushes to `main`.
- Default suite at `38b28d5`: **1066/1066 GREEN** — 912 product tests plus the 154 Fast Gate tests. Deep suite: **18**, behind an explicit path.
- Post-merge CI on `38b28d5`: run **`33567780020`**, Python 3.10–3.14 **SUCCESS**.
- Post-merge Deep qualification on `38b28d5`: run **`33567836733`**, `workflow_dispatch` in `qualification` mode, Python **3.10 SUCCESS** and **3.14 SUCCESS**.
- Release history: PR #34 merge `a42b6bcd…` (0.9.2); PR #35 merge `e073320b…` (N-1…N-4 remediation, 901/901); PR #36 merge `c3f4b14c…` (A-1/A-2 correction, 912/912); PR #37 merge `38b28d5a…` (Permanent Quality Gate, 1066/1066, no production change).
- The certified `engcalc_colab-0.9.2-py3-none-any.whl` with SHA-256 `1d56169c…` predates PR #36. It is **historical qualification evidence, not an artifact of the current tree**. No GitHub Release is published; the documented install path is `git+https` against `main`, so there is no distributed artifact to reconcile.
- Never invoke Codex / Codex Cloud without explicit user authorization.

## Approved behavior

All 0.9.x contracts remain in force and are regression requirements: exact-first
characteristic analysis, deterministic numerical fallback, dimensional-zero semantics,
sampled `envelope(...)`, positive structural moment plotted downward, Numeric/Pint,
Piecewise, tables, plots, multi-argument functions and Matrix/CAS.

The Permanent Quality Gate adds **no** product behavior. Its approved design is
`docs/superpowers/specs/2026-09-01-engcalc-permanent-quality-gate-design.md`; its
approved plan is
`docs/superpowers/plans/2026-09-01-engcalc-permanent-quality-gate-implementation.md`.

Evidence hierarchy adopted by that design: **Level A** constructive oracle is
authoritative; **Level B** internal invariants and **Level C** metamorphic checks are
complementary; **Level D** shared-solver oracles are prohibited as completeness evidence.

## Open issues / user feedback

Presentation defects, demonstrated and open. They were deliberately excluded from the
Quality Gate phase and are the content of the next release:

- **P-1 HIGH** — automatic default rendering collapses a nonzero physical quantity to `0.00`. Minimized: `v := 8e-05*m` renders `0.00 m`.
- **P-2 HIGH** — the substitution stage prints a nonzero factor as `0.00`, so the shown derivation contradicts its own result: `k = 2v = 2(0.00 m) = 0.00 m`.
- **P-3 MEDIUM** — a derived quantity keeps a dimensionally correct but unreadable compound unit: a deflection renders `5625.00 kN/(GPa·m)` instead of `5.63 mm`.

Root cause of P-1/P-2: `renderer.py::_quantity_latex` formats with fixed decimals over the
stored unit without rescaling. P-3 is a distinct contract: it is **not** caught by a
"never renders as zero" property, which the audit demonstrated by having that property
pass on the deflection case.

Known coverage gaps, not defects: roots separated by less than `0.05`; coefficients with
many more decimal places; Piecewise with more than two branches; nested Piecewise;
Piecewise combined with matrices; intersections between two Piecewise responses;
unresolvable symbolic domain bounds; renderer and plotting beyond the above findings.

Other deferred items: `no_vertical_scroll()` Colab ergonomics; multiline ordinary
function-call parsing; generalized structural eigenproblems.

## Validation evidence

### Independent property-based audit of `characteristics/` — CLOSED

Executed against `c3f4b14`, outside the repository, with Hypothesis 6.167.1 installed
only in the auditor environment. Result: **CLEAN within the audited scope** — no new
mathematical defect demonstrated in roots, intersections, extrema, Piecewise, domains,
units, exact/fallback or deduplication.

908 directed and generated mathematical cases, zero failures:

| Evidence level | Cases |
|---|---|
| A — constructive oracle | 811 |
| B — internal invariant | 24 |
| C — metamorphic | 64 |
| D — shared external oracle | 9 |

Composition: 398 deterministic cases across three seeded sweeps plus 510 Hypothesis
examples over 17 properties at 30 each. 965 total engine invocations.

Historical families re-attacked at scale rather than by their original reproductions:

- **N-1** expanded decimal quadratics: previously 8/20 silent failures, now **0/117**;
- **A-1** complex candidates: passes with degree 4 and 6 variants, symbolic coefficients and units;
- **A-2** open-edge Piecewise: passes across four operators × both bounds;
- **PR #36 completeness guard**: passes nine variants of the partially solvable family.

The 9 Level D cases used `sp.solveset` as oracle and are therefore **not acceptable as
completeness evidence**; their replacement is mandated by the Quality Gate design §8.

### Quality Gate design and plan — audited before implementation

The design audit produced D-1/D-2/D-3, all resolved: the first proposed H4 replacement
embedded its root in the coefficients so SymPy exposed it, defeating the sensitivity
requirement; Fast Gate sizing preceded measurement; and one Extrema partition was
presented as audit-inherited when it was new.

The plan audit produced P-1/P-2/P-3 of the plan, all resolved: `pythonpath = ["src"]`
made helper imports fail under bare `pytest` and in historical runs from another
directory, which would have produced a false RED; Task 5 omitted required Extrema
partitions; and a static cache key would have frozen the Hypothesis database after the
first successful run.

The H4 replacement was verified before implementation: `sp.solve` returns `[a]` only
across every mandated configuration, and simulating the historical over-broad rule makes
the guard fail 4/4 configurations while the corrected implementation passes.

### Permanent Quality Gate — implemented, qualified and merged

PR **#37**, developed on `c3f4b14`, merged to `main` as `38b28d5`. Operating notes:
`docs/quality-gate.md`.

**Scope.** 22 files, none of them production source. `git diff --name-only c3f4b14
38b28d5 -- src/engcalc_colab` is empty, verified again after the merge. Package version unchanged at 0.9.2; Hypothesis pinned to
`6.167.1` as a development dependency only.

**Corpus.**

| Suite | Level A | Level C | Level B | Level D | Total |
|---|---|---|---|---|---|
| Fast, every push | 148 | 6 | 0 | **0** | 154 |
| Deep, scheduled | 16 | 2 | 0 | **0** | 18 |

Level B is zero because the audit's H2 invariant was promoted: the Piecewise
operator × bound matrix now asserts branch ownership, reported side and each attained
role, derived from the public Piecewise contract rather than from current output. No
test carries both an authoritative and a complementary marker.

**Measured budget, GitHub Actions.**

| | Python 3.10 | Python 3.14 |
|---|---|---|
| product suite | 190.1 s | 95.0 s |
| Fast Gate added | **45.4 s** | **22.8 s** |
| Deep Gate qualification | **377.1 s** | **168.7 s** |

Contracts: ≤60 s median added per matrix job with a 90 s ceiling, and ≤10 min for the
Deep Gate with a 12 min ceiling. All satisfied, nothing trimmed. The same Fast Gate
took 62.6 s locally, so extrapolating from the workstation would have argued for
cutting coverage the runners do not need — which is why the design requires sizing to
follow measurement.

**Historical sensitivity dossier.** Each guard run against the state it exists to
catch, with the historical tree verified in use:

| Guard | Bad state | Result |
|---|---|---|
| N-1 expanded decimals | `a1dc97b` | 10 failed / 2 passed, assertion failures |
| A-1 complex candidates | `e073320` | 3 failed, product raises the complex `TypeError` |
| A-2 open upper edge | `e073320` | 2 of 4 operator cases failed, exactly those whose topology involves a one-sided limit |
| H4-A over-broad completeness | `7f4a2c5` | 6 failed of 6 |
| all guards | `c3f4b14` | GREEN |

Obtaining that evidence required an isolated pytest configuration. Run from a
temporary tree, pytest still discovers the repository `pyproject.toml` as its
configfile and prepends the current `src`, so the guards initially **passed** while
appearing to exercise the historical code. That false GREEN is the mirror of the false
RED the plan already guarded against, and `docs/quality-gate.md` records the procedure
that avoids both.

**H4 replacement.** `(x - a)*(x^5 + b*x + c)` with `b > 0`. The derivative `5x⁴ + b` is
strictly positive, so the quintic is monotone and has exactly one real root: the count
comes from calculus and the location from test-local bisection, so no symbolic solver
participates in forming the expectation. The earlier candidate that embedded the root
in the coefficients was rejected because SymPy could then factor it out, leaving the
guard green against the very implementation it existed to catch.

## Roadmap / active plan

1. **Permanent Quality Gate** — **DONE**, merged at `38b28d5` and qualified on `main`.
   QA infrastructure only, no production change.
2. **Engineering Presentation** — active and not started. Next functional release,
   opening with formal RED contracts for P-1, P-2 and P-3.
3. Backlog, deliberately unnumbered until Presentation ships: Exact Envelopes /
   Governing Intervals, scalar equation systems, named cases and combinations,
   verification APIs, golden engineering worksheets.

Versions beyond the next release are not committed, because the audits repeatedly
invalidated longer-horizon numbering.

### Independent audit of PR #37 — findings and resolution

Audited by a reviewer who did not implement the gate, before the merge. Ten of the twelve questions
passed outright; production changes zero; no mandatory Level A partition lost; no
authoritative Level D test; H4 independence and performance budgets both confirmed.

**QG-1 — artifact persistence was silently empty. CORRECTED.** Both
`upload-artifact` steps lacked `include-hidden-files: true`. Since v4 the action skips
hidden files by default and `.hypothesis/` is a dot-directory, so the artifact was
never produced. Verified against runs `33561021489` and `33560303585`: both report
`total_count = 0`. This broke the middle tier of the agreed persistence architecture —
cache for exploratory continuity, artifact as evidence of a run, committed regression
as authority — while the workflow still reported green.

The flag is added in both jobs, and a `Report Hypothesis database state` step now
prints whether the database exists. That second part is not cosmetic: this defect
survived review precisely because an empty artifact collection and a working one look
identical in a green log. An absence that cannot be seen is the same failure mode as
the false GREEN found during historical sensitivity, in a different place.

**QG-2 — Deep qualification not on the exact final head. ACCEPTED AS A BOUNDED
BOOTSTRAP EXCEPTION, NOW DISCHARGED.** The acceptance contract requires Deep qualification at the exact
release-candidate SHA. That requirement is operationally circular for this PR alone:
`workflow_dispatch` only registers once the workflow exists on the default branch, so
qualification must be reached through a temporary trigger, and recording the resulting
evidence moves the head again.

The exception is explicitly limited:

- it applies to PR #37 only, the commit that introduces the workflow;
- between the qualified head `9de3207` and the merge candidate, `quality_tests/deep`
  changed **only in one docstring**, with no effect on behaviour. Documentation, the
  Fast Gate evidence markers and the Deep workflow also changed, the last of these
  solely to correct QG-1 in the persistence and observability of the Hypothesis
  database. Verified: the `pytest` invocation, the per-property `max_examples`, the
  `derandomize` setting and the Python matrix are all untouched, so the qualification
  logic and corpus are the same ones that were qualified;
- the deep suite was run locally on the final content at 18 GREEN;
- **immediately after merge, `Quality Gate Deep` must be run in `qualification` mode
  against the merge commit on `main`. If Python 3.10 or 3.14 is not GREEN there, the
  Quality Gate is not considered integrated and Engineering Presentation does not
  begin.**

That condition is satisfied. Run **`33567836733`** ran `qualification` against
`38b28d5`, the merge commit itself, with Python 3.10 and 3.14 both SUCCESS. The
exception is discharged and the Quality Gate is integrated.

Once the workflow exists on `main`, every later qualification must be on the exact SHA
with no exception. The requirement is not weakened; it was acknowledged as unreachable
exactly once, for the change that creates the mechanism it depends on, and that once
is now spent.

**QG-3 — the QG-1 diagnosis is unverified and its fix is still unexercised. OPEN,
EVIDENTIARY ONLY.** Found while confirming QG-1 after the merge, not by the audit.

Hypothesis creates `.hypothesis/examples/` only when it has a counterexample to store.
On a passing run the directory never exists. Demonstrated directly with Hypothesis
6.167.1, the pinned version, in an isolated tree: a green property leaves no `examples/`
directory at all, and the same property made to fail leaves 22 files in it. The local
repository tree shows the same thing after green Deep runs — `.hypothesis/` holds only
`constants/`, and `examples/` is absent.

The consequence is that `total_count = 0` on runs `33561021489` and `33560303585` does
not demonstrate what QG-1 says it demonstrates. Both runs were green, so the artifact
would have been empty with or without `include-hidden-files`. The observation is
consistent with the hidden-file exclusion and equally consistent with there being
nothing to upload, and therefore distinguishes neither. The post-merge run confirms it:
with the flag in place, run `33567836733` still produced **zero** artifacts, and both
jobs printed `database absent: nothing to preserve from this run`.

This is not a functional defect and nothing needs to be reverted. `include-hidden-files`
is harmless and is probably necessary, since every path under `.hypothesis/` has a
hidden component — but "probably" is the whole point: no run has ever produced a
non-empty artifact, so the middle tier of the persistence architecture has never once
been observed working. It is the audit's own failure mode, an absence that cannot be
seen, reproduced one level up: in the evidence for the fix rather than in the fix.

Two things follow. First, `docs/quality-gate.md` reads as though the artifact is
produced on every run; it should say that the artifact appears only when the gate finds
something, which is by design. Second, the decisive test is cheap and has not been run:
force one Deep property RED on a throwaway branch, dispatch the workflow, and check
whether a non-empty artifact appears. Until that is done, the persistence tier is
designed and documented but not evidenced.

## Exact next step

**Task 14: open Engineering Presentation with formal RED contracts for P-1, P-2 and
P-3.** The Quality Gate is integrated, so the discipline it exists to enforce now
applies: the defect is written as a failing test first, on a branch, and the fix is
what turns it green. This is the first functional release since the gate, and the first
change to production source since `c3f4b14`.

P-1 and P-2 share a root cause in `renderer.py::_quantity_latex`, which formats with
fixed decimals over the stored unit without rescaling. P-3 does not: a dimensionally
correct compound unit is a separate contract, and the audit demonstrated that a
"never renders as zero" property passes on the P-3 deflection case. Three contracts,
not one, and P-3 needs its own oracle rather than a shared invariant.

Carried alongside, small and independent:

- **QG-3** — force one Deep property RED on a throwaway branch and confirm a non-empty
  Hypothesis artifact is produced, then correct the artifact paragraph in
  `docs/quality-gate.md`. Evidentiary; blocks nothing.
- 53 stale remote branches from versions already integrated, `0.2` through `0.9.2`.
  `release/`, `spec/`, `planning/` and the `feature/` branches of published versions are
  the obvious candidates; their history lives in the merge commits on `main`. Not
  touched without an explicit request, because deletion is irreversible.

## How to resume in a new conversation

Read this file first. `main` is at `38b28d5` with 0.9.2 closed and the Permanent
Quality Gate integrated: PR #35, #36 and #37 merged, post-merge CI green on Python
3.10–3.14 (run `33567780020`) and Deep qualification green on 3.10 and 3.14 against the
merge commit itself (run `33567836733`), which discharges QG-2. The gate is 154 Fast
tests collected by the ordinary suite on every push, 1066 GREEN in total, plus 18 Deep
properties run weekly or on demand — with zero production source change across the
whole phase.

The mathematical characteristic subsystem was independently audited and is CLEAN within
the audited scope. The three open defects are all in presentation and untouched; they
are the content of the next release. QG-3 is open, evidentiary only, and blocks nothing.

Read `docs/quality-gate.md` for how to operate the gate and, in particular, for the
isolated configuration that historical sensitivity runs require — without it pytest
discovers the repository `pyproject.toml` and prepends the current `src`, so guards pass
while appearing to exercise historical code.

Never merge without explicit user approval and never invoke Codex without explicit
authorization.
