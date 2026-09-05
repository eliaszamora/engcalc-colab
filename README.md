# engcalc-colab

`engcalc-colab` is a compact engineering-calculation layer for Google Colab and Jupyter. It combines a restricted SymPy-backed symbolic language with a separate Pint-backed numerical context, so the same `%%eng` workflow can preserve formulas, evaluate them with physical units, and plot unit-aware engineering functions without redefining the problem in Python.

Current version: **0.25.1**.


## Help, inside the notebook

A notebook cannot help with this language on its own. `Shift+Tab` reads a Python
object's signature, and `integrate` inside `%%eng` is a name in a restricted grammar
rather than a function object. So the help is a line magic, beside `%eng_reset` and
`%eng_config`:

```python
%eng_help              # every call, with its first form
%eng_help integrate    # the forms, what goes in each slot, and an example
```

Every example in the catalogue is executed by the test suite. A help text that does not
run is worse than none: it teaches a form the language refuses, and the reader blames
their own typing.

`examples/memoria-viga.ipynb` is a worked sheet to open in Colab - installation, help,
reactions, moment law, a diagram, an inequality and a summary. Its cells are executed by
the suite too, in order and against one engine, because cell 5 uses what cell 4 solved.


## US customary units

`kip`, `ksi`, `psi`, `inch` and `ft` are names a sheet may use, so a US code example is
worked in the units it is written in rather than transcribed into SI first - a step that
is work the engineer should not have to do, and one where a transcription error would be
invisible in the memoria.

```text
%%eng
L := 20*ft
b := 12*inch
d := 21.5*inch
fc := 4*ksi
fy := 60*ksi
As := 3.16*inch**2
wu := 3.5*kip/ft
phi := 0.9

Ru := wu*L/2
Mu := wu*L**2/8

a := As*fy/(0.85*fc*b)
z = d - a/2
phiMn = phi*As*fy*z
numeric(phiMn)
```

reads `35.00 kip`, `175.00 ft·kip`, `4.65 in` and `272.69 ft·kip`.

Write `inch`, not `in`. `in` is a Python keyword and can never be a name here; typing it
now says so and says what to write instead, where before it said only `invalid syntax`.

The unit a value is shown in is chosen inside the system the value is already in. This
matters in one place, and it is the place a capacity lands: `phi*As*fy*z` comes out
carrying `in³·ksi`, which is the algebra's unit and not one anybody writes, so it is
replaced by the moment family - `kip·ft` on an imperial sheet, `kN·m` on an SI one.
Everything else on the page survives without help, because a declared unit is kept and a
computed `kip`, `ft·kip` or `in` is no more complex than its family's own unit. A value
whose units mix the two systems is shown in US customary: mixing them was a choice, and
converting the imperial half of a deliberately imperial page is the worse answer.

One thing this does not do. The factors of a compound unit are ordered by Pint, which
sorts them alphabetically - `ft·kip`, where US practice writes kip-ft. It agrees with
practice in SI by coincidence, `kilonewton` sorting before `meter`. Changing it means
changing the single call that typesets every unit in the system, so it is recorded in
`docs/project-context/NEXT.md` rather than done here.


## v0.25.1 what the first outside reader saw

Someone was handed the repository link, installed the package and worked a reinforced-
concrete beam from an ACI 318-14 example without reading `src/`. The engineering came out
right - reactions, flexural capacity and shear design all matched an independent hand
check. What did not was the page.

**A name keeps every letter that was typed.** `Mu` printed as `M`. SymPy's translation
table collapses fourteen capital Greek names onto Latin letters, and the guard deciding
whether a rendering may be trusted accepted anything that began with a backslash. A
memoria that quietly drops a subscript is worse than one that refuses to render.

**A dimensionless ratio prints as a number.** A demand-capacity check came out as
`9.63 x 10^-7 kN*m/(MPa*mm^3)` - the units the algebra left behind, carried by a quantity
that by definition has none.

**A moment prints in a moment's units.** `phiMn`, computed from a stress and a volume,
printed as `2.84 x 10^8 MPa*mm^3`. The unit-family table was keyed on a string whose
ordering depended on what the session had already computed, so the same quantity could
find its family or miss it depending on the order the cells were run in.

**A coefficient is as long as the page's precision.** `0.588235294117647` appeared inside
a formula. SymPy prints a Float at full binary precision, and nothing said that a number
written into a formula obeys the same precision setting as a number written into a
result.

All four were found by rendering a memoria and reading it, with
`python tools/render_memoria.py`. The suite was 1387 tests at the time and saw none of
them - each defect produces a LaTeX string containing all the right substrings.

A fifth, found the same way: **a unit left in a substitution reads as a unit.**
`subs(M(x), x, 3*m)` substitutes symbolically, so the metre stays in the expression as an
ordinary free symbol and was typeset in italic between `3` and `q`, exactly where a
variable would sit. The arithmetic was always right; the typesetting said something
false. Only `m`, `N` and `s` could show it - a multi-letter unit like `kN` is upright
already.

Also in this release: EngCalc declared `ipython>=8.18`, so installing it in Colab
upgraded IPython out from under the platform this package exists for. The floor is now
7.34.0, Colab's own pin, and a CI job runs the whole suite against it.


## v0.24.0 one name for one operation

`integral(...)` is retired. `integrate(...)` has been the name since 0.11.0, and the old
one was kept as a permanent alias for memorias written before the rename. There turned
out to be none - EngCalc had never been run in a notebook by anyone - so the reason for
carrying two names for one operation was void.

Typing the old name says what to write instead, because it is still in the version notes
above and in the design history, where somebody can read it:

```text
'integral' was renamed to 'integrate'; write integrate(...) instead
```

Retiring it also hands the name back: `integral := 5*kN*m` is now an ordinary quantity a
sheet may define, which a reserved-but-broken name would not allow.


## v0.25.0 load cases and combinations

```text
%%eng
M_D(x) = qD*x*(L-x)/2
M_Lv(x) = qL*x*(L-x)/2

case D = M_D(x)
case Lv = M_Lv(x)

combo U1 = 1.2*D + 1.6*Lv
combo U2 = 1.4*D

governing(U1(x), U2(x), x, 0, L)
```

```text
U1(x) = 1.2 D(x) + 1.6 Lv(x)
U2(x) = 1.4 D(x)
```

**A combination keeps the factors it was written with.** Written as an ordinary
definition, `U1(x) = 1.2*M_D(x) + 1.6*M_Lv(x)` renders as
`0.6*qD*x*(L - x) + 0.8*qL*x*(L - x)`, because 1.2/2 is 0.6. The number is right and the
load combination is gone: a reviewer checking 1.2 and 1.6 against the code that requires
them cannot, because the page no longer contains them.

A case and a combination are both functions of the member coordinate, so `plot`,
`governing`, `envelope` and `numeric` take them without knowing what they are. The
variable is found rather than declared - everything else in a load case has a value, and
what is left is the coordinate.

This was deferred twice as sugar over plain functions, and the measurement that changed
that is above: it is not the naming, it is that the factors survive.


## v0.23.3 three things the page showed

**A magnitude outside the readable band goes to scientific notation, at both ends.**
`I_z := 80e6*mm**4` printed as `80000000.00 mm^4` - eight zeros nobody writes or counts.
It is now `8.00 x 10^7 mm^4`, in the unit the engineer declared. The floor case has been
handled since 0.10.0; this is the same failure from the other side, where every digit
survives and none can be read. The threshold is a million rather than a hundred thousand
because `200000 MPa` is how a steel modulus is written.

**A multi-letter name is upright.** `eqFy` in italic is spaced by MathJax as a product,
so the reactions block read `e q F y`. Italic is for a quantity, which is a single
letter; a name of several letters is a label. Only the base is touched, and only when
SymPy has not already recognised it, so `theta` stays a theta and `d_{max}` is untouched.

**A power of ten uses a cross, not a dot.** A wrapped product marks its continuation with
`\cdot`. Once large magnitudes started rendering in scientific notation, that line read
`\cdot 1/(8.00 \cdot 10^7 mm^4)` - the same mark carrying two meanings four characters
apart. The cross is the conventional notation anyway.

All three were found by rendering a memoria and reading it, with
`python tools/render_memoria.py memoria-preview.html`. None could have been found by
asserting that a LaTeX string contains a substring, which is what every other check here
does: all three produce strings with the right substrings in them.


## v0.23.2 an equation is written once

A statics sheet printed every equation twice - once where it was defined, once as the
solve's echo of it:

