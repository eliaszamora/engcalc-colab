r"""A unit written into a formula is set as a unit: upright, and apart from its number.

The engineer's modal memoria on 0.31.0, in Colab:

    F = [10kN; 5kN; 2kN]
    u = [17kN/k₁; kN(7k₁ + 17k₂)/(k₁k₂); ...]
    p = [-5 kN m; 0; 10 kN m]        with the `m` in italic

A number and its unit ran together - `10kN` - and a metre was set as the variable `m`.

**Why.** The page had the answer and used it in one place. `unit_literal_names` decides
which names a line reads as units - `m` is a metre unless the sheet stored a value under
it, which makes it a mass - and that set reached the substitution stage only. A definition
row printed with none: `kN` came out upright because a name of several letters is set
upright, `m` came out italic because a name of one letter is not, and the space between
`10` and `\mathrm{kN}` was a LaTeX space, which MathJax does not show.

**So a definition row is told which names are units, and a unit is set apart from what
it multiplies with a thin space**, `10\,\mathrm{kN}`, as siunitx and every code writes it.
A name the sheet gave a value to is still that value.
"""

import engcalc_colab.magic as magic


def page(monkeypatch, source: str) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", source)
    return "".join(str(getattr(obj, "data", "")) for obj in captured)


def test_a_load_vector_reads_ten_kilonewtons(monkeypatch, capsys):
    math = page(monkeypatch, "F = [10*kN; 5*kN; 2*kN]\n")
    capsys.readouterr()

    assert r"\displaystyle 10\,\mathrm{kN}" in math, math


def test_a_unit_over_a_name_keeps_its_space(monkeypatch, capsys):
    math = page(monkeypatch, "k_1 := 2500*kN/m\nu_1 = 17*kN/k_1\n")
    capsys.readouterr()

    assert r"\frac{17\,\mathrm{kN}}{k_{1}}" in math, math


def test_a_metre_is_upright(monkeypatch, capsys):
    math = page(monkeypatch, "s = 2*m\n")
    capsys.readouterr()

    assert r"s & = & \displaystyle 2\,\mathrm{m}" in math, math


def test_a_moment_reads_kilonewton_metres(monkeypatch, capsys):
    math = page(monkeypatch, "p = cross([2*m; 0*m; 1*m], [0*kN; 5*kN; 0*kN])\n")
    capsys.readouterr()

    # The two units are joined by a centred dot since
    # test_two_units_multiplied_read_as_one_unit; what this file asks is whether they
    # are upright.
    assert r"10\,\mathrm{kN} \cdot \mathrm{m}" in math, math


def test_the_formula_of_a_numeric_row_is_set_the_same_way(monkeypatch, capsys):
    math = page(monkeypatch, "k_1 := 2500*kN/m\nnumeric(17*kN/k_1)\n")
    capsys.readouterr()

    assert r"\frac{17\,\mathrm{kN}}{k_{1}} & = &" in math, math


def test_a_formula_shown_as_written_is_asked_for_its_units(monkeypatch, capsys):
    """`6*m/(2*m)` is worth 3, which has no metre in it, and the row prints what was
    written. Asked of the value alone, the metres came out as two variables `m`."""
    math = page(monkeypatch, "n = 6*m/(2*m)\n")
    capsys.readouterr()

    assert r"\frac{6\,\mathrm{m}}{2\,\mathrm{m}}" in math, math


def test_the_equation_a_solve_shows_is_set_the_same_way(monkeypatch, capsys):
    """The equation row is drawn by its own path, and it was told no names at all."""
    math = page(monkeypatch, "a = solve(2*m*x - 6*m, x)\n")
    capsys.readouterr()

    assert r"2\,\mathrm{m}\,x - 6\,\mathrm{m} = 0" in math, math

    math = page(monkeypatch, "a = solve(2*x = 6*m, x)\n")
    capsys.readouterr()

    assert r"2 x = 6\,\mathrm{m}" in math, math


def test_an_input_row_keeps_a_unit_its_value_lost(monkeypatch, capsys):
    """The integral is worth 3; the metre is only in what the row writes before it."""
    math = page(monkeypatch, "n = integrate(1/m, x, 0, 3*m)\n")
    capsys.readouterr()

    assert r"\frac{1}{\mathrm{m}}\, dx = 3" in math, math


def test_an_assigned_entry_keeps_its_unit(monkeypatch, capsys):
    math = page(monkeypatch, "p = [1*m; 2*m]\np[2] = 5*m\n")
    capsys.readouterr()

    last = math.rsplit("\\\\[8pt]", 1)[-1]
    assert r"5\,\mathrm{m}" in last, last


def test_a_definition_too_long_for_one_row_is_set_the_same_way(monkeypatch, capsys):
    """Past the row budget the definition is broken into rows by another path, which has
    to be told the same names."""
    math = page(
        monkeypatch,
        "w_D = gamma_c*b_w*(h - t_s) + gamma_c*t_s*B + 1.2*kN/m^2*B + 0.5*kN/m^2*B + 2*kN/m^2*B\n",
    )
    capsys.readouterr()

    assert r"\quad +" in math, "not broken into rows: " + math
    assert r"\frac{0.5\,\mathrm{kN}\,B}{\mathrm{m}^{2}}" in math, math


# --- what must not move ---------------------------------------------------------------


def test_a_mass_named_m_is_still_a_mass(monkeypatch, capsys):
    """`m := 500*kg` makes `m` a value, and the same precedence the arithmetic uses
    decides the type: italic, and no thin space as if it were a unit."""
    math = page(monkeypatch, "m := 500*kg\na := 2*m/s^2\nF = m*a\n")
    capsys.readouterr()

    assert r"F & = & \displaystyle a m" in math, math


def test_two_names_are_not_set_apart(monkeypatch, capsys):
    math = page(monkeypatch, "b := 300*mm\nh := 600*mm\nA = b*h\n")
    capsys.readouterr()

    assert r"A & = & \displaystyle b h" in math, math
