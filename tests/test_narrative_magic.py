from IPython.display import HTML, Math

from conftest import blocks_into


def test_magic_renders_narrative_in_source_order_between_heading_and_equations(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", blocks_into(displayed))
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

    # A heading is HTML; a narrative is typeset as the working is since 2026-09-25 (his
    # choice), a `Math` output - never HTML, which Colab does not typeset.
    assert [type(item) for item in displayed] == [HTML, Math, Math, Math, Math]
    assert "Análisis de la viga" in displayed[0].data
    assert r"\text{Se analiza una viga simplemente apoyada.}" in displayed[1].data
    assert r"\text{Luego se determina la segunda magnitud.}" in displayed[3].data


def test_narrative_escapes_user_text(monkeypatch):
    """A narrative is text the author typed, and it stays inert whatever it holds."""
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", blocks_into(displayed))
    magics = magic_module.EngMagics(shell=None)

    magics.eng("", '"""<script>alert(1)</script> & cálculo"""')

    assert len(displayed) == 1
    assert isinstance(displayed[0], Math)
    assert "<script>" not in displayed[0].data and "<" not in displayed[0].data
    assert r"\textless{}script\textgreater{}" in displayed[0].data
    assert r"\& cálculo" in displayed[0].data


def test_narrative_renders_blank_line_as_separate_paragraph(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", blocks_into(displayed))
    magics = magic_module.EngMagics(shell=None)

    magics.eng(
        "",
        '"""\nPrimera línea\ncontinúa aquí.\n\nSegundo párrafo.\n"""',
    )

    assert len(displayed) == 1
    # The lines within one paragraph are joined into a single line, and a blank line
    # starts the next paragraph with more room than a line break. Asserted together,
    # because the join is what makes the break mean anything.
    data = displayed[0].data
    assert r"\text{Primera línea continúa aquí.} \\[8pt] \text{Segundo párrafo.}" in data, data
