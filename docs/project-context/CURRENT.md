# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.2 Audit Remediation & Reliability is release-validated on `feature/v0.9.2-audit-reliability`. Tasks 1–13 are complete; Task 14 release validation and cleanup are complete. The release PR is the next action and must STOP before merge for explicit user approval._

## Canonical state

- Repository: `eliaszamora/engcalc-colab`.
- Canonical `main`: **`698696bb8854fa197851cdbb2f5e4c08ef22178b`** — re-verified unchanged after definitive 0.9.2 validation/cleanup.
- Active branch: **`feature/v0.9.2-audit-reliability`**.
- Runtime/package version: **0.9.2**.
- `requires-python = ">=3.10"`.
- Runtime dependency includes **`ipython>=8.18`**.
- Permanent CI: `.github/workflows/ci.yml`, Python **3.10–3.14**, triggered by pull requests and pushes to `main`.
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
9. **COMPLETE** — characteristic plot presentation regressions.
10. **COMPLETE** — residual/realness/simplify audit risks investigated; all **not reproduced; no product change**.
11. **COMPLETE** — permanent Python 3.10–3.14 CI + declared IPython dependency.
12. **COMPLETE** — behavior-preserving `characteristics.py` decomposition behind stable public imports.
13. **COMPLETE** — natural acceptance, README reliability documentation, v0.9.3 envelope deferral naming, complete regression + hygiene.
14. **RELEASE VALIDATION + CLEANUP COMPLETE; PR NEXT** — 0.9.2 version RED, release bump, real-wheel/source-free validation, release-only warning correction, definitive wheel validation and temporary-harness cleanup are complete. Open release PR, verify permanent CI, then **STOP before merge**.

## Key product/evidence commits

- Task 5: `2b6be7d22817cee3c1267495e58635d3bb06fc9d` — `fix: make engineering symbols explicitly real`.
- Task 6: `c115bc9d810e8552a8d5138c88bfffcb3f55cb76` — `fix: centralize direct unit literal bounds`.
- Task 7: `d2ae961bf3be34c2b52b1afbc54b4963f7ceb156` — `fix: normalize Piecewise extrema topology`.
- Task 8: `833009fedcf257c18e84e8ea0992e4f613a5d52d` — `fix: make characteristic diagnostics explicit`.
- Task 9: `5363bfc54a5f4d27a2f1b79f309e6a383eb17a2e` — `fix: polish exact characteristic presentation`.
- Task 10 evidence: `87ee04cf13fd86993245a9f62f1e55c64a6d2f8b` — `test: investigate characteristic audit risks`.
- Task 11 permanent CI/product: `c8c2dd9be63df5c3b7925bbfafe32d607c2372a7`.
- Task 12 product: `cee4b39e19d2f6f2c49595d8a46efcdd6f1d58ce` — `refactor: split characteristic solver by responsibility`.
- Task 13 acceptance/docs: `cce0bd768872a8bc31910435f9b29936e348c027` — `docs: complete 0.9.2 reliability acceptance`.
- Task 14 release bump: **`2f9a13c2ac1141a67915dad745a30d33b9ed0853`** — `release: EngCalc 0.9.2`.
- Task 14 persistent font regression: **`537c848648dc406230c6d5d3bd49a483db1ed17e`** — `test: require supported plot title weight`.
- Task 14 product warning fix: **`4d067a5af1c41ecaa9c58906dcfd735ebb7a51ac`** — `fix: use supported plot title weight`.
- Definitive Task 14 validation trigger: `662041e32844427f570a501e1557e11789582dd9` — temporary workflow only.
- Task 14 cleanup: `dfa5cd2269201fbf1f2bf392b2f4043acdcad231`, `f5b632ce1e6c943d26cad66437873ed3e9932565`, `56cc4a56896c7c20f1427172889ed574d5320f9b`.

## Reliability contract established by 0.9.2

- Exact-first remains authoritative; deterministic numeric fallback supplements incomplete exact discovery.
- Exact provenance wins when exact and numeric candidates deduplicate to one physical point.
- Plausible candidate evaluation failure never silently becomes an empty solution set.
- `roots()` and `intersections()` share continuous zero-set discovery/validation/fallback/merge semantics.
- Engine-created engineering symbols are explicitly real and identity-sensitive reconstruction is protected.
- Supported direct unit literals work consistently in roots/intersections/extrema/plot/table domains.
- Dimensional zero bounds such as `0*m` are preserved before symbolic simplification erases units.
- Piecewise boundaries use the selected governing branch; continuous redundant side records collapse to `at`, while discontinuities retain meaningful sides.
- Ordinary plots retain 201 drawing samples while exact characteristic metadata/coordinates remain authoritative.
- Positive structural moment remains plotted downward.
- Plot titles use supported numeric weight **700**, avoiding Matplotlib font fallback warnings on clean environments.
- `envelope(...)` remains sampled in 0.9.2; exact crossovers/governing intervals are deferred to **0.9.3**.
- No SciPy dependency.
- IPython is declared rather than assumed from the notebook host.
- Advertised Python support is CI-validated from 3.10 through 3.14.
- Characteristic internals live under `src/engcalc_colab/characteristics/` with stable facade imports from `characteristics/__init__.py`.

