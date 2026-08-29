from IPython.display import HTML, Math


def _capture(cell, monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng("", cell)
    return displayed


def test_consecutive_equations_render_as_one_aligned_math_block(monkeypatch):
    displayed = _capture("### Reacciones\nA = 1\nB = 2", monkeypatch)

    assert [type(item) for item in displayed] == [HTML, Math]
    assert r"\hspace{0.2em}\begin{array}{lcl}" in displayed[1].data
    assert r"\displaystyle A & = & \displaystyle 1" in displayed[1].data
    assert r"\displaystyle B & = & \displaystyle 2" in displayed[1].data
    assert r"\begin{aligned}" not in displayed[1].data


def test_blank_line_inside_equation_group_uses_sixteen_point_spacing(monkeypatch):
    displayed = _capture("### Reacciones\nA = 1\n\nB = 2", monkeypatch)

    assert [type(item) for item in displayed] == [HTML, Math]
    assert r"\\[16pt]" in displayed[1].data


def test_level_two_heading_has_stronger_visual_hierarchy(monkeypatch):
    displayed = _capture("## Estado 0: cargas reales\n### Reacciones\nA = 1", monkeypatch)

    assert [type(item) for item in displayed] == [HTML, HTML, Math]
    assert "border-bottom" in displayed[0].data
    assert "border-bottom" not in displayed[1].data


def test_regular_equation_rows_use_eight_point_spacing(monkeypatch):
    displayed = _capture("### Reacciones\nA = 1\nB = 2", monkeypatch)

    assert r"\\[8pt]" in displayed[1].data
    assert r"\\[2pt]" not in displayed[1].data


def test_heading_margins_and_divider_are_subtle(monkeypatch):
    displayed = _capture("## Estado 0\n### Reacciones\nA = 1", monkeypatch)

    assert "rgba(127,127,127,0.18)" in displayed[0].data
    assert "margin:0.60rem 0 0.34rem 0" in displayed[0].data
    assert "margin:0.46rem 0 0.24rem 0" in displayed[1].data


def test_three_column_layout_keeps_extra_equals_on_right_side(monkeypatch):
    displayed = _capture(
        "### Compatibilidad\nA = integral(x, x, 0, L)",
        monkeypatch,
    )

    math = displayed[1].data
    assert r"\begin{array}{lcl}" in math
    assert r"\displaystyle A & = & \displaystyle" in math
    assert r"\int" in math
    # render_result may include a second equality for the evaluated integral;
    # only the assignment equality becomes the dedicated center column.
    assert math.count(" & = & ") == 1


def test_standalone_expression_uses_left_column_without_fake_equals(monkeypatch):
    displayed = _capture("### Resultado\nx^2 + 1", monkeypatch)

    math = displayed[1].data
    assert r"\displaystyle x^{2} + 1 & &" in math
    assert " & = & " not in math
