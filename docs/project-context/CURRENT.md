# EngCalc Current Project Context

> **Read the block directly below, then `NEXT.md`.** Everything after it was last
> updated at 0.13.0 on `9a9d6e3` and describes a tree that no longer exists. Its
> *approved behaviour* and *evidence hierarchy* sections are still in force and are
> regression requirements; its baseline numbers, release history and open-issue list are
> not — do not quote its counts.

## Where things stand today

_2026-10-04._

| | |
|---|---|
| released | **0.45.7** - #396 (a complex pair beside a large eigenvalue refused); 0.45.6 - #395, `dd6da36` |
| before that | **0.45.5** - #393, `83ae814`, closed |
| open PRs | none; branch `feat/numeric-eigenvalues` (chapter 9 fixes; audits 1-2 NOT CLEAN, 3 clean with conditions, 4 NOT CLEAN by a hair, fixed, follow-up CLEAN; 0.45.6 release PR); the fold branch held |
| default suite | **3660 passing** on 0.45.7 (SymPy 1.14 and 1.13.3), about two minutes with `-n auto` |

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


### His exercise 2.1 as a reference sheet (branch `test/exercise-2-1-reference`)

His call left to me (*"lo dejo a tu criterio"*, 2026-09-26). `tools/ejercicio_2_1.eng` is
the angles solution he chose; `test_his_exercise_2_1_gives_the_book_s_answer.py` runs it
with the kN palette and without, no notice, u 2.41 / v 0.72 / aa' 2.52 / δ 2.41, -0.87 mm;
it is also typeset by Colab's KaTeX (`exercise-2-1` in
`test_colab_can_typeset_every_formula`).

### A value line reads a formula (branch `feat/a-value-line-reads-a-formula`)

He left it to me (*"Lo dejo a tu decisión. Think carefully"*, 2026-09-26). A `:=` line
already read a matrix built with `=` and a kept name; a plain scalar `=` formula was the
one gap (`D := [delta_ab; delta_ac]` said "unknown numeric name"). Decided: read it.
`NumericContext.resolve_numeric_name` asks `_scalar_formula` (the shared
`symbolic_namespace`) after the unit aliases, so only names that failed before are read
and a formula named `m`/`N` is still the unit. The number is taken with the values settled
then, as every `:=` line; a formula still missing values says which. `%eng_help :=` and a
README section say so. 6 contracts (5 RED before; the precedence one killed its
mutant); suite 3123 on SymPy 1.14 and 1.13.3.

### A value in a function, and a sum as written (branch `fix/function-arguments`)

