# Where EngCalc stands, and what to pick up next

_Written 2026-09-05, at the end of the session that worked the findings of an external
trial. Read this before `CURRENT.md`, which has not been updated since 0.13.0 and
describes a tree that no longer exists._

## Baseline

| | |
|---|---|
| `main` | `87839a7` (#117 merged) |
| declared version | **0.29.2** — released by #118, carrying #115 through #117 |
| default suite (`pytest -q`) | **1855 passing**, about 3 minutes — `tests` plus `quality_tests/fast` |
| Deep Property Gate (`pytest quality_tests/deep`) | **53 modules of properties**, about 2 minutes |
| CI | six jobs: Python 3.10–3.14 plus one pinned to Colab's `ipython==7.34.0` |

The suite took seven and a half minutes and the Gate twenty-five, until Pint's registry
was shared rather than rebuilt per engine. If a run starts taking that again, measure
before blaming the machine — and note that `--durations=25` would not have found this
one. It reported a slowest test of 4.65 s out of 378, which reads as nothing to fix. A
fixed cost paid once per engine, 724 times, is invisible to it; timing the constructor
is what found it.

**Releasing.** The patch digit is a release of corrections carrying no new feature -
`0.9.2`, `0.10.1`, `0.25.1`, `0.26.1`. The minor digit is a capability that was not
there before, as `0.26.0`'s US customary units were. Kept here because the next one will
want it: a bump is not the two-file change this note first claimed. The version string is
asserted in four test modules, and `tests/test_version.py` additionally pins the README's
opening line, its closing line and its changelog. Seven files:

| file | what holds the string |
|---|---|
| `pyproject.toml` | `version = ` |
| `src/engcalc_colab/__init__.py` | `__version__` |
| `README.md` | the `Current version:` line, a new changelog entry, and the closing `Version:` line |
| `tests/test_version.py` | `EXPECTED_VERSION`, both README assertions, and four test *names* — the fourth names the 0.25.0/0.24.0/0.23.0 trio and can stay as it is |
| `tests/test_packaging.py` | two literals, and two function names that had gone stale saying `0_9_2` (renamed with the 0.25.1 bump) |
| `tests/test_packaging_metadata.py` | one literal |
| `tests/test_parser.py` | one literal |

Two things not to disturb: `## v0.25.0 load cases and combinations` names the release a
feature arrived in, and `test_readme_version_notes_cover_0_25_0_0_24_0_and_0_23_0` needs
those three changelog lines to stay where they are.

The division of labour between a feature pull request and the release that carries it:
the feature adds a plain `## Its Name` section to the README and does not touch the
version; the release renames that section to `## vX.Y.Z its name` and adds the changelog
bullet. `v0.25.0` and `v0.26.0` were both written that way. A release of corrections has
no section to rename and writes one, which is what `v0.23.3` and `v0.25.1` are.

## What this session was

An external trial: someone was handed the repository link, installed the package, and
worked a reinforced-concrete beam from an ACI 318-14 example without reading `src/`. The
engine got the engineering right — reactions, flexural capacity, shear design, all
matching an independent hand check. What it found was four presentation defects, and all
four are now on `main`:

| | | |
|---|---|---|
| #76 | `Mu` printed as `M` | SymPy's Greek table collapses fourteen capitals onto Latin letters; our guard trusted any rendering that began with a backslash |
| #77 | `D/C` printed as `9.63e-7 kN·m/(MPa·mm³)` | a dimensionless ratio kept the units the algebra left behind |
| #78 | `φMn` printed as `2.84e8 MPa·mm³` | the unit-family table was keyed on a string whose ordering depended on what the session had computed earlier |
| #79 | `0.588235294117647` in a formula | SymPy prints a Float at full binary precision |

**Every one was found by looking at a rendered page.** None was found by the suite, and
the suite was 1387 tests at the time.

In three of the four the cause announced first was not the cause. #76 looked like our
uprighting rule and was SymPy's translation table. #78 looked like a tie in a complexity
heuristic — that tie was real, but fixing it changed nothing, and the defect that
mattered was a dictionary key. #79's first rule deleted the `1.0` of `0.9*D - 1.0*Lv`,
caught by a contract from #71. What corrected the course each time was executing
something, not reasoning further.

## Where the findings landed, and what is still open

All four findings of the external trial are closed, and so are two of the three things
that came out of working RC-1. A matrix frame analysis run as a benchmark then produced
seven more, of which four are fixed. What is open, in the order I would take it:

- ~~`_unit_terms` is now inert~~ — **removed by #110.** All seven of the display
  findings are closed and the heuristic behind every one of their ties is gone
- ~~the factors of a compound unit are ordered alphabetically~~ — **fixed by #104.**
  Not a formatter to rewrite: Pint exposes the sort as
  `registry.formatter.default_sort_func`, and `_units` had kept the written order all
  along. One function that returns its argument; `m·N` and `ft·kip` were the only two
  compound units in the whole suite that moved
- **a wide substitution is split into additive terms** by the wrapping path, in the RC-3
  section directly below
- ~~the hunt for guards nobody is checking~~ — **run on the engine and the parser by
  #115.** What it found, and what is left of it, is a section of its own below

The finished ones are kept rather than deleted: each says what the answer turned out to
be and what it cost to find, which is the part a summary would lose.

### The display unit is decided in seven places

**Closed.** A matrix frame analysis, run
as a benchmark, asked one question - *in what unit is this shown?* - of seven different
code paths and got seven answers. Four of them had already drifted and were reconciled one
at a time; #99 settled one, #102 and #109 fixed the last two. All seven are closed, and
#110 removed the heuristic behind every one of their ties.

| where | what decides | state |
|---|---|---|
| a scalar | `_display_quantity`: family, then the factors' shape | the reference behaviour |
| a homogeneous matrix, a table column | `_aggregate_unit` | a tie handed the fallback the win, fixed |
| a heterogeneous matrix cell | `_quantity_latex`, `declared` defaulting True | fixed |
| the substitution stage | `declared` per name, from what the `:=` wrote | fixed by #102 |
| a family with one member | stops at kilo on purpose; the matrix factors instead | settled by #99 |
| `GPa*mm` against `kN/m` | the shape of the factors, not their number | fixed by #109 |

All three, with the answers they got and what each cost on a real page:

- ~~**The substitution stage** shows a value in the unit it was stored in.~~ **Fixed by
  #102.** The question it was waiting on - which substituted values count as declared -
  turned out to be already answered: `written_unit_names` drew exactly that line per
  assignment and then threw the answer away, so the engine keeps the set now. One
  argument was missing, `declared`, which `_quantity_latex` takes and
  `_NumericSubstitutionLatexPrinter` never passed. `70303.22 GPa*mm^2/m` became
  `70303.22 kN/m` and `11.86 GPa^0.5*mm/(kg^0.5*m^0.5)` became `374.98 1/s`, which is
  also where the fractional unit exponents on the page came from.
- ~~**A family of one member** cannot move the magnitude into the readable band.~~
  **Answered by #99, in the opposite direction to the one this bullet assumed.** It
  proposed giving every family a mega step so an assembled stiffness could reach
  `209.67 MN`. The engineer was asked and wanted the reverse: *"prefiero que nos quedemos
  con kN, m, s ... no me gusta que hayan algunos en kilo y otros en mega"*. So the
  families now **stop at kilo** and a matrix takes the largeness outside as `10^3 x []`,
  which is MATLAB's `format short` and siunitx's `fixed-exponent`. `MPa`/`GPa` keep both
  steps deliberately. A large scalar outside a matrix does stay a large number - `517195.95
  kN*m` - and that is the accepted cost, not an open defect.
- ~~**`_unit_terms` cannot separate `GPa*mm` from `kN/m`.**~~ **Fixed by #109, and not
  the way this note predicted.** Both halves of the difficulty were real - both cost 2,
  and the same 2 protects `kN/mm` - but the way out was not the written form. It was to
  stop comparing *how many* factors and start comparing *what they are*: `kN/mm`,
  `tonf/m` and `kgf*cm` reach their dimension through a force, which is how a line load
  or a moment is spelled, and `GPa*mm` reaches it through a pressure, which is what
  `E*t` leaves behind. A plate stiffness printed `1680.00 GPa*mm` and now reads in kN/m.

  **The count is now inert.** The whole suite passes with `_unit_terms(quantity) <=
  canonical` replaced by `True`, and an exhaustive search over twenty base units in six
  composite forms against all three family tables finds no unit with a family member's
  shape and a larger count - which is what the dimensional equation predicts, since the
  shape fixes which dimensions appear and the exponents then follow. Removing it is the
  next change; it is kept out of #109 so that the removal is judged on its own.

That last line is the shape of the answer. One function taking a quantity and the unit
names the sheet actually wrote, returning the unit to show; every path calls it. The
weighting stops being the discriminator and what was typed becomes it, which is the only
thing that tells `kN/mm` from `GPa*mm`.

Until that exists, every new surface is born divergent: matrices, tables and the
substitution stage each grew their own copy of the decision, and each had to be corrected
separately after a page showed the drift.

**Amended by #100.** The sentence above is right about the *unit* paths and was wrong
about one thing it swept in. `_significant_figures` is called from five places, and this
note counted all five as copies of one decision. They are not. One of them formats a
number; the other four ask whether a value sits in the natural band for a unit, which is
a different question wearing the same clothes. Unifying them - which looked like the
tidy fix and was implemented before it was measured - left `0.00008*m` printing as
`0.00008 m` instead of `0.08 mm`. The separation to copy is siunitx's, where `round-mode`
and `exponent-mode` know nothing about each other; it is not a merge.

### A third unit system: metric-technical

Asked which units he works in, the engineer answered with a rule rather than a list:

    "si te los doy en kgf, entonces que sea kgf, si te los doy en MPa entonces que sea
     MPa, si te los doy en ambos, elige kgf cm2"

That is what this renderer already does for US customary - RC-1 gave imperial its own
family table and `_is_us_customary` detects it - applied to the system half the
Spanish-speaking world writes a memoria in. Peru and Mexico put the steel modulus at
2.1e6 kgf/cm^2; f'c and fy are written in kgf/cm^2 beside MPa. Without a table of its
own, such a sheet was rewritten into SI under its author:

    fc := 250*kgf/cm**2          ->  24.52 MPa      the *declared* unit, overruled
    E := 2100000*kgf/cm**2       ->  205.94 GPa

#108 adds `_TECHNICAL_UNIT_FAMILIES` and `_is_technical`, and a whole sheet now reads in
kgf, cm, kgf/cm^2 and tonf*m.

**Two things it turned over, both worth keeping.**

`test_an_aggregate_keeps_the_engineers_unit_against_the_band` used `0.5 tonf`, and stopped
testing what it was written to test: with a technical family, `0.5 tonf` reads
`500.00 kgf` whether the authorship gate is present or not, because that is a band step
*inside* the engineer's own system - exactly as `0.5 kip` has always read `500.00 lbf`.
Its docstring also claimed `kN/mm` could not serve as the case, and that has not been
true since the band work of #94/#97/#99. Re-pointed at `kN/mm`, measured, and the
mutation harness now checks that it bites.

The gate is not an orphan: fifteen tests fail when it is disabled.

~~**What it does not fix.** `25000 kgf / (100 mm x 100 mm)` still reads `2.50 kgf/mm^2`
rather than `250.00 kgf/cm^2` ... sections written in centimetres, which is what this
engineer writes, are unaffected.~~

**Fixed by #119, and that last clause was the mistake.** A structural section is written
in *millimetres* - this repository's own benchmark opens `b := 300*mm` - so the case was
not the corner this note called it. Shown it, the engineer said `kgf/mm^2` is not a unit
he has ever used. It also cost more than a unit: `25000 kgf / (300 mm x 450 mm)` printed
`0.19` where the stress is `18.52 kgf/cm^2`.

There is no rule, and three were tried before admitting it: "the sheet never wrote this
composite" sends `mm^2` built from two declared `mm` to `cm^2`; "the family member has
several factors" and "a one-member family is authoritative" each break one of `N*mm`,
`kN/mm` and an inertia in `mm^4`. What is true is a convention - a stress in the technical
system is written `kgf/cm^2` - and it is recorded as one, yielding to any unit the sheet
actually wrote. Writing the note as a remainder was easier than finding that out, and the
reason it survived is that the reason given for it was never checked.

### Two tables, two questions

`_UNIT_FAMILIES` is what the system *chooses*. `_UNIT_ALIASES` is what the engineer may
*write*. Keeping them straight matters, because #99 took mega out of the first for a
reason that says nothing about the second - the sheet should stay in kilonewtons rather
than mixing prefixes - and `MN` had never been in the second at all.

So `P := 12*MN` answered "unknown numeric name 'MN'. Define the numeric value first",
reading a unit as a variable the engineer had forgotten to define. The alias table gave
pressure four steps and force two. #107 adds the one a bridge reaction is written in, and
its guards pin the other half unchanged: a large computed force still reads
`209670.00 kN`, and an assembled stiffness matrix still factors `10^3` rather than
reaching mega.

Worth remembering as a shape rather than a fact: a rule about *display* was quietly
constraining *input*, and the two are separate tables that happened to be read as one.

### `numeric(expr, unit)` was ignored

Found by auditing `examples/memoria-viga.ipynb` after 0.28.0. The second argument is the
one place in the language where an engineer states the display unit outright; it is
documented, and that notebook uses it.

`convert_quantity` stored the value in exactly the unit asked for, and the renderer then
handed it to the family with `declared=False`, which converted it back. `numeric(M, N*m)`
printed `45.00 kN*m`.

Narrower than "always ignored", which is worth having measured. A requested unit outside
every family survived by accident - `cm` and `inch` are one unit term each, so
`_unit_is_the_engineers` kept them - and only a request the family *also* had an opinion
about was overruled. The notebook's own call names `kN*m`, which is what the family would
have chosen anyway, which is why nobody saw it.

Fixed by #106, and it needed #104 first: honouring `N*m` before compound units kept
their written order would have printed `45000.00 m*N`.

**One mutation was inert and the code went rather than the contract.** A mixed-dimension
matrix cell can never see a requested unit - the engine refuses a target unit
incompatible with any entry, and converting them all to a compatible one makes the matrix
homogeneous - so the branch that passed the flag through was unreachable. Section 6 of
`HOW-THIS-WORK-GOES-WRONG.md` is about exactly that, so the branch is gone and the reason
is in a comment.

### An evaluation with no name on its left

Found by reading `tools/memoria.eng`, this repository's own reference sheet, after
0.28.0 - not by the suite, which was 1697 tests and green. Its moment section rendered:

    M(x)  =  q x L / 2 - q x^2 / 2
             q L^2 / 8                       <- no equals sign, no subject
          =  (10.00 kN/m) (6.00 m)^2 / 8
          =  45.00 kN*m

`q L^2 / 8` is right and hangs there. `_append_assignment_stage` opens a stage with
` & & body` when given no left-hand side, which is what a *wrapped continuation* looks
like everywhere else here, and consecutive statements share one aligned array - so it
landed under the previous statement and read as part of it. Not about `subs`:
`numeric(q*L)` did the same.

#103 puts the expression where a subject goes, so the next stage's `=` attaches to it.
Older than the session that found it: present in 0.27.1 at `a1b9cf5`, from `8b5f95a`.

**The remainder.** A formula too wide to sit beside its own value is not promoted -
`5 k q L^4 / (384 E I)` measures 124 against a budget of 104 - because an identity
column that wide pushes every other row's `=` across the page. Those still open with a
loose row. The reference memoria has none, and the trade was taken deliberately rather
than overlooked; the contract that pins it says so.

**Worth keeping from how it was built.** The mutation harness reported six clean
survivors and had not run pytest at all: one path in its subset named a module that does
not exist, and a run with no summary line reads exactly like a run where nothing failed.
The harness now stops instead. Any harness in this repository should refuse to report a
verdict it did not measure.

### The hunt for guards nobody is checking: engine and parser

Run at last, and with a different question from the usual mutation pass: not "is this
change held up" but "which guards does the suite never even reach". Coverage answers that
in one run where mutation would have taken four hours - 158 `raise` statements at a
hundred seconds each.

    engine.py    87 raises, 39 never executed
    parser.py    71 raises, 25 never executed

Twenty-eight of the sixty-four were then reached deliberately, by typing the mistake each
was written for. **Nothing crashed out of the magic, and every message that appeared was
a sentence that helps.** That is worth recording as a result rather than as an absence.

Two things came out of it.

**A real hole, fixed by #115.** `redefinition conflict` refused a symbolic scalar being
redefined as a function and let a numeric one through, in both directions, because it
checked `self.namespace` and `a := 2*m` stores in `numeric_context.values`. The page then
showed `a = 2.00 m`, `a(x) = x^2` and `a = a` together.

**One message that misdescribes its own guard, not fixed.** `assume takes one comparison
at a time, like assume(L > 0)` guards *chained* comparisons - `assume(0 < L < 10)` - and
`assume(L > 0, b > 0)` is accepted and works. The sentence reads as a limit that is not
there. Cosmetic, and left alone rather than changed without being asked.

**Contracts, by #117.** Seventy-six of them, covering every mistake that could be
reached by typing it. The count of guards the suite never executes went from 63 to 39,
and the parser's from 25 to 9.

**What the last 39 are, measured rather than assumed.** Two kinds, and neither is a gap
a contract would close:

* **Duplicate branches.** The same sentence is raised from more than one place - "narrative
  block cannot be empty" from two, "unbalanced parentheses" from five - so a test can
  reach the message without reaching the line. Two of those pairs are now both covered;
  the rest would need inputs distinguished only by which internal splitter sees them.
* **Defensive branches that the analysis does not need.** `roots`, `extrema`,
  `intersections` and the inequality solver each carry a "could not resolve a safe
  solution set". Fed `sin(1/x)` on a domain that touches its accumulation point, all four
  *resolve* rather than raise. They are there for a case the current analysis has not
  produced.

The engine's thirty are almost all of the second kind, which is why a second battery aimed
squarely at them reached none. Chasing them further would mean constructing inputs to
break an analysis that works, which is a different activity from checking that guards
guard.

**One convention found while looking for a guard, and now pinned.** `solve(x + 2, x)` is
an engineer who forgot `eq(...)`, and the engine reads the expression as `x + 2 = 0` and
answers `-2` rather than refusing it. That helpfulness had no test.

### Re-running the benchmark found one more

The braced frame was re-run against 0.29.0 - the whole sheet, re-rendered, and its
numbers re-checked against the independent NumPy assembly, which still agrees to 2.12e-16
on `k_eq = 70303.22 kN/m`. Everything that had been reported was gone. One thing nobody
had looked at was not.

Its two direction cosines, one line apart:

    c_d =  0.804
    s_d = -0.59

Same brace, same computation, different precision. `_is_reduced` asked
`_significant_figures`, which strips zeros from *both* ends, so `0.80386` rendered `0.80`,
counted as one figure because the trailing zero was discarded, was judged reduced, and
was rescued to three decimals. `0.59489` counted as two and stayed.

A leading zero really does carry nothing; a trailing one is a digit the renderer chose to
print. `_magnitude_text` already counted them that way and carried a comment saying
`_significant_figures` strips both ends because it asks a different question - which it
does, the band question, where a trailing zero genuinely carries nothing. The rescue had
kept the wrong one. Fixed by #113.

**Worth keeping about how it was found.** A sweep of the page for every pattern that had
been a defect flagged two more, and both were the sweep's fault: the `GPa` is the
*declared* modulus and the four `0.00 m` are nodal coordinates that really are zero. A
coarse pattern reports work that is not there, which costs less than the opposite but is
still worth saying out loud.

### The digits are a floor now, not a single page-wide count

`precision` counts decimal places, which is also what Mathcad's Display Precision and
handcalcs' `display_precision` mean. One count cannot serve a sheet spanning seven orders
of magnitude: the braced-frame benchmark printed `T = 0.02 s` for a 0.016756 s period and
`0.00` for two of its section properties, and `precision=6` would have printed
`517195.945000` for a column stiffness.

`figures` (default 3) is a floor underneath it, added in #100. It fires only where the
page's decimals have reduced a value to a single digit or none - which is the reported
defect, `0.02` and `0.00` - and never removes a digit from a large value. The whole
benchmark page moved by three bytes: `0.02 s` became `0.0168 s` and nothing else changed.

Two deliberate departures from the prior art, both measured rather than assumed:

- siunitx, handcalcs, Mathcad and NumPy all *replace* decimals with significant figures.
  At four figures that rounds `70303.22` to `70300`. This only ever adds decimals,
  because the engineer asked for more digits on the small values and never for fewer on
  the large ones.
- They apply to every number. This applies only to the reduced ones, which is what kept
  `0.88`, `2.85` and every formula coefficient exactly where they were.

`docs/project-context/HOW-OTHERS-FORMAT-NUMBERS.md` has the survey this came from,
including the measurement that matters most: **the standard auto-prefix algorithm, which
Pint's `to_compact()` and forallpeople both implement, produces four of the six display
defects reported against this benchmark.** `16.756 ms` for a period, `70.303 MN/m` for a
stiffness, `2278125000.000 mm⁴`, and `-405.4 1/km` for a condensation coefficient. That
is why "do it the way the well-known libraries do" is not available as an answer here.

### RC-3 — preservation of intermediate formulas: done, as `keep`

The last of the four external findings, and the only one that was not a bug. `keep d = ...`
marks a name a later formula shows instead of expanding, so a capacity reads
`phi As fy (d - a/2)` rather than in `cover`, `db_st`, `h`, `b` and `fc`.

The four questions this note asked, answered:

**What makes a name a barrier** — a declaration keyword, `keep`, alongside `case` and
`combo`. Opt-in, and measured rather than argued: making every definition a barrier is
the semantics anyone would expect and moves **24 of the 131** tests shaped like memorias,
including all eighteen worked exercises and the hyperstatic validation case.

**What the substitution stage shows** — the name's own value. `keep` gives the name a
number of its own so the numeric layer substitutes `440.00 mm` instead of expanding the
formula again.

**Does the barrier survive further algebra** — it never enters it. `namespace` holds the
expanded expression and everything computes with that; the written form is only ever
displayed. This is `combo`'s answer, and it is why an opt-in barrier does not divide the
language in two.

**How it interacts with `report`, `summary` and `governing`** — they re-render stored
expressions, and stored expressions are unchanged. `numeric` and `report` share one
branch, so a reported value shows the kept formula too.

Three pieces, and the third was not foreseen here: the written form holds the name; `keep`
gives it a value so the substitution stage shows it; and the *numeric* layer had to be
told not to expand it — `_resolve_symbolic_names` replaced every free symbol the symbolic
namespace defined, before values were consulted. The kept names are shared by reference
the way the symbolic namespace already was, so nothing that does not use `keep` changes.

**One rough edge is left, and it is not `keep`'s.** A substitution wide enough to wrap is
split into additive terms by the wrapping path, so `phi*As*fy*(d - a/2)` shows its numbers
spread over two lines instead of inside the brackets. A wide formula with no kept name
does the same, and a narrow one keeps its shape either way. Whoever takes it should start
at `_bounded_expression_rows` and `_adaptive_additive_rows`, and should know that width is
load-bearing in that path: it is the same mechanism that made #88 decline a written form.

### RC-1 — imperial units: done, and what it turned up

`kip`, `ksi`, `psi`, `inch` and `ft` are in `_UNIT_ALIASES`, `in` says what to write
instead of `invalid syntax`, and the family table is chosen by the system the value is
already in. Pint knew every one of the names, so none of them is a definition.

It was not half an hour, and the reason is worth keeping: the aliases alone leave the
page mixing systems. Everything declared survives, and so does every computed unit no
more complex than its family's canonical member — `kip`, `ft·kip`, `in`. The exception is
the shape RC-2B was: `phi*As*fy*z` carries `in³·ksi`, four unit terms against two, so the
family is consulted and the family had only `kN·m` in it. An all-imperial page printed
its capacity in kilonewton-metres.

Three things came out of rendering that page and reading it, none of them imperial.

**A declared unit that was never declared — done.** `declared` asked whether the
statement used `:=`; it now asks whether the right-hand side names a unit, read with the
precedence the arithmetic uses. Three rows the README presented as current were not
current on that route, and the first of them is in the README's own table:

    d_adm := L/300            0.02 m            the table's "before" column
    phiMn := 0.9*As*fy*z      2.84e8 MPa·mm³    RC-2B, by a second route
    DC    := Mu/(0.9*As*fy*z) 8.79e-7 kN·m/...  RC-2A, for a ratio of 0.88

What made it hard to see is worth keeping: the rows that were right were right by
accident. A declared unit is dropped when it shows *no* figures, so `v := 8e-05*m` and a
deflection carrying `kN·m³/(GPa·mm⁴)` fell into their families because their magnitudes
round to `0.00`. `MPa·mm³` keeps four, so it stayed. Whether the page was right depended
on where the decimal point fell.

**An equation is written twice — done.** It was a defect, and the answer to "same as
v0.23.2 or deliberate?" turned out to be neither: the same page problem, and a different
rule. v0.23.2 asked whether the argument was a name already bound; copying that would
also strip the formula from an evaluation written some way below its definition, where
that row is the only thing saying which formula is being evaluated. The test is now that
the block's opening row is, character for character, the row immediately above it -
which says exactly what is wrong and cannot reach anything else.

A page-level contract came out of it and is worth reusing: no two consecutive rows on
the reference memoria are identical. It is what found the two nothing else could see.

**The factors of a compound unit are ordered alphabetically.** Pint's ordering, applied by
`format(units, "~L")` — the single call that typesets every unit in the system. It reads
`ft·kip` where US practice writes kip-ft, and agrees with SI practice only by the accident
that `kilonewton` sorts before `meter`. Ordering a moment force-first is a change to that
one call and therefore to every unit on every page, which is why it is written here rather
than folded into the alias table.

### The hunt for guards nobody is checking

This session ran a deliberate mutation hunt over the presentation core — fifteen guards,
mutated one at a time — after two load-bearing-but-uncontracted guards turned up by
accident while fixing RC-2A and RC-2B. Six survived all 1558 tests. Two of those moved a
real page and now have contracts (#80); one was unreachable and is gone; three are
defence in depth for each other, which is now written down so nobody removes one on the
grounds that it looks free.

**The same lens has not been run on the symbolic engine, the numeric layer, or the
parser.** The method is in `tests/test_uncontracted_presentation_guards.py`; the shape is:

1. mutate one guard at a time, run a fast subset — most die there;
2. run the **full** suite on every survivor, because surviving a subset proves nothing
   (the deflection guard passed the presentation contracts, the matrix renderer *and* the
   eighteen exercise answers);
3. for whatever still survives, build a sheet that reaches the case the guard exists for
   and **diff the rendered page** — four of the six only separated at this step;
4. mutate suspected pairs **together**, because guards that cover each other look free
   one at a time.

Two things worth carrying: line coverage would have reported 100% on all fifteen — they
all execute, every time, and what was missing was discrimination, not execution. And a
harness whose verdict comes from an exit code rather than pytest's own summary line will
lie to you; one did, in this session.

## Things that are stale, and are not lies you should trust

- **`docs/project-context/CURRENT.md`** describes 0.13.0 at `9a9d6e3`. Its *approved
  behaviour* and *evidence hierarchy* sections are still in force; its baseline numbers,
  release history and open-issue list are not. Do not quote its counts.
- **`docs/project-context/feature-gap-map.md`** was measured at 0.10.1 and reached 15/18
  exercises. It is also, by its own measurement, **blind to three of the four defects the
  external trial found** — it asks whether a line runs, not whether the page is right.
- **`gapmap.json`** shares that limitation.

## How this work is run

The failure modes behind these, each with the instance that produced it and the check
that catches it, are in **`docs/project-context/HOW-THIS-WORK-GOES-WRONG.md`**. Read that
one before writing a contract. The short version is that almost everything on this list
exists because something was believed instead of measured.

Constraints that held all session and should keep holding:

- **Never merge without the user saying so**, and not before CI is green on the exact
  SHA. One merge in this session went in on pending checks because `gh pr merge --auto`
  is not enabled on this repository and `gh` merged directly instead. It happened to be
  green. Check first, then merge.
- **One defect per pull request.** When two touch the same function, stack the second
  locally and rebase it onto `main` after the first merges — do not rely on GitHub
  retargeting a base branch, and verify the rebased diff contains only the new work.
- **Contracts before the fix**, and they must be RED first. Several in this session
  passed for the wrong reason on their first draft; one asserted `\mathrm{m}` was present
  in a row where `q = 10 kN/m` supplies an upright metre by itself.
- **Mutate every contract set.** Survivors are the point, not a formality: they found a
  redundant guard to delete, a comment that was wrong, an untested threshold and a
  coverage hole that predated the branch.
- **Restore the tree at the start of a mutation harness as well as at the end.** A
  timeout that kills the process group does not run the `finally`, and the next run then
  diagnoses its own damage as a real defect.
- **Look at the rendered page.** `tools/render_memoria.py` drives the real magic and
  writes the HTML a notebook would show. Everything else in this repository checks that a
  LaTeX string contains a substring, and a string that renders as garbage contains all
  the same substrings.
