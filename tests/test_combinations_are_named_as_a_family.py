r"""`U1` ... `U6` are one family, `U`; and `governing` reads "Governing along x".

An envelope names what it envelopes by the family of its series - `M_1`, `M_2` are `M`,
and the figure reads `M(x) envelope`, `M_max(x)`, `M_min(x)` - but the family was found by
splitting on an underscore, and a code's combinations are written `U1`, `U2`: the frame's
design envelope was titled `Comparison envelope`, its axis `Comparison [kgf·cm]`. A name
followed by its number is a family too.

`governing` headed its block `Governing — x`, a dash where a word was meant.

Both found writing `tools/portico_diseno.eng`; dealt with among the pending points he
asked for (*"abarques todos esos puntos pendientes"*).
"""

import contextlib
import io

import matplotlib
import pytest
from IPython.display import Math
from matplotlib.figure import Figure

import engcalc_colab.magic as magic

matplotlib.use("Agg")

BEAM = (
    "L := 6*m\nqD := 18*kN/m\nqL := 12*kN/m\n"
    "M_D(x) = qD*x*(L - x)/2\nM_L(x) = qL*x*(L - x)/2\n"
    "case D = M_D(x)\ncase Lv = M_L(x)\n"
    "combo U1 = 1.4*D\ncombo U2 = 1.2*D + 1.6*Lv\n"
)


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str):
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        return captured, console.getvalue()

    return run


def test_combinations_envelope_as_a_family(sheet):
    captured, console = sheet(BEAM + "envelope(U1(x), U2(x), x, 0, L)\n")
    assert not console, console
    (figure,) = [item for item in captured if isinstance(item, Figure)]
    axis = figure.axes[0]
    assert axis.get_title() == "U(x) envelope", axis.get_title()
    assert axis.get_ylabel().startswith("U(x)"), axis.get_ylabel()
    assert "Comparison" not in axis.get_title() + axis.get_ylabel()


def test_names_with_an_underscore_are_a_family_as_before(sheet):
    captured, console = sheet(
        "L := 6*m\nq := 10*kN/m\nM_1(x) = q*x*(L - x)/2\nM_2(x) = q*x*(L - x)/4\n"
        "envelope(M_1(x), M_2(x), x, 0, L)\n"
    )
    assert not console, console
    (figure,) = [item for item in captured if isinstance(item, Figure)]
    assert figure.axes[0].get_title() == "M(x) envelope"


def test_different_families_are_still_a_comparison(sheet):
    captured, console = sheet(BEAM + "M_a(x) = qD*x*(L - x)/3\nenvelope(U1(x), M_a(x), x, 0, L)\n")
    assert not console, console
    (figure,) = [item for item in captured if isinstance(item, Figure)]
    assert figure.axes[0].get_title() == "Comparison envelope"


def test_governing_reads_along(sheet):
    captured, console = sheet(BEAM + "governing(U1(x), U2(x), x, 0, L)\n")
    assert not console, console
    page = " ".join(item.data for item in captured if isinstance(item, Math))
    assert r"\textbf{Governing} \text{ along } x" in page, page
    assert "—" not in page
