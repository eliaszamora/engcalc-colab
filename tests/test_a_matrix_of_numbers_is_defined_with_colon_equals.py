r"""`d := solve(K, F)`: a matrix defined by its numbers, as `:=` defines a scalar.

    K = [2*kN/m, -1*kN/m; -1*kN/m, 1*kN/m]
    F = [0*kN; 10*kN]
    d := solve(K, F)          d = K^{-1} F = [10.00 m; 20.00 m]
    u := d[2,1]               u = 20.00 m
    f := K*d - F              f = K d - F = [0; 0]

`=` keeps a matrix as formulas, which is what a derivation wants and what a frame of
six degrees of freedom cannot afford: `d = solve(K, F)` on the portal frame stored and
printed its closed form, about 30 kB of LaTeX that took ten seconds and that nobody could
read, and `numeric(d)` opened with it too. `:=` already meant "the number, not the
formula" for a scalar. It means the same for a matrix now: the right side is worked out
in numbers, the page shows it as written and then its value, and the name holds the
numbers for the lines after it - indexing, products, sums, `transpose`, `inv`, `solve`,
and matrices written `[a; b]` on the line itself.

Approved by Elías on 2026-09-24 ("Sí, apruebo d := solve(K, F), procede").
"""

import contextlib
import io
import pathlib
import re
import time

import numpy as np
import pytest
from IPython.display import Math

import engcalc_colab.magic as magic
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.matrix_numeric import QuantityMatrix
from engcalc_colab.models import NumericAssignmentResult, ParsedHeading, ParsedNarrative
from engcalc_colab.parser import parse_cell

SPRINGS = "K = [2*kN/m, -1*kN/m; -1*kN/m, 1*kN/m]\nF = [0*kN; 10*kN]\n"

FRAME = (pathlib.Path(__file__).parent.parent / "tools" / "portico_matricial.eng").read_text(
    encoding="utf-8"
)


def run(source: str) -> tuple[EngineeringEngine, list]:
    engine = EngineeringEngine()
    results = [
        engine.evaluate(statement)
        for statement in parse_cell(source)
        if not isinstance(statement, (ParsedHeading, ParsedNarrative))
    ]
    return engine, results


def column(matrix: QuantityMatrix, unit: str) -> list[float]:
    return [float(entry.to(unit).magnitude) for entry in matrix]


@pytest.fixture
def sheet(monkeypatch):
    def render(source: str) -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        page = " ".join(item.data for item in captured if isinstance(item, Math))
        return page, console.getvalue()

    return render


def test_a_solve_is_worked_out_in_numbers():
    engine, results = run(SPRINGS + "d := solve(K, F)\n")
    d = results[-1].quantity_matrix
    assert (d.rows, d.cols) == (2, 1)
    assert column(d, "m") == pytest.approx([10.0, 20.0])
    assert engine.numeric_context.matrices["d"] is d


def test_the_page_shows_the_solve_as_written_and_then_its_numbers(sheet):
    page, console = sheet(SPRINGS + "d := solve(K, F)\n")
    assert not console, console
    assert r"d & = & \displaystyle K^{-1}\,F" in page, page
    assert re.search(r"10\.00.*20\.00", page), page


def test_a_part_of_it_is_a_number_the_sheet_can_use():
    engine, results = run(SPRINGS + "d := solve(K, F)\nu := d[2,1]\nv := 2*d[1,1] + u\n")
    assert isinstance(results[-2], NumericAssignmentResult)
    assert results[-2].quantity.to("m").magnitude == pytest.approx(20.0)
    assert results[-1].quantity.to("m").magnitude == pytest.approx(40.0)
    assert "u" not in engine.numeric_context.matrices


def test_a_number_taken_from_it_reaches_a_numeric_line(sheet):
    page, console = sheet(SPRINGS + "d := solve(K, F)\nu := d[2,1]\nnumeric(u/2)\n")
    assert not console, console
    assert "10.00" in page.split("u", 1)[1], page


def test_products_and_sums_keep_their_units():
    _engine, results = run(SPRINGS + "d := solve(K, F)\nf := K*d - F\ng := transpose(K)*d\n")
    residual = results[-2].quantity_matrix
    assert column(residual, "kN") == pytest.approx([0.0, 0.0], abs=1e-9)
    assert column(results[-1].quantity_matrix, "kN") == pytest.approx([0.0, 10.0], abs=1e-9)


def test_a_sum_is_written_in_the_order_it_was_written(sheet):
    page, console = sheet(SPRINGS + "d := solve(K, F)\nf := K*d - F\n")
    assert not console, console
    assert r"f & = & \displaystyle K\,d - F" in page, page


