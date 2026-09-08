r"""A modulus derived from a sheet written in MPa is shown in MPa.

    E := 200000*MPa
    G = E/(2*1.30)
    numeric(G)          ->   76.92 GPa      where the sheet says MPa throughout

#99 stopped every unit family at kilo, at the engineer's request: *"prefiero que nos
quedemos con kN, m, s ... no me gusta que hayan algunos en kilo y otros en mega"*. The
pressure family was exempted from that, deliberately, on the reasoning that "a concrete
strength is 25 MPa and a modulus 210 GPa in every code on the shelf".

The exemption was granted before the preference was known. Asked what units he works in,
the engineer said it twice, unprompted: *"el E del acero nunca lo he trabajado en GPa"*
and *"GPa nunca lo he usado"*. The code on the shelf is not the sheet on his screen, and
the sheet is the product.

So the SI pressure family is `("MPa",)`, and the change is smaller than it looks because
of what the rest of the renderer already does:

* a value **stored** in MPa has a family member's unit, so the family chooses - and with
  one member the family can only choose MPa. `76923.08 MPa`.
* a value **stored** in GPa no longer wears a family member's unit, so
  `_unit_is_the_engineers` reaches its shape rule: a pressure against the family's own
  pressure, shapes match, kept. A sheet that writes `E := 200*GPa` still reads in GPa,
  which is the rule this whole renderer is built on - a sheet is shown in the units it
  was written in.

Nothing was added to make that second case work. It is what falls out, and it is the
reason this is a one-line table edit rather than a new mechanism.
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


def test_a_shear_modulus_from_a_megapascal_sheet_reads_in_megapascals(cell):
    """200000/2.6 = 76923.08. The page said `76.92 GPa`."""
    final = _final(cell("E := 200000*MPa\nG = E/(2*1.30)\nnumeric(G)\n"))
    assert "76923.08" in final, final
    assert r"\mathrm{MPa}" in final, final
    assert "GPa" not in final, final


def test_a_large_stress_stays_in_megapascals(cell):
    """The band no longer has a step to climb to, which is the whole change."""
    final = _final(cell("s := 5000*MPa\nd = s*2\nnumeric(d)\n"))
    assert "10000.00" in final, final
    assert "GPa" not in final, final


def test_a_sheet_that_writes_gigapascals_keeps_them(cell):
    """The half that must not move. A declared unit is kept in every case."""
    final = _final(cell("E := 200*GPa\nnumeric(E)\n"))
    assert "200.00" in final, final
    assert r"\mathrm{GPa}" in final, final


def test_a_value_derived_on_a_gigapascal_sheet_keeps_gigapascals(cell):
    """Not declared - `numeric` of a product arrives with `declared` False - and still
    GPa, because `GPa` is no longer a family member and its factor shape matches the
    family's own. The sheet is shown in the units it was written in."""
    final = _final(cell("E := 200*GPa\nG = E/(2*1.30)\nnumeric(G)\n"))
    assert "76.92" in final, final
    assert r"\mathrm{GPa}" in final, final


def test_a_concrete_strength_is_untouched(cell):
    """25 MPa was already MPa and stays MPa: the exemption being removed was never
    what put it there."""
    final = _final(cell("fc := 25*MPa\nnumeric(fc)\n"))
    assert "25.00" in final, final
    assert r"\mathrm{MPa}" in final, final
