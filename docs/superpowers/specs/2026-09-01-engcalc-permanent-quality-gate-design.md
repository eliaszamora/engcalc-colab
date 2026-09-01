# EngCalc Permanent Quality Gate — Design

## Status

**APPROVED.** Independently audited; findings D-1, D-2 and D-3 resolved and folded into
this text. This document is the authoritative design; the amendments produced during
review are integrated inline rather than appended.

Basis:

- `main@c3f4b14ccbca2c3ed926c8973648bd5c6168ce58`, merge of PR #36;
- the completed temporary property-based audit of `characteristics/`;
- measured execution data and temporary harnesses supplied after that audit;
- the existing permanent CI contract on Python 3.10–3.14.

The audit classified `characteristics/` as **CLEAN within the audited scope**, over 908
directed and generated mathematical cases:

| Evidence level | Cases |
|---|---|
| A — constructive oracle | 811 |
| B — internal invariant | 24 |
| C — metamorphic | 64 |
| D — shared external oracle | 9 |

No new mathematical defect was demonstrated. The same audit demonstrated three
preexisting presentation defects, P-1, P-2 and P-3, which are recorded inputs for the
later Engineering Presentation work and are **not corrected by this project**.

---

## 1. Goal

Build a permanent, auditable Quality Gate for EngCalc's high-risk mathematical
characteristic subsystem so that:

1. historically fragile families are exercised continuously;
2. the ordinary PR/push loop stays fast enough to remain enabled;
3. broader property-based exploration runs separately from ordinary CI;
4. different forms of test evidence are not treated as equivalent;
5. every newly discovered counterexample becomes permanent deterministic evidence;
6. no shared SymPy oracle can be used to claim solver completeness;
7. future feature work can build on a substantially stronger correctness floor.

The Quality Gate is QA infrastructure. It must not change EngCalc production semantics.

---

## 2. Baseline constraints

- package version remains `0.9.2`;
- Python support remains 3.10–3.14;
- no SciPy dependency;
- exact-first characteristic analysis unchanged;
- deterministic numerical fallback unchanged;
- dimensional-zero semantics unchanged;
- `envelope(...)` remains sampled;
- positive structural moment remains plotted downward;
- no presentation, parser, renderer, plotting or matrix behavior changes;
- no Exact Envelopes work;
- Hypothesis is a development/QA dependency only, never a runtime dependency;
- no merge without explicit user approval.

---

## 3. Evidence hierarchy

Results must classify evidence explicitly. This hierarchy exists because the audit
demonstrated that counting tests without ranking their strength overstates protection.

### Level A — constructive oracle

The correct answer is known independently before EngCalc executes:

- `f(x) = ∏(x − rᵢ)` with selected roots;
- expanded forms generated from those same known roots;
- `g = f + h` where the roots of `h` are chosen in advance;
- parabolas whose vertex is specified in advance;
- Piecewise responses constructed to cross zero at a selected breakpoint;
- parameterized functions whose real-root count is analytically known.

**Level A is authoritative.** Whenever a family can reasonably be expressed as Level A,
it must not be replaced by a weaker oracle.

### Level B — internal invariant

Verifies a necessary internal consistency condition without knowing the complete
expected answer, e.g. *no attained `global_max` may be numerically below another
attained value*. Useful defensive evidence; **not** proof that the complete result set
is correct.

### Level C — metamorphic

Two related executions must preserve a mathematical relation, e.g. `extrema(-f)` swaps
max/min roles, or metre and millimetre formulations locate the same physical root.
Detects asymmetries; **may remain green while both executions share the same systematic
omission.** The audit demonstrated this concretely: an invariance property would not
have caught N-1, because roots were lost identically on both sides of the contrast.

### Level D — shared external oracle

The expected answer is obtained using the same solver machinery EngCalc uses, e.g.
calling `sp.solveset` to decide which roots EngCalc should find.

**Prohibited as authoritative permanent evidence for solver completeness.** May exist
temporarily during investigation; may not satisfy a coverage requirement.

---

## 4. Topology

### 4.1 Fast Gate — every PR and push

Purpose: regression protection, deterministic Level A coverage, supported-Python
compatibility, low latency. Runs on Python 3.10, 3.11, 3.12, 3.13 and 3.14.

Contains the existing suite, existing historical regressions in `tests/`, and a curated
deterministic Quality Gate corpus. No random exploration. No Level D oracle.