def test_a_matrix_written_on_the_line_is_read_in_numbers():
    _engine, results = run(SPRINGS + "d := solve(K, F)\ne := [0*m; d[1,1]; d[2,1]]\n")
    e = results[-1].quantity_matrix
    assert (e.rows, e.cols) == (3, 1)
    assert column(e, "m") == pytest.approx([0.0, 10.0, 20.0])


def test_an_inverse_and_a_scalar_factor():
    _engine, results = run(SPRINGS + "C := 2*inv(K)\n")
    c = results[-1].quantity_matrix
    assert column(c, "m/kN") == pytest.approx([2.0, 2.0, 2.0, 4.0])


def test_a_rotation_comes_out_without_a_unit():
    """A beam's end: a displacement and a rotation, from a force and no moment."""
    source = (
        "E := 200*GPa\nI := 8000*cm^4\nL := 3*m\nP := 10*kN\n"
        "K = [12*E*I/L^3, -6*E*I/L^2; -6*E*I/L^2, 4*E*I/L]\n"
        "F = [P; 0]\n"
        "d := solve(K, F)\n"
    )
    _engine, results = run(source)
    d = results[-1].quantity_matrix
    EI = 200e9 * 8000e-8
    L = 3.0
    expected = np.linalg.solve(
        [[12 * EI / L**3, -6 * EI / L**2], [-6 * EI / L**2, 4 * EI / L]], [10e3, 0.0]
    )
    assert d.entry(0, 0).to("m").magnitude == pytest.approx(expected[0])
    assert d.entry(1, 0).dimensionless
    assert float(d.entry(1, 0).to("").magnitude) == pytest.approx(expected[1])


def test_the_portal_frame_solves_in_numbers_and_quickly(sheet):
    """Six degrees of freedom, three members, the values NumPy gives."""
    start = time.perf_counter()
    page, console = sheet(FRAME)
    elapsed = time.perf_counter() - start
    assert not console, console
    assert elapsed < 20, elapsed
    assert r"d & = & \displaystyle K^{-1}\,F" in page
    # The rows that show `d` are a column of six numbers, not a closed form.
    d_rows = page.split(r"d & = & \displaystyle K^{-1}\,F", 1)[1].split(r"D_{1}", 1)[0]
    assert len(d_rows) < 1500, len(d_rows)
    for shown in ("6.28", "6.24"):
        assert shown in d_rows, d_rows


def test_the_portal_frame_matches_numpy():
    engine, results = run(FRAME)
    d = engine.numeric_context.matrices["d"]
    assert d.entry(0, 0).to("cm").magnitude == pytest.approx(0.62827, rel=1e-4)
    assert d.entry(3, 0).to("cm").magnitude == pytest.approx(0.62392, rel=1e-4)
    assert float(d.entry(2, 0).to("").magnitude) == pytest.approx(-0.00202, rel=2e-3)
    # Equilibrium of the whole frame: the base reactions balance the loads.
    R_1 = engine.numeric_context.matrices["R_1"]
    R_4 = engine.numeric_context.matrices["R_4"]
    H = 3000.0
    wL = 2000.0 * 6
    assert float(R_1.entry(0, 0).to("kgf").magnitude) + float(
        R_4.entry(0, 0).to("kgf").magnitude
    ) == pytest.approx(-H, rel=1e-6)
    assert float(R_1.entry(1, 0).to("kgf").magnitude) + float(
        R_4.entry(1, 0).to("kgf").magnitude
    ) == pytest.approx(wL, rel=1e-6)


def test_a_redefinition_as_a_scalar_replaces_it():
    engine, results = run(SPRINGS + "d := solve(K, F)\nd := 2*m\n")
    assert "d" not in engine.numeric_context.matrices
    assert engine.numeric_context.values["d"].to("m").magnitude == pytest.approx(2.0)


def test_a_redefinition_as_a_formula_replaces_it():
    engine, results = run(SPRINGS + "d := solve(K, F)\nd = 2*m\n")
    assert "d" not in engine.numeric_context.matrices


def test_a_scalar_redefined_as_a_matrix_of_numbers_is_no_longer_a_scalar():
    engine, results = run(SPRINGS + "d := 2*m\nd := solve(K, F)\n")
    assert "d" not in engine.numeric_context.values
    assert "d" in engine.numeric_context.matrices


def test_a_formula_line_that_names_it_says_how_to_use_it():
    with pytest.raises(EngEvaluationError, match=r"'d' holds numbers.*:="):
        run(SPRINGS + "d := solve(K, F)\nx = 2*d\n")


def test_matrices_that_do_not_fit_say_so():
    with pytest.raises(EngEvaluationError, match="2x2.*2x1|2x1.*2x2"):
        run(SPRINGS + "x := K + F\n")
    with pytest.raises(EngEvaluationError, match="incompatible units"):
        run(SPRINGS + "d := solve(K, F)\nx := d + F\n")


