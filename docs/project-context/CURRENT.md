# EngCalc Current Project Context

_Last updated: 2026-08-29 — EngCalc 0.7.2 engineering tables is merged and is now the canonical `main` baseline._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Default/canonical branch: `main`.
- Current release: **EngCalc 0.7.2 — engineering tables / evaluation by points**.
- Release PR: **#29 — `release: EngCalc 0.7.2 engineering tables`**, merged into `main` on 2026-08-29.
- Merge commit: `a7ba9521220743f3cb79814e13bd44b0e0f9ce5d`.
- Final PR head: `44257871068ff8e9138d85a713752eb44052b13c`.
- Comparison final PR head → merge commit contains **zero changed files**, proving the merge introduced no tree changes beyond merge history.
- Package/runtime version on `main`: **0.7.2** in `pyproject.toml` and `src/engcalc_colab/__init__.py`.
- Approved spec: `docs/superpowers/specs/2026-08-29-engcalc-v0.7.2-engineering-tables-design.md`.
- Approved implementation plan: `docs/superpowers/plans/2026-08-29-engcalc-v0.7.2-engineering-tables-implementation.md`.
- Authoritative distribution-validated code/test/docs SHA: `08a58e77c1ebace0790ba1082290e3a291a47948`.
- Changes from that validated SHA through the final PR head were administrative only: release-workflow cleanup and persistent context updates. No production source, tests, package metadata, or README behavior changed after the authoritative distribution gate.
- Release branch `feature/v0.7.2-engineering-tables` and planning branches are retained; do not delete unless explicitly requested.
- Do not manually invoke Codex, `@codex review`, Codex Cloud, or anything that may consume the user's Codex quota without explicit authorization.

## Approved behavior

- Preserve all 0.7.1 behavior, including multi-argument functions, generalized partial evaluation, scalar math, 201-point plot/envelope sampling and positive-moment-down convention.
- Primary 0.7.2 syntax: `table(M(x), x, 0, L, 21)`.
- Exact dimensionless zero may inherit a compatible dimensional peer endpoint; nonzero dimensionless endpoints may not.
- Unit-once explicit points: `table(M(x), x, [0, 1, 1.5, 2], m)`.
- Fully explicit compatible points: `table(M(x), x, [0*m, 50*cm, 1*m])`.
- Descending uniform ranges are valid; count is a dimensionless integer >= 2 and both endpoints are included.
- Multiple response columns preserve source order and must be dimensionally compatible in 0.7.2.
- Table evaluation uses the table variable as a local numeric override and does not mutate stored symbolic/numeric state.
- Constant responses, nested user functions, multi-argument user functions and supported scalar math work inside tables.
- Table output renders as native HTML inside `%%eng`; variable is the first column and responses follow source order.
- Units appear once in table headers, not in every body cell; dimensionless headers omit a unit suffix.
- Table numeric cells obey the same `RenderSettings.precision` and `RenderSettings.zero_tolerance` configuration used elsewhere in `%%eng`.
- User-derived table labels are HTML-escaped before display.
- A table is a display boundary in `%%eng`: pending equations flush before it, the table displays as `HTML`, and later equations resume in a new MathJax group. Headings keep source order around tables.
- Arbitrary list literals remain rejected outside the table-point whitelist and existing plot/envelope sweep whitelist.
- README presents automatic discretization as the normal/recommended form; explicit-point forms are secondary tools for selected locations.
- No pandas runtime dependency was added.
- Export/download APIs and Cartesian multi-parameter table sweeps remain outside 0.7.2.

## Open issues / user feedback

- No known functional blocker remains for EngCalc 0.7.2.
- Task 6 release closure and integration are complete.
- PR #29 is merged; `main` now exposes 0.7.2.
- The first final-distribution attempt exposed only a stale test assertion that still expected version 0.7.1; no production behavior failed. That stale contract was corrected and the entire distribution pipeline was rerun from the beginning successfully.
- No production/test rerun was required after merge because the final PR head and merge commit have zero file differences; post-merge verification additionally confirmed both package metadata and runtime `__version__` are 0.7.2 on `main`.

## Validation evidence

### 0.7.1 release baseline

- Authoritative corrected release gate Actions `33259552699`: focused **77/77**, source **386/386**, installed-wheel source-free **386/386**, repeated source **386/386**.
- Artifact `9716898144`; digest `sha256:18670d97351bd2403d3be912aaff9773953ccaaa54aeb409973cd48baec20361`.

