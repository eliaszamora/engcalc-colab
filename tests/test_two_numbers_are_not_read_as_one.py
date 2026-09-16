r"""Two numbers multiplied on the page are two numbers: `2 · 3 kN`, never `23 kN`.

A definition keeps the coefficients it was written with, so `P = 2*3*kN` shows
`2*3*kN` rather than `6 kN`. It printed

    P   = 2 3\,\mathrm{kN}          MathJax:  23 kN
    A_c = 0.3 0.6\,\mathrm{m}\,\mathrm{m}     0.30.6 m m
    Q   = 0.5 1.2 q L                        0.51.2 qL

**Why.** A product's factors are joined by a LaTeX space, and MathJax does not show a
space between two numbers. For a name beside a name, `b h`, that reads as it should; for a
number beside a number it writes one number that is neither of them. `2 3 kN` is not a
typesetting blemish, it is `23 kN` on the page for a load of 6 kN.

**So two numeric factors that meet are joined by `\cdot`**, as SymPy's own printer and a
hand calculation both write them. Nothing else in a product changes: a unit keeps its thin
space and a name keeps the plain one.
"""

import engcalc_colab.magic as magic


def page(monkeypatch, source: str) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", source)
    return "".join(str(getattr(obj, "data", "")) for obj in captured)


def test_a_load_of_two_times_three(monkeypatch, capsys):
    math = page(monkeypatch, "P = 2*3*kN\n")
    capsys.readouterr()

    assert r"P & = & \displaystyle 2 \cdot 3\,\mathrm{kN}" in math, math


def test_an_area_from_two_dimensions(monkeypatch, capsys):
    math = page(monkeypatch, "A_c = 0.30*m*0.60*m\nnumeric(A_c)\n")
    capsys.readouterr()

    assert r"0.3 \cdot 0.6\,\mathrm{m}\,\mathrm{m}" in math, math
    assert "0.3 0.6" not in math, math


def test_two_coefficients_before_names(monkeypatch, capsys):
    math = page(monkeypatch, "Q = 0.5*1.2*q*L\n")
    capsys.readouterr()

    assert r"Q & = & \displaystyle 0.5 \cdot 1.2 q L" in math, math


def test_numbers_over_a_denominator(monkeypatch, capsys):
    math = page(monkeypatch, "M = 1.2*18*kN/m*(6*m)^2/8\n")
    capsys.readouterr()

    assert r"\frac{1.2 \cdot 18\,\mathrm{kN}" in math, math


# --- what must not move ---------------------------------------------------------------


def test_a_coefficient_before_a_name(monkeypatch, capsys):
    math = page(monkeypatch, "U = 1.2*D_1 + 1.6*L_1\n")
    capsys.readouterr()

    assert r"1.2 D_{1} + 1.6 L_{1}" in math, math


def test_two_names(monkeypatch, capsys):
    math = page(monkeypatch, "b := 300*mm\nh := 600*mm\nA = b*h\n")
    capsys.readouterr()

    assert r"A & = & \displaystyle b h" in math, math