Default `pytest -q` must collect `tests/` and `quality_tests/fast/`, and must **not**
collect `quality_tests/deep/`.

### 4.2 Deep Property Gate — scheduled exploration

Purpose: generate new examples, bias toward boundaries, shrink failures, explore beyond
the fixed corpus.

Scheduled weekly on Python 3.14 with a non-derandomized profile, the example database
enabled, and per-property `max_examples`. The database is a best-effort accelerator,
never an oracle.

### 4.3 Release qualification

Before a functional release: run the Deep Gate on Python 3.10 **and** 3.14 at the exact
release-candidate SHA; both GREEN; no unresolved counterexample.

The two boundary versions are used instead of multiplying the expensive exploratory
search across all five. Compatibility across all five stays enforced by the Fast Gate.

---

## 5. Execution-budget model

Budgeted **per property**, not per broad family. The audit measured, at Python 3.14.3
with Hypothesis 6.167.1 and 30 examples per property:

| Property | s/example |
|---|---:|
| `piecewise_continuous_root_at_breakpoint` | 1.89 |
| `piecewise_jump_is_never_a_root` | 1.13 |
| `extrema_sign_flip_swaps_roles` | 1.01 |
| `roots_expanded_polynomial` | 0.71 |
| `extrema_parabola_known_vertex` | 0.55 |
| `intersections_tangency` | 0.44 |
| `roots_factored_polynomial` | 0.44 |
| `roots_repeated_root` | 0.43 |
| `intersections_built_from_known_difference` | 0.40 |
| `roots_registered_parameter_no_real_roots` | 0.40 |
| `roots_registered_parameter_with_real_roots` | 0.40 |
| `roots_with_units_shear_zero` | 0.40 |
| `units_metre_millimetre_equivalence` | 0.34 |
| `piecewise_breakpoint_equals_lower_bound` | 0.20 |
| `domain_root_on_boundary_is_included` | 0.18 |
| `domain_root_outside_is_excluded` | 0.17 |
| `piecewise_breakpoint_equals_upper_bound` | 0.17 |

These are **baseline measurements and relative ranking**, not portable timings.

Piecewise must not receive one family-wide example count: measured cost varies by about
a factor of eleven between its cheapest and most expensive properties.

### 5.1 Fast Gate budget — calibration precedes sizing

The temporary 398-case deterministic corpus took ~131 s on the auditor's machine. It
must **not** be copied wholesale into every matrix job.

Implementation must not begin by materializing a target such as 160, 180 or 398 cases.
Instead:

1. construct a representative benchmark slice covering every required Level A partition;
2. include samples from both cheap and expensive partitions;
3. run that slice on GitHub Actions, at minimum on Python 3.10 and 3.14;
4. record per-partition and total elapsed time;
5. only then select the permanent deterministic corpus;
6. expand or reduce redundant examples while preserving every mandatory partition.

Auditor-machine timings are useful for ranking and are **not** accepted as GitHub
Actions measurements.

Performance contract after calibration:

- every required structural partition remains covered;
- median added Quality Gate time per Python matrix job: **≤60 s**;
- hard added-time ceiling per matrix job: **90 s**;
- no required partition may be silently removed solely to meet timing.

If required coverage cannot fit under the hard ceiling, implementation **stops** and the
CI topology is revisited.

CI performance evidence must distinguish user-visible wall-clock latency, time added to
each matrix job, and aggregate runner-minutes. The five jobs execute independently;
multiplying one duration by five describes compute cost, not PR latency.

### 5.2 Deep Gate initial budget

| Property | Initial examples |
|---|---:|
| `piecewise_continuous_root_at_breakpoint` | 40 |
| `piecewise_jump_is_never_a_root` | 40 |
| `extrema_sign_flip_swaps_roles` | 40 |
| `roots_expanded_polynomial` | 80 |
| `extrema_parabola_known_vertex` | 60 |
| `extrema_parabola_known_minimum` | 60 |
| `intersections_tangency` | 60 |
| `roots_factored_polynomial` | 80 |
| `roots_repeated_root` | 60 |
| `intersections_built_from_known_difference` | 80 |
| `roots_registered_parameter_no_real_roots` | 80 |
| `roots_registered_parameter_with_real_roots` | 80 |
| `roots_with_units_shear_zero` | 60 |
| `units_metre_millimetre_equivalence` | 60 |
| `piecewise_breakpoint_equals_lower_bound` | 60 |
| `domain_root_on_boundary_is_included` | 80 |
| `domain_root_outside_is_excluded` | 80 |
| `piecewise_breakpoint_equals_upper_bound` | 60 |

