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
    assert r"\hspace{0.35em}\begin{aligned}" in displayed[1].data
    assert "A &=" in displayed[1].data
    assert "B &=" in displayed[1].data


def test_blank_line_inside_equation_group_becomes_compact_row_spacing(monkeypatch):
    displayed = _capture("### Reacciones\nA = 1\n\nB = 2", monkeypatch)

    assert [type(item) for item in displayed] == [HTML, Math]
    assert r"\\[6pt]" in displayed[1].data


def test_level_two_heading_has_stronger_visual_hierarchy(monkeypatch):
    displayed = _capture("## Estado 0: cargas reales\n### Reacciones\nA = 1", monkeypatch)

    assert [type(item) for item in displayed] == [HTML, HTML, Math]
    assert "border-bottom" in displayed[0].data
    assert "border-bottom" not in displayed[1].data
