import re

import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import (
    EigenvalueSet,
    EigenvectorSet,
    MatrixShape,
    NumericMatrixEvaluationResult,
    PartialMatrixNumericEvaluationResult,
)
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import RenderSettings, render_aligned_results, render_result


def evaluate(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def _matrix_markers(latex: str) -> None:
    assert r"\left[" in latex
    assert r"\begin{matrix}" in latex
    assert r"\end{matrix}" in latex
    assert r"\right]" in latex
    assert "Matrix([[" not in latex


def test_symbolic_matrix_rendering_is_native_mathjax_in_direct_and_aligned_paths():
    engine = EngineeringEngine()
    result = evaluate(engine, "A = [a, b; c, d]")

    direct = render_result(result)
    aligned = render_aligned_results([result])

    _matrix_markers(direct)
    _matrix_markers(aligned)
    assert "a & b" in direct
    assert "c & d" in direct
    assert r"\\" in direct
    assert r"\begin{array}{lcl}" in aligned


def test_row_and_column_vectors_keep_their_orientation():
    engine = EngineeringEngine()
    row = render_result(evaluate(engine, "r = [a, b, c]"))
    column = render_result(evaluate(engine, "cvec = [a; b; c]"))

    _matrix_markers(row)
    _matrix_markers(column)
    assert "a & b & c" in row
    assert r"a\\b\\c" in column


def test_homogeneous_quantity_matrix_uses_one_common_unit_and_bare_cells():
    import engcalc_colab.renderer as renderer

    engine = EngineeringEngine()
    evaluate(engine, "k := 10*kN/mm")
    evaluate(engine, "A = [2*k, 0; 0, 3*k]")
    result = evaluate(engine, "numeric(A)")
    assert isinstance(result, NumericMatrixEvaluationResult)

    latex = renderer._quantity_matrix_latex(
        result.quantity_matrix,
        RenderSettings(precision=2),
    )

    _matrix_markers(latex)
    assert "20.00" in latex
    assert "30.00" in latex
    assert len(re.findall(r"(?<!\d)0\.00(?!\d)", latex)) == 2
    assert latex.count(r"\mathrm{kN}") == 1
    assert latex.count(r"\mathrm{mm}") == 1


def test_quantity_matrix_respects_precision_and_zero_tolerance_per_cell():
    import engcalc_colab.renderer as renderer

    engine = EngineeringEngine()
    evaluate(engine, "k := 10*kN/mm")
    evaluate(engine, "A = [1.23456*k, 1e-8*k; 0, 2*k]")
    result = evaluate(engine, "numeric(A)")

    latex = renderer._quantity_matrix_latex(
        result.quantity_matrix,
        RenderSettings(precision=3, zero_tolerance=1e-6),
    )

    assert "12.346" in latex
    assert len(re.findall(r"(?<!\d)0\.000(?!\d)", latex)) == 2
    assert "20.000" in latex


def test_heterogeneous_quantity_matrix_keeps_units_inside_each_cell():
    import engcalc_colab.renderer as renderer

    engine = EngineeringEngine()
    evaluate(engine, "E := 200*GPa")
    evaluate(engine, "I := 450e6*mm^4")
    evaluate(engine, "L := 6000*mm")
    evaluate(engine, "K = [12*E*I/L^3, 6*E*I/L^2; 6*E*I/L^2, 4*E*I/L]")
    result = evaluate(engine, "numeric(K)")

    latex = renderer._quantity_matrix_latex(result.quantity_matrix, RenderSettings())

    _matrix_markers(latex)
    # A beam stiffness submatrix legitimately mixes force/length, force and force*length.
    # The spec requires a unit in each cell, not conversion to one canonical engineering unit.
    assert latex.count(r"\mathrm{GPa}") == 4
    assert latex.count(r"\mathrm{mm}") >= 4
    assert not latex.rstrip().endswith(r"\mathrm{mm}")


def test_numeric_matrix_renders_formula_substitution_and_final_stages():
    engine = EngineeringEngine()
    evaluate(engine, "k := 10*kN/mm")
    evaluate(engine, "A = [k, 0; 0, 2*k]")

    result = evaluate(engine, "numeric(A)")
    latex = render_result(result)
    aligned = render_aligned_results([result])

    assert isinstance(result, NumericMatrixEvaluationResult)
    _matrix_markers(latex)
    assert latex.startswith("A = ")
    assert latex.count(" = ") == 3
    assert latex.count(r"\begin{matrix}") == 3
    assert "10.00" in latex and "20.00" in latex
    assert aligned.count(" & = & ") == 3
    assert aligned.count(r"\begin{matrix}") == 3


def test_result_matrix_compacts_away_substitution_stage():
    engine = EngineeringEngine()
    evaluate(engine, "k := 10*kN/mm")
    evaluate(engine, "A = [k, 0; 0, 2*k]")

    result = evaluate(engine, "result(A)")
    latex = render_result(result)

    assert isinstance(result, NumericMatrixEvaluationResult)
    assert latex.count(" = ") == 2
    assert latex.count(r"\begin{matrix}") == 2
    assert "10.00" in latex and "20.00" in latex


def test_partial_numeric_matrix_renders_known_substitutions_without_fake_final_matrix():
    engine = EngineeringEngine()
    evaluate(engine, "k := 10*kN/mm")
    evaluate(engine, "A = [k, x; 0, 2*k]")

    result = evaluate(engine, "numeric(A)")
    latex = render_result(result)
    aligned = render_aligned_results([result])

    assert isinstance(result, PartialMatrixNumericEvaluationResult)
    assert result.unresolved_symbols == ("x",)
    assert latex.count(r"\begin{matrix}") == 2
    assert latex.count(" = ") == 2
    assert "x" in latex
    assert "10.00" in latex
    assert aligned.count(r"\begin{matrix}") == 2
    assert aligned.count(" & = & ") == 2


def test_matrix_shape_renders_as_mathematical_ordered_pair():
    engine = EngineeringEngine()
    evaluate(engine, "A = [1, 2, 3; 4, 5, 6]")
    result = evaluate(engine, "s = size(A)")

    assert isinstance(result.value, MatrixShape)
    latex = render_result(result)
    aligned = render_aligned_results([result])

    assert latex == r"s = \left(2, 3\right)"
    assert r"s & = & \displaystyle \left(2, 3\right)" in aligned


def test_eigenvalue_rendering_is_deterministic_and_keeps_multiplicity():
    engine = EngineeringEngine()
    evaluate(engine, "A = [2, 0, 0; 0, 2, 0; 0, 0, 3]")
    result = evaluate(engine, "lam = eigenvals(A)")

    assert isinstance(result.value, EigenvalueSet)
    latex = render_result(result)
    aligned = render_aligned_results([result])

    assert "2" in latex and "3" in latex
    assert "m=2" in latex
    assert "m=1" in latex
    assert latex.index("2") < latex.index("3")
    assert r"\begin{array}{lcl}" in aligned


def test_eigenvector_rendering_keeps_vectors_as_native_matrices():
    engine = EngineeringEngine()
    evaluate(engine, "A = [2, 0; 0, 3]")
    result = evaluate(engine, "modes = eigenvects(A)")

    assert isinstance(result.value, EigenvectorSet)
    latex = render_result(result)

    assert "2" in latex and "3" in latex
    assert latex.count("m=1") == 2
    assert latex.count(r"\begin{matrix}") == 2
    assert "Matrix([[" not in latex


def test_numeric_homogeneous_eigenvalues_render_with_common_physical_unit():
    engine = EngineeringEngine()
    evaluate(engine, "k := 10*kN/mm")
    evaluate(engine, "K = [k, 0; 0, 2*k]")
    result = evaluate(engine, "numeric(eigenvals(K))")

    assert isinstance(result.value, EigenvalueSet)
    latex = render_result(result)

    assert "10.00" in latex and "20.00" in latex
    assert latex.count(r"\mathrm{kN}") == 2
    assert latex.count(r"\mathrm{mm}") == 2
    assert "m=1" in latex
