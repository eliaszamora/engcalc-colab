r"""`keep` holds through a numeric coefficient, which is where every deflection formula
puts one.

The engineer's beam memoria, the line he wrote and the line the page printed:

    written:  keep delta = 5*q_s*L^4/(384*E*I)
    printed:  delta = L⁴(5 qD + 5 qL) / (32 b h³ E)

`q_s` and `I` are both `keep` names and both are gone. That is the whole of what `keep`
exists to prevent, and it fails on the most ordinary shape in structural engineering -
`5 q L⁴ / (384 E I)`, `q L² / 8`, `P L³ / (48 E I)` all lead with a coefficient.

Isolated by bisection, and the trigger is narrow:

    q_s/I                  keeps its names
    q_s*L^4/(384*E*I)      keeps its names
    5*q_s/I                loses them
    5*q_s*L^4/(384*E*I)    loses them

**The written form is built correctly.** `_WrittenFormEvaluator` produces `5*q_s/I`; it
is the *verification* that throws it away. SymPy distributes a Number over an Add as it
builds - `5*(qD + qL)` becomes `5*qD + 5*qL` - so the evaluated expression beside the
written one is the same value in a different shape, and `_agrees_with` ends on
`difference == 0`, which is a structural test:

    60*(qD + qL)/(b*h³) - (60*qD + 60*qL)/(b*h³)  ==  0   ->  False

The fix is the one this file already made for matrices in #128, applied to the scalar
branch it was never extended to: `cancel` normalises a rational function and answers the
question the structural test cannot. It runs only where the answer was about to be "no",
so it costs nothing on a formula that already verified, and it is a normalisation rather
than a proof search - a genuinely wrong written form still cancels to something non-zero,
which is what keeps this a verification.
"""

import pytest

import engcalc_colab.magic as magic


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


BEAM = (
    "L := 6.00*m\n"
    "b := 300*mm\n"
    "h := 600*mm\n"
    "E := 23500*MPa\n"
    "qD := 18*kN/m\n"
    "qL := 12*kN/m\n"
    "keep I = b*h^3/12\n"
    "keep q_s = qD + qL\n"
)


def formula_for(page: str, name: str) -> str:
    r"""The right-hand side of one row of the aligned block.

    Scoped to the row on purpose. A first draft asked whether `q_{s}` appeared anywhere
    on the page, and every one of these passed before the fix - because `keep q_s = qD +
    qL` prints `q_s` on its own definition line two rows above. The question is what the
    *deflection* row says.
    """
    for row in page.split(r"\\[8pt]"):
        collapsed = " ".join(row.split())
        head, separator, tail = collapsed.partition("&")
        if not separator:
            continue
        if name in head:
            return tail.split("&")[-1].replace(r"\end{array}", "").strip()
    raise AssertionError(f"no row for {name!r} in {page}")


def test_the_deflection_formula_reads_as_it_was_written(cell):
    """His line, and the one this file exists for."""
    page = cell(BEAM + "keep delta = 5*q_s*L^4/(384*E*I)\n")
    written = formula_for(page, "delta")

    assert "q_{s}" in written, written
    assert "384" in written, written
    assert r"\mathrm{qD}" not in written, written
    assert "I" in written.replace(r"\displaystyle", ""), written


def test_a_coefficient_on_a_kept_sum_is_enough_to_break_it(cell):
    """The narrowest form of the same defect, so a fix aimed at the beam formula alone
    would not pass: one coefficient, one kept sum, one kept product."""
    page = cell(BEAM + "keep W = 5*q_s/I\n")
    written = formula_for(page, " W ")

    assert "q_{s}" in written, written
    assert r"\mathrm{qD}" not in written, written
    assert "h^{3}" not in written, written


def test_the_value_is_untouched(cell):
    """Showing a formula as written must not change what it computes."""
    page = cell(BEAM + "keep delta = 5*q_s*L^4/(384*E*I)\nnumeric(delta)\n")
    assert "3.99" in page or "0.40" in page, page


# --- what must not move ---------------------------------------------------------------


def test_a_formula_with_no_coefficient_still_keeps_its_names(cell):
    """These already worked, and the fix is on the branch that had said no - so if any
    of them changed, something wider happened than the defect."""
    for expression in ("q_s/I", "q_s*L^4/(384*E*I)", "q_s/(E*I)", "q_s + I"):
        page = cell(BEAM + f"keep W = {expression}\n")
        written = formula_for(page, " W ")
        assert "q_{s}" in written, (expression, written)
        assert r"\mathrm{qD}" not in written, (expression, written)


def test_a_sheet_with_no_keep_is_unchanged(cell):
    """`keep` is opt-in and the written form is gated on it. A sheet without one must
    render exactly as it always has, expanded."""
    page = cell(
        "L := 6.00*m\nqD := 18*kN/m\nqL := 12*kN/m\nq_s = qD + qL\nW = 5*q_s\n"
    )
    assert r"\mathrm{qD}" in page, page


def test_a_written_form_that_is_wrong_is_still_refused():
    """`cancel` normalises; it does not agree to anything put in front of it. Without
    this the fix would be a rubber stamp rather than a verification."""
    import sympy as sp

    from engcalc_colab.engine import _agrees_with

    qD, qL, b, h = sp.symbols("qD qL b h")
    q_s, I = sp.symbols("q_s I")
    expansions = {q_s: qD + qL, I: b * h**3 / 12}

    honest = 5 * q_s / I
    value = 60 * (qD + qL) / (b * h**3)
    assert _agrees_with(honest, value, expansions) is True

    # The same shape with the coefficient wrong, which is the mistake worth catching:
    # a formula the reader cannot check is the defect, and a formula that is wrong is
    # worse than the defect.
    assert _agrees_with(6 * q_s / I, value, expansions) is False
    assert _agrees_with(5 * q_s * b / I, value, expansions) is False
