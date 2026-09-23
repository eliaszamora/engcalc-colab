r"""A coefficient is printed as it was typed.

    c = 0.125*q                                   rendered as    c = 0.12 q
    phi = interp(e_t, [0.002, 0.005], ...)        rendered as    [2.00 × 10⁻³, 0.01]

The Float printer rounds any number longer than the page's precision, because that is how
it keeps an artefact of the algebra - `1/(2·0.85) = 0.588235294117647` - off the page. It
could not tell that artefact from a number the engineer typed with three decimals, so it
rounded both: 0.125 became 0.12, and 0.005 became 0.01, a value the sheet does not use.
Found on 2026-09-23 building `interp`, whose ACI φ table read `[2.00 × 10⁻³, 0.01]`.

The two are told apart by length. What a person types is short - 0.125, 0.0018, 0.00207
have three significant figures or fewer - and what the algebra leaves behind has sixteen
or seventeen. A number of at most six significant figures, in plain notation, is printed
as typed; anything longer is rounded to the page's precision as before. Of the thirteen
reference sheets and the eighteen gap-map exercises, no row moves.
"""

import pytest
import sympy as sp

import engcalc_colab.magic as magic
from engcalc_colab.renderer import RenderSettings, _latex


@pytest.fixture
def magics(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    engine = magic.EngMagics()
    engine.captured = captured
    return engine


def run(magics, source: str) -> str:
    magics.captured.clear()
    magics.eng("", source)
    return "".join(getattr(obj, "data", "") for obj in magics.captured)


@pytest.mark.parametrize(
    ("source", "shown"),
    [
        ("c = 0.125*q\n", r"c & = & \displaystyle 0.125 q"),
        ("c = 0.005*q\n", r"c & = & \displaystyle 0.005 q"),
        ("rho = 0.0018*b*h\n", r"0.0018 b h"),
        # Three figures behind three zeros: the zeros are not figures, and counting them
        # would call it long.
        ("c = 0.000125*q\n", r"c & = & \displaystyle 0.000125 q"),
        ("t = [0.002, 0.005]\n", r"0.002 & \displaystyle 0.005"),
    ],
)
def test_a_number_the_engineer_typed_is_printed_as_typed(magics, capsys, source, shown):
    page = run(magics, source)
    assert "engcalc:" not in capsys.readouterr().out
    assert shown in page, page


def test_an_artefact_of_the_algebra_is_still_rounded():
    """`1/(2*0.85)` is `0.5882352941176471` to SymPy: sixteen figures nobody typed. It is the
    number `a = As*fy/(0.85*fc*b)` leaves in `a/2`, the case the rounding exists for."""
    q = sp.Symbol("q")
    assert _latex(sp.Float(1 / (2 * 0.85))) == "0.59"
    assert _latex(sp.Float(1 / 0.85) * q) == "1.18 q"


def test_the_precision_still_decides_what_is_long():
    """A number of eight figures is long at precision 2 and short at precision 6."""
    assert _latex(sp.Float("12.345678"), settings=RenderSettings(precision=6)) == "12.345678"
    assert _latex(sp.Float("12.345678"), settings=RenderSettings(precision=2)) == "12.35"


def test_a_number_written_with_an_exponent_keeps_the_page_s_notation():
    r"""`0.00001` reaches SymPy as `1.0 \cdot 10^{-5}`; the page writes `\times`, as it did."""
    assert _latex(sp.Float("0.00001")) == r"1.00 \times 10^{-5}"
