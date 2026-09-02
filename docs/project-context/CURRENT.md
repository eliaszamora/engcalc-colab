# EngCalc Current Project Context

_Last updated: 2026-09-02 — **EngCalc 0.10.1 is released and closed on `main`**, CI green on Python 3.10–3.14, and **verified installable and working in Google Colab from the documented `git+https` path**. Engineering Presentation shipped in 0.10.0: P-1, P-2 and P-3 corrected over five presentation sites. 0.10.1 closes **EP-1**, and a separate fix closes **QG-3**, which turned out to be the real reason the Deep Gate never preserved a counterexample — and which invalidates QG-1's diagnosis. **No defect is currently open.** Neither release was independently reviewed, by explicit direction; the spec records what that cost._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical `main`: **`4a018fb93493815dd266269d8cc5693d7b84e58b`** — merge of PR #39, EngCalc 0.10.0 Engineering Presentation.
- Runtime/package version: **0.10.1**.
- **Colab verified end to end**, not assumed: a clean virtual environment, installed from
  the documented `git+https` path, `%load_ext engcalc_colab`, and a real memoria through
  `%%eng`. Equations, tables, `plot(...)`, `roots(...)` and `extrema(...)` all exercised.
  The plot arrives as a `Figure` handed to `display()` with 2 series over 201 points and
  units appended to the axis labels, so it does not depend on `%matplotlib inline` being
  active.
- `requires-python = ">=3.10"`; runtime dependency includes `ipython>=8.18`.
- Permanent CI: `.github/workflows/ci.yml`, Python 3.10–3.14 on PRs and pushes to `main`.
- Default suite at `4a018fb`: **1079/1079 GREEN** — 912 product tests, the 154 Fast Gate
  tests, and the 13 presentation contracts. Deep suite: **18**, behind an explicit path.
- Post-merge CI on `4a018fb`: run **`33584446587`**, Python 3.10–3.14 **SUCCESS**.
- Post-merge Deep qualification on `4a018fb`: run **`33584467099`**, 3.10 and 3.14 SUCCESS.
- **Pre-merge Deep qualification on the exact release candidate `aa83b2b`: run
  `33576673675`, 3.10 and 3.14 SUCCESS.** This is the first release to satisfy the
  Qualification SHA rule with no exception; PR #37 was the bootstrap that created it.
  Note the constraint it imposes: the run identifiers cannot be committed to the release
  branch, because doing so moves the head and the qualification stops being on the exact
  SHA. They are recorded here, after the merge, against the merge commit.
- Release history: PR #35 merge `e073320b…` (N-1…N-4 remediation, 901/901); PR #36 merge `c3f4b14c…` (A-1/A-2 correction, 912/912); PR #37 merge `38b28d5a…` (Permanent Quality Gate, 1066/1066, no production change); PR #38 merge `536c22dd…` (post-merge state, QG-3); PR #39 merge `4a018fb9…` (**0.10.0 Engineering Presentation**, 1079/1079).
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