### 0.7.2 execution baseline

- Corrected baseline Actions `33261841291` on SHA `c3b979f22f47d7aecdc7e5fd49541530508eccf5`: **386/386 passed** in Python 3.13.15; runtime version then remained 0.7.1.

### Task 1 — restricted parser grammar and result models

- RED: commit `102b91b0e93f1cf47670fe873944fc08d7ec19ec`, Actions `33261976864`: **12 failed, 28 passed**.
- Product commits: `01788b38fdd06a0054d0c0d116882d5c0631cfb9` and `cb1ccf0417ae20b31e7bbf59110f3e004bdc3c20`.
- Complete GREEN gate Actions `33262151576`: focused **40/40**, source **402/402**.

### Task 2 — table point/range normalization

- RED: commit `2a9ff3aaca0138d1fcf039ea9e540c1f96826b2f`, Actions `33262313647`: **21 failed, 34 passed**.
- Product: `7fe7528b701448aaf05991105191078ebe1a8621` (`src/engcalc_colab/tables.py`).
- Complete GREEN gate Actions `33262681298` on `a1a9a96acbe5b362c28c577b408b1c537c728dbb`: focused **55/55**, source **423/423**.

### Task 3 — end-to-end engine table evaluation

- RED: `e5759ed21bd7573d1e1976a08c9797f5fd9623e2`, Actions `33262826998`: **12 failed, 39 passed**.
- Product: `0625a97656a6a7ffe2a4cfa692eda979c679fc1a` (`src/engcalc_colab/engine.py`).
- Complete GREEN gate Actions `33263067183` on `326117a2190b5fe69ffce072686291f623652fbc`: focused **51/51**, source **436/436**.
- Central engineering contract verified: `M(x,q,L)=q*x*(L-x)/2`, `q=4*kN/m`, `L=5*m`, 21-point table includes `x=2.5 m`, `M=12.5 kN*m`.

### Task 4 — native HTML rendering and real `%%eng` integration

- RED Actions `33263389497`: **7 failed, 37 passed**.
- Product: `55fffe0dbcc280fb2a5685b48921e062be923f9f`, limited to renderer/magic production changes.
- Authoritative gate Actions `33263583872` on `34be4158147e16633dc5f263c29d5df3df84f576`: focused **44/44**, source **443/443**.
- Verified units in headers, magnitude-only body cells, dimensionless headers, precision/zero tolerance, HTML escaping, row/response order and `%%eng` ordering around headings/equations/tables.

### Task 5 — engineer-facing acceptance and documentation

- Acceptance tests introduced at `a3739cc4308841f9e0cda38dd61a815d6cfc7d04`.
- Initial acceptance Actions `33265849521`: engineer-facing **7/7**, complete table subset **79/79** with no production change.
- Documentation RED: `d16f0b9a1ad3a4f1a6266974d467bf9d35801b92`, Actions `33265916449`: **1 failed, 7 passed**, only the intentionally missing README 0.7.2 section.
- README table documentation commit: `8cea6232090b746970dba51197dd7d67a8535091`.
- Authoritative Task 5 gate Actions `33266011166` on `e4ceabd127227c7149d10814559c0cc561169754`: acceptance/docs **8/8**, table subset **80/80**, source **451/451**.

### Task 6 — release closure and distribution validation

