r"""A unit standing alone where a quantity stands is written with its one.

    max(1*m, L/4)                          max(m, L/4)
    interp(x, [0*m, 1*m, 2*m], ...)        [0, m, 2 m]
    extrema over it                        x = m (1.00 m)

`1*m` folds to the symbol `m` before anything is printed, so wherever the page printed the
value rather than the form the sheet wrote, one metre came out as the word "metre". The
definitions were right already - the written form keeps `1 m`, `1 kN·m`, `1 kN/m` - and the
rest was not: a function's arguments, a table, a formula row of `numeric`, a characteristic
row. Reported to him after 0.32.1 and asked for on 2026-09-23 (*"corrige los hallazgos
encontrados"*).

The rule is the one the written form already follows: a unit, or a product or power of
units, standing where a quantity stands - a term of a sum, an argument, a matrix entry, a
side of a comparison, the whole expression - is written with its `1`. As a factor it stays
as it is: `4 kN x / m`, `kN·m` inside a product, the `1/m` that already has its one.
"""

import pytest

import engcalc_colab.magic as magic


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
        ("L := 8*m\nb = max(1*m, L/4)\n", r"\max\left(1\,\mathrm{m}, \frac{L}{4}\right)"),
        ("M_u := 3*kN*m\nb = max(1*kN*m, M_u)\n", r"\max\left(1\,\mathrm{kN} \cdot \mathrm{m}, M_{u}\right)"),
        ("k(x) = interp(x, [0*m, 1*m, 2*m], [1*kN, 5*kN, 2*kN])\n", r"1\,\mathrm{m} & \displaystyle 2\,\mathrm{m}"),
        ("k(x) = interp(x, [0*m, 1*m, 2*m], [1*kN, 5*kN, 2*kN])\n", r"\left[\begin{matrix}\displaystyle 1\,\mathrm{kN} &"),
        ("k(x) = piecewise(5*kN, x <= 1*m, 2*kN)\n", r"x \leq 1\,\mathrm{m}"),
        # With its sign: a stiffness matrix written `-1*kN/m` read `-kN/m`.
        ("K = [2*kN/m, -1*kN/m; -1*kN/m, 2*kN/m]\n", r"- \frac{1\,\mathrm{kN}}{\mathrm{m}}"),
    ],
)
def test_a_unit_alone_is_written_with_its_one(magics, capsys, source, shown):
    page = run(magics, source)
    assert "engcalc:" not in capsys.readouterr().out
    assert shown in page, page


def test_the_formula_row_of_numeric_keeps_it(magics, capsys):
    page = run(magics, "x0 := 1*m\nk(x) = 1*kN + 4*kN*x/m\nnumeric(k(x0))\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\mathrm{kN} + \frac" not in page.replace(r"1\,\mathrm{kN} + \frac", ""), page
    assert r"1\,\mathrm{kN} + \frac{4\,\mathrm{kN}\,x}{\mathrm{m}}" in page, page


def test_the_row_of_a_characteristic_point_keeps_it(magics, capsys):
    page = run(
        magics,
        "L := 2*m\nk(x) = interp(x, [0*m, 1*m, 2*m], [1*kN, 5*kN, 2*kN])\nextrema(k(x), x, 0, L)\n",
    )
    assert "engcalc:" not in capsys.readouterr().out
    assert r"x = 1\,\mathrm{m}\," in page, page
    assert r"x = \mathrm{m}\," not in page, page
    # The value column too: 1 kN at x = 0, the table's first value.
    assert r"\text{value} = 1\,\mathrm{kN}\," in page, page


@pytest.mark.parametrize(
    ("source", "shown"),
    [
        # A unit as a factor stays a factor.
        ("k(x) = 2*kN + 4*kN*x/m\n", r"\frac{4\,\mathrm{kN}\,x}{\mathrm{m}}"),
        # One over a unit already has its one.
        ("f = 1/m\n", r"f & = & \displaystyle \frac{1}{\mathrm{m}}"),
        # A written coefficient other than one is untouched.
        ("L := 8*m\nb = max(2*m, L/4)\n", r"\max\left(2\,\mathrm{m}, \frac{L}{4}\right)"),
        # A definition was right already, from its written form.
        ("b = 1*kN/m\n", r"b & = & \displaystyle \frac{1\,\mathrm{kN}}{\mathrm{m}}"),
    ],
)
def test_what_was_written_right_stays_as_it_was(magics, capsys, source, shown):
    page = run(magics, source)
    assert "engcalc:" not in capsys.readouterr().out
    assert shown in page, page
    assert r"1\,1" not in page, page
