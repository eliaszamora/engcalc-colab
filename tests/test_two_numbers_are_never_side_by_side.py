r"""Two numbers in one product are set apart by a dot, even when they come from two denominators.

`phiMn = fy*As*(d - fy*As/(0.85*fc*b)/2)` read `\frac{fy As}{2 0.85 fc b}` - on the page
"2 0.85", which reads as twenty point eight five. Found writing 0.42.0's contracts, on 0.41.2
too. `sp.fraction` gathers the two denominators, `2` and `0.85 b fc`, into one product whose
second factor is itself a product; the printer set a dot before a factor that *is* a
number (`2*3*kN` read `23 kN`, fixed long ago) and not before one that *begins* with a
number. It does now, read off the printed factor. Reading the nested product as its
factors was tried first and took an interpolation's fraction apart; this touches nothing
else on any page.
"""

import contextlib
import io

from IPython.display import Math

import engcalc_colab.magic as magic
from engcalc_colab.renderer import _EngineeringLatexPrinter

import sympy as sp


def _page(source: str, monkeypatch) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    with contextlib.redirect_stdout(io.StringIO()):
        magic.EngMagics().eng("", source)
    return " ".join(item.data for item in captured if isinstance(item, Math))


def test_a_halved_formula_reads_two_numbers_apart(monkeypatch):
    page = _page(
        "fc := 30*MPa\nfy := 420*MPa\nb := 300*mm\nAs := 1935*mm**2\nd := 446*mm\n"
        "phiMn = fy*As*(d - fy*As/(0.85*fc*b)/2)\n",
        monkeypatch,
    )
    assert "2 0.85" not in page, page
    assert r"{2 \cdot 0.85\,\mathit{fc}\,b}" in page, page


def test_a_product_that_begins_with_a_number_is_set_apart():
    """The printer itself, on the product `sp.fraction` hands it."""
    b, fc = sp.symbols("b fc")
    nested = sp.Mul(2, sp.Mul(sp.Float("0.85"), b, fc, evaluate=False), evaluate=False)
    latex = _EngineeringLatexPrinter()._print_engineering_product(nested)
    assert latex.startswith(r"2 \cdot 0.85"), latex
