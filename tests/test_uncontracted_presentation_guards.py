r"""Guards that were holding the page up with nothing checking them.

Found by a deliberate hunt rather than by a bug report. Fifteen guards in the
presentation core were mutated one at a time; six survived all 1558 tests, meaning
nothing in the suite could tell them from their absence. That is not the same as doing
nothing, so each survivor was then mutated again against sheets built to reach the case
it exists for, and the page was diffed.

Two changed the page:

    a reaction computed in newtons     143.68 kN   ->  143677.39 N
    every dimensionless value          0.90        ->  0.90\,

Those are the two contracts here.

One was provably unreachable and is gone: `_unit_is_the_engineers` opened with an
empty-family shortcut, and its only caller returns before the call when the family is
empty. Turned into a raised error, it never fired across the whole suite.

The remaining three - the starting candidate in `_best_in_family`, the
`own_is_family_member` that supplies it, and the near-zero return in `_display_quantity`
- change nothing on their own, because each is covered by another guard: drop the
starting candidate and the readable band still picks the right unit, widen the band and
the starting candidate still does. Mutating both together moves the page, so they are
defence in depth rather than dead weight. They are recorded here so that a future
reader does not remove one on the grounds that it is free.
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


def test_a_reaction_computed_in_newtons_is_read_in_kilonewtons(cell):
    """The readable band is what moves it, and nothing was checking the band.

    `_band_distance` prefers a magnitude in [1, 1000). Widen that band and every
    candidate ties, the stable `min` keeps the first, and a 143.68 kN reaction prints as
    `143677.39 N`. No test in the suite saw the difference.
    """
    final = _final(cell("L := 7.62*m\nw := 37710.6*N/m\nR = w*L/2\nnumeric(R)\n"))
    assert "143.68" in final and r"\mathrm{kN}" in final, final
    assert "143677" not in final, final


def test_a_load_in_newtons_per_millimetre_still_reads_small(cell):
    """The band works downward too: this one belongs in newtons, not kilonewtons."""
    final = _final(cell("L := 7.62*m\nq := 0.012*N/mm\nR = q*L/2\nnumeric(R)\n"))
    assert "45.72" in final and r"\mathrm{N}" in final, final


@pytest.mark.parametrize("source", ["phi := 0.9\n", "phi := 0.9\nnumeric(phi)\n"])
def test_a_dimensionless_value_carries_no_trailing_unit_separator(cell, source):
    r"""`_quantity_latex` returns early for a bare number. Without it every one of them
    picks up the `\,` that separates a magnitude from its unit, and the page fills with
    `0.90\,` - a number followed by a thin space and nothing.
    """
    latex = cell(source)
    assert "0.90" in latex, latex
    assert "0.90\\," not in latex, latex
