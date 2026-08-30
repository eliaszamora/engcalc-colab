import pytest
from IPython.display import Math

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import NumericMatrixEvaluationResult
from engcalc_colab.parser import parse_cell


def eval_cell(engine: EngineeringEngine, source: str):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def test_piecewise_matrix_cell_evaluates_entrywise_with_dimensional_zero():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "k1 := 10*kN/mm\n"
        "k2 := 20*kN/mm\n"
        "k3 := 30*kN/mm\n"
        "L := 2*m\n"
        "K(x) = [piecewise(k1, x < L/2, k2), 0; 0, k3]",
    )

    left = eval_cell(engine, "numeric(K(0.5*m))")[-1]
    right = eval_cell(engine, "numeric(K(1.5*m))")[-1]

    assert isinstance(left, NumericMatrixEvaluationResult)
    assert isinstance(right, NumericMatrixEvaluationResult)
    assert left.quantity_matrix.entry(0, 0).to("kN/mm").magnitude == pytest.approx(10.0)
    assert right.quantity_matrix.entry(0, 0).to("kN/mm").magnitude == pytest.approx(20.0)
    assert left.quantity_matrix.entry(1, 1).to("kN/mm").magnitude == pytest.approx(30.0)
    assert right.quantity_matrix.entry(1, 1).to("kN/mm").magnitude == pytest.approx(30.0)


def test_piecewise_matrix_function_respects_exact_breakpoint_ownership():
    engine = EngineeringEngine()
    eval_cell(
        engine,
        "k1 := 10*kN/mm\n"
        "k2 := 20*kN/mm\n"
        "L := 2*m\n"
        "K(x) = [piecewise(k1, x < L/2, k2), 0; 0, k1]",
    )

    at_breakpoint = eval_cell(engine, "numeric(K(1*m))")[-1]
    assert at_breakpoint.quantity_matrix.entry(0, 0).to("kN/mm").magnitude == pytest.approx(20.0)


def test_canonical_structural_worksheet_runs_in_one_eng_cell(monkeypatch, capsys):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "E := 200*GPa\n"
        "I := 450e6*mm^4\n"
        "L := 6000*mm\n"
        "P := 30*kN\n"
        "K = [12*E*I/L^3, 6*E*I/L^2;\n"
        "     6*E*I/L^2, 4*E*I/L]\n"
        "F = [P;\n"
        "     0]\n"
        "u = solve(K, F)\n"
        "numeric(K)\n"
        "numeric(u)",
    )

    assert [type(item) for item in displayed] == [Math]
    latex = displayed[0].data
    assert latex.count(r"\begin{matrix}") >= 7
    assert "K" in latex and "F" in latex and "u" in latex
    assert "30.00" in latex
    captured = capsys.readouterr()
    assert "Traceback" not in captured.out
    assert "EngCalc error" not in captured.out


def test_readme_documents_matrix_cas_syntax_and_current_scope():
    readme = open("README.md", encoding="utf-8").read()
    assert "Matrix/CAS" in readme
    assert "[a, b; c, d]" in readme
    assert "A[1,1]" in readme or "A[1, 1]" in readme
    assert "solve(A, b)" in readme
    assert "numeric(A)" in readme
    assert "whole-matrix" in readme.lower() or "matrices completas" in readme.lower()
