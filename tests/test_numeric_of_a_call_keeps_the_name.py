r"""`numeric(M(L/2))` works a call out on the body it was written with.

Seen in his Colab checking 0.42.1 (2026-09-27), older than 0.42 - the same on 0.41.2 with
`keep`: over `R_A = q*L/2` (kept) and `M(x) = R_A*x - q*x^2/2`, `numeric(M(L/2))` opened
with `q L x/2 - q x^2/2` and put in `q` and `L` for the reaction, one row under `M(x) = R_A
x - q x^2/2`. `numeric(name)` already opened with the written form; a call now does too,
and the kept name is put in as its own number, 30 kN. The number is the same.
"""

import contextlib
import io

from IPython.display import Math

import engcalc_colab.magic as magic

SHEET = "L := 6*m\nq := 10*kN/m\nR_A = q*L/2\nM(x) = R_A*x - q*x^2/2\nnumeric(M(L/2))\n"


def _page(source: str, monkeypatch) -> tuple[str, str]:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    latex = " ".join(item.data for item in captured if isinstance(item, Math))
    return latex.replace(r"\displaystyle ", ""), console.getvalue()


def _call_rows(page: str) -> str:
    return page[page.index(r"M\left(\frac{L}{2}\right) & = &"):]


def test_the_call_opens_with_the_written_body(monkeypatch):
    page, console = _page(SHEET, monkeypatch)
    assert not console, console
    rows = _call_rows(page)
    assert r"R_{A} x - \frac{q x^{2}}{2}" in rows, rows
    assert r"\frac{q L x}{2}" not in rows, rows


def test_the_kept_name_is_put_in_as_its_own_number(monkeypatch):
    page, _console = _page(SHEET, monkeypatch)
    rows = _call_rows(page)
    assert r"\left(30.00\,\mathrm{kN}\right)" in rows, rows
    assert rows.rstrip().endswith(r"45.00\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), rows


def test_a_call_with_nothing_kept_is_as_it_was(monkeypatch):
    page, _console = _page(
        "L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L - x)/2\nnumeric(M(L/2))\n", monkeypatch
    )
    rows = _call_rows(page)
    assert r"\frac{q x \left(L - x\right)}{2}" in rows, rows
    assert rows.rstrip().endswith(r"45.00\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), rows
