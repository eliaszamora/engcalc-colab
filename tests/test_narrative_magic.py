from IPython.display import HTML, Markdown, Math


def test_magic_renders_narrative_in_source_order_between_heading_and_equations(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)

    magics.eng(
        "",
        (
            "## Análisis de la viga\n"
            '"""Se analiza una viga simplemente apoyada."""\n'
            "A = 1\n"
            '"""Luego se determina la segunda magnitud."""\n'
            "B = 2"
        ),
    )

    # A heading is HTML and a narrative is Markdown: Colab does not typeset a
    # `display(HTML(...))`, and a narrative is the one of the two that carries
    # mathematics.
    assert [type(item) for item in displayed] == [HTML, Markdown, Math, Markdown, Math]
    assert "Análisis de la viga" in displayed[0].data
    assert "Se analiza una viga simplemente apoyada." in displayed[1].data
    assert "Luego se determina la segunda magnitud." in displayed[3].data


def test_narrative_escapes_user_text(monkeypatch):
    """Markdown passes raw HTML through, so the escaping this asserts is not free -
    moving the narrative to a Markdown output nearly dropped it, and this contract is
    what caught that."""
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)

    magics.eng("", '"""<script>alert(1)</script> & cálculo"""')

    assert len(displayed) == 1
    assert isinstance(displayed[0], Markdown)
    assert "<script>" not in displayed[0].data
    assert "&lt;script&gt;" in displayed[0].data
    assert "&amp; cálculo" in displayed[0].data


def test_narrative_renders_blank_line_as_separate_paragraph(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)

    magics.eng(
        "",
        '"""\nPrimera línea\ncontinúa aquí.\n\nSegundo párrafo.\n"""',
    )

    assert len(displayed) == 1
    # A blank line is markdown's own paragraph break, and the lines within one
    # paragraph are joined into a single line. Asserted together, because the join is
    # what makes the break mean anything.
    assert displayed[0].data == "Primera línea continúa aquí.\n\nSegundo párrafo."
