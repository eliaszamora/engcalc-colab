r"""The first row of `numeric` of a call writes the argument where the parameter was.

His decision of 2026-09-27 ("Procede según tus recomendaciones"): `numeric(M(L/2))` under
`M(x) = R_A*x - q*x^2/2` opened with `M(L/2) = R_A x - q x^2/2`, the left saying `L/2`
and the right saying `x`, and only the substitution row below put `x = 3.00 m`. The first
row now reads `R_A (L/2) - q (L/2)^2/2`; the substitution and the answer are as they were.
A name or a plain number goes in bare, anything else in brackets where it needs them.
"""

import contextlib
import io

from IPython.display import Math

import engcalc_colab.magic as magic

HEAD = "L := 6[m]\nq := 10[kN/m]\nR_A = q*L/2\nM(x) = R_A*x - q*x^2/2\n"


def _page(source: str, monkeypatch) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    assert not console.getvalue(), console.getvalue()
    latex = " ".join(item.data for item in captured if isinstance(item, Math))
    return latex.replace(r"\displaystyle ", "")


def _rows_from(page: str, head: str) -> list[str]:
    return page[page.index(head + r" & = &"):].split(r"\\[")


def test_the_first_row_writes_the_argument(monkeypatch):
    rows = _rows_from(_page(HEAD + "numeric(M(L/2))\n", monkeypatch), r"M\left(\frac{L}{2}\right)")
    first = rows[0]
    assert r"R_{A}\,\left(\frac{L}{2}\right)" in first, first
    assert r"q\,\left(\frac{L}{2}\right)^{2}" in first, first
    assert r"R_{A} x" not in first, first


