# EngCalc Quality Gate — operation

QA infrastructure protecting the mathematical characteristic subsystem. It changes
no product behavior. Design:
`docs/superpowers/specs/2026-09-01-engcalc-permanent-quality-gate-design.md`.

## Commands

```bash
python -m pytest -q                     # product suite + Fast Gate
python -m pytest -q quality_tests/fast  # Fast Gate alone
python -m pytest -q quality_tests/deep  # Deep Property Gate, explicit only
```

The Deep Gate is excluded from `testpaths`, so it never runs by accident. Both
`pytest` and `python -m pytest` collect the same topology; `pythonpath` includes the
repository root so `quality_tests.helpers` resolves either way.

## Evidence levels

Results are only as strong as the oracle behind them, so every test declares which
kind of evidence it provides.

| Level | Marker | Meaning | Authoritative |
|---|---|---|---|
| A | `evidence_a` | the correct answer is known before EngCalc runs | **yes** |
| B | `evidence_b` | an internal consistency condition holds | no |
| C | `evidence_c` | two related runs preserve a relation | no |
| D | — | expectation obtained from the solver under test | **prohibited** |

Level C can stay green while both runs share the same systematic omission: an
invariance property would not have caught the N-1 defect, because roots were lost
identically on both sides of the comparison. Level D is prohibited outright for
completeness claims, because an oracle sharing SymPy with EngCalc can fail the same
way and still report agreement.

## Partition manifest

Every partition required by design §6.1, mapped to the permanent test that covers it.

### Roots — `test_roots_constructive.py`

| Partition | Test |
|---|---|
| factored degree 1, 2, 3 | `test_roots_factored_polynomial` |
| both leading-coefficient signs | `test_roots_factored_polynomial` |
| expanded decimal (N-1) | `test_roots_expanded_decimal_polynomial` |
| repeated / even multiplicity | `test_roots_repeated_even_multiplicity` |
| registered parameter, no real roots (A-1) | `test_roots_registered_parameter_without_real_roots` |
| registered parameter, known real roots | `test_roots_registered_parameter_with_real_roots` |
| degree 4 and 5 | `test_roots_higher_degree` |
| scales `1e-9` … `1e9` | `test_roots_extreme_response_scales` |
| root on each domain bound | `test_root_exactly_on_a_domain_bound_is_included` |
| root outside the domain | `test_root_outside_the_domain_is_excluded` |
| dimensional response and bounds | `test_units_domain.py::test_unit_aware_root_location`, `::test_unit_literals_are_accepted_in_domain_bounds` |

### Intersections — `test_intersections_constructive.py`

| Partition | Test |
|---|---|
| one known crossover | `test_intersections_from_known_difference` |
| multiple known crossovers | `test_intersections_from_known_difference` |
| tangency | `test_intersections_tangency` |
| positive and negative response shift | `test_intersections_from_known_difference` |
| ordinary decimal coefficients | `test_intersections_from_known_difference` |
| no crossing where none exists | `test_parallel_responses_never_intersect` |
| coincident responses | `test_coincident_responses_report_an_interval` |

### Extrema — `test_extrema_constructive.py`

| Partition | Test | Note |
|---|---|---|
| known interior maximum | `test_known_interior_maximum` | inherited from the audit |
| known interior minimum | `test_known_interior_minimum` | **new** Level A coverage |
| extrema at domain boundaries | `test_extrema_at_domain_boundaries` | **new** Level A coverage |
| constant response | `test_constant_response_is_reported_as_an_interval` | |
| sign-flip correspondence | `test_sign_flip_swaps_global_extrema_roles` | Level C, complementary |

### Piecewise — `test_piecewise_constructive.py`

| Partition | Test |
|---|---|
| all four operators | `test_continuous_response_has_its_root_at_the_breakpoint`, `test_pure_jump_never_produces_a_root` |
| continuous root at breakpoint | `test_continuous_response_has_its_root_at_the_breakpoint` |
| jump with no root | `test_pure_jump_never_produces_a_root` |
| breakpoint at upper bound (A-2) | `test_breakpoint_on_upper_bound_topology` |
| breakpoint at lower bound | `test_breakpoint_on_lower_bound_topology` |
| attained vs non-attained extremum | both topology tests, via explicit role expectations |
| interval roles around a jump | `test_interval_roles_around_a_jump` |
| one-sided values at a discontinuity | `test_one_sided_values_are_reported_at_a_discontinuity` |
| no fabricated sides where continuous | `test_continuous_breakpoint_does_not_fabricate_one_sided_values` |
| interior behaviour survives partitioning | `test_interior_extremum_inside_a_branch_is_found`, `test_pole_inside_a_branch_does_not_create_a_root` |

The two topology tests are the Level A promotion of the audit's H2 invariant: they
assert which branch owns the edge, which side is reported and which role each
attained point carries, derived from the public Piecewise ownership contract rather
than read off current output.

### Units, domain, matrix — `test_units_domain.py`, `test_matrix_scalar.py`

