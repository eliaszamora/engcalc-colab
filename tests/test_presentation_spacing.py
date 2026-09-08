from IPython.display import HTML, Markdown, Math


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


def test_a_narrative_carries_no_styling_of_its_own(monkeypatch):
    """This asserted the narrative's margins until the mathematics inside one turned out
    not to typeset in Colab at all: a `display(HTML(...))` is isolated there, whatever
    delimiter it carries. The narrative is a `Markdown` now and takes the notebook's own
    paragraph spacing.

    Which makes the absence worth pinning rather than the margins. Wrapping the prose
    back into a styled `<div>` - markdown passes raw HTML straight through, so it is the
    obvious way to get the spacing back - would put the relations inside HTML again and
    silently stop them rendering, the exact defect that reached the engineer's page.
    """
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng("", '"""Texto explicativo."""\nA = 1')

    assert [type(item) for item in displayed] == [Markdown, Math]
    assert displayed[0].data == "Texto explicativo."
