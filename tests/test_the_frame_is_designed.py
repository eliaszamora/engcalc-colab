r"""The portal frame's beam, designed: `tools/portico_diseno.eng` after `portico_matricial.eng`.

Three load cases solved at once (`d_c := solve(K, F_c)` with one column per case), six
ACI 318-19 combinations, the design moments, the steel and the stirrups. The numbers are
checked against an independent NumPy solution of the same frame; what this file guards is
that the sheet goes on computing them, and saying so without a notice.
"""

import contextlib
import io
import pathlib

import pytest

import engcalc_colab.magic as magic

TOOLS = pathlib.Path(__file__).parent.parent / "tools"


@pytest.fixture(scope="module")
def designed():
    captured = []
    original = magic.display
    magic.display = captured.append
    magics = magic.EngMagics()
    console = io.StringIO()
    try:
        with contextlib.redirect_stdout(console):
            magics.eng_units("kgf")
            magics.eng("", (TOOLS / "portico_matricial.eng").read_text(encoding="utf-8"))
            magics.eng("", (TOOLS / "portico_diseno.eng").read_text(encoding="utf-8"))
    finally:
        magic.display = original
    return magics, console.getvalue(), None


def quantity(magics, name, unit):
    engine = magics.engine if hasattr(magics, "engine") else None
    assert engine is not None
    context = engine.numeric_context
    if name in context.values:
        return float(context.values[name].to(unit).magnitude)
    _subs, value = context.evaluate_symbolic(engine.resolve_name(name))
    return float(value.to(unit).magnitude)


def test_the_design_runs_without_a_notice(designed):
    _magics, console, _values = designed
    assert not [line for line in console.splitlines() if not line.startswith("engcalc units")], console


@pytest.mark.parametrize(
    "name, unit, expected",
    [
        ("Mu_pos", "kgf*cm", 876940.63),
        ("Mu_2", "kgf*cm", -553507.27),
        ("Mu_3", "kgf*cm", -552587.34),
        ("As_min", "cm^2", 4.40),
        ("As_pos", "cm^2", 5.546829),
        ("As_2", "cm^2", 4.40),
        ("Vu", "kgf", 7920.00),
        ("V_c", "kgf", 10138.167),
        ("s_e", "cm", 22.00),
    ],
)
def test_the_design_matches_numpy(designed, name, unit, expected):
    magics, _console, _values = designed
    assert quantity(magics, name, unit) == pytest.approx(expected, rel=1e-4)
