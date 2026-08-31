# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.1 is still the canonical released baseline. The approved 0.9.2 Audit Remediation & Reliability plan is active on `feature/v0.9.2-audit-reliability`. Tasks 1–13 are COMPLETE; Task 14 is NEXT._

## Canonical state

- Repository: `eliaszamora/engcalc-colab`.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`** — re-verified unchanged after Task 13.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- Runtime/package version: **0.9.1**. Version bump occurs only in Task 14.
- `requires-python = ">=3.10"`.
- Runtime dependency includes **`ipython>=8.18`**.
- Permanent CI: `.github/workflows/ci.yml`, Python **3.10–3.14**.
- Approved spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-design.md`.
- Approved plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-implementation.md`.
- Persistent audit regressions: `tests/test_v092_audit_regressions.py`.
- Persistent risk probes: `tests/test_v092_risk_probes.py`.
- Never invoke Codex / Codex Cloud without explicit user authorization.
- Never merge the 0.9.2 release PR without explicit user approval.

## Task status

1. **COMPLETE** — independent C-1/H-1 natural RED.
2. **COMPLETE** — closed real finite SymPy evaluation.
3. **COMPLETE** — non-silent roots + exact/numeric merge.
4. **COMPLETE** — intersections share zero-set semantics.
5. **COMPLETE** — explicit-real engineering symbols and identity-safe reconstruction.
6. **COMPLETE** — centralized direct unit-literal bounds and dimensional-zero preservation.
7. **COMPLETE** — Piecewise boundary selection/topology normalization.
8. **COMPLETE** — explicit renderer/Piecewise diagnostics.
9. **COMPLETE** — plot warning, exact rational coordinates and negative-zero presentation.
10. **COMPLETE** — residual/realness/simplify audit risks investigated; all **not reproduced; no product change**.
11. **COMPLETE** — permanent Python 3.10–3.14 CI + declared IPython dependency.
12. **COMPLETE** — behavior-preserving `characteristics.py` decomposition behind stable public imports.
13. **COMPLETE** — natural acceptance, README reliability documentation, v0.9.3 envelope deferral naming, complete regression + hygiene.
14. **NEXT** — release EngCalc **0.9.2**, validate real wheel/source-free installation, open release PR, then **STOP before merge**.

## Key product/evidence commits

- Task 5: `2b6be7d22817cee3c1267495e58635d3bb06fc9d` — `fix: make engineering symbols explicitly real`.
- Task 6: `c115bc9d810e8552a8d5138c88bfffcb3f55cb76` — `fix: centralize direct unit literal bounds`.
- Task 7: `d2ae961bf3be34c2b52b1afbc54b4963f7ceb156` — `fix: normalize Piecewise extrema topology`.
- Task 8: `833009fedcf257c18e84e8ea0992e4f613a5d52d` — `fix: make characteristic diagnostics explicit`.
- Task 9: `5363bfc54a5f4d27a2f1b79f309e6a383eb17a2e` — `fix: polish exact characteristic presentation`.
- Task 10 evidence: `87ee04cf13fd86993245a9f62f1e55c64a6d2f8b` — `test: investigate characteristic audit risks`.
- Task 11 permanent CI/product: `c8c2dd9be63df5c3b7925bbfafe32d607c2372a7`.
- Task 12 product: `cee4b39e19d2f6f2c49595d8a46efcdd6f1d58ce` — `refactor: split characteristic solver by responsibility`.
- Task 12 cleanup: `6ccf182cef34fc3874793e2b8c5bf0816b13a92d`.
- Task 13 acceptance/docs: **`cce0bd768872a8bc31910435f9b29936e348c027`** — `docs: complete 0.9.2 reliability acceptance`.
- Task 13 cleanup: `1265e7ceff9325485e9cc59894020f2b46d9d52b`, `037f6e6416d446a9e8629557fad240776f24196d`, `52cea79f4ee408128b841445311440e7b84ea64a`.

## Reliability contract after Task 13

- Exact-first remains authoritative; deterministic numeric fallback supplements incomplete exact discovery.
- Exact provenance wins when exact and numeric candidates deduplicate to one physical point.
- Plausible candidate evaluation failure never silently becomes an empty solution set.
- `roots()` and `intersections()` share continuous zero-set discovery/validation/fallback/merge semantics.
- Engine-created engineering symbols are explicitly real and identity-sensitive reconstruction is protected.
- Supported direct unit literals work consistently in roots/intersections/extrema/plot/table domains.
- Dimensional zero bounds such as `0*m` are preserved before symbolic simplification erases units.
- Piecewise boundaries use the actually selected governing branch; continuous redundant side records collapse to `at`, while discontinuities retain meaningful sides.
- Ordinary plots retain 201 drawing samples while exact characteristic metadata/coordinates remain authoritative.
- Positive structural moment remains plotted downward.
- `envelope(...)` remains sampled in 0.9.2; exact crossovers/governing intervals are deferred to **0.9.3**.
- No SciPy dependency.
- IPython is declared rather than assumed from the notebook host.
- Advertised Python support is CI-validated from 3.10 through 3.14.
- Characteristic internals live under `src/engcalc_colab/characteristics/` with stable facade imports from `characteristics/__init__.py`.

## Task 10 evidence

- Run `33358168465`, job `99384201915`: **39/39 focused + 880/880 full PASS**.
- Idempotent job `99384850174`: same GREEN counts and no product diff.
- Residual, tri-state-realness and simplify-cost observations: **not reproduced; no product change**.

## Task 11 evidence

- Authoritative matrix run `33358958365`.
- Python 3.10 job `99386459903`: **881/881**.
- Python 3.11 job `99386460066`: **881/881**.
- Python 3.12 job `99386460051`: **881/881**.
- Python 3.13 job `99386460059`: **881/881**.
- Python 3.14 job `99386460063`: **881/881**.
- Idempotent run `33359297689`, commit job `99388058367`: `No Task 11 product or test patch to commit.`
- Permanent `.github/workflows/ci.yml` remains.

## Task 12 evidence

- Monolithic pre-refactor baseline: run `33359923576`, job `99389160145`, **881/881 in 200.90 s**.
- Mechanical splitter failures were isolated before persistence; no failing candidate product was committed.
- Authoritative GREEN candidate run `33361626996`: **881/881 in 206.46 s**, focused **347/347 in 80.68 s**, public imports/compile/package shape PASS.
- Product commit: `cee4b39e19d2f6f2c49595d8a46efcdd6f1d58ce`.
- Final idempotent run `33362287774`, test job `99395831492`: **881/881 in 172.04 s**, **347/347 in 67.15 s**.
- Commit job `99396580569`: `No Task 12 product or test patch to commit.`
- Task 12 temporary harness removed; permanent CI retained.

## Task 13 evidence

### Authoritative acceptance/persistence

- Run: **`33364523103`**.
- Validation job: **`99402323373`** SUCCESS.
- `compileall` PASS.
- Natural acceptance + persistent audit regressions: **12/12 PASS in 4.82 s**.
- Characteristic plot/envelope integration: **10/10 PASS in 4.41 s**.
- Complete source suite: **884/884 PASS in 177.25 s**.
- `git diff --check` PASS.
- Scope gate PASS: Task 13 changed no `src/engcalc_colab` file.
- Commit job: **`99403039773`** SUCCESS.
- Persistent commit: **`cce0bd768872a8bc31910435f9b29936e348c027`**, exactly README + `tests/test_characteristics_acceptance.py` + `tests/test_characteristics_plot_integration.py` + this context file.
- README current-version label intentionally remained **0.9.1**.
- Envelope sampled-path test renamed only from `...until_v092` to `...until_v093`; assertions unchanged.

### Idempotence

- GitHub does not recursively trigger workflows from the `GITHUB_TOKEN` product commit, so a temporary workflow-only trigger commit was used.
- Idempotent run: **`33365110693`**.
- Validation job: **`99404040721`** SUCCESS.
- Repeated **12/12 PASS in 4.99 s**.
- Repeated **10/10 PASS in 4.42 s**.
- Repeated complete suite: **884/884 PASS in 179.90 s**.
- Hygiene/scope PASS again.
- Commit job: **`99404761219`** SUCCESS.
- Context materializer: `Task 13 closure context already materialized.`
- Exact commit-gate output: **`No Task 13 acceptance/docs patch to commit.`**

### Cleanup/final audit

- Temporary files removed:
  - `.github/scripts/v092_task13_acceptance.py`
  - `.github/scripts/v092_task13_context.py`
  - `.github/workflows/v092-task13-validation.yml`
- Cleanup commits: `1265e7ceff9325485e9cc59894020f2b46d9d52b`, `037f6e6416d446a9e8629557fad240776f24196d`, `52cea79f4ee408128b841445311440e7b84ea64a`.
- Compare `cce0bd768872a8bc31910435f9b29936e348c027...52cea79f4ee408128b841445311440e7b84ea64a` shows **only those three temporary files removed**; no product/test/docs behavior changed after the authoritative Task 13 commit.
- `main` re-verified unchanged at `698696bb8854fa197851cdbb2f5e4c08ef22178b`.
- `pyproject.toml` still reports version **0.9.1**, `requires-python >=3.10`, and `ipython>=8.18`.
- Task 13 is fully closed.

## Exact next step — Task 14

Execute the approved Task 14 release sequence and do not skip gates:

1. Update only version expectations to 0.9.2 while product metadata/runtime still say 0.9.1; run focused version tests and prove every failure is an intentional version mismatch.
2. Bump all release surfaces to **0.9.2** (`pyproject.toml`, `src/engcalc_colab/__init__.py`, README current version and version assertions).
3. Run `compileall`, `git diff --check`, release-contract tests and complete source suite.
4. Build the real **0.9.2 wheel**, inspect METADATA for version/IPython, record exact filename and SHA-256.
5. Run a clean external installed-wheel smoke verifying version, IPython import, log/transcendental/quintic roots, log intersection, abs cusp extrema, direct unit bounds, continuous/discontinuous Piecewise semantics, exact 1/3 plot label and positive-moment-down convention.
6. Run the **complete installed-wheel suite source-free** with `engcalc_colab.__file__` proven to resolve under `site-packages`.
7. Repeat the complete source suite.
8. Remove only release-specific temporary infrastructure; retain permanent `.github/workflows/ci.yml`.
9. Update this file with release-contract/full/wheel/hash/smoke/source-free/repeated-source evidence and current branch SHA.
10. Open PR titled exactly **`release: EngCalc 0.9.2 audit remediation and reliability`**.
11. Verify PR base/head/mergeability and record the PR number here.
12. **STOP BEFORE MERGE and request explicit user approval.**

## Deferred/open after 0.9.2

- 0.9.3: Exact Envelopes / Governing Intervals.
- 0.9.4: Named Response Cases / Combinations.
- Separate deferred issues: `no_vertical_scroll()`, multiline ordinary non-matrix call parsing, generalized structural eigenproblems.

## How to resume in a new conversation

Read this file first. Canonical released baseline is still `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`. **Tasks 1–13 are COMPLETE and Task 14 is NEXT.** Task 13 persistent commit is `cce0bd768872a8bc31910435f9b29936e348c027`; its authoritative run was `33364523103` (12/12 + 10/10 + 884/884), idempotent run `33365110693` repeated the same counts and produced no second patch, and temporary Task 13 harness files were removed through `52cea79f4ee408128b841445311440e7b84ea64a`. Runtime/package version is still 0.9.1. Task 14 must build/validate a real 0.9.2 wheel, run source-free installed-wheel validation, open the release PR, and **STOP before merge for explicit user approval**. Never invoke Codex without explicit authorization.
