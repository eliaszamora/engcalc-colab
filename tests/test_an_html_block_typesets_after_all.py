r"""The four blocks typeset, because a `Markdown` output does what an HTML one cannot.

This replaces `test_an_html_block_does_not_typeset_latex.py`, whose premise was measured
and is now known to be half of one. #133 measured, correctly, that Colab typesets nothing
inside a `display(HTML(...))` - not `\(...\)`, not `$...$`, not an explicit
`MathJax.typeset()` - and concluded that the blocks had to become plain text. The reader
stopped seeing backslashes, and started seeing this instead:

    Extrema — U1(x)
    ... value = L**2*(0.15*qD + 0.2*qL)      Python, in a memoria de cálculo
    M_u  =  0.15 qD L² + 0.2 qL L²           two lines below, typeset

The engineer noticed the smaller half of it - "hay letra o números que salen en otro
formato de letra" - and he was right: half the page was in the notebook's sans-serif and
half in MathJax's serif, with the same quantity appearing in both.

What #133 never asked is whether some *other* output typesets. Measured in Colab, in one
cell, with an HTML control:

    A   HTML     + `$...$`     ->  `$300.00$`, verbatim.  #133 confirmed.
    B   Markdown + raw HTML + `$...$`
                              ->  the table renders WITH its borders, and the
                                  numbers typeset.  This is the answer.
    C   Markdown + raw HTML + `\(...\)`
                              ->  `(300.00)`. The backslashes are eaten.
    E   Markdown + a `<style>` block
                              ->  the rule is dropped; the class is inert.

So: `Markdown`, `$...$`, and inline `style=` attributes. B and E together are the whole
design, and C is why the delimiter is not the one #96 used.

The three contracts here are about *form* - is it a Markdown output, is the mathematics
delimited, is the styling of a kind that survives - and they exist because the helper
that lets the *content* contracts keep working (`block_text` in `conftest.py`) strips
exactly the things they check. One file answers "does it typeset"; the helper answers
"what does it say".

**Superseded in part by `test_a_computed_block_is_written_like_the_working`.** Markdown
typeset the mathematics and set the words around it in the notebook's text font, wrapped a
wide row as prose wraps, and started at the text's edge - the engineer on 0.31.2: "hay
fuentes distintas, no se ve ordenado". The blocks are `Math` outputs now. The contracts here
that were about markdown - a markdown output, `$...$` per cell, inline `style=` - went with
it; the ones about what the blocks must still be stay, asked of the `Math` output.
"""

import pytest
from IPython.display import Markdown, Math

import engcalc_colab.magic as magic


@pytest.fixture
def displayed(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str):
        captured.clear()
        magics.eng("", source)
        return captured

    return run


SHEET = (
    "L := 6.00*m\n"
    "qD := 18*kN/m\n"
    "qL := 12*kN/m\n"
    "M_D(x) = qD*x*(L - x)/2\n"
    "M_L(x) = qL*x*(L - x)/2\n"
    "case D = M_D(x)\n"
    "case Lv = M_L(x)\n"
    "combo U1 = 1.2*D + 1.6*Lv\n"
    "governing(U1(x), M_D(x), x, 0, L)\n"
    "table(U1(x), x, 0, L, 4)\n"
    "extrema(U1(x), x, 0, L)\n"
    "M_u = U1(L/2)\n"
    "report(M_u)\n"
    "summary()\n"
)


def _blocks(displayed) -> list[str]:
    items = displayed(SHEET)
    blocks = [
        item.data
        for item in items
        if isinstance(item, Math) and r"\hspace{0.2em}\begin{array}{l} " in item.data
    ]
    assert len(blocks) == 4, [type(item).__name__ for item in items]
    return blocks


def test_the_exact_expression_is_mathematics_and_not_python(displayed):
    """The line the engineer's screenshot showed: `L**2*(0.15*qD + 0.2*qL)`."""
    extrema = next(block for block in _blocks(displayed) if "Extrema" in block)

    assert "**" not in extrema, extrema
    assert "L^{2}" in extrema, extrema


def test_a_value_and_its_unit_are_one_piece_of_mathematics(displayed):
    """`$183.60\\,\\mathrm{kN} \\cdot \\mathrm{m}$` - the spacing and the dot are LaTeX's,
    so the block reads the way the working above it reads."""
    summary = next(block for block in _blocks(displayed) if "Summary" in block)

    assert r"\mathrm{kN}" in summary, summary
    assert r"\," in summary, summary


# --- what must not move ---------------------------------------------------------------


def test_a_math_row_never_carries_markup(displayed):
    """#120's contract, which is about the other direction and still holds: finished
    markup must never be embedded inside `\\begin{array}`."""
    from IPython.display import Math

    for item in displayed(SHEET):
        if isinstance(item, Math):
            assert "<div" not in item.data, item.data[:200]
            assert "<table" not in item.data, item.data[:200]


def test_a_narrative_typesets_its_relations(displayed):
    """#120's point, kept: the relations in prose must typeset, so prose is never HTML.

    It was a Markdown output for that. Since 2026-09-25 (his choice) it is a Math output,
    its words in `\\text{}` and its relation as mathematics - which typesets in Colab too.
    """
    items = displayed('"""Una viga de seis metros con $q = 10$ kN/m."""\nL := 6*m\n')
    prose = [item.data for item in items if isinstance(item, Math) and "viga" in item.data]
    assert prose and r"\text{Una viga de seis metros con }q = 10\text{ kN/m.}" in prose[0], [
        type(item).__name__ for item in items
    ]


def test_a_unit_name_cannot_smuggle_markup(displayed):
    """The escape #133 kept was inert then and is gone now, because LaTeX needs its
    backslashes and escaping them is what would break it. What reaches the delimiter is a
    magnitude, a Pint unit name, or SymPy's printer - never a sheet's free text. The free
    text a block does carry is a *label*, and that still goes through `escape`."""
    blocks = displayed(
        "L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\ntable(M(x), x, 0, L, 3)\n"
    )
    table = next(item.data for item in blocks if isinstance(item, Math) and r"\hline" in item.data)
    header = table.split(r"\hline")[0]
    assert r"M\left(x\right)" in header, header
    assert "<" not in table, table
