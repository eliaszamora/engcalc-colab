r"""`keep` marks a name that a later formula shows instead of expanding.

RC-3, the one finding of the external reinforced-concrete trial that was not a bug. An
engineer writes

    keep d = h - cover - db_st - db/2
    keep a = As*fy/(0.85*fc*b)
    phiMn = phi*As*fy*(d - a/2)

and wants the memoria to read `phiMn = phi As fy (d - a/2)`. Without the marker the
symbolic layer substitutes each definition's expression where the name is used, so the
capacity comes out in primitives - `cover`, `db_st`, `h`, `b`, `fc` - and the formula an
engineer would check against the code is not on the page.

Why a marker rather than making every definition a barrier, which is the semantics
anyone would expect. Measured, on the tests shaped like memorias: making them all
barriers moves **24 of 131**, including all eighteen worked exercises and the hyperstatic
validation case. Every one of those pages would have to be read and judged one at a time.
`case` and `combo` (#71) already chose a declaration keyword for the same reason, and
this follows them.

What `keep` does *not* change: the value. `namespace` still holds the expanded
expression and everything computes with it, exactly as `combo` keeps its written terms
beside an expanded expression for everything else to use. The barrier is presentation,
which is why it can be opt-in without dividing the language in two.
"""

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.errors import EngSyntaxError
from engcalc_colab.parser import parse_cell


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> str:
        captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


BEAM = (
    "b := 300*mm\n"
    "h := 500*mm\n"
    "cover := 40*mm\n"
    "db_st := 10*mm\n"
    "db := 20*mm\n"
    "fc := 25*MPa\n"
    "fy := 420*MPa\n"
    "As := 1935*mm**2\n"
    "phi := 0.9\n"
)

KEPT = BEAM + "keep d = h - cover - db_st - db/2\nkeep a = As*fy/(0.85*fc*b)\n"


# --- the marker ------------------------------------------------------------------

def test_keep_parses_as_a_declaration():
    statements = parse_cell("keep d = h - cover\n")
    assert statements[0].declaration == "keep"
    assert statements[0].target == "d"


def test_keep_takes_a_plain_name():
    with pytest.raises(EngSyntaxError) as excinfo:
        parse_cell("keep d(x) = 2*x\n")
    assert "plain name" in str(excinfo.value), str(excinfo.value)


# --- the page ---------------------------------------------------------------------

def test_a_formula_shows_the_names_it_was_written_with(cell):
    """The finding. Without `keep` this reads in `cover`, `db_st`, `h`, `b` and `fc`."""
    latex = cell(KEPT + "phiMn = phi*As*fy*(d - a/2)\n")
    assert r"\mathrm{cover}" not in latex.split("phiMn")[-1], latex
    assert "d" in latex, latex
    assert "a" in latex, latex


def test_the_evaluation_shows_the_same_formula_and_the_kept_values(cell):
    """Both stages or neither. If the definition shows `d` and the evaluation below it
    shows `cover` and `h`, the page contradicts itself - and #86's rule that a formula
    is not restated by its own evaluation stops firing, so the reader gets both."""
    latex = cell(KEPT + "phiMn = phi*As*fy*(d - a/2)\nnumeric(phiMn)\n")
    body = latex.split("phiMn")[-1]
    assert r"\mathrm{cover}" not in body, latex
    # d = 500 - 40 - 10 - 10 = 440 mm, and a = 1935 x 420 / (0.85 x 25 x 300) = 127.48 mm
    assert "440.00" in latex, latex
    assert "127.48" in latex, latex