```text
%%eng
eqFy = eq(R_A + R_B, q*L)
eqMA = eq(R_B*L, q*L*L/2)
solve(eqFy, eqMA, R_A, R_B)
```

```text
eqFy   =   R_A + R_B = qL
eqMA   =   L R_B = qL^2/2
R_A    =   qL/2
R_B    =   qL/2
```

An equation passed by name is already on the page under that name, so the solve leaves
it there. Written inline it exists nowhere else, so it is shown:

```text
solve(eq(R_A + R_B, q*L), eq(R_B*L, q*L*L/2), R_A, R_B)
```

still prints both equations before the reactions.

The rule is not "the argument is a name". `solve(delta_B, R_B_aux)` names an
*expression*, and the line displays `delta_B = 0` with the integral evaluated - the
equality is new, and dropping it would hide the equation being solved in a flexibility
calculation. Only a name already bound to an equation is a genuine repeat.

The duplication was invisible until 0.23.1 aligned the block; the malformed array had
been hiding it.


## v0.23.1 what the notebook actually shows

Three merged features produced broken output in a real notebook, and every contract
passed the whole time:

- `solve(M(x) > 20*kN*m, x, 0, L)` raised `AttributeError` and killed the cell (0.23.0);
- `governing(...)` and `summary()` had their finished HTML embedded inside a LaTeX array,
  so the reader saw `\[\hspace{0.2em}\begin{array}{lcl}` as literal text beside the
  values (0.19.0 and 0.20.0, in every release since).

None was found by a test. All three were found the first time the product was rendered
and looked at, which had never happened: every check asserted that a LaTeX string
contained a substring, and a string that renders as garbage contains the same substrings.

The magic now routes on the `CharacteristicResult` and `HtmlBlockResult` unions in the
renderer rather than on type tuples written out by hand, so a result type added to a
union is routed without anyone remembering to.

The summary also disagreed with the working above it: `d = L/300` printed `20.00 mm` in
the derivation and `0.02 m` in the summary, and the names were plain text where the
working used mathematics. A reported value is a computed one, so it now renders exactly
as `numeric(...)` renders it.

`python tools/render_memoria.py memoria-preview.html` writes the page. Open it and look
at it - that is what it is for.


## v0.23.0 solving an inequality

Where on the beam does the moment exceed its limit?

```text
%%eng
L := 6*m
q := 10*kN/m
M(x) = q*x*(L-x)/2
solve(M(x) > 20*kN*m, x, 0, L)
```

```text
Where x satisfies the inequality
Domain: 0.00 m to 6.00 m
x in (0.76 m, 5.24 m)
```

The answer to an inequality is a region, so several come back when there are several:
`solve(M(x) < 20*kN*m, x, 0, L)` gives `[0 m, 0.76 m)` and `(5.24 m, 6 m]`. A strict
comparison opens the boundary and a non-strict one closes it, because the boundary is
where the two sides are equal. The ends of the domain stay closed: they are bounds you
wrote, not roots.

**The domain is required, and that departs from what a CAS does** - TI-Nspire and
Mathematica both answer `x^2 - 6x + 4 < 0` with no domain at all. The reason is units.
Without bounds the variable has none, and "between 0.76 and 5.24" is not an engineering
answer. For a beam it is also simply the beam.

Underneath, the boundaries are the roots of `lhs - rhs`, so this is `roots(...)` with a
sign test rather than a second solver. SymPy cannot take the problem directly:
`q*x*(L - x)/2 > 20*kN*m` raises NotImplementedError, because q, L, kN and m are unsigned
free symbols. What makes it answerable is the `:=` lines above it.


## v0.22.0 numeric reads a unit as a unit

A unit is an ordinary free symbol in the symbolic layer, so `M = 5*kN` stores an
expression containing `kN`. Asking for its number used to refuse:

```text
requires values for: kN. Define the missing numeric values first,
for example: kN := <value>*<unit>
```

Advice nobody should follow. Meanwhile `sigma := N/A` on the same sheet resolved `N` to
newtons without complaint, because the numeric assignment path has read undefined unit
aliases as units since the beginning. The two paths disagreed, and that was the defect.
They agree now, on both the scalar and the matrix path:

```text
%%eng
M = 5*kN
numeric(M)          ->  5.00 kN
Fv = [3*kN; 4*kN]
numeric(Fv)         ->  [3.00; 4.00] kN
```

A unit resolves for the arithmetic and stays out of the substitution stage - nobody
writes "kN = 1 kN" under their working - so it is printed as itself. A value defined
with `:=` always beats the unit of the same name: on a sheet that says `m := 4.0`,
`2*m` is 8, not two metres. And a name that is not a unit is still reported missing,
which is the diagnostic that mattered most to keep.

This closes E14 of the gap map, Euler buckling, which now runs end to end.

**One hazard is pinned rather than hidden.** `N`, `m` and `s` are unit aliases and also
perfectly ordinary variable names. A sheet that writes `sigma = N/A` meaning axial force
and never defines `N` is told, quietly, that sigma is one newton per unit area. `:=` has
always behaved this way; making the paths agree puts it in one place instead of two. It
has a contract of its own so that the day EngCalc warns about it, the decision is visible
rather than accidental.


## v0.21.0 assume decides between several answers

Euler buckling is even in the length, so solving it for L returns a symmetric pair:

```text
%%eng
E := 200*GPa
I := 40e6*mm**4
K := 1.0
assume(Lk > 0)
P_cr(Lk) = pi^2*E*I/(K*Lk)^2
L_max = solve(eq(P_cr(Lk), 500*kN), Lk)
```

`assume(Lk > 0)` now settles it, and `L_max` becomes a single value the sheet can go on
to use. The line shows what was ruled out and why:

```text
discarded by Lk > 0:  -sqrt(5)*pi*sqrt(E*I/kN)/(50*K)
```

An engineer given one answer has no way to know two were found, and the difference
between "there was one" and "I ruled one out" is the difference between arithmetic and
a decision. So the discard is on the page, with the root itself rather than a count.

The assumption had always reached the unknown's symbol; what it could not do is decide
the sign of `pi*sqrt(E*I/kN)/K`, where every symbol is unsigned. SymPy keeps both roots
there and is right to. What settles it is the `:=` lines above - which is exactly what
an engineer reads off their own page when they cross out the negative root.

Three rules keep this from becoming a solver that quietly loses answers:

- without `assume`, nothing is discarded, however obvious the sign looks;
- an answer that cannot be evaluated survives, and so does a complex one: an imaginary
  root is not refuted by "the unknown is positive", it is unaddressed;
- if every answer would go, none does. An assumption that rules out the whole solution
  set is a statement about the problem, and emptying the result would hide it.


## v0.20.0 report and summary

In a memoria of sixty lines the four numbers that matter are scattered among the working.
`report(...)` marks one; `summary()` collects them:

```text
%%eng
L := 6*m
q := 10*kN/m
M_max = q*L^2/8
report(M_max)
R_A = q*L/2
report(R_A)
summary()
```

`report(M_max)` shows the value exactly where it is written, as `numeric(...)` does, and
records it. `summary()` prints what was recorded, in the order it was first marked.

Reporting the same name twice replaces its row in place: a recomputed result is the same
result, not a second row, and a correction belongs where the reader expects it.

This is the code helping rather than the code checking. It computes nothing new and
judges nothing; it saves the reader from scrolling. `result(...)` keeps its own meaning -
formula and final value, without the substitution stage - because which value belongs in
the summary is a different question from how it is shown.


## v0.19.0 governing intervals

`governing(...)` reports which response is largest on which stretch of the span:

```text
%%eng
L := 6*m
w := 28.8*kN/m
P := 40*kN
M_U1(x) = w*x*(L-x)/2
M_U2(x) = P*x
governing(M_U1(x), M_U2(x), x, 0, L)
```

```text
0 m      to 3.22 m   M_U1(x)
3.22 m   to 6 m      M_U2(x)
```

Any number of responses, then the variable and the bounds - the same shape as
`envelope(...)`.

**The boundaries are exact, not sampled.** `envelope(...)` already records which series
is largest at each of its 201 points, and reading that back would have put every boundary
on a 30 mm grid for a 6 m span. `governing(...)` equates the responses pairwise instead
and uses the existing exact-first `intersections` machinery, so the crossover above is
`L - 2P/w` and the boundary is right to the last digit.

A crossover where the governing response does not change is not a boundary: adjacent
stretches with the same winner are one interval.


## v0.18.0 numeric resolves names defined later

A definition captures its free symbols, so a deflection written before its integration
constants are known keeps them:

