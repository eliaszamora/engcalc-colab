r"""`extrema` reads its function across the whole domain, or says why it cannot.

    f(x) = sqrt(x)
    extrema(f(x), x, -1, 4)       x = 4 · value = 2 · boundary, global max, global min

    f(x) = 1/x
    extrema(f(x), x, 0, 2)        x = 2 · value = 1/2 · boundary, global max, global min

Both answers are wrong, and for one reason: a domain end the analysis could not evaluate
was dropped in silence, and the global roles were then handed out among what was left.
`sqrt(-1)` has no real value, so x = -1 went, and with it the minimum at x = 0 where the
root starts; `1/0` is a singularity, so x = 0 went, and with it the fact that `1/x` grows
without bound there. Found on 2026-09-23, reported to him as the one open item that gives
a wrong answer rather than no answer.

The two halves are not the same fix. A function with no real value somewhere in the
domain is refused, in one line, the way `plot` and `table` already refuse it since
0.31.18 - EngCalc works in real numbers, and a domain is the reader's statement that the
function lives on all of it. A singularity at a domain end is what a singularity inside
the domain already was: the analysis takes its one-sided limit and says *unbounded above*
or *below*, and claims no global extreme on that side.
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


REFUSAL = "extrema reads its function across the whole domain, and at x = "


@pytest.mark.parametrize(
    ("source", "where"),
    [
        ("f(x) = sqrt(x)\nextrema(f(x), x, -1, 4)\n", "-1 the square root of -1 has no real value"),
        # Real at both ends and nowhere between -1 and 1: no end tells.
        ("f(x) = sqrt(x^2 - 1)\nextrema(f(x), x, -2, 2)\n", "-0.98 the square root of"),
        ("f(x) = log(x)\nextrema(f(x), x, -1, 2)\n", "-1 the logarithm of -1 has no real value"),
        # An exponent known only by its value: SymPy cannot say it is an integer, which is
        # not the same as saying it is not one.
        ("n := 0.5\nf(x) = x^n\nextrema(f(x), x, -1, 4)\n", "-1 the square root of -1 has no real value"),
    ],
)
def test_a_function_with_no_real_value_in_the_domain_is_refused(magics, capsys, source, where):
    run(magics, source)
    printed = capsys.readouterr().out
    assert f"{REFUSAL}{where}" in printed, printed
    assert printed.startswith("engcalc: line "), printed
    assert printed.count("engcalc:") == 1, printed


def test_a_root_that_is_singular_at_an_end_is_unbounded_not_refused(magics, capsys):
    """`1/sqrt(x)` is real on all of [0, 4] but has no value at 0: the guard that looks for
    values with no real result must pass over a point that is merely singular, and leave
    it to the limit."""
    page = run(magics, "f(x) = 1/sqrt(x)\nextrema(f(x), x, 0, 4)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\text{unbounded above}" in page, page
    assert r"\text{boundary, global min}" in page, page


def test_a_singular_end_is_unbounded_and_holds_no_global_extreme(magics, capsys):
    page = run(magics, "f(x) = 1/x\nextrema(f(x), x, 0, 2)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\text{unbounded above}" in page, page
    assert r"\text{unbounded below}" not in page, page
    assert "global max" not in page, page
    assert r"\text{boundary, global min}" in page, page


def test_a_singular_upper_end_is_read_from_below(magics, capsys):
    """The other side: `1/x` on [-2, 0] falls without bound as x reaches 0 from below."""
    page = run(magics, "f(x) = 1/x\nextrema(f(x), x, -2, 0)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\text{unbounded below}" in page, page
    assert r"\text{unbounded above}" not in page, page
    assert "global min" not in page, page
    assert r"\text{boundary, global max}" in page, page


@pytest.mark.parametrize(
    ("source", "rows"),
    [
        (
            "f(x) = sqrt(x)\nextrema(f(x), x, 0, 4)\n",
            [r"\text{boundary, global min}", r"\text{boundary, global max}"],
        ),
        (
            "f(x) = 1/x\nextrema(f(x), x, -1, 2)\n",
            [r"\text{unbounded above}", r"\text{unbounded below}"],
        ),
        (
            "f(x) = x^2\nextrema(f(x), x, -1, 2)\n",
            [r"\text{local min, global min}", r"\text{boundary, global max}"],
        ),
        (
            "L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L - x)/2\nextrema(M(x), x, 0, L)\n",
            [r"\text{local max, global max}"],
        ),
    ],
)
def test_what_was_answered_right_is_answered_the_same(magics, capsys, source, rows):
    page = run(magics, source)
    assert "engcalc:" not in capsys.readouterr().out
    for row in rows:
        assert row in page, page
