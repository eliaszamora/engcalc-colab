# EngCalc Current Project Context

> **Read the block directly below, then `NEXT.md`.** Everything after it was last
> updated at 0.13.0 on `9a9d6e3` and describes a tree that no longer exists. Its
> *approved behaviour* and *evidence hierarchy* sections are still in force and are
> regression requirements; its baseline numbers, release history and open-issue list are
> not — do not quote its counts.

## Where things stand today

_2026-09-25._

| | |
|---|---|
| released | **0.38.0** - #324, `a53613d`, carrying #322 (`91c74dd`) and #323 (`333d54f`); six jobs and both qualification runs green on it, verified after its merge (below) |
| before that | **0.37.0** - #320, `4795c47` |
| merged, not released | #326 `% if`, #327 `=` values, #328 italic, #329 `% for`, #330 `% while`, #331 `solve` in a range, #332 named `numeric`, #333 one spacing rule + KaTeX letter (`8f40539`), #334 room under a fraction row |
| open | nothing |
| default suite | **3117 passing** (SymPy 1.14 and 1.13.3), about a minute with `-n auto`; CI six jobs green on #334 |

**0.31.15 is closed** (#237, `ebf5ca9`): the audit of 0.31.14 — `numeric(w, 1/s)`, the weekly
suite, dead code, the multiplicity label, 51 stale branches deleted. Verified after its
merge: a clean `git+https` install of `ebf5ca9` in a Colab-like venv reported 0.31.15,
upgraded nothing and read all three corrections outside the repository.

**What 0.31.16 is: what was still pending.** On 2026-09-22 he wrote *"abarca lo pendiente,
tienes mi aprobación y si para abordar lo que esté pendiente o que necesite mi respuesta
según tu criterio"*. Each item was checked on the page before deciding:

1. **#238 (`614d582`), a unit in an eigenvalue is typeset as a unit.** The "known" note that
   `_analysis_scalar_latex` had no unit literals was not theoretical: `A = [2*kN/m, 0; 0,
   3*kN/m]` drew `λ = 2 kN/m` with an italic metre. The engine now asks a set's source
   matrix for its unit names and the renderer hands them to both eigen printers, the vectors
   and the `det(A - λI) = 0` matrix. 5 contracts, 4 RED before, mutation 5/5.
2. **#239 (`67b4efd`), a frequency can be written in hertz** — the question he had not
   answered. `Hz` can be written and asked for, never chosen: measured first with the alias
   patched in, `2*pi*f` already read `1/s`, and a contract pins it. 5 contracts, 4 RED
   before, mutation 4/4.
3. **#240 (`6fae2b0`), a unit that becomes a value says so.** Worse than recorded:
   `k := 2000*kN/m` then `m := 500*kg`, the usual one degree of freedom, drew
   `k = 4.00 kN/kg` the second time the cell ran, in silence. Which meaning was wanted cannot
   be known, so the rule stays and the two moments a name changes meaning are printed. 12
   contracts, 7 RED before, mutation 11/11 (the survivor of the first pass, a third run
   falling silent, now pinned).
4. **A record corrected**: "a non-zero literal branch keeps its written form" was carried
   here as known after #224 had fixed it in 0.31.11; the page shows `(5.00 kN/m)`.
5. **The README opens with how to start** in Colab — the two cells, and never
   `--force-reinstall` — above the "Current version" line, so the release procedure is
   unchanged. The audit had found install instructions 2200 lines down.
6. **Left as it is, deliberately:** `A_c = 0.30*m*0.60*m` written `0.3 · 0.6 m · m`. It is
   correct, and keeping the typed zeros would need a float that remembers how it was typed.

No page of the thirteen moves; the harness's two-storey dynamics sheet, which writes the
metre and then names a mass `m`, prints the new line.

Release evidence, on the release commit's tree:

- the seven version assertions RED before the bump and GREEN after; source suite 2567,
  twice;
- a wheel built from `git archive` of the commit, its 29 package files byte-identical to
  `src`;
- installed in a clean Python 3.12 venv holding Colab's pins (ipython 7.34.0, numpy 2.2.6,
  matplotlib 3.10.0, sympy 1.13.3), it adds Pint 0.26.1 and four small dependencies and
  **upgrades nothing**;
- outside the repository, through `%load_ext`, a smoke of fifteen checks: the frame still
  reads `EA` and answers 71689.33 kgf/cm and 0.0168 s; `1/s`, `rad/s`, no `m=1`,
  `multiplicity 2`; an upright unit in an eigenvalue; `5.00 Hz` and `2πf` in `1/s`; both
  notices on the single degree of freedom, first run and second; nothing printed by the
  consistent sheets;
- the whole suite against the installed wheel, from a copy of the tree with no `src/`: all
  pass except `test_the_ipython_surface_stays_small`, which reads `src/.../magic.py` by path
  and passes when handed the wheel's own copy;
- the thirteen sheets render byte-identical from the wheel and from the working tree.

**0.31.16 verified after its merge**: six jobs and both qualification runs green on
`131137d`, and a clean `pip install --upgrade git+https://github.com/eliaszamora/engcalc-colab.git@main`
in a Colab-like venv resolved to `131137d`, reported 0.31.16, upgraded nothing, installed 29
files byte-identical to `src`, and passed the fifteen-check smoke outside the repository.

**NEXT.md's "still open" list, re-checked on the page on 2026-09-22** (it had not been
since 0.29.2): *a modulus derived from MPa prints GPa* was closed by #122 — `G = E/2.6`
reads `76923.08 MPa`; *a wide substitution is split into additive terms* is still real —
`phiMn = phi*As*fy*(d - a/2)` over definitions of `d` and `a` substitutes into five rows —
and `keep` on those definitions avoids it, as RC-3 intended.

### The order of a sum — #243, merged with his yes, released as 0.31.17

Found re-checking NEXT.md's list: a sum was printed in SymPy's order, so
`d = h - cover - db_st - db/2` read `- cover - db/2 - db_st + h` and his frame wrote
`(- x_1 + x_2)`. Asked on 2026-09-22 he answered *"sí me molesta eso de ver primero el
- x1 + x2 en vez de x2 - x1"* and *"procede"*; I had promised to measure rules the way #228
did and show every moved row before merging.

Four rules, measured on the thirteen sheets and the eighteen gap-map exercises (A, F and
G move the same 44 rows there, D four more) and on the shapes that separate them:

| rule | polynomial `- qL³x/24 + qLx³/12 - qx⁴/24` | effective depth | `- a + b - c` |
|---|---|---|---|
| A, first positive term leads | broken: powers 3, 1, 4 | `h - cover - db/2 - db_st` | `b - a - c` |
| D, positive terms first | broken, and 4 more rows move | as A | as A |
| F, read backwards | kept | `h - db_st - db/2 - cover` | left as it was |
| **G, chosen** | **kept** | **`h - cover - db/2 - db_st`** | **`b - a - c`** |

G: a sum ordered by the powers of a name is read backwards when that opens it with a plus;
any other sum lets its first positive term lead. One function, `_ordered_sum_terms`, used
by the printer and by both term-by-term paths — the definition and its substitution row
came from different places. **#243**, this branch: 9 contracts, 6 RED before; mutation 7/7
(A alone and F alone each killed by the contract that refutes it). Moves 42 rows on the
three frame pages (14 per palette, each the same symbols and minus signs reordered), 2 in
the exercises (E6's Macaulay bracket `<x - a>`, E9's compatibility equation) and 2 in the
README's force-method example (`Δ_B = L³V_B/3EI - qL⁴/8EI`). Six existing tests pinned the
old order and were rewritten with a note each; two of them used the README's propped
cantilever to exercise row wrapping, which no longer wraps (its result is now one compact
row), so they carry a six-load integral that wraps either way. Suite 2576.

He saw every row #243 moves and answered *"Tienes mi aprobación"* (2026-09-22). Merged as
`389a251`; six jobs and both qualification runs green on it.

Release evidence for 0.31.17, on the release commit's tree:

- the seven version assertions RED before the bump and GREEN after; source suite 2576,
  twice;
- of the thirteen sheets, only the frame moves against 0.31.16 — fourteen rows in each of
  its three palettes;
- a wheel built from `git archive` of the commit, its 29 package files byte-identical to
  `src`; installed in a clean Python 3.12 venv holding Colab's pins it adds Pint 0.26.1 and
  four small dependencies and **upgrades nothing**;
- outside the repository, through `%load_ext`, eighteen smoke checks: the fifteen of 0.31.16
  plus the frame writing `(x_2 - x_1)`, an effective depth opening with `h` in its
  definition and its substitution, and a polynomial keeping its powers in order;
- the whole suite against the installed wheel from a copy of the tree with no `src/`: all
  pass except `test_the_ipython_surface_stays_small`, which reads `src/.../magic.py` by path
  and passes when handed the wheel's own copy;
- the thirteen sheets render byte-identical from the wheel and from the working tree.

**0.31.17 verified after its merge**: six jobs and both qualification runs green on
`b02b9b0`, and a clean `pip install --upgrade git+https://github.com/eliaszamora/engcalc-colab.git@main`
in a Colab-like venv resolved to `b02b9b0`, reported 0.31.17, upgraded nothing, installed 29
files byte-identical to `src`, and passed the eighteen-check smoke outside the repository.

### What Calcpad has, measured against EngCalc — 2026-09-23

