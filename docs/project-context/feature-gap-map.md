# EngCalc feature gap map — measured against real exercises

**Executed, not imagined.** Eighteen exercises from Estática, Mecánica de Materiales,
Análisis Estructural, diseño y matemática general were written the way an engineer would
write them — *before* checking what EngCalc accepts — and then run line by line against
`main` at EngCalc 0.10.1. Every failing line is recorded with its verbatim error.

The method matters as much as the result, and this document is its own best argument.
Its first version clustered failures by each line's *first* error and concluded that
first-class comparisons were the highest-return gap - which was wrong, and which
contradicted a recommendation that had been right. A second, automated attempt to fix
that introduced fresh errors of its own. The numbers below are hand-verified from twenty
failing lines. **Automating the analysis of a measurement is another place to be
confidently wrong.**

## Result

| | |
|---|---|
| exercises | 18 |
| lines executed | 132 |
| lines that failed | 24, of which **4 are cascades** — a name undefined because an earlier line failed |
| distinct gaps | **12** |
| exercises that ran end to end when measured | **4 / 18** |
| **after step 1.1, scalar equation systems** | **7 / 18** |

Four already run clean, and they are not trivial ones: composite section properties,
stress transformation with principal stresses and angle, **the propped cantilever by the
flexibility method** — two integrals of `M_0*M_1/(E*I)` and a solve — and **sizing a
section by solving a deflection limit for `I`**. The mathematical base is stronger than a
feature list suggests.

## What each exercise needs

Determined **by hand**, from the verbatim error of every failing line plus reading the
line. The first automated attempt clustered by each line's *first* error, which is wrong:
`check(d_max <= d_adm)` fails on `Compare`, and would fail again on `check` even if
comparisons were allowed. A second automated attempt introduced further errors. Twenty
failing lines is small enough to analyse by hand, and that is what these numbers are.

| Exercise | Area | Gaps it needs closed |
|---|---|---|
| E1 reactions, simply supported beam | estática | scalar systems |
| E2 point plus distributed load | estática | scalar systems |
| E3 truss, method of joints | estática | scalar systems |
| E4 elastic curve by double integration | mecmat | indefinite integral **+** scalar systems |
| E5 maximum deflection and its limit | mecmat | comparisons **+** `check()` |
| E6 moment diagram, Macaulay brackets | mecmat | Macaulay notation |
| E7 composite section properties | mecmat | — runs |
| E8 stress transformation | mecmat | — runs |
| E9 propped cantilever, flexibility | estructuras | — runs |
| E10 load cases and combinations | estructuras | `case` / `combo` syntax |
| E11 governing envelope | estructuras | `governing()` |
| E12 flexural design check | diseño | comparisons **+** `check()` |
| E13 sizing for a deflection limit | diseño | — runs |
| E14 Euler buckling, solve for length | diseño | multi-solution solve |
| E15 zone of positive moment | general | comparisons **+** inequality-capable solve |
| E16 assumptions and simplification | general | comparisons **+** `assume()` |
| E17 evaluated summation of loads | general | evaluated summation |
| E18 recorded results and summary | general | `report()` **+** `summary()` |

## Ranking — exercises that run end to end, against pieces of work

An exercise needs **every** one of its gaps closed. Counting exercises a gap merely
touches is what produced the wrong answer the first time.

| Block | Pieces of work | End to end |
|---|---|---|
| today | — | 4 / 18 |
| **scalar equation systems** | **1** | **7 / 18** |
| **scalar systems + indefinite integral** | **2** | **8 / 18** |
| comparisons + `check()` | 2 | 6 / 18 |
| comparisons + `check()` + `assume()` + inequality solve | 4 | 8 / 18 |
| Macaulay notation | 1 | 5 / 18 |
| `case` / `combo` | 1 | 5 / 18 |
| `governing()` | 1 | 5 / 18 |
| multi-solution solve | 1 | 5 / 18 |
| evaluated summation | 1 | 5 / 18 |
| `report()` + `summary()` | 2 | 5 / 18 |

**Neither first-class comparisons nor the indefinite integral unblocks a single exercise
on its own.** Both are prerequisites. Comparisons gate `check`, `assume` and inequality
solving; the indefinite integral is needed only by E4, which also needs scalar systems.

**Scalar equation systems is the one gap that pays alone**: three exercises, one piece of
work, and it is how statics is actually written — `ΣF = 0`, `ΣM_A = 0`.

Adding the indefinite integral to it reaches 8/18 for two pieces of work, and makes the
elastic curve derivable from scratch. The comparisons block reaches the same 8/18 and
costs four.

### One caveat on E4 that the count hides

`theta(x) = integral(M(x)/(E*I), x)` as an engineer writes it carries an implied constant
of integration. SymPy's indefinite integral omits it, so the two boundary conditions in E4
have nothing to solve for unless EngCalc has a story for integration constants. Closing
both gaps may still leave E4 short. Recorded because the count says 8/18 and that number
assumes E4 completes.

## Recommended order

1. **Scalar equation systems** — **DONE in 0.12.0. The map predicted 7/18 and the
   re-measurement returned exactly 7/18**: E1, E2 and E3 now run end to end with zero
   broken lines. Re-run `python tools/gap_map.py` to confirm.
2. **Indefinite integral**, shipped alongside — 8/18, and the elastic curve becomes
   derivable rather than quoted. Resolve the integration-constant question here.
3. **Comparisons, then `check()`** — 6/18 on its own but `check` is what turns a memoria
   into an auditable verification, which is worth more than the exercise count says.
4. `assume()` and inequality solving, on the comparison groundwork — 8/18 cumulative for
   that branch.
5. Then multi-solution solve, evaluated summation, and the structural and memoria blocks.

## API naming decision

**Done in 0.11.0.** `integral(...)` is renamed to `integrate(...)`, the SymPy and common
convention, on the principle of not inventing names for operations that already have
recognised ones. `integral(...)` stays as a permanent alias, because existing memorias and
the documented worked examples use it.

`diff` keeps its name — it is already the recognised one.

## What this map does not cover

Eighteen exercises is a sample, chosen to span areas rather than to be exhaustive. It
under-represents hydraulics, circuits, dynamics and reinforced-concrete detailing
entirely, and the structural block above is measured by one exercise each. A gap that
appears once here may be far more important in practice than this count suggests — the
ranking is evidence about these eighteen, not a claim about all engineering.

Reproduce or extend it with `python tools/gap_map.py`. Each exercise in
`tools/gap_map_exercises.py` is plain EngCalc source, run line by line, with failures
recorded rather than worked around. The harness reports *where* each line breaks; deciding
what a broken line needs is done by hand, for the reason given at the top.
