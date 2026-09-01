# EngCalc Current Project Context

_Last updated: 2026-09-01 — EngCalc 0.9.2 is released and closed on `main`. PR #35 and PR #36 are merged, post-merge CI is GREEN on Python 3.10–3.14, and an independent property-based audit of `characteristics/` is complete and closed. The active phase is the **Permanent Quality Gate**, QA infrastructure only, on branch `qa/permanent-quality-gate`. Production source must not change during this phase. P-1/P-2/P-3 presentation defects remain open and are deliberately not corrected here._

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

## Roadmap / active plan

1. **Permanent Quality Gate** — active. QA infrastructure only, no production change.
2. **Engineering Presentation** — next functional release, opening with formal RED
   contracts for P-1, P-2 and P-3.
3. Backlog, deliberately unnumbered until Presentation ships: Exact Envelopes /
   Governing Intervals, scalar equation systems, named cases and combinations,
   verification APIs, golden engineering worksheets.

Versions beyond the next release are not committed, because the audits repeatedly
invalidated longer-horizon numbering.

## Exact next step

Execute the Permanent Quality Gate plan task by task on `qa/permanent-quality-gate`.

Task 1 is complete when this file, the design spec and the implementation plan are
committed as a documentation-only diff. Task 2 establishes the dev-only Hypothesis
dependency and the Fast/Deep collection topology. **Task 3 benchmarks a representative
slice on GitHub Actions before any corpus is dimensioned** — sizing must not precede
measurement.

Stop conditions during implementation: any permanent Level A test that demonstrates a
current product defect halts the Quality Gate and becomes a separate corrective project;
any required partition that cannot fit under the 90 s per-job ceiling halts implementation
for a topology review.

Task 13 is an independent audit performed by a reviewer who did not implement. No merge
without explicit user approval.

## How to resume in a new conversation

Read this file first. `main` is at `c3f4b14` with 0.9.2 closed, PR #35 and #36 merged,
912/912 GREEN and post-merge CI green on Python 3.10–3.14. The mathematical characteristic
subsystem was independently audited and is CLEAN within the audited scope; the three open
defects are all in presentation and are not touched by the current phase. Work continues
on `qa/permanent-quality-gate` following the approved design and plan under
`docs/superpowers/`. Production source must not change in this phase. Never merge without
explicit user approval and never invoke Codex without explicit authorization.