| Partition | Test |
|---|---|
| metre/millimetre equivalence | `test_metre_millimetre_equivalence`, `test_extrema_roles_survive_a_unit_change` (Level C) |
| dimensional zero | `test_dimensional_zero_offset_matches_the_bare_response` |
| identically zero response | `test_identically_zero_response_is_reported_as_an_interval` |
| registered dimensional parameters | `test_unit_aware_root_location`, `test_unit_aware_extremum_of_a_simply_supported_moment` |
| unit literals in domain bounds | `test_unit_literals_are_accepted_in_domain_bounds` |
| incompatible response dimensions | `test_incompatible_response_dimensions_are_rejected` |
| indexed matrix scalar | `test_indexed_entry_is_a_valid_root_response`, `test_indexed_entry_is_a_valid_extrema_response` |
| whole matrix rejected | `test_whole_matrix_is_rejected_as_a_response` |

### Historical guards — `test_historical_guards.py`

| Defect | Test | RED against |
|---|---|---|
| H4 / over-broad completeness | `test_partial_symbolic_polynomial_keeps_numeric_fallback` | `7f4a2c5` |
| A-1 complex candidates | `test_a1_*` | `e073320` |
| A-2 open upper edge | `test_a2_left_limit_is_reported_when_breakpoint_is_the_upper_bound` | `e073320` |
| N-1 decimal polynomials | `test_roots_expanded_decimal_polynomial` | `a1dc97b` |
| N-2 roundoff residual | `test_n2_near_double_root_is_not_rejected_by_roundoff` | `e073320` |
| N-3 unit literals in response | `test_n3_*` | `e073320` |

## Measured budget

GitHub Actions, both figures from the same job back to back:

| Python | product suite | Fast Gate added |
|---|---|---|
| 3.10 | 190.1 s | **45.4 s** |
| 3.14 | 95.0 s | **22.8 s** |

Contract: ≤60 s median added per matrix job, 90 s hard ceiling. Both satisfied with
margin. Local measurement was slower than Actions, which is why the design requires
sizing to follow measurement rather than precede it.

## Historical sensitivity

A guard that cannot fail against the state it exists to catch is not a guard.
Sensitivity runs use an isolated pytest configuration, because pytest otherwise
discovers the repository `pyproject.toml` as its configfile and prepends the current
`src`, so the guard silently exercises the corrected code while appearing to test the
historical one:

```bash
ROOT="$(pwd)"; TMP="$(mktemp -d)"
git archive <sha> src | tar -x -C "$TMP"
printf '[pytest]\nmarkers =\n    evidence_a: a\n    evidence_b: b\n    evidence_c: c\n' > "$TMP/pytest.ini"
( cd "$TMP"
  PYTHONPATH="$TMP/src:$ROOT" python -m pytest \
    "$ROOT/quality_tests/fast/<file>" -k <selector> -q \
    -c "$TMP/pytest.ini" -p no:cacheprovider )
```

**An import, collection or setup error is never RED evidence.** A valid RED is a
failure produced by the behaviour the guard exists to detect — an assertion, or a
product exception where the defect was an exception.

## Counterexample promotion protocol

1. **Capture** the minimized example, property, exact input, actual result, expected
   contract, Python and Hypothesis versions and SHA.
2. **Reproduce independently**, not relying on the Hypothesis database. An
   unreproduced hypothesis is not a demonstrated defect.
3. **Materialize a permanent regression** in source control *before* production is
   corrected. The committed regression is the authoritative artefact.
4. **Prove RED** against the defective state.
5. **Correct production**, only now.
6. **Prove GREEN**: focused regression, affected family, Fast Gate, full 3.10–3.14 CI,
   and Deep qualification when the defect concerns completeness or fallback.

Persistence has three levels of authority: the Hypothesis cache is exploratory
convenience, the workflow artifact is evidence of one run, and the committed
regression is permanent. Losing the cache must never remove a known defect from the
gate's protection.

The artifact steps set `include-hidden-files: true`. `.hypothesis/` is a
dot-directory and `upload-artifact` skips hidden files by default, so without the flag
the artifact is silently empty while the workflow still reports green. Each job also
prints whether the database exists before saving it, because an absence that cannot be
seen is indistinguishable from a working one — which is how that defect survived
review in the first place.

## Qualification SHA rule

Deep qualification must run on the exact release-candidate SHA. One bounded exception
is on record: PR #37, the commit that introduced this workflow, could not satisfy it,
because `workflow_dispatch` registers only once a workflow exists on the default
branch, so reaching qualification required a temporary trigger and recording the
evidence moved the head. That exception covers that commit only. Every later
qualification is on the exact SHA, without exception.

## Known uncovered families

The gate does **not** protect these; they were never explored and remain open work:

- roots separated by less than `0.05`;
- coefficients with substantially more than three decimal places;
- Piecewise with more than two branches, and nested Piecewise;
- Piecewise combined with matrices;
- intersections between two Piecewise responses;
- domains whose symbolic bounds cannot be numerically resolved;
- renderer and plotting behaviour beyond the presentation findings below.

Future work must not assume these are covered merely because the gate is green.

## Out of scope

Presentation defects P-1, P-2 and P-3 were open and deliberately untouched by this gate.
They became formal RED contracts when Engineering Presentation began and were corrected
in **0.10.0**; their contracts live in `tests/test_engineering_presentation.py` and are
collected by the ordinary suite, not by this gate. The rule that produced them stands: no
permanently failing or indefinitely `xfail`ed test for a known defect belongs here.

The exception recorded above is the shape of the rule, not a loophole. A known defect is
either a RED contract on a branch that is being fixed, or an entry in the open-issues
list. It is never a green test that quietly tolerates it.