## Earlier authoritative evidence

### Task 10

- Run `33358168465`, job `99384201915`: **39/39 focused + 880/880 full PASS**.
- Idempotent job `99384850174`: same GREEN counts and no product diff.
- Residual, tri-state-realness and simplify-cost observations: **not reproduced; no product change**.

### Task 11

- Matrix run `33358958365`.
- Python 3.10/3.11/3.12/3.13/3.14 jobs `99386459903`, `99386460066`, `99386460051`, `99386460059`, `99386460063`: **881/881 each**.
- Idempotent run `33359297689`, commit job `99388058367`: `No Task 11 product or test patch to commit.`
- Permanent `.github/workflows/ci.yml` remains.

### Task 12

- Pre-refactor run `33359923576`, job `99389160145`: **881/881 in 200.90 s**.
- Authoritative refactor run `33361626996`: **881/881 in 206.46 s**, focused **347/347 in 80.68 s**, public imports/compile/package shape PASS.
- Product commit: `cee4b39e19d2f6f2c49595d8a46efcdd6f1d58ce`.
- Final idempotent run `33362287774`, job `99395831492`: **881/881 in 172.04 s**, focused **347/347 in 67.15 s**; commit job `99396580569` reported `No Task 12 product or test patch to commit.`

### Task 13

- Authoritative run `33364523103`, validation job `99402323373`: **12/12 natural/audit**, **10/10 plot integration**, **884/884 full in 177.25 s**, hygiene PASS.
- Persistent commit: `cce0bd768872a8bc31910435f9b29936e348c027`.
- Idempotent run `33365110693`, job `99404040721`: repeated **12/12**, **10/10**, **884/884 in 179.90 s**; commit job `99404761219` reported `No Task 13 acceptance/docs patch to commit.`
- Cleanup through `52cea79f4ee408128b841445311440e7b84ea64a` removed only Task 13 temporary infrastructure.

## Task 14 — release evidence

### Intentional version RED

- Run **`33365667027`**, job **`99405676920`**.
- Test expectations requested 0.9.2 while product/release surfaces still reported 0.9.1.
- Result: **8 failed / 16 passed in 0.19 s**.
- All eight failures were the expected `0.9.1` → `0.9.2` version mismatches; no product/release surface was modified by the RED harness.
- Gate marker: **`TASK14_VERSION_RED=8 expected version mismatches only`**.

### Initial 0.9.2 candidate and superseded wheel

- Release bump commit: **`2f9a13c2ac1141a67915dad745a30d33b9ed0853`**.
- Initial full release run: **`33365958586`**, release-candidate job **`99406633046`**.
- Release contract: **35/35 PASS in 10.34 s**.
- Full source suite: **884/884 PASS in 128.90 s**.
- Initial real wheel: `engcalc_colab-0.9.2-py3-none-any.whl`.
- Initial SHA-256 **`ea211038c3767e6bc44982a0aa0e5a001ed536828869630528351689edc28df1`** — **SUPERSEDED**, not the release-authoritative hash.
- External `site-packages` smoke PASS.
- Installed source-free suite: **884/884 PASS in 123.16 s**.
- Repeated source suite: **884/884 PASS in 124.27 s**.
- During the clean external smoke, Matplotlib emitted `Failed to find font weight 600, now using 700`; release closure was deliberately halted for a TDD correction.

### Font-warning reproduction and TDD correction

- Independent clean-cache reproduction run **`33366721530`**, job **`99408789784`** confirmed the warning.
- Root cause: five title call sites requested `fontweight=600`, unavailable in the runner's default font set; Matplotlib fell back to 700 and warned.
- Persistent regression commit: **`537c848648dc406230c6d5d3bd49a483db1ed17e`**.
- Persistent RED run **`33394638708`**, job **`99496130524`**: targeted regression failed exactly with `600 != 700` before product modification.
- Product correction commit: **`4d067a5af1c41ecaa9c58906dcfd735ebb7a51ac`** — four `plotting.py` title weights and one `presentation.py` title weight changed from 600 to supported weight 700.
- GREEN run **`33394816387`**, job **`99496705763`**:
  - plotting regression **20/20 PASS in 9.60 s**;
  - clean-font-cache probe marker **`TASK14_FONT_WARNING=ABSENT`**;
  - `compileall` PASS;
  - complete source suite **884/884 PASS in 131.65 s**;
  - scope gate confirmed exactly `src/engcalc_colab/plotting.py` and `src/engcalc_colab/presentation.py` changed.

### Definitive release validation — AUTHORITATIVE