def test_a_singular_matrix_says_so():
    with pytest.raises(EngEvaluationError, match="the matrix is singular - check the supports"):
        run("K = [1*kN/m, 1*kN/m; 1*kN/m, 1*kN/m]\nF = [1*kN; 1*kN]\nd := solve(K, F)\n")


def test_an_index_outside_it_says_so():
    with pytest.raises(EngEvaluationError, match=r"d\[3,1\].*2x1"):
        run(SPRINGS + "d := solve(K, F)\nu := d[3,1]\n")


def test_a_reset_forgets_it():
    engine, _results = run(SPRINGS + "d := solve(K, F)\n")
    engine.reset()
    assert not engine.numeric_context.matrices


def test_a_number_taken_from_it_is_shown_with_where_it_came_from(sheet):
    page, console = sheet(SPRINGS + "d := solve(K, F)\nu := d[2,1]\n")
    assert not console, console
    assert r"u & = & \displaystyle d_{2,1} = 20.00\,\mathrm{m}" in page, page


def test_the_frame_is_in_equilibrium(sheet):
    engine, _results = run(FRAME)
    for name in ("Sigma_F_x", "Sigma_F_y"):
        assert abs(float(engine.numeric_context.values[name].to("kgf").magnitude)) < 1e-6


def test_a_value_settled_with_colon_equals_outranks_a_matrix_of_formulas():
    """The precedence a scalar `:=` has always had: `K := 3*m` makes `K` that length."""
    _engine, results = run(SPRINGS + "K := 3*m\nx := 2*K\n")
    assert results[-1].quantity.to("m").magnitude == pytest.approx(6.0)


def test_one_index_takes_an_entry_of_a_column_or_a_row():
    _engine, results = run(SPRINGS + "d := solve(K, F)\nu := d[2]\nv := transpose(d)[1]\n")
    assert results[-2].quantity.to("m").magnitude == pytest.approx(20.0)
    assert results[-1].quantity.to("m").magnitude == pytest.approx(10.0)


def test_numeric_of_it_shows_its_numbers(sheet):
    """`numeric(d)` after `d := solve(K, F)`: the numbers, not an error."""
    page, console = sheet(SPRINGS + "d := solve(K, F)\nnumeric(d)\n")
    assert not console, console
    shown = page.split("K^{-1}", 1)[1]
    assert shown.count("10.00") == 2 and shown.count("20.00") == 2, shown
    # The name and its value, not `d = d = [...]`.
    assert shown.rstrip().endswith(r"\,\mathrm{m} \end{array}"), shown
    assert r"\displaystyle d & = & \displaystyle \left[\begin{matrix}" in shown, shown


def test_numeric_of_it_in_a_unit_converts_every_entry(sheet):
    page, console = sheet(SPRINGS + "d := solve(K, F)\nnumeric(d, cm)\n")
    assert not console, console
    # One unit, so the factor he chose to keep comes out: 10^3 [1.00; 2.00] cm.
    last = page.rsplit(r"\displaystyle d & = & ", 1)[1]
    assert last.startswith(r"\displaystyle 10^{3}"), last
    assert "1.00" in last and "2.00" in last and last.rstrip().endswith(r"\,\mathrm{cm} \end{array}"), last


def test_numeric_of_it_in_a_unit_that_does_not_fit_says_so():
    with pytest.raises(EngEvaluationError, match=r"\[1,1\].*kN"):
        run(SPRINGS + "d := solve(K, F)\nnumeric(d, kN)\n")


def test_an_entry_that_does_not_fit_is_named_the_way_the_page_writes_it():
    with pytest.raises(EngEvaluationError, match=r"entry \[1,1\] is 10 m, which cannot be written in kN"):
        run(SPRINGS + "d := solve(K, F)\nnumeric(d, kN)\n")
    source = (
        "E := 200*GPa\nI := 8000*cm^4\nL := 3*m\nP := 10*kN\n"
        "K = [12*E*I/L^3, -6*E*I/L^2; -6*E*I/L^2, 4*E*I/L]\n"
        "F = [P; 0]\nd := solve(K, F)\nnumeric(d, mm)\n"
    )
    with pytest.raises(EngEvaluationError, match=r"entry \[2,1\] is 0\.00281, a number without a unit,"):
        run(source)


def test_a_row_of_matrices_is_written_as_a_matrix(sheet):
    """`fv := k*d + [f0_D, f0_L, Z_6]` printed the brackets as source text."""
    page, console = sheet(SPRINGS + "d := solve(K, F)\nG := [d, d] + [d, d]\n")
    assert not console, console
    written = page.split(r"G & = & \displaystyle ", 1)[1].split(r"\\", 1)[0]
    assert "[d, d]" not in written, written
    assert r"\left[\begin{matrix}\displaystyle d & \displaystyle d\end{matrix}\right]" in written, written