```text
theta(x) = integrate(M(x)/(E*I_z), x) + C1
v(x) = integrate(theta(x), x) + C2
solve(eq(subs(v(x), x, 0), 0), eq(subs(v(x), x, L), 0), C1, C2)
numeric(subs(v(x), x, L/2))
```

Until now the last line could not produce a number: `numeric(...)` looked only at values
given with `:=`, not at names the symbolic sheet had defined. It now follows those too,
so **the elastic curve is derived and evaluated from scratch** - the midspan deflection
comes out as `-5qL⁴/(384 E I)` to the last digit.

Chains are followed, and a name defined in terms of itself is reported as a missing value
rather than looping.


## v0.17.0 multi-substitution and assumptions

`subs(expr, v1, a1, v2, a2, ...)` replaces several variables at once. The
three-argument form is the one-pair case of the same rule and is unchanged.

```text
numeric(subs(M(x, b), x, L/2, b, c))
```

The replacements are **simultaneous**, so `subs(x + y, x, y, y, 2)` is `y + 2` and not
`4`: writing both on one line means they happen together.

`assume(L > 0, E > 0)` tells the engine what you already know. It matters:
`simplify(sqrt(L^2))` is `Abs(L)` for a merely real `L` and `L` for a positive one.

**Assumptions must come before the symbol is used**, and stating one late is refused
rather than ignored. A SymPy symbol carries its assumptions in its identity, so a late
assumption would apply to a symbol nothing references and change nothing at all,
silently. Comparisons against zero only: `L > 5` is not something a symbol can carry.

Comparisons remain allowed in the places that already took them - `piecewise(...)` and
now `assume(...)` - rather than becoming general expressions.


## v0.16.0 summations evaluate

`sum(expr, i, lower, upper)` already built the right thing and already rendered as a real
sigma. What it could not do was become a number:

```text
%%eng
n := 5
P := 10*kN
S = sum(P*i, i, 1, n)
numeric(S)
```

`numeric(S)` now gives `150.00 kN`, and `S` still shows as a sigma in the memoria.

**No second function was added.** A `summation()` alongside `sum()` would invent a second
name for one operation and break the pattern the whole language runs on: the symbolic
layer keeps the formula and `numeric(...)` produces the value, exactly as `M(x)` stays
symbolic while `numeric(M(x))` gives a number.

Summation bounds must be dimensionless. Reversed bounds follow SymPy's convention, so
`sum(i, i, 3, 1)` is `-2` whether or not the terms carry units.


## v0.15.0 Macaulay brackets

`<x-a>^n` is the singularity function of Hibbeler and Beer: zero before `a`, and
`(x-a)^n` from there on. A beam becomes one expression with **one term per load**:

```text
%%eng
L := 8*m
q := 12*kN/m
P := 40*kN
a := 3*m
R_A = q*L/2 + P*(L-a)/L
M(x) = R_A*x - q/2*<x>^2 - P*<x-a>^1
plot(M(x), x, 0, L)
```

The same beam as a Piecewise needs a branch per load, and every branch repeats the one
before it. Adding a load here adds a summand.

Brackets integrate term by term, so the double-integration method chains directly:

```text
theta(x) = integrate(M(x)/(E*I_z), x) + C1
v(x) = integrate(theta(x), x) + C2
```

The exponent must be written: `<x-a>^1`, not `<x-a>`. The bracket shifts its variable and
does not scale it, so `<2*x-a>` is refused rather than guessed at.

`<` and `>` remain comparison operators inside `piecewise(...)`; the bracket notation is
recognised only when a `>` is immediately followed by `^` and an integer, which no
comparison ever is.


## v0.14.0 solve shows every solution

An equation with more than one answer no longer raises. All of them are shown:

```text
%%eng
solve(x^2 - 5*x + 6, x)
```

```text
x² - 5x + 6 = 0
x = 2
x = 3
```

The statement **defines nothing**, because there is no single value to assign. Binding one
would quietly pick the last, and the next line would use it without anyone knowing a
choice had been made.

When what you want is the physically admissible root, `roots(...)` is the tool and always
was: it selects inside a domain, with units. The error you get from assigning a
multi-solution `solve` says so.

Complex roots do not appear, and not because this path discards them: engine symbols are
declared real, so `solve(x^3 - 1, x)` returns `1` and SymPy never offers the complex pair.


## v0.13.0 indefinite integral

`integrate(expr, var)` returns the antiderivative. Together with scalar equation systems
this derives an elastic curve from scratch instead of quoting it:

```text
%%eng
L := 6*m
q := 10*kN/m
E := 200*GPa
I_z := 80e6*mm**4
R_A = q*L/2
V(x) = R_A - q*x
M(x) = integrate(V(x), x, 0, x)
theta(x) = integrate(M(x)/(E*I_z), x) + C1
v(x) = integrate(theta(x), x) + C2
solve(eq(subs(v(x), x, 0), 0), eq(subs(v(x), x, L), 0), C1, C2)
```

which gives the textbook constants, `C2 = 0` and `C1 = -qL³/(24 E I_z)`.

**No constant of integration is invented.** You write the one you need, which is what you
do on paper and avoids EngCalc naming symbols nobody asked for. `C1` is an ordinary free
symbol and the boundary conditions determine it.

Two arguments or four: two for the indefinite form, four for the definite one. Three
almost always means a bound was forgotten, and the message says so.


## v0.12.0 scalar equation systems

Statics as it is actually written — sum the forces, sum the moments, solve for the
reactions:

```text
%%eng
L := 6*m
q := 10*kN/m
eqFy = eq(R_A + R_B, q*L)
eqMA = eq(R_B*L, q*L*L/2)
solve(eqFy, eqMA, R_A, R_B)
```

The memoria shows both equations and then each unknown on its own labelled line, and
`R_A` and `R_B` are defined from there on, so `V(x) = R_A - q*x` just works.

The same shape determines the constants of an elastic curve from its boundary
conditions:

```text
solve(bc1, bc2, C1, C2)
```

**n equations followed by n unknowns**, so the argument count is even; `solve(eq, x)` is
the n = 1 case and is unchanged. The unknowns are named in the call and the results come
back labelled, which is what SymPy, Mathematica, Maxima, TI-Nspire and Mathcad all do.
Positional destructuring was deliberately not adopted: `R_B, R_A = solve(eq1, eq2, R_A,
R_B)` would cross the values with nothing to catch it.

One thing worth knowing: an equation stored in a variable is built when that line runs,
so a name that already carries a value is substituted into it there. Name your unknowns
before giving them values, which is what you would do on paper anyway.


## v0.10.0 engineering presentation

EngCalc 0.10.0 changes how numbers reach the page. Nothing about how they are computed
changes, and no result moves; what changes is that the rendered memoria no longer
contradicts the values behind it.

A quantity is shown in a unit an engineer would write. The unit you declare is the unit
you see: `q := 2.8*tonf/m` renders in `tonf/m`, and a 5 m span stays `5.00 m`. A unit that
only the algebra produced is replaced by one of its own dimension — a deflection that
evaluates to `kN/(GPa·m)` is a length, and is shown as `5.63 mm`.

A declared unit is left alone unless it would misrepresent the value, measured by the
significant figures that survive at the active precision:

| source | before | now |
|---|---|---|
| `v := 8e-05*m` | `0.00 m` | `0.08 mm` |
| `k = 2*v`, `numeric(k)` | `2(0.00 m) = 0.00 m` | `2(0.08 mm) = 0.16 mm` |
| a deflection `P·L³/(48·E·I_z)` | `5625.00 kN/(GPa·m)` | `5.63 mm` |
| an admissible deflection `L/300` | `0.02 m` | `16.67 mm` |

Where two family units are both plausible, the one that puts the magnitude in a readable
range wins, so a deflection and the admissible limit it is compared against are shown in
the same unit. A span stays in metres; a deflection moves to millimetres.
| a table column of small values | every cell `0.00` | `0.00 0.08 0.16 0.24` in mm |

Tables and matrices choose one unit for the whole column or matrix, because the unit is
printed once in the header or outside the brackets; cells are never rescaled
individually.

Below the point where no unit of the family retains a figure, the value is shown in
scientific notation in the unit you declared: `1e-6 m` reads `1.00 · 10⁻⁶ m`.
`zero_tolerance` is unchanged and still decides what counts as a genuine zero — evaluated
against the value as you stored it, so a change of display unit can never turn a zero
into a number.


## v0.9.2 reliability work