def test_the_substitution_and_the_answer_are_as_they_were(monkeypatch):
    page = _page(HEAD + "numeric(M(L/2))\n", monkeypatch)
    rows = page[page.index(r"M\left(\frac{L}{2}\right) & = &"):]
    assert r"\left(30.00\,\mathrm{kN}\right)\,\left(3.00\,\mathrm{m}\right)" in rows, rows
    assert rows.rstrip().endswith(r"45.00\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), rows


def test_a_number_with_its_unit_is_written_in_brackets(monkeypatch):
    first = _rows_from(_page(HEAD + "numeric(M(3*m))\n", monkeypatch), r"M\left(3\,\mathrm{m}\right)")[0]
    assert r"R_{A}\,\left(3\,\mathrm{m}\right)" in first, first
    assert r"R_{A} x" not in first, first


def test_a_plain_number_goes_in_bare(monkeypatch):
    first = _rows_from(
        _page("L := 6[m]\nq := 10[kN/m]\nf(n) = n*q*L\nnumeric(f(2))\n", monkeypatch), r"f\left(2\right)"
    )[0]
    assert r"2 q L" in first, first
    assert "n q L" not in first, first


def test_a_name_goes_in_bare(monkeypatch):
    first = _rows_from(
        _page("L := 6[m]\nq := 10[kN/m]\na := 2[m]\nM(x) = q*L*x/2 - q*x^2/2\nnumeric(M(a))\n", monkeypatch),
        r"M\left(a\right)",
    )[0]
    assert r"\frac{q a^{2}}{2}" in first, first
    assert "x" not in first.split("& = &", 1)[1], first


def test_a_call_at_its_own_variable_is_as_it_was(monkeypatch):
    # Its first row is the definition's, and the page writes it once.
    rows = _rows_from(_page(HEAD + "numeric(M(x))\n", monkeypatch), r"M\left(x\right)")
    assert r"R_{A} x - \frac{q x^{2}}{2}" in rows[0], rows
    assert r"\left(30.00\,\mathrm{kN}\right)\,x - " in rows[1], rows


def test_the_conditions_of_a_piecewise_read_the_argument(monkeypatch):
    page = _page(
        "L := 12[m]\nq1 := 8[kN/m]\nq2 := 4[kN/m]\na_q := 3[m]\n"
        "q_v(x) = piecewise(q1, x < a_q, q2, x <= L, 0*kN/m)\nnumeric(q_v(9*m))\n",
        monkeypatch,
    )
    first = page[page.index(r"q_{v}\left(9\,\mathrm{m}\right) & = &"):]
    first = first[: first.index(r"\end{cases}")]
    assert r"9\,\mathrm{m} < a_{q}" in first, first
    assert r"x < a_{q}" not in first, first


def test_result_writes_it_too(monkeypatch):
    first = _rows_from(_page(HEAD + "result(M(L/2))\n", monkeypatch), r"M\left(\frac{L}{2}\right)")[0]
    assert r"R_{A}\,\left(\frac{L}{2}\right)" in first, first


def test_a_negative_argument_in_a_sum_keeps_its_brackets(monkeypatch):
    # The additive rows print each term alone and join them with a sign: `L + - a`.
    first = _rows_from(
        _page("L := 6[m]\na := 2[m]\ng(x) = x + L\nnumeric(g(-a))\n", monkeypatch), r"g\left(- a\right)"
    )[0]
    right = first.split("& = &", 1)[1]
    assert r"\left(- a\right)" in right, right
    assert "+ - a" not in right, right


def test_a_negative_number_keeps_its_brackets(monkeypatch):
    first = _rows_from(
        _page("L := 6[m]\nq := 10[kN/m]\nf(n) = n*q*L\nnumeric(f(-2))\n", monkeypatch), r"f\left(-2\right)"
    )[0]
    assert r"\left(-2\right)\,q L" in first, first


def test_under_a_radical_and_in_a_function_it_goes_in_bare(monkeypatch):
    page = _page(
        "L := 6[m]\nq := 10[kN/m]\nr(x) = q*sqrt(x)\nnumeric(r(L/2))\nt(n) = q*L*exp(n)\nnumeric(t(1/2))\n",
        monkeypatch,
    )
    root = _rows_from(page, r"r\left(\frac{L}{2}\right)")[0]
    assert r"\sqrt{\frac{L}{2}}" in root, root
    power = _rows_from(page, r"t\left(\frac{1}{2}\right)")[0]
    assert r"e^{\frac{1}{2}}" in power, power


def test_an_exponent_goes_in_bare(monkeypatch):
    first = _rows_from(
        _page("L := 6[m]\nq := 10[kN/m]\np(n) = q*L*3^n\nnumeric(p(1/2))\n", monkeypatch),
        r"p\left(\frac{1}{2}\right)",
    )[0]
    assert r"3^{\frac{1}{2}}" in first, first


def test_a_call_with_a_free_variable_left_writes_the_others(monkeypatch):
    # A variable left free makes the row a partial one, drawn by its own function.
    first = _rows_from(
        _page("L := 6[m]\nq := 10[kN/m]\nF(x, y) = q*x*y - q*y^2\nnumeric(F(L/2, y))\n", monkeypatch),
        r"F\left(\frac{L}{2}, y\right)",
    )[0]
    assert r"q\,\left(\frac{L}{2}\right)\,y" in first, first


def test_a_partial_first_row_that_wraps_is_counted_with_its_argument(monkeypatch):
    page = _page(
        "L_1 := 6[m]\nL_2 := 4[m]\nL_3 := 5[m]\nq := 10[kN/m]\nP := 20[kN]\nw := 3[kN/m^2]\n"
        "R_A = q*L_1/2\nM(x, y) = R_A*x - q*x^2/2 + P*x/3 - w*x^3/6 + q*y^2\n"
        "numeric(M((L_1 + L_2 + L_3)/2, y))\n",
        monkeypatch,
    )
    assert r"\quad - \frac{q\,\left(\frac{L_{1}}{2} + \frac{L_{2}}{2} + \frac{L_{3}}{2}\right)^{2}}{2}" in page, page


def test_the_base_of_a_power_takes_brackets(monkeypatch):
    first = _rows_from(
        _page("L := 6[m]\nq := 10[kN/m]\nu(x) = q*x^2\nnumeric(u(L/2))\n", monkeypatch), r"u\left(\frac{L}{2}\right)"
    )[0]
    assert r"\left(\frac{L}{2}\right)^{2}" in first, first


def test_a_free_argument_is_put_in_once(monkeypatch):
    first = _rows_from(_page(HEAD + "numeric(M(L - x))\n", monkeypatch), r"M\left(L - x\right)")[0]
    assert r"R_{A} \left(L - x\right)" in first, first
    assert r"L - \left(L - x\right)" not in first, first


def test_a_first_row_that_wraps_is_counted_with_its_argument(monkeypatch):
    # The rows are counted a second time for their spacing; counted without the argument,
    # a first row that wraps only with it raised "spacing metadata does not match".
    page = _page(
        "L_1 := 6[m]\nL_2 := 4[m]\nL_3 := 5[m]\nq := 10[kN/m]\nP := 20[kN]\nw := 3[kN/m^2]\n"
        "R_A = q*L_1/2\nM(x) = R_A*x - q*x^2/2 + P*x/3 - w*x^3/6\nnumeric(M((L_1 + L_2 + L_3)/2))\n",
        monkeypatch,
    )
    assert r"\quad - \frac{q\,\left(\frac{L_{1}}{2} + \frac{L_{2}}{2} + \frac{L_{3}}{2}\right)^{2}}{2}" in page, page
    assert page.rstrip().endswith(r"-217.19\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), page


def test_the_one_line_rendering_writes_it_too():
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.models import ParsedHeading
    from engcalc_colab.parser import parse_cell
    from engcalc_colab.renderer import render_result

    engine = EngineeringEngine()
    results = [
        engine.evaluate(item)
        for item in parse_cell(HEAD + "numeric(M(L/2))\n")
        if not isinstance(item, ParsedHeading)
    ]
    formula = render_result(results[-1]).split(" = ")[1]
    assert r"\left(\frac{L}{2}\right)" in formula, formula
    assert "x" not in formula, formula


def test_a_matrix_body_writes_it_too(monkeypatch):
    page = _page(
        "E := 200[GPa]\nA := 10[cm^2]\nL := 3[m]\nk = E*A/L\nK(x) = [k*x, 0; 0, k]\nnumeric(K(L))\n",
        monkeypatch,
    )
    first = page[page.index(r"K\left(L\right) & = &"):]
    first = first[: first.index(r"\end{matrix}")]
    assert r"k L & 0" in first, first
    assert r"k x" not in first, first