He asked whether EngCalc has Calcpad's capabilities. Calcpad itself is no longer open
source; CalcpadCE (`imartincei/CalcpadCE`, MIT, C#) continues 7.6.2. Its quick reference was
read and each EngCalc counterpart run on 0.31.17, not recalled. Same core: formula →
substitution → result, units with conversion (`ksi`, `kip`, `ft`, `in` work as targets),
numeric roots, integrals without a closed form (`∫₀¹ e^{-x²} cos x³ dx = 0.71`), sums,
matrices, eigenvalues, plots. EngCalc only: a CAS — symbolic `integrate`/`diff`/`solve`,
systems, inequalities, `assume` — Macaulay brackets, `governing`, `envelope`, load cases and
combinations that keep their factors, Colab. CalcpadCE only, each rejected by `%%eng` today:
`min`/`max`, `round`/`floor`/`ceiling`, `mod`, `if`/`switch` as functions, `line`/`spline`
interpolation, `$Product`, loops and `#if` blocks, complex numbers, `#input` forms,
`#read`/`#write` CSV and Excel, `$Map` colour maps, `#include`/macros, `lsolve`/`svd` and the
other decompositions, export to Word/PDF. A 30×30 stiffness `solve` plus `eigenvals` takes
1.7 s here (exact SymPy); fine for study, not for a model of thousands of freedoms.

**Found by the comparison, fixed in 0.31.18 (#247).** `z := sqrt(-4)` was stored as `2i` and
the page failed on it with a raw `TypeError` (`float()` of a complex in `_magnitude_text`):
a traceback in place of the whole cell, the rows before it too. Twelve paths, all through a
power. He approved on 2026-09-23 (*"Procede según lo que tú me recomiendes"*) a clear
message, RED before and GREEN after, released as 0.31.18.

The rule: a value with no real result is refused where it is made — `_real_power` in
`numeric.py`, used by the three places a power is made, and domain checks for `log`,
`asin`, `acos` — in one line naming the operation and the value, with the rows before it
shown. The refusal is `NoRealValueError(EngEvaluationError)`, a type of its own because
`roots` must read it as a candidate outside the real domain (`±sqrt(-a)` for `x^2 + a`),
which it used to discard by catching the `TypeError`; the first draft without the type
failed 12 quality tests. 32 contracts, 22 RED before; mutation 10/10; suite 2608; deep 53;
the thirteen sheets and eighteen exercises byte-identical to 0.31.17.

Known, found with it and not caused by it: `extrema(sqrt(x), x, -1, 4)` reports x = 4 as
both global max and global min and misses the minimum at x = 0.

### 0.32.0 — min, max and a table

**0.31.18 verified after its merge**: six jobs and both qualification runs green on
`9be53ad`; a clean `git+https` install of `main` in a Colab-like venv resolved to `9be53ad`,
upgraded nothing, installed 29 files byte-identical to `src` and passed 24 smoke checks.

He approved on 2026-09-23 the two functions recommended after the Calcpad comparison
(*"Procede según lo que tú me recomiendes"*) and, having seen the table of rows, the
coefficient rule (*"Tienes mi autorización y aprobación para avanzar con lo que se necesita
hacer, merge y sí en el fix"*). A first `gh pr merge 249` had been refused by the session's
permission classifier; his message authorised it, and the three were merged in order, each
on its own green CI, the stacked ones moved onto `main` and their trees checked identical
to the ones tested.

- **#249 (`73e9978`) `min`/`max`** in the order the code writes them.
  `min_max.WrittenMin/WrittenMax` build SymPy's real lattice and put the arguments back
  (through the subclass, `max(3, 5)` was 3 — pinned). `numeric` works each limit out
  before the one that governs, unless that repeats the substitution; `result` shows none.
  `:=` takes them. 14 contracts; mutation 14/15, the survivor removed as furniture.
- **#250 (`de88808`) `interp(x, [x_i], [y_i])`**: the table as written, the segment used
  worked out in the table's unit, refusal outside it and for `:=`. Its derivative stays
  unevaluated (SymPy recursed through the matrices; `plot` found it). 21 contracts;
  mutation 17/17. Known: `extrema` over it answers in one line.
- **#251 (`1cff502`) a coefficient printed as typed**: at most six significant figures in
  plain notation is printed as typed, longer is rounded as before. `0.125 q L²`, not
  `0.12 q L²`; ACI's φ table `[0.002, 0.005]`, not `[2.00×10⁻³, 0.01]`. The contract that
  pinned `0.1234` → `0.12` now uses `1234.56789`. 8 contracts; mutation 5/5 after two
  thin-margin cases were added.

Of the thirteen reference sheets and eighteen gap-map exercises, nothing moves with the
three together. Suite 2657.

### 0.32.1 — what extrema could not see

**0.32.0 closed** (#253, `ec90dfc`), verified after its merge and recorded by #254.

He asked on 2026-09-23, after seeing 0.32.0 in Colab, for the four open items to be
addressed (*"aborda los puntos 1 2 3 y 4 según tus recomendaciones y si se deben tomar
decisiones las dejo bajo tu mano"*), and asked why the function is called `extrema`: it is
English, the plural of *extremum*, as *maxima* is of *maximum*.

- **1. #255 (`cc18299`) `extrema` reads its function across the whole domain.** A domain
  end the analysis could not evaluate was dropped in silence: `sqrt(x)` on [-1, 4] named
  x = 4 global max and min, `1/x` on [0, 2] named x = 2 the global max. A function with no
  real value in the domain is refused on `plot`'s grid (only for functions that can leave
  the reals); a singular end is read from its one side. 11 contracts; mutation 9/9.
- **2. #258 `extrema` over an `interp`**: read as its piecewise (`Interpolation.as_piecewise`),
  the domain checked against the table first. Mutation 5/6, the survivor equivalent. A
  restriction to `interp(x, ...)` was measured, cost `interp(x/2, ...)`, and was removed.
  On the way, two defects on `main`, each its own PR:
  - **#256 (`4087749`) a unit alone in a sum** — `1*kN + 4*kN*x/m` failed in `numeric` and
    `table` with Pint's words; it made a piecewise in kN drop its x = 0 end in `extrema`.
  - **#257 (`59d849d`) a plot reads a unit written in its function** — `V(x) = 30*kN - q*x`
    could not be drawn (KeyError in `piecewise_segment_starts`).
- **3. `0.90` → `0.9`: decided not to do.** The number reaches EngCalc as a float that
  cannot remember its zero. Keeping the typed spelling means carrying it from the parser
  into SymPy, and a Float subclass holding it is unsafe: SymPy caches expressions by value,
  so one statement's spelling could print in another. A trailing zero is not worth that.
- **4. More Calcpad functions: decided not to do**, as recommended: they pull EngCalc
  towards a programming language. `ceiling` (number of bars) is the first candidate if a
  sheet of his asks for it.

The 13 reference sheets and 18 exercises are byte-identical to 0.32.0 through all four.
Suite 2684; deep 53.

### 0.32.2 — a breakpoint and a metre

**0.32.1 closed** (#259, `177b4be`), verified after its merge and recorded by #260.

He looked at 0.32.1 in Colab on 2026-09-23 and asked for the findings to be corrected
(*"corrige los hallazgos encontrados"*). Two, both on his page:

- **#261 (`4f82b9d`) a breakpoint is called a breakpoint.** The peak of a table, x = 1
  inside 0 to 2, read `boundary, local max, global max`: every point where a piecewise law
  changes went through the helper that reads the domain ends and took their word. Each
  caller now names its point; a law changing on a domain end stays `boundary`. The role is
  only written, never read. 5 contracts; mutation 5/5.
- **#262 (`4dffd91`) a unit alone is written with its one.** `1*m` folds to `m` before
  printing; the written form already kept `1 m`, so only paths printing the value were
  wrong - arguments, tables, `numeric` formula rows, characteristic rows, matrices
  (`-kN/m`). The printer tracks each node's parent and writes a unit (or product or power
  of units, with its sign) standing where a quantity stands as the explicit product with
  one; a factor is left alone. Characteristic results now carry `unit_literals`, which
  their rows never had. Two eigen contracts updated with notes. 13 contracts; mutation
  6/6; a `1/m` guard measured to change nothing and removed.

Left, deliberately: `x = 0 (0.00)` repeats a plain number (the characteristic's exact-form
convention); a `0*m` in a table prints `0` (lost at parse, not at print).

No row of the 13 sheets or 18 exercises moves. Suite 2701; deep 53.

### 0.32.3 — what a derivation showed

**0.32.2 closed** (#263, `2da4dea`), verified after its merge and recorded by #264.

He asked on 2026-09-23 for the matrix derivation of the bar and frame elements (`F = K u`,
horizontal, inclined, vertical) done with EngCalc, run and audited on the page, and handed
over in as few cells as possible; then the ultra review (draft #265, not to be merged).
Writing and reading it found two defects, each fixed before the sheet was handed over:

- **#266 (`0eb15a7`) a variable named like a unit is not given a one** - a regression of
  0.32.2: `T = [c, s; -s, c]` read `[c, 1 s; -1 s, c]`, `N + P` read `1 N + P`. The engine
  now collects `measured_units` (aliases written in a whole product of numbers and units,
  matrix-literal entries included); the magic hands them to the printer through the
  `MEASURED_UNITS` context variable for the cell; the one goes only to them. 10 contracts;
  mutation 6/6.
- **#267 (`eb3fd61`) the formula beside a value is the whole formula** - older, and worse:
  `y = 2*diff(x^2, x)` read `d/dx x² = 4x`, `integrate(x, x, 0, 1) + 1` read `∫ = 3/2`, the
  elastic curve lost its `C1`, a matrix of derivatives read as its last. `_shown_input`
  re-reads a statement whose call is not the whole statement with the evaluator in a
  `showing` mode. 12 contracts; mutation 8/8. Gap-map exercise E4 moves: its rows gain the
  `C₁`, `C₂` they had lost.

Seen, not changed: `expand`/`simplify` substitute kept names (the sheet uses the plain
product instead); a matrix of integrals is drawn entry by entry and can be wide (the sheet
integrates the ten bending terms one by one).

The 13 reference sheets are byte-identical through both. Suite 2723; deep 53.

### Exact next step

**0.33.0 is closed.** On the release commit `b3ee263`: the seven version assertions RED
then GREEN; source suite 2738, twice; a wheel from `git archive`, 31 files byte-identical
to `src`; in a clean Colab-like venv it upgrades nothing; 54 smoke checks outside the
repository (the derivation reads `E A` throughout, `As*fy` reads `As fy`); the suite
against the wheel, 2738; the 13 sheets and 18 exercises identical between wheel and tree
and to the approved #270 branch. After its merge **the push to `main` triggered no
workflow at all** (the one before it, `7851f14`, did); CI and the deep gate in
qualification mode were dispatched by hand on `7bfd026` and all six jobs and both
qualification runs are green. A clean `git+https` install of `main` resolved to
`7bfd026`, upgraded nothing, installed 31 files identical to `src`, passed the 54.

**0.33.0 - a product keeps the order it was written in** (#270, approved by him with
every moving row in front of him on 2026-09-23: *"Apruebo, tienes mi Sí"*). Reading the derivation he asked why `E*A` read
`AE`: SymPy stores `A*E` as it reads, and `_engineering_factor_key` fell to the alphabet for
two capitals with no value. He said he wants the written order. The engine records, per
product, which name was written before which (`record_written_order`, first writing kept,
cleared by `reset`); the magic hands it to the printer as `WRITTEN_ORDER`; `_in_written_order`
moves only names, among the positions names hold, so numbers stay first and units keep the
page's order; a product never written (`transpose(T)*k*T`) takes the order its names were
first written together in, and names never written together keep the old rule. 14
contracts; mutation 10/10; suite 2738. Rows that move: one reference row (memoria
`L R_B` → `R_B L`, as written), E1 and E2 (`a P` → `P a`, three rows), the derivation
(21 `A E` → `E A`), and eight contracts updated with notes - among them his earlier choice
`q*x*L/2` → `q L x` now reads `q x L` as written (the coordinate-last rule still answers
for products the sheet did not write), and ACI's `As*fy` now reads `As fy`. Sums keep the
page's order. Released as 0.33.0 (#271).

**0.33.1 - a matrix row has room** (#273, merged with his yes on 2026-09-23:
*"Tienes mi aprobación"*). Reading `k_v` he asked whether the entries were touching
vertically: `_matrix_from_cells_latex` joined rows with a bare `\\`, and display fractions
stood 5.7 px apart at 14 px type (6.8 px at the page's 17 px) against ≥14 px between
columns. Shown `\\`, `4pt`, `6pt`, `8pt` side by side, he chose the recommended `6pt`
(*"Procede con tu recomendación"*): rows as far apart as columns, 14.2 px at 14 px and
16.9 px (1 em) at 17 px on his derivation. `_latex_visual_width` reads `\\[..]` as no
width. 7 contracts; nine contracts pinned the bare `\\` and were updated with notes (one
test parser read the `6` of `[6pt]` as a mode entry). Moves: the separator only - dinámica
6, pórtico 96 × 3 palettes, the derivation 60; every other page and all 18 exercises
byte-identical. Suite 2745. Released as 0.33.1 (#274).

**0.33.1 is closed.** On the release commit `c10a982`: version assertions RED then GREEN;
source suite 2745, twice; wheel from `git archive`, 31 files identical to `src`; clean
Colab-like venv upgrades nothing; smoke 56/56 outside the repository (60 derivation rows
`\\[6pt]` apart, no bare separator); suite against the wheel 2745; 13 sheets and 18
exercises identical to the approved #273 branch. After its merge the push triggered CI
and the deep gate this time: six jobs and both qualification runs green on `d225e48`; a
clean `git+https` install of `main` resolved to it, upgraded nothing, 31 files identical
to `src`, smoke 56/56.

**0.33.1 was calibrated in the wrong renderer; 0.33.2 corrects it** (#276, merged with
his yes on 2026-09-23). He ran 0.33.1 in Colab and `k_v` still read tight.
Checked in his own Colab through the Claude-in-Chrome extension (a scratch cell, nothing
saved in his notebook): the runtime was 0.33.1 and the separator reached the page, but
Colab's renderer leaves no space between matrix rows of its own, where the preview's
MathJax 3 leaves 5.7 px - so `6pt` was a thin gap there. Drawn in Colab bare, 6, 10, 12
and 14 pt, `12pt` put the rows about as far apart as the columns; he chose it (*"procede
con tu recomendación"*). In the preview it measures 27-29 px (1.6 em). The five contracts
that only needed *some* separator now read `_MATRIX_ROW_SEPARATOR` instead of a literal.
Moves the separator only (6pt to 12pt): dinámica 6, pórtico 96 × 3, the derivation 60.
Suite 2745. Lesson: a presentation measurement is taken in Colab, not only in the preview.
Released as 0.33.2 (#277).

**0.33.2 is closed.** On the release commit `fb61336`: version assertions RED then GREEN;
source suite 2745, twice; wheel from `git archive`, 31 files identical to `src`; clean
Colab-like venv upgrades nothing; smoke 56/56 (60 derivation rows `\\[12pt]` apart);
suite against the wheel 2745; 13 sheets and 18 exercises identical to the approved #276
branch. After its merge: six jobs and both qualification runs green on `a8955a3`; a clean
`git+https` install resolved to it, upgraded nothing, 31 files identical, smoke 56/56.
**And in his Colab**, driven through the Claude-in-Chrome extension: session restarted,
his own install cell reported 0.33.2, his derivation cell re-run - `k_b` and `k_v` read
with rows as far apart as columns. A plain-number matrix (`k_bl`) reads roomier; noted,
not changed. Scratch cells used for the calibration are not saved in his notebook.

**0.33.3 - a matrix has room in KaTeX** (#279, merged under his "lo dejo a tu criterio"). He asked
whether the space *between* matrices had been checked, and to deal with what I had noted
and left (plain matrices read loose at 12pt), "a tu criterio". Checked in his Colab: two
matrices one above the other touched (`T_f` on `K_f`, `K_22c`/`F_c`/`d_c`). Asked from
inside an output: **Colab typesets with KaTeX 0.16.28** (gstatic), not MathJax; KaTeX
reads `\\[len]` as LaTeX's `\@argarraycr` - a minimum depth, nothing added to a deeper row
- so no row spacing separates two matrices (`24pt` still touched under a 4-row one).
Reproduced exactly with KaTeX 0.16.28 locally. Fix: `_row_break` puts a spacer row
(`\rule{0pt}{0.7em}`, as `_computed_block` uses) wherever the row above or below holds a
matrix; inside a matrix a boundary is `12pt` when either row holds something tall
(`_TALL_CELL`: fractions, big operators, nested arrays) and `3pt` otherwise (balanced in
Colab). `conftest.without_spacer_rows`; `block_text` drops spacer rows (a reader sees no
row). Verified in his Colab with the branch's own LaTeX for `T_f`/`K_f`,
`K_22`/`F_h`/`d_h`, `K_22c`/`F_c`/`d_c`. Mutation 7/7; suite 2760. Moves room only:
dinámica, pórtico × 3, the derivation. Released as 0.33.3 (#280).

**0.33.3 is closed.** On the release commit `24699ff`: version assertions RED then GREEN;
source suite 2760, twice; wheel from `git archive`, 31 files identical to `src`; clean
Colab-like venv upgrades nothing; smoke 58/58 (derivation: 28 tall row boundaries, 32
plain, 16 spacer rows, `T_f` kept apart from `K_f`); suite against the wheel 2760; 13
sheets and 18 exercises identical to the #279 branch. After its merge: six jobs and both
qualification runs green on `1ed3831`; a clean `git+https` install resolved to it,
upgraded nothing, 31 files identical, smoke 58/58. **In his Colab** (session restarted,
his install cell reported 0.33.3, his derivation re-run): `T_b`/`K_b`, `T_f`/`K_f`,
`K_22c`/`F_c`/`d_c` apart; plain matrices compact; fraction matrices keep 12pt.
Lesson recorded: Colab is KaTeX 0.16.28 - calibrate presentation against it (a local
page with KaTeX 0.16.28 from jsdelivr reproduces Colab exactly).

**The ultra review ran (2026-09-24) - five findings, each reproduced on 0.33.3 by running
it** (scratchpad `ultra_probe.py`). Merged with his yes: branch
`fix/what-the-ultra-review-found`, `tests/test_what_the_ultra_review_found.py` (8, 7 RED on
0.33.3); suite 2772 with option A; 13 sheets, 18 exercises and the derivation byte-identical to 0.33.3.
1. *A failed line still taught the sheet*: `evaluate` took `measured_units`/`written_order`
   before `_evaluate_statement`; `q = 3*s + nofunc(1)` brought back `[c, 1 s; ...]`. Now
   taken after success.
2. *`solve` inside a larger expression solved twice* (the `_shown_input` second reading):
   `_Evaluator.answered` keeps each solve's answer by node; the reading reuses it. Page
   unchanged (`z = 8`).
3. *Substitution stage built in three places*, the spacing metadata's without the row's
   units or piecewise branches: one `_numeric_substituted_rows(result, settings,
   formula_rows)` for drawing and counting.
5. *A name updated from itself showed its new value in its own formula*
   (`v = v + 2*diff(t^2, t)` read `4t + 2 d/dt t² + 5`): `_shown_input` now runs before
   the name is stored; reads `2 d/dt t² + 5`. Functions too.
4. **His decision: option A** (*"Sí, fusiona y publica la 0.33.4, opción A"*): keep the
   principal power, make the line true - "has no real principal value" - and say how:
   `For its real cube root, write -(8^(1/3))` for a cube root of a plain number, the rule
   with `-(8^(1/3)) = -2` otherwise (`(-27)^(2/3)` is +9, so no per-case example).

**0.33.4 is closed** (#283, `5b7e1ee`). On the release commit `3044948`: version
assertions RED then GREEN; source suite 2772, twice; wheel from `git archive`, 31 files
identical to `src`; clean Colab-like venv upgrades nothing; smoke 60/60 (`smoke-0334/`:
the new cube-root line, a failed line not bringing back `1 s`, `v = v + 2*diff(t^2, t)`
showing the old `v`); suite against the wheel 2772; 13 sheets and 18 exercises
identical to 0.33.3. After its merge: six jobs and both qualification runs green on
`5b7e1ee`; a clean `git+https` install resolved to it, upgraded nothing, 31 files
identical, smoke 60/60. Not re-checked in Colab: no page moves.

**Colab's KaTeX in the suite** (branch `test/colab-can-typeset-every-formula`, his yes to
"la 1 y luego la 2", 2026-09-24). `tests/test_colab_can_typeset_every_formula.py` hands every
formula of the 5 reference pages, `tools/matrix_derivation.eng` (his derivation, now in the
repo) and the 18 gap-map exercises - 153 formulas, the `Math` blocks and the `$...$` of the
Markdown - to KaTeX 0.16.28 (`tools/katex/package.json` + lock, `render.cjs`, Node), and
fails on any it cannot typeset. 0 errors, 0 strict warnings today. Skipped on a workstation
without `npm ci --prefix tools/katex`; required in CI (`CI` set), where both jobs run
`npm ci`. Mutation: the spacer as `\vrule` (not in KaTeX) caught; `\hskip` survives because
KaTeX has it. Suite 2798. It does not measure spacing.

**Item 2 found a defect first - a kept value did not follow its inputs** (#287,
`fix/a-kept-value-follows-its-inputs`, merged with his yes). `_store_kept_value` computed a
kept name's number once: `keep a = E*A/L; z = 2*a; E := 100*GPa` answered `numeric(z)`
with the old `a` (50000 kN/m) and `numeric(a)` with the new (12500) - wrong, silent, in
every release since `keep`; and `keep` before the values made `numeric(2*a)` ask for `a`.
`_refresh_kept_values` after each `:=`; a number no longer computable is dropped. 4
contracts (3 RED); no page moves.

**Item 2 - a kept name survives `subs`, `expand`, `simplify`, `factor`** (branch
`feat/a-kept-name-survives-an-algebra-call`, #288, merged with his yes after seeing the
rows: *"Sí, fusiona ambos y publica la 0.33.5"*). The four join `_WRITTEN_FORM_SAFE_CALLS`; `_agrees_with` keeps it honest - `subs(...,
L, L_1)` replaces the `L` inside `a`, the check fails and the entry reads `E A / L_1`. 8
contracts (6 RED). Rows that move: only his derivation - `K_b0` in `a`, `K_c` and `K_22c`
in `a`, `b_1 ... b_4`; `K_1`, `K_2` keep `E A / L_1`, `E A / L_2`. The 13 sheets and 18
exercises are identical. Suite 2810.

**0.33.5 is closed** (#289, `71a7584`). On the release commit `c5fa399`: version
assertions RED then GREEN; source suite 2810, twice; wheel from `git archive`, 31 files
identical to `src`; clean Colab-like venv upgrades nothing; smoke 62/62 (`smoke-0335/`:
a kept value following a later `:=`, `K_c` in `a`/`b_1...b_4`, `K_1` in `E A / L_1`);
suite against the wheel 2810 with KaTeX installed in the copy; 13 sheets and 18
exercises identical to 0.33.4. After its merge: six jobs and both qualification runs
green on `71a7584`; a clean `git+https` install resolved to it, upgraded nothing, 31
files identical, smoke 62/62. **In his Colab** (a reconnect reused the 0.33.3 session
- "extension is already loaded" - so the session was restarted; his install cell then
reported 0.33.5): `K_b0` in `a`, `K_c`, `K_22c`, `K_22` in `a`, `b_1...b_4`, `K_1` in
`E A / L_1`, `N_1` = -4078.86 kgf and `N_2` = 5098.58 kgf as before.

**0.33.6 - a letter read as a unit says so** (#291, merged with his yes; he chose it from my recommendations on 2026-09-24).
`sigma = N/A` with `N` never defined gave 0.002 MPa in silence (N = one newton). A line
that reads `N`, `m` or `s` as a unit, where the sheet never wrote that letter beside a
number or another unit (`letters_written_as_units_in`), now says once per letter: "'N'
is read as a unit (newton), and nothing on the sheet writes it as one. If it is a
quantity, give it a value first (N := ...) or another name, such as N_1." The value is
unchanged. 11 contracts (5 RED); ten contracts that use `s`/`N` as names on purpose
filter it with `conftest.without_letter_notices`. No notice on the 13 sheets, 18
exercises or the derivation. Suite 2821. Released as 0.33.6 (#292). **Closed**: on `e3bab2e` version assertions RED then GREEN,
suite 2821 twice, wheel 31 files identical, clean Colab-like venv upgrades nothing, smoke
63/63 (`smoke-0336/`), suite against the wheel 2821 with KaTeX, sheets and exercises
identical to 0.33.5; after its merge six jobs and both qualification runs green on
`18f2f75`, `git+https` resolved to it, 31 files identical, 63/63. He then chose option
B for the portal frame: I write it, check it in his Colab, and hand him the cells.

**The portal frame (his option B) found a gap - a real frame's solution is unreadable.**
One bay, fixed bases, h = 4 m, L = 6 m, 30x30 columns, 30x50 beam, f'c 210, H = 3000 kgf,
w = 2000 kgf/m, 6 free DOF (scratchpad `portal_v1..v4.eng`). EngCalc solves it right
(delta 0.628 cm, theta_2 -0.00202, theta_3 0.00118, equal to NumPy to every figure;
base shears + H = 0, vertical reactions = wL) in about 10 s, but `solve(K, F)` is kept
and printed in closed form - 29-33 kB of LaTeX, unreadable - and `numeric(...)` opens
with that form; `K_n := K` is refused (`:=` takes no matrix). `keep` coefficients do not
help (solve is not a written-form call). Proposed to him: `d := solve(K, F)` as a
numeric matrix definition; he approved it on 2026-09-24 (*"Sí, apruebo d := solve(K, F),
procede"*).

**`d := solve(K, F)` - a matrix defined by its numbers** (#294, `dc0ce3b`, merged with
his yes on 2026-09-24: *"Tienes mi si mi aprobación"*; released as 0.34.0, #295 `ac6199b`).
**0.34.0 is closed.** On the release commit `5bfad3d`: version assertions RED then GREEN;
source suite 2845, twice; wheel from `git archive`, 31 files identical to `src`; clean
Colab-like venv upgrades nothing; smoke 69/69 (`smoke-0340/`, adds the matrix frame);
suite against the wheel 2844 + the by-path magic test passing on the wheel's copy; 13
sheets and 18 exercises from the wheel identical to the tree and to 0.33.6. After its
merge: CI (six jobs) and the deep gate (both qualification runs) green on `ac6199b`; a
clean `git+https` install resolved to it, upgraded nothing, 23 modules identical to `src`,
smoke 69/69. **In his Colab on the published 0.34.0**: the appended install cell now installs
`main` (plain `git+https`, no `--force-reinstall`); a fresh runtime printed `0.34.0`, and
the frame cell rendered `d = K^-1 F` = [0.63 cm; -0.0103 cm; -0.00202; 0.62 cm; ...],
`R_1` = [-619.54 kgf; 5051.98 kgf; 198601.90 kgf cm; ...] and `Sigma_F_x = Sigma_F_y =
0.00 kgf`, no notice.

**Decided: a matrix of mixed units keeps its `10^3` factor.** Shown to him in his Colab
side by side (trial branch, deleted after): `f_4 = 10^3 [6.95 kgf; 2.38 kgf; 432.59 kgf cm;
...]` against `[6948.02 kgf; 2380.46 kgf; 432587.86 kgf cm; ...]`; he chose the factor on
2026-09-24 (*"Me gusta como queda en Antes con el 10^3 x, se ve más limpio"*). The rule in
`_matrix_scale_exponent` stays as it is, including that `f_1` takes no factor because
619.54 would read 0.62. Do not propose removing it again.

**His three points after 0.34.0 (2026-09-24, "abarca los 3 puntos"):**
1. Independent review: he asked me to launch `/code-review ultra` through Chrome; I may not
   launch it myself (billed, user-triggered), so the frame is ready - draft #299,
   `review/before-0.34.0` (`5fab92f`) ... `review/since-0.33.6` - and he types
   `/code-review ultra 299`. Never merge #299; close it after the review.
2. The frame draws its diagrams (branch `feat/frame-diagrams`): `tools/portico_matricial.eng`
   takes end forces out with `:=` (`V_2 := f_v[2,1]`), writes `M_b(x)`, `V_b(x)`,
   `M_c1(y)`, `M_c4(y)` and plots them, with `extrema`/`roots`. Beam M max 6872.77 kgf m at
   x = 2.526 m; joint moments agree (492.14 and 5195.96 kgf m). Checked in his Colab.
3. `numeric(d)` of a matrix defined with `:=` shows `d = [numbers]`, and `numeric(d, cm)`
   converts every entry (or names the entry that cannot be). 3 contracts, 2 mutants caught.
   The written form on a scalar taken from a matrix (`u = d_{2,1} = 20.00 m`) is kept as is
   unless he says otherwise. Suite 2848; the 13 sheets and 18 exercises are identical.

Seen in the diagrams, not changed: the beam moment axis uses matplotlib's `x10^6` offset
(0.25 ... 1.00) while the column plot prints 200000 ... 800000 - two styles for one unit.

**#300 merged with his yes** (`e0512c2`, *"Sí, fusiona y publica la 0.34.1"*), released as 0.34.1.
Added in the release PR, not in #300: `numeric(d, cm)` named a misfit entry with the whole
float (`-0.0020228091706281292`); it now reads `-0.00202, a number without a unit` (1 contract).
**0.34.1 is closed.** On the release commit `862de44`: version assertions RED then GREEN;
suite 2849 twice; wheel 31 files identical to `src`; clean Colab-like venv upgrades
nothing; smoke 71/71 (`smoke-0341/`: `numeric(d)`, the frame's diagrams); suite against
the wheel 2848 + the by-path magic test on the wheel's copy; 13 sheets and 18 exercises
identical to 0.34.0. After its merge: CI (six jobs) and the deep gate green on `24ada0b`;
`git+https` resolved to it, upgraded nothing, 23 modules identical, smoke 71/71. In his
Colab (runtime deleted first - the trial session held a same-version build): 0.34.1, the
whole frame through the column extrema, no error.

**An axis takes its power of ten in thousands** (branch
`fix/an-axis-takes-its-power-of-ten-in-thousands`). He disliked both spellings of one unit
on the frame's diagrams - the beam's `x10^6` with ticks 0.25 ... 1.00 and the columns'
200000 ... 800000 (matplotlib takes an offset only once an axis reaches a million, and
whatever power that is). Shown two ways to take a power in thousands; he chose option A,
`x10^3` in the corner where matplotlib writes it (2026-09-24, *"Prefiero la opción A"*),
over `[10^3 kgf cm]` in the label. `plotting._style_axes` fixes the offset to a multiple of
three sized on the largest value drawn, once a value reaches 10^4 (a shear of 6948 kgf
takes none); annotations keep the page's numbers. Moves three figures of the reference
sheets, shown to him before merging: formas-kgf sweep `x10^7` -> `x10^6`, larga-mm
`x10^8` -> `x10^6`, memoria-kgf none -> `x10^3`. 5 contracts; mutation 4/4. Suite 2854.

Merged as #303 (`aa88b1d`) with his yes (*"Sí, fusiona y publica la 0.34.2"*), which
also said *"si hay cosas que corregir corrígelas, dejo a tu criterio"*. What I fixed and
decided under that (branch `fix/a-design-moment-is-plotted-downward`):

- **A moment by another name is drawn positive-down.** Moment-ness was the name alone
  (`M(`, `M_b(`, `M2(`), so the `Md(x)` sweep in formas, the load-combination envelope
  in viga (`U1`, `U2` over `case D = M_D(x)`) and exercise E10's `U1(x)` were drawn
  upward. Now `engine._is_moment_series`: the old names as before; `M` + letters
  (`Md`, `Mu`, `Mn`, `Mmax`) and load cases/combinations count when the values are a
  force times a length (`Mass(x)` in kg and a combination of shears are not). 13
  contracts; mutation 4/4. Five figures turn: formas x2, viga x2, E10.
- **The snapshots record which way positive runs** (`positive: down/up` per figure) -
  nothing had, which is how the sweep went unseen.
- **A legend goes where the lines are fewest** (`loc="best"`, `_LEGEND_PLACE`): fixed
  "upper right" sat on the turned sweep's curves. Checked every figure with a legend on
  the sheets and exercises: only the sweep's legend moves (to upper centre).
- **Kept, deliberately:** an annotation of a million or more still writes the page's
  number (`8.10x10^7`) while the axis now reads `x10^6` - the annotation follows the page.

Merged as #304 (`a87f299`); released as 0.34.2 by the release PR.

**0.34.2 is closed.** On the release commit `62e2f29`: version assertions RED then GREEN;
suite 2867 twice; wheel 31 files identical to `src`; clean Colab-like venv upgrades
nothing; smoke 73/73 (`smoke-0342/`: the frame's moment axes read x10^3 and run
positive-down, the shear takes no factor); suite against the wheel 2866 + the by-path
magic test on the wheel's copy; 13 sheets and 18 exercises from the wheel identical to the
tree. After its merge: CI (six jobs) and the deep gate green on `a791a8b`; `git+https`
resolved to it, upgraded nothing, 23 modules identical, smoke 73/73. In his Colab (session
restarted - it held 0.34.1): 0.34.2; beam M x10^3 (ticks to 1000) positive-down, shear
without factor, columns x10^3 (-600 ... 800) with the legend clear of the lines.
Windows screen capture came back black this time (screen locked); the Chrome extension's
own screenshot was used to look.

**The ultra review of #299 (everything since 0.33.6) - he launched it.** Seven findings,
each reproduced by running it (scratchpad `ultra_299_probe.py`) before any change. Fixed on
branch `fix/what-the-second-ultra-review-found`:
1. `s := min(3*h, d[1,1])` stopped ("min cannot be worked out"): a call that takes numbers
   now works out only its matrix-reading arguments and is evaluated by
   `_QuantityOfTheFormula`, so `min`, `max`, `interp`, sqrt... mean what they do elsewhere.
2. `r := [d[1,1], d[2,1]]` (a row with commas) stopped: read as a row, as on a `=` line.
3. `y := M(3*m)*d[1,1]/m` stopped at the sheet function `M`: the parts that read no
   matrix and call a sheet function go through `_QuantityOfTheFormula`.
4. `K = [...]`, `K := solve(K, F)`, `y = 2*K` read the OLD formula in silence (the one
   wrong answer): a matrix given numbers with `:=` drops its formula (namespace, written
   form, guards, kept), so `y = 2*K` says to use `:=` and `numeric(K)` shows the numbers.
5. `D := [0;` over several lines gave "unbalanced parentheses": `:` removed from the
   comparison set in `matrix_syntax._has_symbolic_assignment_before_first_bracket`.
6. `solve`/`inv`/`transpose` listed twice: one `matrix_numeric.MATRIX_CALLS`.
Not changed, measured: stages built twice per `:=` matrix line (15 ms of a 2.36 s
render); one LU per right-hand-side column (10 ms for six columns).
7 contracts (7 RED); mutation 5/5. Suite 2874. The 13 sheets and 18 exercises identical.

Merged as #307 (`e56bac9`) with his yes (*"Sí, fusiona y publica la 0.34.3"*); released as
0.34.3 by the release PR.

**0.34.3 is closed.** On the release commit `17f36c2`: version assertions RED then GREEN;
suite 2874 twice; wheel 31 files identical to `src`; clean Colab-like venv upgrades
nothing; smoke 75/75 (`smoke-0343/`: a matrix given numbers drops its formula, `min` over
a matrix entry, a `:=` matrix over two lines); suite against the wheel 2873 + the by-path
magic test on the wheel's copy; 13 sheets and 18 exercises identical to 0.34.2. After its
merge: CI (six jobs) and the deep gate green on `f0e17d8`; `git+https` resolved to it,
upgraded nothing, 23 modules identical, smoke 75/75. In his Colab (fresh runtime): 0.34.3,
the whole frame through the column moment diagram, no error. #299 closed unmerged.

**He asked (2026-09-24): "empieza por la 1 y 2", and images in a memoria.**

**1. The frame's beam designed** (branch `feat/frame-design`): `tools/portico_diseno.eng`,
a second cell after `portico_matricial.eng`. Assumed (stated on the sheet): w = 1400 dead
+ 600 live kgf/m, H = 3000 kgf seismic at strength level; ACI 318-19. Three cases solved
at once (`d_c := solve(K, F_c)`, one column per case), cases D/Lv/EQ, six combinations,
envelope; Mu+ 876940.63, Mu- -553507.27 / -552587.34 kgf cm; As 5.55 / 4.40 (min) cm2;
Vu 7920 kgf > phi Vc 7603.63 kgf; stirrups 2 legs 8 mm at 22 cm (s_max). Every number
equals an independent NumPy solution. Writing it found and fixed:
- a `keep` name inside `min`/`max` was expanded (`As = max(...)` lost `f_cw`, `R_n`,
  `As_min`; 0.85 folded into 2.35): `min`/`max` join `_WRITTEN_FORM_SAFE_CALLS`, and
  `_agrees_with` compares limits as SymPy's canonical `Min`/`Max` (`_canonical_limits`),
  since `WrittenMin` came back from `srepr` as an unknown function. 3 contracts.
- a row written with commas on a `:=` line printed as source text: `_WrittenLine` prints
  an `ast.List` as a one-row matrix. 1 contract.
Found, NOT fixed (to propose): `governing` over six quadratics took 54 s (15 exact
symbolic intersections; the sheet uses the envelope instead); a `keep` name inside a
sheet function (`As_req(Mu)`) is expanded; a call to a combination is written expanded
(`U1(L/2)` reads `0.15 qD L^2 + ...`, also on viga); `governing` heads its block
"Governing - x"; a combination envelope is titled "Comparison envelope".
No reference page moves. Suite 2889. `tests/test_the_frame_is_designed.py` (10).

**2. Diagrams drawn on the frame**: a mock-up to show him before any code.
**3. Images in a memoria**: not possible today (a narrative escapes Markdown); an API to
propose (`image("file.png", "caption", width=...)`, embedded so it stays in the notebook).

#310 merged with his yes (`f887551`); not released - he said to wait and publish together.
His answers: tension side is the usual convention (he asked what I meant); labels WITH
sign; red loads and boxed values yes, but a distributed load must start and end with an
arrow at the member's ends; add shear, axial and the deformed shape.

**3. `image` implemented** (branch `feat/image`): `image("file", "caption", width=12*cm)`
reads a file (Colab `/content`, Drive) or a URL, embeds it (HTML data URI) and writes the
caption as Markdown (`$...$` typeset). Numbered automatically, by (file, caption): a cell
run again keeps its numbers, `%eng_reset` restarts at 1. Parser allows `width=` only here.
The label reads **"Figura N."** - his choice (*"déjalo como Figura"*), over the English of
the block names (`7987242`). 13 contracts; mutation 3/3. PR #311, not merged.

**4. Diagrams drawn on the frame** (branch `feat/frame-plot`, stacked on `feat/image`).
Approved over a four-panel mock-up (*"Sí, opción (b), apruebo la sintaxis"*):
`member("V", start=[0*m, h], end=[L, h], forces=f_v, displacements=d, EI=E*I_v, load=w)`
declares what the sheet worked out (local end forces `[N_i; V_i; M_i; N_j; V_j; M_j]`,
local displacements, a uniform load towards -y') and puts nothing on the page;
`frame_plot(M|V|N|deformed, "caption", scale=150)` draws every declared member as a
numbered "Figura", sharing the numbering with `image`. Nothing is solved again.
Sign, option (b): each member is read as a beam seen from inside the frame (inside = the
side facing the middle of the joints), so M is positive when it pulls the inside fibre and
a knee reads one number (-519 596 kgf·cm from beam and column); V follows the same reading
(right column -2 380 kgf), N is positive in tension. M drawn on the tension side. Values
with sign in boxes (whole numbers from 100, two decimals below), in the unit the page
writes the largest value in (`renderer.quantity_as_displayed`: palette, else family - kN·m,
not the base units a `:=` matrix keeps). Loads red: the distributed load starts and ends
with an arrow at the member's ends and stands clear of the diagram; a joint's load is read
back from the end forces meeting at a free joint (3 000 kgf at node 2); supports where the
sheet's displacements hold a joint still. Deformed: Hermite on the end displacements plus
the load's own deflection (needs EI), Δx at joints, δ on a loaded member, scale given or
rounded to 1/2/5×10^n. Module `frame_diagrams.py`. `tools/portico_matricial.eng` ends with
the four diagrams. 25 contracts (`test_a_frame_is_drawn_with_its_diagrams.py`), mutation
8/8. Suite 2927.
Not drawn (no syntax for it yet): a moment applied at a joint; a load other than uniform.

**In his Colab** ("Ejercicio 2.2", cells 13-14, runtime
deleted first - a reconnect had reused a session where pip skipped the same 0.34.3):
`feat/frame-plot` built from `git+https`, the frame sheet with `image("portico.png",
"Geometría del pórtico", width=9*cm)` at its head ran whole with no error: the sketch
embedded as "Figura 1. Geometría del pórtico", then "Figura 2. Momento flector" to "Figura
5. Deformada", each as drawn locally (-519 596 once at the knee, 3 000 kgf, Δx 0.63/0.62 cm,
δ -0.35 cm, ×150). #311 CI green (six jobs) with "Figura".

Merged with his yes (*"Sí, fusiona #311 y #312"*): #311 squashed as `29bce85`; #312
rebased onto it (tree identical to what ran in his Colab, 0 diff lines), retargeted to
`main`, six jobs green, squashed as `79d5fe9`. CI and the deep gate green on both commits.

Released as 0.35.0 with his yes (*"Sí, fusiona #313 y publica la 0.35.0"*).

**0.35.0 is closed.** On the release commit: version assertions RED (7) then GREEN; suite
2927 twice; wheel from `git archive` 32 files identical to `src`; a clean Colab-like venv
(3.12, ipython 7.34.0, numpy 2.2.6, matplotlib 3.10.0, sympy 1.13.3) gained only Pint and
four small deps; smoke 80/80 outside the repository (`smoke-0350/`: the frame's four
diagrams as Figuras 1-4, one moment at the knee, 3 000 kgf read back, Δx 0.63 cm, an image
embedded keeping its number, a kept name inside `min`); suite against the wheel 2926 + the
by-path IPython-surface test on the wheel's `magic.py`; 13 sheets and 18 exercises
identical to 0.34.3. After its merge: CI (six jobs) and the deep gate green on `509e65e`;
`git+https` resolved to it, upgraded nothing, 24 modules identical, smoke 80/80. In his
Colab (runtime deleted, cell 13 back to the plain `--upgrade` install from `main`): 0.35.0,
the whole frame with `image` and the four diagrams, no error.

Found while designing the beam, still NOT fixed (to propose to him): `governing` over six
quadratics takes 54 s; a `keep` name inside a sheet function is expanded; a call to a
combination is written expanded (`U1(L/2)`); "Governing - x" heading; "Comparison
envelope" title. Not drawn by `frame_plot` (no syntax yet): a moment on a joint, a
non-uniform load.

**The five pending points** (he asked: *"La idea es que abarques todos esos puntos
pendientes"*), branch `fix/pending-findings`, one commit each so a choice can drop one:
1. `a7d4b01` `governing` over polynomials finds crossings as numeric roots of their
   difference (`_polynomial_in_base_units`, `_real_roots_between`); piecewise/Macaulay keep
   the exact path. Frame design: 55.9 s -> the whole design cell in 7 s, boundaries equal
   the exact path's to 1e-9. `tools/portico_diseno.eng` now shows `governing`. 5 contracts.
2. `d4716c4` + part of `ad6f71e`: a function that reads a kept name is written as typed
   (`As_req(Mu)` keeps `f_cw`, no 2.35) and a call of it substitutes into that written body
   (`engine.written_functions`, `_flat_products`: `2 · 876940 kgf·cm`). 5 contracts.
3. `ad6f71e` **option B, his choice**: `M_u = U1(L/2)` on its own row, then
   `= 0.15 qD L^2 + 0.2 qL L^2`, substitution, value (`_call_of_the_sheet_shown`,
   `_print_AppliedUndef`, `_opens_by_repeating` accepts the split). Moves one row on
   formas, formas-kgf, viga, viga-kgf and corta (`M_c = M(L/2)`, `M_0 = M(0 mm) = 0`).
4. `294e980` **approved**: `U1`..`U6` are the family `U` (envelope `U(x) envelope`,
   `U_max/U_min`, axis `U(x)`), and "Governing along x" for "Governing — x". Moves viga,
   viga-kgf, corta and E11 headings/figure labels.
5. `4a8ca70`: a moment applied at a free joint is read back from the end moments and drawn
   (red arc + value); a fixed end of one member is a wall across it (cantilever). The
   frame's figures are unchanged. `da70eb9` (approved syntax): `load=[w_1, w_2]` runs
   linearly start->end, `point=[P, a]` (rows `[P_1, a_1; P_2, a_2]` for several), both
   towards -y'. V and M follow (`_internal`), the moment's peaks where the shear crosses
   zero (`_shear_zeros`, bisection), labels under point loads and on both sides of a jump,
   the deformed shape adds the fixed-end deflection under any of them
   (`_held_deflection`: particular solution + c2 s^2 + c3 s^3), drawn in red. A typed load
   keeps its typed unit (`declared=True`; it read `2.00 tonf/m` for `2000*kgf/m`).
   Checked against textbook values: wL^2/(9 sqrt 3), Pab/L, PL^3/(192EI), wL^4/(764EI).
   11 contracts; mutation 7/7.
His answer: *"Opción B, apruebo los nombres y la sintaxis de cargas"*. Suite 2958. The 13
sheets and 18 exercises differ from 0.35.0 only by points 3 and 4.

Also fixed, found on his Colab page while checking: a `:=` matrix wrote a unit that is a
factor as `1 kN` (`[0*kN; 20*kN]` read `0 1 kN`, `20 1 kN` - already in 0.35.0);
`_WrittenLine._binary` drops the one. 1 contract. Suite 2959. Found, NOT fixed: without a
palette a `0*kN` entry of a `:=` matrix reads `0.00 N` (the zero loses its written unit).

**In his Colab** (runtime deleted; cell 13 installs `fix/pending-findings`, built fresh,
loaded clean; cell 14 = frame + design in one cell; cell 15 is new and mine: two beams on
the kN palette through `run_cell_magic`): the whole frame and design ran in about 20 s
(governing had taken 55 s alone), "Governing along x" with U5/U3/U2/U4/U6, the envelope
"U(x) envelope" with U_max/U_min and axis U(x) [kgf·cm]; the point load (30.00 kN,
40.00 under it, shear 20.00/-10.00) and the triangular load (arrows growing to
12.00 kN/m, 27.71). That run was the commit before the `1 kN` fix.

Merged as #316 (`173835f`) with his yes (*"Sí, fusiona #316 y publica la 0.36.0"*); #315
closed as carried. Released as 0.36.0 by the release PR.

**The release found one defect of #316 and fixed it in the release PR** (told to him): the
suite against the wheel on Colab's SymPy 1.13.3 failed `As_2 = As_req(876940*kgf*cm)` -
that SymPy builds `sqrt(219235)*sqrt(4.85e-7 - ...)` and `cancel` cannot prove the written
form equal, so it was dropped. `_agrees_with` now falls back to `_agree_at_points` (three
fixed-seed points in 0.5..2, nine figures). The dev venv has SymPy 1.14 and did not see
it: **a presentation contract must also run on 1.13.3** (`PYTHONPATH=src` with the
Colab-like venv's python) - the release's wheel suite is where that happens.

**0.36.0 is closed.** On the release commit: version assertions RED (7) then GREEN; suite
2960 twice (SymPy 1.14) and 2960 on 1.13.3; wheel 32 files identical to `src`; clean
Colab-like venv gained only Pint and four small deps; smoke 86/86 (`smoke-0360/`: the
frame's design whole with Governing along x in <40 s, U(x) envelope, a call written as
called, a kept name through a call, point and linear loads, no `1 kN`); suite against the
wheel 2959 + the by-path test on the wheel's `magic.py`; 13 sheets and 18 exercises move
only as approved. After its merge: CI (six jobs) and the deep gate green on `9ebbd78`;
`git+https` resolved to it, upgraded nothing, 24 modules identical, smoke 86/86. In his
Colab (runtime deleted; cell 13 back to the plain `--upgrade` install from `main`; cell 15
gained the `As_req` call): 0.36.0 built fresh, the frame + design, the loads, `f_p` as
`0 kN / 20 kN`, and `As_2 = As_req(876940 kgf·cm) = f_cw b d/fy (1 - sqrt(1 - 2·876940
kgf·cm/(φ f_cw b d^2))) = ... = 5.55 cm^2`.

Found, NOT fixed (to propose): a long substitution row wraps into additive terms with a
trailing `· 1/(4200 kgf/cm^2)`; without a palette a `0*kN` entry of a `:=` matrix reads
`0.00 N`.

**Next three points** (he asked: *"Aborda los 3 puntos de tu recomendación"*), branch
`feat/help-rows-zeros`:
1. `b153d46` `%eng_help` documents `keep`, `case`, `combo`, `:=` (kind "statement", with a
   `note` saying what it is for - keep shows `C = 0.85 b d fc` vs `C = f_cw b d`) and
   `member`, `frame_plot`, `image` (`parser.PLACING_CALLS`); the list shows Statements
   apart from Calls; `tests/test_eng_help.py` holds the catalogue against all of them and
   runs every example. He had asked what `keep` was for: it had no entry.
2. `5e1286e` **option B, his choice ("Opción B, fusiona #319")**: a long substitution row keeps the shape of
   its formula - the plain factors as one fraction, each bracket on the next row
   (`_shaped_product_rows`, allowance 1.15 x the budget), instead of expanding into terms
   with a stray `· 1/(4200 kgf/cm^2)`. A bare fraction of a bracket (a centroid) is left as
   it was. No reference sheet or exercise moves; As_2 = As_req(...) does.
3. `c555020` a zero in a `:=` matrix reads in the unit of a neighbour of its kind
   (`0.00 kN`, not `0.00 N`) without a palette.
Suite 2980 on SymPy 1.14 and on 1.13.3.

Merged as #319 (`4cfa805`) with his yes; released as 0.37.0 by the release PR (*"Publica la
0.37.0"*).

**0.37.0 is closed.** On the release commit: version assertions RED (7) then GREEN; suite
2980 twice (SymPy 1.14) and 2980 on 1.13.3; wheel 32 files identical to `src`; clean
Colab-like venv gained only Pint and four small deps; smoke 89/89 (`smoke-0370/`: `%eng_help
keep` and the statement list, a long row in shape, a zero in its neighbours' unit); suite
against the wheel 2979 + the by-path test on the wheel's `magic.py`; 13 sheets and 18
exercises identical to 0.36.0. After its merge: CI (six jobs) and the deep gate green on
`4795c47`; `git+https` resolved to it, upgraded nothing, 24 modules identical, smoke 89/89.
In his Colab (the runtime deletion did not take - cell 13 installed 0.37.0 but printed
0.36.0 "already loaded" - so the session was restarted and cell 13 run again): 0.37.0
loaded clean; cell 15 shows `As_2` in option B's shape and `%eng_help keep` with its note.

#322 (help in Spanish) and #323 (points 1-3) merged with his yes; released as 0.38.0 by
the release PR (*"Sí, fusiona #323 y publica la 0.38.0"*).

**0.38.0 is released.** On the release commit: version assertions RED (7) then GREEN; suite
2988 twice (SymPy 1.14) and 2988 on 1.13.3; wheel 32 files identical to `src`; clean
Colab-like venv gained only Pint and four small deps; smoke 92/92 (`smoke-0380/`: help in
Spanish, `0.90` as typed, a wide bracket wrapping, a zero column's unit); suite against the
wheel 2987 + the by-path test on the wheel's `magic.py`; 13 sheets and 18 exercises: only
`formas`' `A_c = 0.30 · 0.60 m·m` moves. After its merge: CI (six jobs) and the deep gate
green on `a53613d`; `git+https` resolved to it, upgraded nothing, 24 modules identical,
smoke 92/92. **0.38.0 is closed.** In his Colab (after he reconnected the extension; a
new tab, runtime disconnected so a clean VM): cell 13 installed and loaded 0.38.0 clean;
cell 15 showed the loads, `As_2`, `%eng_help keep` in Spanish, `phiMn` over three rows with
its bracket in shape (`= 280.20 kN·m`) and `z = 0.90 b`. At that window width the output
panel is narrow and a long row runs past it (a horizontal scrollbar) - the formula row too,
which did not change.

### Control flow with % - approved 2026-09-25, `if` first

He asked for `if`/`for`/`while` in a sheet and proposed `%` lines. Approved (*"Apruebo tus
recomendaciones en los 4 puntos, empieza por el if"*): a line starting with `%` is control,
written as Python; `% end` closes a block; the branch taken opens with a "Como ...:" sentence
in numbers; `for` shows each iteration's rows; `while` shows only the final result and the
iteration count; Python helper variables stay off the memoria; `{...}` interpolates a
value into a line. He rejected a `check()` call. Order: `if`, then `for`, then `while`.
In the same message he asked for three more: (1) a numeric `solve` with an interval that
assigns, `c := solve(eq(...), c, 0*cm, d)` ("unsupported numeric function" today); (2)
`table` over a list of values, `table(As_req(Mu), Mu, [Mu_pos, Mu_2, Mu_3])`; (3) fix the
unit of `k_1 := k(4*m)`.

**#326 merged with his yes** (`1f926db`, *"fusiona #326 y #327"*), branch `feat/if-blocks`:
- `f3cfa88` (point 3): a `:=` value keeps its unit only when its line wrote every part of it
  (`unit_text.unit_was_written`). `k_1 := k(4*m)` reads `16000.00 kN·m`, not GPa·mm⁴/m. 5
  contracts. No page moves.
- `4ead9b6` + `f673ad0` `% if / % elif / % else / % end` (`control.py`; `magic._eng_cell`
  routes a cell with `%` lines through `control.run`). The structure and every line are read
  before anything runs. A condition is Python comparisons joined by `and`/`or`/`not` over the
  sheet's values (`numeric(...)` through the engine). The sentence - `Como Vu = 7920.00 kgf >
  φ_v V_c = 7603.63 kgf:` - is a Math output (his option 1b, `23516b7`): the rows' letter and
  size, **Como** bold, a `\rule` strut for room above and below (to calibrate in Colab). Each side is written as the page writes
  it, and the other sides in the first side's unit. A branch that does not hold is neither
  computed nor written. Conditions that did not hold are stated negated (`≤`) before the
  one that did, joined with " y ". A `%` inside a `"""` block is text. 15 contracts
  (`tests/test_a_sheet_decides_with_if.py`); mutation 9/9. KaTeX 0.16.28 typesets the
  sentences.
- `df18d39` **a defect on 0.38.0, found rendering it**: `Vu = max(a, b)` then
  `Vu := 5000*kgf` printed 5000.00 kgf and kept computing with `max(a, b)`. The scalar `:=`
  path now drops the formula, as the matrix path did. 4 contracts (3 RED).
- `1af5e62` `%eng_help if`.
The 13 sheets and 18 exercises are identical to 0.38.0. His shear design rendered with
`% if` was shown to him (`Como Vu = 77.67 kN > φ_v V_c = 74.57 kN:`).

Found, NOT fixed (on 0.38.0, not caused by this branch): on `portico_diseno.eng`,
`Vu = max(V_U1, ...)` has a row in base units (`57663.10 kg·m/s²`), and
`s_e = min(s_req, s_max)` has one in `cm·kgf·s²/(kg·m)`.


### His exercise 2.1 - a `=` line of values (#327, branch `fix/equals-lines-with-values`)

He wrote data with `=` (`E = 200*MPa`, `L_ba = sqrt(6**2+4**2)*m`) and `delta_ba` ended on
`6.68e-4 kN·m·√13/(mm²·MPa)`. He asked (2026-09-25) to fix points 2, 3 and 4:
- 2: a `=` line with nothing left to substitute (numbers and units only) whose value is
  not already a number in a unit is written as `numeric` writes one: formula in its names
  (`_NamesStandEvaluator`), each name's value, the value (`engine._in_numbers`,
  `_reads_as_a_number`). A formula over `:=` values is untouched (left to `numeric()`).
- 3: `sqrt(6^2 + 4^2)*m` no longer raises the "'m' is read as a unit" notice
  (`_worked_out_from_numbers`).
- 4: a factor with no free symbols sorts with the numbers: `√(4²+6²) m`; E14 moves two
  rows to `π² E I/(K² Lk²)`. The order inside the sum follows #243 (`4² + 6²`).
14 contracts, mutation 9/9. Suite 3002 on SymPy 1.14 and 1.13.3. The 13 sheets are
identical to `main`; of the 18 exercises only E14 moves.

Fonts, measured with KaTeX 0.16.28 (Colab's): all mathematics is KaTeX's own LaTeX fonts
(KaTeX_Main upright for numbers, units, operators and `\mathrm`; KaTeX_Math italic for
one-letter names). Headings and `"""` text are Colab's font. Found: a name of more than one
letter (`Vu`, `fc`, `As`, `phiMn`) is `\mathrm` - upright, the same letter as a unit -
while `V_c` is italic. He chose italic: branch `feat/names-in-italic`.

### Names of several letters in italic (#328, merged with his yes, `cf8ffa5`)

He asked (2026-09-25) to check the fonts, saw the rows that move, and approved (*"Apruebo
la cursiva"*). `_print_Symbol` writes `\mathit{Vu}` - text italic, the letters kept one
word, where math italic spaced `eqFy` as a product - instead of `\mathrm{Vu}`; units stay
upright. 9 contracts in `tests/test_a_name_of_several_letters_is_italic.py`; about 80
pinned `\mathrm{name}` updated; `conftest.block_text` reads `\mathit` too. Rows that move:
formas 17, viga 15, memoria 2, dinámica 1 (and their palettes), E1 E2 E3 E4 E8 E10 E11 E14,
his design sheet 33. Told him: `qL` the name and `q L` the product look alike in italic;
he was advised to write names with a subscript (`q_L`, `V_u`, `f_c`, `A_s`). Suite 3038 on the
branch, SymPy 1.14 and 1.13.3; snapshots regenerated, 51 lines, each only `\mathrm` -> `\mathit`.

### `% for` (#329, merged with his yes, `44a8ed6`)

He said *"Sí, fusiona #328 y sigue con el for"*. `control.py`: `% for <target> in <iter>:`
parsed as Python (`_for_header`); a `%` line with an open bracket continues on the `%`
lines after it (`_lines`); `% end` closes it; any other `%` line must be one assignment,
a helper (`% n = 0`, `% n += 1`, `_Helper`). One `_Scope` per cell: the `%` layer's
variables, and a sheet `:=` name read in it is a `_SheetName` - `{F}` writes `F_1`, not a
number; arithmetic on it gives a plain value that `{...}` refuses with its line. `{...}`
is filled in on sheet lines only, never inside `"""` text (LaTeX braces); `_check_lines`
reads each `{...}` as `1` so a body written wrong refuses the cell first. A `% if` inside
reads the loop's variables (`_InScope`). Cap 1000 iterations. Builtins limited to range,
enumerate, zip, len, abs, min, max, round, int, float, str, list, tuple, sum, sorted,
reversed. `%eng_help for`. 17 contracts (`tests/test_a_sheet_repeats_with_for.py`),
mutation 10/10. Suite 3058 on SymPy 1.14 and 1.13.3; 13 sheets and 18 exercises identical
to `main`. His design sheet with its 24 combination lines as four `% for` blocks over one
`% combos = [...]`: 179 -> 169 lines, and the page is the same 377 rows, byte for byte.

### `% while` (#330, merged with his yes, `2ff83d2`)

He said *"Sí, fusiona #329 y sigue con el while"*. `control._iterate` works each iteration
out itself (`engine.evaluate`), writes nothing, and at the end yields a `ConditionNote`
**En N iteraciones:** (singular for 1) with the condition as it stands now, negated, which
shows it converged, then the last iteration's results as `control.Evaluated` (the magic
displays them without evaluating again). Zero iterations: the note and no rows. Cap 1000
iterations: "does not converge from this start". Found writing it and fixed in the same
branch: a zero compares with a value of any unit (`x > 0*m`: `0*kN` arrives as a plain 0);
the sentence's sides share one unit even when the first side's leaves another with no
figure (`_reads_in`), so `1e-6 m²` no longer reads `0.00 m²` beside `0.01 cm²`.
`%eng_help while`. 12 + 2 contracts; mutation 9/9 (the cap's mutant hangs, as it should).
Suite 3076 on SymPy 1.14 and 1.13.3; no page moves. His neutral axis by Newton (b 30, d 44,
As 5.55, n 9): `c = 10.55 cm` in 4 iterations, `I_cr = 67631.59 cm⁴`. Seen, not changed:
the sentence writes `|f(c)|` expanded (`|b c²/2 - n A_s (d - c)|`).

Seen on his exercise 2.1 with `%eng_units kN`, NOT changed (his call): the palette writes a
typed `6000*mm^2` as `0.006 m²` and δ as `0.00241 m`.

### `solve` in a range (#331, merged with his yes, `9ac0c26`)

He said *"Sí, fusiona #330 y sigue con el solve"*. `solve(eq(...), c, lower, upper)` (and
with an expression instead of `eq`): `_solves_in_a_range` tells it from a system - the
second argument is a name that is not an equation of the sheet; three arguments with a
non-name third are a range missing its upper bound. `_Evaluator._solve_in_a_range`: with
every other name valued, `_roots_in_numbers` evaluates the equation with Pint at 256
pieces of the range, halves each change of sign 60 times, drops a pole by its value and a
point with no value (nan); the root comes back as `Float * unit` (`_as_written_quantity`).
A sheet of symbols keeps the exact `roots(...)` path. None / several roots are refused
with bounds and roots (`_one_root`). On `:=` the line goes through `_assign_through_the_sheet`
and `NumericAssignmentResult.equation` puts the equation above the value
(`renderer._display_rows`, two stages). Found: `roots` on a cubic in symbols took 20-34 s
and said "could not validate a solution set" (NOT fixed, `roots` itself). 10 contracts +
help; mutation 9/9. Suite 3087 on SymPy 1.14 and 1.13.3; no page moves.

### A named `numeric` / `result` line (#332, merged with his yes, `39097c7`)

He got lost among the forms; shown on his exercise: `:=` value, `=` formula, `numeric(x)`
formula + substitution + value, `result(x)` formula + value, `x := formula` value only.
He accepted keeping the forms and fixing `d = numeric(...)` (*"corrige el numeric"*).
Three defects, one line each: the row was written under the formula, not `d`
(`renderer._display_lhs` now falls back to the statement's target); `d = result(...)`
showed the substitution (`_shows_substitution` read `^result(` off the source - the parser
hands `result` on as `numeric` - and now allows `name =` in front); and the name was never
defined (the engine returned before storing; now `namespace[d]` = the formula). 5
contracts. Suite 3092.

`table` over a list: it ALREADY worked - `table(As_req(Mu), Mu, [Mu_pos, Mu_2, 8e5*kgf*cm])`
gives the table, sheet names and sheet functions included. My earlier "unsupported" came
from probing with `As_req` undefined. Possible improvement, not done: name the rows
(`Mu_pos`) instead of only their numbers.

### One rule for the room between blocks (#333, merged with his yes, `8f40539`)

He asked (2026-09-25) why the `"""` text looked like another letter, why it sat so close to
the equations, and for one spacing rule instead of patches. MEASURED IN HIS COLAB (cell 15,
a Javascript output answering `postMessage` from the page): every output is its own
`div.display_data`; rows inside a block ~13 px apart; text 5-7 px from the equations; text
and headings Google Sans 14 px vs KaTeX 16.94 px. Colab STRIPS style from HTML inside a
Markdown output (spacer, font: five ways, no effect), but keeps an HTML output's style.
Shown three options in his Colab; he chose option 2 (*"Me gusta más tu recomendación"*):
- `magic._Page.show`: one spacer, `BLOCK_SPACER` = 18 px HTML, between any two blocks (a
  figure and its caption are one block). Calibrated in his Colab: the gap shown is the
  spacer's height (0 px: blocks touch); 18 px = ~1.4 x the row gap; before a heading the
  page opens wider by itself (36 px). No block has room of its own any more: the computed
  block's empty rows (#192) and the `Como` strut are gone.
- `renderer.narrative_latex`: a paragraph is a `Math` output - words in `\text{}`, `$...$`
  spans as mathematics, lines <= 62 characters (80 ran off a 489 px output at a 1254 px
  window in his Colab; KaTeX sets ~7.3 px a character), paragraphs `\\[8pt]` apart, `**bold**` /
  `*italic*` only when paired, `# $ % & _ { } ~ ^ \\ < >` written as text, `·` as `$\cdot$`
  (KaTeX has `\cdotp` only in maths). KaTeX 0.16.28 lacks `\textquestiondown`,
  `\guillemotleft`, `@{}`: `¿ ¡ « »` stay as they are (a strict-mode warning, no error);
  the frame is `\hspace{-5pt}\begin{array}{l}` instead of `@{}l@{}`.
- headings in `KaTeX_Main` (20 / 17.6 px).
- On seeing it he asked the text two points smaller: `{\footnotesize ...}` (0.8, 2.5 pt, the
  nearest KaTeX step), lines of 76 characters. Measured in his Colab: text 13.55 px, the
  paragraph 414 px wide in a 641 px output. (A local preview must set KaTeX's container
  to 14 px: KaTeX multiplies by 1.21, and 16.94 px is what Colab shows.)
Tests that count outputs use `conftest.blocks_into` (records all but the spacer); the
Markdown-era narrative contracts were translated to the Math form, keeping what they
protect. The five reference pages move only by these four kinds of change, checked item by
item after normalising them (scratchpad `check_snapshots.py`). 17 contracts; mutation
10/10; suite 3109 on SymPy 1.14 and 1.13.3. Verified in his Colab with the branch
installed: gaps 15-20 px, all text KaTeX.


### A `% while` reads its counter every pass (branch `fix/while-reads-its-counter`)

Found by the smoke of 0.39.0 before publishing: `% k = 0`, `% while k < 3:` with `% k += 1`
in the body ran 1000 times. `control._in_scope` is a `NodeTransformer` and rewrote the
condition's tree in place, so the first pass put `0` where `k` stood for good. It now
works on a copy. 2 contracts (1 RED before; the `% for` + `% if` one guards the same
reading), suite 3119 on SymPy 1.14 and 1.13.3.

### A row holding a fraction keeps its room (#334, merged with his yes 2026-09-25)

Seen in the images of #333 (he asked to correct what I noticed): `R_A = qL/2` stood on
`R_B = qL/2`, measured -4 px apart (ink on ink); `q` on `E` -5 px; the `d_max` derivation
-1..6 px; plain rows 11 px. KaTeX reads `\[Npt]` as the least depth of the row above, and a
display fraction is already ~0.69 em deep (11.6 px of 16.94 px), so the space added
nothing. `renderer._row_break`: a row that `_is_tall` (fraction, integral, sum, cases...)
and has no matrix above or below takes `_FRACTION_DEPTH_PT` = 9 pt on top of its space
(`8pt` -> `17pt`, `4pt` -> `13pt`, `16pt` -> `25pt`). A unit fraction (`kN/m`) counts:
it is as deep. After: R_A->R_B 11 px, q->E 3 px, d_max 6..18 px. Tests that read which
space stands between stages use `conftest.without_fraction_depth`; the five reference
pages changed only by that depth (126 breaks, checked item by item, scratchpad
`check_fraction_snapshots.py`). 5 contracts; mutation 2/2; suite 3117 on SymPy 1.14 and
1.13.3.

He saw the before/after images and approved (*"Tienes mi aprobación"*). He also said to
leave the English `Where` / `Domain: ... to ...` / `x in` of the region block as it is.

The kN palette question is closed, not his to decide again: `%eng_units kN` shows one
unit per dimension by his earlier choice (`6000*mm^2` reads `0.006 m²`, δ `0.00241 m`);
`numeric(delta, mm)` or no `%eng_units` line gives millimetres. Explained to him.

### His exercise 2.1 solved in his Colab (2026-09-25)

Notebook "Untitled9" (`12CCpV_S6Q5GdXDEo_j2yUvfFwtpP0zhH`), cell 2 (index 2, mine; his
attempt in cell 1 untouched; cell 0 installs and sets `%eng_units kN`). He asked for the
solution with angles only, no matrix: `keep delta_ab = F L/(E A)`, then
`keep u = (delta_ab*sin(phi) - delta_ac*sin(theta))/sin(theta + phi)`, `v` likewise;
u 2.41, v 0.72, aa' 2.52 mm, as the book. His runtime runs an older install (upright `aa`).

Found on the way, both on `main` (`3eb4c40`), not fixed:
- a substituted value inside a function call is bracketed twice: `sin((0.50))`,
  `sin((0.93 rad) + (0.59 rad))` reads right but `sin((0.93 rad))` does not;
- a sum inside a function keeps SymPy's order, not the written one: `sin(b + a)` reads
  `sin(a + b)`, his `sin(theta + phi)` reads `sin(φ + θ)`.
- (by design, worth asking) a `:=` line cannot read a name defined by `=`:
  `D := [delta_ab; delta_ac]` after `delta_ab = ...` says "unknown numeric name".

**Exact next step:** his exercise 2.1 (a truss: compatibility, not the sum of the two elongation
vectors - see the conversation of 2026-09-25) as a reference exercise, the kN palette
question; a release when he asks.
A `:=` line that names a matrix is worked out in numbers (`engine._MatrixNumbers`, with
`matrix_numeric.NumberMatrix`: base-unit magnitudes, one unit per entry, `None` for the
written `0`; mpmath, not numpy). Symbolic matrices are evaluated as `numeric(K)` does;
`solve`, `inv`, `transpose`, `+ - *`, a scalar factor, `d[4,1]`, `d[4]`, `K[[1,2],[1,2]]`
and `[0; d[1,1]]` / `[K_jj, Z; Z, K_jj]` written on the line. The unit of each entry of an
inverse or a solution comes from factoring the matrix's units as r_i/c_k (a stiffness:
forces/moments over displacements/rotations). A matrix is kept in
`numeric_context.matrices`, apart from the scalars; one entry taken out is a scalar
`:=` value a `numeric` line can use. The page shows the line as written, from its own
tree (SymPy would reorder `k_v d + f_0`), then the numbers: `d = K^{-1} F` over
`[0.63 cm; -0.0103 cm; -0.00202; 0.62 cm; -0.0141 cm; 0.00118]` on his kgf palette;
`u := d[2,1]` reads `u = d_{2,1} = 20.00 m` (the written form on a scalar `:=` is only
for lines that read a matrix). A `=` line naming such a matrix says to use it on a `:=`
line. Redefinition either way replaces it. 23 contracts; mutation 18/18 killed. The
frame is `tools/portico_matricial.eng` (displacements, member-end forces with f_0,
reactions `transpose(T_c)*f`, `Sigma_F_x = Sigma_F_y = 0.00 kgf`), added to the KaTeX
test with the kgf palette. The 13 sheets and 18 exercises are byte-identical to 0.33.6.
Suite 2845. **In his Colab** (notebook "Ejercicio 2.2", two cells appended at the end: an
install of the branch - the reconnect reused a 0.33.5 session, so it was restarted - and
the frame with `%eng_units kgf`): the branch loaded, the whole frame rendered in KaTeX,
`d` as above, `f_1` = [5051.98 kgf; 619.54 kgf; 198601.90 kgf cm; ...], `R_1` and `R_4`,
`Sigma_F_x = Sigma_F_y = 0.00 kgf`. His session now runs the branch, not a release.

Seen, not changed (his call): a matrix of mixed units takes a `10^3` factor in front
when its entries are large, so `f_4` reads `10^3 [6.95 kgf; ...; 432.59 kgf cm]` while
`f_1` (largest 198601.90) has none - existing behaviour of every numeric matrix.

**%eng_help in Spanish** (he asked, 2026-09-25: *"Tradúcela al español"*), branch
`feat/help-in-spanish`: every summary, note, argument and placeholder, the headings
(Argumentos, Ejemplo, Sentencias, Funciones) and the messages (`no hay ayuda para ...`).
Call names, keywords and examples stay as the language writes them. Translating found that
`table`'s last argument was documented as "how many intervals": it is the number of rows,
both ends included (`table(..., 11)` = "Once estaciones"); fixed and held by a contract.

**Points 1-4 of that list** (he asked, 2026-09-25: *"aborda el 1 y 2 y 3 y 4"*), branch
`fix/four-points`:
1. `99e65ea` a number keeps the figures it was typed with: the parser notes them
   (`matrix_syntax.mark_typed_decimals`, `node.typed`), the written form carries a
   `TypedFloat` (turned back into a Float before `srepr`), the printer writes `typed`.
   `formas` moves one row: `A_c = 0.30 · 0.60 m·m`.
2. `6767aaf` a bracket too wide for a row wraps inside itself (`\left( ... \right.` /
   `\left. ... \right)`): `phiMn` over plain `d`, `a` takes 3 rows, not 5. No sheet moves.
3. `82e0e16` a table column of zeros takes its unit from the expression at mid-range
   (`TableColumn.reference`): `M(x) [kN·m]`, not `[N·m]`.
4. No change: an undefined `N` already warns since 2026-09-24 ("Said, not changed" was his
   decision then); listed as pending by mistake. Refusing the line instead is his call.
Suite 2988 on SymPy 1.14 and 1.13.3.

Re-checked on the page on 2026-09-25 (0.37.0 + this branch), still real, none requested:
- `a = 0.90*b` is written `0.9 b` - a coefficient from a code loses its trailing zero.
- A long substitution over plain (not `keep`) definitions still expands into rows of terms:
  `phiMn = phi*As*fy*(d - a/2)` over `d` and `a` takes 7 rows. `keep d`, `keep a` avoid it;
  option B's allowance (1.15) does not reach this case.
- A table column that is zero at every station takes the base unit in its header (`N·m`).
- An `N` never defined reads as one newton.
- (His call, seen) a mixed-unit numeric matrix takes a `10^3` factor in front when large.

Known and not requested:
`0.90` prints `0.9`; a `0*m` in a table prints `0`; a wide substitution over plain definitions
splits into additive terms (`keep` avoids it); an `N` never defined still reads as one newton.

**Where the live narrative is.** `NEXT.md` for how the work goes and how a release is
cut; this file's later sections for the approved behaviour that is still in force.

_Last updated: 2026-09-02 — **EngCalc 0.13.0 is released and closed on `main` at `9a9d6e3`**, CI green on Python 3.10–3.14 and **verified installable and working in Google Colab from the documented `git+https` path**, running a complete memoria: a statics system, a moment from its shear, an elastic curve and a plot. Etapa 1 is three quarters done — `integrate` canonical (0.11.0), scalar equation systems (0.12.0), the indefinite integral (0.13.0) — and the measured gap map has gone from 4/18 to 7/18 exercises running end to end, with broken lines down from 24 to 17. No defect is open. One protocol lapse is recorded and corrected below._

## Current baseline

- Repository: `eliaszamora/engcalc-colab`.
- Canonical `main`: **`9a9d6e3`** — EngCalc **0.13.0**. Etapa 1 steps 1.0, 1.1 and 1.2 are in; 1.3 is next.
- Runtime/package version: **0.13.0**.
- **Colab verified end to end**, not assumed: a clean virtual environment, installed from
  the documented `git+https` path, `%load_ext engcalc_colab`, and a real memoria through
  `%%eng`. Equations, tables, `plot(...)`, `roots(...)` and `extrema(...)` all exercised.
  The plot arrives as a `Figure` handed to `display()` with 2 series over 201 points and
  units appended to the axis labels, so it does not depend on `%matplotlib inline` being
  active.
- `requires-python = ">=3.10"`; runtime dependency includes `ipython>=8.18`.
- Permanent CI: `.github/workflows/ci.yml`, Python 3.10–3.14 on PRs and pushes to `main`.
- Default suite at `9a9d6e3`: **1116/1116 GREEN**. Deep suite: **18**, behind an
  explicit path.
- Post-merge CI on `9a9d6e3`: run **`33663672405`**, Python 3.10–3.14 **SUCCESS**.
- Deep qualification on `9a9d6e3`: run **`33663679263`**, 3.10 and 3.14 **SUCCESS**. This
  is the run that corrects the lapse recorded further down.
- Colab verified on this commit, not assumed: a clean virtual environment, install from
  the documented `git+https` path, `%load_ext engcalc_colab`, and one `%%eng` cell running
  a statics system, a moment integrated from its shear, an elastic curve with its
  constants, and a plot.
- Release history: PR #35 merge `e073320b…` (N-1…N-4 remediation, 901/901); PR #36 merge `c3f4b14c…` (A-1/A-2 correction, 912/912); PR #37 merge `38b28d5a…` (Permanent Quality Gate, 1066/1066, no production change); PR #38 merge `536c22dd…` (post-merge state, QG-3); PR #39 merge `4a018fb9…` (**0.10.0 Engineering Presentation**, 1079/1079).
- The certified `engcalc_colab-0.9.2-py3-none-any.whl` with SHA-256 `1d56169c…` predates PR #36. It is **historical qualification evidence, not an artifact of the current tree**. No GitHub Release is published; the documented install path is `git+https` against `main`, so there is no distributed artifact to reconcile.
- Never invoke Codex / Codex Cloud without explicit user authorization.

## Approved behavior

All 0.9.x contracts remain in force and are regression requirements: exact-first
characteristic analysis, deterministic numerical fallback, dimensional-zero semantics,
sampled `envelope(...)`, positive structural moment plotted downward, Numeric/Pint,
Piecewise, tables, plots, multi-argument functions and Matrix/CAS.

The Permanent Quality Gate adds **no** product behavior. Its approved design is
`docs/superpowers/specs/2026-09-01-engcalc-permanent-quality-gate-design.md`; its
approved plan is
`docs/superpowers/plans/2026-09-01-engcalc-permanent-quality-gate-implementation.md`.

Evidence hierarchy adopted by that design: **Level A** constructive oracle is
authoritative; **Level B** internal invariants and **Level C** metamorphic checks are
complementary; **Level D** shared-solver oracles are prohibited as completeness evidence.

## Open issues / user feedback

**P-1, P-2 and P-3 are CLOSED**, corrected in 0.10.0 (PR #39). Their contracts are in
`tests/test_engineering_presentation.py` and are collected by the ordinary suite on every
push. The reproductions and the before/after are in the release section below; the design
and both audits are in
`docs/superpowers/specs/2026-09-01-engcalc-v0.10.0-engineering-presentation-design.md`.

One thing from their history is still load-bearing and must not be lost: **P-3 is not
caught by a "never renders as zero" property.** The audit demonstrated this by having
that property pass on the deflection case, and the implementation confirmed it from the
other side - `5625.00 kN/(GPa·m)` retains *more* significant figures than `5.63 mm`, so a
rule that merely maximised figures kept the compound unit. Anyone tempted to fold the
presentation contracts into one property will reintroduce P-3 and see green.

**EP-1 is CLOSED**, corrected in 0.10.1 (PR #43). The root cause was not a subtle metric failure:
design §4.5 specifies a band rule and it was never implemented. §4.3's significant-figures
criterion, which exists to decide whether a *declared* unit still says anything, was used
for the family choice as well — one criterion doing two jobs, and wrong for the second.

Measured over the cases that reach the family choice, the band rule is right 10 times out
of 10 where counting figures is right 8. The two it fixes are `f_adm = L/300` with
`L := 6*m`, where the quotient is exactly 0.02 and the figures tie, and a derived
thickness. Ties keep the unit the value already carries, which is what leaves a derived
11 m span in metres rather than rendering it as `11000.00 mm`.

No presentation defect is currently open.

Known coverage gaps, not defects: roots separated by less than `0.05`; coefficients with
many more decimal places; Piecewise with more than two branches; nested Piecewise;
Piecewise combined with matrices; intersections between two Piecewise responses;
unresolvable symbolic domain bounds; renderer and plotting beyond the above findings.

Other deferred items: `no_vertical_scroll()` Colab ergonomics; multiline ordinary
function-call parsing; generalized structural eigenproblems.

## Validation evidence

### Independent property-based audit of `characteristics/` — CLOSED

Executed against `c3f4b14`, outside the repository, with Hypothesis 6.167.1 installed
only in the auditor environment. Result: **CLEAN within the audited scope** — no new
mathematical defect demonstrated in roots, intersections, extrema, Piecewise, domains,
units, exact/fallback or deduplication.

908 directed and generated mathematical cases, zero failures:

| Evidence level | Cases |
|---|---|
| A — constructive oracle | 811 |
| B — internal invariant | 24 |
| C — metamorphic | 64 |
| D — shared external oracle | 9 |

Composition: 398 deterministic cases across three seeded sweeps plus 510 Hypothesis
examples over 17 properties at 30 each. 965 total engine invocations.

Historical families re-attacked at scale rather than by their original reproductions:

- **N-1** expanded decimal quadratics: previously 8/20 silent failures, now **0/117**;
- **A-1** complex candidates: passes with degree 4 and 6 variants, symbolic coefficients and units;
- **A-2** open-edge Piecewise: passes across four operators × both bounds;
- **PR #36 completeness guard**: passes nine variants of the partially solvable family.

The 9 Level D cases used `sp.solveset` as oracle and are therefore **not acceptable as
completeness evidence**; their replacement is mandated by the Quality Gate design §8.

### Quality Gate design and plan — audited before implementation

The design audit produced D-1/D-2/D-3, all resolved: the first proposed H4 replacement
embedded its root in the coefficients so SymPy exposed it, defeating the sensitivity
requirement; Fast Gate sizing preceded measurement; and one Extrema partition was
presented as audit-inherited when it was new.

The plan audit produced P-1/P-2/P-3 of the plan, all resolved: `pythonpath = ["src"]`
made helper imports fail under bare `pytest` and in historical runs from another
directory, which would have produced a false RED; Task 5 omitted required Extrema
partitions; and a static cache key would have frozen the Hypothesis database after the
first successful run.

The H4 replacement was verified before implementation: `sp.solve` returns `[a]` only
across every mandated configuration, and simulating the historical over-broad rule makes
the guard fail 4/4 configurations while the corrected implementation passes.

### Permanent Quality Gate — implemented, qualified and merged

PR **#37**, developed on `c3f4b14`, merged to `main` as `38b28d5`. Operating notes:
`docs/quality-gate.md`.

**Scope.** 22 files, none of them production source. `git diff --name-only c3f4b14
38b28d5 -- src/engcalc_colab` is empty, verified again after the merge. Package version unchanged at 0.9.2; Hypothesis pinned to
`6.167.1` as a development dependency only.

**Corpus.**

| Suite | Level A | Level C | Level B | Level D | Total |
|---|---|---|---|---|---|
| Fast, every push | 148 | 6 | 0 | **0** | 154 |
| Deep, scheduled | 16 | 2 | 0 | **0** | 18 |

Level B is zero because the audit's H2 invariant was promoted: the Piecewise
operator × bound matrix now asserts branch ownership, reported side and each attained
role, derived from the public Piecewise contract rather than from current output. No
test carries both an authoritative and a complementary marker.

**Measured budget, GitHub Actions.**

| | Python 3.10 | Python 3.14 |
|---|---|---|
| product suite | 190.1 s | 95.0 s |
| Fast Gate added | **45.4 s** | **22.8 s** |
| Deep Gate qualification | **377.1 s** | **168.7 s** |

Contracts: ≤60 s median added per matrix job with a 90 s ceiling, and ≤10 min for the
Deep Gate with a 12 min ceiling. All satisfied, nothing trimmed. The same Fast Gate
took 62.6 s locally, so extrapolating from the workstation would have argued for
cutting coverage the runners do not need — which is why the design requires sizing to
follow measurement.

**Historical sensitivity dossier.** Each guard run against the state it exists to
catch, with the historical tree verified in use:

| Guard | Bad state | Result |
|---|---|---|
| N-1 expanded decimals | `a1dc97b` | 10 failed / 2 passed, assertion failures |
| A-1 complex candidates | `e073320` | 3 failed, product raises the complex `TypeError` |
| A-2 open upper edge | `e073320` | 2 of 4 operator cases failed, exactly those whose topology involves a one-sided limit |
| H4-A over-broad completeness | `7f4a2c5` | 6 failed of 6 |
| all guards | `c3f4b14` | GREEN |

Obtaining that evidence required an isolated pytest configuration. Run from a
temporary tree, pytest still discovers the repository `pyproject.toml` as its
configfile and prepends the current `src`, so the guards initially **passed** while
appearing to exercise the historical code. That false GREEN is the mirror of the false
RED the plan already guarded against, and `docs/quality-gate.md` records the procedure
that avoids both.

**H4 replacement.** `(x - a)*(x^5 + b*x + c)` with `b > 0`. The derivative `5x⁴ + b` is
strictly positive, so the quintic is monotone and has exactly one real root: the count
comes from calculus and the location from test-local bisection, so no symbolic solver
participates in forming the expectation. The earlier candidate that embedded the root
in the coefficients was rejected because SymPy could then factor it out, leaving the
guard green against the very implementation it existed to catch.

## Roadmap / active plan

1. **Permanent Quality Gate** — **DONE**, merged at `38b28d5` and qualified on `main`.
   QA infrastructure only, no production change. Still green on every push.
2. **Engineering Presentation** — **DONE**, released as 0.10.0 and merged at `4a018fb`.
   P-1, P-2 and P-3 corrected; one production file changed.
3. **EP-1** — **DONE**, released as 0.10.1. Design §4.5's band rule was specified and
   never implemented; §4.3's significant-figures criterion was doing both jobs. Measured
   10/10 against 8/10 before changing anything.
4. **QG-3** — **DONE**. The Deep Gate had no example database in CI at all.
5. Next, and now genuinely open: Exact Envelopes / Governing Intervals, scalar equation
   systems, named cases and combinations, verification APIs, golden engineering
   worksheets. Nothing among them is a defect; they are new work.

Versions beyond the next release are not committed, because the audits repeatedly
invalidated longer-horizon numbering.

### Independent audit of PR #37 — findings and resolution

Audited by a reviewer who did not implement the gate, before the merge. Ten of the twelve questions
passed outright; production changes zero; no mandatory Level A partition lost; no
authoritative Level D test; H4 independence and performance budgets both confirmed.

**QG-1 — artifact persistence was silently empty. CORRECTED.** Both
`upload-artifact` steps lacked `include-hidden-files: true`. Since v4 the action skips
hidden files by default and `.hypothesis/` is a dot-directory, so the artifact was
never produced. Verified against runs `33561021489` and `33560303585`: both report
`total_count = 0`. This broke the middle tier of the agreed persistence architecture —
cache for exploratory continuity, artifact as evidence of a run, committed regression
as authority — while the workflow still reported green.

The flag is added in both jobs, and a `Report Hypothesis database state` step now
prints whether the database exists. That second part is not cosmetic: this defect
survived review precisely because an empty artifact collection and a working one look
identical in a green log. An absence that cannot be seen is the same failure mode as
the false GREEN found during historical sensitivity, in a different place.

**QG-2 — Deep qualification not on the exact final head. ACCEPTED AS A BOUNDED
BOOTSTRAP EXCEPTION, NOW DISCHARGED.** The acceptance contract requires Deep qualification at the exact
release-candidate SHA. That requirement is operationally circular for this PR alone:
`workflow_dispatch` only registers once the workflow exists on the default branch, so
qualification must be reached through a temporary trigger, and recording the resulting
evidence moves the head again.

The exception is explicitly limited:

- it applies to PR #37 only, the commit that introduces the workflow;
- between the qualified head `9de3207` and the merge candidate, `quality_tests/deep`
  changed **only in one docstring**, with no effect on behaviour. Documentation, the
  Fast Gate evidence markers and the Deep workflow also changed, the last of these
  solely to correct QG-1 in the persistence and observability of the Hypothesis
  database. Verified: the `pytest` invocation, the per-property `max_examples`, the
  `derandomize` setting and the Python matrix are all untouched, so the qualification
  logic and corpus are the same ones that were qualified;
- the deep suite was run locally on the final content at 18 GREEN;
- **immediately after merge, `Quality Gate Deep` must be run in `qualification` mode
  against the merge commit on `main`. If Python 3.10 or 3.14 is not GREEN there, the
  Quality Gate is not considered integrated and Engineering Presentation does not
  begin.**

That condition is satisfied. Run **`33567836733`** ran `qualification` against
`38b28d5`, the merge commit itself, with Python 3.10 and 3.14 both SUCCESS. The
exception is discharged and the Quality Gate is integrated.

Once the workflow exists on `main`, every later qualification must be on the exact SHA
with no exception. The requirement is not weakened; it was acknowledged as unreachable
exactly once, for the change that creates the mechanism it depends on, and that once
is now spent.

**QG-3 — the QG-1 diagnosis is unverified and its fix is still unexercised. OPEN,
EVIDENTIARY ONLY.** Found while confirming QG-1 after the merge, not by the audit.

Hypothesis creates `.hypothesis/examples/` only when it has a counterexample to store.
On a passing run the directory never exists. Demonstrated directly with Hypothesis
6.167.1, the pinned version, in an isolated tree: a green property leaves no `examples/`
directory at all, and the same property made to fail leaves 22 files in it. The local
repository tree shows the same thing after green Deep runs — `.hypothesis/` holds only
`constants/`, and `examples/` is absent.

The consequence is that `total_count = 0` on runs `33561021489` and `33560303585` does
not demonstrate what QG-1 says it demonstrates. Both runs were green, so the artifact
would have been empty with or without `include-hidden-files`. The observation is
consistent with the hidden-file exclusion and equally consistent with there being
nothing to upload, and therefore distinguishes neither. The post-merge run confirms it:
with the flag in place, run `33567836733` still produced **zero** artifacts, and both
jobs printed `database absent: nothing to preserve from this run`.

This is not a functional defect and nothing needs to be reverted. `include-hidden-files`
is harmless and is probably necessary, since every path under `.hypothesis/` has a
hidden component — but "probably" is the whole point: no run has ever produced a
non-empty artifact, so the middle tier of the persistence architecture has never once
been observed working. It is the audit's own failure mode, an absence that cannot be
seen, reproduced one level up: in the evidence for the fix rather than in the fix.

Two things follow. First, `docs/quality-gate.md` reads as though the artifact is
produced on every run; it should say that the artifact appears only when the gate finds
something, which is by design. Second, the decisive test is cheap and has not been run:
force one Deep property RED on a throwaway branch, dispatch the workflow, and check
whether a non-empty artifact appears. Until that is done, the persistence tier is
designed and documented but not evidenced.

## Engineering Presentation - v0.10.0, RELEASED

Merged as PR #39 at `4a018fb`. Design:
`docs/superpowers/specs/2026-09-01-engcalc-v0.10.0-engineering-presentation-design.md`.
Thirteen contracts, 1079 tests, one production file changed: `renderer.py`.

| source | before | now |
|---|---|---|
| `v := 8e-05*m` | `0.00 m` | `0.08 mm` |
| `k = 2*v`, `numeric(k)` | `2(0.00 m) = 0.00 m` | `2(0.08 mm) = 0.16 mm` |
| deflection `P*L^3/(48*E*I_z)` | `5625.00 kN/(GPa*m)` | `5.63 mm` |
| table column of small values | every cell `0.00` | `0.00 0.08 0.16 0.24` in mm |
| `q := 2.8*tonf/m` | `2.80 tonf/m` | unchanged |
| `w := 1e-6*m` | `0.00 m` | `1.00e-6 m` |
| `z := 1e-11*m` | `0.00 m` | unchanged, genuine zero |

**The rule.** Provenance is a property of the result: a `NumericAssignmentResult` and any
value substituted into a derivation are declared, everything else is derived. A declared
unit is kept unless rendering it retains no significant figure. A derived unit is kept
when it came from the engineer's own inputs - measured by term count against the family's
canonical member, so `tonf` and `kN/mm` survive and `kN/(GPa*m)` does not - and otherwise
moves to the family member retaining the most significant figures, ties keeping what the
value already carries. Below the family floor, scientific notation in the declared unit.
`zero_tolerance` is evaluated in the stored unit, before any conversion.

Five presentation sites, not three: the scalar path, the matrix cell path
(`_magnitude_latex`) and the table cell path (`_table_magnitude`). A fourth fixed-decimal
format at `renderer.py:306` is a literal zero for an empty polynomial and is not a
collapse site; the enumeration is closed.

### EP-1 - CLOSED in 0.10.1

The root cause was not a subtle metric failure. **Design §4.5 specifies a band rule and it
was never implemented**; §4.3's significant-figures criterion, which exists to decide
whether a *declared* unit still says anything, was doing the family choice as well. One
criterion, two jobs, wrong for the second.

Measured before changing anything, over the cases that reach the family choice: the band
rule is right **10 out of 10** where counting figures is right **8**. Ties keep the unit
the value already carries, which is what leaves a derived 11 m span in metres instead of
`11000.00 mm` - the outcome design §5 had already measured and rejected.

Why the A-4 contract missed it, which matters more than the defect: it was written with
`L := 5*m`, where `L/300` is unterminating and millimetres win four figures to one. With
`L := 6*m` the quotient is exactly 0.02 and the comparison ties. **The contract passed
through the case rather than through the rule.** Its replacement carries a guard asserting
the tie, so it cannot quietly stop testing what it claims to test.

Re-running the mutation battery afterwards found two guards that had stopped guarding: the
aggregate authorship gate, invisible because the band rule now reaches the same answer on
the only case that covered it, and a tie-break comment crediting `start` with a result the
band rule produces unaided. The first has a contract where the two rules genuinely
disagree; the second is documented as inert, since every family steps by 1000 or more and
a tie can never occur.

### QG-3 - CLOSED, and it invalidates QG-1

**The Deep Gate had no example database in CI at all.** Hypothesis auto-loads a built-in
`ci` profile when it detects CI, setting `database=None`; a profile registered afterwards
inherits it. `quality_deep` set `derandomize` explicitly - so exploration survived - and
never set `database`.

| environment | resolved database |
|---|---|
| local | `DirectoryBasedExampleDatabase(.hypothesis/examples)` |
| `CI=1 GITHUB_ACTIONS=1` | **`None`** |

For its entire existence the gate stored counterexamples locally and none in CI, which is
the only place it runs. Nothing was saved, the cache restored nothing, the artifact had
nothing to upload, and every run reported green.

Found by forcing a Deep property red on a throwaway branch: the test failed in CI exactly
as intended and the job still reported `database absent`, contradicting the same failure
locally, which writes 13 example files. Rather than guess, the workflow was instrumented
to print the resolved path. It printed `None`.

**Proved closed rather than argued closed.** The same deliberate failure on top of the fix,
run `33592040244`: `configured database: DirectoryBasedExampleDatabase(PosixPath(...))`,
and artifact `hypothesis-examples-py314-33592040244`, **1288 bytes**. The middle tier of
the persistence architecture has now been observed working, for the first time.

That corrects **QG-1**, which attributed the empty artifact to `upload-artifact` skipping
hidden files. The flag it added is harmless and probably right, but there was never a
database to skip. QG-3 had already recorded that the cited evidence could not distinguish
the two explanations; it was the other one.

`tests/test_quality_gate_profile.py` now asserts the profile in a subprocess under CI
environment variables, in the ordinary suite on every push, because the defect only exists
under those variables.

### What this release is missing

**It was never independently reviewed**, by explicit direction. The design, its audit, the
contracts, the implementation and the mutation battery are one perspective. Six things
passed for the wrong reason before being caught (spec §9.1, §9.2), EP-1 is the seventh,
and the two defects that actually shipped in the implementation were caught by tests
written in earlier sessions - not by this release's own contracts.

### Roadmap - Etapa 1, ecuaciones y calculo

The route is chosen from the measured gap map, filtered by the user's own statement of
what EngCalc is for: **a place to solve the exercise, with the code's help - not a place
to verify a design.** That excludes `check()`, `summary()` and `report()` from the
critical path, and demotes `case`/`combo`, which measurement showed is already achievable
with plain functions: `M_U1(x) = 1.2*M_D(x) + 1.6*M_L(x)` works today.

| Step | State |
|---|---|
| **1.0 `integrate` canonical**, `integral` a permanent alias | **DONE, 0.11.0** |
| **1.1 scalar equation systems** | **DONE, 0.12.0 — gap map 4/18 → 7/18, as predicted** |
| **1.2 indefinite integral** | **DONE, 0.13.0** |
| **resolve namespace symbols at numeric time** | **DONE, 0.18.0 — gap map 10/18 → 11/18** |
| **1.3 multi-solution `solve`** | **DONE, 0.14.0 — gap map unchanged at 7/18, and why is recorded** |
| **2.1 Macaulay `<x-a>^n`** | **DONE, 0.15.0 — gap map 7/18 → 8/18, as predicted** |
| **3.1 evaluated summation** | **DONE, 0.16.0 — gap map 8/18 → 9/18** |
| **3.2 multi-variable `subs`, 3.3 `assume`** | **DONE, 0.17.0 — gap map 9/18 → 10/18. Etapa 3 complete** |
| **`governing()`, with exact boundaries** | **DONE, 0.19.0 — gap map 11/18 → 12/18** |

Etapa 1 complete takes the gap map from 4/18 to 9/18. Measured after each step, on
`python tools/gap_map.py`:

| after | exercises end to end | broken lines |
|---|---|---|
| 0.10.1 | 4 / 18 | 24 |
| 0.12.0, scalar systems | **7 / 18** | 21 |
| 0.13.0, indefinite integral | 7 / 18 | **17** |
| 0.14.0, multi-solution solve | 7 / 18 | 17 |
| 0.15.0, Macaulay brackets | **8 / 18** | **15** |
| 0.16.0, evaluated summation | **9 / 18** | **14** |
| 0.17.0, multi-subs and assume | **10 / 18** | **13** |
| 0.18.0, namespace resolution | **11 / 18** | **12** |
| 0.19.0, governing intervals | **12 / 18** | **11** |
| 0.20.0, report and summary | **13 / 18** | **9** |
| 0.21.0, assumption-filtered solve | **13 / 18** | **8** |
| 0.22.0, numeric reads unit literals | **14 / 18** | **7** |
| 0.23.0, inequality solve | **15 / 18** | **6** |
| case and combo | **16 / 18** | **2** |

1.1 delivered exactly what the map predicted for it alone. 1.2 completed no further
exercise, which the map had also predicted, and the reason turned out to be a gap nobody
had identified rather than the constant-of-integration the map guessed at. Broken lines
still fell, so the progress is real even where the exercise count does not move.

### The gap 1.2 uncovered

**A definition captures its free symbols, and `numeric(...)` resolves symbols from the
numeric context - values given with `:=` - not from the symbolic namespace where a solved
constant lands.**

```text
y = 2*k ; k = 5      ; z = y       -> 2*k      a definition captures, it does not refer
y = 2*k ; k = 5      ; numeric(y)  -> refuses
y = 2*k ; k := 5*kN  ; numeric(y)  -> 10 kN    resolved from the numeric context
```

So E4 derives its elastic curve symbolically end to end - the textbook `C2 = 0` and
`C1 = -qL³/(24 E I_z)` - and stops one step short of a number, because `v(x)` was defined
before the constants were known and keeps their symbols.

It is not obvious that the answer is to make `numeric` resolve the namespace: capture is
consistent across the whole language, and changing it is a core-path change with an
unmeasured blast radius. Measure before deciding, as with the unit metric.

### The gap 0.21.0 uncovered: `numeric()` does not read unit literals

**CLOSED in 0.22.0.** The analysis below is kept because its premise was wrong in an
instructive way, and the correction is recorded at the end of the section.

`M = 5*kN` then `numeric(M)` fails with *"requires values for: kN. Define the missing
numeric values first, for example: kN := <value>*<unit>"* - advice nobody should follow.
In the symbolic layer a unit is an ordinary free symbol, and only the characteristic
domain path (`_resolve_domain_numeric_value`) calls `unit_literal_overrides` to resolve
one. This predates 0.21.0; E14 simply never reached the line before.

It is what still blocks E14's last line. `L_max` comes out of the solve carrying `kN`
from the `500*kN` the engineer wrote, so asking for its number fails.

The one-line fix - pass `unit_literal_overrides` on the `numeric()` path too - is not
safe as it stands. Of the fifteen unit aliases, three are single letters: **N, m, s.**
`N` is axial force in any structures memoria. A sheet that writes `sigma = N/A` and
forgets to define `N` is told so today; with the aliases resolved it would silently be
told that sigma is one newton per unit area. Partial resolution does not save it either:
if `A := 100*mm**2` is defined and `N` is not, every symbol resolves and the wrong
answer is complete and quiet.

The distinction that would settle it - a symbol that entered the expression from a unit
literal in the source, as opposed to a bare undefined name - is erased by the time the
symbolic layer stores `Symbol('kN')`. Restoring it means marking unit literals at parse
time, which is a real change and not this one.

**What that reasoning missed.** `:=` already resolves undefined unit aliases as units:
`sigma := N/A` returns `0.01 newton/mm**2` and always has. The hazard was never being
introduced - it was already there, on the more heavily used of the two paths. The actual
defect was the disagreement between them, and the fix is to make `numeric()` follow the
rule the numeric layer had all along.

The N/m/s collision remains real and is now pinned by
`tests/test_numeric_unit_literals.py::test_an_undefined_axial_force_reads_as_newtons`,
which asserts the two paths agree rather than asserting the behaviour is desirable. It
lives in one place instead of two, so a decision to warn is a change to one contract.

**Two measurements are worth keeping.** A counter on the new branch stayed at zero across
all 1203 tests: the existing corpus never reaches it, so the green suite was evidence of
no regression and no evidence whatever that the change worked. Those had to be
established separately, and the contracts exist because of that.

And the first attempt put resolved units into the substitution dictionary, which crashed
the renderer outright - a Pint `Unit` has no magnitude. The near miss was to "fix" that
by substituting `1*kN` and printing `kN = 1 kN` under the working, a line no engineer
writes. Units resolve for the arithmetic and stay out of the substitution stage.

### What the gap map does not measure

**The gap map catches exceptions and nothing else.** Every "N/18 exercises run end to
end" in this document and in PRs #46 to #62 means N exercises raised no error. It has
never meant that a single answer was right, and an exercise returning a number wrong by
a factor of a thousand is reported as a success.

Measured rather than argued, by breaking the product and running both:

| Defect introduced | Gap map | `tests/test_exercise_answers.py` |
|---|---|---|
| Macaulay bracket permanently on | **15/18, green** | caught |
| summation drops its last term | **15/18, green** | caught |
| bracket opens one step early | **15/18, green** | caught |
| definite integral loses its bounds | 14/18 | caught |

Three of four leave the gap map completely green. The first ruins every beam carrying a
point load.

`tests/test_exercise_answers.py` closes this for the fifteen exercises that run. Every
expected value is worked from the statics, and where a textbook formula exists it is
quoted as a second independent check - a propped cantilever's prop reaction is 3qL/8
whatever EngCalc thinks, and the flexibility method has to arrive there on its own.

The two numbers answer different questions and both are worth keeping. The gap map says
how much of the language an exercise can reach; the answer file says whether what came
back is true. Quoting the first as evidence of the second is the mistake this section
exists to prevent.

### Nobody had ever looked at the output

Elias has never run EngCalc in Colab. He has been trusting the reports, and every report
until 0.23.1 rested on the same kind of check: that a LaTeX string contains a substring.
A string that renders as garbage contains all the same substrings.

The first time the product was rendered and read, it had **three defects in merged
releases**, all with passing contracts:

| Defect | Shipped in | Contracts said |
|---|---|---|
| `solve(ineq, ...)` raised AttributeError and killed the cell | 0.23.0 | green |
| `governing(...)` HTML embedded inside a LaTeX array | 0.19.0 | green |
| `summary()` the same | 0.20.0 | green |

Every one of those contracts called `render_characteristic_result` or
`render_summary_result` directly. None asked whether the magic would route anything to
them, and the magic listed its types in a hand-written tuple. `tests/test_characteristics_magic.py`
had established the right pattern in 0.9.x; three features were added without following it.

The routing now goes through the `CharacteristicResult` and `HtmlBlockResult` unions in
the renderer, so a type added to a union is routed without anyone remembering.

`tools/render_memoria.py` is the instrument that found them. It drives the real magic and
writes the page a notebook would show. **Run it and look at it** before believing a
presentation claim.

Two more came out of the same render and are now closed. The system-solve block was not
merely misaligned: `render_system_solve_result` built a single-column array which
`_standard_result_row` then split on its first " = ", injecting `& = &` into an
environment declared `{l}`. Fixed in 0.23.1 by making each equation and each unknown a
row of the sheet's own array. Two contracts had asserted
`latex.count(r"\displaystyle") == 4` on the flat form, and the count was identical for
the mangled output.

Aligning it exposed the next one: every equation printed twice, once as its definition
and once as the solve's echo. Fixed in 0.23.2. An equation passed by name is left where
it is; written inline it is shown, because it exists nowhere else. The rule tests for a
name **bound to an equation**, not merely for a name: `solve(delta_B, R_B_aux)` names an
expression and displays `delta_B = 0` with the integral evaluated, which the reader has
not seen.

The remaining three were closed in 0.23.3, and the third turned out to be a consequence
of the first. Scientific notation now applies above a ceiling as well as below the floor,
so `80000000.00` is `8.00 x 10^7`; a multi-letter base renders upright, so `eqFy` is one
name rather than four sliding letters; and a power of ten uses `	imes` rather than
`\cdot`, because the wrapped-product continuation already owns the dot and
`\cdot 1/(8.00 \cdot 10^7 mm^4)` gave one mark two meanings four characters apart.

The `\quad \cdot` continuation marker itself was left alone. It is a contracted choice
from earlier work, and once the glyphs stopped colliding it reads correctly.

### Quality Gate: a lapse, recorded

**0.10.1, the QG-3 fix, 0.11.0 and 0.12.0 were merged without a Deep Gate
qualification.** The last successful one before this entry was run `33584467099` on
`4a018fb`, which is 0.10.0. The rule written in `docs/quality-gate.md` says every
release candidate is qualified on its exact SHA, and four merges went by without it.

No evidence of harm: the Fast Gate's 154 tests ran on every one of them, and CI was green
on Python 3.10-3.14 throughout. But this is precisely the kind of discipline that erodes
without anyone noticing, which is why it is written here rather than quietly resumed.
Corrected by qualifying the current `main`; the result is in the baseline above.

### The solve API, decided by research rather than by taste

`solve(eq1, eq2, R_A, R_B)` names the unknowns as trailing arguments, renders both
results labelled in the memoria, and **defines them**:

```text
R_A = qL/2 = 30.00 kN
R_B = qL/2 = 30.00 kN
```

One shape at any number of unknowns, so `solve(eq1, V_B)` behaves the same and the
existing `V_B = solve(eq1, V_B)` keeps working.

Two alternatives were considered and rejected, both after checking what established
systems do:

- `R_A, R_B = solve(...)` - **positional destructuring, rejected.** No CAS does this.
  SymPy returns a dict, Mathematica returns rules, Maxima returns `[x = ..., y = ...]`,
  TI-Nspire returns `x=... and y=...`, Mathcad assigns a vector from `Find(x, y)`. Every
  one of them returns *labelled* results. Positional targets introduce a silent swap:
  `R_B, R_A = solve(eq1, eq2, R_A, R_B)` crosses the values with nothing to catch it.
- keeping two shapes, one per arity - rejected as incoherent in a language written by
  hand, which is how the user put it.

Defining the unknowns as a statement effect was the objection to this design, and it does
not apply here: `q := 2.8*tonf/m` and `M(x) = ...` already define by statement. It does
change one behaviour deliberately - today a bare `solve` binds nothing - and that is
recorded rather than silent.

**The mathematics is not the work.** `sp.solve([e1, e2], [R_A, R_B])` already returns
`{R_A: L*q/2, R_B: L*q/2}` and SymPy is already a dependency. What 1.1 builds is the API
and the rendering.

## How to resume in a new conversation

Read this file first. `main` is at `9a9d6e3`, **EngCalc 0.13.0**, CI green on Python
3.10-3.14, Deep Gate qualified, 1116 tests green, and verified installable and working in
Google Colab from the documented `git+https` path.

**No defect is open.** The active work is Etapa 1 of the roadmap above, chosen from the
measured gap map rather than from a feature list: 1.0, 1.1 and 1.2 are done and **1.3,
multi-solution `solve`, is next**. The gap map has gone from 4/18 to 7/18 exercises
running end to end, with broken lines down from 24 to 17; re-measure with
`python tools/gap_map.py`.

Two things are carried rather than open: the gap 1.2 uncovered - a definition captures
its free symbols and `numeric(...)` does not resolve them from the symbolic namespace -
and the seven families `docs/quality-gate.md` says the gate does not cover.

Read `docs/quality-gate.md` for how to operate the gate: the isolated configuration that
historical sensitivity runs require, the qualification-SHA rule and the consequence that
its run identifiers can only be recorded after a merge, and the requirement that the
Hypothesis profile set every setting the environment could otherwise decide.

Two rules that have each paid for themselves repeatedly: never merge without explicit user
approval, and never let whoever built something be the one to certify it. The second is
suspended by explicit direction and what that costs is documented rather than argued.

The habit that has caught more than either rule: **measure before concluding, including
about your own work.** In this project a confident recommendation has been overturned by
measurement four times, an analysis of a measurement was wrong twice, and an intermittent
test failure was nearly blamed on the change in hand until `main` was measured at the same
failure rate. Nothing here is believed because it reads correctly.

Never invoke Codex / Codex Cloud without explicit authorization.
