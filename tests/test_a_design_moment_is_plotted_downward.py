r"""`Md(x)`, `Mu(x)`, `Mn(x)`: a moment by another name is still plotted positive-down.

Whether a figure is a moment - and so drawn with positive values downward, the
convention the project keeps - was read off the name alone: `M(`, `M_b(`, `M2(`. The beam
sweep in `tools/formas.eng` is `Md(x)`, a design moment, and it was drawn upward; so
would a factored `Mu(x)` or a nominal `Mn(x)` be, which are the names a design sheet uses.

A letter after the `M` could as well begin `Mass(x)`, so for those names the values
decide: a moment is a force times a length. The names the rule already knew are left
exactly as they were, with units or without.
"""

import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib.figure  # noqa: E402

import engcalc_colab.magic as magic  # noqa: E402
from engcalc_colab.engine import EngineeringEngine  # noqa: E402
from engcalc_colab.parser import parse_cell  # noqa: E402


def plot_of(source: str):
    engine = EngineeringEngine()
    results = [engine.evaluate(statement) for statement in parse_cell(source)]
    return results[-1]


SPAN = "L := 6*m\nq := 20*kN/m\nP2 := 200*kN\n"


@pytest.mark.parametrize("name", ["Md", "Mu", "Mn", "Mmax", "M_u", "M"])
def test_a_moment_by_any_of_its_names_is_a_moment(name):
    result = plot_of(SPAN + f"{name}(x) = q*x*(L - x)/2\nplot({name}(x), x, 0, L)\n")
    assert all(series.is_moment for series in result.series), name


def test_a_sweep_of_a_design_moment_is_a_moment():
    result = plot_of(
        SPAN + "Md(x) = P2*x*(L - x)/L\nplot(Md(x), x, 0, L, P2=[200*kN, 400*kN])\n"
    )
    assert all(series.is_moment for series in result.series)


def test_a_name_that_only_starts_with_m_is_not_a_moment():
    result = plot_of("L := 6*m\nrho := 2400*kg/m^3\nMass(x) = rho*x*(1*m^2)\nplot(Mass(x), x, 0, L)\n")
    assert not any(series.is_moment for series in result.series)


def test_a_bare_m_without_units_is_still_a_moment_as_before():
    result = plot_of("M(x) = x*(6 - x)\nplot(M(x), x, 0, 6)\n")
    assert all(series.is_moment for series in result.series)


def test_the_design_moment_is_drawn_positive_down(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", SPAN + "Mu(x) = q*x*(L - x)/2\nplot(Mu(x), x, 0, L)\n")
    (figure,) = [o for o in captured if isinstance(o, matplotlib.figure.Figure)]
    assert figure.axes[0].yaxis_inverted()


CASES = (
    "L := 6*m\nqD := 18*kN/m\nqL := 12*kN/m\n"
    "M_D(x) = qD*x*(L - x)/2\nM_L(x) = qL*x*(L - x)/2\n"
    "V_D(x) = qD*(L/2 - x)\nV_L(x) = qL*(L/2 - x)\n"
    "case D = M_D(x)\ncase Lv = M_L(x)\ncase SD = V_D(x)\ncase SL = V_L(x)\n"
    "combo U1 = 1.2*D + 1.6*Lv\ncombo U2 = 1.4*D\ncombo W1 = 1.2*SD + 1.6*SL\n"
)


def test_a_combination_of_moment_cases_is_a_moment():
    """`viga.eng` compares `U1(x)` and `U2(x)`, made of `M_D` and `M_L`: moments."""
    result = plot_of(CASES + "plot(U1(x), U2(x), x, 0, L)\n")
    assert all(series.is_moment for series in result.series)


def test_a_combination_of_shear_cases_is_not():
    result = plot_of(CASES + "plot(W1(x), x, 0, L)\n")
    assert not any(series.is_moment for series in result.series)


def test_the_envelope_of_moment_combinations_is_a_moment():
    result = plot_of(CASES + "envelope(U1(x), U2(x), x, 0, L)\n")
    assert all(series.is_moment for series in result.series)
