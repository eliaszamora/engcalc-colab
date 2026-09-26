r"""Prose can typeset the relation it is explaining, and does so in Colab.

A narrative block was escaped text and nothing else, so a memoria that explains a matrix
formulation had to write its relations in ASCII:

    K_e = transpose(A_e) k_e A_e
    u_e_g = L_e U
    A_e = R_e L_e T

Eight of those sat in one frame-analysis sheet, and they are the didactic spine of it -
the chain `q -> T -> U -> L_e -> u_e^g -> R_e -> u_e^l` that the prose exists to explain.

Writing them as statements instead is not a workaround; it is worse than one. Free
symbols commute, so

    A_e = R_e*L_e*T_m     renders   L_e R_e T_m

with the factors reordered. For matrices the order *is* the mathematics, so the page
would state something false - and `K_e = transpose(A_e)*k_e*A_e` does not render at all,
because `transpose` refuses a symbol. The relations can only live in the prose.

`$...$`, because it is what a Colab markdown cell already uses. The risks are prose that
contains a lone `$` and prose that contains two, and both are handled by the same rule:
a span becomes mathematics only when its content neither begins nor ends with a space.
`cuesta $5 y $10` keeps its dollars.

**The output is a `Markdown`, and #96 shipped an `HTML` that does not typeset in Colab.**
The engineer's own memoria showed the relations as raw text. Measured in Colab, not
reasoned about: of `\(...\)`, `$...$`, `\[...\]` and an explicit `MathJax.typeset()`
call, *none* renders inside an HTML output - Colab isolates it. `Markdown`, `Latex` and
`Math` all typeset, and `Markdown` is the one that keeps prose as prose.

It went unnoticed because the harness this repository renders pages with configures
MathJax with exactly the delimiters the magic emitted, so it could not have failed. The
check worked; it did not measure what it was believed to measure.

Markdown then eats what HTML did not. This sheet's own narrative carries seven
underscores outside the formulas - `L_e`, `R_e`, `A_e`, `theta_1`, `theta_4` - and
markdown reads the span between two of them as emphasis, so they are escaped. So are
`<`, `>` and `&`, as entities rather than backslashes, because markdown passes raw HTML
through and the HTML path used to escape them: a formula that does not typeset is not
worth trading for a paragraph that can inject markup.

**Since 2026-09-25 the output is a `Math`, and a paragraph is typeset as the working is.**
Colab set the Markdown in its own letter, Google Sans at 14 px beside KaTeX's 16.94 px, and
strips any style put on it; he chose the paragraph in the letter of the mathematics. The
words go in `\\text{}` and each `$...$` span is mathematics between them - still never
HTML, which is the point above and still true. What Markdown ate is now what LaTeX would
read as a command, `# $ % & _ { } ~ ^ \\`, and it is written as text; the prose stays
inert, the mathematics is still read whole, and the same rule decides which dollars are a
formula. The contracts below are the ones this file held, asked of the new form.
"""

import pytest
from IPython.display import HTML, Markdown, Math

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> str:
        captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def narrative(text: str) -> str:
    return '"""\n' + text + '\n"""\n'


# --- the mathematics ------------------------------------------------------------------

def test_a_paired_span_becomes_inline_math(cell):
    out = cell(narrative("La cadena termina en $A_e = R_e L_e T$ y nada más."))
    assert r"\text{La cadena termina en }A_e = R_e L_e T\text{ y nada más.}" in out, out


def test_several_spans_in_one_paragraph(cell):
    out = cell(narrative("Primero $U = T q$, después $u_e = L_e U$."))
    assert r"\text{Primero }U = T q\text{, después }u_e = L_e U\text{.}" in out, out


def test_the_output_is_typeset_and_never_html(monkeypatch):
    """The whole point, and the thing a later edit is most likely to undo. An `HTML`
    output does not typeset in Colab at all, whatever delimiter it carries."""
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", narrative("Se cumple $U = T q$ siempre."))
    assert [type(obj) for obj in captured] == [Math], captured


# --- the prose is inert -----------------------------------------------------------------