Using audit timings this is ≈529 s on the auditor's machine before the replacement H4
property. These are **initial tuning values**, not permanent API.

After the first Actions benchmark: target ≤10 min on one Python version, hard ceiling
12 min. Counts may be redistributed per property. The historically critical
`roots_expanded_polynomial` family must not be starved merely because it costs more than
other roots properties. No property may drop below the 30-example audit baseline solely
to meet timing without explicit design review.

---

## 6. Fast deterministic corpus

The temporary `sweep*.py` scripts are input material, not permanent architecture. The
permanent corpus must remove runtime random generation, materialize selected cases
explicitly, keep the audit seeds only as provenance, remove audit counters and
print-based collection, use pytest assertions and public EngCalc APIs, and classify
complementary Level B/C cases explicitly.

### 6.1 Required partitions

Selection is by equivalence partition and historical risk, not by case count. No fixed
initial total is prescribed; the corpus is derived after the §5.1 calibration.

**Roots**

- factored degree 1, 2 and 3;
- positive and negative leading coefficients;
- expanded decimal polynomial family (N-1);
- repeated / even-multiplicity root;
- registered parameter with zero real roots (A-1);
- registered parameter with two known real roots;
- degree 4 and 5 with roots selected in advance;
- scales from `1e-9` to `1e9`;
- dimensional response and dimensional bounds;
- root exactly at each domain boundary;
- root outside the domain.

For N-1 the original 117-case sweep is explicitly redundant as a permanent push gate. A
smaller representative subset must cover both leading-coefficient signs, one and
multiple in-domain roots, ordinary decimal engineering coefficients, roots near each
side of the domain, the historically failing reproductions, and representative scale
variation. The exact number is chosen only after calibration.

**Intersections**

- one known crossover;
- multiple known crossovers;
- tangency;
- positive response shift;
- negative response shift;
- ordinary decimal coefficients.

Expected crossovers must be built from chosen factors, never computed afterwards with
SymPy.

**Extrema**

- known interior maximum — Level A, inherited from the audit;
- known interior minimum — **new** Level A coverage added by this design;
- extrema at domain boundaries — **new** Level A coverage added by this design;
- sign-flip max/min correspondence — Level C complementary.

For boundary extrema use a monotonic response, e.g. `f(x) = k·x + c` on `[0, L]`:
`k > 0` gives `global_min` at `x = 0` and `global_max` at `x = L`; `k < 0` inverts both.
This is preferable to a polynomial carrying unnecessary interior critical points.

The interior-minimum and boundary families must not be described as audit-proven
coverage until their permanent Level A tests are implemented and qualified.

**Piecewise**

- all four operators `<`, `<=`, `>`, `>=`;
- continuous root at breakpoint;
- jump with no root;
- breakpoint at lower domain bound;
- breakpoint at upper domain bound;
- attained versus non-attained extremum behavior;
- interval-role behavior around a jump.

**Units / domain**

- metre/millimetre equivalence (Level C);
- dimensional-zero behavior;
- registered dimensional parameters.

**Matrix scalar integration**

- indexed scalar `K(x)[1,1]` accepted as a characteristic response.

---

## 7. H2 classification

Temporary `sweep2.py` H2 is Level B: it verifies only that an attained global extremum
does not contradict another attained value.

**Preferred path.** Promote the breakpoint/boundary operator matrix to Level A by
encoding explicit expected topology: selected branch at the domain edge, expected
`side`, expected attained/non-attained status, expected global role and expected
characteristic value. The expectation must be derived from EngCalc's public Piecewise
ownership contract, not from current implementation output.

**Fallback path.** Retain H2 as clearly labelled Level B complementary evidence, in
which case it satisfies no Level A coverage requirement.

---

## 8. H4 replacement — mandatory Level A reconstruction

Temporary H4 is Level D because its second expected root comes from `sp.solveset`, which
shares solver machinery with EngCalc. It must not enter the permanent gate unchanged.

### Rejected construction

An earlier proposal built the difficult factor around a selected root `r`:

```text
Q(x) = x^5 + b*x - (r^5 + b*r)
```

Mathematically valid, but **rejected**: because `r` is algebraically embedded in the
coefficients, `(x − r)` is an extractable factor and SymPy exposes `r` symbolically.
Measured evidence:

