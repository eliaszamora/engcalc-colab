# EngCalc Current Project Context

_Last updated: 2026-08-30 — EngCalc 0.9.1 exact characteristics is complete, release-validated, merged into `main`, and post-merge validated. All temporary validation infrastructure has been removed. The next planned release is 0.9.2 exact envelopes/governing intervals._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical released version: **EngCalc 0.9.1 Exact Characteristics**.
- Release PR: **#33 — `release: EngCalc 0.9.1 exact characteristics`**.
- PR #33 merge commit: **`25edd1e652081f31c16ffed05d24f4d00eaa8950`**.
- Post-merge validation workflow commit: `1ef76411277968924b07e3090ccc92d3ab4756f7`.
- Post-merge workflow cleanup commit: **`27bb27cdd3fde13e27d70eafb55a958a493b57ce`**.
- Runtime/package version on `main`: **0.9.1**.
- Real release wheel: `engcalc_colab-0.9.1-py3-none-any.whl`.
- Wheel SHA-256: **`f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`**.
- Approved 0.9.1 spec: `docs/superpowers/specs/2026-08-30-engcalc-v0.9.1-exact-characteristics-design.md`.
- Approved 0.9.1 plan: `docs/superpowers/plans/2026-08-30-engcalc-v0.9.1-exact-characteristics-implementation.md`.
- Never invoke Codex / `@codex review` / Codex Cloud without explicit user authorization.

## Approved behavior

Public standalone characteristic calls released in 0.9.1:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

- Characteristic solving is exact-first, unit-aware, Piecewise-safe, scalar-only and provenance-preserving.
- Deterministic residual-validated numeric fallback is used only when exact symbolic resolution is unresolved.
- Whole matrices remain invalid characteristic responses; indexed matrix scalars are valid.
- Standalone rendering distinguishes exact `=` from numerical fallback `≈`.
- Ordinary `plot(...)` retains its 201-point drawing grid while carrying authoritative exact global-extremum metadata independently of that grid.
- Positive structural moment remains plotted downward.
- Existing Numeric/Pint, Piecewise, tables, plots, envelopes, multi-argument functions and Matrix/CAS behavior remain regression requirements.
- `envelope(...)` remains sampled in 0.9.1; exact crossovers/governing intervals are intentionally deferred to **0.9.2**.

## Open issues / user feedback

- No blocking 0.9.1 product, packaging, wheel, source-free, merge or post-merge validation issue remains.
- `no_vertical_scroll()` remains a separate ergonomics issue.
- Multiline ordinary non-matrix function-call parsing remains separate.
- Generalized structural eigenproblems remain deferred.
- Next planned product scope: **0.9.2 exact envelopes/governing intervals**.

## Validation evidence

### 0.9.1 implementation progression

- Task 1: 758/758 full GREEN.
- Task 2: 772/772 full GREEN.
- Task 3: 783/783 full GREEN.
- Task 4: 794/794 full GREEN.
- Task 5: 800/800 full GREEN.
- Task 6: 808/808 full GREEN.
- Task 7: 820/820 full GREEN.
- Task 8 run `33340983117`, job `99336452342`: 828/828 full GREEN in 104.51 s.
- Task 9 run `33341538689`, job `99337950723`: 835/835 full GREEN in 117.02 s.
- Task 10 run `33342633493`, job `99340916954`: `compileall` PASS, diff hygiene PASS, 844/844 full GREEN in 142.78 s.
- Task 11 run `33343511326`, job `99343282200`: acceptance 2/2 PASS and 846/846 full source PASS in 98.43 s.

### Task 12 release validation

- Intentional version RED: 6 failed / 5 passed in 0.08 s, exclusively the expected 0.9.0 → 0.9.1 mismatch.
- Effective stale-version test correction: `a358ed15910b6393399d86f3c9ce8383d0e82040`; product behavior unchanged.
- Successful metadata GREEN run `33344172956`, job `99345049612`: 11/11 focused release contract PASS; 846/846 full source PASS in 172.60 s.
- Verified release metadata commit: `e997d93a69d1ba3589dc48a9ce945b1037476967`.
- Authoritative wheel run `33344486134`, job `99345919150`: SUCCESS.
- Committed release contract including parser: 23/23 PASS.
- External clean-venv/site-packages smoke: PASS.
- Installed-wheel source-free suite: **846/846 PASS in 90.59 s**.
- Post-wheel source suite: **846/846 PASS in 89.52 s**.
- Release evidence artifact: `engcalc-0.9.1-release-validation`, artifact ID `9741591634`, ZIP SHA-256 `39453d375a3148fb27b3944d398f48381665f17edb0a17f4c9c09fa8fee9b4c0`.

### Final pre-PR validation

- Gate SHA `50581b6ab8fdf46b072577bd1b2e189711761a73`.
- Run `33345708275`, job `99349296928`: SUCCESS on Python 3.13.15.
- `compileall`: PASS.
- `git diff --check origin/main...HEAD`: PASS.
- Release contract: **23/23 PASS in 0.07 s**.
- Complete source suite: **846/846 PASS in 111.56 s**.
- All temporary pre-PR validation files removed before PR creation.

### Merge and post-merge validation

- User explicitly approved merge of PR #33.
- Immediately before merge, PR #33 was open, mergeable, base `main@cdc454db7ea43e57e334d523afded8b4ef498ded`, head `6aff1791742eddf9ea2f61e00f176cd123da6c63`.
- PR #33 merged successfully as **`25edd1e652081f31c16ffed05d24f4d00eaa8950`**.
- Post-merge run **`33346335859`**, job **`99351086733`**: SUCCESS on `main`.
- Post-merge version checks: PASS.
- Post-merge `compileall`: PASS.
- Post-merge diff hygiene: PASS.
- Post-merge release contract: **23/23 PASS in 0.08 s**.
- Post-merge complete source suite: **846/846 PASS in 133.55 s**.
- Temporary post-merge workflow removed in cleanup commit **`27bb27cdd3fde13e27d70eafb55a958a493b57ce`**.
- No Codex review or Codex Cloud was invoked.

## Roadmap / active plan

- **0.9.0 Matrix/CAS:** COMPLETE + RELEASE-VALIDATED + MERGED.
- **0.9.1 Exact Characteristics:** **COMPLETE + RELEASE-VALIDATED + MERGED + POST-MERGE VALIDATED**.
- Next planned release: **0.9.2 exact envelopes/governing intervals**.
- Later: **0.9.3 named response cases/combinations → 0.10.x engineering verification → 1.0.0 stabilization**.

## Exact next step

1. Treat `main` with EngCalc 0.9.1 as the new canonical baseline.
2. Before starting 0.9.2, create/approve its design spec and implementation plan.
3. Implement 0.9.2 exact envelope crossovers/governing intervals with the same RED→GREEN and release-validation discipline.
4. Preserve all released 0.9.1 behavior as regression requirements.
5. Never invoke Codex unless separately authorized.

## How to resume in a new conversation

Read this file first. EngCalc 0.9.1 Exact Characteristics is now the canonical released baseline on `main`. PR #33 merged as `25edd1e652081f31c16ffed05d24f4d00eaa8950`. The real wheel SHA-256 is `f993599186f4e93cd79b2fc64b84df646499140c6625addad38d2f29f36af0ab`; external wheel smoke and the source-free suite passed. Final pre-PR validation was 846/846 GREEN, and post-merge run `33346335859`, job `99351086733`, also passed 23/23 release-contract tests and 846/846 full source tests in 133.55 s. All temporary validation workflows/scripts are removed. The next planned release is 0.9.2 exact envelopes/governing intervals. Never invoke Codex without explicit authorization.