def test_markup_in_prose_is_text(cell):
    """A narrative block is text the sheet's author typed, and it stays inert: inside
    `\\text{}` a `<b>` is three characters, not bold - and written as `\\textless{}`, so no
    `<` reaches the output's data at all."""
    out = cell(narrative("Antes <b>x</b> y luego $K_e = A^T k A$ después."))
    assert r"\text{Antes \textless{}b\textgreater{}x\textless{}/b\textgreater{} y luego }K_e = A^T k A" in out, out
    assert "<b>" not in out, out


def test_an_ampersand_is_an_ampersand(cell):
    out = cell(narrative("Acero A & B en la tabla."))
    assert r"A \& B" in out, out


def test_an_underscore_in_prose_is_an_underscore(cell):
    """Measured on this repository's own benchmark: seven of these, in `L_e`, `R_e`,
    `A_e`, `theta_1` and `theta_4`. In prose they are underscores, not subscripts."""
    out = cell(narrative("La cadena T, L_e, R_e y nada más."))
    assert r"L\_e" in out and r"R\_e" in out, out


@pytest.mark.parametrize(
    "character, written",
    [
        ("_", r"\_"),
        ("#", r"\#"),
        ("%", r"\%"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
        ("\\", r"\textbackslash{}"),
        ("*", "*"),
    ],
)
def test_every_latex_special_stays_literal_in_prose(cell, character, written):
    """One rule, not a list of remembered characters: a narrative is text the author
    typed, and it reads back the way it was typed. `#` is `estribos #3 @ 20 cm`, how a
    Chilean sheet writes rebar; a lone `*` is not emphasis."""
    out = cell(narrative(f"Un texto con {character} en medio."))
    assert rf"\text{{Un texto con {written} en medio.}}" in out, out


def test_a_numbered_paragraph_keeps_its_own_number(cell):
    """Markdown renumbered `3.` and `5.` as a list, 3 and 4. Typeset, a number is a number."""
    out = cell(narrative("3. Tercera etapa.\n\n5. Quinta etapa."))
    assert r"\text{3. Tercera etapa.}" in out and r"\text{5. Quinta etapa.}" in out, out


def test_a_paragraph_opening_with_a_dash_is_not_a_bullet(cell):
    out = cell(narrative("- El acero llega en barras."))
    assert r"\text{- El acero llega en barras.}" in out, out


def test_a_bracket_is_a_bracket(cell):
    out = cell(narrative("El vector U [doce componentes] se toma aparte."))
    assert r"\text{El vector U [doce componentes] se toma aparte.}" in out, out


def test_the_mathematics_itself_is_not_escaped(cell):
    """The other half of the same rule, and the one an over-eager escape breaks. LaTeX
    is read whole: `\\,` is a thin space and `<` is a relation."""
    out = cell(narrative(r"Se cumple $A_e = R_e\,L_e\,T$ cuando $a < b$."))
    assert r"A_e = R_e\,L_e\,T" in out and r"a < b" in out, out


# --- the dollars that are not mathematics -------------------------------------------------

def test_a_lone_dollar_stays_a_dollar(cell):
    out = cell(narrative("El coste es de 5 $ por metro."))
    assert r"\text{El coste es de 5 \$ por metro.}" in out, out


def test_two_amounts_are_not_read_as_one_formula(cell):
    """The rule that makes `$...$` safe in prose: a span whose content begins or ends
    with a space is not mathematics, so `cuesta $5 y $10` keeps its dollars."""
    out = cell(narrative("Cuesta $5 y $10 según el caso."))
    assert r"\text{Cuesta \$5 y \$10 según el caso.}" in out, out


def test_an_empty_span_is_left_alone(cell):
    out = cell(narrative("Nada aquí $$ tampoco."))
    assert r"\text{Nada aquí \$\$ tampoco.}" in out, out


def test_a_narrative_without_any_dollar_is_written_whole(cell):
    """The half that must not move: every memoria written before this reads the same."""
    out = cell(narrative("Una explicación corriente, sin matemáticas."))
    assert r"\text{Una explicación corriente, sin matemáticas.}" in out, out
