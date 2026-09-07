r"""The shape of a unit's factors does everything the term count used to.

`_unit_terms` was the heuristic behind `_unit_is_the_engineers`: it summed a unit's
exponents and kept the value's own unit when that cost no more than the family's
canonical member. It was the source of every tie in the seven-places series - `GPa*mm`
against `kN/m`, `kgf/mm^2` against `kgf/cm^2` - and #109 replaced the comparison it could
not win with a comparison of what the factors *are*.

This module pins the two jobs the count is documented as doing, and shows the shape rule
doing both, so its removal is judged on what it was for rather than on the suite going
quiet.

    #78, why the count was added   `phi*As*fy*z` printed `2.84e8 MPa*mm^3` for a
                                   `284.30 kN*m` capacity. `MPa*mm^3` is a *pressure*
                                   and a length; `kN*m` is a force and a length. The
                                   shapes differ, so the family answers.

    what the count protected       "an inertia written in mm^4 is left where the
                                   engineer put it". `mm^4` and the family's `cm^4` are
                                   both a single length, so the shapes match and the
                                   value is kept.

Measured before removing, not after: the whole suite passes with the comparison replaced
by `True`, and an exhaustive search over twenty base units in six composite forms against
all three family tables finds no unit with a family member's shape and a larger count.
That is what the dimensional equation predicts - the shape fixes which dimensions appear,
and the exponents then follow.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)

    def run(source: str) -> str:
        captured.clear()
        magic.EngMagics().eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


def test_the_capacity_that_made_the_count_necessary_still_reads_as_a_moment(cell):
    """#78. The shape rule answers it because `MPa*mm^3` reaches a moment through a
    pressure and `kN*m` reaches it through a force."""
    final = _final(cell(
        "fy := 420*MPa\nAs := 1935*mm**2\nz := 400*mm\nphi := 0.9\n"
        "phiMn = phi*As*fy*z\nnumeric(phiMn)\n"
    ))
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final
    assert "MPa" not in final, final


def test_an_inertia_in_mm4_is_still_left_where_the_engineer_put_it(cell):
    """What the count's docstring says it protects. `mm^4` and `cm^4` are each a single
    length, so the shapes match and nothing moves it."""
    final = _final(cell("I := 80e6*mm**4\nJ = 2*I/2\nnumeric(J)\n"))
    assert r"\mathrm{mm}^{4}" in final, final
    assert "cm" not in final, final


def test_the_engineers_own_spellings_are_still_kept(cell):
    """The three that carried the tie through the whole series."""
    assert r"\frac{\mathrm{kN}}{\mathrm{mm}}" in _final(
        cell("k := 10*kN/mm\nx = 2*k/2\nnumeric(x)\n")
    )
    assert r"\frac{\mathrm{tonf}}{\mathrm{m}}" in _final(
        cell("q := 2.8*tonf/m\nw = 1*q\nnumeric(w)\n")
    )
    assert r"\mathrm{kgf} \cdot \mathrm{cm}" in _final(
        cell("M := 5000*kgf*cm\nx = 2*M/2\nnumeric(x)\n")
    )


def test_the_algebras_own_spelling_is_still_refused(cell):
    final = _final(cell("E := 210*GPa\nt := 8*mm\nk = E*t\nnumeric(k)\n"))
    assert "GPa" not in final, final
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in final, final


def test_unit_terms_is_gone():
    """The point of the change. A heuristic that decides nothing is a heuristic a reader
    still has to understand before they can trust the one that does."""
    import engcalc_colab.renderer as renderer

    assert not hasattr(renderer, "_unit_terms")