The two findings of his exercise 2.1, which he asked to address (*"Aborda estos
hallazgos"*, 2026-09-26):
- `renderer._bracketed`: a substituted value directly inside a function's own
  parentheses (`_FUNCTIONS_IN_PARENTHESES`: trig, inverse trig, hyperbolic, log, sign,
  Min, Max, a sheet function) takes no brackets of its own - `sin(0.93 rad)`,
  `max(45.00 kN, 30.00 kN)`. In a product, sum or power, under a root, between bars or in
  an exponent it keeps them.
- `engine.record_written_sums` + `renderer.WRITTEN_SUMS` / `sum_term_key`: a sum the
  sheet wrote reads in its written order (`sin(θ + φ)`, `√(6² + 4²)`,
  `h - cover - db_st - db/2`). A term is known by its names, or by its size when it has
  none; only a sum whose terms are exactly the written ones is reordered, the first
  writing is kept, and a written order that opens with a minus leaves the sum to the
  0.31.17 rule as before.
No reference page and none of the 13 harness sheets move. 20 contracts; suite 3137 on
SymPy 1.14 and 1.13.3.

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

All three findings above were addressed with his yes (*"tienes mi Sí para todo"*,
2026-09-26): #336 (brackets once, sums as written), #337 (`:=` reads `=`), and his
exercise is `tools/ejercicio_2_1.eng` (#338).

**0.39.0 is closed** (#339, `edc95d5`, carrying #326-#335). On the release tree: version
assertions RED (7) then GREEN; suite 3119 twice (SymPy 1.14), 3117 on 1.13.3 (the two
installed-metadata contracts deselected: that venv holds the 0.38.0 wheel); wheel from
`git archive`, 33 files identical to `src`; a clean Colab-like venv (3.12, ipython 7.34.0,
numpy 2.2.6, matplotlib 3.10.0, sympy 1.13.3) gains only Pint 0.26.1 and four small deps;
smoke outside the repository 101/101 (scratchpad `smoke-0390/`; its first run found the
`% while` counter defect, fixed by #335 before the release); suite against the wheel 3118 +
the by-construction `test_the_ipython_surface_stays_small`. After the merge: CI, Quality
Gate Deep (push) and Deep in qualification mode green on `edc95d5`; a clean
`git+https` install resolved to `edc95d5`, reported 0.39.0, upgraded nothing, 33 files
identical to the tree, smoke 101/101.

**0.40.0 before its merge** (#336-#338): version assertions RED (7) then GREEN; suite 3158
twice (SymPy 1.14); wheel 33 files identical to `src`; clean Colab-like venv gains only
Pint and four small deps; smoke 104/104 (`smoke-0400/`: brackets once, sums as written,
`:=` reads `=`; the `min` check now reads `min(2.00 m, 2.22 m, 3.00 m)`); suite against the
wheel on SymPy 1.13.3: 3157 + the by-construction one.

**0.40.0 is closed.** After its merge: CI, Quality Gate Deep (push) and Deep in qualification
mode green on `ea79f53`; a clean `git+https` install resolved to `ea79f53`, reported
0.40.0, upgraded nothing, 33 files identical to the tree, smoke 104/104. In his Colab
("Untitled9"): session restarted from the menu, his cell 0 (`--upgrade --no-cache-dir`)
built and installed it, cell 2 (the angles sheet) reads `sin(θ + φ)`, `cos(0.93 rad)`,
italic `aa`, u 2.41 / v 0.72 / aa' 2.52 mm. Slip recorded: a `Ctrl+M .` sent while his
cell 1 editor had focus typed `period` into its first line; removed at once by checking
the exact text (583 characters, as before). Restart from the menu, never by keys.

### Angles in degrees (branch `feat/angles-in-degrees`, PR open, left to me)

He left it to me (*"Aborda el punto 2 según tu recomendación, lo dejo a tu criterio"*,
2026-09-26). `renderer._display_quantity`: an undeclared plain radian (an `atan`, an
`asin`) is shown in degrees - `θ = 33.69°`, `sin(53.13°)`; `t := 0.5*rad` keeps rad,
`rad/s` untouched. A degree is written `33.69^{\circ}` (`_quantity_latex`,
`_latex_unit_text`, `unit_text` / `quantity_text` "°"), tables of angles convert
(`_aggregate_unit`, `_in_unit`) and read `[°]`, the plot axis too. `numeric(name)` of a
value is one row (`_is_a_value_by_its_name`): `w = 374.98 1/s`, not `w = w = (...) = ...`;
a declared angle keeps its radians there. 13 contracts; 8 older ones pinned `rad`/`deg`
text and were updated; no reference page and none of the 13 harness sheets move; suite
3169 (1.14), 3167 (1.13.3, the two installed-metadata contracts deselected).
Found, not fixed: `extrema(atan(x/L), x, 0, L)` says "extrema response values have
incompatible dimensions" (also on 0.40.0).

Angles merged with his yes as #342 (`465a2dd`).

### Units in brackets (branch `feat/units-in-brackets`, PR open)

The name-that-is-a-unit trap. He rejected refusing unit-named variables (*"sí hay veces
que uso como variable m, s o N"*), asked for a different way to write units, and chose
brackets with no brackets on the page (2026-09-26). `6_m` was discussed: rejected for
compound units (`10_kN/m` cannot say where the unit ends). Built:
- `parser._rewrite_bracketed_units` (in `normalize_expression`, before `^` and before
  matrix literals): `number[units]` -> `(number*__u_unit...)`; only after a number, so
  `d[1,1]` stays an index; a name inside that is not a unit alias is refused with its
  line; `__u_` names cannot be targets. `numeric.BRACKETED_UNIT_PREFIX` entries join
  `_UNIT_ALIASES`, so everything downstream reads them as units; `_print_Symbol` drops
  the prefix.
- `resolve_numeric_name`: a sheet formula outranks the unit its name spells, as a value
  did (reverses #337's order): `m = 3*a`, `x := 4*m` = 24 kg.
- `engine._refuse_a_name_beside_a_unit`: a name of the sheet spelled like a unit, in
  one product with another plain unit (`2000*kN/m`, `5*m/s`), stops the line with
  `write the unit in brackets ..., as 2000[kN/m]`; `numeric`'s target unit is not read.
  The SDOF re-run no longer draws `4.00 kN/kg`.
- `%eng_help :=` recommends `6[m]` (its example runs with brackets, matrices too);
  README section. 23 contracts; 5 older ones updated (the re-run notices became a stop);
  no reference page moves; the 13 harness sheets move only by the notice's words.

#343 merged with his yes (*"Fusiona #343 y publica la 0.41.0"*), released as 0.41.0 with #342.

**0.41.0 before its merge**: version assertions RED (7) then GREEN; suite 3192 twice
(SymPy 1.14); wheel 33 files identical to `src`; clean Colab-like venv gains only Pint and
four small deps; smoke 107/107 (new scratchpad `c0d9fc55.../smoke-0410/`: brackets, the
re-run stop, degrees; the old re-run notice and `sin(0.93 rad)` checks now read the new
behaviour); suite against the wheel on SymPy 1.13.3: 3191 + the by-construction one.

**0.41.0 is closed.** After its merge: CI, Quality Gate Deep (push) and Deep by dispatch
green on `e879667`; a clean `git+https` install of `main` in a Colab-like venv (3.12,
ipython 7.34.0, numpy 2.2.6, matplotlib 3.10.0, sympy 1.13.3) resolved to `e879667`,
reported 0.41.0, upgraded nothing (adds Pint 0.26.1, flexcache, flexparser, platformdirs,
typing_extensions), 33 files identical to `src`. The 107-check smoke of `smoke-0410/` lived
in the previous session's scratchpad and is gone; a new one, kept as
`tools/smoke_installed.py`, 27 checks through
`%load_ext` from outside the repository (brackets, the re-run stop, degrees, one-row
`numeric`, `:=` reads `=`, sums as written, `min`, no real value, `% if/for/while`, Hz,
eigen units, kgf, `%eng_help :=`), each after `%eng_reset`: 27/27. The 8 `tools/*.eng`
sheets in three palettes (none, kN, kgf), 24 pages, render byte-identical from the
installed package and from the tree. Source suite on `e879667`: 3192 passed (SymPy 1.14,
KaTeX installed with `npm ci --prefix tools/katex`; without it 30 skip). **Not done: the user's Colab** - not reachable from
the session that closed it; the user checks it with cell 0 after a restart from the menu.

Found while closing, not caused by 0.41.0, not fixed:
- **A `:=` value outlives a later `=` of the same name** (also on 0.40.0, any name):
  `p := 500*kg`, `a := 2`, `p = 3*a`, `x := 4*p` gives `x = 2000.00 kg`, not 24, in
  silence; the other order (`=` then `:=`) is right. With a unit letter (`m`) the notice
  printed says the line "read 'm' as a unit when it ran before", which is not what
  happened. Proposed: a `=` line drops the name's `:=` value, as a `:=` replaces a
  formula. Needs the user's yes (it changes which value a sheet reads).
- `%eng_units none` is refused with "unknown unit palette 'none'; available: kN, kgf
  (or none to clear)" - the help means an empty argument. Either accept `none` or say
  "(or nothing, to clear)".

He answered both on 2026-09-26 (*"Sí a los dos, procede con TDD"*), from a new Claude
account; the handoff through this file and `NEXT.md` matched what the old session held.

**#346 (`fix/an-equals-line-drops-the-old-value`), a `=` line drops the number.**
`engine._drop_the_number`: a `=` line without `keep` (and a named `p = numeric(...)` line)
drops the name's `:=` value and its keep mark; `keep p = numeric(...)` stores the new kept
number. Reproduced first, and it reached `keep` too: `keep d = h - 4*cm`, `d = 3*h`,
`x := 2*d` read 112 cm (the old kept number) and, left marked, `numeric(2*d)` stopped
asking for `d`. `numeric.written_unit_names` now asks for a sheet formula before the unit
alias, as `resolve_numeric_name` has since #343 - that is what made the `m` sheet, run
again, say "'m' has been read as a unit". 12 contracts
(`test_the_last_definition_is_the_one_read.py`), 9 RED on `4f0b77d`; mutation 6/6 (a
seventh line, `kept_values.discard`, had no observable effect and was removed); suite 3204;
the 24 `tools/*.eng` pages byte-identical to `main`.

**#347 (`fix/eng-units-none`, base #346's branch), `%eng_units none` clears.** `none` in any
case is the empty argument; the empty argument is unchanged; README says so. 5 contracts,
all RED before; the `.lower()` mutant killed; suite 3209.

He then authorised the merges and the release (*"Tienes mi autorización para proceder con
fusiones, publicaciones etc..."*). #346 squashed as `5a10d74` on green CI at `88d1a26`;
#347 rebased onto it (diff byte-identical to the stacked one, tree identical to the tested
head), retargeted to `main`, green at `ada6e0f`, squashed as `f4d5e03`.

**0.41.1 before its merge**, on the release commit's tree: version assertions RED (7) then
GREEN; source suite 3209 twice (SymPy 1.14); a wheel from `git archive`, 33 files identical
to `src`; installed in a clean Python 3.12 venv holding Colab's pins (ipython 7.34.0, numpy
2.2.6, matplotlib 3.10.0, sympy 1.13.3) it adds Pint 0.26.1, flexcache, flexparser,
platformdirs, typing_extensions and upgrades nothing; `tools/smoke_installed.py` (three
checks added: `=` drops a `:=` value, `=` after `keep`, `%eng_units none`) 30/30 from
outside the repository; the suite against the wheel on SymPy 1.13.3, from a copy of the
tree with no `src/` and KaTeX installed: 3208 + `test_the_ipython_surface_stays_small`
passing on the wheel's own `magic.py`; the 8 `tools/*.eng` sheets in three palettes, 24
pages, byte-identical from the wheel and from the tree.

**0.41.1 is closed** (#348, `05c5bf5`). After its merge: CI (six jobs), Quality Gate Deep
(push) and Deep in qualification mode by dispatch green on `05c5bf5`; a clean
`pip install --upgrade --no-cache-dir git+https://...@main` in a Colab-like venv resolved
to `05c5bf5`, reported 0.41.1, upgraded nothing (adds Pint 0.26.1 and the same four small
deps), installed 33 files identical to `src`, and `tools/smoke_installed.py` passed 30/30
from outside the repository. **In his Colab** ("Untitled9"): his install cell printed
`0.41.1`; then, once the Claude in Chrome extension reached this session, I added cell 3
at the end (his cells 0-2 untouched), ran his cell 0 on a fresh runtime (26 s) and cell 3:
`engcalc 0.41.1`, `engcalc units: cleared (was kN)` for `none`, `x_t = 24.00` for
`p_t := 500*kg; a_t := 2; p_t = 3*a_t; x_t := 4*p_t`, `y_t = 3.60 m` (kN palette) for
`keep d_t = h_t - 4*cm; d_t = 3*h_t; y_t := 2*d_t`, and `th_t = 33.69°`. Cell 3 is marked
as mine and can be deleted; the palette was set back to kN.

Mechanics for the next session: after he signed the extension in with the new account,
`list_connected_browsers` stayed empty until this Code session was restarted; it then
listed "Browser 1" in use.

### The text under a heading is small and stops short (his report, 2026-09-26)

On his exercise 2.1 in Colab he found the paragraph under "Compatibilidad" a little small,
and its lines ending well before the width of the output. Three causes, read in
`renderer.narrative_latex`:

1. The size is `\footnotesize` (0.8 of the working: about 13.6 px beside the formulas'
   16.9 px, under Colab's own 14 px text). It was chosen on 2026-09-25, when he asked for the
   text two points smaller than the working.
2. The paragraph is broken at `NARRATIVE_LINE` = 76 characters of *source*, and a `$...$`
   span counts its LaTeX: `$u \cos\theta + v \sin\theta = \delta_{ab}$` counts 42 and shows
   about 15, so a line holding a formula breaks at a third of the width.
3. 76 characters (about 445 px) were measured for his window of 2026-09-25 (an output
   489 px wide). A wider output still breaks at 445 px; a narrower one scrolls. KaTeX does
   not break a paragraph that sits in an array inside a `{...}` group.

Measured, not assumed: typeset inline at the top level, as `\small \text{Lo }\allowbreak
\text{que }\allowbreak ... {u \cos\theta + ...}`, KaTeX 0.16.28 gives the browser 25 break
points in that paragraph against 1 today (`strict: "error"` accepts it). In his Colab
("Untitled9", cell 4, mine) the paragraph then filled the output's width at
`\footnotesize`, `\small` and normal size, the formulas unbroken. Proposed to him: the
browser breaks the lines (not a character count), and `\small`; the size is his choice.
To settle when building it: the room between paragraphs, the left edge beside the
working, the snapshots (every narrative line changes its LaTeX, not its words).

Re-measured on 0.41.1, from the "known" lists above: `0.90` is written `0.90` (fixed by
#323); an `N` never defined warns (his decision); `extrema(atan(x/L), x, 0, L)` still
stops with "extrema response values have incompatible dimensions"; `phiMn` over plain `d`
and `a` still expands them (`h - 0.59 As fy/(fc b) - cover`, the 0.85 and the 1/2 folded),
now in two rows, and `keep` still avoids it.

He chose the recommendation (*"Me gusta tu recomendación. aborda lo pendiente también"*):
the browser breaks the lines, `\small`. Built on `fix/text-fills-the-width`:
`narrative_latex` typesets a paragraph at the top level, a word at a time (`\text{word }`,
`\allowbreak` between, a formula as a `{...}` group, `\text{ }` after a formula),
paragraphs `\\[8pt]` apart; `_FRAME` and `NARRATIVE_LINE` are gone. `render.cjs` reports
KaTeX's `bases`; `conftest.in_one_run` reads a paragraph one run per style for the 22
contracts about what it says; `test_no_formula_is_printed_twice` takes a fraction's depth
out of each output (read over the joined page, a top-level paragraph break made the
working's `\\[17pt]` count as inner rows). 11 contracts (10 RED); mutation 8/8, two
unreachable branches removed; suite 3220; the 5 reference pages move in their 48
paragraphs only, same words in the same order (checked by script). **In his Colab**
(cell 4, the branch run in a subprocess so his install is untouched): exercise 2.1's
paragraphs reach the output's edge; "Compatibilidad" reads in two lines, both formulas
whole, the text aligned with the heading.

**`extrema` over an angle** (`fix/extrema-of-an-angle`, stacked on the text branch).
`extrema(atan(x/L), x, 0*m, L)` stopped with "incompatible dimensions": the values were
`0 rad` and `0.785 rad`, and the guard that refuses a plain number beside a unit asked
whether the unit *was* `dimensionless`. Pint counts a radian without dimension, so it now
asks `canonical_unit.dimensionless`, in `extrema._extrema_magnitude_in_unit` and in
`fallback._fallback_magnitude_in_unit` (which dropped every non-zero angle sample in
silence). The block reads `π/4 (45.00°)`, `asin`: `−π/6 (−30.00°)`; a characteristic value
in degrees is written `45.00^{\circ}`, as a row writes it, not `45.00\,{}^{\circ}`
(`_characteristic_quantity_latex`; no block could show one before). 8 contracts (4 RED,
then 2 more for the sign); mutation 7/7; suite 3228; no reference page moves.

Merged, each on green CI at its exact head: #351 as `d5fcd2f`; #352 rebased onto it (diff
and tree identical to the tested ones), retargeted, as `9996f29`. Released as 0.41.2 with
his standing authorisation (*"Tienes mi autorización para proceder con fusiones,
publicaciones etc..."*).

**The plain definitions that expand - measured, his decision.** `phiMn = phi*As*fy*(d -
a/2)` over plain `d = h - cover` and `a = As*fy/(0.85*fc*b)` reads `φ As fy (h - 0.59 As
fy/(fc b) - cover)`, the substitution in two rows; with `keep d`, `keep a` it reads `φ As fy
(d - a/2)` and `(0.90)(1500 mm²)(420 MPa)((460 mm) - (88.24 mm)/2)`. Two rules were tried in
scratch copies, not committed:
1. every scalar `=` definition kept: frames and the derivation get worse - `R_2 = R_1`
   hides the matrix, `k_v` reads `[k_11 ...]`, `K_c` loses its `b_1` - on 3 of the 8 sheets;
2. a scalar formula whose value is already a number kept (formulas over names without a
   value keep expanding, as a derivation needs): none of the 24 pages moves (they use
   `keep` where it matters), `phiMn` reads as with `keep`, and 11 contracts fail, among
   them the design's own `test_an_unmarked_definition_is_expanded_as_before` and
   `test_a_sheet_with_no_kept_name_is_unchanged` (`keep` was made opt-in on purpose, RC-3),
   `test_one_mode_at_a_time` and a value line of #327.
Rule 2 changes what an unmarked sheet shows, so it is his call.

**0.41.2 before its merge**, on the release commit's tree: version assertions RED (7) then
GREEN; source suite 3228 twice (SymPy 1.14); wheel from `git archive`, 33 files identical
to `src`; a clean Python 3.12 venv with Colab's pins gains only Pint 0.26.1 and the four
small deps, upgrades nothing; `tools/smoke_installed.py` (two checks added: a paragraph's
break points, `extrema` of an angle) 32/32 from outside the repository; the suite against
the wheel on SymPy 1.13.3, from a copy with no `src/` and KaTeX installed: 3227 +
`test_the_ipython_surface_stays_small` passing on the wheel's `magic.py`; the 24
`tools/*.eng` pages byte-identical from the wheel and from the tree.

**0.41.2 is closed** (#353, `915936b`). After its merge: CI (six jobs), Quality Gate Deep
(push) and Deep in qualification mode by dispatch green on `915936b`; his Colab path,
`pip install --upgrade --no-cache-dir git+https://...@main`, in the Colab-like venv that
held 0.41.1 changed only `engcalc-colab` (`05c5bf5` -> `915936b`), 33 files identical to
`src`, smoke 32/32 from outside the repository. **In his Colab** ("Untitled9"): session
restarted from the menu (Entorno de ejecución > Reiniciar la sesión > Sí), his cell 0
reinstalled, my cell 3 printed `engcalc 0.41.2`, a long paragraph reached the output's edge
with `M = qL^2/8` whole, and `extrema(atan(x/L_t), ...)` read `0 (0.00°)` global min and
`π/4 (45.00°)` global max. Cells 3 and 4 are mine and can be deleted.

### A formula whose names have values stays a name (rule 2, his yes)

He chose it (*"Sí, adopta la regla 2 por defecto. Lo dejo a tu criterio"*, 2026-09-26).
Branch `feat/a-valued-formula-stays-a-name`: `engine._a_formula_with_a_number` gives an
unmarked `=` definition the `keep` mark when the names it reads are all sheet names holding
a number (`:=` values or names kept before) and it works out as one number. Refined from
the measured rule 2 by what the first draft drew: a formula over a value written with `=`
(`M = q*L^2/8` over `L = 6*m`) was kept and then drew `10 kN (6 m)^2/(8 m)` - a sheet with a
kept name writes every `=` name in its written form - so such a formula folds as before. A
formula of a free variable (`M = q*x*(L - x)/2`) and a matrix are not numbers and are left.
`%eng_help keep` rewritten (its three claims run). 9 contracts
(`test_a_valued_formula_stays_a_name.py`, 4 RED); nine older contracts pinned "an unmarked
definition expands" and were rewritten with notes to reach their cases again - names without
values where they needed an expansion, the bracket and the 0.59 coefficient written out
or with the formulas before the values; mutation 6/6, two redundant conditions removed;
suite 3237 (and the changed files on SymPy 1.13.3); none of the 24 pages moves against
`main` rendered with the same Python (the figures differ between matplotlib 3.10 and 3.11,
nothing else); gap-map E4, E7, E8 read in their names.

Found with it, not caused by it, not fixed:
- a written form puts two numbers side by side with a space: `phiMn = fy*As*(d -
  fy*As/(0.85*fc*b)/2)` reads `\frac{fy As}{2 0.85 fc b}` (on 0.41.2 too) - it reads as
  "20.85"; its own PR next;
- E4's `M(x) = integrate(V(x), x, 0, x)` shows the integrand as `q L/2 - q x` under
  `V(x) = R_A - q x` (a kept name inside an integral's shown input; the same with `keep`).

**Two numbers side by side** (`fix/two-numbers-side-by-side`, stacked on #355). `sp.fraction`
gathers two denominators into `Mul(2, Mul(0.85, b, fc))`, and `_print_engineering_product`
set a dot only before a factor that *is* a number, so the nested one printed `2 0.85 fc b`.
A factor whose printed form begins with a digit now takes the dot too:
`{2 \cdot 0.85\,fc\,b}`. Reading the nested product as its factors was tried first and
took `interp`'s substitution fraction apart (`((0.70) - (0.50)) \frac{1}{...}`); reverted.
Asking also that the factor before it end in a digit changed nothing anywhere (suite,
24 pages, 18 exercises) and was dropped. 2 contracts, both RED before; suite 3239; no page
or exercise moves.

#355 merged as `5de01de` and #356, rebased onto it (diff and tree identical), as `a80d89d`,
each on green CI at its exact head.

**0.42.0 before its merge**, on the release tree: version assertions RED (7) then GREEN;
source suite 3239 twice (SymPy 1.14); wheel from `git archive`, 33 files identical to `src`;
a clean Colab-like venv gains only Pint and the four small deps; smoke 35/35 (three checks
added: a valued formula stays a name, a value written out still folds, two numbers set
apart); the suite against the wheel on SymPy 1.13.3: 3238 + the by-path surface test on the
wheel's `magic.py`; the 24 pages identical from the wheel and from the tree.

**0.42.0 is closed** (#357, `1ddcdd3`). After its merge: CI (six jobs), Quality Gate Deep
(push) and Deep in qualification mode by dispatch green on `1ddcdd3`; his Colab path,
`pip install --upgrade --no-cache-dir git+https://...@main`, in the Colab-like venv that
held 0.41.2 changed only `engcalc-colab` (`915936b` -> `1ddcdd3`), 33 files identical to
`src`, smoke 35/35 from outside the repository. **In his Colab** ("Untitled9", 2026-09-27,
0:47): the runtime had closed, so his cell 0 installed 0.42.0 on a fresh one (27.6 s); my
cell 3 printed `engcalc 0.42.0`, `phiMn_t = φ As fy (d - a/2)`, then `(0.90)(0.0015 m²)
(420.00 MPa)((0.46 m) - (0.0882 m)/2) = 235.81 kN·m` on his kN palette, and `M_t = As fy
(d - As fy/(2 · 0.85 fc b))`. His Chrome windows were minimized (the tab reported 0x0): the
Windows tool restored Chrome and a click on the tab brought it forward.

**A kept name does not reach an integral or a function built on a function** - measured
after the closure, on 0.42.0, the same with `keep`: over `R_A = q*L/2` (kept) and `V(x) =
R_A - q*x`, `M(x) = integrate(V(x), x, 0, x)` shows `∫_0^x (qL/2 - qx) dx = qLx/2 - qx²/2`
(E4), so does `integrate(R_A - q*x, ...)` written out, and `W(x) = 2*V(x)` reads
`q L - 2 q x`. Tried in a scratch copy, not committed: `integrate` and `diff` in
`_WRITTEN_FORM_SAFE_CALLS` gave a mixed row, `∫(qL/2 - qx) dx = R_A x - qx²/2` - the
integral's shown input (`_shown_input`) and a call of a function with a written body
(`_reaches_a_kept_name` does not look through `written_functions`) are two more places.
A design of its own that moves derivation rows: to measure on the pages and show him.

He asked for it (*"Sí, aborda el nombre guardado en integrales y funciones"*), with the
rows shown before anything is merged. Branch `feat/a-kept-name-reaches-integrals-and-functions`:
1. `_reaches_a_kept_name` counts a call of a function in `written_functions`: `W(x) =
   2*V(x)` reads `2 (R_A - q x)`.
2. `_a_written_form_may_call`: `integrate` and `diff` (`_CALLS_A_KEPT_NAME_MAY_WALK`) may
   be walked by a written form only on a line that reaches a kept name - on every line,
   `y = 2*diff(x^2, x)` read `2 · 2 x` (5 contracts caught it).
3. `_shown_in_kept_names`: the integral or derivative a row shows is read by the written
   evaluator in showing mode and kept only if, worked out (`doit`), it agrees with the
   value; `subs(V(x), L, 2*L)` - where `R_A` standing would be the wrong beam - falls back.
   The same restriction on calls as the written form: read through `solve`, the equation
   row was lost; through `sum`, it was written twice.
E4 reads `M(x) = ∫_0^x (R_A - q x) dx = R_A x - q x²/2`, `θ(x) = C_1 + ∫ (x R_A - q x²/2)/(E I)
dx = C_1 + R_A x²/(2 E I) - q x³/(6 E I)`, `v(x)` likewise; the deflection is -10.55 mm as
before. 9 contracts (4 RED); mutation 8/10 killed plus the solve/sum contract for one
survivor; the reach check survives by equivalence (no page or exercise moves without it,
3.73 s against 3.67 s for the exercises) and is kept as containment; suite 3248, the
changed files on SymPy 1.13.3 too; none of the 24 pages moves; of the 18 exercises only
E4, in the three rows above. Seen, not changed: inside an integral a product reads `x R_A`
where the result reads `R_A x` (the order inside integrals was already its own on 0.42.0:
`q x L/2`).

Shown the rows he asked what had been wrong and why it was not seen; told plainly that
0.42.0 had made the mixture visible in E4 (before it nothing stayed a name without `keep`,
and no reference sheet used `keep` before an integral). His yes: *"Fusiona #359 y publica
la 0.42.1"*. Merged as `8ddde86` on green CI at `9b17573`.

**0.42.1 before its merge**, on the release tree: version assertions RED (7) then GREEN;
source suite 3248 twice (SymPy 1.14); wheel from `git archive`, 33 files identical to
`src`; a clean Colab-like venv gains only Pint and the four small deps; smoke 36/36 (one
check added: a kept name inside an integral and a function of a function, `M(L/2)` 45 kN·m);
the suite against the wheel on SymPy 1.13.3: 3247 + the by-path surface test on the wheel's
`magic.py`; the 24 pages identical from the wheel and from the tree.

**0.42.1 is closed** (#360, `59cc98c`). After its merge: CI (six jobs), Quality Gate Deep
(push) and Deep in qualification mode by dispatch green on `59cc98c`; his Colab path,
`git+https` with `--upgrade`, in the venv that held 0.42.0 changed only `engcalc-colab`
(`1ddcdd3` -> `59cc98c`), 33 files identical to `src`, smoke 36/36. **In his Colab**
("Untitled9", 2026-09-27, 13:00): his cell 0 on a fresh runtime, my cell 3 printed
`engcalc 0.42.1`, `M_t(x) = ∫_0^x (R_t - q_t x) dx = R_t x - q_t x²/2`, `θ_t` in `R_t`,
`W_t(x) = 2 (R_t - q_t x)`, `M_t(L_t/2) = 45.00 kN·m`.

Seen in that check, older than 0.42 (the same on 0.41.2, with `keep`): `numeric(M(L/2))`
opens with the body in `x`, `M(L/2) = q L x/2 - q x²/2`, then substitutes `x = 3.00 m`, and
a kept name inside is expanded. It would read `R_A (L/2) - q (L/2)²/2`. To propose.

### A kept name reaches an equation (his "aborda el punto 1", 2026-09-27)

Branch `feat/a-kept-name-reaches-an-equation`, the step after #359:
- `_equation_in_kept_names`: the equation a single `solve` shows is read with the kept
  names standing (`R_A - q x = 0`, not `qL/2 - q x = 0`), an expression made `= 0`, and
  kept only if its difference agrees with the one solved; the answer is left as computed.
- `_written_form` takes an equation (`bc2 = eq(subs(v(x), x, L), 0)`), its two sides
  checked as one difference; `eq` joins `_CALLS_A_KEPT_NAME_MAY_WALK`.
Moves, of the 24 pages none; of the 18 exercises three: E4's `bc_2 = L C_1 + C_2 -
qL⁴/(24 E I) + R_A L³/(6 E I) = 0`, E9's compatibility `D_B0 + V_B f_11 = 0 m` (written
`0*m`; it read `L³V_B/(3EI) - qL⁴/(8EI) = 0`), E13's `5qL⁴/(384EI) = d_adm` (it read `=
L/300`). 7 contracts (2 RED); mutation 6/8, the two containment checks equivalent (no
page or exercise moves without them) and kept; suite 3253 + 2.

### `numeric` of a call works on the written body (stacked on the equation branch)

Branch `fix/numeric-of-a-call-keeps-the-name`: `numeric(M(L/2))` under `M(x) = R_A*x -
q*x^2/2` (kept `R_A`) opened with `q L x/2 - q x^2/2`; the call now uses
`written_functions[M]` as `numeric(name)` uses the written form, and the kept name is put in
as its own number: `M(L/2) = R_A x - q x²/2 = (30.00 kN)(3.00 m) - (10.00 kN/m)(3.00 m)²/2 =
45.00 kN·m`. 3 contracts (2 RED); mutation: the written body removed is caught; a
restriction to non-matrix bodies was unreachable (no matrix body is ever written) and was
removed; suite 3258; no page or exercise moves against the equation branch.

Left as it is, a convention: the call's first row is the law in `x` (`M(L/2) = R_A x - ...`)
and the substitution puts `x = 3.00 m` - the same on every sheet, with or without `keep`;
writing `R_A (L/2) - q (L/2)²/2` instead would move rows, so it is his call.

Found, not fixed: a kept name inside a function whose value is a matrix is expanded in
its own row - `k = E*A/L` (kept), `K(x) = [k*x, 0; 0, k]` reads `[E A x/L, 0; 0, E A/L]`
(`written_functions` never holds a matrix).

#361 merged as `151e841`, #362 as `3f48329`, each on green CI (#362 at `8cdf539`).

**0.42.2 before its merge**, on the release tree (rebased onto `3f48329`, its tree identical
to the one tested): version assertions RED (7) then GREEN; source suite 3258 twice (SymPy
1.14); wheel from `git archive`, 33 files identical to `src`; a clean Colab-like venv gains
only Pint and the four small deps; smoke 37/37 (one check added: a kept name in an
equation and a call, `R_A - q x = 0`, `(30.00 kN)`); the suite against the wheel on SymPy
1.13.3: 3256 + the by-path surface test on the wheel's `magic.py` + one timing test
(`test_the_portal_frame_solves_in_numbers_and_quickly`, `< 20 s`) that failed only while
the second source run shared the machine and passed alone twice (6.8 s, 6.5 s); the 24
pages identical from the wheel and from the tree.

**0.42.2 is closed** (#363, `0134b9e`, its tree identical to the release tree). After its
merge: CI (six jobs), Quality Gate Deep (push) and Deep in qualification mode by dispatch
green on `0134b9e`; his Colab path, `git+https` with `--upgrade`, in the venv that held
0.42.1 changed only `engcalc-colab` (`59cc98c` -> `0134b9e`), 33 files identical to `src`,
smoke 37/37. **In his Colab** ("Untitled9", 2026-09-27, 14:10): the runtime still held
0.42.1 in memory (`already loaded`), so the session was restarted from the menu; his cell
0, then my cell 3 printed `engcalc 0.42.2`, `R_t - q_t x = 0`, `x_t = L_t/2`, `M_t(L_t/2)
= R_t x - q_t x²/2 = (30.00 kN)(3.00 m) - (10.00 kN/m)(3.00 m)²/2 = 45.00 kN·m`.

Found after it, both older than this release:
- a matrix-valued function reads its kept names expanded (above) - being fixed on
  `fix/a-kept-name-in-a-matrix-function`;
- a regression of 0.42.1 (#359): on a line that reaches a kept name, a derivative inside
  a product is walked by the written reader and its number is not multiplied in -
  `Z = 2*diff(R_A*x^2, x)` reads `= 2 · 2 R_A x` (0.42.0: `2 q L x`, the kept name
  expanded but folded). #359's own note said this was avoided; it was, only on lines with
  no kept name. To fix next.

#364 (this closure) merged as `bbedc1d`.

### A kept name reaches a function whose value is a matrix

Branch `fix/a-kept-name-in-a-matrix-function`: a function keeps its written body only
when the line reaches a kept name (`_reaches_a_kept_name`), and a matrix written on the
line reaches the evaluator as one placeholder, so the names in its cells were never
looked at. `_a_line_reaches_a_kept_name(statement)` walks the cells too, at the one place
a function decides. Over `k = E*A/L` (kept by rule 2): `K(x) = [k x, 0; 0, k]` (it read
`[E A x/L, 0; 0, E A/L]`); `numeric(K(2))` opens with it and puts in `(66666.67 kN/m)`;
`D = K(2)` reads `[2 k, 0; 0, k]`; the numbers are the same. 4 contracts (3 RED);
mutation 4/4 (the check reverted, the cells never looked at, only the cells: caught by
the focused tests; every function given a written body: caught by the suite, 3 failures);
suite 3262; of the 24 pages and 18 exercises none moves.

### After the `=`, a derivative is worked out with what it is combined with

Branch `fix/a-derivative-in-a-product-is-its-value`, stacked on the matrix-function
branch. A regression of 0.42.1 (#359): on a line that reaches a kept name the written
reader works out `diff` and `integrate`, and `_combine` set the typed factor beside the
result unevaluated. `_WrittenFormEvaluator.visit_BinOp` now combines by evaluation any
operation with a worked call in an operand (`_holds_a_worked_call`), except when
`showing`, where the calls stand and the typed formula keeps its numbers.

| line (kept `R_A`) | 0.42.2 | this branch |
|---|---|---|
| `2*diff(R_A*x^2, x)` | `2 · 2 R_A x` | `4 R_A x` |
| `diff(R_A*x^2, x)/2` | `2 R_A x/2` | `R_A x` |
| `0.85*diff(...)` | `0.85 · 2 R_A x` | `1.7 R_A x` |
| `3*x*diff(...)` | `2 · 3 R_A x x` | `6 R_A x²` |
| `diff(...)^2` | `(2 R_A x)²` | `4 R_A² x²` |
| `diff(...) + R_A*x` | `2 R_A x + R_A x` | `3 R_A x` |
| `2*integrate(V(x), x, 0, x)` | `2 (R_A x - q x²/2)` | `2 R_A x - q x²` |
| `[2*diff(...), 0]` | `[2 · 2 R_A x, 0]` | `[4 R_A x, 0]` |

13 contracts (12 RED); mutation 11/11 (one survivor, nesting only through products, was
given `2*(diff(...) + R_A*x) = 6 R_A x`); suite 3275; of the 24 pages and 18 exercises
none moves (none multiplies a worked call on a kept line).

#365 merged as `708b3ce` on green CI at `8abbf34`; #366 rebased onto it, its tree identical
to the one tested, merged as `496eb54` on green CI at `2e6b519`.

**0.42.3 before its merge**, on the release tree (stacked on #366, its tree identical
after each rebase): version assertions RED (7) then GREEN; source suite 3275 twice (SymPy
1.14); wheel from `git archive`, 33 files identical to `src`; a clean Colab-like venv
gains only Pint and the four small deps; smoke 38/38 (one check added: `K(x) = [k x, 0; 0,
k]` and `Z = 2 ∂/∂x R_A x² = 4 R_A x` - its first draft looked for the matrix without the
`\displaystyle` each cell carries, and failed on a correct page); the suite against the
wheel on SymPy 1.13.3: 3274 + the by-path surface test on the wheel's `magic.py` (the venv
needs PyYAML for the two workflow tests); the 24 pages identical from the wheel and from
the tree.

**0.42.3 is closed** (#367, `7377aa0`, its tree identical to the release tree). After its
merge: CI (six jobs), Quality Gate Deep (push) and Deep in qualification mode by dispatch
green on `7377aa0`; his Colab path, `git+https` with `--upgrade`, in the venv that held
0.42.2 changed only `engcalc-colab` (`0134b9e` -> `7377aa0`), 33 files identical to `src`,
smoke 38/38. **In his Colab** ("Untitled9"): NOT YET - his screen was locked when the release closed (Chrome frozen, the renderer did not answer). My cell 3 holds the 0.42.3 check, ready: restart the session from the menu, run cell 0, then cell 3; it should print `engcalc 0.42.3`, `K_t(x) = [k_t x, 0; 0, k_t]`, `Z_t = ... = 4 R_t x`, `W_t = ... = R_t x`.

Open, his decisions (rows shown to him):
- `numeric` of a call opens with the law in `x`: `M(L/2) = R_A x - q x²/2`, then `x = 3.00
  m`; the alternative writes the argument in: `M(L/2) = R_A (L/2) - q (L/2)²/2`. Moves
  every `numeric(f(a))` row.
- A value written out with `=` folds into a formula that also reads a name standing:
  `L = 3*m; M = q*L^2/2` (no value for `q`) reads `9 m² q/2`; `L := 3[m]; q_1 = 10*kN/m;
  M_1 = q_1*L^2/2` reads `5 kN L²/m`. The alternative keeps the names (`q L²/2`,
  `q_1 L²/2`); a line whose every name folds still ends on its number (`45 kN·m`).
Cosmetic, found: a function's written body called inside an indefinite integral on a
plain line reads `x R_A` where its own row reads `R_A x` (`Z = integrate(M(x), x)`).

His answer (2026-09-27): *"Procede según tus recomendaciones"* - both alternatives, and he
asked that the Colab checks be mine, with screenshots sent to him. 0.42.3 was checked in
his Colab that way (Untitled9 cell 3; screenshots via a localhost receiver page that
the extension's `upload_image` fills, `scratchpad/shot_receiver.py`).

### `numeric` of a call writes its argument (his decision, 2026-09-27)

Branch `feat/numeric-call-writes-its-argument`. The evaluator records the arguments of the
parameters bound to a value (`written_arguments` on the four numeric result types); the
renderer prints the first row with the substitution printer, each parameter standing as
`renderer._WrittenArgument`: `M(L/2) = R_A (L/2) - q (L/2)²/2`, then the substitution and
the answer as before. A name or a plain non-negative number goes in bare (`f(2) = 2 q L`,
`K(2) = [k · 2, 0; 0, k]`); otherwise brackets unless nothing binds tighter: alone or as a
term of a sum only when negative (the additive rows print terms alone - `L + - a` in the
first prototype), none in a comparison (`q_v(9 m)`: `9 m < a_q`), inside a function
(`e^{1/2}`, `sin(...)`), under a radical or in an exponent; brackets as a factor or a
power's base. A lone numerator/denominator keeps them (`q/(L/2)`), like the substitution
row. Found by prototyping first (a workflow explorer, `scratchpad/explore-arg`): the
spacing metadata counts rows a second time, and without the argument a wrapped first row
raised "spacing metadata does not match". Moves: the three `formas` pages, one row each
(`q_v(9 m)`'s conditions); no exercise. 19 contracts (the first 7 RED); 5 older contracts
rewritten (2 snapshots, 3 assertions, each with a note); mutation 25 mutants: 24 killed,
the survivor (a call at its own variable writing `x` for `x`) measured equivalent on the
whole suite, pages and exercises, and its condition removed; an unreachable default
branch left as it was. Suite 3294 on SymPy 1.14 and on 1.13.3.

An independent audit (four workflow auditors, two per change, on a frozen copy) found in
this change three defects, fixed with a contract each: `L - x` at `L - a` read `L - L -
a` (SymPy prints the term `-x` as ` - ` then `x`, parent the sum), a wrapped product ended
`c q a + b` (factors printed alone), and a partial call with a unit argument raised
"spacing metadata does not match" (the partial count lacked `unit_literals`; 56 of 120
generated sheets). A term of a sum or anything printed alone now brackets an argument
that is a sum or negative. A second audit (two agents; both stopped at the session limit,
their measurements recovered from their transcripts) left an oracle,
`scratchpad/latex_oracle.py`, that reads a first row back with ordinary precedence, and a
sweep, `scratchpad/lens_sweep.py` (bodies x arguments, variants plain / `long` / `long
pa`): 14 false rows of 5372, a number argument after a numeric coefficient in a wrapped
product - KaTeX draws `2 2.5` as `22.5` (spaces do not count in math). The wrapped join
now sets a factor that begins with a digit apart with `\cdot`, as the unwrapped printer
does (#356): 5372/5372 in every variant, on SymPy 1.14 and 1.13.3, and no existing row
moves. 23 contracts; mutation 25/25 plus the join; suite 3298 on both SymPy.
Found, pre-existing, not fixed: a free argument named like another parameter is
captured (`F(x, y) = x + 2*y`, `numeric(F(3, x))` answers 9.00 on main too); a kept name
passed as an argument is expanded in the call's head (`M(d)` reads `M(L - a)` on main).
Left as house style: a lone fraction numerator/denominator or matrix entry keeps its
brackets (`q/(L/2)`), as the substitution row writes values.

### The value-of-`=` fold: held after its audit (2026-09-27)

Branch `feat/a-value-written-out-stands-beside-a-name` (`6e0d0f0`, not a PR): a name an
`=` line gave a number stands beside a name that stands (`q L²/2`, `q_1 L²/2`), on the
kept-name machinery, with rule 2 counting it. Its own contracts, mutation and the pages
were clean; the audit showed it reaches far past the two rows he approved: a zero written
with `=` (`e = 0*m`) crashes every numeric row reading it (the SymPy 0 lost its metre); a
mixed `:=`/`=` sheet now gets rule-2 kept names, so a later `q = 20*kN/m` leaves `y = 2 M`
on the stale 45 kN·m while `M` reads 90 (the stale-kept-number gap of an all-`:=` sheet);
once anything is kept, every later line of values stops ending on its number (`A = 30 ·
60 cm · cm`), the kept-sheet mode; `n = 2` as an exponent stays a symbol inside integrals
and derivatives (the general-n case, `numeric` of it raises); rows of one block mix `L`
and `6 m` (piecewise, `solve`, `% if` fold as before); an `=` value is substituted in the
palette's unit (`86675.88 kgf` under `P_u = 850 kN`). Not shipped: told him, with options.

He reviewed the screenshots (Untitled9 cell 4, before/after) and wrote *"fusiona #369 y
publica la 0.43.0. Para el =, haz el aviso que sugiere :=, y corrige el error del argumento
que se llama como otro parámetro"*. #369 merged as `abca016` on green CI at `dc3e20d`.

**0.43.0 before its merge**, on the release tree: version assertions RED (7) then GREEN;
source suite 3298 twice (SymPy 1.14); wheel from `git archive`, 33 files identical to
`src`; a clean Colab-like venv gains only Pint and the four small deps (`platformdirs`
now 4.12.1); smoke 39/39 (one check added: `numeric(M(L/2))` writes `R_A (L/2)`,
`M_D(L - a)` writes `L - (L - a)`); the suite against the wheel on SymPy 1.13.3: 3297 +
the by-path surface test on the wheel's `magic.py`; the 24 pages identical from the wheel
and from the tree.

**0.43.0 is closed** (#370, `81bacef`, its tree identical to the release tree): CI, Quality
Gate Deep (push) and Deep in qualification mode by dispatch green on `81bacef`; `git+https`
with `--upgrade` changed only `engcalc-colab` (`7377aa0` -> `81bacef`), 33 files identical,
smoke 39/39; in his Colab (Untitled9 cell 3, runtime fresh), `engcalc 0.43.0`, `M_t(L_t/2) =
R_t (L_t/2) - q_t (L_t/2)²/2 = 45.00 kN·m`, `M_u(L_t - a_t) = q_t (L_t - a_t)(L_t - (L_t -
a_t))/2 = 40.00 kN·m`; screenshots sent to him.

### A free argument named like a parameter (#371) and the `:=` notice (#372)

#371 (`3bf56aa`): `numeric(F(3, x))` of `F(x, y) = x + 2*y` answered 9.00 (0.42.3 and
0.43.0 too): the free `x` put in for `y` took the value given to the parameter `x`. A
valued parameter a free argument names now stands apart (`x__argument`) before the
arguments go in, as a call on a `=` line puts them in at once. Its audit found the
internal name reaching a later row through `w = numeric(...)`, and under it an older
defect: a named `numeric` of a call stored the function's body (`w = numeric(F(3, 4))`
gave `u = 2*w = 2 x + 4 y`; `w = numeric(M(L/2))` gave `u = q x (L - x)`). The value
stored is now the body with the arguments put in (`22`, `q L²/4`). 8 contracts;
mutation 4/5 plus the storage (the survivor, the name's `real=True`, removed).

#372 (`9c8dee9`): the notice his decision chose over changing `=`: once per name, when a
formula writes a value of `=` in beside a name that stays a name, `'L' was defined with
'=', ... define it with ':=' (L := 3*m) to keep it a name here`. Its audit found it lost in
a `% while` (said on a dropped turn, counted as said), suggesting `x1 := solve(...)` (which
`:=` refuses), and firing on a matrix index or a derivative's order; fixed - told again
only by the line that told it, the number suggested where `:=` would refuse the line
(`x1 := 3[m]`), indices and orders not counted. 15 contracts; mutation 17/17. No reference
sheet or exercise prints it.

Found by the audits, not fixed: unknown units (`km`, `lbf`, `percent`) are free letters,
so a line of values in them draws the notice about a correct value (the unknown unit is
the older problem); a `% for` defining `=` values tells each iteration's name; `numeric`
inside a product drops the rest of the formula (`M = q*numeric(L^2)/2` stores `9 m²`,
on 0.43.0 too - a wrong number, to fix next); a partial call past a derivative breakpoint
gives the older piecewise-condition message.

**0.43.1 before its merge**, on the release tree: version assertions RED (7) then GREEN;
source suite 3321 twice (SymPy 1.14); wheel from `git archive`, 33 files identical to
`src`; a clean Colab-like venv gains only Pint and the four small deps; smoke 40/40 (one
check added: `F(3, x)` reads `2 x + 3`, `u = 2*w` reads `22`, the notice suggests `L :=
3*m`); the suite against the wheel on SymPy 1.13.3: 3320 + the by-path surface test on the
wheel's `magic.py`; the 24 pages identical from the wheel and from the tree, and none
moves from 0.43.0.

**0.43.1 is closed** (#373, `739e81a`, its tree identical to the release tree): CI, Quality
Gate Deep (push) and Deep in qualification mode by dispatch green on `739e81a`; `git+https`
with `--upgrade` changed only `engcalc-colab` (`81bacef` -> `739e81a`), 33 files identical,
smoke 40/40. In his Colab (Untitled9 cell 3; a Reconectar reattached the 0.43.0 session,
"already loaded", so the session was restarted from the menu): `engcalc 0.43.1`, `F_t(3,
x) = 2x + 3 = ... = 3.00 + 2.00 x`, `F_t(3, 4) = 11.00`, `u_t = 22`, the notice on line 6
for `L_b`, `M_b = 9 m² q_b/2` unchanged; a screenshot sent to him.

### `numeric` is a line of its own (0.43.2, his "corrige numeric dentro de un producto")

Branch `fix/numeric-is-a-line-of-its-own`. `numeric(...)` written inside a formula took the
line over: `M = q*numeric(L^2)/2` defined `M` as `9 m²`, `y = sqrt(numeric(L_2^2))` showed
`9.00 m²`, a matrix cell showed the cell, a `:=` line stopped at `unsupported numeric
function`. The approved 0.9.0 design (`numeric(A) * numeric(B)` "is not part of the public
contract") decided it: the line stops and is written back without it (`engine.
_refuse_numeric_inside_a_formula`): `Write M = q*L^2/2, then numeric(M).`; on `:=`, that
`:=` works out a number already. `result` and `report` are told by their own names.

Three independent audits (a subagent; a workflow of three lenses with a skeptic per
finding, 17 confirmed; a subagent on the delta, 5 confirmed), all fixed with contracts:
- a `% if`/`% while` condition evaluates each side as `numeric(<side>)`, so a `numeric`
  there was refused: a whole side is worked out as on main (unit checked and written -
  `numeric(d, mm)` in mm; `numeric(M(L_2))` as the call worked out); one inside a side
  reads as its value, its unit checked; `report` in a condition refused; "line 1" gone;
- the written-back line runs: `then numeric(y)` only where every name has a value
  (`_reads_only_values`, recursive through `=` formulas; `solve`/`subs` unknowns and
  definite `integrate`/`sum` variables bound), brackets before a power or an index,
  report advice (`report(M_2)`; "write 2*M_2 under a name"), the kept call checked
  first, a `% for` line written as the template (`ParsedStatement.written_as`, set by
  `control._parse_stretch`, whole name `M_{i+1}`), comments and strings respected;
- older, found on the way: `case D = numeric(M(L/2))` defined `D(x) = M(x)`; `K[1, 1] =
  numeric(M(L_2))` stored `M` at the sheet's `x` (both refused now); `keep w = result(...)`
  showed the substitution; `v := 2` then `v = v*2` hung the kernel (since 0.41.2 at
  least) - `_resolve_symbolic_names` stops after `len(namespace)+1` passes: `v is defined
  from itself`.
Seen, differs from main, his call: a whole side `numeric(M, tonf*m)` in a condition is now
written in the unit asked (main wrote the default unit, inconsistently). Lines that gave a
right number on main by accident and now stop: `roots(numeric(M(x)), ...)`,
`numeric(numeric(M_2))`, `numeric([numeric(a), 0; 0, b])`, `K[1,1] = 2*numeric(a)`.
Not fixed: a bare `numeric(M(x))` over a function with a free `x` crashes in the renderer
(`semantic spacing metadata does not match rendered row count`, on main too); `case D =
M(L/2)` advice fails when pasted (a case needs a variable); a two-name cycle names one.

Contracts: `test_numeric_is_a_line_of_its_own` (57), `test_numeric_advice_runs` (35),
`test_a_name_defined_from_itself` (4); mutation 52/52.

**0.43.2 before its merge**, on the release tree (`295e7a4`): version assertions RED (7)
then GREEN; source suite 3417 twice (SymPy 1.14) and once on 1.13.3; wheel from `git
archive`, 33 files identical to `src`; a clean Colab-like venv gains only Pint and the four
small deps; smoke 43/43 from `C:\`; the suite against the wheel: 3416 + the by-path surface
test on the wheel's `magic.py`; the 24 pages identical from the wheel and from the tree,
and identical to 0.43.1's; the 18 exercises identical.

**0.43.2 is closed** (#375, `3a1c492`, its tree identical to the release tree `013e6b7`):
CI, Quality Gate Deep (push) and Deep in qualification mode by dispatch green on
`3a1c492`; `git+https` with `--upgrade` changed only `engcalc-colab` (`739e81a` ->
`3a1c492`), 33 files identical, smoke 43/43. In his Colab (Untitled9 cell 3, reconnected
to a fresh runtime, his cell 0 run first): `engcalc 0.43.2`, `M_d = 45.00 kN·m`, the
refusal on line 5, `Como q_d L_d²/2 = 45.00 kN·m > 40.00 kN·m`, the `:=` message on line 4,
`v_t is defined from itself` with no hang; two screenshots sent to him.

### His book, chapter 2 (*Matrix Structural Analysis*, McGuire, Gallagher, Ziemian)

He asked (2026-09-28) to test EngCalc on every exercise of the book, chapter by chapter.
The sheets live outside the repo (copyright): scratchpad `book/ch02/solver-{A,B,C}`.
Three solvers, each with an independent Python oracle: 2.1 (a-f), 2.2-2.8, 2.12-2.15 all
give the oracle's numbers; 2.9-2.11 are conceptual. Findings, deduplicated:
- **Wrong on the page:** a computed coefficient 0.007 printed `0.01` (2.3's `R_d = -0.01
  EA`; 0.447 as 0.45); with `keep k`, `u = P/(5*k/4)` reads `P/(5 ¼ k)` - a mixed number.
- **Bugs:** a bare `solve(eq(...), x)` shows `x = ...` but does not define `x` (README says
  it does); `x := solve(eq(...), x)` stops at `unsupported numeric function`; a
  matrix-valued function call is refused on a `:=` line ("needs a single numeric value").
- **Missing:** temperature units (`degC`, `K`, `delta_degC`); `numeric` of a formula still
  in a free symbol (a function call of it works), and a target unit on a partial result;
  rationalising a radical denominator.
- **Presentation:** kept names lost in `K[...] = K[...] + k*[...]` and `zeros(n,n) + M`;
  `solve` answers expand kept names (0.42.2's choice, it hurts here: `dP_b = A_b T/(A_b +
  A_c)`, not `k_b T/(k_b + k_c)`); a kept flexibility substituted as `7.50e-9 m/(mm²·MPa)`;
  substitution rows that fold or reorder the formula row; a wrapped formula printed twice
  before `numeric`; `(−1) f R`; `((8000 mm²))²`; `−0.00 EA`; a parameter `s` read as
  seconds; `cos(60 deg)` on a `=` line; a bare solve of a named equation with nothing on
  the left; piecewise "for ... otherwise" in English; plot legend `F_b(T)` raw, title
  `F(T)` for two series, the kink unlabelled.
- **Tooling:** `tools/render_memoria.py` typesets with MathJax, which does not know
  `\allowbreak` - every paragraph reads as red source there since 0.41.2 (KaTeX, Colab's,
  renders it); the harness no longer measures Colab for text.

### Chapter 2's four, fixed (0.43.3, his "corrige primero los dos números ... y los errores de solve")

Branch `fix/chapter-2-numbers-and-solve`: a computed coefficient keeps as many
significant figures as the page has decimals (`R_d = -0.007 E A`, was `-0.01`;
`renderer._print_Float`); a denominator holding a fraction is printed as one
(`renderer._print_Mul`: `P/((5 k)/4)`, was `P/(5 1/4 k)`, numbers as typed); `x :=
solve(...)` goes through `_assign_through_the_sheet` (several answers: "solve returned N
solutions"). **Differs from what he approved:** a bare `solve(eq(...), T)` was made to
define `T`; its audit found that `solve(eq(V(x), 0), x)` then pins `x` and `M(x)` becomes
a constant (plot flat at 45 kN·m, `M(L/4)` 11.25 for 33.75, later solves broken), so it
was reverted: the bare form defines nothing, the README (which said otherwise) is
corrected, and a later line of the same cell asking for `T` - `:=` lines too - is told
`T on line 3 was solved on a line of its own ... write T = solve(...) to use it`
(`engine._told_where_it_was_solved`, cleared per cell by `begin_cell`). Contracts
`test_chapter_2_numbers_and_solve` (16); audit twice (subagent), every finding fixed.

**0.43.3 is closed** (#377, `e8f05d3`, its tree identical to the release tree `a42f569`):
CI, Quality Gate Deep (push) and Deep qualification green on `e8f05d3`; `git+https` changed
only `engcalc-colab`, 33 files identical, smoke 45/45. In his Colab (Untitled9 cell 3, a
fresh runtime, his cell 0 first): `engcalc 0.43.3`, `R_d = -0.007 E A`, `u = P/((5k)/4)`,
`x_2 = 1.00 m`, the bare-solve hint on `numeric(Z)`; two screenshots sent. Seen in Colab:
the fraction inside a denominator is set small by KaTeX and sits close to the next row -
readable; `\frac{P}{5 k/4}` with a slash is the alternative, his call.

### His book, chapter 3 (direct stiffness; solvers A 3.1, B 3.2-3.5, D 3.7-3.14; C 3.6, 3.15 running)

Every number agrees with a numpy oracle (and with Example 3.4's K for 3.9). The book gives
no answers. Findings, deduplicated (sheets and repros in scratchpad `book/ch03/solver-*`):
- **Hang:** `plot` works out a curve's extrema exactly with no guard - `plot` of
  `max(abs(...))` of a 2x2 solve took 19 s, the real 3.2 sheet was killed after 400 s.
- **Wrong or misleading on the page:** a `:=` matrix entry plus a value reads in SI base units
  (`F[1] + 1[kN]` = `301000.00 m·kg/s²`); `N := k*0.5[mm]` reads `2.00e7 MPa·mm³/m`; a small
  force switches to N among kN (`N_hb = -190.63 N`), a zero too; `plot` of a quantity in
  `m·kN/(mm²·MPa)` with end labels rounded to 0; `solve(K, -K*u)` printed `K^{-1} -K u`;
  the internal `__u_m` on the page (`numeric(S)` of a symbolic matrix); the 3.2 ratio's unit
  off by 1000 in `table`.
- **Refused though valid:** no numeric assembly (`K[[..],[..]] := ...`, a `:=` element
  matrix in an `=` part assignment); `det`/`rank` on `:=` lines (wrong hint); `:=` index
  lists only literal (`K[1:2, 1:2]`, a named list refused), `libres := [1, 3]` and an inline
  row literal on `:=` ("unsupported numeric syntax 'List'"); `^-1` on `:=` lines; a 1x1
  `k*transpose(g)*D` not addable to a scalar; `abs()` of an expression with bracket units
  ("bad operand type for abs(): 'Unit'"); `extrema` of `max(...)` (internal jargon);
  `table` with columns of different units; a `% for` over lists of DOF numbers.
- **Missing:** a symbolic answer with decimal coefficients (`0.4829 P m/(A E)`); a loop value
  in narrative (`{th}` printed literally); `$...$` in headings.
- **Presentation:** the symbolic K reprinted after every bar (3.5: 30 prints, 20x20, 41 300 px,
  3 of 20 columns fit) - the assembly section is unreadable and the assembly line itself is
  never shown; kept names lost in part assignment (`c² E A/L`, not `k c²`); a function body
  expands kept names inside `piecewise`; `solve` of a named equation inlines the answer;
  `numeric` of a piecewise substitutes every branch; table headers drop fixed arguments;
  the plot's extrema panel in English with the wrong variable name; mixed number formats in
  one matrix (`2.69 × 10^6` beside `-332106.78`; `10^3` factored in one, not the next);
  `\frac{1 kN}{1 m}` for a bracket unit in a matrix; a scalar `:=` line never shows its
  formula (`L = sqrt(Δx² + Δy²)`); a parameter `s` read as seconds.
- **Practicality:** loops with `{i}` made a 6-bar truss about 60 lines and correct; the page
  is what fails. Wanted: a numeric assembly statement, and a way to show only the final K.

Solver C (3.6, 3.15 a-e, the large trusses): 116 bar forces, 110 displacements, 22
reactions, 0 mismatches; 3.6's page is 54 377 px, 63% the assembly (33 reprints of a
36x36 K, 13 page widths), 2.5% the results. A `% while` over the bars shows the final K
once (21 628 px) - a hack. Wanted, by page saved: the assembly shown once (rule + final K
or a summary), a loop of `:=` scalars as one table, DOF bookkeeping (named lists, d back
into D, a node table), a truss figure.

### Chapter 3's plot hang and raw units, fixed (0.43.4, his "corrige el cuelgue de plot y las unidades crudas")

Branch `fix/chapter-3-plot-and-units`: a plot of more than 24 operations is marked from its
samples (`engine._marks_from_samples`; the reference plots have at most 14); a curve in a
unit the algebra invented is drawn in the page's unit, one unit per axis
(`renderer._plotted_in_units_a_page_writes`; `portico_matricial`'s figures move from
`m²·kg/s²` to kN·m); `unit_was_written` reads a bracket alias `__u_kN` as its unit
(`S := F[1] + 1[kN]` = 301.00 kN, was `301000.00 m·kg/s²`); no `__u_m` in matrix rows.
Seen, not changed (approved rule, his call): a lone zero reads in its family's first
member (`0.00 N` on a kN sheet, `test_a_zero_standing_alone_reads_in_its_family`); a small
force in N is the band rule. Contracts `test_chapter_3_plot_and_units` (10); audit
(subagent) found the per-curve unit and a matrix-call alias, both fixed.

**0.43.4 is closed** (#379, `382f339`): CI, Quality Gate Deep (push) and Deep
qualification green on `382f339`; a `git+https` install reports 0.43.4 and its 33 files are
identical to `382f339`'s `src`. In his Colab (Untitled9 cell 3, his cell 0 first, 2026-09-29):
`engcalc 0.43.4`, `F = k D` in kN, `S = F_1 + 1 kN = 301.00 kN`, `plot(v(P), P, -30[kN],
150[kN])` drawn at once with P in kN and v in mm; two screenshots sent.

**His decision on the assembly** (2026-09-29, "haz primero 1 + 3 con el resumen cuando la
matriz no quepa"): a `% for` that assembles shows it once (rule + final K, or a size summary
when K is wider than the page), and a loop of 2+ `:=` values is one table. Being built on
`feat/a-loop-shows-its-assembly-once`; its state is recorded there.

### The loop page (branch `feat/a-loop-shows-its-assembly-once`, 0.44.0 when released)

`abeb95c` was the first version; its audit (subagent) found 15 defects, fixed in `7c400e4`;
chapter 4's solvers found more, fixed in `c7a16f1`; three more audits of the same
auditor found 13, 5 and 3, fixed in `6623195`, `829b3f6`, `e0b7db1` (a line that reads its
own name or its earlier passes keeps its rows; a loop with its own headings, an assembly
under `% if` or inside a loop that does not gather streams as before; notes name only the
`%` names the rule stands on, in header order, helpers followed back, constants said once;
`{i-1}` glued to a name keeps its group). Left, low: the draw/summary edge (±3% of 900
px), page order when a line reads K mid-assembly, `str(...)` helpers in a con row, a rule
row is not wrapped, `- {-i}` loses its parentheses. What a `% for` that gathers (2+ `:=`
lines of its own, or a line anywhere inside adding into a part of a matrix) puts on the
page, after every pass is worked out in `control._gathered`:
1. the formulas of its tabled `:=` lines once ("En cada uno de los N pasos:"), then one
   table, a row per pass; a column holds one kind of quantity, a line written twice keeps
   its rows, notices reach the console once;
2. what the passes showed, in order - a `=` line of its own that every pass wrote with
   only its subscripts changed, whose value still has symbols, is said once as a rule
   (problem 3.6's g vectors; the developer's call, which he left to judgement);
3. per matrix, "Ensamble en N pasos, para (vars) = values, con (helpers):" with the rule on
   a row of its own (written by `_RuleLine`, the `:=` line printer), then K, or
   "K : r x c, simétrica, N términos no nulos" when K is wider than the page - measured by
   `renderer._katex_em`, fitted to KaTeX 0.16.28 widths (within 10%);
4. a failing pass leaves the rows before it on the page. A nested loop streams into the
   gathering one. An all-zero matrix larger than 4 is written `\mathbf{0}_{r \times c}`.
Problem 3.6's page: 54 377 px -> 10 936 px, 0 KaTeX errors; the book's 118 loop notes
measure at most 801 px in KaTeX. Contracts: `test_a_for_loop_shows_its_assembly_once` (7),
`test_a_loop_s_page_reads_what_it_ran` (47). Visible on a reference sheet: `portico_diseno`'s
`Z_6 = zeros(6, 1)` reads `Z_6 = 0_{6x1}` (the zeros rule, >4 in either dimension).

**0.44.0 release evidence (tree `e0b7db1`):** suite 3497 (SymPy 1.14) and 3496 + the
frozen-SymPy run (1.13.3, Colab's), twice; wheel 33 files identical to `src`; clean Python
3.12 venv with Colab's pins adds only Pint and its dependencies; smoke 47/47 outside the
repository; suite against the installed wheel 3496 + the surface test 5; the 24 reference
pages identical wheel vs tree, and vs main except `portico_diseno`.

### His book: worked examples, and where the notebooks are

He mistook Example 2.1 (section 2.6, u_a = 2.41 mm) for Problem 2.1 (section 2.7, the rigid
beam on links) - only the end-of-chapter problems had been solved. The notebooks now open
with the text's worked examples, then the problems. Examples 2.1-2.6 and 3.1-3.6 agree with
the book (to its 3-digit rounding). They live in his Google Drive, folder "EngCalc - Matrix
Structural Analysis", and in Documents (outside the repo). Examples' findings, not fixed:
a system `solve` defines its unknowns while a one-unknown one does not; `subs` of a name
with a `=` definition does nothing, silently; a one-row literal refused on `:=`; `inv` of a
stiffness matrix in `s²/kg`; the summary counts `s k` with `s := 0` as non-zero; `solve` of
a named equation drops the unknown's name; no temperature unit; `45 deg` in formulas;
kN/mm stiffnesses read in kN/m.

### His book, chapter 4 (solvers A 4.1-4.3, B 4.4-4.7, C 4.8-4.12; D 4.13-4.16 pending)

Every number agrees with a sympy/numpy oracle and with Example 4.14. Findings not yet fixed
(sheets and repros in scratchpad `book/ch04/solver-*`):
- **Refused though valid:** a matrix-function call on a `:=` line (`f := g(k)*u`, "symbolic
  type 'ImmutableDenseMatrix'"); `lambda` as a name (a Python keyword; no hint).
- **Presentation:** a `=` matrix line drops the formula typed (`inv(d)`, blocks, reorders,
  `simplify`); no "formula = 0" verification row; `diff` of a named quantity writes out the
  expression, `keep` or not; a factor in front of a matrix literal is pushed into every
  entry and not cancelled (`6EIL/L^3`), and a symbolic matrix cannot show a common factor
  outside (the book's `3EI/(a^3+b^3)[...]`); numeric `:=` matrices wider than the page are
  drawn in full (K_ff 13x13, 1889 px); `frame_plot`'s moment sign follows where the other
  members are (the same beam reads +20 or -20); a tiny length among mm reads
  `7.49 x 10^-7 m`; compound units in typed literals read `kN m`; the `% while` note
  without the counter's name; solved constants still shown in later formulas.

**0.44.0 is closed** (#381, `624eb87`): CI, Quality Gate Deep (push) and Deep qualification
green on `624eb87`; a `git+https` install changed only `engcalc-colab`, 33 files identical to
the release tree, smoke 47/47. In his Colab (Untitled9 cell 3, his cell 0 first, 2026-09-30):
`engcalc 0.44.0`, a 3-bar truss's formulas once, its table, `g_ij` as one rule, `K = 0_{6x6}`,
the assembly note (para / con / rule), `K : 6 x 6, simétrica, 36 términos no nulos`,
`Z = 0_{36x36}`, no KaTeX error; two screenshots sent. Seen there: the note's rule rows set
fractions in text style (small) - `\displaystyle` in each rule row is the fix, not done.

### His book, chapter 4 complete (solver D: 4.13-4.16 and Examples 4.5-4.15)

Every number agrees with the oracle and the book (4.12's table misprints .423 for .413).
The notebooks in his Drive now hold chapters 2-4 with their worked examples (6, 6, 11) and
problems (13, 24, 17). Solver D's findings, not fixed:
- **Wrong number:** `diff` treats a name set by a system `solve` as a constant
  (`t = subs(diff(y(x), x), x, 0)` then `diff(t, p)` gives 0 for -1); linked to the
  system-solve-defines-its-unknowns finding.
- **Presentation:** a sheet function's call inlines the `=` names of its argument; a
  kip/inch sheet's matrices read in SI; a loop's `:=` lines that read matrix entries
  (`N_{m} := f_{m}[1]`, shown as written) are never tabled; `frame_plot` draws no moment
  applied at a supported joint, and its value box covers a drawn one's label; trig of
  degree values never reduces symbolically; values between 0.1 and 1 get two decimals
  (0.24 in for 0.237); units chosen per entry in one displacement vector; a long literal
  index list runs off the page; `factor` of a matrix works per entry.
- **Missing:** `sinh`, `cosh`, `tanh`; a scalar minus a 1x1 matrix.

### 0.44.1: what the book's worked examples found (his "procede... delego las decisiones")

Branch `fix/loop-note-fractions-and-solve`. The first design - every name a function's body
holds read by its latest definition - was audited (subagent) and dropped: it broke `keep`,
captured arguments and moved pages that read a formula on purpose. What shipped, audited
three more times:
- `engine.with_solved`: what a solve of a SYSTEM fixed (`solved_values`, while the name
  still holds that answer; never kept names; never a variable of the sheet - a function's
  parameter, a diff/integrate variable of the solve) is read by its value in `resolve_name`
  and after a call binds its arguments. `eq(...)` values are left alone. A solve holds its
  own unknowns (`engine.held`) while it is worked out, so it can run again.
- `subs`: a variable with a definition is replaced where its definition stands (as in
  0.44.0) and as the bare name; a name a system solve answered is taken as its symbol with
  the expression read with it held, and its value replaced when the expression no longer
  holds the name.
- A `=` line of a loop is said as one rule only if its right side reads a `{...}` value
  and calls no subs/diff/integrate/solve/numeric/simplify/expand/factor/limit.
- A loop note's rule rows in `\displaystyle`.
Contracts `test_what_the_book_s_examples_found` (16). Known, not changed: re-running a
whole problem cell without `%eng_reset` after its solve fails as in 0.44.0 (p4_2 twice);
`subs(g(x), C_2, 5)` of a function defined after the solve stays wrong as in 0.44.0.

**0.44.1 release evidence (tree `8585c17` + README):** suite 3513 (SymPy 1.14) and 3513
(SymPy 1.13.3); wheel 33 files identical; clean Python 3.12 venv with Colab's pins adds only
Pint; smoke 48/48 outside the repository; suite against the installed wheel 3512 + surface
5; the 24 reference pages identical to 0.44.0 and wheel = tree; the 193 book and audit
sheets differ from 0.44.0 only where a solve fixed constants (p4_2, r_diff2, r_diffsolved)
or in the audits' own cases, consoles identical.

**0.44.1 is closed** (#383, `4d16a38`): CI, Quality Gate Deep (push) and Deep qualification
green on `4d16a38`; a `git+https` install changed only `engcalc-colab`, 33 files identical,
smoke 48/48. In his Colab (Untitled9: session restarted from the menu, his cell 0, then
cell 3, 2026-09-30): `engcalc 0.44.1`, after the solve `t = -p` and `g = diff(t, p) = -1`,
`G = subs(F, u, 0) = -k x`, the loop note's `c_i = 2 m / L_i` at the page's size; two
screenshots sent.

### 0.45.0: a temperature, sinh/cosh/tanh, a row on a `:=` line (his pick, 2026-09-30)

Branch `feat/temperature-hyperbolic-row-literal`:
- `[degC]`, `[degF]` are Pint's `delta_degC`/`delta_degF` - a temperature on a structural
  sheet is a change (alpha*dT a strain); written `°C`/`°F` in text (`unit_text`) and LaTeX
  (`renderer._temperature_latex`, `_DEGREE_LATEX` for bracket names in formulas); `[K]` the
  kelvin in brackets only (`__u_K`; a bare `K` stays the stiffness matrix); a temperature
  in kelvin from base-unit numbers (matrices) reads in °C. A conversion between scales is
  refused (`numeric._refuse_another_temperature_scale`): `20 °C` as `36 °F` read as a false
  thermometer equality (audit).
- `sinh`, `cosh`, `tanh` in every function table (engine, numeric, parser, reference).
- `_MatrixNumbers._writes_a_row`: a list that is not a part's index nor a non-matrix call's
  argument (interp tables) is a row on a `:=` line.
Example 2.4 is now written with `[1/degC]` and `[degC]`. Audit (subagent) found the scale
conversion, kelvin matrices and `\mathrm{degC}` in formulas - fixed. Left: bare `degC` is a
unit like `kN`; `cosh(30[deg])` refused; a mixed-unit row accepted; `libres := [1, 3]` then
`K[libres, libres]` on `:=` says index lists must be literal.
Contracts `test_temperature_hyperbolic_and_a_row` (11).

**0.45.0 release evidence (tree `d7acbdd` + docs):** suite 3530 (SymPy 1.14 and 1.13.3);
wheel 33 files identical; clean Python 3.12 venv with Colab's pins adds only Pint; smoke
49/49; suite against the installed wheel 3529 + surface 5; 24 reference pages identical to
0.44.1 and wheel = tree; the book corpus differs from 0.44.1 only in Example 2.4 (now with
units) and a chapter 5 sheet that uses them.

**0.45.0 is closed** (#385, `0a7ddab`): PR CI green; Quality Gate Deep (push) and Deep
qualification green on `0a7ddab`; a `git+https` install changed only `engcalc-colab`, 33
files identical, smoke 49/49. In his Colab (Untitled9, fresh runtime, his cell 0, cell 3,
2026-09-30): `engcalc 0.45.0`, `alpha = 1.17e-5 1/°C`, `dT = 40.00 °C`, `u = 1.40 mm`,
`sinh + cosh = 1.65`, `F = k [c s] d = 5.20 kN`, `numeric(dT, degF)` refused with its reason;
two screenshots sent.

### His book, chapter 5 complete (problems 5.1-5.17, worked examples 5.1-5.13)

Every number agrees with an oracle, and the examples with the book (to its rounding; 5.7
prints u_b = 0.09982 for 0.9982 mm). The thermal problems (5.11-5.13, 5.16) and examples
(5.12, 5.13) used `[degC]`/`[1/degC]` without trouble. The notebook `Capitulo_05.ipynb` is
in his Drive. Findings, not fixed:
- **Silent stop:** `numeric` of a matrix whose `E*I` cancels prints the substitution row and
  no value (`simplify` works around); the scalar form says "requires values for: E, I".
- **Presentation:** a function parameter named `s` read as the second (every `(c, s)`
  rotation matrix); `EI_theta_b` not Greek; a 4x1 substitution row wider than the page.
- **Missing:** `:` in an index on a `:=` line; `member()` with a load over part of a span
  (5.8c's diagram wrong, numbers right); a 6x6 `[gamma, zeros(3,3); ...]` on `:=`; a part
  assigned on a `:=` line (`K[[1,2],[1,2]] := ...`, refused naming `K[1, 1]`).
- **Wrong page (Colab red):** a 12x12 matrix with typed units fails KaTeX with "Too many
  expansions" (5.10d).
- **Refused or silent:** a system `solve` on a `:=` line ("'NoneType' object has no
  attribute 'free_symbols'"); a loop line whose target starts with a placeholder
  (`{r}_a = ...` -> "invalid assignment target '1_a'"); an undefined `psi` read as the unit
  psi silently (no warning, as `m` and `s` get); `[in]` in brackets refused without the
  "use inch" hint.
- **Presentation:** the loop rule writes `{A}e3[mm^2]` as `(Ae_3)_{mm^2}` and `{phi}*deg`
  with an italic deg; one loop assembling K and P_F says its "para" list twice; stacked
  fractions of loop rules touch; the summary counts `lambda*mu` with lambda := 0 as non-zero
  (117 for 93); symbolic `=` matrices wider than the page cut off; `alpha` 1.2e-5 as
  0.000012; numbers typed into function arguments folded and rounded (0.86 inch^2 E/ft);
  the fixed-end vector assembled by parts never shown in numbers.

### 0.45.1: what chapter 5 found refused, silent or wrong (his pick, 2026-09-30)

Branch `fix/chapter-5-refusals`: unknowns that cancel are cancelled (`numeric.evaluate_matrix`
and `evaluate_symbolic`, only when every missing name goes); a system `solve` on a `:=` line
gets the standalone-statement message; the structure probe stands `n1` for a `{...}` glued to
a name (`{r}_a`); `psi` read as a unit is said (`_UNITS_SPELLED_LIKE_GREEK`); `[in]` is the
inch in brackets, `[inch]` in a formula reads `in`; function parameters are never units; a
block with more than 200 `\,` writes `\mkern3mu` (KaTeX's 1000 expansions). Audit (subagent):
no new defect, 26 of 540 sheets differ from 0.45.0 and all as intended. Left, low: a matrix
where only some entries cancel still stops silently; the psi notice also fires for US sheets
that mean the unit unbracketed. Contracts `test_what_chapter_5_found` (8).

**0.45.1 release evidence (tree `01ae474` + docs):** suite 3538 (SymPy 1.14 and 1.13.3);
wheel 33 files identical; clean Python 3.12 venv with Colab's pins adds only Pint; smoke
50/50; suite against the installed wheel 3537 + surface 5; 24 reference pages identical to
0.45.0 and wheel = tree.

**0.45.1 is closed** (#388, `ea59ea1`): CI, Quality Gate Deep (push) and Deep qualification
green on `ea59ea1`; a `git+https` install changed only `engcalc-colab`, 33 files identical,
smoke 50/50. In his Colab (Untitled9: session restarted from the menu, his cell 0, cell 3,
2026-10-01): `engcalc 0.45.1`, `numeric(R)` with E·I cancelling = [12.50; 2.50] kN,
`A = 10.60 in²`, `f(c, s) = c + 2s` italic, `{r}_a` in a loop gives `x_a`; screenshots sent.

### His book, chapter 6 complete (virtual work; problems 6.1-6.18, examples 6.1-6.8)

Every number agrees with an oracle, and the examples with the book. `Capitulo_06.ipynb` is
in his Drive. Fixed in 0.45.2 (his pick, 2026-10-01): the integral crash, the `__u_kN` equation
row, the nested piecewise, `q = solve(..., q)`. Findings still open: `for`/`otherwise` in English;
- **Missing:** a virtual increment δθ, δv_A as a name (`dtheta` is an italic word,
  `delta_theta` subscripts θ).
- **Presentation:** a solve's equation row repeats the whole expression; a sum expanded
  into 12 fractions in 6.3; ∂²/∂x² left unevaluated inside an integrand; d/dx and ∂/∂x mixed;
  ratios 0.597/0.605 both shown 0.60; the integral of a piecewise with a symbolic limit opens
  a "for L < 0" case without `assume(L > 0)`, and a product of piecewise functions lists
  impossible branches; `log(-2L) - log(-L)` not simplified to `ln 2`; radicals not
  rationalized (25-digit integers, 6.8's page 8195 px); a substitution row leaving a `:=`
  name as a letter; a bracket literal folded into a rounded float coefficient (`0.032 P/(mm
  k)`); `K = K + ...` in a loop prints every pass (only part assignments are summarised);
  `numeric(name)` repeats a long result; a system with `:=` coefficients shown as huge
  fractions; a sum of integrals reordered.
- **Missing:** a symbolic result with decimal coefficients (`0.0116 P_2 + 0.0134 P_3`);
  `heaviside`.

### 0.45.2: what chapter 6 found breaking the page (his pick, 2026-10-01)

Branch `fix/chapter-6-page-breakers`: `_value_row_spacings` measures an evaluation's input with
its units (the integral of 6.15 counted two rows for one and the cell stopped); the equation row
of a `:=` solve passes the bracket units of its equation; `_flattened_piecewise` merges a
piecewise standing as a branch value into its parent (`And` of the conditions); engine
`_fixed_by_its_own_solve`: `q = solve(eq(...), q)` records `q` in `solved_values`/`solve_answers`
(not a bare solve, not `k = solve(..., q)`, not a variable of the sheet). Audit (subagent): no
defect; 15 of 605 sheets differ from 0.45.1, all chapter 6 and all as intended (three crashes
gone, KaTeX errors gone, `M_4 = subs(M_x, x, L/4)` after `x = solve(...)` now right). Left, low:
an impossible combined condition (`x > 2 ∧ x < 1`) is printed; `g(2[m])` with `q = P/2` shows
`m P`. Contracts `test_what_chapter_6_found` (9).

**0.45.2 release evidence (tree `f17948b`):** suite 3547 (SymPy 1.14 and 1.13.3); wheel 33 files
identical; clean Python 3.12 venv with Colab's pins adds only Pint and its dependencies; smoke
51/51; suite against the installed wheel 3546 + surface 5; 24 reference pages identical to
0.45.1 and wheel = tree.

Chapter 7 (PDF 195-236, problems 7.1-7.29 on 230-235): brief in scratchpad `book/ch07/BRIEF.md`,
four solvers running on the 0.45.2 snapshot.

**0.45.2 is closed** (#390, `e090c89`): PR CI green; Quality Gate Deep (push) and Deep
qualification green on `e090c89`; a `git+https` install changed only `engcalc-colab`, 33 files
identical, smoke 51/51. In his Colab (Untitled9: fresh session, his cell 0, cell 3, 2026-10-01):
`engcalc 0.45.2`, the integral of 6.15 drawn, `50 kN` in the solve's equation row, one list of
three cases, `z = g(2) = P`; screenshots sent.

### His book, chapter 7 complete (virtual work in frameworks; problems 7.1-7.29, examples 7.1-7.12)

Every number agrees with an oracle and, where printed, with the book (book misprints: Ex. 7.9's
off-diagonal sign and d22 = 3/8; 7.12's k36 = -0.489, not -0.429; Ex. 7.6's twist figure is 4x).
`Capitulo_07.ipynb` is in his Drive and Documents (runs end to end on 0.45.2; only the psi
notice). Fixed in 0.45.3, below. Findings still open:
- **Slow:** a symbolic 3x3 `inv` of trig entries takes ~70 s (7.29); an integral with symbolic
  exponents does not return (7.17; `expand` first works).
- **Missing:** an integer assumption (sin(nπ) stays); general `b(y)` inside `integrate`;
  `assume(beta < pi/2)` refused and stops the cell; `$$` display math in a text block breaks.
- **Presentation:** 7.4/7.6 unreadable (simplify puts dofs into exponents, `log(2^{...})`);
  a function definition shown expanded; product-rule derivatives uncollected; a matrix
  integral drawn entry by entry and off the page; definite integrals not collected
  (`6a/L + (3c - 9a)/L + ...`); a matrix times a scalar not simplified; `log` never `ln`;
  zeros unsimplified (`((2-π)L - (2+3π)L + 4πL)/(4π)`); the `extrema` block in English;
  `:=` lines with `integrate` show the value only (the integral is now written on matrix
  lines); math in a `###` heading literal; a loop of `:=` lines reading a matrix entry
  not gathered into a table.

### 0.45.3: what chapter 7 found read wrong or refused (his pick, 2026-10-01)

Branch `fix/chapter-7-misread-numbers`: renderer `_in_force_and_length` (a unit not declared,
with no family, holding a stress, a mass or one dimension twice, is written in the sheet's
force and length - palette's, else kN/m, kip/in, kgf/cm; `E*I` now reads kN·m²) used for
scalars, matrices, columns and plots; ratio columns and axes are numbers (angles keep °);
`entry_quantity` gives a written 0 its vector's unit; engine `_real_integral`/`_logs_real_at`
(indefinite: flip a log whose argument at 0 is a negative number; definite rational: F(b) -
F(a) flipped at the lower bound); numeric log sums tried as written, then split, then
combined; `:=` builders `zeros`/`identity`/`diag`/`integrate` and part assignment
`K[[..],[..]] :=` (parser `target_index`, `with_a_part`, whole-number index arithmetic) with
the assembly note then the matrix in loops; `NumericContext.variables` from `assume`; `subs`
with two lists; `atanh`; `:=` written forms (`\cos`, `\int`, measurements in typed order).
Audit (subagent): first pass found D1-D6 (angle column, psi on `:=`, log of a product of
negatives, indefinite flip with a symbol, plots, loop index), all fixed and re-audited: no
regression; 107 of 706 sheets differ from 0.45.2, every stored value identical or
numerically equivalent. Contracts `test_what_chapter_7_found` (23).

**0.45.3 release evidence (tree `68ba114` + docs):** suite 3572 (SymPy 1.14 and 1.13.3);
wheel 33 files identical; clean Python 3.12 venv with Colab's pins adds only Pint and its
dependencies; smoke 52/52; suite against the installed wheel 3571 + surface 5; 24 reference
pages identical to 0.45.2 and wheel = tree.

**0.45.3 is closed** (#391, `22716e5`, merged with his yes): CI, Quality Gate Deep (push) and
Deep qualification green on `22716e5`; a `git+https` install changed only `engcalc-colab`, 33
files identical, smoke 52/52. In his Colab (Untitled9, fresh session, his cell 0, cell 3,
2026-10-01): `engcalc 0.45.3`, `f = 0.0004 1/(kN·m)`, K assembled by `:=` parts in a `% for`,
C1 and C2 solved with `ln(3 - x)`, the `x/a` column a number; screenshots sent.

### Chapter 7's leftovers (his "aborda lo pendiente", 2026-10-01)

Branch `feat/chapter-7-pending`: `matrix_inv` of a matrix holding functions by adjugate over a
Berkowitz determinant (100 s -> 0.01 s; rational matrices keep `inv()`); `_real_integral`
expands an integrand with a symbolic power of the variable (7.17 hung > 20 min, now 3 s);
`assume(n > 0, integer(n))` (parser + engine, page `n \in \mathbb{Z}`); engine `_simplified`
and `_readable_logs` on simplify, diff and solve answers (`log(2^(a))` -> `a log 2`, a log of
a pure power by its primes, `2^(-a) 2^a` combined); `_collected` on definite integrals with
two or more sum-over-denominator terms; the printer's `ln_notation` and `ln(x)` accepted.
Not done, by his earlier decision (2026-09-25: keep `Where`/`Domain` in English): the
`extrema` block's words. Contracts `test_what_chapter_7_left` (9); suite 3583.

### His book, chapter 8 complete (nonlinear analysis, an introduction; problems 8.1-8.10, examples 8.1-8.9)

Every number agrees with an oracle and, where printed, with the book (book slips: 8.6's limit
deflection 1.204 in is 1.243; 8.7's limit point 192 kip at 28.1 in belongs to beta = 3e4, not
the stated 1e5 - 267.7 kip at 66.8 in; 8.8's Eq. (e) drops cos alpha; 8.4's figure repeats 8.3's
initial slope; M_p 1225.3 is 1225.1). `Capitulo_08.ipynb` in his Drive and Documents (runs
end to end on 0.45.3; only the `=`-constant notices). Findings, not fixed:
- **Wrong value:** `solve(eq(...), t, 0[deg], 15[deg])` returns a number in degrees read as
  radians (`numeric(t_1, deg)` = 361.32°); a ratio of `acos(..)/kL` shown as degrees
  (32.32° for 0.56); `atan(1)^2` in a ratio left as `rad²`.
- **Refused:** `subs` on a `:=` line ("unsupported numeric function"); `sum` on a `:=` line;
  `numeric` of `elliptic_k` and of an integral SymPy returns as a complex piecewise (no
  numerical quadrature fallback; a `:=` integrate with no closed form); `plot` of an `interp`
  refused at the table's own last point after unit round-trips (message prints `ksi·in³·s²/m/kg`).
- **Slow:** `plot` of `sqrt(t)/sin(t)`-type curves 40-80 s.
- **Design question:** a function's body never takes `=` constants defined after it
  (`w(x) = A_1 sin x + A_2`, then `A_1 = ...`): the book's pattern; only a solve fixes them.
- **Presentation:** the loop rule drops the parentheses of `(a/L)^(1/3)` (reads a^(1/3)/L);
  `x/0.85` in a function shown as `1.18 x`; `% while` never shows its update formula; a loop's
  `solve` lines printed after its table; plot maxima are sampled points, not the solved ones;
  `0.3` turning into `3.0`/`10.0` in a system solve; unit order `in·kip`; substitution rows in
  another unit than the value; `(15.00°) - (5.00°)` double parentheses; `N := 40` shown 40.00.
- **Missing:** `dsolve`; `cot`/`sec`; relational assumptions (`L < 3 L_e/2`).

**0.45.4 audit and release evidence:** audit of be3a759 found B1 (a mechanism of sines and
cosines got an "inverse": the determinant was tested unsimplified), B2 (trig inverses much
longer), B3 (loop labels `\log`), B4 (`L^(-n) L^(n+1)`); all fixed in c3abb18 and re-audited:
no defect, 22 of 794 sheets differ beyond log -> ln, every value numerically equal; a 6 x 6
frame with a symbolic angle inverts in 113 s (0.45.3 did not finish). Tree `8d70e68`: suite
3587 (SymPy 1.14 and 1.13.3); wheel 33 identical; clean 3.12 venv with Colab's pins adds only
Pint and its dependencies; smoke 53/53; suite against the installed wheel 3586 + surface 5;
24 reference pages identical to 0.45.3, wheel = tree.

**0.45.4 is closed** (#392, `dddd38b`, merged with his yes): PR CI green; Quality Gate Deep
(push) and Deep qualification green on `dddd38b`; a `git+https` install changed only
`engcalc-colab`, 33 identical, smoke 53/53. In his Colab (Untitled9, fresh session, cell 0, cell
3, 2026-10-02, SymPy 1.13.3): `engcalc 0.45.4`, the rotation's inverse, `n ∈ ℤ` with
`sin(nπ) = 0`, `ln`, `(a - c)/L`; screenshot sent.

### Chapter 8's wrong values and refusals (his pick, 2026-10-02)

Branch `fix/chapter-8-wrong-values`: engine `_as_written_quantity` returns an angle root in
radians times `rad` (was a bare number in degrees); renderer shows `rad^n`, n ≠ 1, as a number;
`_MatrixNumbers._BUILDING_CALLS` adds `subs`, `sum` (written `f|_{t=t_0}` and Σ; unknown
calls italic as sheet functions, `_WRITTEN_OPERATORS` keeps `\operatorname`); numeric
`_integral_in_numbers` (mpmath quadrature) for `sp.Integral` and special functions of numbers
(`elliptic_k`); engine `_integral_of` leaves a real integrand's complex closed form as the
integral; `interpolation_segment` clamps within 1e-9 of the ends, message in reduced units.
Left by my judgement: `acos(0.5)/kL` with a plain kL stays an angle (θ/2 is an angle; write kL
in rad or divide by 1[rad] for a ratio). Not done (not asked): slow plots. Contracts
`test_what_chapter_8_found` (8); suite 3595.

**0.45.5 audit and release evidence:** audit of 9bf49c8 found E1 (a `mm/m` root printed as
an angle, 0.17°) and E2 (a divergent integral killed the cell with an OverflowError in the
printer); fixed in 026ec92 (only angle units give an angle; `evaluate_symbolic` refuses a
non-finite value) and re-audited clean; 21 of 806 sheets differ from 0.45.4, all intended, no
value changed. Chapter 9's solver then found a crash present since 0.45.3 - a `% for`
assembling a `:=` matrix wider than the page (`_assemblies` read `result.value`) - fixed in
5ec7651 (summary from the quantity matrix, exact zeros) and checked by the auditor. Tree
`5ec7651`: suite 3598 (SymPy 1.14 and 1.13.3); wheel 33 identical; clean 3.12 venv with Colab's
pins adds only Pint and its dependencies; smoke 54/54; suite against the installed wheel 3597
+ surface 5; 24 reference pages identical to 0.45.4, wheel = tree. His yes: "Cuando la
auditoría esté limpia, publica la 0.45.5".

### His book, chapter 9 complete (geometric nonlinear and critical loads; problems 9.1-9.16, examples 9.1-9.13)

Every number agrees with an oracle and, where printed, with the book (book slips: Ex. 9.3
states alpha 1.25e-4 and solves with 1.125e-4; Prob. 9.9's Iz = 210 in^4 looks like 2100).
Findings, not fixed:
- **No route to a critical load from an assembled numeric matrix:** `eigenvals`/`det` refused
  on `:=` lines and `=` lines refuse a `:=` matrix; `eigenvals` of a mixed-unit pencil
  refused; `eigenvals(...)*3` crashes; `solve(eq(det(K - G_x), 0), x, a, b)` demands `x` as
  data. Every frame example used inverse iteration in `% while`. Wanted: `eigenvals` of
  numbers and a generalized `eig(K, -K_g)`.
- **Wrong value on the page:** a computed exact 0 in a `solve` result takes the vector's
  length unit (`theta = 0.00 m`), and the next line fails "incompatible units"; a `% for`
  holding a `% while` tabulates the values from before the while.
- **Refused / hangs:** `{a}` placeholder in a `% while` condition not substituted; a placeholder
  holding an operator after `)` / space is "invalid syntax"; `extrema` of a trigonometric ratio
  hangs (> 120 s); a range `solve` says "no root" when the equation adds incompatible units.
- **Missing:** pound-force (`lb`, `lbf` refused though pages print lbf); a kip palette; a list
  in a loop placeholder.
- **Presentation:** `solve(K, -2*F)` written `K^{-1} -2 F`; nested `% for` assembly summary
  merged and printed after; `identity(2)` written as a word; `1e8[mm^4]` argument written
  100000000.0; pass 1's rows before the loop rule; nested loops dump every pass's matrices
  (pages 2.7-4.3 MB); loop tables print the raw tuple; `det(B - λI)` with I the inertia;
  `tan(π/4)` in a table reads `10.00 × 10⁻¹`.

**0.45.5 is closed** (#393, `83ae814`, merged with his yes): PR CI green; Quality Gate Deep
(push) and Deep qualification green on `83ae814`; a `git+https` install changed only
`engcalc-colab`, 33 identical, smoke 54/54. In his Colab (Untitled9, fresh session, cell 0,
cell 3, 2026-10-02): `engcalc 0.45.5`, `t_1 = 6.31°` and `sin = 0.11`, `f|_{t=t_0} = 1.00`, the
quadrature integral 3.96 m³, a 12 x 12 `:=` assembly in a `% for`; screenshots sent.
`Capitulo_09.ipynb` in his Drive and Documents (every cell runs on 0.45.5).

### Chapter 9's top findings, fixed (branch `feat/numeric-eigenvalues`, pushed, no PR, not released)

His "sí, sigue con eso" (2026-10-04), then "Audita la rama y, si está limpia, publica la
0.45.6" (2026-10-04; his "Ok" to: fix what the audit finds, re-audit, publish only when
clean). A session that ran out of credits left the first fixes uncommitted (WIP `d33548f`);
finished in `17a09f1`; the first independent audit (subagent, 32 mutants) found it **NOT
CLEAN**, and every finding was fixed with contracts:
- **B1** `extrema` of `P/sin t` on 0°-180° printed 815 invented "global min" rows (main
  refused): letting a periodic singularity family through left the slope's numeric search
  to call points beside a pole its extrema. Now `extrema._no_singularity_in_domain` lets a
  family only *prove* the range holds none of its members (complex families have none);
  any member inside or at an end is unresolved, as on main.
- **B2** `eigenvals([0, 1; 1, 0])` gave `[0; 0]`: the unit was read off the diagonal. Now
  `matrix_numeric._eigenvalue_unit`: a diagonal entry, or the k-th root of a closed walk of
  k entries (λ² = a₁₂ a₂₁), every entry checked against `unit · s_i / s_k`; a matrix with no
  closed walk is nilpotent (all zeros, plain numbers).
- **B3** Example 7.4 regressed: the WIP's `written_zeros` were known only to `numbers_of`, so
  `GJ*transpose(D)[1]/T` read `0.00 m` again. Reversed: main's rule stays (a unitless zero
  taken out of a matrix takes the unit beside it), and `NumberMatrix.worked_zeros` /
  `QuantityMatrix.fixed_zeros` mark the zeros an operation worked out (solve, product,
  inverse; kept through transpose, a part, blocks, a factor, assignment into a part, and a
  `:=` store, including a dimensionless 0 with a unit), which stay plain numbers.
- **S1** the solveset skip turned main's exact `x = π`, `asin(1/4)`, `-π/4` into `≈`: now only
  a trig function under a root in an expression of more than 20 operations
  (`_TRIGONOMETRIC_RADICAL_OPERATIONS`; measured on main: 9-18 exact in < 2 s, 22 took 67 s,
  24/44/100 hang).
- **S2** `{k}` in a `% while` condition was written in once (1000 passes); now at every
  evaluation, in `% if` too (`control._with_placeholders`).
- **S3** range `solve`: "incompatible units" whenever a sample failed for units and no root
  was found (a pole at 0 brought "no root" back); the "range has no unit" hint only for a
  range written without one (a degree is dimensionless to Pint).
- **S4** a `% for` table lost a correct column when a block of a *later* pass set the same
  name: rows a block shows now carry their pass, and the scan stops at the next pass.
- **S5** `eigenvals(K, G)` with a singular G blamed K's supports; now names the second matrix.
- **S6** the claim "a solve's exact 0 reads 0.00" held only when F's zero had a unit; true now
  for `F := [10[kN]; 0]` too.
- **S7** 16 of 32 mutants survived; contracts added for each (see the mutation run below).
- Dead code removed: the sheet-function guard on `det`/`eigenvals` (both reserved
  identifiers); `inv`/`transpose` in `_WRITTEN_OPERATORS` (unreachable).
- Still from the first round: `det` and `eigenvals(K)`/`eigenvals(K, G)` on `:=` numeric
  matrices (one-element cantilever 2485.96 kN = NumPy; his p9_4 1241.57 = his inverse
  iteration); the placeholder after `)`/`]`/an operand parses as ` + 1`; Example 9.1's
  limit point φ ≈ 0.44, 339.21 kN (book 340), also in degrees; main hangs.

Declared limitations (not defects): a monotonic range of a long trig-under-root expression
refuses ("could not validate", the 0.9.x contract); a pole inside the range refuses;
eigenvalues are ordered by signed value (with an indefinite G, `lam[1]` is the most
negative); unit-misfit messages print base SI units; a loop label shows `"+ 1"` as `1`.
Older defects the audit found, not from this branch (N6): `P/(x-2)` on [1, 3] labels the ends
global min/max with no "unbounded" (a named constant defeats the ±∞ test); `P/(x(3-x))` on
[0, 3] labels "local min, global max, global min"; `transpose(transpose(T))` renders
`T^{T}^{T}`; `cos x + 1/sin x` on [0.5, 2.5], `1/sin(x²)` on [1, 2] and
`sin x + 1/cos(x/1000)` on [0, 3000] hang on both.

**Second audit (subagent, at `d2c4955`): NOT CLEAN**, one blocker: marking every worked-out
zero a number moved the S6 error onto springs - `solve([k, 0; 0, k], [10 kN; 0])` gave
`u_2 = 0.00` and `k u_2 = 0.00 kN/m` (main: `0.00 m`, `0.00 kN`). Fixed with his "a tu
criterio": `matrix_numeric._worked_zeros` - a solve, product or inverse marks its unitless
zeros plain numbers only when its operands mix dimensions (a frame) or already carry such a
zero; of one kind (springs, a truss) the zero borrows the unit beside it, as on main. Also
from it: contracts for the zero through a part, blocks, a product, a sum and an assignment
into a part; two placeholders in one condition; `quantity_matrix_of` asks Pint for a
dimension only for zeros (p9_5 now 18 s, main 20 s). Re-verified there and kept: B1-B3,
S1-S7, his p9_4/p9_5/p9_7 eigenvalues = NumPy.

**Third audit (subagent, at `51727e8`): CLEAN with conditions** - SF1: a frame loaded only
axially (`K` axial + bending, `F := [10[kN]; 0; 0]`) left its transverse displacement a
plain number, so the shear `12EI/L³ v` read kN/m where main read kN (main's rotation was
wrong instead); SF2: this file had a duplicated, stale block of ~1900 lines (my splice in
d2c4955 found the closing marker before the section; rebuilt from 17a09f1's structure);
SF3: three mutants of the zero rule survived. Fixed: `matrix_numeric._units_by_work` - an
entry of a solution its load leaves unknown takes its unit from its own stiffness by work,
`K_ii c_i² = F_j x_j` of a loaded entry (m against kN/m, none against kN·m), unless the load
holds a zero of unknown kind or the root has no whole exponents; contracts for SF1 and SF3.
Visible effect: his p5_10c prints its zero translations `0.00 mm` (rotations stay plain).

**Fourth audit (subagent, at `aa4de89`): NOT CLEAN by a hair** - the work rule is right on
every stiffness tried (flexibility N·m, mass 1/s², grids, torsion, kN/mm, kgf, rotational
springs left plain) but a solve that is no stiffness took the unit of its first load:
equilibrium `[M; H; V]` gave V `0.00 N·m`, a 6×6 transformation gave a rotation `0.00 m`.
Fixed: the rule applies only where K_ii has a dimension; `_eigenvalue_unit` reuses
`_unit_root`. Contracts for both cases, a kN/m² diagonal and a load only in column 2.
Notes kept: `numeric(d, mm)` of the axial-only frame now refuses its rotation (as with any
nonzero rotation on main); `inv(K)*F` leaves the zero plain where `solve` gives it a unit;
zeros print in base SI (main too); `d[3] + 1[mm]` silently 1 mm (main too).

Contracts `tests/test_what_chapter_9_found.py`: 59. Suite 3657 collected and passing on
SymPy 1.14 and 1.13.3 (39 KaTeX tests skip without `tools/katex/node_modules`). Mutation
(author's 33): 31 killed, 2 equivalent; the second audit's 46 found the zero-propagation and
two-placeholder gaps now covered. Corpus, 238 sheets: the 7 chapter 9 tables (byte-identical
to the audited render) and chapter 7 pages that alternate on main by itself (ex7_12, p7_17,
p7_23, p7_29); render total 2000 s against main's 2622 s.

**Fourth audit follow-up at `932685d`: CLEAN** (the guard holds; every stiffness case
unchanged; full corpus identical to aa4de89 but chapter 7 noise). Its contract gap (a load in
column 2 only on a frame, a zero diagonal) closed with two contracts; the three mutants it
named are killed.

**0.45.6 release evidence (tree `a6541de`, "release 0.45.6"):** the seven version assertions
RED before the bump, GREEN after; source suite 3659 twice (SymPy 1.14) and 3659 on 1.13.3;
wheel from `git archive`, its 33 package files byte-identical to the commit (the working
copy differs only by CRLF); clean Python 3.12 venv with Colab's pins (ipython 7.34.0, numpy
2.2.6, matplotlib 3.10.0, sympy 1.13.3) adds only Pint 0.26.1, flexcache, flexparser,
platformdirs, typing_extensions; smoke outside the repository 55/55 (new 0.45.6 check:
2485.96 kN by eigenvals, a frame's θ = 0.00 without metre, `{a}` in a while); suite against
the installed wheel from a tree with no `src/`: 3658 + the by-path surface test (5/5 on the
wheel's `magic.py`); 24 reference pages (tools/*.eng × none/kN/kgf) wheel = source. His
yes: "Audita la rama y, si está limpia, publica la 0.45.6".

**0.45.6 merged** (#395, squash `dd6da36`, 6/6 CI on `7984ddf`): git+https install of main
in a Colab-pinned venv = 0.45.6 at `dd6da36`, 33 files identical to main, smoke 55/55;
Deep qualification green on main. **0.45.7** (#396, his "Fusiónala como 0.45.7"): the Codex
review of #395 found `eigenvals([0, -1, 0; 1, 0, 0; 0, 0, 1e12])` read ±i as two zeros (the
tolerance used the largest eigenvalue); each eigenvalue now judged by its own size above a
1e-13 round-off floor. Evidence on `090ee46`: version assertions RED then GREEN; suite 3660
twice and on 1.13.3; wheel 33 files = commit; clean Colab-pinned venv adds only Pint and four
small deps; smoke 56/56; suite against the wheel 3659 + surface 5/5; 24 reference pages
wheel = source. Not audited by a separate auditor (a 4-line change; he asked to merge).

**Exact next step:** merge #396 on green CI; then post-merge checks (Deep gate on main, a `git+https` install in a Colab-like venv, smoke)
and the closure in his Colab. After that, **0.46.0, his asks of 2026-10-04 (high on the
list)**, on a new branch: (1) an expression or call split over lines inside parentheses or
brackets - today `y = sin(` + `x)` says "unbalanced parentheses", and
`matrix_syntax.consume_matrix_statement` says "ordinary multiline calls remain unsupported"
(only matrix literals continue); (2) `T'` for `transpose(T)` (now "invalid syntax"); (3)
`U^-1` on a `:=` line ("is not an operation between matrices"; `inv(U)`, `solve(U, F)` and
`T^-1` on `=` lines work). Then his pick among the rest of chapter 9's findings
(pound-force, kip palette, presentation list above); chapter 10 (PDF 290-).

**`d := solve(K, F)` - a matrix defined by its numbers** (#294, 0.34.0).
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

_Rewritten 2026-09-26 (the text before it described 0.13.0)._ A new conversation - in
this Claude account or another one - knows only what is in the repository. Start it on
`eliaszamora/engcalc-colab`, branch `main`, and:

1. Read `AGENTS.md`, then the block **Where things stand today** at the top of this file
   and the newest sections just above **Current baseline** (the last is 0.41.0's closure,
   with the open findings and the **Exact next step**), then `NEXT.md` for how a release
   is cut. The sections between were written at 0.13.0; their approved behaviour still
   holds, their numbers do not.
2. Verify against GitHub before relying on it: `main`'s SHA and version, open PRs, CI.
3. Tooling in a fresh container: a venv with `pip install -e ".[dev]" pytest-xdist`,
   `npm ci --prefix tools/katex` (without it 30 KaTeX tests skip), then
   `pytest -q -n auto`. A release closure also runs `tools/smoke_installed.py` from
   outside the repository against a clean `git+https` install (its docstring has the
   recipe) and compares the `tools/*.eng` pages rendered from the install and from `src`.
4. The user's Colab is in their Google account, not in the repository; the notebooks
   named here ("Untitled9", "Ejercicio 2.2") are theirs. A session cannot open it unless
   given a browser; the user checks a release there with the install cell after a restart
   from the menu.
5. The user writes in Spanish; answer in Spanish. The documents here are in English.

Two rules that have each paid for themselves repeatedly: never merge without explicit user
approval, and never let whoever built something be the one to certify it. The second is
suspended by explicit direction and what that costs is documented rather than argued.

The habit that has caught more than either rule: **measure before concluding, including
about your own work.** In this project a confident recommendation has been overturned by
measurement four times, an analysis of a measurement was wrong twice, and an intermittent
test failure was nearly blamed on the change in hand until `main` was measured at the same
failure rate. Nothing here is believed because it reads correctly.

Never invoke Codex / Codex Cloud without explicit authorization.