EngCalc 0.9.2 hardens exact characteristic analysis and packages the completed audit-remediation reliability work as the current release. Characteristic solving remains exact-first; when exact discovery is incomplete, EngCalc supplements it with a deterministic numerical fallback instead of silently returning an empty result. Engine-created engineering symbols are explicitly real, and accepted exact candidates keep exact provenance when exact and numerical candidates coincide.

Previously fragile transcendental and non-elementary cases are covered end to end with normal EngCalc syntax:

```text
roots(log(x)-1, x, 1, 10)
roots(exp(x)-3*x, x, 0, 3)
roots(x^5-x-1, x, 0, 2)
intersections(log(x), 1+0*x, x, 1, 10)
extrema(abs(x-2), x, 0, 4)
```

Natural unit-literal bounds use the same engineering grammar as plots and tables; no Python-qualified unit syntax is required:

```text
L := 6*m
V(x) = x-L/2
roots(V(x), x, 0*m, 6000*mm)
```

Continuous Piecewise boundaries preserve the selected governing branch and collapse equivalent left/at/right records to the physical `at` value, while real discontinuities retain meaningful one-sided values:

```text
a := 3*m
L := 6*m
f(x) = piecewise(x-a, x < a, 2*(x-a))
extrema(f(x), x, 0*m, L)
```

Ordinary plots keep exact characteristic coordinates and annotation identity independently of their 201-point drawing grid. The characteristic solver is now split internally by responsibility under `engcalc_colab.characteristics` while its public imports remain stable. IPython is a declared runtime dependency, and permanent CI validates the advertised Python 3.10–3.14 range.

`envelope(...)` deliberately remains sampled in 0.9.2. Exact envelope crossovers and governing intervals are planned for **0.9.3**.

## v0.9.1 Exact characteristic analysis

EngCalc 0.9.1 adds exact-first engineering characteristic analysis with three standalone calls:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

In 0.9.1 these calls are **standalone statements**: do not assign them to another symbol and do not nest them inside `numeric(...)`, `table(...)`, or another expression. Exact symbolic solutions are preferred. When exact solving is unresolved, EngCalc uses its deterministic numerical fallback and rendered locations use `≈` rather than `=`.

### 1. Beam-like moment extrema

```text
L := 6*m
q := 12*kN/m
M(x) = q*x*(L-x)/2

extrema(M(x), x, 0, L)
```

For this beam-like parabola, the authoritative maximum is obtained from the characteristic solver rather than from a plotting grid: `x = L/2 = 3 m`, with `M = 54 kN·m`.

### 2. Shear roots

```text
V(x) = q*(L/2-x)

roots(V(x), x, 0, L)
```

The zero-shear location is reported exactly at `x = L/2 = 3 m`. Closed-domain endpoints are included when they are roots.

### 3. Response-case intersections

```text
M2(x) = q*x*(L-x)/3

intersections(M(x), M2(x), x, 0, L)
```

Intersections solve the response difference while preserving the common response value and physical units. In this example the curves meet at `x = 0 m` and `x = 6 m`.

### 4. Piecewise jump is not a false root

```text
J(x) = piecewise(-1, x < 2, 1)

roots(J(x), x, 0, 4)
```

The sign changes across `x = 2`, but the function is never zero there. EngCalc therefore reports no root; it does not bracket across a Piecewise jump and invent a crossing.

### 5. Indexed matrix scalar analysis

```text
K(x) = [x + L, 0; 0, 2*x + L]

roots(K(x)[1,1] - 7*m, x, 0, L)
```

Characteristic analysis is scalar-only, so a whole matrix is rejected. An indexed scalar entry is valid; here the root is `x = 1 m`. Unit literals such as `7*m` are resolved through the same Pint unit registry during physical validation.

### 6. Approximate numerical fallback

```text
roots(cos(x) - x, x, 0, 1)
```

This equation has no elementary closed-form root. EngCalc's deterministic fallback validates the numerical solution near `0.7390851332`; the standalone renderer marks the location with `≈` to distinguish numerical provenance from an exact symbolic result.

Ordinary `plot(...)` series in 0.9.1 can already use exact global-extremum metadata independently of their 201-point drawing grid. Exact envelope crossovers and governing intervals remain intentionally deferred to **0.9.3**; `envelope(...)` keeps its existing sampled governing mathematics through the 0.9.2 reliability work.

## v0.9.0 Matrix/CAS

EngCalc 0.9.0 adds a native Matrix/CAS layer to the same restricted `%%eng` workflow. Matrix literals use mathematical/MATLAB-inspired syntax with mandatory commas between columns and semicolons between rows:

```text
A = [a, b; c, d]
r = [a, b, c]
v = [a; b; c]
```

Matrices use **1-based indexing**, so `A[1, 1]` is the upper-left scalar entry. Row and column vectors additionally accept one-index shorthand. Matrix algebra is exact and SymPy-backed: `A*B` is mathematical matrix multiplication, with constructors and operations such as `identity`, `zeros`, `diag`, `transpose`, `det`, `inv`, `trace`, `rank`, `rref`, `norm`, `size`, `eigenvals` and `eigenvects`. Exact linear systems use `solve(A, b)`.

Numerical evaluation remains Pint-backed. `numeric(A)` evaluates a symbolic matrix cell by cell. Homogeneous matrices can share a compatible display/target unit, while heterogeneous engineering matrices preserve the physical dimensionality of each entry instead of inventing one matrix-wide unit. Matrix-valued functions, Piecewise scalar cells and exact `solve(A, b)` results can all flow into `numeric(...)`.

Existing engineering table/plot APIs remain scalar-response APIs by design. An indexed matrix entry such as `K(x)[1, 1]` may be used in `table(...)`, `plot(...)` or `envelope(...)`; **whole-matrix** responses are rejected with a concise scalar-response diagnostic. Whole-matrix tables, plots and envelopes are outside the 0.9.0 core scope.

## Install in Google Colab

Colab pins `ipython==7.34.0`, and EngCalc's floor is that same version rather than the
newest release. A higher floor makes the install upgrade IPython underneath the platform,
which pip reports as a conflict with `google-colab`. Nothing here needs a newer one, and
CI runs the whole suite against 7.34.0 so the claim keeps being checked.


```python
%pip install -q --upgrade --no-cache-dir git+https://github.com/eliaszamora/engcalc-colab.git
%load_ext engcalc_colab
```

If the extension is already loaded after an update, use:

```python
%reload_ext engcalc_colab
```

## v0.8.0 Piecewise expressions

EngCalc 0.8.0 adds restricted, unit-aware Piecewise expressions for engineering response laws. The primary form is:

```text
q1 := 8*kN/m
q2 := 4*kN/m
a := 3*m
L := 6*m
q(x) = piecewise(q1, x < a, q2, x <= L, 0)
```

Every `piecewise(...)` requires ordered `value, condition` pairs followed by a **mandatory default** value. Conditions are intentionally restricted to one direct `<`, `<=`, `>` or `>=` comparison between the Piecewise interval variable and a breakpoint expression. Boolean combinations, chained inequalities and arbitrary condition logic are outside the public 0.8.0 grammar. Source branch order determines ownership at boundaries.

The same definition works through full and partial numerical evaluation:

```text
numeric(q(2*m))
numeric(q(x))
```

Fully numeric calls select the governing branch using Pint-aware comparisons. A partial call retains the interval variable and renders the evaluated Piecewise cases. Exact dimensionless zero branches inherit the compatible dimensional unit of the other branches; incompatible branch or comparison dimensions raise an engineering-facing error.

Tables preserve their existing exact-count contract:

```text
table(q(x), x, 0, L, 21)
```

The example above returns exactly 21 rows. Piecewise does not add hidden table samples. Plotting is different by design: it retains the existing **201-point base grid** and adds any exact, numerically resolvable Piecewise breakpoints that are not already present. Multi-series plots, parameter sweeps and envelopes use the union of their breakpoints on one shared grid. Lines and fills are split at branch transitions, so a discontinuity is never shown with a fictitious connector. Positive structural moment remains plotted downward.

Symbolic calculus continues to delegate to SymPy. `integrate(...)` results containing supported `Piecewise`, `Min` or `Max` structures remain numerically evaluable. `diff(...)` returns branchwise derivatives without introducing a public `DiracDelta`; however, EngCalc treats a derivative as undefined at every explicit Piecewise breakpoint and `numeric(...)` raises a corrective diagnostic exactly at that point, regardless of endpoint ownership. Evaluate the derivative immediately to either side when one-sided values are needed.

### 0.8.0 limitations

