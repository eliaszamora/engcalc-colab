# How this work goes wrong

Failure modes seen while building EngCalc, each with the instance that produced it and
the check that catches it. Written after a session that closed the four findings of an
external trial, because the same mistakes kept arriving in different clothes.

None of these are about carelessness in the code. Every one of them is about **believing
something without measuring it**, and every one produced work that looked finished.

---

## 1. A contract that passes without exercising anything

The most common failure here by a distance. A test is written, it is green, and it never
reaches the code it is named after.

| the contract | why it proved nothing |
|---|---|
| `parse_cell("b := sin(")` for the `in`/`inch` hint | dies on the unbalanced-parenthesis guard, never reaches the hint |
| `parse_cell("b := 12*(")` as the negative case | same guard, same nothing |
| `\frac{L^{2} q}{8}` for a definition's rendering | that is `sp.latex`'s ordering; the renderer writes `\frac{q L^{2}}{8}` |
| `\left(-1\right)` absent, for a written form | again `sp.latex`; the renderer collects those denominators correctly |

Each was green on the first run. Each died the moment the thing it guarded was mutated —
which is the only reason any of them was found.

**The check.** A contract is not evidence until it has failed on purpose. Mutate the
guard it is named after and watch it die. If it stays green, it is testing something
else, and the something else is usually a guard three layers earlier.

**And take expectations from the system, not from a library.** `sp.latex` is not this
renderer: it orders products differently and knows nothing about the upright rule for a
multi-letter name. Run the sheet, read what comes out, assert that.

---

## 2. Verifying the mathematics is not verifying the page

`Mul(-1, Add(a, b), evaluate=False)` is the correct expression for `-(a + b)`. It prints
as `- a + b`. The value is right and the page states something false.

A verification that rebuilds the expression and compares it - `_agrees_with` - cannot see
this, and neither can any test asserting that a LaTeX string contains a substring, because
the wrong page contains all the same substrings.

This is the same shape as #76, where `Mu` printed as `M`: a rendering that was accepted
because it began with a backslash.

**The check.** Render the page and read it. `tools/render_memoria.py` drives the real
magic and writes the HTML a notebook would show. The external trial's four defects were
found that way with a suite of 1387 watching, and this session's were found the same way
with more than 1562.

---

## 3. Comments that were true when they were written

Two kinds, both found by mutation rather than by reading.

**A comment invalidated by a change elsewhere.** `_best_in_family` documented its `start`
argument as inert *because every family stepped by 1000 or more*. Adding the US customary
length family - `inch` to `ft`, a step of 12 - made that reason false while leaving the
conclusion true. The branch is still inert, for a sturdier reason, and the comment now
gives that one.

**A comment written from the wrong measurement.** Two comments blamed `(-1)` and separate
`1/b`, `1/fc` fractions for a restriction. That was `sp.latex` output. The real reason was
width: the written form is wider, which tips the row past the wrapping budget, and the
wrapping path splits a product into additive terms.

**The check.** When you add an entry to a table that a comment reasons about, re-verify
the comment. And when a comment states a measurement, the measurement is part of the
comment: re-run it rather than inheriting it.

---

## 4. A number said from memory instead of counted

| claimed | actual |
|---|---|
| the version bump is "two files" | seven |
| the version appears in "three test names" | four |
| those names had been stale "for fifteen releases" | never counted; removed |
| `As fy / (0.85 fc b)` is "127.5 mm" | 127.48 mm |

The first one was written into a handoff document and would have been read as fact by the
next session.

**The check.** If a number can be counted, count it before writing it down. `grep -c` is
cheaper than being wrong in a document somebody trusts.

---

## 5. A sloppy measurement that nearly killed a good design

The written form for `#88` was first built with nested unevaluated `Add`s and `Mul`s. It
printed `L^4 \cdot 5 q` and `-(cover + db_st - h)`: worse than the defect it was meant to
fix, on four of eight real formulas. The approach looked dead.

The nesting was the fault, not the approach. Flattened, six of the eight render
identically. Of the two that differ, one is the defect being fixed, and the other differs
only because the probe used `sympify("E")` - Euler's number, not a defined name - where
the written form was right and the evaluated one wrong.

**The check.** When a measurement says no, ask whether the measurement is at fault before
believing it. A negative result from a probe you wrote in five minutes is a claim about
your probe.

---

## 6. Guards nobody can reach, and abstractions nobody uses

A guard was written to stop the written form running for a statement that plots or
summarises. Turned into a raise, it fired **zero times** across the whole suite: both of
those return their own result before it. A `_negate` seam was opened in the evaluator for
a subclass that, once measured, turned out not to need it.