- Version RED test commit: `3cde70bc7e2dfda86b7b0f9bae67fdfc41453d01`.
- Version RED Actions `33266296064`: new version contract **2 expected failures** (`0.7.1` vs `0.7.2`), while table subset remained **80/80** and all prior tests remained **451/451**.
- Release version bump commit: `e5a6a78be70ca7d3b69a253ed63e61109d813b64`; it changed only the version in `pyproject.toml`, `src/engcalc_colab/__init__.py`, and the README current-version line.
- Obsolete 0.7.1 release contracts were cleaned from `tests/test_release_version_v071.py` and `tests/test_packaging.py`.
- Release-documentation RED commit: `450a4dfa45a7c16b2ac1e502609fc4f39238dacf`; Actions `33266570230`: **3 failed, 2 passed**, where the technical 0.7.2 version checks passed and only stale README release text failed.
- Final README release documentation commit: `c39344adf8cfb94b60edf944b44d42b8063ae1b8`.
- Release-documentation GREEN Actions `33266681245`: **5/5 passed**.
- First distribution attempt Actions `33266769037`: release contracts **11/11**, table subset **80/80**, full source **453 passed / 1 failed**. The sole failure was a historical `tests/test_parser.py` assertion still requiring `__version__ == "0.7.1"`; production was not changed. The stale assertion was updated in `ad40a8b303ca2826ea54369d41a82dd871a9db96`.
- **Authoritative final distribution gate:** Actions **`33266879721`**, job `99138382437`, validated SHA **`08a58e77c1ebace0790ba1082290e3a291a47948`**, Python **3.13.15**.
- Release/version/packaging contracts: **11/11 passed**.
- Complete table feature subset: **80/80 passed**.
- Complete source suite: **454/454 passed**.
- Built wheel: **`engcalc_colab-0.7.2-py3-none-any.whl`**; wheel METADATA verified `Name: engcalc-colab`, `Version: 0.7.2`.
- Clean venv installed the built wheel. External smoke executed from `/tmp` with `PYTHONPATH=''`, verified the imported package came from `site-packages`, not repository `src/`, and returned **PASS**.
- External smoke covers primary automatic 21-point tables, unit-once points, mixed `m/cm` points, multi-response tables, descending ranges, native `%%eng` HTML + plot source ordering, representative 0.7.1 multi-argument numeric/partial evaluation and 201-point plotting.
- Source-free installed-wheel test tree contained tests + `pyproject.toml` + README and explicitly no `src/`; full installed-wheel suite: **454/454 passed**.
- Repeated complete source suite after installed-wheel validation: **454/454 passed**.
- Wheel SHA-256: **`bb7ece9ee102f3909cf78b53e99ff46f2229053372e7446bede2af321ae621cf`**.
- GitHub Actions artifact: **`engcalc-colab-0.7.2-final-wheel`**, artifact ID **`9718968626`**, size **32635 bytes**, artifact ZIP digest **`sha256:534987da55e705ee977f0f2c5d067777da2e4d3bd0860fcf594eeb77b543599f`**, created `2026-08-29T18:00:39Z`, expires `2026-11-27T17:55:16Z`.
- Temporary final-distribution workflow was removed only after the authoritative gate succeeded.

### Post-merge verification

- PR #29 merged successfully at `2026-08-29T18:22:56Z`.
- Merge commit: `a7ba9521220743f3cb79814e13bd44b0e0f9ce5d`; GitHub reports a valid verified merge signature.
- Final PR head: `44257871068ff8e9138d85a713752eb44052b13c`.
- Compare final PR head → merge commit: **1 merge-history commit, 0 changed files**.
- `main` `pyproject.toml`: `version = "0.7.2"`.
- `main` `src/engcalc_colab/__init__.py`: `__version__ = "0.7.2"`.
- Because the merged tree is file-identical to the approved final PR head, the authoritative distribution gate remains applicable to the merged product tree.

## Roadmap / active plan

- **0.7.1 complete and merged.**
- **0.7.2 engineering tables complete, distribution-validated, and merged to `main`.**
- Tasks 0–6 for 0.7.2 are complete.
- Canonical baseline is now EngCalc 0.7.2.
- Next roadmap milestone remains **0.7.3 derivation traces** unless amended.

## Exact next step

- No further 0.7.2 implementation or release action is pending.
- Preserve 0.7.2 behavior and release evidence as the new regression baseline.
- When work resumes, read `docs/superpowers/specs/2026-08-28-engcalc-evolution-roadmap-design.md` and this file first.
- The next planned milestone is **0.7.3 derivation traces**. Start with design/spec work before implementation, following the Superpowers approval gates and strict TDD RED→GREEN workflow.
- Retain feature/planning branches unless explicitly requested otherwise.
- Do not manually invoke Codex.

## How to resume in a new conversation

Read this file first. EngCalc **0.7.2** is the canonical `main` release. PR #29 is merged at `a7ba9521220743f3cb79814e13bd44b0e0f9ce5d`, with zero file differences between the final PR head and merge commit. The authoritative distribution gate is Actions `33266879721` on `08a58e77c1ebace0790ba1082290e3a291a47948`: release contracts 11/11, table subset 80/80, source 454/454, external installed-wheel smoke PASS, source-free installed-wheel 454/454, repeated source 454/454. Wheel: `engcalc_colab-0.7.2-py3-none-any.whl`, SHA-256 `bb7ece9ee102f3909cf78b53e99ff46f2229053372e7446bede2af321ae621cf`; artifact ID `9718968626`. The next planned roadmap milestone is 0.7.3 derivation traces; do not begin implementation before the design/spec approval workflow. Do not manually invoke Codex.