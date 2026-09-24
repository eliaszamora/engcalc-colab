r"""What the ultra review of everything since 0.33.6 (#299) found, each reproduced first.

    s_max := min(3*h, d[1,1])            min cannot be worked out in numbers on a := line
    r := [d[1,1], d[2,1]]                '[d[1, 1], d[2, 1]]' cannot be worked out ...
    y := M(3*m)*d[1,1]/m                 unsupported numeric function 'M'
    K = [...]; K := solve(K, F); y = 2*K y used the old formula, in silence
    D := [0;                             unbalanced parentheses
          d[1,1]]

A `:=` line that reads a matrix goes to `_MatrixNumbers`, and everything on it that was
not a matrix operation had to be something `NumericContext` knew - so `min`, `max`, a
function of the sheet and a row written with commas stopped the line. A name defined with
`=` and then given numbers with `:=` kept its formula beside them, and a `=` line went on
reading the formula. And the gate that lets a matrix run over several lines knew only `=`.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell

SPRINGS = "K = [2*kN/m, -1*kN/m; -1*kN/m, 1*kN/m]\nF = [0*kN; 10*kN]\nd := solve(K, F)\n"


def run(source: str):
    engine = EngineeringEngine()
    return engine, [engine.evaluate(statement) for statement in parse_cell(source)]


def test_min_and_max_take_an_entry_of_a_matrix():
    _engine, results = run(SPRINGS + "h := 3*m\ns := min(3*h, d[1,1])\nt := max(d[1,1], d[2,1])\n")
    assert results[-2].quantity.to("m").magnitude == pytest.approx(9.0)
    assert results[-1].quantity.to("m").magnitude == pytest.approx(20.0)


def test_a_row_written_with_commas_is_a_row():
    _engine, results = run(SPRINGS + "r := [d[1,1], d[2,1]]\n")
    r = results[-1].quantity_matrix
    assert (r.rows, r.cols) == (1, 2)
    assert [e.to("m").magnitude for e in r] == pytest.approx([10.0, 20.0])


def test_a_function_of_the_sheet_on_a_line_that_reads_a_matrix():
    _engine, results = run(SPRINGS + "M(x) = 2*kN*x\ny := M(3*m)*d[1,1]/m\nz := M(d[1,1])\n")
    assert results[-2].quantity.to("kN*m").magnitude == pytest.approx(60.0)
    assert results[-1].quantity.to("kN*m").magnitude == pytest.approx(20.0)


def test_a_formula_given_numbers_is_no_longer_read_as_the_formula():
    """`y = 2*K` after `K := solve(K, F)` read the old K. It says to use `:=` now."""
    with pytest.raises(EngEvaluationError, match=r"'K' holds numbers"):
        run(
            "K = [2*kN/m, -1*kN/m; -1*kN/m, 1*kN/m]\nF = [0*kN; 10*kN]\n"
            "K := solve(K, F)\ny = 2*K\n"
        )


def test_a_formula_given_numbers_still_shows_them():
    engine, results = run(
        "K = [2*kN/m, -1*kN/m; -1*kN/m, 1*kN/m]\nF = [0*kN; 10*kN]\n"
        "K := solve(K, F)\nnumeric(K)\n"
    )
    assert "K" not in engine.namespace
    assert [e.to("m").magnitude for e in results[-1].quantity_matrix] == pytest.approx([10.0, 20.0])


def test_a_matrix_on_a_colon_equals_line_may_run_over_several_lines():
    _engine, results = run(SPRINGS + "D := [0*m;\n      d[1,1];\n      d[2,1]]\n")
    D = results[-1].quantity_matrix
    assert [e.to("m").magnitude for e in D] == pytest.approx([0.0, 10.0, 20.0])


def test_a_matrix_argument_to_a_number_function_says_so():
    with pytest.raises(EngEvaluationError, match=r"min on a := line takes numbers"):
        run(SPRINGS + "s := min(d, 3*m)\n")