Both were deleted. Neither could be told apart from its absence.

**The check.** A guard you cannot make fire is not defence in depth, it is furniture.
Turn it into a raise and run everything. An abstraction with one implementation and no
second caller is the same thing.

---

## 7. Harnesses that lie

Three ways, all seen:

- **An exit code is not a verdict.** Read pytest's own summary line. A harness scoring by
  exit code will report a pass for a run that collected nothing.
- **A killed harness does not run its `finally`.** A mutation run that times out leaves
  the tree mutated, and the next run diagnoses its own damage as a real defect. Restore at
  the *start* as well as the end.
- **A subset proves nothing about a survivor.** A mutation that survives a fast subset
  must be re-run against the full suite before it is called inert. One survivor in this
  session was inert on a subset and inert on the full suite; that is a different sentence
  from the first one, and only the second is worth writing down.

---

## 8. Escaping, which cost more time than any defect

Writing Python that patches Python, inside a shell heredoc, inside a tool call, loses
backslashes at a layer nobody is watching. It produced, in one session: several silent
no-op replacements whose `assert` was missing, an anchor that never matched, and a
literal backspace character (`\x08`) written into a regular expression in place of a
word boundary.

**The check.** Write files with a file-writing tool, not with nested heredocs. Where a
patch script is unavoidable, `assert old in text` before replacing, every time - a silent
no-op looks exactly like success.

---

## 9. A check that fails towards "fine"

Section 7 is about harnesses. This is the shape underneath it, and it showed up three
times in one session, in three different kinds of tool. Every time, the broken check
produced the reassuring answer rather than an error:

- **`gh pr checks` reported six green from a stale run.** After a force-push it answered
  for the commit that had been replaced, while the new one was still `in_progress`. The
  rule in this repository is CI green *on that exact SHA*, and the tool most likely to be
  used to check it will happily answer about a different one. Ask
  `repos/<owner>/<repo>/commits/<sha>/check-runs` instead.

- **A mutation harness reported six clean survivors having never run pytest.** One path
  in its subset named a module that does not exist. pytest exits without a summary line,
  the harness found no "failed" in it, and "no failure" and "nothing ran" are the same
  string to a grep. It reads as a weak contract set - which is a conclusion you might act
  on - rather than as a broken tool.

- **A polling loop span for twenty-four minutes on green CI.** Its `jq` filter had
  `\"-\"` inside single quotes, which is a parse error; `2>/dev/null` swallowed it; the
  empty result failed the loop's own guard; and the symptom was "CI is slow". The
  engineer noticed before I did.

**What they share.** None of them raised. Each degraded into the answer that invites you
to move on, and two of the three were about *verification itself* - so the thing that
failed was the thing whose job was to notice failure.

**The checks.**

- A verifier must fail loudly. If it cannot produce a verdict, say so and stop; never
  return the shape of a good answer. The mutation harness now raises on a missing summary
  line rather than printing "SURVIVED".
- Do not silence a checker's stderr. `2>/dev/null` on a query whose output you are about
  to branch on converts a bug into a wrong answer.
- Prefer a query that names what you are asking about. `gh pr checks` asks about a pull
  request; the rule is about a commit.
- When something takes much longer than every previous run of the same thing, that is
  data. Twenty-four minutes against a two-minute baseline was the signal, and it was
  read as patience for three-quarters of an hour.

---

## What would make the tool better, rather than the process

**Write page-level invariants, not only substring contracts.** The single most productive
test of the session asserts that no two consecutive rows on the reference memoria are
identical. It found two defects that nothing else could see, including one on the
repository's own reference sheet. Everything else in the suite asks whether a LaTeX string
contains a substring; those questions cannot see a page that is wrong in a new way.

Other invariants worth having, in the same shape:

- no row on the reference memoria contains a unit outside the family of its dimension
- no coefficient the engineer typed is absent from the page it was typed on
- no name is rendered in a form that would parse as a different name

**Measure before choosing, and let the measurement decide.** `keep` is opt-in because
making every definition a barrier moves 24 of 131 memoria-shaped tests, not because
opt-in felt safer. The blast radius of the alternative was a number, obtained by making
the crude version of the change and counting what failed. The question had stood in the
handoff as a design decision waiting on an opinion; it wanted a measurement, and the
measurement was one run of a subset.

**The suite grows faster than its ability to see.** It went from 1562 to 1624 tests in one
session, and two duplicated rows sat on the repository's own reference memoria the whole
time, on the sheet every reader is pointed at first. Test count is
not coverage of the thing that matters here, which is what the page says. When adding
tests, ask which of them would fail if the page were wrong in a way nobody has thought of
yet.
