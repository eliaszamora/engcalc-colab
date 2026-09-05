r"""A declared unit is one the engineer wrote, not one a `:=` line happened to produce.

`_display_quantity` keeps a unit outright when `declared` is true and the unit still
shows a figure. `declared` means "this statement used `:=`". Every sentence about the
rule means something narrower - "The unit you declare is the unit you see", and the
example beside it is `q := 2.8*tonf/m`, where a unit really was typed.

The two part company exactly when the right-hand side is a product of other quantities
and names no unit of its own. Nothing was declared there, and three behaviours the
README presents as current are not current on that route:

    L := 6*m
    d_adm := L/300                  0.02 m           the README's own "before" column
    phiMn := 0.9*As*fy*z            2.84e8 MPa*mm^3  RC-2B, by a second route
    DC := Mu/(0.9*As*fy*z)          8.79e-7 kN*m/... RC-2A, by a second route

Each of those three has a passing contract already, written against `numeric(...)` on a
symbolic definition. The fix shipped for the route the external trial used and not for
the one an engineer reaches for when the value is simply a number.

Three of them survive today only by accident, and the accident is worth naming: a
declared unit is dropped when it shows *no* figures at the active precision, so
`v := 8e-05*m` and a deflection carrying `kN*m^3/(GPa*mm^4)` escape into their families
because their magnitudes round to `0.00`. `MPa*mm^3` keeps four figures, so it stays.
Whether the page is right depends on where the decimal point falls, which is not a rule.

What `declared` becomes: the right-hand side names a unit. The precedence that decides
what a name means already exists and is the one the arithmetic uses - a stored value
before the alias table, so `m := 500*kg` makes `m` a mass and does not relabel it a
metre. #75 built that for the substitution printer; this reads the same table.
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


CAPACITY_INPUTS = (
    "fy := 413.6854*MPa\n"
    "As := 1935.48*mm**2\n"
    "z := 394.53*mm\n"
)


# --- the three the route gets wrong -----------------------------------------------

def test_an_admissible_deflection_moves_to_millimetres(cell):
    """The README's own table row, in the column it calls `before`. `L/300` on a 6 m
    span is 0.02 m, which keeps one figure at a precision of 2, so the declared metre
    survives - and 20 mm is what the reader needs beside a deflection in millimetres."""
    final = _final(cell("L := 6*m\nd_adm := L/300\n"))
    assert r"\mathrm{mm}" in final, final
    assert "20.00" in final, final


def test_a_capacity_assigned_as_a_number_reads_as_a_moment(cell):
    """RC-2B by the other route. `numeric(phiMn)` on a symbolic definition has said
    284.30 kN*m since v0.23.3; the same arithmetic written as a numeric assignment
    still says 2.84e8 MPa*mm^3."""
    final = _final(cell(CAPACITY_INPUTS + "phiMn := 0.9*As*fy*z\n"))
    assert "284.30" in final, final
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final
    assert "MPa" not in final, final


def test_a_ratio_assigned_as_a_number_prints_as_a_number(cell):
    """RC-2A by the other route. A demand over a capacity is 0.88, and the units the
    algebra left behind scaled it to 8.79e-7."""
    final = _final(cell(
        CAPACITY_INPUTS + "Mu := 250*kN*m\nDC := Mu/(0.9*As*fy*z)\n"
    ))
    assert "0.88" in final, final
    assert "MPa" not in final, final
    assert "kN" not in final, final


# --- everything a declared unit is for, which must not move ------------------------

def test_a_unit_the_engineer_wrote_is_kept(cell):
    """The sentence the rule exists for, and the example the README gives for it."""
    final = _final(cell("q := 2.8*tonf/m\n"))
    assert "2.80" in final, final
    assert r"\mathrm{tonf}" in final, final


def test_a_span_stays_in_the_metres_it_was_written_in(cell):
    final = _final(cell("L := 6*m\n"))
    assert "6.00" in final, final
    assert r"\mathrm{m}" in final, final
    assert "mm" not in final, final


def test_a_declared_unit_that_shows_no_figure_still_moves(cell):
    """`v := 8e-05*m` reads `0.00 m` in the unit it was written in. This is the escape
    the three broken rows above were relying on, and it has to keep working on its own
    terms rather than as the only thing standing between the page and nonsense."""
    final = _final(cell("v := 8e-05*m\n"))
    assert "0.08" in final, final
    assert r"\mathrm{mm}" in final, final


def test_an_area_built_from_two_declared_lengths_stays_in_mm2(cell):
    """Names no unit, so it is no longer declared - and must still be left alone,
    because `mm^2` costs no more than the family's own `cm^2`. `_unit_is_the_engineers`
    is what keeps it, and this is the contract that says so."""
    final = _final(cell("b := 300*mm\nh := 500*mm\nA := b*h\n"))
    assert r"\mathrm{mm}^{2}" in final, final


def test_a_dimensionless_scalar_is_untouched(cell):
    final = _final(cell("phi := 0.9\n"))
    assert "0.90" in final, final


def test_pi_is_not_a_written_unit(cell):
    """The one case that separates "names a unit" from "names something that is not a
    stored value", and a mutation survived the first draft for want of it.

    Any name a numeric assignment resolves is either a stored value, `pi`, or a unit -
    anything else raises before the renderer is reached. So testing the alias table
    looks redundant beside testing stored values, and is not: `pi` falls through both.
    Counting it as a written unit would make every formula that uses it declared.

    Torsion of a circular shaft. pi x (50 mm)^3 x 80 MPa / 16 = 1.96 kN*m; the unit the
    algebra hands over is `mm^3 * MPa`, which keeps its figures and would survive.
    """
    final = _final(cell("d := 50*mm\ntau := 80*MPa\nT := pi*d**3*tau/16\n"))
    assert "1.96" in final, final
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final
    assert "MPa" not in final, final


def test_a_name_that_shadows_a_unit_is_read_as_the_value(cell):
    """`m := 500*kg` makes `m` a mass. The rule that decides what a name means must be
    the one the arithmetic uses, or the page relabels the reader's own quantity - and a
    second, divergent copy of that precedence is the way this goes wrong."""
    latex = cell("m := 500*kg\nw := 3*m\n")
    assert r"\mathrm{kg}" in latex, latex
    assert "1500.00" in latex, latex


def test_a_shadowed_unit_name_does_not_make_a_statement_declared(cell):
    """The contract the previous one cannot supply, and the reason it is here.

    `m := 500*kg` renders the same whether or not the precedence is honoured, because
    a mass has no family to be moved into - so dropping the `not in self.values` test
    survives it. Shadowing `m` with a *stress* and building the capacity out of it
    makes the difference visible: read as a value, the statement declares no unit and
    the capacity reads 284.30 kN*m; read as the metre it is not, the statement counts
    as declared and keeps 2.84e8 MPa*mm^3.
    """
    final = _final(cell(
        "m := 413.6854*MPa\n"
        "As := 1935.48*mm**2\n"
        "z := 394.53*mm\n"
        "phiMn := 0.9*As*m*z\n"
    ))
    assert "284.30" in final, final
    assert "MPa" not in final, final