The 0.8.0 scope does not add arbitrary boolean Piecewise logic, open/closed endpoint glyphs, `solve(piecewise(...))`, exact Piecewise roots/intersections, exact governing-interval envelopes, arbitrary Python execution, or automatic differentiability proofs. Breakpoints used for plotting must be numerically resolvable from the current EngCalc numerical context.

## v0.7.2 engineering tables

v0.7.2 adds native pointwise engineering tables to the same restricted, unit-aware `%%eng` workflow used for calculations and plots. The normal form uses automatic discretization: give the response, independent variable, start, end, and number of points. Both endpoints are included.

```text
%%eng

M(x) = q*x*(L-x)/2
q := 4*kN/m
L := 5*m

table(M(x), x, 0, L, 21)
```

When `L` already carries a length unit, the exact zero in `0, L` inherits the compatible unit automatically. You therefore do not need to write `0*m`. The example above evaluates 21 uniformly spaced positions from `0 m` through `5 m`.

Several dimensionally compatible responses may share one table and remain in source order:

```text
table(M_D(x), M_L(x), M_U(x), x, 0, L, 21)
```

When particular evaluation positions matter more than uniform discretization, declare their unit once:

```text
table(M(x), x, [0, 1, 1.5, 2], m)
```

Fully explicit compatible quantities remain available when individual points use different units:

```text
table(M(x), x, [0*m, 50*cm, 1*m])
```

Explicit points are normalized to one compatible point unit. Dimensionless tables are also supported, and uniform ranges may be descending, for example `table(V(x), x, L, 0, 21)`.

Inside `%%eng`, tables render as native HTML in source order alongside MathJax equations, headings, and existing plots. Units appear once in the table headers rather than in every cell, and the active `%eng_config` precision and zero tolerance are respected. EngCalc does not add pandas as a runtime dependency for this feature.

General Python list literals remain restricted: list syntax is accepted only in the approved table-point context and the existing plot/envelope sweep contexts. Export/download APIs and Cartesian multi-parameter table sweeps are outside the 0.7.2 scope.

## v0.7.1 multi-argument functions and generalized partial evaluation

v0.7.1 generalizes EngCalc user-defined functions from one positional parameter to any positive number of ordered positional parameters while preserving the existing one-argument syntax. It also generalizes `numeric(...)` so known arguments and known numerical context values can be evaluated with Pint while one or more caller-supplied symbols remain symbolic.

```text
%%eng

M(x) = q*x*(L-x)/2
M_param(x, q) = q*x*(L-x)/2
M_base(x, q, L) = q*x*(L-x)/2
qU(qD, qL) = 1.2*qD + 1.6*qL
M_U(x) = M_base(x, qU(qD, qL), L)
v(x, A, L) = A*sin(pi*x/L)

qD := 10*kN/m
qL := 5*kN/m
L := 4*m
A := 20*mm

numeric(M_base(2*m, qD, L), kN*m)
numeric(M_base(x, qD, L))
numeric(v(x, A, L))
result(M_base(2*m, qD, L), kN*m)
plot(M_U(x), x, 0*m, L)
```

Function calls use exact positional arity. Parameter binding is simultaneous, local parameters shadow same-named symbolic or numerical context values only inside the function call, and redefining a function replaces its previous signature rather than creating an overload. Nested user-defined functions can be passed as arguments, including load-combination forms such as `M_base(x, qU(qD, qL), L)`.

For a partial numerical call such as `numeric(M_base(x, qD, L))`, EngCalc substitutes the known `qD` and `L` quantities while retaining the caller-side name `x` as unresolved. Multiple unresolved caller symbols are supported. Polynomial partials retain the existing evaluated-coefficient presentation when exactly one unresolved polynomial variable remains; non-polynomial partials such as `numeric(v(x, A, L))` render the known substitutions plus the remaining symbolic structure without fabricating a final quantity. Target-unit conversion still requires a fully numerical result.

Multi-argument functions integrate with the existing plotting and envelope APIs. Direct calls such as `plot(M_base(x, qD, L), x, 0*m, L)` and one-variable wrappers such as `M_U(x)` use the existing 201-point sampling grid and existing structural sign conventions.

v0.7.1 intentionally does **not** add default parameter values, keyword arguments, variadic parameters, function overloads by arity, or Cartesian multi-parameter sweeps. Existing single-parameter plot/envelope sweep behavior is unchanged.

## v0.7.0 scalar engineering mathematics

v0.7.0 adds a fixed, restricted scalar-mathematics layer that works symbolically and through the Pint-backed numerical context. The public functions are `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `exp`, and `log`, together with the reserved constant `pi`. These names are built into EngCalc and cannot be redefined as variables or function parameters.

```text
%%eng

f(x) = A*sin(pi*x/L)
A := 10*mm
L := 4*m

theta := sin(30*deg)
r := sqrt(9*m^2)
a := atan(1)

numeric(a, deg)
plot(f(x), x, 0, L)
```

Numerically, `sqrt` propagates units through a power of one half. `sin`, `cos`, and `tan` accept dimensionless values or angle quantities; degree quantities are converted to radians before evaluation. `asin`, `acos`, and `atan` require dimensionless arguments and return radians, so results can be converted explicitly, for example with `numeric(atan(1), deg)`. `exp` and `log` require dimensionless arguments. Incompatible dimensions produce EngCalc evaluation errors rather than silently stripping units.

The same functions are valid inside user-defined functions and native plots. For example, `f(x) = A*sin(pi*x/L)` can be sampled directly with `plot(f(x), x, 0, L)`. Under the pre-0.7.1 partial-evaluation model, `numeric(f(x))` may preserve `x` as unresolved but does not yet construct compact evaluated coefficients for a non-polynomial transcendental expression; generalized partial evaluation is reserved for 0.7.1.

## v0.6.2 numeric ergonomics and diagnostics

v0.6.2 improves the boundary between EngCalc's symbolic functions and its Pint-backed numerical context. A complete numerical/unit expression may now be passed directly as the argument of a user-defined function without introducing an auxiliary numeric symbol first.

```text
M(x) = q*x*(L-x)/2
q := 10*kN/m
L := 6*m

numeric(M(2.5*m))
numeric(M(0*m), kN*m)
numeric(M(L/2))
result(M(2.5*m))
```

Direct quantities such as `2.5*m`, expressions using known numerical values such as `L/2`, load quantities such as `4*tonf/m`, and dimensional zeros such as `0*m` are evaluated from their restricted numeric AST before SymPy simplification can erase unit information. A lone unassigned name remains intentionally symbolic, so `numeric(M(x))` and `result(M(x))` continue to produce partial numerical functions.

`result(...)` uses the same numerical engine as `numeric(...)`, so the direct-function-argument behavior is identical; only the presentation stages differ. Engineering-facing errors now distinguish unknown numerical names, unresolved numerical symbols and incompatible units in evaluated functions, and include a corrective hint when EngCalc can provide one safely.

## v0.6.1 visual polish

v0.6.1 is a presentation-focused release. It does not change the structural mathematics, the 201-point sampling grid, unit handling, signed-envelope rules, magnitude-envelope rules, or the convention of **positive structural moment downward**.

The release refines the notebook output in three related ways:

- **MathJax calculations** remain the single mathematical renderer. Formula, numerical-substitution and final-result stages are kept semantically separate and may wrap over several rows when required by the visual-width budget. Long additive expressions wrap at complete top-level terms rather than splitting mathematical fragments. The final vertical hierarchy is 4 pt for a wrapped continuation of the same mathematical stage, 8 pt between distinct mathematical stages or consecutive source results, and 16 pt when an explicit blank source line precedes the next result.
- **Compact numerical presentation** is available through `result(expr[, target_unit])`, which reuses the existing numerical evaluation path but displays only symbolic formula → final result. `numeric(...)` keeps the detailed formula → substitution → result presentation.
- **Characteristic plot values** are attached to the sampled points they describe using compact coordinate labels such as `(2.5, 3.15)`. Multi-series plots, signed envelopes and magnitude envelopes no longer use a separate characteristic-value panel. Labels contain no duplicated units, boxes or leader lines; their color follows the corresponding series, while placement avoids axes boundaries, the legend, sampled curves and other labels.

For example:

```text
%%eng

M_D(x) = q_D*x*(L-x)/2
M_L(x) = q_L*x*(L-x)/2

q_D := 8*kN/m
q_L := 5*kN/m
L := 6*m

