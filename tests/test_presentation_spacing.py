from IPython.display import HTML, Math


def test_section_heading_has_slightly_more_vertical_separation(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng("", "## Análisis de la viga\nA = 1")

    assert [type(item) for item in displayed] == [HTML, Math]
    assert "margin:0.60rem 0 0.34rem 0" in displayed[0].data


def test_subsection_heading_has_slightly_more_vertical_separation(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng("", "### Momento flector\nA = 1")

    assert [type(item) for item in displayed] == [HTML, Math]
    assert "margin:0.46rem 0 0.24rem 0" in displayed[0].data


def test_narrative_block_has_more_air_before_following_equation(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng("", '"""Texto explicativo."""\nA = 1')

    assert [type(item) for item in displayed] == [HTML, Math]
    assert "margin:0.36rem 0 0.60rem 0" in displayed[0].data
