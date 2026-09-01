# EngCalc Permanent Quality Gate — Implementation Plan

**Status: APPROVED.** Independently audited; findings P-1, P-2 and P-3 of the plan review
are resolved and folded into the tasks below.

Spec: `docs/superpowers/specs/2026-09-01-engcalc-permanent-quality-gate-design.md`

Execute task-by-task. Do not begin a task until the previous one has its required
evidence.

---

## Global constraints

- baseline `main@c3f4b14ccbca2c3ed926c8973648bd5c6168ce58`; package version stays `0.9.2`;
- **do not modify `src/engcalc_colab/**` at any point in this project**;
- if a permanent Level A test demonstrates a current product defect, **stop**: freeze the
  counterexample as RED and handle it as a separate corrective project;
- stay strictly inside the audited families of spec §6.1; do not stray into the §15
  uncovered families, where a defect would halt the gate for a reason that is not the
  gate's;
- Hypothesis dev-only, pinned `6.167.1`;
- P-1/P-2/P-3 presentation findings remain untouched;
- no merge without explicit user approval.

---

## Task 1 — Administrative closure and QA branch

Create the spec and this plan under `docs/superpowers/`, normalize
`docs/project-context/CURRENT.md`, branch `qa/permanent-quality-gate` from the verified
baseline. Documentation-only diff. Verify `git diff --check` and that only the three
documentation paths changed.

## Task 2 — QA dependency and test topology

`pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8",
    "hypothesis==6.167.1",
    "tomli>=2.0; python_version < '3.11'",
]

[tool.pytest.ini_options]
pythonpath = ["src", "."]
testpaths = ["tests", "quality_tests/fast"]
markers = [ ... evidence_a/b/c, quality_deep ... ]
```

`pythonpath` must contain `"."` as well as `"src"`. With only `"src"`,
`from quality_tests.helpers import ...` resolves under `python -m pytest` — which
prepends the working directory — but fails under bare `pytest`, and fails outright in
the historical-sensitivity runs of Task 4 that execute from another directory. Verified.

Append `.hypothesis/` to `.gitignore`. Hypothesis must not appear in
`[project].dependencies`.

Create `quality_tests/helpers.py` with `evaluate_cell`, `characteristic_xs`,
`assert_close_sequence` and `bisect_monotone_quintic`. The bisection helper must not
import SymPy.

**Verification.** Both invocations must collect the same topology and neither may collect
the deep suite:

```bash
pytest --collect-only -q
python -m pytest --collect-only -q
```

## Task 3 — Calibration before sizing

Temporary `quality_tests/calibration/test_calibration_slice.py` with representative
Level A examples for every required partition, explicit `parametrize`, no random values.
Temporary `.github/workflows/quality-gate-benchmark.yml` running that slice on Python
3.10 and 3.14 with `--durations=0`.

Record wall time, per-test durations, case count, runner image and SHA per version.
**Only then** select the permanent corpus size. Record the decision in `CURRENT.md`.

## Task 4 — Fast Gate roots and historical guards

`quality_tests/fast/test_roots_constructive.py` covering the spec §6.1 roots partitions.
`quality_tests/fast/test_historical_guards.py` with the H4-A replacement: monotonic
quintic `x^5 + b*x + c` with `b > 0`, root located by `bisect_monotone_quintic`, at least
four `(a, b, c)` configurations with both signs of `c` and `a` on both sides.

**Historical sensitivity.** Run focused guards against historical source trees:

```bash
ROOT="$(pwd)"; TMP="$(mktemp -d)"
git archive <historical-sha> src | tar -x -C "$TMP"
( cd "$TMP"
  PYTHONPATH="$TMP/src:$ROOT" python -m pytest \
    "$ROOT/quality_tests/fast/test_roots_constructive.py" -k <selector> -q -c /dev/null )
```

`PYTHONPATH` must list the historical `src` **first** and the repository root **second**:
the first makes `engcalc_colab` resolve to the old tree — verified to win over the
editable install — and the second makes `quality_tests` importable.

**An import, collection or setup error is not RED evidence.** A valid RED is an
assertion failure showing the mathematical defect, e.g.
`assert [] == approx([0.313, 2.619])`.

Historical SHAs: N-1 → `a1dc97b`; A-1 and A-2 → `e073320`; over-broad completeness rule
→ `7f4a2c5`.

## Task 5 — Intersections and extrema

`test_intersections_constructive.py` — Level A, explicitly covering one known crossover,
multiple known crossovers, tangency, and both positive and negative response shifts.
Expected crossovers built from chosen factors, never recomputed with SymPy.

`test_extrema_constructive.py` — Level A interior maximum; Level A interior minimum
(new); Level A extrema at domain boundaries (new) using a monotonic `f(x) = k·x + c` on
`[0, L]` with both signs of `k`; Level C sign-flip marked `evidence_c` and excluded from
Level A totals.

Boundary extrema and interior minimum were absent from the original plan and are required
by spec §6.1; both were verified satisfiable against current EngCalc before adoption.

## Task 6 — Piecewise and H2 classification