- Run: **`33395163462`**.
- Job: **`99497835438`** SUCCESS.
- Trigger/tree: `662041e32844427f570a501e1557e11789582dd9`, whose parent is product-fix commit `4d067a5af1c41ecaa9c58906dcfd735ebb7a51ac`; the trigger changed only the temporary validation workflow.
- Final release surfaces: version **0.9.2**, `Requires-Python >=3.10`, IPython dependency present, permanent CI present, no product `fontweight=600` remains.
- `compileall` PASS.
- Final release contract: **55/55 PASS in 20.23 s**.
- `git diff --check origin/main...HEAD` PASS.
- Complete source suite before wheel: **884/884 PASS in 179.70 s**.
- Definitive wheel: **`engcalc_colab-0.9.2-py3-none-any.whl`**.
- **Definitive wheel SHA-256: `c493de3b527de4b6100830f00a038a137d1ec110a66aeef27b286e0874357de5`.**
- Wheel METADATA: version 0.9.2, `Requires-Python: >=3.10`, IPython declared; marker **`WHEEL_METADATA=PASS`**.
- GitHub Actions artifact: `engcalc-colab-0.9.2-definitive-wheel`, artifact ID **`9759140418`**. The Actions wrapper ZIP SHA-256 is `6a5aa3aa8e2750d569dbf319270f5165b1a4bf0e92fbcf75813d35ab045076ae` (distinct from the wheel SHA above).
- External installed-wheel smoke imported from `/tmp/engcalc-v092-final-wheel/lib/python3.12/site-packages/engcalc_colab/__init__.py`; marker **`TASK14_EXTERNAL_SMOKE=PASS`**.
- Clean-font-cache test against the installed definitive wheel: marker **`TASK14_INSTALLED_FONT_WARNING=ABSENT`**.
- Complete installed-wheel source-free suite: **884/884 PASS in 179.31 s**, with `engcalc_colab.__file__` proven under `site-packages` and repository `src/` excluded.
- Repeated complete source suite: **884/884 PASS in 177.12 s**.
- Final tracked-tree gate: **`TASK14_FINAL_TREE=TRACKED_CLEAN`**. `wheel.env` existed only as an untracked runner artifact.

### Task 14 cleanup/final audit

- Removed temporary workflow `.github/workflows/v092-task14-release.yml` in **`dfa5cd2269201fbf1f2bf392b2f4043acdcad231`**.
- Removed temporary RED harness `.github/scripts/v092_task14_version_red.py` in **`f5b632ce1e6c943d26cad66437873ed3e9932565`**.
- Removed temporary release/smoke harness `.github/scripts/v092_task14_release_candidate.py` in **`56cc4a56896c7c20f1427172889ed574d5320f9b`**.
- Compare `662041e32844427f570a501e1557e11789582dd9...56cc4a56896c7c20f1427172889ed574d5320f9b` shows **exactly those three temporary files removed and no other changes**.
- Permanent `.github/workflows/ci.yml` remains with Python **3.10–3.14** matrix.
- `pyproject.toml` remains version **0.9.2**, `requires-python >=3.10`, and `ipython>=8.18`.
- Canonical `main` remains **`698696bb8854fa197851cdbb2f5e4c08ef22178b`**.

## Exact next step — release PR

1. Open PR from `feature/v0.9.2-audit-reliability` to `main` titled exactly **`release: EngCalc 0.9.2 audit remediation and reliability`**.
2. Verify PR base/head and that the changes match the approved 0.9.2 scope.
3. Allow permanent `.github/workflows/ci.yml` to run its Python 3.10–3.14 pull-request matrix and verify every job GREEN.
4. Record PR number and final CI evidence in this handoff if another persistent checkpoint is useful.
5. **STOP BEFORE MERGE and request explicit user approval.**

## Deferred/open after 0.9.2

- 0.9.3: Exact Envelopes / Governing Intervals.
- 0.9.4: Named Response Cases / Combinations.
- Separate deferred issues: `no_vertical_scroll()`, multiline ordinary non-matrix call parsing, generalized structural eigenproblems.

## How to resume in a new conversation

Read this file first. Canonical released baseline is still `main@698696bb8854fa197851cdbb2f5e4c08ef22178b` until the 0.9.2 PR is explicitly approved and merged. Active branch is `feature/v0.9.2-audit-reliability`, package/runtime version **0.9.2**. Tasks 1–13 are complete; Task 14 release validation and cleanup are complete. Definitive release run is `33395163462`, job `99497835438`: 55/55 release contract, 884/884 source, definitive wheel SHA-256 `c493de3b527de4b6100830f00a038a137d1ec110a66aeef27b286e0874357de5`, external smoke PASS, installed warning absent, 884/884 source-free installed-wheel, 884/884 repeated source. Temporary Task 14 infrastructure was removed through `56cc4a56896c7c20f1427172889ed574d5320f9b`. Next: open the 0.9.2 release PR, verify permanent CI, then **STOP before merge for explicit user approval**. Never invoke Codex without explicit authorization.
