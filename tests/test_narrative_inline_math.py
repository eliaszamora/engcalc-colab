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
"""

import pytest

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
    assert "$A_e = R_e L_e T$" in out, out
    assert "La cadena termina en" in out, out


def test_several_spans_in_one_paragraph(cell):
    out = cell(narrative("Primero $U = T q$, después $u_e = L_e U$."))
    assert "$U = T q$" in out, out
    assert "$u_e = L_e U$" in out, out


def test_the_output_is_a_markdown_not_an_html(monkeypatch):
    """The whole point, and the thing a later edit is most likely to undo. An `HTML`
    output does not typeset in Colab at all, whatever delimiter it carries."""
    from IPython.display import Markdown

    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", narrative("Se cumple $U = T q$ siempre."))
    assert any(isinstance(obj, Markdown) for obj in captured), captured


# --- the prose is inert -----------------------------------------------------------------

def test_the_prose_around_it_is_still_escaped(cell):
    """A narrative block is text the sheet's author typed, and it stays inert. Markdown
    passes raw HTML through, so this is entities rather than the HTML path's escaping -
    and it is the property that nearly went while the rendering was being fixed."""
    out = cell(narrative("Antes <b>x</b> y luego $K_e = A^T k A$ después."))
    assert "&lt;b&gt;" in out, out
    assert "<b>" not in out, out
    assert "$K_e = A^T k A$" in out, out


def test_the_prose_after_the_last_span_is_escaped_too(cell):
    """The half the first draft missed. Its only escaping contract put the markup
    *before* the mathematics, so the tail after the last span was never exercised and
    dropping its escape survived mutation."""
    out = cell(narrative("Primero $K = A$ y luego <b>negrita</b>."))
    assert "&lt;b&gt;" in out, out
    assert "<b>" not in out, out


def test_an_ampersand_is_an_ampersand(cell):
    out = cell(narrative("Acero A & B en la tabla."))
    assert "&amp;" in out, out


def test_an_underscore_in_prose_does_not_become_emphasis(cell):
    """Measured on this repository's own benchmark: seven of these, in `L_e`, `R_e`,
    `A_e`, `theta_1` and `theta_4`. Left unescaped, "la cadena T, L_e, R_e" prints with
    "e, R" in italics and the underscores gone."""
    out = cell(narrative("La cadena T, L_e, R_e y nada más."))
    assert r"L\_e" in out, out
    assert r"R\_e" in out, out


@pytest.mark.parametrize(
    "character, meaning",
    [
        ("_", "emphasis"),
        ("*", "emphasis"),
        ("`", "code"),
        ("#", "a heading"),
        ("\\", "an escape"),
    ],
)
def test_every_markdown_special_stays_literal_in_prose(cell, character, meaning):
    """One rule, not a list of remembered characters: a narrative is text the author
    typed, and it reads back the way it was typed. The HTML path guaranteed that by
    escaping everything; markdown keeps the guarantee only if the whole set is escaped,
    and a set is exactly the kind of thing a later edit trims a member from.

    `#` is the one that looks like padding and is not - `estribos #3 @ 20 cm` is how a
    Chilean sheet writes rebar, and at the start of a paragraph markdown reads it as a
    heading.
    """
    out = cell(narrative(f"Un texto con {character} en medio."))
    assert "\\" + character in out, out


def test_a_bracket_is_an_entity_and_never_a_backslash(cell):
    r"""The one member of the set that cannot take a backslash. `\[` is MathJax's
    default display delimiter, and the notebook lifts mathematics out before markdown
    runs, so `el vector U [doce componentes]` escaped the markdown way arrives as
    `\[doce componentes\]` and the sentence turns into a centred formula.

    Found by a mutant: removing `]` from the escape set killed nothing, and asking why
    `]` was there at all was what exposed what `[` was doing.
    """
    out = cell(narrative("El vector U [doce componentes] se toma aparte."))
    assert "&#91;doce componentes] se toma" in out, out
    assert "\\[" not in out, out


def test_the_mathematics_itself_is_not_escaped(cell):
    """The other half of the same rule, and the one an over-eager escape breaks. LaTeX
    is read whole by MathJax: `\\,` is a thin space and `<` is a relation, and escaping
    either turns a formula into rubble."""
    out = cell(narrative(r"Se cumple $A_e = R_e\,L_e\,T$ cuando $a < b$."))
    assert r"$A_e = R_e\,L_e\,T$" in out, out
    assert "$a < b$" in out, out


# --- the dollars that are not mathematics -------------------------------------------------

def test_a_lone_dollar_stays_a_dollar(cell):
    out = cell(narrative("El coste es de 5 $ por metro."))
    assert r"5 \$ por metro" in out, out


def test_two_amounts_are_not_read_as_one_formula(cell):
    """The rule that makes `$...$` safe in prose: a span whose content begins or ends
    with a space is not mathematics. Escaped as well, because Colab reads a markdown
    output's dollars itself and turned `cuesta $5 el kilo y $10 el metro` into one
    formula when they were left bare."""
    out = cell(narrative("Cuesta $5 y $10 según el caso."))
    assert r"\$5 y \$10" in out, out


def test_an_empty_span_is_left_alone(cell):
    out = cell(narrative("Nada aquí $$ tampoco."))
    assert r"\$\$" in out, out


def test_a_narrative_without_any_dollar_is_unchanged(cell):
    """The half that must not move: every memoria written before this."""
    out = cell(narrative("Una explicación corriente, sin matemáticas."))
    assert "Una explicación corriente, sin matemáticas." in out, out
    assert "$" not in out, out
