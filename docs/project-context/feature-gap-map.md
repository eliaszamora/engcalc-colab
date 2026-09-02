# EngCalc feature gap map — measured against real exercises

**Executed, not imagined.** Eighteen exercises from Estática, Mecánica de Materiales,
Análisis Estructural, diseño y matemática general were written the way an engineer would
write them — *before* checking what EngCalc accepts — and then run line by line against
`main` at EngCalc 0.10.1. Every failing line is recorded with its verbatim error.

The method matters as much as the result. This document exists because a feature list
imagined from the outside had already produced two confident recommendations that
measurement contradicted, including one of mine.

## Result

| | |
|---|---|
| exercises | 18 |
| lines executed | 132 |
| lines that failed | 24, of which **4 are cascades** — a name undefined because an earlier line failed |
| distinct gaps | **12** |
| exercises that run end to end today | **4 / 18** |

Four already run clean, and they are not trivial ones: composite section properties,
stress transformation with principal stresses and angle, **the propped cantilever by the
flexibility method** — two integrals of `M_0*M_1/(E*I)` and a solve — and **sizing a
section by solving a deflection limit for `I`**. The mathematical base is stronger than a
feature list suggests.

## What each exercise needs

| Exercise | Area | Gaps it needs closed |
|---|---|---|
| E1 reactions, simply supported beam | estática | scalar systems |
| E2 point plus distributed load | estática | scalar systems |
| E3 truss, method of joints | estática | scalar systems |
| E4 elastic curve by double integration | mecmat | indefinite integral **and** scalar systems |
| E5 maximum deflection and its limit | mecmat | first-class comparisons |
| E6 moment diagram, Macaulay brackets | mecmat | Macaulay notation |
| E7 composite section properties | mecmat | — runs |
| E8 stress transformation | mecmat | — runs |
| E9 propped cantilever, flexibility | estructuras | — runs |
| E10 load cases and combinations | estructuras | `case` / `combo` syntax |
| E11 governing envelope | estructuras | `governing()` |
| E12 flexural design check | diseño | first-class comparisons |
| E13 sizing for a deflection limit | diseño | — runs |
| E14 Euler buckling, solve for length | diseño | multi-solution solve, evaluated summation |
| E15 zone of positive moment | general | first-class comparisons |
| E16 assumptions and simplification | general | first-class comparisons |
| E17 evaluated summation of loads | general | evaluated summation |
| E18 recorded results and summary | general | `report()`, `summary()` |

## Ranking — by exercises that run *end to end*, not by exercises touched

An exercise needs **every** one of its gaps closed to run. Counting exercises a gap
touches is misleading; this counts exercises that go green.

| Close this | Exercises running end to end |
|---|---|
| today | 4 / 18 |
| **first-class comparisons** | **8 / 18** |
| **scalar equation systems** | **7 / 18** |
| evaluated summation | 5 / 18 |
| Macaulay notation | 5 / 18 |
| `case` / `combo` | 5 / 18 |
| `governing()` | 5 / 18 |
| **indefinite integral** | **4 / 18 — unblocks nothing on its own** |
| multi-solution solve | 4 / 18 |
| `report()` / `summary()` | 4 / 18 |

Blocks:

| Block | Exercises running end to end |
|---|---|
| indefinite integral + scalar systems | 8 / 18 |
| first-class comparisons alone | 8 / 18 |
| both of the above | 12 / 18 |
| plus multi-solution solve and evaluated summation | **14 / 18** |

## Two findings that change the plan

**Indefinite integral unblocks nothing by itself.** It is the only gap in that position.
E4 is the sole exercise needing it, and E4 also needs scalar systems, so building the
integral first moves the count from 4/18 to 4/18. It is a prerequisite, not a deliverable.

**First-class comparisons buy as much as the two-gap block, for one gap.** Comparisons
already exist in the grammar but only inside `piecewise(...)`; a bare `Compare` node is
rejected by the general expression validator. That single restriction is what blocks
`check(...)`, `assume(...)` and inequality solving — three separately-listed features with
one shared prerequisite — and it blocks four exercises across design, mechanics and
general mathematics.

This **corrects an earlier recommendation made in conversation**, which put indefinite
integral plus scalar systems first on the strength of the elastic-curve workflow. That
argument was built from one exercise. Measured over eighteen, comparisons return the same
for half the work, and the integral returns nothing until scalar systems exist.

## Recommended order

1. **First-class comparisons** → 8/18. One parser change unblocks `check`, `assume` and
   inequalities. Each of those three is then its own contained piece of work, and `check`
   is the one that turns a memoria into a verification.
2. **Scalar equation systems** → 12/18 cumulative. The largest single functional gap, and
   the natural way an engineer writes statics: `ΣFy = 0`, `ΣM_A = 0`.
3. **Indefinite integral**, shipped with (2), which is what makes the elastic curve
   derivable from scratch: integrate twice, then solve the boundary conditions together.
4. **Multi-solution solve and evaluated summation** → 14/18. Both small. The solve guard
   is a v0.1-era contract that says so in its own error message, not a mathematical limit.
5. Then the structural block — `case`/`combo`, `governing()`, Macaulay — and the memoria
   block — `report()`/`summary()`. Each worth one exercise here, but this sample
   under-represents them.

## API naming decision

`integral(...)` is renamed to **`integrate(...)`**, the SymPy and common convention, on
the principle of not inventing names for operations that already have recognised ones.
`integral(...)` stays as an alias so existing memorias and the documented examples keep
working; say so if a clean break is preferred instead.

`diff` keeps its name — it is already the recognised one.

## What this map does not cover

Eighteen exercises is a sample, chosen to span areas rather than to be exhaustive. It
under-represents hydraulics, circuits, dynamics and reinforced-concrete detailing
entirely, and the structural block above is measured by one exercise each. A gap that
appears once here may be far more important in practice than this count suggests — the
ranking is evidence about these eighteen, not a claim about all engineering.

Reproduce or extend it with the harness in the session scratchpad: each exercise is
plain EngCalc source, run line by line, with failures recorded rather than worked around.