plot(M_D(x), M_L(x), x, 0, L)
envelope(M_D(x), M_L(x), x, 0, L)
```

The curves and envelope are evaluated exactly as before; v0.6.1 changes how their characteristic values are presented.

## Symbolic + numerical workflow

Symbolic definitions use `=`. Numerical data use `:=`. The two contexts are intentionally separate: assigning a numerical value never overwrites the symbolic formula.

```text
%%eng

V_B = 3*q*L/8
V_A = 5*q*L/8
M_A = q*L^2/8

q := 2.8*tonf/m
L := 4*m

numeric(V_B)
numeric(V_A)
numeric(M_A)
```

The symbolic namespace still contains the original formulas. `numeric(...)` evaluates with the current numerical context and renders formula → numerical substitution → final quantity. When the explicit substitution is not useful in the memory, `result(...)` uses the same evaluation but renders formula → final quantity:

```text
result(M_A)
result(M_A, kN*m)
result(M(x))
```

## Numerical context and units

Numeric assignments use:

```text
name := numeric_expression
```

Numerical values may reference earlier values:

```text
q := 2.8*tonf/m
L := 4*m
P := q*L
```

Supported unit aliases include:

- length: `mm`, `cm`, `m`
- force: `N`, `kN`, `kgf`, `tonf`
- pressure/stress: `Pa`, `kPa`, `MPa`, `GPa`
- other: `kg`, `s`, `rad`, `deg`

EngCalc defines:

\[
1\,\mathrm{tonf}=9.80665\,\mathrm{kN}.
\]

Units are interpreted only inside the numerical context. A name such as `m` remains available as a normal symbolic identifier in symbolic expressions.

Numerical quantities render with two decimal places by default. Global presentation settings can change that policy without altering stored values or symbolic formulas.

## Adaptive MathJax rendering

MathJax is the single mathematical renderer for symbolic and numerical calculations. This keeps font metrics, fraction sizing, subscripts and equation scale consistent throughout one engineering memory.

Numerical evaluations keep the calculation stages separate:

```text
formula
= numerical substitution
= final result
```

`result(...)` uses the compact two-stage form:

```text
formula
= final result
```

Formula and substitution stages use adaptive top-level term packing. EngCalc estimates the visual complexity of complete `+` / `-` terms and keeps adding whole terms to the current row while the row stays within a conservative visual budget. If the next term would exceed the budget, that term starts a continuation row.

The renderer applies a semantic vertical hierarchy:

- **4 pt** between rows that are only continuations of the same wrapped mathematical stage;
- **8 pt** between distinct stages of one operation, such as equation → solution in `solve(...)`, formula → substitution → result in `numeric(...)`, or formula → result in `result(...)`;
- **8 pt** between consecutive source results when there is no blank source line;
- **16 pt** when an explicit blank line in `%%eng` precedes the next source result.

A short expression such as:

```text
A + B - C + D
```

remains on one row when it fits. A longer engineering expression can instead be arranged as:

```text
[ long term 1 ] + [ long term 2 ]
- [ long term 3 ]
```

The final numerical result always starts its own semantic stage. The visual budget is a deterministic heuristic rather than a browser-pixel measurement.

## Global numerical presentation settings

Use `%eng_config` to control numerical formatting for later `%%eng` output in the current notebook session:

```python
%eng_config precision=3 zero_tolerance=1e-10
```

Defaults:

```text
precision=2
zero_tolerance=1e-10
```

Run `%eng_config` with no arguments to inspect the active settings.

`precision` accepts integers from 0 through 10 and applies to numerical assignments, substituted values, final `numeric(...)` / `result(...)` results, and evaluated coefficients of partial numerical functions.

`zero_tolerance` is presentation-only. Values whose displayed magnitude is below the threshold render as zero, while the stored Pint quantity remains unchanged.

`%eng_reset` clears symbolic and numerical calculation state but does not change the active render configuration.

## Target-unit conversion

A fully numerical evaluation may request a compatible target unit:

```text
numeric(expression, target_unit)
result(expression, target_unit)
```

Examples:

```text
numeric(M_A, kN*m)
numeric(V_A, kN)
result(M_A, kN*m)
result(V_A, kN)
```

Target-unit expressions may contain products, divisions and powers:

```text
kN*m
N*mm
mm^4
mm/kN
```

The conversion applies to the final result. `numeric(...)` preserves original units in its formula/substitution stages; `result(...)` omits the substitution stage but uses the same converted final quantity. Pint checks dimensional compatibility and rejects incompatible targets.

Target-unit conversion currently requires a fully numerical result. A partial function with a free independent variable should use `numeric(V(x))` or `result(V(x))` without a target unit.

## Evaluated partial numerical functions

When a user-defined function keeps its independent variable free, EngCalc evaluates known polynomial coefficients with Pint instead of stopping after textual substitution.

```text
V(x) = 5*q*L/8 - q*x
q := 2.8*tonf/m
L := 2*m

numeric(V(x))
```

produces a compact numerical function equivalent to:

\[
V(x)=3.50\,\mathrm{tonf}
-2.80\,\frac{\mathrm{tonf}}{\mathrm m}x.
\]

Likewise:

```text
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2
numeric(M(x))
```

with the same data produces a function equivalent to:

\[
M(x)=
-1.40\,\mathrm{tonf\,m}
+3.50\,\mathrm{tonf}\,x
-1.40\,\frac{\mathrm{tonf}}{\mathrm m}x^2.
\]

`result(M(x))` produces the same evaluated coefficient function but omits the explicit numerical-substitution stage. The symbolic definition remains unchanged. Direct expressions remain strict: `numeric(q*x)` and `result(q*x)` do not guess that `x` is an independent variable.

## Function evaluation and dimensional zeros

Fully evaluated user functions keep their engineering label in the rendered memory. Function evaluation is performed with Pint before an exact symbolic zero can erase dimensional information, so a boundary value such as `numeric(M(L))` remains a zero moment rather than a dimensionless zero.

The numerical workflow also supports mixed engineering units:

```text
Delta_B0 = integrate(M_0(x)*M_1(x)/(E*I), x, 0, L)
f_11 = integrate(M_1(x)^2/(E*I), x, 0, L)

E := 200*GPa
I := 8.5e8*mm^4

numeric(Delta_B0)
numeric(f_11)
```

## Native plotting inside `%%eng`

The restricted unit-aware plotting command is:

```text
plot(expression, variable, start, end)
```

The primary workflow is to define engineering functions and numerical data once and plot them in the same cell:

```text
%%eng

V(x) = 5*q*L/8 - q*x
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2

q := 2.8*tonf/m
L := 4*m

numeric(V(x))
numeric(M(x))

plot(V(x), x, 0, L)
plot(M(x), x, 0, L)
```

Each plot samples exactly 201 positions including both endpoints. The plotting variable is locally overridden during sampling, so a previously stored value such as `x := 2.5*m` is neither used to collapse the plot nor modified by plotting.

Plot bounds are unit-aware. The common structural form:

```text
plot(M(x), x, 0, L)
```

works when `L := 4*m`: the exact dimensionless zero is promoted to the compatible dimensional unit of `L`. Incompatible bounds are rejected.

The first evaluated ordinate establishes the y-axis unit and later samples are converted to that common unit. Axes are labeled automatically, for example:

```text
x [m]
M(x) [tonf·m]
```

Structural moment diagrams use **positive moment downward**.

### Multi-series plotting

Several dimensionally compatible functions may share one axis:

```text
plot(M_D(x), M_L(x), x, 0, L)
```

One function may also be swept over several numerical values of one parameter:

```text
plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
```

The sweep accepts exactly one keyword parameter with a non-empty list of complete numerical EngCalc expressions. `[5, 10, 15]*kN/m` is not supported. A sweep and multiple plotted expressions cannot be combined in the same call.

Sweep values are local overrides and do not mutate stored numerical state. All series on a shared y-axis must have compatible dimensions, and a multi-expression comparison cannot mix moment-classified and non-moment-classified responses.

Presentation in v0.6.1:

- a single series uses a line, translucent fill, endpoint/extrema markers and compact `(x, y)` labels at its maximum/minimum characteristic points;
- multiple series use clean lines without overlapping area fills, an automatic legend, restrained extrema markers and compact `(x, y)` labels for each curve;
- coordinate labels have no boxes, leader lines or repeated units; label color follows the corresponding series, and the placement engine avoids axes boundaries, the legend, other labels and sampled curve points.

One `plot(...)` statement creates exactly one Matplotlib figure in source order between surrounding MathJax calculation groups.

## Sampled engineering envelopes

`envelope(...)` reuses the same symbolic functions, numerical state, 201-point sampling grid, unit normalization and structural sign convention as `plot(...)`.

Several compatible responses may be reduced to one upper and one lower signed envelope:

```text
%%eng

