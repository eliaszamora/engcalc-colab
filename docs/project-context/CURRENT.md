# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.1 exact characteristics is fully release-validated. Tasks 1–12, wheel/source-free validation and the final clean pre-PR gate are complete. All temporary validation infrastructure is removed. Release PR #33 is open against `main`. Work is intentionally STOPPED before merge pending explicit user approval._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released branch: `main@cdc454db7ea43e57e334d523afded8b4ef498ded` — EngCalc 0.9.0 Matrix/CAS.
- Active release branch: `feature/v0.9.1-exact-characteristics`.
- Runtime/package version on release branch: **0.9.1**.
- Verified release metadata commit: `e997d93a69d1ba3589dc48a9ce945b1037476967`.
- Authoritative wheel-validation SHA: `2628186afd409cf2a1ec898a39a6e8c5ed5f6f2b`.
- Final pre-PR gate SHA: `50581b6ab8fdf46b072577bd1b2e189711761a73`.
- Final gate cleanup commit: `03c56a89d1e42a107d34fe078e80ba63da4adf0a`.
- Release PR: **#33 — `release: EngCalc 0.9.1 exact characteristics`**, head `feature/v0.9.1-exact-characteristics`, base `main`, open and not merged.
- Approved spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
- Approved plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.1-exact-characteristics-implementation.md`.
- User selected inline execution.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.
- Never merge PR #33 without explicit user approval.

## Approved behavior

Public standalone characteristic calls in 0.9.1:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

- Characteristic calls are standalone-only in 0.9.1; assignment, nesting and unsupported composition are rejected.
- Core solving is exact-first, unit-aware, Piecewise-safe, deterministic on fallback, scalar-only and provenance-preserving.
- Whole matrices remain invalid characteristic responses; indexed matrix scalars are valid.
- Standalone rendering distinguishes exact `=` from numerical fallback `≈`.
- Ordinary `plot(...)` retains its 201-point drawing grid while carrying authoritative exact global-extremum metadata independently of that grid.
- Positive structural moment remains plotted downward.
- Existing Numeric/Pint, Piecewise, tables, plots, envelopes, multi-argument functions and Matrix/CAS behavior remain regression requirements.
- `envelope(...)` deliberately remains sampled in 0.9.1; exact governing intervals/crossovers are deferred to 0.9.2.

## Open issues / user feedback

- No blocking 0.9.1 product, packaging, wheel, source-free or pre-PR validation issue remains.
- Tasks 1–12 are complete.
- PR #33 is open; the only release-blocking checkpoint is **explicit user approval to merge**.
- `no_vertical_scroll()` remains a separate ergonomics issue.
- Multiline ordinary non-matrix function-call parsing remains separate.
- Generalized structural eigenproblems remain deferred.

## Validation evidence

### 0.9.1 progression

- Task 1 full suite: 758/758 GREEN.
- Task 2: 772/772 GREEN.
- Task 3: 783/783 GREEN.
- Task 4: 794/794 GREEN.
- Task 5: 800/800 GREEN.
- Task 6: 808/808 GREEN.
- Task 7: 820/820 GREEN.
- Task 8 run `33340983117`, job `99336452342`: 828/828 full GREEN in 104.51 s.
- Task 9 run `33341538689`, job `99337950723`: 835/835 full GREEN in 117.02 s.
- Task 10 run `33342633493`, job `99340916954`: `compileall` PASS, diff hygiene PASS, 844/844 full GREEN in 142.78 s.
- Task 11 authoritative run `33343511326`, job `99343282200`: `compileall` PASS, diff hygiene PASS, acceptance 2/2 PASS, 846/846 full source PASS in 98.43 s.

### Task 12 release validation

- Intentional version RED: 6 failed / 5 passed in 0.08 s, exclusively expected 0.9.0 → 0.9.1 mismatches.
- First GREEN run `33343868704`, job `99344237909`: one stale historical parser version assertion remained; 845 passed / 1 failed in 175.29 s. Release bump was not committed from that failed run.
- Effective stale-version correction: `a358ed15910b6393399d86f3c9ce8383d0e82040`; no product behavior change.
- Successful metadata GREEN run `33344172956`, job `99345049612`: release contract 11/11 PASS in 0.05 s; full source 846/846 PASS in 172.60 s.
- Release metadata commit: `e997d93a69d1ba3589dc48a9ce945b1037476967`.
- Authoritative wheel run `33344486134`, job `99345919150`: SUCCESS.
- Committed release contract including parser: 23/23 PASS in 0.05 s.
- Real wheel: `engcalc_colab-0.9.1-py3-none-any.whl`.
- Wheel metadata version: 0.9.1.
- Wheel SHA-256: `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`.
- External clean-venv/site-packages smoke: PASS.
- Installed-wheel source-free suite: 846/846 PASS in 90.59 s.
- Post-wheel source suite: 846/846 PASS in 89.52 s.
- Evidence artifact: `engcalc-0.9.1-release-validation`, artifact ID `9741591634`, ZIP SHA-256 `39453d375a3148fb27b3944d398f48381665f17edb0a17f4c9c09fa8fee9b4c0`.

### Final clean pre-PR gate

- Gate SHA: `50581b6ab8fdf46b072577bd1b2e189711761a73`.
- Run `33345708275`, job `99349296928`: SUCCESS on Python 3.13.15.
- Confirmed all prior Task 12 harness files absent and version metadata/README at 0.9.1.
- `python -m compileall -q src/engcalc_colab`: PASS.
- `git diff --check origin/main...HEAD`: PASS.
- Release contract: 23/23 PASS in 0.07 s.
- Complete source suite: **846/846 PASS in 111.56 s**.
- Temporary final-gate workflow removed immediately after success in `03c56a89d1e42a107d34fe078e80ba63da4adf0a`.
- Final compare before PR creation: branch 178 commits ahead / 0 behind `main`; 29 changed files; **no `.github` validation file present**.
- `main` remained exactly `cdc454db7ea43e57e334d523afded8b4ef498ded`.
- PR #33 created from the validated release branch; no pre-existing duplicate PR was found.
- No Codex review or Codex Cloud has been invoked.

## Roadmap / active plan

- 0.9.0 Matrix/CAS: COMPLETE + RELEASE-VALIDATED + MERGED.
- 0.9.1 Tasks 1–12: COMPLETE.
- 0.9.1 wheel/source-free/final pre-PR validation: COMPLETE.
- 0.9.1 PR #33: **OPEN — AWAITING EXPLICIT MERGE APPROVAL**.
- Later: 0.9.2 exact envelopes/governing intervals → 0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization.

## Exact next step

1. STOP now; do not merge PR #33 automatically.
2. Obtain explicit user approval to merge PR #33.
3. After approval, re-read PR #33 and verify its current head/base/state immediately before merge.
4. Merge only if the PR still corresponds to the validated 0.9.1 release branch and `main` has not changed unexpectedly.
5. Perform post-merge verification/update of `CURRENT.md` as required by the project workflow.
6. Never invoke Codex unless separately authorized.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.1 exact characteristics is release-validated and PR #33 is open against `main`. Final gate run `33345708275`, job `99349296928` passed `compileall`, diff hygiene, 23/23 release contract and 846/846 full source tests in 111.56 s. The real 0.9.1 wheel passed external smoke and 846/846 source-free tests; its SHA-256 is `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`. All temporary validation infrastructure is removed. STOP before merge until the user explicitly approves PR #33. After approval, verify PR state/head/base, merge, then perform post-merge closure. Never invoke Codex without explicit authorization.
