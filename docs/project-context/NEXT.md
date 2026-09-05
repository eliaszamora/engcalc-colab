# Where EngCalc stands, and what to pick up next

_Written 2026-09-05, at the end of the session that worked the findings of an external
trial. Read this before `CURRENT.md`, which has not been updated since 0.13.0 and
describes a tree that no longer exists._

## Baseline

| | |
|---|---|
| `main` | `6a675ac` (#81 merged) |
| declared version | **0.25.1** |
| default suite (`pytest -q`) | **1562 passing** — `tests` plus `quality_tests/fast` |
| Deep Property Gate (`pytest quality_tests`) | **207 properties** |
| CI | six jobs: Python 3.10–3.14 plus one pinned to Colab's `ipython==7.34.0` |

**The bump is done** - 0.25.1, the patch digit `0.9.2` and `0.10.1` used for a release
of corrections carrying no new feature. Kept here because the next one will want it: a
bump is not the two-file change this note first claimed. The version string is asserted
in four test modules, and `tests/test_version.py` additionally pins the README's opening
line, its closing line and its changelog. Seven files:

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
those three changelog lines to stay where they are. A release also gets a `## vX.Y.Z`
section of its own; `v0.23.3` and `v0.25.1` are the shape a set of corrections takes.

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

## Open work, in the order I would take it

### RC-3 — preservation of intermediate formulas

**This is design, not a patch, and it is the only one of the four external findings that
is not a bug.**

An engineer writes

```text
a = As*fy/(0.85*fc*b)
phiMn = phi*As*fy*(d - a/2)
numeric(phiMn)
```

and wants the main stage of the memoria to read

    φMn = φ As fy (d − a/2)

Today EngCalc expands it down to primitives — `cover`, `db_st`, `h`, `b`, `fc` — because
the symbolic layer substitutes a definition's free symbols at definition time. That is
the two-layer model working as designed, not a defect, which is why it needs a decision
before it needs code.

The questions I would want answered before anyone writes a line:

- **What makes a name a barrier?** Opt-in with a marker, or does every `=` definition
  become one? Making them all barriers changes every memoria that already works.
- **What does the substitution stage show for a barrier name** — the name's own value
  (`a = 103.04 mm`), or nothing, or a nested trace?
- **Does the barrier survive further algebra?** `solve(...)` and `subs(...)` rebuild
  expressions; a barrier that dissolves the moment it is used is worse than none.
- **How does it interact with `report`, `summary` and `governing`,** all of which
  re-render stored expressions?

Related surface already in the tree: `case` / `combo` (#71) keep a combination's factors
rather than expanding them, which is the same idea in a narrower place. Read that first.

### RC-1 — imperial units

`kip`, `ksi`, `inch`, `ft` are not in `_UNIT_ALIASES` (`src/engcalc_colab/numeric.py`),
so an ACI example in its own units stops at `unknown numeric name 'ksi'`. Half an hour of
work: the alias table, `_UNIT_FAMILIES` entries if imperial families are wanted for
display, and contracts. Low urgency for a sheet in SI, and it is the difference between
reading a US code example directly and transcribing it.

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
