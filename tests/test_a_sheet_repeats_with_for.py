r"""`% for`: a sheet writes a line once and the memoria has it once per value.

    % for i, (a, b) in enumerate([(1.4, 0), (1.2, 1.6)], start=1):
    M_U{i} := M({a}, {b})
    % end

Approved on 2026-09-25 with `% if` (*"Apruebo tus recomendaciones en los 4 puntos"*): the
`%` lines are Python; `{...}` puts a value of the `%` layer into a sheet line - `M_U{i}`
becomes `M_U1`, `M({a}, {b})` becomes `M(1.4, 0)`; the memoria shows each iteration's rows
one after the other, as if they had been written by hand; the `%` layer's own variables
(`% n = 0`, `% n += 1`) never appear on it. A name of the sheet inside the `%` layer stands
for itself, so `{F}` over `[F_1, F_2]` writes `F_1`, then `F_2`, as a hand-written sheet
would. He asked to go on with it on 2026-09-25 (*"sigue con el for"*).
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str):
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        math = " ".join(item.data for item in captured if isinstance(item, Math))
        return math, console.getvalue()

    return run


BEAM = "q_D := 18*kN/m\nq_L := 12*kN/m\nL := 6*m\nM(a, b) = (a*q_D + b*q_L)*L^2/8\n"


def test_each_combination_is_written_as_if_by_hand(sheet):
    math, console = sheet(BEAM + (
        "% for i, (a, b) in enumerate([(1.4, 0), (1.2, 1.6)], start=1):\n"
        "M_U{i} := M({a}, {b})\n"
        "% end\n"
    ))
    assert not console, console
    assert r"M_{U1} & = &" in math and r"M_{U2} & = &" in math, math
    assert r"113.40\,\mathrm{kN} \cdot \mathrm{m}" in math, math
    assert r"183.60\,\mathrm{kN} \cdot \mathrm{m}" in math, math
    # In the order written, and nothing of the `%` layer on the page.
    assert math.index(r"M_{U1}") < math.index(r"M_{U2}"), math
    assert "enumerate" not in math and "for" not in math, math


def test_a_header_may_run_over_several_lines(sheet):
    math, console = sheet(BEAM + (
        "% for i, (a, b) in enumerate([(1.4, 0),\n"
        "%                             (1.2, 1.6),\n"
        "%                             (0.9, 0)], start=1):\n"
        "M_U{i} := M({a}, {b})\n"
        "% end\n"
    ))
    assert not console, console
    assert r"M_{U3} & = &" in math and r"72.90\,\mathrm{kN} \cdot \mathrm{m}" in math, math


def test_a_name_of_the_sheet_is_written_as_its_name(sheet):
    math, console = sheet(
        "F_1 := 10*kN\nF_2 := 20*kN\n"
        "% for i, F in enumerate([F_1, F_2], start=1):\n"
        "D_{i} = 2*{F}\n"
        "numeric(D_{i})\n"
        "% end\n"
    )
    assert not console, console
    first = math.split(r"D_{1} & = &", 1)[1].split(r"D_{2}", 1)[0]
    assert r"2 F_{1}" in first and r"20.00\,\mathrm{kN}" in first, first
    second = math.split(r"D_{2} & = &", 1)[1]
    assert r"2 F_{2}" in second and r"40.00\,\mathrm{kN}" in second, second


def test_a_helper_variable_counts_and_stays_off_the_page(sheet):
    math, console = sheet(
        "% n = 0\n"
        "% for x in [2, 3, 5]:\n"
        "% n += 1\n"
        "y_{n} := {x}*m\n"
        "% end\n"
        "k := {n}*m\n"
    )
    assert not console, console
    assert r"y_{3} & = & \displaystyle 5.00\,\mathrm{m}" in math, math
    assert r"k & = & \displaystyle 3.00\,\mathrm{m}" in math, math
    assert "n & = &" not in math, math


def test_an_if_inside_a_for_reads_the_loop_variable(sheet):
    math, console = sheet(
        "% for x in [1, 3]:\n"
        "% if x > 2:\n"
        "y_{x} := {x}*m\n"
        "% end\n"
        "% end\n"
    )
    assert not console, console
    assert r"y_{3} & = &" in math and r"y_{1} & = &" not in math, math


def test_a_for_inside_a_branch_runs_only_when_the_branch_does(sheet):
    math, console = sheet(
        "V := 5*kN\n"
        "% if V > 10*kN:\n"
        "% for i in [1, 2]:\n"
        "z_{i} := {i}*m\n"
        "% end\n"
        "% end\n"
    )
    assert not console, console
    assert "z_{1}" not in math, math


@pytest.mark.parametrize(
    "source, words",
    [
        ("% for i in [1, 2]:\ny_{i} := {i}*m\n", ("line 1", "% end")),
        ("% for i in [1, 2]:\ny_{j} := 1*m\n% end\n", ("line 2", "j")),
        ("% for i in 5:\ny_{i} := 1*m\n% end\n", ("line 1", "5")),
        ("% for i in [1, 2]\ny_{i} := 1*m\n% end\n", ("line 1", "for")),
        ("% for i in [1, 2]:\ny_{i} := 1*m\n% else:\n% end\n", ("line 3", "% else")),
        ("% for i in range(5000):\ny_{i} := 1*m\n% end\n", ("line 1", "1000")),
        ("F_1 := 1*kN\n% for F in [2*F_1]:\nD := {F}\n% end\n", ("line 3", "{F}")),
        ("% while 1 > 0:\n% end\n", ("line 1", "% for")),
        ("% import os\n", ("line 1", "% n = 0")),
    ],
)
def test_a_loop_written_wrong_says_where(sheet, source, words):
    math, console = sheet(source)
    for word in words:
        assert word in console, (word, console)


def test_a_line_written_wrong_in_the_body_refuses_the_cell_before_anything_runs(sheet):
    math, console = sheet("y := 1*m\n% for i in [1, 2]:\nz_{i} = w +\n% end\n")
    assert "line 3" in console, console
    assert "y" not in math, math


def test_a_brace_in_a_text_block_is_text(sheet):
    # A `%` line, so the cell goes through the `%` layer, where a brace is read.
    math, console = sheet('% n = 1\n"""\nLa fórmula $\\frac{a}{b}$ de la norma.\n"""\ny := 1*m\n')
    assert not console, console
    assert r"y & = & \displaystyle 1.00\,\mathrm{m}" in math, math
