r"""A value with no real result says so, in one line, and the rows before it stay.

    a := 1
    b := 2
    c := 5
    D = sqrt(b^2 - 4*a*c)
    numeric(D)           the square root of -16 has no real value

Python answers `(-16) ** 0.5` with a complex number and Pint carries it on. The value was
stored without a word, and the renderer, which prints real numbers, raised a `TypeError`
on it: Colab showed a traceback in place of the cell, and not one row of the cell - the
three definitions above included - reached the page. Twelve paths led there, every one
through a power: a root or a fractional power, written with `:=`, asked for with `numeric`
or `result`, inside a function called at a point, a matrix, a `table` or a `plot`. Found on
2026-09-23 comparing EngCalc with Calcpad, which has a complex mode; EngCalc works in real
numbers, and the fix is to say that where the value is made.

`log`, `asin` and `acos` outside their domain already gave one line, but Python's own:
`math domain error` on the 3.12 Colab runs, `expected a positive input, got -1.0` on 3.14.
They say the same thing now on every version.

What is real stays real: an even power of a negative number, the root of its square, a
negative number to an integer power however it is written, and each function at the edge
of its domain.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def magics(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    engine = magic.EngMagics()
    engine.captured = captured
    return engine


def run(magics, source: str) -> str:
    magics.captured.clear()
    magics.eng("", source)
    return "".join(getattr(obj, "data", "") for obj in magics.captured)


REAL = "EngCalc works in real numbers"
POSITIVE = "its argument must be positive"
UNIT_RANGE = "its argument must lie between -1 and 1"

# Each of the twelve raised TypeError before the change: measured through this magic.
NO_REAL_POWER = [
    ("L := 6*m\nz := sqrt(-4)\n", "line 2: the square root of -4 has no real value"),
    ("z := sqrt(-4)\nnumeric(z)\n", "line 1: the square root of -4 has no real value"),
    ("z := (-4)^0.5\n", "line 1: the square root of -4 has no real value"),
    ("z := (-8)^(1/3)\n", "line 1: -8 raised to a fractional power has no real value"),
    ("x := -2*m\nz := sqrt(x)\n", "line 2: the square root of -2 m has no real value"),
    (
        "a := 1\nb := 2\nc := 5\nD = sqrt(b^2 - 4*a*c)\nnumeric(D)\n",
        "line 5: the square root of -16 has no real value",
    ),
    (
        "a := 1\nb := 2\nc := 5\nD = sqrt(b^2 - 4*a*c)\nresult(D)\n",
        "line 5: the square root of -16 has no real value",
    ),
    ("f(x) = sqrt(x)\nnumeric(f(-4))\n", "line 2: the square root of -4 has no real value"),
    (
        "x0 := -4\nf(x) = sqrt(x)\nnumeric(f(x0))\n",
        "line 3: the square root of -4 has no real value",
    ),
    ("x := -8\ny = x^(1/3)\nnumeric(y)\n", "line 3: -8 raised to a fractional power has no real value"),
    # A matrix already names the entry, and keeps doing so in front of the new words.
    (
        "a := -4\nA = [sqrt(a), 1; 1, 2]\nnumeric(A)\n",
        "line 3: matrix numeric evaluation failed at [1,1]: the square root of -4 has no real value",
    ),
    ("f(x) = sqrt(x)\ntable(f(x), x, -1, 1, 3)\n", "line 2: the square root of -1 has no real value"),
    ("f(x) = sqrt(x)\nplot(f(x), x, -1, 1)\n", "line 2: the square root of -1 has no real value"),
]


@pytest.mark.parametrize(("source", "said"), NO_REAL_POWER)
def test_a_power_with_no_real_value_says_so_in_one_line(magics, capsys, source, said):
    run(magics, source)
    printed = capsys.readouterr().out
    assert f"engcalc: {said}; {REAL}" in printed, printed
    assert printed.count("engcalc:") == 1, printed


def test_the_rows_before_it_are_shown(magics, capsys):
    """The part of the defect worse than the traceback: the definitions above the line that
    failed were lost with it, so the page showed nothing at all."""
    page = run(magics, "a := 1\nb := 2\nc := 5\nD = sqrt(b^2 - 4*a*c)\nnumeric(D)\n")
    assert "the square root of -16" in capsys.readouterr().out
    for row in (r"a & = & \displaystyle 1.00", r"c & = & \displaystyle 5.00", r"D & = &"):
        assert row in page, page


def test_the_magnitude_of_a_root_that_has_no_value_is_not_its_value(magics, capsys):
    """`abs(sqrt(-4))` drew `2.00`: the modulus of `2i`, a number this page cannot have
    produced. The root is refused before `abs` sees it."""
    page = run(magics, "z := abs(sqrt(-4))\n")
    assert f"engcalc: line 1: the square root of -4 has no real value; {REAL}" in (
        capsys.readouterr().out
    )
    assert "2.00" not in page, page


OUT_OF_DOMAIN = [
    ("z := log(-1)\n", f"line 1: the logarithm of -1 has no real value; {POSITIVE}"),
    ("z := log(0)\n", f"line 1: the logarithm of 0 has no real value; {POSITIVE}"),
    ("z := asin(2)\n", f"line 1: asin of 2 has no real value; {UNIT_RANGE}"),
    ("z := acos(-1.5)\n", f"line 1: acos of -1.5 has no real value; {UNIT_RANGE}"),
    ("x := -1\ny = log(x)\nnumeric(y)\n", f"line 3: the logarithm of -1 has no real value; {POSITIVE}"),
    ("x := 2\ny = asin(x)\nnumeric(y)\n", f"line 3: asin of 2 has no real value; {UNIT_RANGE}"),
]


@pytest.mark.parametrize(("source", "said"), OUT_OF_DOMAIN)
def test_a_function_outside_its_domain_says_which(magics, capsys, source, said):
    run(magics, source)
    printed = capsys.readouterr().out
    assert f"engcalc: {said}" in printed, printed
    assert "math domain error" not in printed and "expected a" not in printed, printed


def test_a_value_just_past_the_edge_is_quoted_in_full(magics, capsys):
    """Four figures would print `acos of 1`, which is in range; the value that failed is
    the one a rounding left just outside it, and the message has to show that."""
    run(magics, "a := 0.1 + 0.2\nb := 0.3\nt := acos(a/b)\n")
    printed = capsys.readouterr().out
    assert "engcalc: line 3: acos of 1.0000000000000002 has no real value" in printed, printed


STAYS_REAL = [
    ("x := -3\ny = x^2\nnumeric(y)\n", r"\displaystyle 9.00"),
    ("x := -3\ny = sqrt(x^2)\nnumeric(y)\n", r"\displaystyle 3.00"),
    ("z := (-2)^3\n", r"\displaystyle -8.00"),
    ("z := (-2)^(-1)\n", r"\displaystyle -0.50"),
    ("z := (-4)^2.0\n", r"\displaystyle 16.00"),
    ("z := sqrt(0)\n", r"z & = & \displaystyle 0.00"),
    ("z := asin(1)\n", r"1.57\,\mathrm{rad}"),
    ("z := acos(-1)\n", r"3.14\,\mathrm{rad}"),
    ("z := log(1)\n", r"z & = & \displaystyle 0.00"),
    ("f(x) = sqrt(x) - 1\nroots(f(x), x, -1, 4)\n", r"\text{root}"),
]


@pytest.mark.parametrize(("source", "shown"), STAYS_REAL)
def test_what_has_a_real_value_keeps_it(magics, capsys, source, shown):
    page = run(magics, source)
    assert "engcalc:" not in capsys.readouterr().out
    assert shown in page, page
