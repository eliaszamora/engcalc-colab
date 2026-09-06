r"""Prose can typeset the relation it is explaining.

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


def test_a_paired_span_becomes_inline_math(cell):
    html = cell(narrative("La cadena termina en $A_e = R_e L_e T$ y nada más."))
    assert r"\(A_e = R_e L_e T\)" in html, html
    assert "La cadena termina en" in html, html
    assert "$" not in html, html


def test_the_prose_around_it_is_still_escaped(cell):
    """A narrative block is text the sheet's author typed, and it stays inert."""
    html = cell(narrative("Antes <b>x</b> y luego $K_e = A^T k A$ después."))
    assert "&lt;b&gt;" in html, html
    assert "<b>" not in html, html
    assert r"\(K_e = A^T k A\)" in html, html


def test_the_prose_after_the_last_span_is_escaped_too(cell):
    """The half the first draft missed. Its only escaping contract put the markup
    *before* the mathematics, so the tail after the last span was never exercised and
    dropping its `escape` survived mutation."""
    html = cell(narrative("Primero $K = A$ y luego <b>negrita</b>."))
    assert "&lt;b&gt;" in html, html
    assert "<b>" not in html, html


def test_a_lone_dollar_stays_a_dollar(cell):
    html = cell(narrative("El coste es de 5 $ por metro."))
    assert "5 $ por metro" in html, html
    assert r"\(" not in html, html


def test_two_amounts_are_not_read_as_one_formula(cell):
    """The rule that makes `$...$` safe in prose: a span whose content begins or ends
    with a space is not mathematics. `$5 y $` would otherwise be typeset."""
    html = cell(narrative("Cuesta $5 y $10 según el caso."))
    assert "$5 y $10" in html, html
    assert r"\(" not in html, html


def test_several_spans_in_one_paragraph(cell):
    html = cell(narrative("Primero $U = T q$, después $u_e = L_e U$."))
    assert r"\(U = T q\)" in html, html
    assert r"\(u_e = L_e U\)" in html, html


def test_an_empty_span_is_left_alone(cell):
    html = cell(narrative("Nada aquí $$ tampoco."))
    assert "$$" in html, html
    assert r"\(" not in html, html


def test_a_narrative_without_any_dollar_is_unchanged(cell):
    """The half that must not move: every memoria written before this."""
    html = cell(narrative("Una explicación corriente, sin matemáticas."))
    assert "Una explicación corriente, sin matemáticas." in html, html
    assert r"\(" not in html, html
