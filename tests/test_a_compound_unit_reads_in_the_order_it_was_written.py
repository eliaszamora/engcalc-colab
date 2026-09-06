r"""A compound unit keeps the order its factors were written in.

Open in `docs/project-context/NEXT.md` since RC-1, described there as "the factors of a
compound unit are ordered alphabetically - `ft·kip` where US practice writes kip-ft".

Pint sorts a compound unit's factors by name when it formats. That is right often enough
to hide that it is not a rule anyone writes by: a moment is `kN*m` and survives because
`k` precedes `m`, while the same moment in newtons prints `m*N` and an imperial one
prints `ft*kip`. No code on any shelf writes either.

The order was never lost. `_units` records it as the quantity is built - `N*m` gives
newton then meter, `m*N` the reverse - and only the formatter discarded it. Pint exposes
the sort as `registry.formatter.default_sort_func`, so keeping the order is one function
that returns its argument.

Measured rather than assumed: of every compound unit this suite renders, `m*N` and
`ft*kip` are the only two that move. The whole suite is one failing test, and it is the
one whose docstring named this as an open item.
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


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


# --- the two that move --------------------------------------------------------------

def test_a_small_moment_reads_as_newton_millimetres(cell):
    """Eurocode work is full of moments in N*mm. None of it writes mm*N."""
    final = _final(cell("F := 10*N\nr := 500*mm\nM = F*r\nnumeric(M)\n"))
    assert r"\mathrm{N} \cdot \mathrm{mm}" in final, final
    assert r"\mathrm{mm} \cdot \mathrm{N}" not in final, final


def test_an_imperial_moment_reads_as_kip_feet(cell):
    """The example NEXT.md named. US practice writes kip-ft."""
    final = _final(cell("P := 12*kip\nd := 8*ft\nM = P*d\nnumeric(M)\n"))
    assert r"\mathrm{kip} \cdot \mathrm{ft}" in final, final
    assert r"\mathrm{ft} \cdot \mathrm{kip}" not in final, final


def test_the_order_is_the_written_one_and_not_a_second_convention(cell):
    """Not "force first" - *written* first. An engineer who writes `mm*N` gets `mm*N`,
    which is the same rule that keeps a declared unit anywhere else here."""
    final = _final(cell("M := 5000*mm*N\nX = 1*M\nnumeric(X)\n"))
    assert r"\mathrm{mm} \cdot \mathrm{N}" in final, final


# --- everything else must not move ---------------------------------------------------

def test_an_ordinary_beam_moment_is_unchanged(cell):
    """`kN*m` was always right, because the written order and the alphabet agree."""
    final = _final(cell("q := 10*kN/m\nL := 6*m\nM = q*L**2/8\nnumeric(M)\n"))
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final
    assert "45.00" in final, final


def test_a_line_load_is_unchanged(cell):
    final = _final(cell("q := 10*kN/m\nw = 2*q\nnumeric(w)\n"))
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in final, final


def test_a_stress_is_unchanged(cell):
    """`25 N/mm^2` reads `25.00 MPa`, and that is the pressure family answering, not
    this change - `N/mm^2` is three unit terms against `MPa`'s one. Asserted as it is
    rather than as I first wrote it, which expected the factors and had to be corrected
    by running it."""
    final = _final(cell("s := 25*N/mm**2\nx = 1*s\nnumeric(x)\n"))
    assert r"\mathrm{MPa}" in final, final
    assert "25.00" in final, final


def test_a_factor_with_a_larger_exponent_does_not_jump_the_queue(cell):
    """`E*I` is written modulus first and reads `GPa*mm^4`, not `mm^4*GPa`.

    Asserted as an ordered string rather than as two `in` checks. Written the loose way
    first, it let a mutation that sorted by exponent through the whole contract set:
    both factors were present in either order, and presence was all it asked.
    """
    final = _final(cell("E := 200*GPa\nI := 80e6*mm**4\nk = E*I\nnumeric(k)\n"))
    assert r"\mathrm{GPa} \cdot \mathrm{mm}^{4}" in final, final


def test_a_declared_unit_is_still_the_engineers(cell):
    """The rule this joins rather than competes with."""
    final = _final(cell("q := 2.8*tonf/m\nw = 1*q\nnumeric(w)\n"))
    assert r"\frac{\mathrm{tonf}}{\mathrm{m}}" in final, final
