r"""A name of several letters is set in italic, like every quantity; a unit stays upright.

`Vu = 7920.00 kgf > φ_v V_c` set `Vu` upright, in the letter `kgf` is set in, next to an
italic `V_c`: two different V's for one kind of thing, and a name that read as a unit. He
asked on 2026-09-25 to check the fonts and chose italic (*"Sí, pasa las variables a
cursiva"*).

`\mathit`, not plain italic. Math italic spaces letters as a product - which is why names
were made upright in the first place: `eqFy` read as `e q F y`. `\mathit` is text italic:
one word, with the letters kept together.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        with contextlib.redirect_stdout(io.StringIO()):
            magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return run


@pytest.mark.parametrize("name", ["Vu", "fc", "As", "phiMn", "eqFy"])
def test_a_name_of_several_letters_is_italic(sheet, name):
    page = sheet(f"{name} := 2*kN\n")
    assert rf"\mathit{{{name}}} & = &" in page, page
    assert rf"\mathrm{{{name}}}" not in page, page


def test_its_subscript_follows_it(sheet):
    page = sheet("As_min := 2*cm^2\n")
    assert r"\mathit{As}_{min} & = &" in page, page


def test_a_unit_stays_upright(sheet):
    page = sheet("Vu := 7920*kgf\n")
    assert r"7920.00\,\mathrm{kgf}" in page, page


def test_a_greek_name_and_a_one_letter_name_are_as_they_were(sheet):
    page = sheet("theta := 2\nb := 3*cm\nDelta := 4*cm\n")
    assert r"\theta & = &" in page and r"b & = &" in page and r"\Delta & = &" in page, page


def test_it_stays_apart_from_its_neighbour(sheet):
    # Two names of several letters side by side still take the thin space that kept
    # `qD L` from reading `qDL`.
    page = sheet("qD := 2*kN/m\nLv := 3*m\nM = qD*Lv\n")
    assert r"\mathit{qD}\,\mathit{Lv}" in page, page