`test_piecewise_constructive.py`: continuous root at breakpoint across all four
operators; pure jump with no root; A-2 upper-bound topology asserting explicitly the
one-sided left value, its `side`, the attained branch-owned value and the absence of an
invalid `global_max`; lower-bound coincidence; interval roles around a jump with explicit
`(high, low)` pairs.

If the explicit topology tests authoritatively cover H2's operator and bound cases, H2 is
promoted; otherwise retain it separately marked `evidence_b`.

Sensitivity: the A-2 case must be RED against `e073320`.

## Task 7 — Units, domain, dimensional zero, matrix

`test_units_domain.py`: unit-aware roots; dimensional zero; metre/millimetre equivalence
marked `evidence_c`; lower-bound, upper-bound and outside-domain roots.
`test_matrix_scalar.py`: indexed scalar `K(x)[1,1]`.

## Task 8 — Recalibrate and finalize

Measure the completed Fast Gate on Actions for Python 3.10 and 3.14. Enforce ≤60 s median
added time and the 90 s hard ceiling. If over ceiling, remove only redundant values inside
already-covered partitions; never a whole required partition; never disproportionately the
historical defect coverage. If required partitions cannot fit, **stop** and revisit CI
topology.

Produce a partition manifest mapping every spec-required partition to at least one
permanent test. Delete `quality_tests/calibration/` and
`.github/workflows/quality-gate-benchmark.yml`.

## Task 9 — Deep Property Gate

`quality_tests/deep/strategies.py` with reusable strategies; prefer `assume()` and
strategy construction over manual early returns. `quality_tests/deep/conftest.py`
registering and loading a `quality_deep` profile with `deadline=None` and explicit
`derandomize=False`.

Port the seventeen audit properties plus the new interior-minimum property, with the
per-property `max_examples` of spec §5.2 and explicit evidence markers.

Verify no audit instrumentation survived:

```bash
grep -RE 'AUDIT_COUNTS|AUDIT_RUNS|AUDIT_EXERCISED|atexit' quality_tests/deep
```

Verify `pytest -q` excludes deep and `pytest -q quality_tests/deep` runs it.

## Task 10 — Deep workflow and persistence

`.github/workflows/quality-gate-deep.yml` with `schedule` (weekly, Python 3.14) and
`workflow_dispatch` (`exploration` / `qualification`; qualification on 3.10 and 3.14).

Persistence must survive a failing job, which is exactly when the interesting
counterexample exists. Use `actions/cache/restore` → tests → `actions/cache/save` with
`if: always()`, plus `upload-artifact` with `if: always()`. Rotating key:

```yaml
key: hypothesis-deep-${{ runner.os }}-py<ver>-${{ github.run_id }}-${{ github.run_attempt }}
restore-keys: |
  hypothesis-deep-${{ runner.os }}-py<ver>-
```

A static key freezes the database after the first successful run, because GitHub caches
are immutable and are written only on a primary-key miss. The combined `actions/cache`
action saves in a post-step that does not run when the job fails. `run_attempt` keeps
re-runs from warning about an existing key. Qualification keys are separated per Python
version so 3.10 and 3.14 do not contaminate each other.

`docs/quality-gate.md` documents the Fast and Deep commands, the A/B/C/D definitions, the
cadence, the qualification procedure, the counterexample promotion protocol, the known
uncovered families, and that P-1/P-2/P-3 are outside this gate.

## Task 11 — Deep Gate benchmark

Run the Deep Gate on Actions for Python 3.14; capture total and per-property duration,
Hypothesis version and SHA. Target ≤10 min, ceiling 12 min. Redistribute `max_examples`
per property if needed; keep every inherited property at or above the 30-example audit
baseline; keep investment in `roots_expanded_polynomial`. Confirm the real Actions
ranking still supports the distribution rather than relying on auditor-machine timings.

## Task 12 — Final qualification

Tree hygiene: no calibration directory, no benchmark workflow, no audit counters,
`git diff --check` clean. Production immutability:

```bash
git diff --name-only <BASE_SHA>...HEAD -- src/engcalc_colab
```

must be empty; if not, **stop**. Then `compileall`, the complete default suite, the Deep
suite locally, permanent CI GREEN on all five versions, manual Deep qualification on 3.10
and 3.14 at the exact final SHA, evidence-level counts, and the historical sensitivity
dossier. Update `CURRENT.md` and re-run CI on the final head, since the documentation
commit moves it.

## Task 13 — Independent audit

Performed by a reviewer who did not implement. Inputs: spec, plan, final PR diff, both
corpora, Actions timings, sensitivity dossier, `CURRENT.md`. Twelve questions:

1. Did every mandatory Level A partition survive calibration?
2. Was any coverage silently removed for speed?
3. Is every B/C test labelled complementary?
4. Are there zero authoritative Level D tests?
5. Is H4 truly independent of SymPy solving?
6. Does H4 still detect the historical over-broad completeness rule?
7. Does default pytest exclude Deep?
8. Does the Deep workflow actually explore rather than derandomize?
9. Can a failed Deep counterexample survive CI through the promotion protocol?
10. Did any production source change?
11. Are P-1/P-2/P-3 untouched?
12. Are the timing budgets satisfied on Actions?

Any demonstrated deficiency returns the branch to the appropriate task. Only after a
CLEAN audit may the PR be presented for explicit merge approval.
