# EngCalc Current Project Context

> **Read the block directly below, then `NEXT.md`.** Everything after it was last
> updated at 0.13.0 on `9a9d6e3` and describes a tree that no longer exists. Its
> *approved behaviour* and *evidence hierarchy* sections are still in force and are
> regression requirements; its baseline numbers, release history and open-issue list are
> not — do not quote its counts.

## Where things stand today

_2026-09-23._

| | |
|---|---|
| released | **0.33.4** - this release PR, carrying #282; its closure is recorded below |
| before that | **0.33.3** - #280, `1ed3831`, verified after its merge and in his Colab |
| open PRs | this release's; **#265**, the frame for `/code-review ultra 265` - a draft never to be merged |
| default suite | **2772 passing**, about a minute and a half with `-n auto` |

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

**Then**, known and not requested:
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
