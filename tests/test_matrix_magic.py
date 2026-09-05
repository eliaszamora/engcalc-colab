from IPython.display import Math


def test_eng_magic_groups_symbolic_matrix_calculations_in_one_mathjax_display(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng("", "A = [a, b; c, d]\nB = transpose(A)")

    assert [type(item) for item in displayed] == [Math]
    latex = displayed[0].data
    assert latex.count(r"\begin{matrix}") == 2
    assert "Matrix([[" not in latex
    assert r"\begin{array}{lcl}" in latex


def test_eng_magic_groups_matrix_numeric_stages_without_traceback(monkeypatch, capsys):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "k := 10*kN/mm\nA = [k, 0; 0, 2*k]\nnumeric(A)\nresult(A)",
    )

    assert [type(item) for item in displayed] == [Math]
    latex = displayed[0].data
    # Five matrices, named so the number means something: the definition, the two
    # stages `numeric(A)` adds to it, and the two `result(A)` prints on its own.
    #
    # This read `>= 6` while `numeric(A)` opened by restating the definition verbatim,
    # immediately below it. That row is gone - see
    # tests/test_a_formula_is_not_restated_by_its_own_evaluation.py - and the block now
    # continues from the definition instead. `result(A)` still restates the formula,
    # correctly: the row above it is the numeric result, not the definition.
    assert latex.count(r"\begin{matrix}") == 5
    assert "10.00" in latex and "20.00" in latex
    assert "Matrix([[" not in latex
    assert "Traceback" not in capsys.readouterr().out


def test_eng_magic_uses_active_precision_for_numerical_matrix_cells(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng_config("precision=4 zero_tolerance=1e-6")
    magics.eng("", "k := 10*kN/mm\nA = [1.23456*k, 1e-8*k; 0, 2*k]\nresult(A)")

    assert [type(item) for item in displayed] == [Math]
    latex = displayed[0].data
    assert "12.3456" in latex
    assert latex.count("0.0000") >= 2
    assert "20.0000" in latex


def test_eng_magic_renders_shape_and_eigen_analysis_in_source_order(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "A = [2, 0; 0, 3]\ns = size(A)\nlam = eigenvals(A)\nmodes = eigenvects(A)",
    )

    assert [type(item) for item in displayed] == [Math]
    latex = displayed[0].data
    assert r"\left(2, 2\right)" in latex
    assert "m=1" in latex
    assert latex.count(r"\begin{matrix}") >= 3
    assert "Matrix([[" not in latex
