r"""One rule for the room between blocks, and the text in the letter of the mathematics.

Measured in his Colab on 2026-09-25: rows inside a block of equations are ~13 px apart, and
a paragraph between triple quotes sat 5-7 px from the equations around it - closer than two rows of one
block, so it read as part of its neighbour. Room had been given case by case: empty rows
around a table and a `roots` block, a strut in the "Como" sentence, margins on headings. The
text was Colab's own letter, Google Sans at 14 px, beside KaTeX's at 16.94 px. Colab strips
any style from HTML inside a Markdown output (a margin, a font - measured, all five ways),
so a paragraph cannot carry room or a letter of its own.

His choice, from the three shown in his Colab (*"Me gusta más tu recomendación"*): every
block of mathematics takes the same room above and below, from one place
(`renderer.page_block`), and a paragraph is typeset as the mathematics is - its words in
`\text{}`, its `$...$` as mathematics - in lines of a width that fits the page. Headings take
the same letter. The room between rows inside a block is not touched.
"""

import contextlib
import io
import re

import pytest
from IPython.display import HTML, Markdown, Math

import engcalc_colab.magic as magic
from engcalc_colab.magic import BLOCK_SPACER
from engcalc_colab.renderer import narrative_latex

from test_colab_can_typeset_every_formula import _typeset, katex_ready  # noqa: F401


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str):
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", source)
        return captured, console.getvalue()

    return run


EVERY_KIND = (
    "## Título\n### Subtítulo\n"
    '"""Un párrafo con una relación $M = q L^2/8$ en medio."""\n'
    "q := 2000*kgf/m\nL := 6*m\nd := 44*cm\nb := 30*cm\n"
    '"""Otro párrafo."""\n'
    "M = q*L^2/8\nnumeric(M)\n"
    "% if d > b:\nh := d + 6*cm\n% end\n"
    "table(2*x, x, [1*m, 2*m])\n"
    "f(x) = x^2 - 4*m^2\nroots(f(x), x, 0*m, 5*m)\n"
    "result(M)\n"
)


def test_the_same_room_stands_between_any_two_blocks(sheet):
    captured, console = sheet(EVERY_KIND)
    assert not console, console
    spacer = [isinstance(item, HTML) and item.data == BLOCK_SPACER for item in captured]
    # Never first, never last, never two together: exactly one between two blocks.
    assert not spacer[0] and not spacer[-1], captured
    assert all(not (a and b) for a, b in zip(spacer, spacer[1:])), captured
    assert all(a or b for a, b in zip(spacer, spacer[1:])), captured
    blocks = [item for item, is_spacer in zip(captured, spacer) if not is_spacer]
    # Two headings, two paragraphs, data, working, the sentence, its row, table, roots, result.
    assert len(blocks) >= 10, blocks


def test_no_block_carries_room_of_its_own_any_more(sheet):
    captured, _console = sheet(EVERY_KIND)
    for item in captured:
        if isinstance(item, Math):
            assert r"\rule[-0.7em]" not in item.data, item.data
            assert r"\rule{0pt}{0.7em} \\[-4pt]" not in item.data, item.data


def test_a_figure_and_its_caption_are_one_block(sheet):
    captured, console = sheet("L := 6*m\nM(x) = x*(L - x)*kN/m\nplot(M(x), x, 0, L)\nq := 1*m\n")
    assert not console, console
    kinds = ["spacer" if isinstance(item, HTML) and item.data == BLOCK_SPACER else type(item).__name__ for item in captured]
    assert kinds.count("spacer") == len([k for k in kinds if k != "spacer"]) - 1, kinds


def test_a_paragraph_is_typeset_as_the_mathematics_is(sheet):
    captured, _console = sheet(EVERY_KIND)
    assert not [item for item in captured if isinstance(item, Markdown)], captured
    paragraph = next(item.data for item in captured if isinstance(item, Math) and "párrafo con" in item.data)
    assert r"\text{Un párrafo con una relación }M = q L^2/8\text{ en medio.}" in paragraph, paragraph


def test_a_long_paragraph_is_cut_into_lines_that_fit(sheet):
    words = " ".join(f"palabra{i}" for i in range(60))
    captured, _console = sheet(f'"""{words}"""\n')
    (paragraph,) = [item.data for item in captured if isinstance(item, Math)]
    lines = re.findall(r"\\text\{([^}]*)\}", paragraph)
    assert len(lines) > 3, lines
    assert all(len(line) <= 80 for line in lines), [len(line) for line in lines]
    assert " ".join(line.strip() for line in lines) == words


def test_two_paragraphs_stay_two(sheet):
    captured, _console = sheet('"""\nPrimero.\n\nSegundo.\n"""\n')
    (paragraph,) = [item.data for item in captured if isinstance(item, Math)]
    assert paragraph.index(r"\text{Primero.}") < paragraph.index(r"\text{Segundo.}"), paragraph


@pytest.mark.parametrize(
    "written, typeset",
    [
        ("50 % de 10 & más", r"50 \% de 10 \& más"),
        ("la barra #3 y a_b", r"la barra \#3 y a\_b"),
        # KaTeX has no command for them; written as they are, they show in the system's
        # letter with a warning and no error, in Colab as here.
        ("¿Cuánto? ¡Sí!", "¿Cuánto? ¡Sí!"),
        ("uno — dos – tres", r"uno \textemdash{} dos \textendash{} tres"),
        # KaTeX reads `·` in text as `\cdotp`, which it has only in mathematics.
        ("en cm·kgf", r"en cm$\cdot$kgf"),
    ],
)
def test_what_latex_would_read_is_written_as_text(written, typeset):
    assert typeset in narrative_latex([written]), narrative_latex([written])


def test_bold_and_italic_are_kept(sheet):
    captured, _console = sheet('"""Una **fuerza** y una *longitud*."""\n')
    (paragraph,) = [item.data for item in captured if isinstance(item, Math)]
    assert r"\textbf{fuerza}" in paragraph and r"\textit{longitud}" in paragraph, paragraph


def test_a_heading_takes_the_letter_of_the_mathematics(sheet):
    captured, _console = sheet("## Título\n### Subtítulo\nq := 1*m\n")
    headings = [item.data for item in captured if isinstance(item, HTML) and item.data != BLOCK_SPACER]
    assert len(headings) == 2 and all("KaTeX_Main" in heading for heading in headings), headings


def test_colab_typesets_the_text_without_a_complaint(katex_ready):  # noqa: F811
    latex = (narrative_latex(["¿Cuánto? ¡Sí! — «uno» 50 % & #3 a_b ~x^y {z} cm·kgf, según $M = q L^2/8$."]))
    (result,) = _typeset([{"tex": latex, "display": True}])["results"]
    assert result["error"] is None, result
    # Only the letters KaTeX draws from the system's font, `¿ ¡ « »`, may warn.
    assert all(warning.startswith("unknownSymbol") for warning in result["warnings"]), result
