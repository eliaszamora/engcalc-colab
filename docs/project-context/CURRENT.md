# EngCalc Current Project Context

_Last updated: 2026-08-31 — EngCalc 0.9.2 Audit Remediation & Reliability is integrated into `main`. Tasks 1–14 are COMPLETE. Release PR #34 was merged only after explicit user approval and after the permanent Python 3.10–3.14 PR CI matrix was fully GREEN._

## Canonical state

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released product integration: **PR #34**, merge commit **`a42b6bcd18c54794f02d032e8b376747c35bba87`**.
- Previous 0.9.1 `main`: `698696bb8854fa197851cdbb2f5e4c08ef22178b`.
- Release branch retained: `feature/v0.9.2-audit-reliability`; do not delete it unless explicitly requested.
- Runtime/package version: **0.9.2**.
- `requires-python = ">=3.10"`.
- Runtime dependency includes **`ipython>=8.18`**.
- Permanent CI: `.github/workflows/ci.yml`, Python **3.10–3.14**, on pull requests and pushes to `main`.
- Approved spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-design.md`.
- Approved implementation plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.2-audit-remediation-reliability-implementation.md`.
- Persistent audit regressions: `tests/test_v092_audit_regressions.py`.
- Persistent risk probes: `tests/test_v092_risk_probes.py`.
- Never invoke Codex / Codex Cloud without explicit user authorization.

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
14. **COMPLETE** — 0.9.2 release bump, real-wheel/source-free validation, clean-environment font warning correction, cleanup, permanent PR CI, explicit merge approval, merge, and post-merge `main` CI.

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
- Task 14 warning fix: **`4d067a5af1c41ecaa9c58906dcfd735ebb7a51ac`** — `fix: use supported plot title weight`.
- Final release-branch handoff before PR: **`3e3c3b5dbce9e428c65951a84345c3e81b6a5070`**.
- Release merge: **`a42b6bcd18c54794f02d032e8b376747c35bba87`** — PR #34.

## Earlier authoritative evidence

### Task 10

- Run `33358168465`, job `99384201915`: **39/39 focused + 880/880 full PASS**.
- Idempotent job `99384850174`: same GREEN counts and no product diff.
- Residual, tri-state-realness and simplify-cost observations: **not reproduced; no product change**.

### Task 11

- Matrix run `33358958365`.
- Python 3.10/3.11/3.12/3.13/3.14 jobs `99386459903`, `99386460066`, `99386460051`, `99386460059`, `99386460063`: **881/881 each**.
- Idempotent run `33359297689`, commit job `99388058367`: `No Task 11 product or test patch to commit.`

### Task 12

- Pre-refactor run `33359923576`, job `99389160145`: **881/881 in 200.90 s**.
- Authoritative refactor run `33361626996`: **881/881 in 206.46 s**, focused **347/347 in 80.68 s**, public imports/compile/package shape PASS.
- Final idempotent run `33362287774`, job `99395831492`: **881/881 in 172.04 s**, focused **347/347 in 67.15 s**; commit job `99396580569` reported `No Task 12 product or test patch to commit.`

### Task 13

- Authoritative run `33364523103`, validation job `99402323373`: **12/12 natural/audit**, **10/10 plot integration**, **884/884 full in 177.25 s**, hygiene PASS.
- Idempotent run `33365110693`, job `99404040721`: repeated **12/12**, **10/10**, **884/884 in 179.90 s**; commit job `99404761219` reported `No Task 13 acceptance/docs patch to commit.`

## Task 14 — release evidence

### Intentional version RED

- Run **`33365667027`**, job **`99405676920`**.
- Result: **8 failed / 16 passed in 0.19 s**.
- All eight failures were intentional `0.9.1` → `0.9.2` version mismatches; marker: `TASK14_VERSION_RED=8 expected version mismatches only`.

### Initial candidate and warning correction

- Initial 0.9.2 candidate run `33365958586`, job `99406633046`: release contract **35/35**, source **884/884**, installed source-free **884/884**, repeated source **884/884**.
- Initial wheel SHA-256 `ea211038c3767e6bc44982a0aa0e5a001ed536828869630528351689edc28df1` is **SUPERSEDED**.
- Clean external smoke exposed Matplotlib warning `Failed to find font weight 600, now using 700`; release closure was halted for a TDD correction.
- Independent reproduction: run `33366721530`, job `99408789784`.
- Persistent RED: run `33394638708`, job `99496130524`, failed exactly with `600 != 700`.
- GREEN fix run `33394816387`, job `99496705763`: plotting **20/20**, `TASK14_FONT_WARNING=ABSENT`, `compileall` PASS, full source **884/884 in 131.65 s**.

### Definitive release validation — AUTHORITATIVE

