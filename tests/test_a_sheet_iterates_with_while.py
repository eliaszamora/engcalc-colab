r"""`% while`: a sheet iterates until a condition stops holding, and the memoria shows the end.

    x := 1*m
    % while abs(x^2 - 2*m^2) > 1e-6*m^2:
    x := (x + 2*m^2/x)/2
    % end

Approved on 2026-09-25 with `% if` and `% for`: a `% while` shows only the final result and
how many iterations it took - an iteration nobody reads is not written. The rows are those
of the last iteration, after a sentence in the letter of the rows that says how many there
were and that the condition no longer holds: **En 4 iteraciones:** `|x² - 2 m²| = ... ≤ ...`,
which is what shows it converged. A loop that does not stop within a limit is refused with
its line, instead of hanging the notebook. He asked for it on 2026-09-25 (*"sigue con el
while"*).
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.control as control
import engcalc_colab.magic as magic

NOTE = r"\textbf{En "


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str):
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        shown = [item.data for item in captured if isinstance(item, Math)]
        notes = [data for data in shown if NOTE in data or r"\textbf{Como}" in data]
        math = " ".join(data for data in shown if data not in notes)
        return math, notes, console.getvalue()

    return run


NEWTON = (
    "x := 1*m\n"
    "% while abs(x^2 - 2*m^2) > 1e-6*m^2:\n"
    "x := (x + 2*m^2/x)/2\n"
    "% end\n"
)


def test_only_the_last_iteration_is_written(sheet):
    math, notes, console = sheet(NEWTON)
    assert not console, console
    assert math.count(r"x & = &") == 2, math  # the start, and the end
    assert r"x & = & \displaystyle 1.41\,\mathrm{m}" in math, math
    # 1.50 m and 1.42 m were iterations: not on the page.
    assert "1.50" not in math and "1.42" not in math, math


def test_it_says_how_many_iterations_and_that_the_condition_no_longer_holds(sheet):
    _math, notes, _console = sheet(NEWTON)
    (note,) = notes
    assert r"\textbf{En 4 iteraciones:}" in note, note
    assert r"\leq" in note, note


def test_the_value_after_the_loop_is_the_last_one(sheet):
    math, _notes, console = sheet(NEWTON + "y := 2*x\n")
    assert not console, console
    assert r"y & = & \displaystyle 2.83\,\mathrm{m}" in math, math


def test_one_iteration_is_said_in_the_singular(sheet):
    _math, notes, _console = sheet("x := 3*m\n% while x > 2*m:\nx := x - 2*m\n% end\n")
    (note,) = notes
    assert r"\textbf{En 1 iteración:}" in note, note


def test_a_condition_that_does_not_hold_at_the_start_runs_nothing_and_says_so(sheet):
    math, notes, console = sheet("x := 1*m\n% while x > 2*m:\nx := x - 1*m\n% end\n")
    assert not console, console
    (note,) = notes
    assert r"\textbf{En 0 iteraciones:}" in note and r"\leq" in note, note
    assert math.count(r"x & = &") == 1, math


def test_a_counter_of_the_percent_layer_counts_the_iterations(sheet):
    math, _notes, console = sheet(
        "% n = 0\nx := 3*m\n% while x > 2*m:\nx := x - 0.5*m\n% n += 1\n% end\nk := {n}*m\n"
    )
    assert not console, console
    assert r"k & = & \displaystyle 2.00\,\mathrm{m}" in math, math


def test_a_condition_on_a_counter_reads_the_counter_each_time(sheet):
    # Found by the smoke of 0.39.0 before it was published: `% while k < 3` with `% k += 1`
    # in the body ran 1000 times. The condition was read with the counter's value put in
    # its place, and put there for good - `0 < 3` every time after the first.
    math, notes, console = sheet("% k = 0\nx := 1*m\n% while k < 3:\n% k += 1\nx := x + 1*m\n% end\n")
    assert not console, console
    assert r"\textbf{En 3 iteraciones:}" in notes[0], notes
    assert r"x & = & \displaystyle 4.00\,\mathrm{m}" in math, math


def test_a_counter_in_a_condition_inside_a_for_is_read_each_time(sheet):
    # The same reading, for `% if` inside a `% for`: each pass reads its own value.
    math, _notes, console = sheet(
        "% for i in [1, 2, 3]:\n% if i > 1:\nx_{i} := {i}*m\n% end\n% end\n"
    )
    assert not console, console
    assert r"x_{1}" not in math and r"x_{2}" in math and r"x_{3}" in math, math


def test_a_loop_that_does_not_stop_is_refused_with_its_line(sheet, monkeypatch):
    monkeypatch.setattr(control, "_MOST_ITERATIONS", 20)
    math, _notes, console = sheet("x := 1*m\n% while x > 0*m:\nx := x + 1*m\n% end\n")
    assert "line 2" in console and "20" in console, console


@pytest.mark.parametrize(
    "source, words",
    [
        ("% while 1 > 0:\n", ("line 1", "% end")),
        ("% while:\n% end\n", ("line 1", "% while")),
        ("% while 1 > 0:\n% else:\n% end\n", ("line 2", "% else")),
    ],
)
def test_a_while_written_wrong_says_where(sheet, source, words):
    _math, _notes, console = sheet(source)
    for word in words:
        assert word in console, (word, console)


def test_both_sides_of_the_sentence_are_in_one_unit(sheet):
    # The tolerance, 1e-6 m², has no figure left in m²: both sides go to a unit where it
    # has, rather than `0.00 m² ≤ 0.01 cm²`. The residual then reads as what it is.
    _math, notes, _console = sheet(NEWTON)
    (note,) = notes
    assert r"= 4.51 \times 10^{-8}\,\mathrm{cm}^{2} \leq 0.01\,\mathrm{cm}^{2}" in note, note


def test_a_condition_written_wrong_refuses_the_cell_before_anything_runs(sheet):
    math, _notes, console = sheet("y := 1*m\n% while y >:\ny := 2*m\n% end\n")
    assert "line 2" in console, console
    assert "y" not in math, math