M_A(x) = q_A*x*(L-x)/2
M_B(x) = -0.5*q_B*x*(L-x)/2

q_A := 8*kN/m
q_B := 10*kN/m
L := 6*m

envelope(M_A(x), M_B(x), x, 0, L)
```

The final three positional arguments are `variable, start, end`. Every earlier positional argument is a source response. A non-sweep envelope requires at least two response series.

One expression may also be enveloped over a restricted one-parameter sweep:

```text
%%eng

M(x) = q*x*(L-x)/2
L := 6*m

envelope(
    M(x),
    x,
    0,
    L,
    q=[-10*kN/m, 5*kN/m, 15*kN/m]
)
```

At each of the 201 shared sample positions, EngCalc computes the **signed algebraic maximum and signed algebraic minimum** across source series. A negative response can govern the lower envelope while a positive response governs the upper envelope. The governing source-series index is retained internally.

All source responses must be dimensionally compatible. Compatible values are normalized to a common unit before comparison. Mixed moment/non-moment series and incompatible dimensions such as shear versus moment are rejected.

The envelope figure:

- shows original source responses as faint context curves;
- emphasizes the upper and lower envelope boundaries;
- lightly fills the region between signed envelope boundaries;
- keeps the `y = 0` reference visible;
- places compact `(x, y)` labels at the global maximum and minimum governing sampled points without boxes, units or leader lines;
- keeps positive moment downward for moment envelopes.

## Absolute-value / magnitude envelopes

`abs(...)` is a safe, composable symbolic/numerical operation. Applying it to every source of an envelope requests a nonnegative magnitude-demand envelope:

```text
%%eng

V_constr(x) = R_constr - q_constr*x
V_uso(x) = R_uso + q_uso*x

R_constr := 6*kN
q_constr := 4*kN/m
R_uso := -9*kN
q_uso := 1*kN/m
L := 2*m

envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)
```

At each sample EngCalc compares absolute magnitudes and keeps the maximum-magnitude demand. Original signed source curves remain available as faint context, so a negative response can govern magnitude without losing its original sign internally.

The same mode works with the restricted parameter sweep:

```text
%%eng

V(x) = q*(L/2-x)
L := 4*m

envelope(
    abs(V(x)),
    x,
    0,
    L,
    q=[2*tonf/m, 3*tonf/m, 4*tonf/m]
)
```

Every source in one envelope must use the same comparison mode. Mixing `abs(V_A(x))` with signed `V_B(x)` in the same envelope is rejected. There is no separate `abs_envelope(...)` alias.

Magnitude-envelope figures emphasize one `|response|_max` boundary, fill from zero to that boundary, retain signed source curves as faint context and place one compact `(x, y)` label at the global maximum-magnitude point.

## Example — propped cantilever by the force method

```text
%%eng
#@title { vertical-output: true }

## Estado 0: cargas reales
### Reacciones de la estructura base

Sigma_F_y_0 = 0
V_A0 = q*L

Sigma_M_A_0 = 0
M_A0 = q*L^2/2

### Fuerzas internas

V_0(x) = V_A0 - q*x
M_0(x) = -M_A0 + V_A0*x - q*x^2/2

## Estado 1: carga unitaria en B
### Reacciones de la estructura base

Sigma_F_y_1 = 0
V_A1 = -1

Sigma_M_A_1 = 0
M_A1 = -L

### Fuerzas internas

V_1(x) = V_A1
M_1(x) = -M_A1 + V_A1*x

## Compatibilidad

Delta_B0 = integrate(M_0(x)*M_1(x)/(E*I), x, 0, L)
f_11 = integrate(M_1(x)^2/(E*I), x, 0, L)
Delta_B = Delta_B0 + V_B*f_11
V_B = solve(Delta_B = 0, V_B)

V_A = q*L - V_B
M_A = q*L^2/2 - V_B*L
V(x) = expand(V_0(x) + V_B*V_1(x))
M(x) = expand(M_0(x) + V_B*M_1(x))

## Datos numéricos

q := 2.8*tonf/m
L := 4*m
E := 200*GPa
I := 8.5e8*mm^4

## Resultados

numeric(Delta_B0, mm)
numeric(V_B, kN)
numeric(V_A, kN)
numeric(M_A, kN*m)

## Funciones con datos conocidos

numeric(V(x))
numeric(M(x))

## Diagramas

plot(V(x), x, 0, L)
plot(M(x), x, 0, L)
```

The result and plot calls reuse the same symbolic functions and numerical data; no duplicate Python definitions are required.

## Complete command reference

### Notebook magics

- `%%eng` — evaluate a whole EngCalc cell.
- `%eng_reset` — clear both symbolic and numerical EngCalc state.
- `%eng_config precision=3 zero_tolerance=1e-10` — set global numerical presentation settings.
- `%eng_config` — show the active numerical presentation settings.

`%load_ext engcalc_colab` and `%reload_ext engcalc_colab` are IPython extension-management magics, not EngCalc expression commands.

### Symbolic definitions and expressions

- `A = expression` — scalar/symbolic assignment.
- `M(x) = expression` — single-argument symbolic function definition.
- `M(x)` — call a previously defined EngCalc function.
- standalone expressions are supported.
- identifiers are created symbolically on first use; no `symbols()` declaration is required.

### Numerical definitions and evaluation

- `q := 2.8*tonf/m` — associate a unit-aware numerical value with `q` without changing symbolic `q`.
- `P := q*L` — numerical values may reference earlier numerical values.
- `numeric(V_B)` — detailed numerical presentation: symbolic formula → explicit substitution → final result.
- `numeric(M_A, kN*m)` — detailed evaluation with final target-unit conversion.
- `result(V_B)` — compact numerical presentation: symbolic formula → final result.
- `result(M_A, kN*m)` — compact presentation with final target-unit conversion.
- `numeric(q*L^2/8)` / `result(q*L^2/8)` — evaluate a direct symbolic expression; every free symbol must have a numerical value.
- `numeric(V(x))` / `result(V(x))` — partially evaluate a user-defined symbolic function if its argument is still free; fully evaluate it if the argument has a numerical value.
- `numeric(M(L))` / `result(M(L))` — fully evaluate a user-defined symbolic function at another symbolic quantity whose numerical value is known.

### Plotting and envelopes

- `plot(expression, variable, start, end)` — create one unit-aware Matplotlib figure using 201 samples including both endpoints.
- `plot(expr1, expr2, ..., variable, start, end)` — overlay several dimensionally compatible expressions on one shared axis.
- `plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])` — plot one expression for several local values of one parameter.
- `envelope(expr1, expr2, ..., variable, start, end)` — compute and render signed pointwise upper/lower envelopes.
- `envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])` — compute an envelope from one expression over one local parameter sweep.
- `envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)` — compute a nonnegative maximum-magnitude envelope while retaining signed source context.
- the final three positional arguments are always `variable, start, end`.
- a parameter sweep accepts one keyword with a non-empty list of complete numerical expressions.
- sweeps do not persist or overwrite the swept parameter's stored numerical value.
- the plotting variable is locally overridden for sampling and any stored numeric value for that name is preserved.
- all y series on one shared axis must have compatible dimensions.
- all-moment plots and envelopes retain positive moment downward.
- plotting and envelopes are standalone statements; assigning `A = plot(...)` or `A = envelope(...)` is rejected.
- arbitrary plot styling/Matplotlib keyword arguments are not exposed.

### Arithmetic syntax

- addition: `a + b`
- subtraction: `a - b`
- multiplication: `a*b`
- division: `a/b`
- powers: `a^2` or `a**2`
- unary signs: `+a`, `-a`
- parentheses: `( ... )`
- integer and decimal constants

### Symbolic operations

- `integrate(expr, var, lower, upper)` — definite integral.
- `integrate(expr, var)` — indefinite integral. No constant of integration is invented;
  write the one you need, as on paper: `integrate(M(x)/(E*I), x) + C1`.
- `diff(expr, var)` — first derivative.
- `diff(expr, var, order)` — higher derivative.
- `solve(lhs = rhs, unknown)` — solve one equation for one unknown.
- `solve(expr, unknown)` — interpreted as `expr = 0`. When the equation has more than one
  solution they are all shown, and the statement defines nothing: there is no single value
  to assign. Use `roots(...)` to take the one inside a physical domain.
- `solve(eq_1, ..., eq_n, x_1, ..., x_n)` — solve a scalar system: **n equations
  followed by n unknowns**, so the argument count is always even. The two-argument form
  above is the n = 1 case of the same rule. A system is a standalone statement: the
  unknowns are the result, and solving defines them.
- `sum(expr, index, lower, upper)` — unevaluated indexed symbolic sum.
- `simplify(expr)` — simplify.
- `expand(expr)` — expand.
- `factor(expr)` — factor.
- `subs(expr, variable, value)` — symbolic substitution.
- `eq(lhs, rhs)` — explicit symbolic equality, mainly for advanced/internal use.
- `abs(expr)` — symbolic/numerical absolute value; composes with plotting and magnitude envelopes.

`solve(...)` currently requires exactly one solution; zero or multiple solutions produce a concise EngCalc error.

## Engineering presentation syntax

- `Sigma_F_y = ...` — renders the `Sigma_` prefix as engineering equilibrium notation such as `\Sigma F_y`.
- `# text` — invisible comment.
- `## text` — visible section heading.
- `### text` — visible subsection heading.
- blank line — adds a larger visual separation inside the current equation group.