```text
sp.solve( (x-a)*(x^5 + b*x - (r^5 + b*r)) , x )  ->  6 candidates, including a AND r
sp.solve( (x-a)*(x^5 + b*x + c) , x )            ->  [a] only
```

Under the historical over-broad rule `is_polynomial(variable) => complete=True` the
fallback is suppressed without losing `r`, so the guard stays GREEN and fails the
sensitivity requirement below.

**Principle, worth stating generally:** a second root cannot be simultaneously known a
priori by algebraic construction and symbolically undiscoverable. The construction that
supplies the oracle is the one SymPy uses to find it.

### Required construction

Preserve the original dangerous structure:

```text
Q(x) = x^5 + b*x + c        with registered b > 0
f(x) = (x - a) * Q(x)
```

For every real `x`, `Q'(x) = 5·x⁴ + b > 0`, so `Q` is strictly increasing; with
`Q → ∓∞` at `∓∞` it has **exactly one real root**. The root *count* is therefore
established analytically, without asking SymPy to solve `Q`.

### Independent numerical oracle

The unique real root is located in the test by scalar bisection in ordinary
floating-point arithmetic. The oracle must not call `sp.solve`, `sp.solveset`, EngCalc's
fallback solver or EngCalc characteristic helpers, and must not use the implementation
under test to choose the expected root.

A valid implementation expands a bracket `[lo, hi]` until `Q(lo)` and `Q(hi)` have
opposite signs, relies on strict monotonicity for uniqueness, and bisects to tolerance.

For distinct `a` and the unique root `r_Q`, both inside the domain, the expected complete
real-root set is `[a, r_Q]`; `a` retains exact provenance when discovered symbolically
and `r_Q` may carry numerical provenance.

### Parameter controls

More than one `(a, b, c)` configuration with `b > 0`, positive and negative `c`,
positive and negative difficult roots, `a` on both sides of the difficult root,
`a ≠ r_Q`, and both roots inside the domain.

Sensitivity was verified across the mandated space: `sp.solve` returns `[a]` only for
positive, negative, decimal, registered-symbolic and mixed configurations.

### Sensitivity requirement

Accepted only if it demonstrates:

```text
historical over-broad completeness rule  ->  RED
corrected implementation                 ->  GREEN
```

Verified feasible before implementation: simulating the over-broad rule in memory makes
the replacement fail 4/4 configurations, and reverting restores GREEN.

---

## 9. Deep property suite

Starts from `test_constructive.py`, but the audit harness must not be copied verbatim.
Remove `AUDIT_COUNTS`, `AUDIT_EXERCISED`, `AUDIT_RUNS`, `atexit` reporting and any
scratchpad-only instrumentation. Preserve constructive generators, known-root
construction, boundary-biased strategies and explicit engineering ranges.

### 9.1 Filtering

The audit generated seven examples that returned before executing EngCalc because roots
were too close. Permanent tests should prefer Hypothesis-native strategy construction or
`assume()` over manual early returns, and must not report nominal `max_examples` as
engine executions when guards discard generated examples.

### 9.2 Profiles

`quality_deep`: exploration enabled, `derandomize=False` explicitly, `deadline=None`,
example database enabled, per-property `max_examples`. A cheaper local developer profile
may exist. The Fast Gate does not depend on Hypothesis generation.

---

## 10. Dependency and persistence

Hypothesis is added only to the development dependency set, initially pinned to
`hypothesis==6.167.1`, the audited version. Updates are deliberate QA dependency changes
accompanied by a Deep Gate qualification.

The example database is a **non-authoritative cache**. Deep CI restores it when
available, runs the suite, and preserves the result — as a cache for the next
exploration and as an artifact for inspection of this run.

Persistence must survive a failing job. GitHub caches are immutable and the combined
`actions/cache` action saves in a post-step that does not run when the job fails, so the
workflow must use `actions/cache/restore` → tests → `actions/cache/save` with
`if: always()`, and a rotating key including `github.run_id` and `github.run_attempt`
plus `restore-keys` for recovery. A static key would freeze the database after the first
successful run, and a post-step save would drop exactly the runs that found something.

Three levels of persistence, in increasing authority:

1. Hypothesis cache — exploratory convenience, non-authoritative;
2. workflow artifact and logs — evidence of one run;
3. committed regression test — permanent authoritative evidence.

Loss of the database must never remove a known defect from the gate's protection.

---

## 11. Counterexample promotion protocol

1. **Capture** — minimized example, property name, exact EngCalc input, actual result,
   expected contract, Python version, Hypothesis version, SHA, reproduction data.
