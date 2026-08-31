import os
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "docs" / "project-context" / "CURRENT.md"


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    marker = "## Validation evidence — Task 13"
    if marker in text:
        print("Task 13 closure context already materialized.")
        return

    run_id = os.environ["TASK13_RUN_ID"]

    text = text.replace(
        "Tasks 1–12 are complete; Task 13 is next.",
        "Tasks 1–13 are complete; Task 14 is next.",
    )
    text = text.replace(
        "re-verified unchanged through Task 12.",
        "re-verified unchanged through Task 13.",
    )
    text = text.replace(
        "13. **NEXT** — broaden natural-input acceptance, rename v0.9.3 envelope acceptance, README reliability documentation, complete regression + hygiene.\n14. 0.9.2 version/release validation/PR; **STOP before merge**.",
        "13. **COMPLETE** — natural audit-remediation acceptance, 0.9.3 envelope deferral naming, README reliability documentation, full regression + hygiene.\n14. **NEXT** — 0.9.2 version/release validation/PR; **STOP before merge**.",
    )
    text = text.replace(
        "## Reliability contract established through Task 12",
        "## Reliability contract established through Task 13",
    )

    start = text.index("## Exact next step — Task 13")
    end = text.index("## Still deferred / open", start)
    replacement = f"""## Validation evidence — Task 13

- Authoritative pre-persistence acceptance run: **`{run_id}`**.
- `compileall` PASS.
- Natural acceptance + persistent audit regressions: **12/12 PASS**.
- Characteristic plot/envelope integration: **10/10 PASS**; the sampled-envelope deferral test is now named `...until_v093` with assertions unchanged.
- Complete source suite: **884/884 PASS**.
- `git diff --check` PASS; no `src/engcalc_colab` modification is permitted or present in Task 13.
- `.github/workflows/ci.yml` remains the only intentionally permanent workflow added relative to canonical `main`; the Task 13 workflow/scripts are temporary validation infrastructure.
- README documents exact-first + deterministic fallback, natural unit-literal bounds, continuous Piecewise boundary semantics, exact ordinary-plot characteristic coordinates, Python 3.10–3.14 CI, declared IPython dependency, the `characteristics` package split, and exact-envelope deferral to 0.9.3 while the released-version label remains 0.9.1.
- C-1 **COMPLETE** — `log`, incomplete transcendental discovery, quintic roots and log intersections no longer silently false-negative.
- H-1 **COMPLETE** — engine engineering symbols are explicitly real; identity-sensitive reconstruction and `abs` extrema remain covered.
- M-1 **COMPLETE** — direct supported unit literals are resolved consistently in domain-bearing APIs with dimensional-zero preservation.
- M-2 **COMPLETE** — Piecewise boundary `value_symbolic` comes from the selected governing branch while parameters stay symbolic.
- M-3 **COMPLETE** — continuous redundant sides collapse to `at`; discontinuities retain meaningful side topology after unit normalization.
- L-series **COMPLETE** — renderer misuse, unresolved Piecewise diagnostics, Matplotlib title weight, exact rational annotation coordinates and negative-zero presentation are regression-covered.
- Task 10 risk probes remain classified **not reproduced; no product change**.
- Task 11 permanent Python 3.10–3.14 CI remains GREEN evidence with jobs `99386459903`, `99386460066`, `99386460051`, `99386460059`, `99386460063`.
- Task 12 decomposition remains complete at product commit `cee4b39e19d2f6f2c49595d8a46efcdd6f1d58ce`, with stable public imports and no behavior change.
- Runtime/package version remains **0.9.1**. No Task 13 product/solver source change exists.

## Exact next step — Task 14

Task 14 is the **0.9.2 release task**. Execute the approved plan in order: prove intentional version RED; bump every release surface to 0.9.2; run pre-wheel source gates; build and inspect the real wheel; record wheel SHA-256; run an external clean-environment smoke; run the complete installed-wheel suite with repository source unavailable; repeat the complete source suite; remove release-only temporary infrastructure while retaining permanent `ci.yml`; update this handoff with authoritative release evidence; open the release PR titled `release: EngCalc 0.9.2 audit remediation and reliability`; then **STOP before merge and request explicit user approval**.

"""
    text = text[:start] + replacement + text[end:]
    text = text.replace("- Task 13: acceptance/docs/full regression.\n", "")
    text = text.replace(
        "**Tasks 1–12 COMPLETE; Task 13 NEXT**.",
        "**Tasks 1–13 COMPLETE; Task 14 NEXT**.",
    )

    resume = text.index("## How to resume in a new conversation")
    resume_text = f"""## How to resume in a new conversation

Read this file first. Canonical released baseline remains `main@698696bb8854fa197851cdbb2f5e4c08ef22178b`, EngCalc 0.9.1. Active branch is `feature/v0.9.2-audit-reliability`; runtime/package version is still 0.9.1. Tasks 1–13 are complete. Task 13 authoritative acceptance run is `{run_id}` with 12/12 natural/audit acceptance, 10/10 plot integration and 884/884 complete source tests; no `src/` product change is part of Task 13. Permanent Python 3.10–3.14 CI remains. Task 14 is next and must perform real-wheel release validation and open the 0.9.2 PR, then STOP before merge for explicit user approval. Never invoke Codex without explicit authorization.
"""
    text = text[:resume] + resume_text
    PATH.write_text(text, encoding="utf-8")
    print("Recorded Task 13 closure context.")


if __name__ == "__main__":
    main()
