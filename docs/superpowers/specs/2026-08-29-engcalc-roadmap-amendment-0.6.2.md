# EngCalc Evolution Roadmap Amendment — 0.6.2 Numeric Ergonomics

_Date: 2026-08-29_

## Why this amendment exists

The original evolution roadmap was written when version **0.6.1** was reserved for symbolic/numeric ergonomics and diagnostic quality. During pre-roadmap product work, EngCalc 0.6.1 instead became the presentation-focused release merged through PR #25, including semantic MathJax spacing, compact plot/envelope characteristic labels, the `result(...)` presentation command, and final renderer/plotting corrections.

PR #25 merged to `main` as EngCalc **0.6.1** at merge commit:

```text
0db200a2fe691ec8fc54eb2bd0374cc9289eff2b
```

A post-merge capability inspection confirms that the original roadmap's numeric-ergonomics block is not fully implemented in `main`: direct unit-bearing arguments inside `numeric(user_function(...))` still cross the symbolic visitor first, and the centralized corrective diagnostic-hint layer is still absent.

## Version reconciliation

The original roadmap milestone:

```text
0.6.1 — symbolic/numeric ergonomics and diagnostic quality
```

is hereby renumbered to:

```text
0.6.2 — symbolic/numeric ergonomics and diagnostic quality
```

Its functional scope is unchanged.

All references in `2026-08-28-engcalc-evolution-roadmap-design.md` and `2026-08-28-engcalc-evolution-roadmap-implementation.md` to the original **Task 1 / 0.6.1 numeric ergonomics** milestone must be interpreted according to this amendment as **Task 1 / 0.6.2 numeric ergonomics**.

Specifically:

- suggested implementation branch becomes `feature/v0.6.2-numeric-ergonomics`;
- release-closing version bump becomes `0.6.2`;
- release commit wording becomes `release: EngCalc 0.6.2 numeric ergonomics`;
- references to preserving the previous suite now mean preserving the merged **0.6.1** baseline;
- the standard source/wheel/installed-wheel/repeated-source release gate remains unchanged.

## Required 0.6.2 behavior

The original Task 1 requirements remain authoritative:

- `numeric(M(2.5*m))` works directly when the function argument is a complete numerical/unit expression;
- `numeric(V(L/2))` works when `L` has a numerical value;
- `numeric(R(4*tonf/m))` works directly;
- `numeric(M(x))` remains a valid partial evaluation when `x` is intentionally unresolved;
- `solve(expression, unknown)` remains the preferred shorthand for `expression = 0` and explicit `eq(left, right)` remains supported;
- errors distinguish unknown numeric names, incompatible function units, unresolved numeric symbols and unsupported symbolic/numeric crossings;
- corrective examples are included when EngCalc can determine a safe correction;
- `diagnostic_hint(code: str, **context)` remains the planned centralized source for corrective hints;
- no scalar-math functions, multi-argument user functions or tables are added in 0.6.2.

## Dependency order after amendment

```text
0.6.1 visual/presentation release — MERGED
   ↓
0.6.2 numeric ergonomics + diagnostics
   ↓
0.7.0 scalar engineering mathematics
   ↓
0.7.1 multi-argument functions + generalized partial evaluation
   ↓
0.7.2 tables
   ↓
... remaining roadmap unchanged ...
```

Version **0.7.0 and all later roadmap version numbers remain unchanged**.

## Implementation baseline

Task 1 / 0.6.2 must branch from current merged `main`, not from the historical 0.6.0 tree referenced by the original plan. The 0.6.1 release is a required compatibility baseline and its accepted behavior—including positive moment downward, compact characteristic labels, `result(...)`, and semantic 4/8/16 MathJax spacing—must remain green throughout 0.6.2.

This amendment is authoritative wherever it conflicts only with the original Task 1 version number, branch name, baseline wording or release-closing version. All technical Task 1 requirements remain otherwise unchanged.