2. **Reproduce independently**, not relying solely on the Hypothesis database. An
   unreproduced hypothesis is not a demonstrated defect.
3. **Materialize a permanent regression** in source control before production is
   corrected: a parametrized pytest case, or an explicit `@example(...)` where that is
   clearest. The source-controlled regression is authoritative.
4. **Prove RED** against the defective state.
5. **Correct production** only after persistent RED exists.
6. **Prove GREEN**: focused regression, affected family, Fast Gate, complete 3.10–3.14
   CI, and Deep Gate qualification where the defect concerns completeness or fallback.

A fix without a source-controlled regression is not release-qualified.

---

## 12. Anti-tautology / sensitivity contract

Because the Quality Gate is new infrastructure, ordinary RED→GREEN cannot be shown by
first making the current product fail. New guards must instead demonstrate
**sensitivity** against historical bad states:

- N-1 expanded decimal family against a pre-N-1-fix state;
- A-1 complex candidate family against the released defective state;
- A-2 open-edge Piecewise family against the released defective state;
- H4-A must preserve a symbolically incomplete polynomial factor whose unique second
  real root is established independently by monotonicity plus test-local bisection, and
  must be RED against the first over-broad A-1 completeness implementation and GREEN
  against the corrected implementation.

Expected evidence: `known bad state -> RED`, `current state -> GREEN`.

**An import, collection or setup error does not count as RED evidence.** Sensitivity is
valid only if the test is collected, executes the target assertion, and fails because of
the mathematical behavior the guard exists to detect:

```text
FAILED ... assert [] == approx([0.313, 2.619])   -> valid RED
ModuleNotFoundError                              -> invalid evidence
collection error                                 -> invalid evidence
```

This contract exists because an audit of the implementation plan found an invocation
that would have produced exactly that false RED.

Sensitivity evidence may live in temporary validation infrastructure and need not remain
in permanent CI. For families with no known historical defect, Level A oracle
independence plus review is sufficient.

---

## 13. Repository structure

```text
tests/                                   existing regression and product tests
quality_tests/
    helpers.py
    fast/
        test_roots_constructive.py
        test_intersections_constructive.py
        test_extrema_constructive.py
        test_piecewise_constructive.py
        test_units_domain.py
        test_matrix_scalar.py
        test_historical_guards.py
    deep/
        conftest.py
        strategies.py
        test_roots_properties.py
        test_intersections_properties.py
        test_extrema_properties.py
        test_piecewise_properties.py
        test_units_properties.py
```

`pytest -q` runs `tests/` and `quality_tests/fast/`, never `quality_tests/deep/`, which
is explicit: `pytest -q quality_tests/deep`.

`pythonpath` must include both `src` and the repository root, so that
`quality_tests.helpers` resolves under `pytest` as well as `python -m pytest`. Relying on
`python -m pytest` alone is fragile and breaks historical-sensitivity runs executed from
another working directory.

Registered markers make evidence intent visible: `evidence_a`, `evidence_b`,
`evidence_c`, `quality_deep`. **No permanent Level D completeness test is allowed.**

---

## 14. CI workflows

`.github/workflows/ci.yml` remains the permanent PR/push gate on Python 3.10–3.14 and
gains the Fast Quality Gate through ordinary pytest collection. No Deep Gate runs there.

`.github/workflows/quality-gate-deep.yml` is added with `schedule` and
`workflow_dispatch` triggers. Scheduled mode explores on Python 3.14; qualification mode
runs Python 3.10 and 3.14 at an exact SHA. The workflow reports Python version, package
SHA, Hypothesis version, per-property timing, total timing, and failures with minimized
examples, and preserves the example database best-effort including on failure.

---

## 15. Known uncovered families

The gate must not claim protection for families the audit did not explore:

- roots separated by less than `0.05`;
- coefficients with substantially more than three decimal places;
- Piecewise with more than two branches;
- nested Piecewise;
- Piecewise combined with matrices;
- intersections between two Piecewise responses;
- domains whose symbolic bounds cannot be numerically resolved;
- renderer and plotting behavior beyond the demonstrated presentation findings.

These are **known coverage gaps, not current defects.** Implementation of this gate must
stay strictly inside the audited families; expanding toward these gaps is separate work
with its own prior audit, because a defect found there would halt the gate for a reason
that is not the gate's.

Exact Envelopes must not assume these gaps are covered merely because this gate is GREEN.

---

