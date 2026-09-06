r"""A number reduced to one digit or none gets its figures back.

The engineer read the period of his braced frame and asked:

    "¿por qué lo dejaste en 0.02s? si no tengo problemas en que hayan varios decimales
     con los segundos 0.00002 sería lo máximo que acepto."

`T = 0.016756 s` rendered `0.02 s`. The cause is not the unit - the time family is `s`
and nothing else, deliberately - but `precision`, which counts *decimal places*. One
such count has to serve a sheet spanning seven orders of magnitude, and it cannot:

    precision=2                     precision=6
    I_c   0.00       destroyed      0.002278
    T     0.02       destroyed      0.016756
    k_col 517195.95  fine           517195.945000   unreadable
    omega 374.98     fine           374.984660      unreadable

So `figures` is a floor underneath `precision`: never fewer decimals than the page
asked for, and never so few that the number stops saying anything.

Where this comes from, and the two places it deliberately differs. `round-mode =
figures` is siunitx's; handcalcs spells it `# scientific`, Mathcad `float`, NumPy
`format_float_positional(fractional=False)`.

  * All of them *replace* decimal places with significant figures, which at four
    figures rounds `70303.22` to `70300`. This is a floor, so it only ever adds
    decimals. The engineer asked for more digits on the small values and never for
    fewer on the large ones.

  * All of them apply to every number. This fires only where a value has been reduced
    to a single digit or none, because that is the reported defect: `0.02` and `0.00`.
    `0.88` and `2.85` are good numbers and are left exactly alone, which is what keeps
    a page from churning under a change nobody asked for.
"""

import pytest

from engcalc_colab.renderer import RenderSettings

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str, *, config: str = "") -> str:
        captured.clear()
        if config:
            magics.eng_config(config)
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


# --- the defect ---------------------------------------------------------------------

def test_a_period_does_not_round_away_to_two_decimals(cell):
    """The reported defect. 0.016756 s is a real period and `0.02` is not it."""
    final = _final(cell("T := 0.016756*s\nx = 1*T\nnumeric(x)\n"))
    assert "0.0168" in final, final
    assert r"\mathrm{s}" in final, final


def test_the_smallest_time_the_engineer_accepts_still_reads(cell):
    """He named his own floor: 0.00002 s."""
    final = _final(cell("t := 0.00002*s\nu = 1*t\nnumeric(u)\n"))
    assert "0.00002" in final, final
    assert "10^{" not in final, final


def test_a_small_bare_number_is_not_zero(cell):
    """`0.00` is not a number.

    Deliberately dimensionless. Where a family exists it answers first and answers
    better - `0.002278125*m**4` becomes `227812.50 cm^4`, which is what an engineer
    writes - and the floor is for the values no family can reach: ratios, strains,
    slopes, and any quantity whose unit has nowhere left to step.
    """
    final = _final(cell("r := 0.002278125\ns = 1*r\nnumeric(s)\n"))
    assert "0.00228" in final, final


def test_a_computed_period_keeps_its_significant_zero(cell):
    """0.0300394 s must print `0.0300`, not `0.03`. Giving back a decimal is right
    only where the value genuinely has nothing there; here the third decimal is a
    figure, and dropping it reports a different period."""
    final = _final(cell(
        "E := 210*GPa\nA := 625*mm**2\nL := 6*m\nms_ := 500*kg\n"
        "keep k = E*A/L\nw = sqrt(k/ms_)\nkeep w_n = w\nT = 2*pi/w_n\nnumeric(T)\n"
    ))
    assert "0.0300" in final, final
    assert "10^{" not in final, final


# --- what must not move -------------------------------------------------------------

def test_a_large_value_keeps_every_digit_it_already_had(cell):
    """The difference from siunitx's `round-mode = figures`, which at four figures
    would round this to `70300`. A floor never removes digits."""
    final = _final(cell("k := 70303.2244*kN/m\nq = 1*k\nnumeric(q)\n"))
    assert "70303.22" in final, final


