r"""A value written out with `=` stands as its name in a formula that also has a name standing.

His decision of 2026-09-27 ("Procede según tus recomendaciones"): `L = 3*m` then
`M = q*L^2/2`, `q` with no value, read `9 m^2 q/2`; with `L := 3[m]` and `q_1 = 10*kN/m`,
`M_1 = q_1*L^2/2` read `5 kN L^2/m` - neither the formula nor the number. They read
`q L^2/2` and `q_1 L^2/2`. A line whose every name is a value written out still ends on
its number: `L = 6*m`, `q = 10*kN/m`, `M = q*L^2/8` reads `45 kN m`, as before.
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


def _row(page: str, head: str) -> str:
    start = page.index(head + r" & = &")
    ends = [i for i in (page.find(r"\\[", start), page.find(r"\end{array}", start)) if i != -1]
    return page[start:min(ends)]


def test_beside_a_name_with_no_value_it_stands(monkeypatch):
    row = _row(_page("L = 3*m\nM = q*L^2/2\n", monkeypatch), "M")
    assert r"\frac{q L^{2}}{2}" in row, row
    assert r"9\,\mathrm{m}^{2}" not in row, row


def test_beside_a_colon_equals_value_it_stands(monkeypatch):
    row = _row(_page("L := 3[m]\nq_1 = 10*kN/m\nM_1 = q_1*L^2/2\n", monkeypatch), "M_{1}")
    assert r"\frac{q_{1} L^{2}}{2}" in row, row
    assert r"5\,\mathrm{kN}" not in row, row


def test_a_line_of_values_still_ends_on_its_number(monkeypatch):
    row = _row(_page("L = 6*m\nq = 10*kN/m\nM = q*L^2/8\n", monkeypatch), "M")
    assert row.rstrip().endswith(r"45\,\mathrm{kN} \cdot \mathrm{m}"), row


def test_numeric_puts_its_number_in(monkeypatch):
    page = _page("L := 3[m]\nq_1 = 10*kN/m\nM_1 = q_1*L^2/2\nnumeric(M_1)\n", monkeypatch)
    rows = page[page.rindex(r"M_{1} & = &"):]
    assert r"\left(10.00\,\frac{\mathrm{kN}}{\mathrm{m}}\right)\,\left(3.00\,\mathrm{m}\right)^{2}" in rows, rows
    assert rows.rstrip().endswith(r"45.00\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), rows


def test_a_formula_of_valued_names_then_stays_a_name(monkeypatch):
    # Every name `M` reads has a value now that `L` stands, so rule 2 keeps it: the
    # exclusion of 0.42.0 (`10 kN (6 m)^2/(8 m)`) was for an `L` folded inside `M`.
    page = _page("q := 10*kN/m\nL = 6*m\nM = q*L^2/8\ny = 2*M\nnumeric(y)\n", monkeypatch)
    assert r"\frac{q L^{2}}{8}" in _row(page, "M"), page
    assert r"2 M" in _row(page, "y"), page
    assert page.rstrip().endswith(r"90.00\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), page


def test_a_later_line_reads_it_as_the_formula_did(monkeypatch):
    row = _row(_page("L = 3*m\nM = q*L^2/2\ny = 2*M\n", monkeypatch), "y")
    assert "L" in row, row
    assert r"9\,\mathrm{m}^{2}" not in row, row


def test_a_function_reads_it_beside_its_variable(monkeypatch):
    row = _row(_page("L = 6*m\nq = 10*kN/m\nM(x) = q*L*x/2 - q*x^2/2\n", monkeypatch), r"M\left(x\right)")
    assert r"\frac{q L x}{2}" in row, row
    assert r"30\,\mathrm{kN}" not in row, row


def test_a_value_changed_later_is_not_read_into_an_older_formula(monkeypatch):
    # `M` was worked out with 3 m; after `L = 4*m` its formula in `L` is no longer true.
    page = _page("L = 3*m\nM = q*L^2/2\nL = 4*m\ny = 2*M\n", monkeypatch)
    row = _row(page, "y")
    assert row.rstrip().endswith(r"9\,\mathrm{m}^{2}\,q"), row
    assert r"q L^{2}" not in row, row


def test_numeric_of_a_call_puts_its_number_in(monkeypatch):
    page = _page("q := 10[kN/m]\nL = 6*m\nM(x) = q*L*x/2 - q*x^2/2\nnumeric(M(2*m))\n", monkeypatch)
    assert r"\left(6.00\,\mathrm{m}\right)\,\left(2.00\,\mathrm{m}\right)" in page, page
    assert r"\,L\," not in page, page


def test_numeric_of_a_matrix_puts_its_number_in(monkeypatch):
    page = _page("q := 10[kN/m]\nL = 6*m\nK = [q*L, 0; 0, q*L/2]\nnumeric(K)\n", monkeypatch)
    assert r"\left(6.00\,\mathrm{m}\right)" in page, page
    assert r"60.00 & 0.00" in page, page


def test_numeric_of_a_name_worked_out_before_the_value_changed(monkeypatch):
    # `M_1` holds 45 kN m, worked out with 10 kN/m; its formula in `q_1` no longer holds.
    page = _page(
        "L := 3[m]\nq_1 = 10*kN/m\nM_1 = q_1*L^2/2\nq_1 = 20*kN/m\nnumeric(M_1)\n", monkeypatch
    )
    assert page.rstrip().endswith(r"45.00\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), page
    assert r"20.00\,\frac{\mathrm{kN}}{\mathrm{m}}" not in page, page


def test_numeric_of_a_call_worked_out_before_the_value_changed(monkeypatch):
    page = _page(
        "q := 10[kN/m]\nL = 6*m\nM(x) = q*L*x/2 - q*x^2/2\nL = 8*m\nnumeric(M(2*m))\n", monkeypatch
    )
    assert page.rstrip().endswith(r"40.00\,\mathrm{kN} \cdot \mathrm{m} \end{array}"), page
    assert r"8.00\,\mathrm{m}" not in page, page


def test_a_matrix_written_on_the_line_reads_it_too(monkeypatch):
    page = _page("L = 3*m\nK = [q*L, 0; 0, q]\n", monkeypatch)
    row = page[page.index(r"K & = &"):]
    assert r"q L & 0" in row, row


def test_a_value_written_as_a_sum_stands_too(monkeypatch):
    row = _row(_page("L = 3*m + 20*cm\nM = q*L^2/2\n", monkeypatch), "M")
    assert r"\frac{q L^{2}}{2}" in row, row


def test_a_number_worked_out_with_equals_stands_too(monkeypatch):
    # Read from the value, not the line: on a rule that asked the line to read no name,
    # `V(x)` read `30 kN - q x`, the mixture decided against one step further on.
    page = _page("L = 6*m\nq = 10*kN/m\nR_A = q*L/2\nV(x) = R_A - q*x\nx_1 = 2*L\nF = P*x_1\n", monkeypatch)
    assert r"R_{A} - q x" in _row(page, r"V\left(x\right)"), page
    assert r"P x_{1}" in _row(page, "F"), page


def test_a_name_defined_again_as_a_formula_is_expanded(monkeypatch):
    row = _row(_page("L = 3*m\nL = 2*b\nM = q*L\n", monkeypatch), "M")
    assert r"2 b q" in row, row


def test_a_name_that_is_a_formula_is_as_it_was(monkeypatch):
    # `a` reads `L` and `b`: a formula, not a value written out; it is not kept (no
    # value for `b`), and `M` reads it expanded as before - in `L`, now standing.
    row = _row(_page("L = 3*m\na = b*L\nM = q*a\n", monkeypatch), "M")
    assert "b" in row and "q" in row, row