def test_a_kept_name_reads_as_a_memoria_is_written(cell):
    """The shape the whole thing is for, on a formula narrow enough to show it whole:

        z = 2 a
          = 2 (127.48 mm)
          = 254.96 mm

    Without the marker the middle line reads `2.35 fy As / (b fc)` with every primitive
    substituted into it, which is the same number and not a step anyone writes.

    A wide formula still has its substitution split into additive terms by the wrapping
    path - `phi*As*fy*(d - a/2)` does - but that is width and not `keep`: a wide formula
    with no kept name in it does the same, and a narrow one keeps its shape either way.
    """
    latex = cell(
        "b := 300*mm\nfc := 25*MPa\nfy := 420*MPa\nAs := 1935*mm**2\n"
        "keep a = As*fy/(0.85*fc*b)\n"
        "z = 2*a\n"
        "numeric(z)\n"
    )
    assert r"\displaystyle 2 a" in latex, latex
    assert r"2 \left(127.48\,\mathrm{mm}\right)" in latex, latex
    assert "254.96" in latex, latex


def test_the_number_is_unchanged_by_the_marker(cell):
    """`keep` is presentation. phi As fy (d - a/2) with d = 440 mm and a = 127.48 mm is
    0.9 x 1935 x 420 x (440 - 63.74) = 275.21 kN*m either way."""
    without = _final(cell(
        BEAM
        + "d = h - cover - db_st - db/2\na = As*fy/(0.85*fc*b)\n"
        + "phiMn = phi*As*fy*(d - a/2)\nnumeric(phiMn)\n"
    ))
    with_keep = _final(cell(KEPT + "phiMn = phi*As*fy*(d - a/2)\nnumeric(phiMn)\n"))
    assert "275.21" in without, without
    assert "275.21" in with_keep, with_keep


def test_a_kept_name_still_evaluates_on_its_own(cell):
    final = _final(cell(KEPT + "numeric(d)\n"))
    assert "440.00" in final, final
    assert r"\mathrm{mm}" in final, final


def test_a_kept_definition_shows_its_own_formula(cell):
    """The barrier is for the names *inside* a later formula. `keep d = ...` still shows
    what `d` is, on its own line, or the reader has no way to know."""
    latex = cell(KEPT)
    assert r"\mathrm{cover}" in latex, latex
    assert "h" in latex, latex


# --- what must not move -----------------------------------------------------------

def test_an_unmarked_definition_is_expanded_as_before(cell):
    """The whole reason this is opt-in. Twenty-four of a hundred and thirty-one
    memoria-shaped tests move if every definition becomes a barrier."""
    latex = cell(
        BEAM + "d = h - cover - db_st - db/2\nphiMn = phi*As*fy*d\n"
    )
    assert r"\mathrm{cover}" in latex.split("phiMn")[-1], latex


def test_a_reset_forgets_what_was_kept(monkeypatch):
    """`%eng_reset` clears the sheet, and a name that was kept in the sheet before it
    must not go on being kept. Nothing else was checking this: the reset line survived
    every mutation until this contract existed, and a stale barrier is worse than none -
    the page would show a name the reader has no definition for.
    """
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    magics.eng("", "b := 300*mm\nkeep w = 2*b\n")
    assert magics.engine.kept_names == {"w"}
    assert sorted(magics.engine.written_namespace) == ["w"]

    magics.eng_reset("")
    assert magics.engine.kept_names == set()
    assert magics.engine.written_namespace == {}

    captured.clear()
    magics.eng("", "b := 300*mm\nw = 2*b\nz = 3*w\n")
    latex = "".join(getattr(obj, "data", "") for obj in captured)
    # `w` is an ordinary definition again, so `z` shows what it stands for.
    assert r"\displaystyle z & = & \displaystyle 6 b" in latex, latex


def test_keep_does_not_disturb_solve(cell):
    """Everything downstream keeps using the expanded expression, so an algebraic step
    over a kept name behaves as it always did."""
    latex = cell(
        "q := 10*kN/m\nL := 6*m\n"
        "keep Ra = q*L/2\n"
        "M(x) = Ra*x - q*x**2/2\n"
        "numeric(subs(M(x), x, L/2))\n"
    )
    assert "45.00" in latex, latex