- Run **`33395163462`**, job **`99497835438`** SUCCESS.
- Final release contract: **55/55 PASS in 20.23 s**.
- Complete source suite before wheel: **884/884 PASS in 179.70 s**.
- Definitive wheel: **`engcalc_colab-0.9.2-py3-none-any.whl`**.
- **Definitive wheel SHA-256: `c493de3b527de4b6100830f00a038a137d1ec110a66aeef27b286e0874357de5`.**
- Wheel METADATA: version 0.9.2, `Requires-Python: >=3.10`, IPython declared; `WHEEL_METADATA=PASS`.
- Actions artifact: `engcalc-colab-0.9.2-definitive-wheel`, artifact ID `9759140418`.
- External installed-wheel smoke from `site-packages`: `TASK14_EXTERNAL_SMOKE=PASS`.
- Installed clean-font-cache test: `TASK14_INSTALLED_FONT_WARNING=ABSENT`.
- Complete installed-wheel source-free suite: **884/884 PASS in 179.31 s**.
- Repeated complete source suite: **884/884 PASS in 177.12 s**.
- Final tracked-tree gate: `TASK14_FINAL_TREE=TRACKED_CLEAN`.

### Cleanup

- Temporary Task 14 workflow/harness removals: `dfa5cd2269201fbf1f2bf392b2f4043acdcad231`, `f5b632ce1e6c943d26cad66437873ed3e9932565`, `56cc4a56896c7c20f1427172889ed574d5320f9b`.
- Compare `662041e32844427f570a501e1557e11789582dd9...56cc4a56896c7c20f1427172889ed574d5320f9b` showed exactly the three temporary files removed; no product/test behavior changed.
- Permanent `.github/workflows/ci.yml` remained.

### Permanent PR CI before merge

- Release PR: **#34**, `release: EngCalc 0.9.2 audit remediation and reliability`.
- Base: `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`.
- Head: `feature/v0.9.2-audit-reliability@3e3c3b5dbce9e428c65951a84345c3e81b6a5070`.
- PR CI run: **`33396652111`**; all five jobs SUCCESS on GitHub's combined PR merge tree.
- Python 3.10 job `99502652504`: **884/884 in 149.93 s**.
- Python 3.11 job `99502652562`: **884/884 in 188.05 s**.
- Python 3.12 job `99502652472`: **884/884 in 200.81 s**.
- Python 3.13 job `99502652547`: **884/884 in 188.77 s**.
- Python 3.14 job `99502652157`: **884/884 in 158.17 s**.
- PR was re-verified `mergeable=true` with the exact expected head before merge.

### Authorized merge and post-merge CI

- User gave explicit merge approval after the PR CI matrix was GREEN.
- PR #34 merged on **2026-08-31 13:31:52Z** with expected head `3e3c3b5dbce9e428c65951a84345c3e81b6a5070`.
- Merge commit: **`a42b6bcd18c54794f02d032e8b376747c35bba87`**.
- GitHub reports PR #34 `closed`, `merged=true`.
- `main` was verified to point to `a42b6bcd18c54794f02d032e8b376747c35bba87` immediately after merge.
- Post-merge permanent CI run on `main`: **`33397476016`**, conclusion SUCCESS.
- Python 3.10 job `99505370856`: **884/884 in 151.03 s**.
- Python 3.11 job `99505371332`: **884/884 in 167.65 s**.
- Python 3.12 job `99505370924`: **884/884 in 201.38 s**.
- Python 3.13 job `99505370690`: **884/884 in 185.47 s**.
- Python 3.14 job `99505370611`: **884/884 in 131.72 s**.
- Main `pyproject.toml` was re-read after merge and reports version **0.9.2**, `requires-python >=3.10`, and `ipython>=8.18`.

## Next planned release

**0.9.3 — Exact Envelopes / Governing Intervals** is the next approved roadmap direction. The 0.9.2 contract intentionally leaves `envelope(...)` sampled.

Deferred beyond that:
- 0.9.4: Named Response Cases / Combinations.
- Separate deferred issues: `no_vertical_scroll()`, multiline ordinary non-matrix call parsing, generalized structural eigenproblems.

## How to resume in a new conversation

Read this file first. EngCalc **0.9.2** is the canonical baseline integrated into `main` through PR #34 / merge commit `a42b6bcd18c54794f02d032e8b376747c35bba87`. Tasks **1–14 are COMPLETE**. The definitive 0.9.2 wheel is `engcalc_colab-0.9.2-py3-none-any.whl` with SHA-256 `c493de3b527de4b6100830f00a038a137d1ec110a66aeef27b286e0874357de5`. The definitive release run, full installed-wheel validation, permanent PR CI, and post-merge `main` CI are all GREEN. The next roadmap target is **0.9.3 Exact Envelopes / Governing Intervals**. Never invoke Codex without explicit authorization.
