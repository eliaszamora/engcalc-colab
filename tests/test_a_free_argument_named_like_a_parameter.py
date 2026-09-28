r"""`numeric` of a call whose free argument is named like another of its parameters.

Found by the audit of 2026-09-27, wrong on 0.42.3 too; his "corrige el error del argumento
que se llama como otro parámetro" (2026-09-28). Over `F(x, y) = x + 2*y`, `numeric(F(3, x))`
answered 9.00: the free `x` was put in for `y`, and then the value given to the parameter
`x` reached that `x` too. `K(y, 3*m)` of `K(x, y) = y - x` answered 0. A call on a `=` line
was right all along (`z = F(3, x)` reads `2 x + 3`); `numeric` now agrees with it.
"""

import contextlib
import io

from IPython.display import Math

import engcalc_colab.magic as magic


def _page(source: str, monkeypatch) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    assert not console.getvalue(), console.getvalue()
    latex = " ".join(item.data for item in captured if isinstance(item, Math))
    return latex.replace(r"\displaystyle ", "")


def _rows(page: str, head: str) -> str:
    start = page.index(head + r" & = &")
    return page[start:]


def test_a_free_argument_is_not_given_the_value_of_a_parameter(monkeypatch):
    rows = _rows(_page("F(x, y) = x + 2*y\nnumeric(F(3, x))\n", monkeypatch), r"F\left(3, x\right)")
    assert r"9.00" not in rows, rows
    assert rows.rstrip().endswith(r"2.00 x + 3.00 \end{array}") or "2 x + 3" in rows, rows


def test_a_free_argument_is_not_put_in_where_it_cancels(monkeypatch):
    rows = _rows(_page("K(x, y) = y - x\nnumeric(K(y, 3*m))\n", monkeypatch), r"K\left(y, 3\,\mathrm{m}\right)")
    assert r"& = & 0 " not in rows and r"0.00 \end{array}" not in rows, rows
    assert "y" in rows.split("& = &", 1)[1], rows


def test_a_free_argument_beside_a_length(monkeypatch):
    page = _page("G(x, y) = x - y\nnumeric(G(2*m, x))\nH(x, y) = x*y\nnumeric(H(3*m, x))\n", monkeypatch)
    assert r"0.00 \end{array}" not in _rows(page, r"G\left(2\,\mathrm{m}, x\right)").split(r"H\left(x, y\right)")[0], page
    rows = _rows(page, r"H\left(3\,\mathrm{m}, x\right)")
    assert r"9.00\,\mathrm{m}^{2}" not in rows, rows
    assert "x" in rows.split("& = &", 1)[1], rows


def test_numeric_agrees_with_the_call_on_an_equals_line(monkeypatch):
    page = _page("F(x, y) = x + 2*y\nz = F(3, x)\nnumeric(F(3, x))\n", monkeypatch)
    assert "2 x + 3" in _rows(page, "z"), page
    assert r"9.00" not in page, page


def test_a_named_numeric_of_a_call_holds_its_value(monkeypatch):
    # The audit (2026-09-28): `w = numeric(F(3, 4))` stored F's body, `x + 2 y`, so `u = 2*w`
    # read `2 x + 4 y`; wrong on 0.43.0 too. A call is stored with its arguments put in.
    page = _page("F(x, y) = x + 2*y\nw = numeric(F(3, 4))\nu = 2*w\n", monkeypatch)
    row = _rows(page, "u")
    assert "22" in row, row
    assert "x" not in row.split("& = &", 1)[1], row


def test_the_name_kept_apart_never_reaches_the_page(monkeypatch):
    page = _page("F(x, y) = 2*x\nw = numeric(F(3, x))\nu = 2*w\n", monkeypatch)
    assert "argument" not in page, page
    assert "12" in _rows(page, "u"), page


def test_a_named_numeric_at_a_formula_argument_holds_the_formula_there(monkeypatch):
    page = _page(
        "L := 6[m]\nq := 10[kN/m]\nM(x) = q*x*(L - x)/2\nw = numeric(M(L/2))\nu = 2*w\nnumeric(u)\n",
        monkeypatch,
    )
    assert r"x" not in _rows(page, "u").split(r"\\[", 1)[0].split("& = &", 1)[1], page
    assert page.rstrip().endswith(r"90.00\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), page


def test_a_call_with_no_name_in_common_is_as_it_was(monkeypatch):
    rows = _rows(
        _page("L := 6[m]\nq := 10[kN/m]\nM(x) = q*x*(L - x)/2\nnumeric(M(L/2))\n", monkeypatch),
        r"M\left(\frac{L}{2}\right)",
    )
    assert rows.rstrip().endswith(r"45.00\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), rows
