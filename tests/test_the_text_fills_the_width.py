r"""A paragraph fills the width the page has, a little smaller than the working.

His report of 2026-09-26, on exercise 2.1 in Colab: the text under "Compatibilidad" was a
little small, and its lines ended well short of the output's width. `narrative_latex` cut a
paragraph every 76 characters of *source* - a `$...$` span counted its LaTeX, 42 for
`$u \cos\theta + v \sin\theta = \delta_{ab}$`, which shows about 15 - and 76 characters were
445 px measured for the window of one day. KaTeX breaks no line inside the array the text
sat in. It was `\footnotesize`, 0.8 of the working, under Colab's own 14 px text.

His choice, from four versions of his own paragraph shown in his Colab (*"Me gusta tu
recomendación"*): the browser breaks the lines where the output ends, and `\small`. The
paragraph is typeset inline at the top level, a word at a time with `\allowbreak` between
them, so KaTeX hands the browser one piece per word; a formula is a group, never cut.
"""

import pytest
from IPython.display import Math

from engcalc_colab.renderer import narrative_latex

from test_colab_can_typeset_every_formula import _typeset, katex_ready  # noqa: F401

PARAGRAPH = (
    "Lo que A se mueve a lo largo de cada barra es lo que esa barra se alarga: "
    r"$u \cos\theta + v \sin\theta = \delta_{ab}$ y $-u \cos\phi + v \sin\phi = \delta_{ac}$. "
    "Despejando u y v:"
)
WORDS = len(PARAGRAPH.split(" ")) - 2 * 6  # each formula is one word, written as seven


def _as_colab_reads_it(latex: str) -> dict:
    """IPython's own `$\\displaystyle ...$`, typeset inline as Colab typesets it."""
    tex = Math(latex)._repr_latex_().strip("$")
    (result,) = _typeset([{"tex": tex, "display": False}])["results"]
    return result


def test_the_renderer_cuts_no_line():
    latex = narrative_latex([PARAGRAPH])
    assert r"\begin{array}" not in latex, latex
    assert r"\\" not in latex, latex


def test_every_word_is_a_place_the_browser_may_break():
    latex = narrative_latex([PARAGRAPH])
    assert latex.count(r"\allowbreak") == WORDS - 1, latex


def test_a_formula_is_never_cut():
    latex = narrative_latex([PARAGRAPH])
    assert r"{u \cos\theta + v \sin\theta = \delta_{ab}}" in latex, latex
    assert r"{-u \cos\phi + v \sin\phi = \delta_{ac}}\text{. }" in latex, latex


def test_the_text_is_small_and_not_a_group():
    """`\\small` (0.9 of the working) at the top level: inside `{...}` KaTeX would hand the
    browser the whole paragraph as one piece."""
    assert narrative_latex(["Un párrafo."]).startswith(r"\small ")


def test_two_paragraphs_keep_their_room():
    latex = narrative_latex(["Primero.", "Segundo."])
    assert latex == r"\small \text{Primero.} \\[8pt] \text{Segundo.}", latex


def test_colab_s_katex_hands_the_browser_a_piece_per_word(katex_ready):  # noqa: F811
    result = _as_colab_reads_it(narrative_latex([PARAGRAPH]))
    assert result["error"] is None and not result["warnings"], result
    # Today one piece: the paragraph could not be broken at all.
    assert result["bases"] == WORDS, result


def test_colab_s_katex_keeps_a_paragraph_break(katex_ready):  # noqa: F811
    result = _as_colab_reads_it(narrative_latex(["Uno dos.", "Tres cuatro."]))
    assert result["error"] is None and not result["warnings"], result
    assert result["bases"] == 4, result


@pytest.mark.parametrize(
    "written, word",
    [
        ("Una **fuerza** y", r"\textbf{fuerza }"),
        ("una *longitud*.", r"\textit{longitud}\text{.}"),
        ("$M$, dos", r"{M}\text{, }"),
        ("es $M = q L^2/8$ en", r"{M = q L^2/8}\text{ }\allowbreak \text{en}"),
    ],
)
def test_a_word_keeps_its_style_and_its_space(written, word):
    assert word in narrative_latex([written]), narrative_latex([written])
