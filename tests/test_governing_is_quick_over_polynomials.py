r"""`governing` over six quadratic combinations answers in seconds, not in a minute.

    governing(U1(x), U2(x), U3(x), U4(x), U5(x), U6(x), x, 0, L)

The frame's beam, designed (`tools/portico_diseno.eng`): six combinations of three load
cases, each a quadratic in x. `governing` equated them pairwise *symbolically* - fifteen
closed forms in `M_2D`, `V_2E`, `w_L` with nested square roots, each simplified twice -
and took 54 s, so the sheet used `envelope` instead. Found on 2026-09-24; he asked for it
to be dealt with with the other pending points (*"abarques todos esos puntos pendientes"*).

What `governing` keeps of a crossing is where it is, as a number: the block reads
`42.25 cm to 195.20 cm   U3(x)`. So when both responses are polynomials in the variable
once the sheet's values are put in, a crossing is a real root of their difference, found
numerically - exact to the precision the page prints, and never on a sampling grid, which
was the point of building `governing` on crossovers at all. Anything else - a `piecewise`,
a Macaulay bracket - keeps the exact path it had.

The boundaries below are the exact path's own, recorded before the change.
"""

import contextlib
import io
import pathlib
import time

import matplotlib
import pytest

import engcalc_colab.engine as engine_module
import engcalc_colab.magic as magic
from engcalc_colab.parser import parse_cell

matplotlib.use("Agg")

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOVERNING = "governing(U1(x), U2(x), U3(x), U4(x), U5(x), U6(x), x, 0, L)"
# The exact path's answer, in cm, recorded on 0.35.0 (55.9 s).
EXACT = [
    ("U5(x)", 0.0, 42.25032301466644),
    ("U3(x)", 42.25032301466644, 195.19910392332318),
    ("U2(x)", 195.19910392332318, 405.49437219141106),
    ("U4(x)", 405.49437219141106, 557.7496769853335),
    ("U6(x)", 557.7496769853335, 600.0),
]


@pytest.fixture(scope="module")
def designed():
    magics = magic.EngMagics()
    design = (ROOT / "tools" / "portico_diseno.eng").read_text(encoding="utf-8")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(magic, "display", lambda *_: None)
        with contextlib.redirect_stdout(io.StringIO()):
            magics.eng_units("kgf")
            magics.eng("", (ROOT / "tools" / "portico_matricial.eng").read_text(encoding="utf-8"))
            magics.eng("", design.split("### Momentos de diseño")[0])
    return magics.engine


def governing(engine, line=GOVERNING):
    (statement,) = parse_cell(line)
    return engine.evaluate(statement)


def test_the_boundaries_are_the_exact_ones(designed):
    started = time.perf_counter()
    result = governing(designed)
    elapsed = time.perf_counter() - started
    found = [
        (segment.label, segment.lower_quantity.to("cm").magnitude, segment.upper_quantity.to("cm").magnitude)
        for segment in result.intervals
    ]
    assert [label for label, *_ in found] == [label for label, *_ in EXACT]
    for (_, lower, upper), (_, exact_lower, exact_upper) in zip(found, EXACT):
        assert lower == pytest.approx(exact_lower, rel=1e-9, abs=1e-9)
        assert upper == pytest.approx(exact_upper, rel=1e-9, abs=1e-9)
    assert elapsed < 20, f"governing took {elapsed:.1f} s"


def test_polynomials_are_not_solved_symbolically(designed, monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("a polynomial crossing was solved symbolically")

    monkeypatch.setattr(engine_module, "solve_intersections_exact", refuse)
    assert len(governing(designed).intervals) == 5


def test_a_piecewise_response_keeps_the_exact_path(monkeypatch):
    calls = []
    original = engine_module.solve_intersections_exact

    def spy(*args, **kwargs):
        calls.append(kwargs.get("left_label"))
        return original(*args, **kwargs)

    monkeypatch.setattr(engine_module, "solve_intersections_exact", spy)
    magics = magic.EngMagics()
    shown = []
    monkeypatch.setattr(magic, "display", shown.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magics.eng(
            "",
            "L := 6*m\n"
            "A(x) = piecewise(2*kN*m, x < 3*m, 5*kN*m)\n"
            "B(x) = 1*kN*x\n"
            "governing(A(x), B(x), x, 0, L)\n",
        )
    assert not console.getvalue(), console.getvalue()
    assert calls, "the piecewise pair did not reach the exact path"


def test_two_lines_cross_where_they_should():
    magics = magic.EngMagics()
    shown = []
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(magic, "display", shown.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magics.eng(
                "",
                "L := 6*m\nq := 2*kN/m\nP := 3*kN\n"
                "A(x) = q*x\nB(x) = P + 0*x\nC(x) = q*x^2/(4*m) - 1*kN\n"
                "governing(A(x), B(x), C(x), x, 0, L)\n",
            )
    assert not console.getvalue(), console.getvalue()
    page = " ".join(str(item.data) for item in shown)
    # B until A reaches P at 1.5 m; A until C overtakes it at 2 + sqrt(6) = 4.45 m.
    assert r"1.50\,\mathrm{m}" in page and r"4.45\,\mathrm{m}" in page, page


def test_a_macaulay_response_keeps_the_exact_path(monkeypatch):
    calls = []
    original = engine_module.solve_intersections_exact

    def spy(*args, **kwargs):
        calls.append(kwargs.get("left_label"))
        return original(*args, **kwargs)

    monkeypatch.setattr(engine_module, "solve_intersections_exact", spy)
    monkeypatch.setattr(magic, "display", lambda *_: None)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng(
            "",
            "L := 6*m\nP := 10*kN\n"
            "A(x) = P*<x - 2*m>^1\n"
            "B(x) = 5*kN*x\n"
            "governing(A(x), B(x), x, 0, L)\n",
        )
    assert not console.getvalue(), console.getvalue()
    assert calls, "the Macaulay pair did not reach the exact path"