def test_a_value_that_already_reads_well_is_untouched(cell):
    """`2.85` carries three digits and `0.88` two; neither is the reported defect, and
    the floor must not reach them. These are the cases that sized the trigger."""
    assert "2.85" in _final(cell("q := 2.845*tonf/m\nw = 1*q\nnumeric(w)\n"))
    assert "0.88" in _final(cell("r := 0.8794\ns = 1*r\nnumeric(s)\n"))


def test_an_ordinary_beam_moment_is_unchanged(cell):
    final = _final(cell("q := 10*kN/m\nL := 6*m\nM = q*L**2/8\nnumeric(M)\n"))
    assert "45.00" in final, final


def test_zeros_that_reveal_nothing_are_not_padded(cell):
    """Pure significant figures would print `3.700`; the floor gives back a decimal the
    value does not have."""
    final = _final(cell("h := 3.70*m\ny = 1*h\nnumeric(y)\n"))
    assert "3.70" in final, final
    assert "3.700" not in final, final


def test_a_declared_unit_still_moves_when_its_band_is_wrong(cell):
    """The half that shows why the unit rules were left asking about `precision`.

    `0.00008 m` is a length an engineer writes as `0.08 mm`, however many decimals the
    page is willing to print. Making the family rules consult the floor - which looked
    like the tidy unification - left it as `0.00008 m`.
    """
    final = _final(cell("g := 0.00008*m\ny = 1*g\nnumeric(y)\n"))
    assert "0.08" in final, final
    assert r"\mathrm{mm}" in final, final


def test_a_formula_coefficient_is_still_as_long_as_the_precision(cell):
    """1/(2*0.85) is an artefact of the algebra, not a value the engineer typed, and
    `0.59` has lost nothing. Letting the floor stretch it to `0.588` would overturn a
    decision this page already made and shift where long expressions wrap."""
    latex = cell(
        "fc := 30*MPa\nfy := 420*MPa\nb := 300*mm\nAs := 1935*mm**2\nd := 446*mm\n"
        "a = fy*As/(0.85*fc*b)\nphiMn = fy*As*(d - a/2)\n"
    )
    assert "0.59" in latex, latex
    assert "0.588" not in latex, latex


# --- the truth test -----------------------------------------------------------------

def test_a_value_the_decimals_cannot_tell_the_truth_about_keeps_its_exponent(cell):
    """`0.00002` and `1.05e-5` both read `0.00` at two decimals and part company here:
    the first is exactly what it says, the second would become a different number."""
    assert "10^{-5}" in _final(cell("a := 1.05e-5\nb = 1*a\nnumeric(b)\n"))
    assert "10^{" not in _final(cell("a := 0.00002\nb = 1*a\nnumeric(b)\n"))


def test_a_value_below_the_depth_limit_keeps_its_exponent(cell):
    """Six decimals is as deep as the floor goes. Past that the reader is counting
    zeros, which is the job an exponent exists to remove."""
    final = _final(cell("a := 1e-8\nb = 1*a\nnumeric(b)\n"))
    assert "10^{-8}" in final, final
    assert "0.00000001" not in final, final


# --- the setting --------------------------------------------------------------------

def test_the_page_can_turn_the_floor_off(cell):
    """`figures=0` is exactly what every page rendered before this existed."""
    final = _final(cell("T := 0.016756*s\nx = 1*T\nnumeric(x)\n", config="figures=0"))
    assert "0.02" in final, final
    assert "0.0168" not in final, final


def test_the_page_can_ask_for_more(cell):
    final = _final(cell("T := 0.016756*s\nx = 1*T\nnumeric(x)\n", config="figures=6"))
    assert "0.016756" in final, final


def test_figures_is_validated_like_precision():
    for bad in (-1, 11, True):
        with pytest.raises(ValueError):
            RenderSettings(figures=bad)


def test_the_config_line_reports_and_rejects(capsys):
    from IPython.core.interactiveshell import InteractiveShell

    shell = InteractiveShell.instance()
    shell.extension_manager.load_extension("engcalc_colab")

    shell.run_line_magic("eng_config", "figures=5")
    shell.run_line_magic("eng_config", "")
    assert "figures=5" in capsys.readouterr().out

    shell.run_line_magic("eng_config", "figures=nonsense")
    assert "figures must be an integer from 0 to 10" in capsys.readouterr().out
    InteractiveShell.clear_instance()
