# EngCalc Current Project Context

_Last updated: 2026-09-01 — EngCalc 0.9.2 is released and closed on `main`. The **Permanent Quality Gate** is implemented and qualified on branch `qa/permanent-quality-gate`, PR #37, awaiting independent audit and then explicit merge approval. No production source changed. P-1/P-2/P-3 presentation defects remain open and are deliberately not corrected here._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical `main`: **`c3f4b14ccbca2c3ed926c8973648bd5c6168ce58`** — merge of PR #36.
- Runtime/package version: **0.9.2**. No version bump for QA infrastructure.
- `requires-python = ">=3.10"`; runtime dependency includes `ipython>=8.18`.
- Permanent CI: `.github/workflows/ci.yml`, Python 3.10–3.14 on PRs and pushes to `main`.
- Complete suite at `c3f4b14`: **912/912 GREEN**.
- Post-merge CI on `c3f4b14`: run **`33426755170`**, Python 3.10–3.14 **SUCCESS**.
- Release history: PR #34 merge `a42b6bcd…` (0.9.2); PR #35 merge `e073320b…` (N-1…N-4 remediation, 901/901); PR #36 merge `c3f4b14c…` (A-1/A-2 correction, 912/912).
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

Presentation defects, demonstrated and open, **outside the Quality Gate phase**:

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

### Permanent Quality Gate — implemented and qualified

Branch `qa/permanent-quality-gate`, PR **#37**, based on `c3f4b14`. Operating notes:
`docs/quality-gate.md`.

**Scope.** 22 files, none of them production source. `git diff --name-only c3f4b14 --
src/engcalc_colab` is empty. Package version unchanged at 0.9.2; Hypothesis pinned to
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

1. **Permanent Quality Gate** — active. QA infrastructure only, no production change.
2. **Engineering Presentation** — next functional release, opening with formal RED
   contracts for P-1, P-2 and P-3.
3. Backlog, deliberately unnumbered until Presentation ships: Exact Envelopes /
   Governing Intervals, scalar equation systems, named cases and combinations,
   verification APIs, golden engineering worksheets.

Versions beyond the next release are not committed, because the audits repeatedly
invalidated longer-horizon numbering.

### Independent audit of PR #37 — findings and resolution

Audited by a reviewer who did not implement the gate. Ten of the twelve questions
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
BOOTSTRAP EXCEPTION.** The acceptance contract requires Deep qualification at the exact
release-candidate SHA. That requirement is operationally circular for this PR alone:
`workflow_dispatch` only registers once the workflow exists on the default branch, so
qualification must be reached through a temporary trigger, and recording the resulting
evidence moves the head again.

The exception is explicitly limited:

- it applies to PR #37 only, the commit that introduces the workflow;
- the difference between the qualified head `9de3207` and the merge candidate is one
  docstring in `quality_tests/deep`, plus documentation and Fast Gate marker fixes;
- the deep suite was run locally on the final content at 18 GREEN;
- **immediately after merge, `Quality Gate Deep` must be run in `qualification` mode
  against the merge commit on `main`. If Python 3.10 or 3.14 is not GREEN there, the
  Quality Gate is not considered integrated and Engineering Presentation does not
  begin.**

Once the workflow exists on `main`, every later qualification must be on the exact SHA
with no exception. The requirement is not weakened; it is acknowledged as unreachable
exactly once, for the change that creates the mechanism it depends on.

## Exact next step

**Task 13: independent audit of PR #37, by a reviewer who did not implement it.**

The implementer must not certify the gate, and that rule has already paid for itself
twice in this project. It matters more than usual here because the same agent wrote
the design, the plan and the implementation, so three of the four review layers share
one perspective. The twelve audit questions are in the implementation plan; the two
worth the closest attention are whether any mandatory partition was silently dropped
during calibration, and whether the H4 replacement really is independent of the solver
under test.

After a CLEAN audit, request explicit merge approval. Do not merge before that.

No further implementation work remains: temporary calibration infrastructure is
deleted, no audit instrumentation survives, `git diff --check` is clean, `compileall`
passes, the default suite is 1066 GREEN and the Deep suite is 18 GREEN.

## How to resume in a new conversation

Read this file first. `main` is at `c3f4b14` with 0.9.2 closed, PR #35 and #36 merged
and post-merge CI green on Python 3.10–3.14. The mathematical characteristic subsystem
was independently audited and is CLEAN within the audited scope; the three open defects
are all in presentation and untouched. The Permanent Quality Gate is implemented and
qualified on `qa/permanent-quality-gate` as PR #37: 154 Fast Gate tests collected by the
ordinary suite and 18 Deep properties behind an explicit path, with no production source
change. What remains is the independent audit and then explicit merge approval. Read
`docs/quality-gate.md` for how to operate the gate and, in particular, for the isolated
configuration that historical sensitivity runs require. Never merge without explicit user
approval and never invoke Codex without explicit authorization.
