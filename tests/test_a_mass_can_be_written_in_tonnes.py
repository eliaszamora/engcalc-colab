r"""`ton` is a thousand kilograms, and getting that wrong is not a display defect.

The engineer listed the units he works in and one of them did not exist: "kgf y tonf,
kg y ton". `tonf` this package defines; `ton` was absent.

Adding it is one line, and the line is a trap. Pint's `ton` is the **US short ton, 907.18
kg**. An alias pointing at it would have silently taken ten per cent off every mass on a
Spanish-language sheet - a wrong number, not a wrong unit, and the kind that survives
review because it looks like a plausible answer. The alias table already carries the same
warning for `kip`, whose neighbour `kilopound` is a mass of 453 kg.

Defining our own `ton` the way `tonf` is defined does not work either, and fails in the
worst available way:

    registry.define("ton = 1000 * kilogram")   ->  reports success
    Quantity(5, "ton").to("kg")                ->  4536

Pint accepts the redefinition, says nothing, and keeps its own. A check that reports
"OK" and changes nothing is the failure mode recorded in section 9 of
`HOW-THIS-WORK-GOES-WRONG.md`, and this is the second time in one session that trusting
such a report would have shipped a defect.

So the alias points at `metric_ton`, which is 1000 kg, and the page shows `t` - the
symbol every code uses for a tonne. That is the one place this departs from showing what
was typed, and it is worth it: `t` is right, and `ton` was not available without being
wrong.
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


# --- the value, which is where the trap is ------------------------------------------

def test_a_tonne_is_a_thousand_kilograms():
    """The assertion that matters. Pint's own `ton` is 907.18 kg, and an alias pointing
    at it would have taken ten per cent off every mass on the sheet."""
    from engcalc_colab.numeric import NumericContext

    context = NumericContext()
    quantity = context.evaluate_expression(__import__("ast").parse("5*ton", mode="eval"))
    assert quantity.to("kg").magnitude == pytest.approx(5000.0)
    assert quantity.to("kg").magnitude != pytest.approx(4535.92, abs=1.0)


def test_a_mass_written_in_tonnes_reads_as_one(cell):
    latex = cell("m := 5*ton\n")
    assert "5.00" in latex, latex
    assert r"\mathrm{t}" in latex, latex


def test_it_computes_against_kilograms(cell):
    """1 ton + 500 kg is 1500 kg, and the sheet has to agree with itself."""
    final = _final(cell("a := 1*ton\nb := 500*kg\nm = a + b\nnumeric(m, kg)\n"))
    assert "1500.00" in final, final
    assert r"\mathrm{kg}" in final, final


def test_a_weight_from_a_tonne_is_a_force(cell):
    """`M*g` with M in tonnes, which is what the unit is for on a real sheet.

    The mass is `M` and not `m`, and that is not cosmetic: `resolve_numeric_name`
    consults stored values before the alias table, so `m := 5*ton` makes `m` a mass and
    the `m` in `9.80665*m/s**2` stops being a metre. Written the other way first, and
    the engine said "target unit is incompatible with result" - which is the rule
    `written_unit_names` documents, working.
    """
    final = _final(cell("M := 5*ton\ng := 9.80665*m/s**2\nW = M*g\nnumeric(W, kN)\n"))
    assert "49.03" in final, final
    assert r"\mathrm{kN}" in final, final


# --- the neighbour it must not disturb ----------------------------------------------

def test_tonne_force_is_untouched(cell):
    """`tonf` is a force of 9.80665 kN and has nothing to do with this. One letter
    apart, like `kip` and `kilopound`."""
    from engcalc_colab.numeric import engineering_registry

    registry = engineering_registry()
    assert registry.Quantity(1.0, "tonf").to("kN").magnitude == pytest.approx(9.80665)
    assert r"\mathrm{tonf}" in _final(cell("q := 2.8*tonf/m\nw = 1*q\nnumeric(w)\n"))


def test_a_kilogram_is_untouched(cell):
    final = _final(cell("m := 500*kg\nx = 2*m/2\nnumeric(x)\n"))
    assert "500.00" in final, final
    assert r"\mathrm{kg}" in final, final
