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
| E14 Euler buckling, solve for length | diseño | **written with the wrong tool** — see below |
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
| Macaulay notation | 1 | 5 / 18 — **delivered in 0.15.0, and it did move the count** |
| `case` / `combo` | 1 | 5 / 18 |
| `governing()` | 1 | 5 / 18 |
| multi-solution solve | 1 | **4 / 18** — corrected, see below |
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

### E14 was written with the wrong tool, and the ranking overstated 1.3

Measured while designing step 1.3: **`roots(...)` already solves E14 today**, returning
12.57 m - the positive Euler length, inside a physical domain, in metres. The exercise
asks `L_max = solve(eq(P_cr(Lk), 500*kN), Lk)`, which has a symmetric pair of answers and
no single value to assign. `roots` is the tool the project designed for exactly that job.

So multi-solution `solve` unblocks **no** exercise, not one, and this table said
otherwise. That is the third time an entry in this document has been wrong, and the third
time the error was in an exercise or an analysis rather than in EngCalc.

`assume` would not have helped either. Declaring the unknown positive does not filter
SymPy's answer, because the sign of `K` remains unknown - measured, not assumed.

The exercise is **left as written**. An engineer reaching for `solve` there is behaving
reasonably, and the natural expression failing is a genuine ergonomic gap even when a
different tool can do the job. What 0.14.0 changes is that the dead end becomes guidance:
the error now names `roots(...)`.

### The E4 caveat, resolved and replaced by a different one

The caveat recorded here was that SymPy omits the constant of integration, so E4's
boundary conditions would have nothing to solve for. **That turned out not to be the
problem**: `C1` is an ordinary free symbol, the engineer writes it exactly as on paper,
and 0.13.0 derives the textbook constants `C2 = 0` and `C1 = -qL³/(24 E I_z)` from the
boundary conditions.

The real blocker is elsewhere, and was found by running the exercise rather than by
reasoning about it. **A definition captures its free symbols, and `numeric(...)` resolves
symbols from the numeric context - values given with `:=` - not from the symbolic
namespace where a solved constant lands.** So `v(x)`, defined before the constants are
known, keeps the symbols `C1` and `C2` and cannot be evaluated numerically afterwards:

```text
y = 2*k ; k = 5    ; z = y        ->  2*k      a definition captures, it does not refer
y = 2*k ; k = 5    ; numeric(y)   ->  refuses, asking for a numeric value
y = 2*k ; k := 5*kN ; numeric(y)  ->  10 kN    resolved from the numeric context
```

E4 therefore derives its elastic curve symbolically end to end and stops one step short
of a number. That step is a gap of its own, newly measured, and is not what 1.2 was for.

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