**P-1, P-2 and P-3 are CLOSED**, corrected in 0.10.0 (PR #39). Their contracts are in
`tests/test_engineering_presentation.py` and are collected by the ordinary suite on every
push. The reproductions and the before/after are in the release section below; the design
and both audits are in
`docs/superpowers/specs/2026-09-01-engcalc-v0.10.0-engineering-presentation-design.md`.

One thing from their history is still load-bearing and must not be lost: **P-3 is not
caught by a "never renders as zero" property.** The audit demonstrated this by having
that property pass on the deflection case, and the implementation confirmed it from the
other side - `5625.00 kN/(GPa·m)` retains *more* significant figures than `5.63 mm`, so a
rule that merely maximised figures kept the compound unit. Anyone tempted to fold the
presentation contracts into one property will reintroduce P-3 and see green.

**EP-1 is CLOSED**, corrected in 0.10.1 (PR #43). The root cause was not a subtle metric failure:
design §4.5 specifies a band rule and it was never implemented. §4.3's significant-figures
criterion, which exists to decide whether a *declared* unit still says anything, was used
for the family choice as well — one criterion doing two jobs, and wrong for the second.

Measured over the cases that reach the family choice, the band rule is right 10 times out
of 10 where counting figures is right 8. The two it fixes are `f_adm = L/300` with
`L := 6*m`, where the quotient is exactly 0.02 and the figures tie, and a derived
thickness. Ties keep the unit the value already carries, which is what leaves a derived
11 m span in metres rather than rendering it as `11000.00 mm`.

No presentation defect is currently open.

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
   QA infrastructure only, no production change. Still green on every push.
2. **Engineering Presentation** — **DONE**, released as 0.10.0 and merged at `4a018fb`.
   P-1, P-2 and P-3 corrected; one production file changed.
3. **EP-1** — **DONE**, released as 0.10.1. Design §4.5's band rule was specified and
   never implemented; §4.3's significant-figures criterion was doing both jobs. Measured
   10/10 against 8/10 before changing anything.
4. **QG-3** — **DONE**. The Deep Gate had no example database in CI at all.
5. Next, and now genuinely open: Exact Envelopes / Governing Intervals, scalar equation
   systems, named cases and combinations, verification APIs, golden engineering
   worksheets. Nothing among them is a defect; they are new work.

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

## Engineering Presentation - v0.10.0, RELEASED

Merged as PR #39 at `4a018fb`. Design:
`docs/superpowers/specs/2026-09-01-engcalc-v0.10.0-engineering-presentation-design.md`.
Thirteen contracts, 1079 tests, one production file changed: `renderer.py`.

| source | before | now |
|---|---|---|
| `v := 8e-05*m` | `0.00 m` | `0.08 mm` |
| `k = 2*v`, `numeric(k)` | `2(0.00 m) = 0.00 m` | `2(0.08 mm) = 0.16 mm` |
| deflection `P*L^3/(48*E*I_z)` | `5625.00 kN/(GPa*m)` | `5.63 mm` |
| table column of small values | every cell `0.00` | `0.00 0.08 0.16 0.24` in mm |
| `q := 2.8*tonf/m` | `2.80 tonf/m` | unchanged |
| `w := 1e-6*m` | `0.00 m` | `1.00e-6 m` |
| `z := 1e-11*m` | `0.00 m` | unchanged, genuine zero |

**The rule.** Provenance is a property of the result: a `NumericAssignmentResult` and any
value substituted into a derivation are declared, everything else is derived. A declared
unit is kept unless rendering it retains no significant figure. A derived unit is kept
when it came from the engineer's own inputs - measured by term count against the family's
canonical member, so `tonf` and `kN/mm` survive and `kN/(GPa*m)` does not - and otherwise
moves to the family member retaining the most significant figures, ties keeping what the
value already carries. Below the family floor, scientific notation in the declared unit.
`zero_tolerance` is evaluated in the stored unit, before any conversion.

Five presentation sites, not three: the scalar path, the matrix cell path
(`_magnitude_latex`) and the table cell path (`_table_magnitude`). A fourth fixed-decimal
format at `renderer.py:306` is a literal zero for an empty polynomial and is not a
collapse site; the enumeration is closed.

### EP-1 - CLOSED in 0.10.1

The root cause was not a subtle metric failure. **Design §4.5 specifies a band rule and it
was never implemented**; §4.3's significant-figures criterion, which exists to decide
whether a *declared* unit still says anything, was doing the family choice as well. One
criterion, two jobs, wrong for the second.

Measured before changing anything, over the cases that reach the family choice: the band
rule is right **10 out of 10** where counting figures is right **8**. Ties keep the unit
the value already carries, which is what leaves a derived 11 m span in metres instead of
`11000.00 mm` - the outcome design §5 had already measured and rejected.

Why the A-4 contract missed it, which matters more than the defect: it was written with
`L := 5*m`, where `L/300` is unterminating and millimetres win four figures to one. With
`L := 6*m` the quotient is exactly 0.02 and the comparison ties. **The contract passed
through the case rather than through the rule.** Its replacement carries a guard asserting
the tie, so it cannot quietly stop testing what it claims to test.

Re-running the mutation battery afterwards found two guards that had stopped guarding: the
aggregate authorship gate, invisible because the band rule now reaches the same answer on
the only case that covered it, and a tie-break comment crediting `start` with a result the
band rule produces unaided. The first has a contract where the two rules genuinely
disagree; the second is documented as inert, since every family steps by 1000 or more and
a tie can never occur.

### QG-3 - CLOSED, and it invalidates QG-1

**The Deep Gate had no example database in CI at all.** Hypothesis auto-loads a built-in
`ci` profile when it detects CI, setting `database=None`; a profile registered afterwards
inherits it. `quality_deep` set `derandomize` explicitly - so exploration survived - and
never set `database`.

| environment | resolved database |
|---|---|
| local | `DirectoryBasedExampleDatabase(.hypothesis/examples)` |
| `CI=1 GITHUB_ACTIONS=1` | **`None`** |

For its entire existence the gate stored counterexamples locally and none in CI, which is
the only place it runs. Nothing was saved, the cache restored nothing, the artifact had
nothing to upload, and every run reported green.

Found by forcing a Deep property red on a throwaway branch: the test failed in CI exactly
as intended and the job still reported `database absent`, contradicting the same failure
locally, which writes 13 example files. Rather than guess, the workflow was instrumented
to print the resolved path. It printed `None`.

**Proved closed rather than argued closed.** The same deliberate failure on top of the fix,
run `33592040244`: `configured database: DirectoryBasedExampleDatabase(PosixPath(...))`,
and artifact `hypothesis-examples-py314-33592040244`, **1288 bytes**. The middle tier of
the persistence architecture has now been observed working, for the first time.

That corrects **QG-1**, which attributed the empty artifact to `upload-artifact` skipping
hidden files. The flag it added is harmless and probably right, but there was never a
database to skip. QG-3 had already recorded that the cited evidence could not distinguish
the two explanations; it was the other one.

`tests/test_quality_gate_profile.py` now asserts the profile in a subprocess under CI
environment variables, in the ordinary suite on every push, because the defect only exists
under those variables.

### What this release is missing

**It was never independently reviewed**, by explicit direction. The design, its audit, the
contracts, the implementation and the mutation battery are one perspective. Six things
passed for the wrong reason before being caught (spec §9.1, §9.2), EP-1 is the seventh,
and the two defects that actually shipped in the implementation were caught by tests
written in earlier sessions - not by this release's own contracts.

### Exact next step

**Nothing is broken and nothing is half-finished.** The next step is new work, and it is
now chosen from measurement rather than from a feature list:
`docs/project-context/feature-gap-map.md`, reproducible with `python tools/gap_map.py`.

Eighteen real exercises written the way an engineer writes them, run line by line against
0.10.1: **4 run end to end.** Ranked by exercises that go *fully* green against pieces of
work, hand-verified:

1. **scalar equation systems** — one piece, **4/18 → 7/18**. The only gap that pays on its
   own, and how statics is actually written: `ΣF = 0`, `ΣM_A = 0`.
2. **indefinite integral**, shipped alongside — two pieces, **8/18**, and the elastic curve
   becomes derivable instead of quoted. Alone it unblocks nothing: the only exercise
   needing it also needs scalar systems.
3. **comparisons, then `check()`** — 6/18, but `check` is what turns a memoria into an
   auditable verification, which is worth more than the count says. Comparisons exist in
   the grammar only inside `piecewise(...)`; a bare `Compare` is rejected, and that one
   restriction gates `check`, `assume` and inequalities alike.
4. `assume()` and inequality solving on that groundwork — 8/18 for that branch, four
   pieces. Then multi-solution solve, evaluated summation, and the structural and memoria
   blocks.

The map's first version said comparisons were the best first move. That was an artifact of
clustering each line by its first error, and it is corrected in place; the document records
the mistake rather than hiding it.

`integral(...)` becomes **`integrate(...)`** in that work, with `integral` kept as an
alias — the user's decision, on the principle of not inventing names for operations that
already have recognised ones.

Two things are owed rather than open:

- **Neither 0.10.0 nor 0.10.1 was independently reviewed**, by explicit direction. The
  design, its audit, the contracts, the implementation and the mutation battery are one
  perspective. Spec §9.1 and §9.2 record what that cost, in evidence rather than in
  principle.
- **Seven families remain uncovered by the Quality Gate** and are listed in
  `docs/quality-gate.md` with the warning that green does not mean covered: roots
  separated by less than 0.05, Piecewise with more than two branches, nested Piecewise,
  Piecewise combined with matrices, intersections between two Piecewise responses,
  domains whose symbolic bounds cannot be resolved, and renderer/plotting beyond the
  presentation findings. Covering them is a project, not a cleanup.

Also deferred, and not defects: `no_vertical_scroll()` Colab ergonomics, multiline
ordinary function-call parsing, generalized structural eigenproblems.

## How to resume in a new conversation

Read this file first. `main` is at **EngCalc 0.10.1**, CI green on Python 3.10-3.14, and
verified installable and working in Google Colab from the documented `git+https` path.
1086 tests green: 912 product, 154 Fast Gate on every push, the presentation contracts and
the Quality Gate profile guards, plus 18 Deep properties weekly or on demand.

**No defect is open.** P-1, P-2, P-3, EP-1, QG-1, QG-2 and QG-3 are all closed, and QG-3's
resolution corrected QG-1's diagnosis rather than confirming it. What remains is new work
from the backlog, seven families the gate does not cover and says so, and three deferred
ergonomics items.

Read `docs/quality-gate.md` for how to operate the gate: the isolated configuration that
historical sensitivity runs require, the qualification-SHA rule and the consequence that
its run identifiers can only be recorded after a merge, and the requirement that the
Hypothesis profile set every setting the environment could otherwise decide.

Two rules that have each paid for themselves repeatedly: never merge without explicit user
approval, and never let whoever built something be the one to certify it. The second was
suspended for 0.10.0 and 0.10.1 by explicit direction. What that cost is documented rather
than argued. Across those two releases **nine separate things were green or correct for
the wrong reason**, and not one was found by reading: they were found by executing, by
mutating the finished implementation, by tests written in earlier sessions, by running a
real memoria after a merge, and once by forcing a passing gate to fail on purpose to see
whether it could even record the failure. It could not.

Never invoke Codex / Codex Cloud without explicit authorization.
