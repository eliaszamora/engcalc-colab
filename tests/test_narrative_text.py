from engcalc_colab.parser import parse_cell


def test_single_line_triple_quoted_text_is_a_narrative_item():
    text = "Se analiza una viga simplemente apoyada de 6 m de luz."

    items = parse_cell(f'"""{text}"""')

    assert len(items) == 1
    narrative = items[0]
    assert type(narrative).__name__ == "ParsedNarrative"
    assert narrative.line_no == 1
    assert narrative.paragraphs == (text,)


def test_multiline_narrative_joins_wrapped_lines_and_preserves_paragraph_breaks():
    cell = (
        '"""\n'
        "Se analiza una viga simplemente apoyada sometida a una carga\n"
        "uniformemente distribuida.\n"
        "\n"
        "Posteriormente se determina el momento máximo de diseño.\n"
        '"""'
    )

    items = parse_cell(cell)

    assert len(items) == 1
    narrative = items[0]
    assert type(narrative).__name__ == "ParsedNarrative"
    assert narrative.paragraphs == (
        "Se analiza una viga simplemente apoyada sometida a una carga "
        "uniformemente distribuida.",
        "Posteriormente se determina el momento máximo de diseño.",
    )


def test_hash_markup_inside_narrative_is_literal_text_not_heading_or_comment():
    cell = '"""\n## No es un título\n# Tampoco es un comentario\n"""'

    items = parse_cell(cell)

    assert len(items) == 1
    narrative = items[0]
    assert type(narrative).__name__ == "ParsedNarrative"
    assert narrative.paragraphs == (
        "## No es un título # Tampoco es un comentario",
    )
