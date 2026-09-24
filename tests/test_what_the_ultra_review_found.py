r"""What the independent review of 0.31.18 - 0.33.3 found, each one run before it was fixed.

The review (`/code-review ultra 265`, 2026-09-24) reported five findings. Each was
reproduced on 0.33.3 before anything changed; four are defects and are pinned here.

1. **A line that fails still taught the sheet.** `evaluate` recorded the units a statement
   measures and the order its products are written in before evaluating it, so a line that
   then failed - a typo, an unknown function - left both behind for the rest of the
   session. `q = 3*s + nofunc(1)` followed by `T = [c, s; -s, c]` read `[c, 1 s; ...]`
   again, the regression 0.32.3 had fixed; and `a = I*E + nofunc(3)` made every later
   `E*I` read `I E`. What a failed line reads is not something the sheet goes on with.

2. **`solve` inside a larger expression was solved twice.** The row's formula is read a
   second time when a call sits inside something larger (#267), and `solve` had no answer
   kept for that second reading. The page was right - `z = 8` - and the equation was
   solved again for nothing. The first reading's answers are now reused.

3. **The substitution stage was drawn one way and counted another.** The row spacing
   rebuilt the stage without the row's units and without its piecewise branches, and a
   helper rebuilt it again, so the rows counted and the rows drawn were separate
   computations that could disagree. One function builds it now, for both passes.

5. **A name updated from itself showed its new value in its own formula.** The formula is
   read a second time after the name is stored, so `v = 5` then `v = v + 2*diff(t^2, t)`
   read `v = 4t + 2 d/dt t² + 5`: the new `v` inside the formula that defines it. It is
   read before the name is stored now, and reads `2 d/dt t² + 5`, the `5` it was.

The fourth finding - `(-8)^(1/3)` has a real cube root, and EngCalc says it has no real
value - is a decision, not a defect, and is left to him.
"""

import contextlib
import io

import pytest

from IPython.display import Math

import engcalc_colab.magic as magic
import engcalc_colab.engine as engine_module
import engcalc_colab.renderer as renderer


@pytest.fixture
def sheet(monkeypatch):
    engine = magic.EngMagics()

    def run(source: str) -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            engine.eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), console.getvalue()

    run.engine = engine
    return run


# --- 1 ---------------------------------------------------------------------------------


def test_a_failed_line_does_not_make_a_letter_a_unit(sheet):
    _, console = sheet("q = 3*s + nofunc(1)\n")
    assert "nofunc" in console, console
    page, _ = sheet("T = [c, s; -s, c]\n")
    assert r"1\,\mathrm{s}" not in page, page


def test_a_failed_line_does_not_set_the_order_of_a_product(sheet):
    _, console = sheet("a = I*E + nofunc(3)\n")
    assert "nofunc" in console, console
    page, _ = sheet("b = E*I/L\n")
    assert r"\frac{E I}{L}" in page, page


def test_a_line_that_succeeds_still_teaches_the_sheet(sheet):
    sheet("k := 2*kN/m\nx = 1*m\n")
    assert "m" in sheet.engine.engine.measured_units
    sheet("a = I*E\n")
    page, _ = sheet("b = E*I/L\n")
    assert r"\frac{I E}{L}" in page, page


# --- 2 ---------------------------------------------------------------------------------


def test_solve_inside_a_larger_expression_is_solved_once(sheet, monkeypatch):
    calls = []
    real = engine_module.sp.solve

    def counting(*args, **kwargs):
        calls.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(engine_module.sp, "solve", counting)
    page, console = sheet("z = 2*solve(x - 4 = 0, x)\n")
    assert not console, console
    assert len(calls) == 1, calls
    assert page.rstrip().endswith(r"z & = & \displaystyle 8 \end{array}"), page


# --- 3 ---------------------------------------------------------------------------------


def test_the_rows_drawn_and_the_rows_counted_are_one_computation(sheet, monkeypatch):
    """Drawing and spacing are two passes, and each asks `_numeric_substituted_rows` once:
    no copy of the stage is built anywhere else, and both passes get the same rows."""
    branches = []
    stages = []
    real_branches = renderer._named_value_branches
    real_stage = renderer._numeric_substituted_rows

    def counting_branches(*args, **kwargs):
        branches.append(args)
        return real_branches(*args, **kwargs)

    def recording_stage(*args, **kwargs):
        rows = real_stage(*args, **kwargs)
        stages.append(rows)
        return rows

    monkeypatch.setattr(renderer, "_named_value_branches", counting_branches)
    monkeypatch.setattr(renderer, "_numeric_substituted_rows", recording_stage)
    page, console = sheet("q := 10*kN/m\nL := 6*m\nM = q*L^2/8\nnumeric(M)\n")
    assert not console, console
    assert r"\left(10.00" in page, page
    assert len(stages) == 2, len(stages)
    assert stages[0] == stages[1], stages
    assert len(branches) == len(stages), (len(branches), len(stages))


# --- 5 ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "formula", "false"),
    [
        ("v = 5\nv = v + 2*diff(t^2, t)\n", r"2 \frac{d}{d t} t^{2} + 5", r"4 t + 2 \frac{d}{d t} t^{2} + 5"),
        ("v = 5\nv = 2*integrate(t, t, 0, 1) + v\n", r"2 \int\limits_{0}^{1} t\, dt + 5", r"dt + 6"),
        ("v(t) = t\nv(t) = v(t) + 2*diff(t^2, t)\n", r"t + 2 \frac{d}{d t} t^{2}", r"5 t + 2 \frac{d}{d t}"),
    ],
)
def test_a_name_updated_from_itself_shows_what_it_was(sheet, source, formula, false):
    page, console = sheet(source)
    assert not console, console
    last = page[page.rindex(r"& = &"):]
    assert formula in last, last
    assert false not in last, last