## 16. Presentation findings

Open, and outside this implementation:

- **P-1 HIGH** — automatic default rendering can collapse a nonzero physical quantity to `0.00`;
- **P-2 HIGH** — substitution display can show a nonzero factor as `0.00`, breaking derivation traceability;
- **P-3 MEDIUM** — a derived quantity can retain a dimensionally correct but engineering-unreadable compound unit.

Do not add permanently failing or indefinite `xfail` tests for these as part of the
mathematical gate. They become formal RED contracts when Engineering Presentation begins.

---

## 17. Golden engineering worksheets

Intentionally **not** part of this implementation. This gate protects mathematical
characteristic behavior; golden worksheets protect end-to-end presentation. Combining
both now would mix two correctness surfaces and make this phase harder to qualify.

---

## 18. Definition of Done

**Architecture**

1. Fast and Deep gates physically and operationally separated.
2. Default `pytest -q` does not run the Deep Gate.
3. Hypothesis is a dev-only dependency.
4. No production source behavior changes.
5. No package version bump for QA infrastructure.

**Evidence**

6. Every required mathematical family has Level A permanent coverage where technically reasonable.
7. Level B/C tests explicitly classified as complementary.
8. No Level D shared-oracle test counted as completeness evidence.
9. H4 replaced by a Level A family whose difficult root count is proved analytically and whose numerical location comes from an independent test-local bisection oracle.
10. The H4 oracle does not call SymPy symbolic solving or EngCalc solving machinery.
11. The H4 replacement is RED against the historical over-broad completeness implementation and GREEN against the corrected one.
12. H2 either promoted to Level A or explicitly Level B and non-authoritative.

**Sensitivity**

13. Historical defect guards have RED evidence against appropriate known-bad states where practical, and every RED is an assertion failure rather than an import or collection error.

**Performance**

14. A representative slice was benchmarked on GitHub Actions **before** the permanent corpus was dimensioned.
15. Every mandatory structural partition remains covered.
16. Median added time per matrix job ≤60 s.
17. No matrix job exceeds the 90 s hard ceiling without explicit design review.
18. Deep property counts calibrated per property, not per broad family.
19. Deep Gate on Python 3.14 within ≤10 min target and ≤12 min ceiling, or the design is revisited before merge.

**CI**

20. Permanent PR/push CI GREEN on Python 3.10–3.14.
21. Scheduled/manual Deep Gate exists and is GREEN.
22. Release qualification on Python 3.10 and 3.14 demonstrated.
23. Deep workflow identifies exact SHA and QA dependency version.

**Counterexamples**

24. The promotion protocol is documented.
25. At least one exercise demonstrates a Deep Gate failure becoming a deterministic persistent regression.
26. Hypothesis database loss cannot remove authoritative regression coverage.

**Hygiene**

27. Temporary audit counters and scratchpad reporting absent.
28. Temporary harness scripts not copied blindly into production tests.
29. `git diff --check` passes.
30. Complete source suite passes.
31. No temporary audit artifacts in the tree.
32. `CURRENT.md` records the finished gate, authoritative CI runs and the exact next action.

---

## 19. Verification contract

Per slice: select family and evidence level; derive the independent oracle; demonstrate
historical sensitivity where a known-bad state exists; add the permanent test; run
focused tests; run the complete source suite; benchmark the slice; only then continue.

Final qualification requires `compileall`, the complete default suite, permanent CI on
3.10–3.14, Deep Gate on 3.14, release-style Deep Gate on 3.10 and 3.14, execution-budget
evidence, H2 classification evidence, H4 Level A replacement evidence, historical
sensitivity evidence, and tree hygiene.

A wheel rebuild is not required solely because QA files and workflows changed and no
packaged source, metadata or runtime dependency changed.

---

## 20. Non-goals

This gate does not fix P-1/P-2/P-3, redesign units or numerical presentation, implement
significant figures, create golden worksheets, add scalar equation systems, implement
Exact Envelopes, add named cases, add verification APIs, expand the uncovered families,
refactor `characteristics/` production code to ease testing, introduce a runtime
dependency, or change public EngCalc syntax.

---

## 21. Role separation

The person or agent implementing the Quality Gate must not be the sole authority
certifying that the completed gate is sufficient. Independent audit precedes any request
for merge approval.

This rule is retained because it demonstrably worked in both directions during the work
that produced this design: an implementer's plausible correction was caught by review,
and a reviewer's plan was corrected by audit before any code existed.