Calculation rows use compact three-column MathJax blocks. The semantic spacing policy is **4 / 8 / 16 pt**: 4 pt for a wrapped continuation of the same stage, 8 pt for a distinct stage or consecutive source result, and 16 pt after an explicit blank source line.

For commutative products, the renderer applies engineering-oriented factor order without changing the mathematics.

## Google Colab side-by-side layout

Put this Colab directive immediately below `%%eng` when desired:

```text
%%eng
#@title { vertical-output: true }
```

EngCalc ignores the directive because it begins with a single `#`. Numerical equations continue to use the same MathJax renderer as symbolic equations, and native plots appear in source order between equation groups.

## Safety

`%%eng` uses restricted AST evaluators for symbolic expressions, numerical expressions and target-unit expressions. `plot(...)` and `envelope(...)` are restricted EngCalc operations: they do not expose arbitrary Matplotlib functions, callbacks, filenames or Python objects. Raw cell text is never passed to unrestricted Python `eval` or `exec`.

## Current limitations

v0.9.0 currently does not provide:

- subplots or multiple axes in one `plot(...)` or `envelope(...)` statement;
- arbitrary plot styling/options from EngCalc syntax;
- labeled dictionary cases such as named load combinations;
- multi-parameter/cartesian sweeps;
- dual y-axes for quantities with different dimensions;
- explicit plot/envelope x/y target-unit conversion;
- open/closed Piecewise endpoint glyphs or dedicated jump markers;
- automatic scientific-notation policy for very large/small displayed values;
- target-unit conversion of partially evaluated functions with a free independent variable;
- automatic compact coefficient evaluation for non-polynomial partial functions;
- exact browser-pixel-aware MathJax line wrapping;
- general keyword arguments or general list/dictionary syntax outside the restricted plot/envelope sweep slot;
- arbitrary Python execution or arbitrary library functions;
- multi-solution `solve(...)`;
- full LaTeX parsing.

## Version notes

- **0.25.1** — presentation corrections from the first use of the package by someone outside it: a name keeps every letter that was typed, a dimensionless ratio prints as a number, a moment prints in a moment's units, a coefficient obeys the page's precision, and a unit left in a substitution reads as a unit. The IPython floor is Colab's own 7.34.0, so installing EngCalc no longer upgrades the platform underneath it.
- **0.25.0** — `case D = M_D(x)` and `combo U1 = 1.2*D + 1.6*Lv`: a load combination keeps the factors it was written with, and `%eng_help` explains every call.
- **0.24.0** — `integral(...)` is retired; `integrate(...)` is the one name for the operation, and typing the old one says what to write instead.
- **0.23.0** — `solve(M(x) > 20*kN*m, x, 0, L)` answers an inequality with the region that satisfies it.
- **0.22.0** — `numeric(...)` reads a unit literal as the unit, agreeing with `:=`; scalars and matrices alike.
- **0.21.0** — `assume(...)` now decides between several answers from `solve`, and the sheet shows which were ruled out.
- **0.20.0** — `report(...)` marks a value and `summary()` collects the marked ones into a table at the end of the memoria.
- **0.19.0** — `governing(...)` reports which response governs on which interval, with exact boundaries taken from the crossovers rather than from the envelope's sampling.
- **0.18.0** — `numeric(...)` resolves names the symbolic sheet defines, not only values given with `:=`, so a deflection written with its integration constants can be evaluated once the boundary conditions determine them.
- **0.17.0** — `subs(...)` takes several variable/value pairs and applies them simultaneously, and `assume(L > 0)` states what is known before a symbol is used, which is what lets `sqrt(L^2)` simplify to `L`.
- **0.16.0** — `numeric(...)` evaluates a symbolic summation, so a sum of loads becomes a number while still rendering as a sigma. No second function name; the symbolic/numeric division of labour is the same as everywhere else.
- **0.15.0** — Macaulay brackets `<x-a>^n`: a beam is written as one expression with one term per load instead of a Piecewise branch per load, and the brackets integrate term by term so double integration chains directly.
- **0.14.0** — `solve` shows every solution instead of refusing when there is more than one. The statement defines nothing, since there is no single value to assign; `roots(...)` remains the tool for taking the physically admissible root.
- **0.13.0** — indefinite integral: `integrate(expr, var)` returns the antiderivative, so an elastic curve is derived from its shear rather than quoted. No constant of integration is invented; the engineer writes it.
- **0.12.0** — scalar equation systems: `solve(eq_1, ..., eq_n, x_1, ..., x_n)` solves n equations for n unknowns, renders each on its own labelled line and defines them. Statics and elastic-curve boundary conditions no longer need a matrix.
- **0.11.0** — `integrate(...)` is the name for the definite integral, matching the convention every mathematical Python user already knows. `integral(...)` was kept as an alias at the time and retired in 0.24.0.
- **0.10.1** — the display unit is chosen by readable magnitude rather than by counting significant figures, so an admissible deflection of exactly `L/300` no longer stays in metres beside the deflection it bounds.
- **0.10.0** — engineering presentation: quantities shown in units an engineer writes, declared units preserved, algebra-produced compound units replaced by units of their own dimension, one unit per table column and per matrix, and scientific notation below the family floor. No computed value changes.
- **0.9.2** — audit remediation and reliability: resilient exact-first characteristic discovery with deterministic fallback, explicit-real engineering symbols, consistent direct unit bounds, normalized Piecewise topology, exact characteristic presentation polish, declared IPython runtime support, and permanent Python 3.10–3.14 CI.
- **0.9.1** — exact-first roots, intersections and extrema with unit-aware Piecewise semantics, deterministic numerical fallback, and authoritative ordinary-plot extrema metadata.
- **0.9.0** — native exact symbolic matrices/vectors, one-based indexing, matrix-valued CAS functions, Pint-backed per-entry numerical matrices, exact `solve(A, b)`, guarded rank/RREF/norm/eigen analysis, native MathJax matrix presentation, Piecewise-cell integration and indexed scalar table/plot/envelope workflows.
- **0.8.0** — restricted unit-aware Piecewise expressions with partial numerical cases, exact breakpoint-enriched shared plot grids, segmented discontinuous rendering, Piecewise calculus semantics, diagnostics and real `%%eng` acceptance.
- **0.7.2** — native engineering tables with automatic unit-aware discretization, unit-once and fully explicit point forms, compatible multi-response columns, native HTML rendering, and source-order `%%eng` integration.
- **0.7.1** — multi-argument user functions and generalized partial numerical evaluation.
- **0.7.0** — scalar engineering mathematics: `sqrt`, trig/inverse trig, `exp`, `log`, and `pi` with unit-aware numerical rules.
- **0.6.2** — direct unit-bearing arguments for numerical user-function evaluation, dimensional-zero preservation, and corrective numerical diagnostics.
- **0.6.1** — adaptive semantic MathJax rendering with 4/8/16 spacing; compact `result(...)`; compact collision-aware `(x, y)` characteristic labels for plots and envelopes; no numerical-method changes.
- **0.6.0** — `abs(...)` and magnitude envelopes.
- **0.5.0** — sampled signed engineering envelopes.
- **0.4.0** — multi-series plotting and restricted one-parameter sweeps.
- **0.3.0** — native unit-aware plotting inside `%%eng`.
- **0.2.x** — numerical presentation settings, adaptive MathJax rendering, target-unit conversion and partial numerical functions.

## Development

```bash
python -m pip install -e '.[dev]'
pytest -q
```

Version: `0.25.1`.
